"""
User-level analysis commands, typically for measuring or generating SheetViews.

Most of this file consists of commands for creating SheetViews, paired
with a template for how to construct plots from these SheetViews.

For instance, the implementation of Activity plots consists of the
update_activity() command plus the Activity PlotGroupTemplate.  The
update_activity() command reads the activity array of each Sheet and
makes a corresponding SheetView to put in the Sheet's sheet_views
dictionary, while the Activity PlotGroupTemplate specifies which
SheetViews should be plotted in which combination.  See the help for
PlotGroupTemplate for more information.

Some of the commands are ordinary Python functions, but the rest are
ParameterizedFunctions, which act like Python functions but support
Parameters with defaults, bounds, inheritance, etc.  These commands
are usually grouped together using inheritance so that they share a
set of parameters and some code, and only the bits that are specific
to that particular plot or analysis appear below.  See the
superclasses for the rest of the parameters and code.
"""

import Image,ImageDraw

import copy

from numpy.oldnumeric import array, maximum
from numpy import pi, sin, cos, nonzero, round, linspace, floor, ceil

import param
from param.parameterized import ParameterizedFunction
from param.parameterized import ParamOverrides

import topo
from topo.base.cf import Projection
from topo.base.sheet import Sheet
from topo.sheet import GeneratorSheet
from topo.base.sheetview import SheetView
from topo.misc.distribution import Distribution, DistributionStatisticFn
from topo.misc.distribution import DSF_MaxValue, DSF_BimodalPeaks
from topo.misc.distribution import DSF_WeightedAverage, DSF_VonMisesFit, DSF_BimodalVonMisesFit
from topo.pattern import GaussiansCorner, Gaussian, RawRectangle, Composite, Constant
from topo.analysis.featureresponses import ReverseCorrelation
from topo.plotting.plotgroup import create_plotgroup, plotgroups

from topo.plotting.plotgroup import UnitMeasurementCommand,ProjectionSheetMeasurementCommand
from topo.analysis.featureresponses import Feature, PatternPresenter, MeasureResponseCommand
from topo.analysis.featureresponses import SinusoidalMeasureResponseCommand, PositionMeasurementCommand, SingleInputResponseCommand
from topo.base.patterngenerator import PatternGenerator
from topo.command import pattern_present

from topo.misc.patternfn import line


# Helper function for save_plotgroup
def _equivalent_for_plotgroup_update(p1,p2):
    """
    Helper function for save_plotgroup.

    Comparison operator for deciding whether make_plots(update==False) is
    safe for one plotgroup if the other has already been updated.

    Treats plotgroups as the same if the specified list of attributes
    (if present) match in both plotgroups.
    """

    attrs_to_check = ['pre_plot_hooks','keyname','sheet','x','y','projection','input_sheet','density','coords']

    for a in attrs_to_check:
        if hasattr(p1,a) or hasattr(p2,a):
            if not (hasattr(p1,a) and hasattr(p2,a) and getattr(p1,a)== getattr(p2,a)):
                return False

    return True



class save_plotgroup(ParameterizedFunction):
    """
    Convenience command for saving a set of plots to disk.  Examples:

      save_plotgroup("Activity")
      save_plotgroup("Orientation Preference")
      save_plotgroup("Projection",projection=topo.sim['V1'].projections('Afferent'))

    Some plotgroups accept optional parameters, which can be passed
    like projection above.
    """

    equivalence_fn = param.Callable(default=_equivalent_for_plotgroup_update,doc="""
        Function to call on plotgroups p1,p2 to determine if calling pre_plot_hooks
        on one of them is sufficient to update both plots.  Should return False
        unless the commands are exact equivalents, including all relevant parameters.""")

    use_cached_results = param.Boolean(default=False,doc="""
        If True, will use the equivalence_fn to determine cases where
        the pre_plot_hooks for a plotgroup can safely be skipped, to
        avoid lengthy redundant computation.  Should usually be
        False for safety, but can be enabled for e.g. batch mode
        runs using a related batch of plots.""")

    saver_params = param.Dict(default={},doc="""
        Optional parameters to pass to the underlying PlotFileSaver object.""")


    # Class variables to cache values from previous invocations
    previous_time=[-1]
    previous_plotgroups=[]

    def __call__(self,name,**params):
        p=ParamOverrides(self,params,allow_extra_keywords=True)

        plotgroup = copy.deepcopy(plotgroups[name])

        # JABALERT: Why does a Projection plot need a Sheet parameter?
        # CB: It shouldn't, of course, since we know the sheet when we have
        # the projection object - it's just leftover from when we passed the
        # names instead. There should be an ALERT already about this somewhere
        # in projectionpanel.py or plotgroup.py (both need to be changed).
        if 'projection' in params:
            setattr(plotgroup,'sheet',params['projection'].dest)

        plotgroup._set_name(name)

        # Specified parameters that aren't parameters of
        # save_plotgroup() are set on the plotgroup
        for n,v in p.extra_keywords().items():
            plotgroup.set_param(n,v)

        # Reset plot cache when time changes
        if (topo.sim.time() != self.previous_time[0]):
            del self.previous_time[:]
            del self.previous_plotgroups[:]
            self.previous_time.append(topo.sim.time())

        # Skip update step if equivalent to prior command at this sim time
        update=True
        if p.use_cached_results:
            for g in self.previous_plotgroups:
                if p.equivalence_fn(g,plotgroup):
                    update=False
                    break

        keywords=" ".join(["%s" % (v.name if isinstance(v,param.Parameterized) else str(v)) for n,v in p.extra_keywords().items()])
        plot_description="%s%s%s" % (plotgroup.name," " if keywords else "",keywords)
        if update:
            self.previous_plotgroups.append(plotgroup)
            self.debug("%s: Running pre_plot_hooks" % plot_description)
        else:
            self.message("%s: Using cached results from pre_plot_hooks" % plot_description)

        plotgroup.make_plots(update=update)
        plotgroup.filesaver.save_to_disk(**(p.saver_params))



def decode_feature(sheet, preference_map = "OrientationPreference", axis_bounds=(0.0,1.0), cyclic=True, weighted_average=True, cropfn=lambda(x):x):
    """
    Estimate the value of a feature from the current activity pattern on a sheet.

    The specified preference_map should be measured before this
    function is called.

    If weighted_average is False, the feature value returned is the
    value of the preference_map at the maximally active location.

    If weighted_average is True, the feature value is estimated by
    weighting the preference_map by the current activity level, and
    averaging the result across all units in the sheet.  The
    axis_bounds specify the allowable range of the feature values in
    the preference_map.  If cyclic is true, a vector average is used;
    otherwise an arithmetic weighted average is used.

    For instance, if preference_map is OrientationPreference (a cyclic
    quantity), then the result will be the vector average of the
    activated orientations.  For an orientation map this value should
    be an estimate of the orientation present on the input.

    If desired, a cropfn can be supplied that will narrow the analysis
    down to a specific region of the array; this function will be
    applied to the preference_map and to the activity array before
    decoding.  Examples:

    Decode whole area:

       decode_feature(topo.sim["V1"])

    Decode left half only:

       r,c = topo.sim["V1"].activity.shape
       lefthalf  = lambda(x): x[:,0:c/2]
       righthalf = lambda(x): x[:,c/2:]

       decode_feature(topo.sim["V1"], cropfn=lefthalf)

    """

    d = Distribution(axis_bounds, cyclic)

    if not (preference_map in sheet.sheet_views):
        topo.sim.warning(preference_map + " should be measured before calling decode_feature.")
    else:
        v = sheet.sheet_views[preference_map]
        for (p,a) in zip(cropfn(v.view()[0]).ravel(),
                         cropfn(sheet.activity).ravel()): d.add({p:a})

    res = DSF_WeightedAverage()(d) if weighted_average else DSF_MaxValue()(d)
    return res['']['preference']



def update_activity():
    """
    Make a map of neural activity available for each sheet, for use in template-based plots.

    This command simply asks each sheet for a copy of its activity
    matrix, and then makes it available for plotting.  Of course, for
    some sheets providing this information may be non-trivial, e.g. if
    they need to average over recent spiking activity.
    """
    for sheet in topo.sim.objects(Sheet).values():
        activity_copy = array(sheet.activity)
        new_view = SheetView((activity_copy,sheet.bounds),
                              sheet.name,sheet.precedence,topo.sim.time(),sheet.row_precedence)
        sheet.sheet_views['Activity']=new_view


pg = create_plotgroup(name='Activity',category='Basic',
             doc='Plot the activity for all Sheets.', auto_refresh=True,
             pre_plot_hooks=[update_activity], plot_immediately=True)
pg.add_plot('Activity',[('Strength','Activity')])


def update_rgb_activities():
    """
    Make available Red, Green, and Blue activity matrices for all appropriate sheets.
    """
    for sheet in topo.sim.objects(Sheet).values():
        for c in ['Red','Green','Blue']:
            # should this ensure all of r,g,b are present?
            if hasattr(sheet,'activity_%s'%c.lower()):
                activity_copy = getattr(sheet,'activity_%s'%c.lower()).copy()
                new_view = SheetView((activity_copy,sheet.bounds),
                                     sheet.name,sheet.precedence,topo.sim.time(),sheet.row_precedence)
                sheet.sheet_views['%sActivity'%c]=new_view


pg = create_plotgroup(name='RGB',category='Other',
             doc='Combine and plot the red, green, and blue activity for all appropriate Sheets.', auto_refresh=True,
             pre_plot_hooks=[update_rgb_activities], plot_immediately=True)
pg.add_plot('RGB',[('Red','RedActivity'),('Green','GreenActivity'),('Blue','BlueActivity')])



class update_connectionfields(UnitMeasurementCommand):
    """A callable Parameterized command for measuring or plotting a unit from a Projection."""

    # Force plotting of all CFs, not just one Projection
    projection = param.ObjectSelector(default=None,constant=True)


pg= create_plotgroup(name='Connection Fields',category="Basic",
                     doc='Plot the weight strength in each ConnectionField of a specific unit of a Sheet.',
                     pre_plot_hooks=[update_connectionfields],
                     plot_immediately=True, normalize='Individually', situate=True)
pg.add_plot('Connection Fields',[('Strength','Weights')])



class update_projection(UnitMeasurementCommand):
    """A callable Parameterized command for measuring or plotting units from a Projection."""


pg= create_plotgroup(name='Projection',category="Basic",
           doc='Plot the weights of an array of ConnectionFields in a Projection.',
           pre_plot_hooks=[update_projection],
           plot_immediately=False, normalize='Individually',sheet_coords=True)
pg.add_plot('Projection',[('Strength','Weights')])



class update_projectionactivity(ProjectionSheetMeasurementCommand):
    """
    Add SheetViews for all of the Projections of the ProjectionSheet
    specified by the sheet parameter, for use in template-based plots.
    """

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('sheet').compute_default()
        s = p.sheet
        if s is not None:
            for conn in s.in_connections:
                if not isinstance(conn,Projection):
                    topo.sim.debug("Skipping non-Projection "+conn.name)
                else:
                    v = conn.get_projection_view(topo.sim.time())
######################################################################
## CEBALERT: when a TemplatePlot tp is created from a ProjectionView
## pv, tp.plot_src_name comes ultimately from pv.projection.src.name,
## but tp.plot_bounding_box comes from pv.projection.dest.bounds. So,
## we get a plot with mismatched src_name and bounds. Fixing that here
## is not the correct solution, but it allows the Projection Activity
## GUI window to work.
                    v.src_name = v.projection.dest.name
## JABALERT: Similarly, probably not the right thing to do, but makes
## the name of the src available for the plot to be labelled.
                    v.proj_src_name = v.projection.src.name
######################################################################
                    key = ('ProjectionActivity',v.projection.dest.name,v.projection.name)
                    v.projection.dest.sheet_views[key] = v


pg =  create_plotgroup(name='Projection Activity',category="Basic",
             doc='Plot the activity in each Projection that connects to a Sheet.',
             pre_plot_hooks=[update_projectionactivity.instance()],
             plot_immediately=True, normalize='Individually',auto_refresh=True)
pg.add_plot('Projection Activity',[('Strength','ProjectionActivity')])


class measure_rfs(SingleInputResponseCommand):
    """
    Map receptive fields by reverse correlation.

    Presents a large collection of input patterns, typically pixel by pixel on
    and off, keeping track of which units in the specified input_sheet were
    active when each unit in other Sheets in the simulation was active.  This
    data can then be used to plot receptive fields for each unit.  Note that
    the results are true receptive fields, not the connection fields usually
    presented in lieu of receptive fields, because they take all circuitry in
    between the input and the target unit into account.

    Note also that it is crucial to set the scale parameter properly when using
    units with a hard activation threshold (as opposed to a smooth sigmoid),
    because the input pattern used here may not be a very effective way to
    drive the unit to activate.  The value should be set high enough that the
    target units activate at least some of the time there is a pattern on the
    input.
    """
    static_parameters = param.List(default=["offset","size"])

    sampling_interval = param.Integer(default=1,bounds=(1,None),doc="""
    	The sampling interval determines the number of units in the input sheet
    	that are sampled per presentation.  The higher the value the coarser
    	the receptive field measurement will be.""")

    sampling_area = param.NumericTuple(doc="""
    	Dimensions of the area to be sampled during reverse correlation
        measured in units x and y on the input sheet centered around the origin
        and expressed as a tuple (x,y).""")

    __abstract = True

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('input_sheet').compute_default()
        x=ReverseCorrelation(self._feature_list(p),input_sheet=p.input_sheet)
        static_params = dict([(s,p[s]) for s in p.static_parameters])

        if p.duration is not None:
            p.pattern_presenter.duration=p.duration
        if p.apply_output_fns is not None:
            p.pattern_presenter.apply_output_fns=p.apply_output_fns
        x.collect_feature_responses(p.pattern_presenter,static_params,p.display,self._feature_list(p))

    def _feature_list(self,p):

        left, bottom, right, top = p.input_sheet.nominal_bounds.lbrt()
        sheet_density = float(p.input_sheet.nominal_density)
        x_units,y_units = p.input_sheet.shape

        unit_size = 1.0 / sheet_density
        p.size = unit_size * p.sampling_interval

        if p.sampling_area == (0,0):
            p.sampling_area = (x_units,y_units)

        y_range = (top - (unit_size * floor((y_units-p.sampling_area[1])/2)), bottom + (unit_size * ceil((y_units-p.sampling_area[1])/2)))
        x_range = (right - (unit_size * floor((x_units-p.sampling_area[0])/2)), left + (unit_size * ceil((x_units-p.sampling_area[0])/2)))

        return [Feature(name="x", range=x_range, step=-p.size),
                Feature(name="y", range=y_range, step=-p.size),
                Feature(name="scale", range=(-p.scale, p.scale), step=p.scale*2)]

pg = create_plotgroup(name='RF Projection',category='Other',
    doc='Measure receptive fields.',
    pre_plot_hooks=[measure_rfs.instance(display=True,
    pattern_presenter=PatternPresenter(RawRectangle(size=0.01,aspect_ratio=1.0)))],
    normalize='Individually')

pg.add_plot('RFs',[('Strength','RFs')])


# Helper function for measuring direction maps
def compute_orientation_from_direction(current_values):
    """
    Return the orientation corresponding to the given direction.

    Wraps the value to be in the range [0,pi), and rounds it slightly
    so that wrapped values are precisely the same (to avoid biases
    caused by vector averaging with keep_peak=True).

    Note that in very rare cases (1 in 10^-13?), rounding could lead
    to different values for a wrapped quantity, and thus give a
    heavily biased orientation map.  In that case, just choose a
    different number of directions to test, to avoid that floating
    point boundary.
    """
    return round(((dict(current_values)['direction'])+(pi/2)) % pi,13)



class measure_sine_pref(SinusoidalMeasureResponseCommand):
    """
    Measure preferences for sine gratings in various combinations.
    Can measure orientation, spatial frequency, spatial phase,
    ocular dominance, horizontal phase disparity, color hue, motion
    direction, and speed of motion.

    In practice, this command is useful for any subset of the possible
    combinations, but if all combinations are included, the number of
    input patterns quickly grows quite large, much larger than the
    typical number of patterns required for an entire simulation.
    Thus typically this command will be used for the subset of
    dimensions that need to be evaluated together, while simpler
    special-purpose routines are provided below for other dimensions
    (such as hue and disparity).
    """

    num_ocularity = param.Integer(default=1,bounds=(1,None),softbounds=(1,3),doc="""
        Number of ocularity values to test; set to 1 to disable or 2 to enable.""")

    num_disparity = param.Integer(default=1,bounds=(1,None),softbounds=(1,48),doc="""
        Number of disparity values to test; set to 1 to disable or e.g. 12 to enable.""")

    num_hue = param.Integer(default=1,bounds=(1,None),softbounds=(1,48),doc="""
        Number of hues to test; set to 1 to disable or e.g. 8 to enable.""")

    num_direction = param.Integer(default=0,bounds=(0,None),softbounds=(0,48),doc="""
        Number of directions to test.  If nonzero, overrides num_orientation,
        because the orientation is calculated to be perpendicular to the direction.""")

    num_speeds = param.Integer(default=4,bounds=(0,None),softbounds=(0,10),doc="""
        Number of speeds to test (where zero means only static patterns).
        Ignored when num_direction=0.""")

    max_speed = param.Number(default=2.0/24.0,bounds=(0,None),doc="""
        The maximum speed to measure (with zero always the minimum).""")

    subplot = param.String("Orientation")


    def _feature_list(self,p):
        # Always varies frequency and phase; everything else depends on parameters.

        features = \
            [Feature(name="frequency",values=p.frequencies,
                    preference_fn=DSF_WeightedAverage())]

        if p.num_direction==0: features += \
            [Feature(name="orientation",range=(0.0,pi),step=pi/p.num_orientation,
                            cyclic=True, preference_fn=self.preference_fn)]

        features += \
            [Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True,
                     preference_fn=DSF_WeightedAverage( value_scale=(0., 1/2.0/pi) ))]

        if p.num_ocularity>1: features += \
            [Feature(name="ocular",range=(0.0,1.0),step=1.0/p.num_ocularity)]

        if p.num_disparity>1: features += \
            [Feature(name="phasedisparity",range=(0.0,2*pi),step=2*pi/p.num_disparity,cyclic=True)]

        if p.num_hue>1: features += \
            [Feature(name="hue",range=(0.0,1.0),step=1.0/p.num_hue,cyclic=True)]

        if p.num_direction>0 and p.num_speeds==0: features += \
            [Feature(name="speed",values=[0],cyclic=False)]

        if p.num_direction>0 and p.num_speeds>0: features += \
            [Feature(name="speed",range=(0.0,p.max_speed),step=float(p.max_speed)/p.num_speeds,cyclic=False)]

        if p.num_direction>0:
            # Compute orientation from direction
            dr = Feature(name="direction",range=(0.0,2*pi),step=2*pi/p.num_direction,cyclic=True)
            or_values = list(set([compute_orientation_from_direction([("direction",v)]) for v in dr.values]))
            features += [dr, \
                 Feature(name="orientation",range=(0.0,pi),values=or_values,cyclic=True,
                         compute_fn=compute_orientation_from_direction,preference_fn=self.preference_fn)]

        return features


# Here as the simplest possible example; could be moved elsewhere.
class measure_or_pref(SinusoidalMeasureResponseCommand):
    """Measure an orientation preference map by collating the response to patterns."""

    subplot = param.String("Orientation")

    preference_fn = param.ClassSelector( DistributionStatisticFn,
        default=DSF_WeightedAverage(value_scale=(0.0,1.0/pi)), doc="""
        Function that will be used to analyze the distributions of unit
        responses. Sets value_scale to normalize orientation preference
        values.""" )

    def _feature_list(self,p):

        return [Feature(name="frequency",values=p.frequencies),
                Feature(name="orientation",range=(0.0,pi),step=pi/p.num_orientation,
                        preference_fn=self.preference_fn,cyclic=True),
                Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True)]


pg= create_plotgroup(name='Orientation Preference',category="Preference Maps",
             doc='Measure preference for sine grating orientation.',
             pre_plot_hooks=[measure_sine_pref.instance(
                 preference_fn=DSF_WeightedAverage( value_scale=(0., 1./pi) ))] )
pg.add_plot('Orientation Preference',[('Hue','OrientationPreference')])
pg.add_plot('Orientation Preference&Selectivity',
            [('Hue','OrientationPreference'), ('Confidence','OrientationSelectivity')])
pg.add_plot('Orientation Selectivity',[('Strength','OrientationSelectivity')])
pg.add_plot('Phase Preference',[('Hue','PhasePreference')])
pg.add_plot('Phase Selectivity',[('Strength','PhaseSelectivity')])
pg.add_static_image('Color Key','command/or_key_white_vert_small.png')


pg= create_plotgroup(name='vonMises Orientation Preference',category="Preference Maps",
             doc='Measure preference for sine grating orientation using von Mises fit.',
             pre_plot_hooks=[measure_sine_pref.instance(
                 preference_fn=DSF_VonMisesFit( value_scale=(0., 1./pi) ),
                 num_orientation=16)])
pg.add_plot('Orientation Preference',[('Hue','OrientationPreference')])
pg.add_plot('Orientation Preference&Selectivity',
            [('Hue','OrientationPreference'), ('Confidence','OrientationSelectivity')])
pg.add_plot('Orientation Selectivity',[('Strength','OrientationSelectivity')])
pg.add_plot('Phase Preference',[('Hue','PhasePreference')])
pg.add_plot('Phase Selectivity',[('Strength','PhaseSelectivity')])
pg.add_static_image('Color Key','command/or_key_white_vert_small.png')


pg= create_plotgroup(name='Bimodal Orientation Preference', category="Preference Maps",
             doc='Measure preference for sine grating orientation using bimodal von Mises fit.',
             pre_plot_hooks=[measure_sine_pref.instance(
                 preference_fn=DSF_BimodalVonMisesFit( value_scale=(0., 1./pi) ),
                 num_orientation=16)])
pg.add_plot('Orientation Preference',[('Hue','OrientationPreference')])
pg.add_plot('Orientation Preference&Selectivity',
            [('Hue','OrientationPreference'), ('Confidence','OrientationSelectivity')])
pg.add_plot('Orientation Selectivity',[('Strength','OrientationSelectivity')])
pg.add_plot('Second Orientation Preference', [('Hue','OrientationMode2Preference')])
pg.add_plot('Second Orientation Preference&Selectivity',
            [('Hue','OrientationMode2Preference'), ('Confidence','OrientationMode2Selectivity')])
pg.add_plot('Second Orientation Selectivity', [('Strength','OrientationMode2Selectivity')])
pg.add_static_image('Color Key', 'command/or_key_white_vert_small.png')


pg = create_plotgroup(name='Two Orientation Preferences',category='Preference Maps',
    doc='Display the two most preferred orientations for each units, using bimodal von Mises fit.',
    pre_plot_hooks=[measure_sine_pref.instance(
         preference_fn=DSF_BimodalVonMisesFit(), num_orientation=16)])
pg.add_plot( 'Two Orientation Preferences', [
		( 'Or1',	'OrientationPreference' ),
		( 'Sel1',	'OrientationSelectivity' ),
		( 'Or2',	'OrientationMode2Preference' ),
		( 'Sel2',	'OrientationMode2Selectivity' )
])
pg.add_static_image('Color Key','command/two_or_key_vert.png')


pg= create_plotgroup(name='Spatial Frequency Preference',category="Preference Maps",
             doc='Measure preference for sine grating orientation and frequency.',
             pre_plot_hooks=[measure_sine_pref.instance(
                 preference_fn=DSF_WeightedAverage( value_scale=(0., 1./pi) ))] )
pg.add_plot('Spatial Frequency Preference',[('Strength','FrequencyPreference')])
pg.add_plot('Spatial Frequency Selectivity',[('Strength','FrequencySelectivity')])
# Just calls measure_sine_pref to plot different maps.


class measure_od_pref(SinusoidalMeasureResponseCommand):
    """Measure an ocular dominance preference map by collating the response to patterns."""

    def _feature_list(self,p):
        return [Feature(name="frequency",values=p.frequencies),
                Feature(name="orientation",range=(0.0,pi),step=pi/p.num_orientation,cyclic=True),
                Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True),
                Feature(name="ocular",range=(0.0,1.0),values=[0.0,1.0])]

pg= create_plotgroup(name='Ocular Preference',category="Preference Maps",
             doc='Measure preference for sine gratings between two eyes.',
             pre_plot_hooks=[measure_sine_pref.instance()])
pg.add_plot('Ocular Preference',[('Strength','OcularPreference')])
pg.add_plot('Ocular Selectivity',[('Strength','OcularSelectivity')])




class measure_phasedisparity(SinusoidalMeasureResponseCommand):
    """Measure a phase disparity preference map by collating the response to patterns."""

    num_disparity = param.Integer(default=12,bounds=(1,None),softbounds=(1,48),
                                  doc="Number of disparity values to test.")

    orientation = param.Number(default=pi/2,softbounds=(0.0,2*pi),doc="""
        Orientation of the test pattern; typically vertical to measure
        horizontal disparity.""")

    static_parameters = param.List(default=["orientation","scale","offset"])

    def _feature_list(self,p):
        return [Feature(name="frequency",values=p.frequencies),
                Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True),
                Feature(name="phasedisparity",range=(0.0,2*pi),step=2*pi/p.num_disparity,cyclic=True)]


pg= create_plotgroup(name='PhaseDisparity Preference',category="Preference Maps",doc="""
    Measure preference for sine gratings at a specific orentation differing in phase
    between two input sheets.""",
             pre_plot_hooks=[measure_phasedisparity.instance()],normalize='Individually')
pg.add_plot('PhaseDisparity Preference',[('Hue','PhasedisparityPreference')])
pg.add_plot('PhaseDisparity Preference&Selectivity',
            [('Hue','PhasedisparityPreference'), ('Confidence','PhasedisparitySelectivity')])
pg.add_plot('PhaseDisparity Selectivity',[('Strength','PhasedisparitySelectivity')])
pg.add_static_image('Color Key','command/disp_key_white_vert_small.png')



class measure_dr_pref(SinusoidalMeasureResponseCommand):
    """Measure a direction preference map by collating the response to patterns."""

    num_phase = param.Integer(default=12)

    num_direction = param.Integer(default=6,bounds=(1,None),softbounds=(1,48),
                                  doc="Number of directions to test.")

    num_speeds = param.Integer(default=4,bounds=(0,None),softbounds=(0,10),doc="""
        Number of speeds to test (where zero means only static patterns).""")

    max_speed = param.Number(default=2.0/24.0,bounds=(0,None),doc="""
        The maximum speed to measure (with zero always the minimum).""")

    subplot = param.String("Direction")

    preference_fn = param.ClassSelector( DistributionStatisticFn,
        default=DSF_WeightedAverage(value_scale=(0.0,1.0/(2*pi))), doc="""
        Function that will be used to analyze the distributions of
        unit responses. Sets value_scale to normalize direction
        preference values.""" )


    def _feature_list(self,p):
        # orientation is computed from direction
        dr = Feature(name="direction",range=(0.0,2*pi),step=2*pi/p.num_direction,cyclic=True)
        or_values = list(set([compute_orientation_from_direction([("direction",v)]) for v in dr.values]))

        return [Feature(name="speed",values=[0],cyclic=False) if p.num_speeds is 0 else
                Feature(name="speed",range=(0.0,p.max_speed),step=float(p.max_speed)/p.num_speeds,cyclic=False),
                Feature(name="frequency",values=p.frequencies),
                Feature(name="direction",range=(0.0,2*pi),step=2*pi/p.num_direction,cyclic=True,
                        preference_fn=self.preference_fn),
                Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True),
                Feature(name="orientation",range=(0.0,pi),values=or_values,cyclic=True,
                        compute_fn=compute_orientation_from_direction)]


pg= create_plotgroup(name='Direction Preference',category="Preference Maps",
             doc='Measure preference for sine grating movement direction.',
             pre_plot_hooks=[measure_dr_pref.instance()])
pg.add_plot('Direction Preference',[('Hue','DirectionPreference')])
pg.add_plot('Direction Preference&Selectivity',[('Hue','DirectionPreference'),
                                                ('Confidence','DirectionSelectivity')])
pg.add_plot('Direction Selectivity',[('Strength','DirectionSelectivity')])
pg.add_plot('Speed Preference',[('Strength','SpeedPreference')])
pg.add_plot('Speed Selectivity',[('Strength','SpeedSelectivity')])
pg.add_static_image('Color Key','command/dr_key_white_vert_small.png')



class measure_hue_pref(SinusoidalMeasureResponseCommand):
    """Measure a hue preference map by collating the response to patterns."""

    num_phase = param.Integer(default=12)

    num_hue = param.Integer(default=8,bounds=(1,None),softbounds=(1,48),
                            doc="Number of hues to test.")

    subplot = param.String("Hue")

    # For backwards compatibility; not sure why it needs to differ from the default
    static_parameters = param.List(default=[])

    def _feature_list(self,p):
        return [Feature(name="frequency",values=p.frequencies),
                Feature(name="orientation",range=(0,pi),step=pi/p.num_orientation,cyclic=True),
                Feature(name="hue",range=(0.0,1.0),step=1.0/p.num_hue,cyclic=True),
                Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True)]


pg= create_plotgroup(name='Hue Preference',category="Preference Maps",
             doc='Measure preference for colors.',
             pre_plot_hooks=[measure_hue_pref.instance()],normalize='Individually')
pg.add_plot('Hue Preference',[('Hue','HuePreference')])
pg.add_plot('Hue Preference&Selectivity',[('Hue','HuePreference'), ('Confidence','HueSelectivity')])
pg.add_plot('Hue Selectivity',[('Strength','HueSelectivity')])



gaussian_corner = Composite(
    operator = maximum, generators = [
        Gaussian(size = 0.06,orientation=0,aspect_ratio=7,x=0.3),
        Gaussian(size = 0.06,orientation=pi/2,aspect_ratio=7,y=0.3)])


class measure_second_or_pref(SinusoidalMeasureResponseCommand):
    """Measure the secondary  orientation preference maps."""

    num_orientation	= param.Integer( default=16, bounds=(1,None), softbounds=(1,64),
                                    doc="Number of orientations to test.")
    true_peak 	 	= param.Boolean( default=True, doc="""If set the second
	    orientation response is computed on the true second mode of the
	    orientation distribution, otherwise is just the second maximum response""" )

    subplot		= param.String("Second Orientation")

    def _feature_list(self, p):
    	fs	= [ Feature(name="frequency", values=p.frequencies) ]
    	if p.true_peak:
	    fs.append(
		Feature(name="orientation", range=(0.0, pi), step=pi/p.num_orientation,
                    cyclic=True, preference_fn=DSF_BimodalPeaks() ) )
	else:
	    fs.append(
		Feature(name="orientation", range=(0.0, pi), step=pi/p.num_orientation,
                    cyclic=True, preference_fn=DSF_BimodalPeaks() ) )
	fs.append( Feature(name="phase", range=(0.0, 2*pi), step=2*pi/p.num_phase, cyclic=True) )

	return fs


pg= create_plotgroup(name='Second Orientation Preference', category="Preference Maps",
             doc='Measure the second preference for sine grating orientation.',
             pre_plot_hooks=[measure_second_or_pref.instance( true_peak=False )])
pg.add_plot('Second Orientation Preference', [('Hue','OrientationMode2Preference')])
pg.add_plot('Second Orientation Preference&Selectivity',
            [('Hue','OrientationMode2Preference'), ('Confidence','OrientationMode2Selectivity')])
pg.add_plot('Second Orientation Selectivity', [('Strength','OrientationMode2Selectivity')])
pg.add_static_image('Color Key', 'command/or_key_white_vert_small.png')


pg= create_plotgroup(name='Second Peak Orientation Preference',category="Preference Maps",
             doc='Measure the second peak preference for sine grating orientation.',
             pre_plot_hooks=[measure_second_or_pref.instance( true_peak=True )])
pg.add_plot('Second Peak Orientation Preference', [('Hue','OrientationMode2Preference')])
pg.add_plot('Second Peak Orientation Preference&Selectivity',
            [('Hue','OrientationMode2Preference'), ('Confidence','OrientationMode2Selectivity')])
pg.add_plot('Second Peak Orientation Selectivity', [('Strength','OrientationMode2Selectivity')])
pg.add_static_image('Color Key','command/or_key_white_vert_small.png')


pg = create_plotgroup(name='Two Peaks Orientation Preferences',category='Preference Maps',
    doc="""Display the two most preferred orientations for all units with a
    multimodal orientation preference distribution.""",
    pre_plot_hooks=[
    		measure_second_or_pref.instance(num_orientation=16, true_peak=True)
])
pg.add_plot( 'Two Peaks Orientation Preferences', [
		( 'Or1',	'OrientationPreference' ),
		( 'Sel1',	'OrientationSelectivity' ),
		( 'Or2',	'OrientationMode2Preference' ),
		( 'Sel2',	'OrientationMode2Selectivity' )
])
pg.add_static_image('Color Key','command/two_or_key_vert.png')

class measure_corner_or_pref(PositionMeasurementCommand):
    """Measure a corner preference map by collating the response to patterns."""

    scale = param.Number(default=1.0)

    divisions=param.Integer(default=10)

    pattern_presenter = param.Callable(PatternPresenter(gaussian_corner,apply_output_fns=False,duration=1.0))

    x_range=param.NumericTuple((-1.2,1.2))

    y_range=param.NumericTuple((-1.2,1.2))

    num_orientation = param.Integer(default=4,bounds=(1,None),softbounds=(1,24),
                                    doc="Number of orientations to test.")

    # JABALERT: Presumably this should be omitted, so that size is included?
    static_parameters = param.List(default=["scale","offset"])

    def _feature_list(self,p):
        width =1.0*p.x_range[1]-p.x_range[0]
        height=1.0*p.y_range[1]-p.y_range[0]
        return [
            Feature(name="x",range=p.x_range,step=width/p.divisions,preference_fn=self.preference_fn),
            Feature(name="y",range=p.y_range,step=height/p.divisions,preference_fn=self.preference_fn),
            Feature(name="orientation",range=(0,2*pi),step=2*pi/p.num_orientation,cyclic=True,
                preference_fn=DSF_WeightedAverage(value_scale=(0., 1/2.0/pi))
            )]


pg= create_plotgroup(name='Corner OR Preference',category="Preference Maps",
             doc='Measure orientation preference for corner shape (or other complex stimuli that cannot be represented as fullfield patterns).',
             pre_plot_hooks=[measure_corner_or_pref.instance(
                 preference_fn=DSF_WeightedAverage())],
             normalize='Individually')
pg.add_plot('Corner Orientation Preference',[('Hue','OrientationPreference')])
pg.add_plot('Corner Orientation Preference&Selectivity',[('Hue','OrientationPreference'),
                                                   ('Confidence','OrientationSelectivity')])
pg.add_plot('Corner Orientation Selectivity',[('Strength','OrientationSelectivity')])


class measure_corner_angle_pref(PositionMeasurementCommand):
    """Generate the preference map for angle shapes, by collating the response to patterns."""

    scale = param.Number(default=1.0)

    size = param.Number(default=0.2)

    positions = param.Integer(default=6)

    x_range = param.NumericTuple((-1.0, 1.0))

    y_range = param.NumericTuple((-1.0, 1.0))

    num_or = param.Integer(default=4,bounds=(1,None),softbounds=(1,24),doc=
        "Number of orientations to test.")

    angle_0 = param.Number(default=0.25*pi,bounds=(0.0,pi),softbounds=(0.0,0.5*pi),doc=
        "First angle to test.")

    angle_1 = param.Number(default=0.75*pi,bounds=(0.0,pi),softbounds=(0.5*pi,pi),doc=
        "Last angle to test.")

    num_angle=param.Integer(default=4,bounds=(1,None),softbounds=(1,12),doc=
        "Number of angles to test.")

    key_img_fname=param.Filename(default='command/key_angles.png',doc=
        "Name of the file with the image used to code angles with hues.")

    pattern_presenter=PatternPresenter(GaussiansCorner(aspect_ratio=4.0,cross=0.85),apply_output_fns=False,duration=1.0)

    static_parameters = param.List( default=[ "size", "scale", "offset" ] )



    def _feature_list( self, p ):
    	"""Return the list of features to vary, generate hue code static image"""
        x_step	= ( p.x_range[1]-p.x_range[0] ) / float( p.positions - 1 )
        y_step	= ( p.y_range[1]-p.y_range[0] ) / float( p.positions - 1 )
	o_step	= 2.0*pi / p.num_or
	if p.angle_0 < p.angle_1:
            angle_0 = p.angle_0
            angle_1 = p.angle_1
	else:
            angle_0 = p.angle_1
            angle_1 = p.angle_0
	a_range	= ( angle_0, angle_1 )
	a_step	= ( angle_1 - angle_0 ) / float( p.num_angle - 1 )
	self._make_key_image( p )
        return [
            Feature( name="x",           range=p.x_range, step=x_step ),
            Feature( name="y",           range=p.y_range, step=y_step ),
            Feature( name="orientation", range=(0, 2*pi), step=o_step, cyclic=True ),
            Feature( name="angle",       range=a_range,   step=a_step,
                    preference_fn=DSF_WeightedAverage( value_scale=( -angle_0, 1./(angle_1-angle_0) ) ) )
	]


    def _make_key_image( self, p ):
    	"""Generate the image with keys to hues used to code angles
	   the image is saved on-the-fly, in order to fit the current
	   choice of angle range
	"""
	width	= 60
	height	= 300
	border	= 6
	n_a	= 7
	angle_0	= p.angle_0
	angle_1	= p.angle_1
	a_step	= 0.5 * ( angle_1 - angle_0 ) / float( n_a )
	x_0	= border
	x_1	= ( width - border ) / 2
	x_a	= x_1 + 2 * border
	y_use	= height - 2 * border
	y_step	= y_use / float( n_a )
	y_d	= int( float( 0.5 * y_step ) )
	y_0	= border + y_d
	l	= 15

	hues	= [ "hsl(%2d,100%%,50%%)" % h		for h in range( 0, 360, 360 / n_a ) ]
	angles	= [ 0.5*angle_0 + a_step * a		for a in range( n_a ) ]
	y_pos	= [ int( round( y_0 + y * y_step ) )	for y in range( n_a ) ]
	deltas	= [ ( int( round( l * cos( a ) ) ), int( round( l * sin( a ) ) ) )
							for a in angles ]
	lb_img	= Image.new( "RGB", ( width, height ), "white" )
	dr_img	= ImageDraw.Draw( lb_img )

	for h, y, d	in zip( hues, y_pos, deltas ):
		dr_img.rectangle( [ ( x_0, y - y_d ), ( x_1, y + y_d ) ], fill = h )
		dr_img.line( [ ( x_a, y ), ( x_a + d[ 0 ], y + d[ 1 ] ) ], fill = "black" )
		dr_img.line( [ ( x_a, y ), ( x_a + d[ 0 ], y - d[ 1 ] ) ], fill = "black" )
	
	lb_img.save( p.key_img_fname )

	#return( p.key_img_fname.default )
		

pg= create_plotgroup(name='Corner Angle Preference',category="Preference Maps",
             doc='Measure preference for angles in corner shapes',
             normalize='Individually')
pg.pre_plot_hooks=[ measure_corner_angle_pref.instance() ]
pg.add_plot('Corner Angle Preference',[('Hue','AnglePreference')])
pg.add_plot('Corner Angle Preference&Selectivity',[('Hue','AnglePreference'),
                                                   ('Confidence','AngleSelectivity')])
pg.add_plot('Corner Angle Selectivity',[('Strength','AngleSelectivity')])
pg.add_plot('Corner Orientation Preference',[('Hue','OrientationPreference')])
pg.add_plot('Corner Orientation Preference&Selectivity',[('Hue','OrientationPreference'),
                                                   ('Confidence','OrientationSelectivity')])
pg.add_plot('Corner Orientation Selectivity',[('Strength','OrientationSelectivity')])
pg.add_static_image( 'Hue Code', measure_corner_angle_pref.instance().key_img_fname )



class PatternPresenter2(param.Parameterized):

    apply_output_fns = param.Boolean(default = True,
        doc = """When presenting a pattern, whether to apply each
        sheet's output function.  If False, for many networks the
        response will be linear, which requires fewer test patterns to
        measure a meaningful response, but it may not correspond to the
        actual preferences of each neuron under other conditions. If
        True, callers will need to ensure that the input patterns are
        in a suitable range to drive the neurons to generate meaningful
        output, because e.g. a threshold-based output function might
        result in no activity for inputs that are too weak..""")

    duration = param.Number(default = 1.0,
        doc = """Amount of simulation time for which to present each
        test pattern. By convention, most Topographica example files
        are
        designed to have a suitable activity pattern computed by the
        default time, but the duration will need to be changed for
        other models that do not follow that convention or if a
        linear response is desired.""")

    # CEBALERT: generator_sheets=[] is probably a surprising way of
    # actually getting all the generator sheets.
    generator_sheets = param.List(default = [],
        doc="""The set of GeneratorSheets onto which patterns will be
        drawn. By default (i.e. for an empty list), all GeneratorSheets
        in the simulation will be used.""")

    pattern_generator = param.Parameter(default=Constant(),
        doc = """The PatternGenerator that will be drawn on the generator
        sheets (the parameters of the pattern_generator are specified
        during calls).""")


    def __call__(self, features_values, param_dict):

        for param, value in param_dict.iteritems():
            setattr(self.pattern_generator, param, value)

        for feature, value in features_values.iteritems():
            setattr(self.pattern_generator, feature, value)

        all_input_sheet_names = topo.sim.objects(GeneratorSheet).keys()

        if len(self.generator_sheets) > 0:
            input_sheet_names = [sheet.name for sheet in self.generator_sheets]
        else:
            input_sheet_names = all_input_sheet_names

        # Copy the given generator once for every GeneratorSheet
        inputs = dict.fromkeys(input_sheet_names)
        for key in inputs.keys():
            inputs[key] = copy.deepcopy(self.pattern_generator)

        self._custom_presenter(inputs, input_sheet_names)

        # blank patterns for unused generator sheets
        for sheet_name in set(all_input_sheet_names).difference(set(input_sheet_names)):
            inputs[sheet_name] = Constant(scale=0)

        pattern_present(inputs, self.duration, plastic=False, apply_output_fns=self.apply_output_fns)


    def _custom_presenter(self, inputs, input_sheet_names):
        """This method provides a minimum overload for performing custom actions
        with a pattern presenter."""



class frequency_mapper(PatternGenerator):
    """Activates a generator sheet at the specified frequency (for all latencies).
    It does so by translating from a frequency to a y position and presenting a line
    at that y position (of the specified size)."""

    __abstract = True

    size = param.Number(default=0.01, bounds=(0.0,None), softbounds=(0.0,1.0),
        doc="Thickness (width) of the frequency band for every presentation.")

    frequency_spacing = param.Array(default=None,
        doc="""The spacing of the available frequency range, this allows us to define
        (and hence map) a non linear spacing by specifying the frequency value at each
        sheet unit.""")


    def __init__(self, **params):
        super(frequency_mapper, self).__init__(**params)
        self.frequency_spacing = round(self.frequency_spacing)


    def getFrequency(self):
        sheet_range = self.bounds.lbrt()
        y_range = sheet_range[3] - sheet_range[1]

        index = ((self.y - sheet_range[1]) / y_range) * (len(self.frequency_spacing) - 1)

        return self.frequency_spacing[index]


    def setFrequency(self, new_frequency):
        index = nonzero(self.frequency_spacing >= new_frequency)[0][0]

        sheet_range = self.bounds.lbrt()
        y_range = sheet_range[3] - sheet_range[1]

        ratio = (len(self.frequency_spacing) - 1) / y_range

        y = (index / ratio) + sheet_range[1]
        setattr(self, 'y', y)


    frequency = property(getFrequency, setFrequency, "The frequency at which to present.")


    def function(self, p):
        return line(self.pattern_y, p.size, 0.001)



class measure_frequency_preference(MeasureResponseCommand):
    """Measure a best frequency preference and selectivity map for auditory neurons."""

    display = param.Boolean(True)
    static_parameters = param.List(default=["scale", "offset"])


    def _feature_list(self,p):
        input_sheets = topo.sim.objects(GeneratorSheet).values()

        # BK-NOTE: if anyone wants to generalise this method for heterogeneous sheets, by all means do so,
        # for my personal use the additional code required to generalise was overkill.
        for sheet in range(1, len(input_sheets)-1):
            assert input_sheets[sheet].bounds == input_sheets[sheet-1].bounds
            assert input_sheets[sheet].xdensity == input_sheets[sheet-1].xdensity
            assert input_sheets[sheet].ydensity == input_sheets[sheet-1].ydensity

        divisions = float(input_sheets[0].ydensity)

        try:
            min_frequency = input_sheets[0].input_generator.min_frequency
            max_frequency = input_sheets[0].input_generator.max_frequency
            frequency_spacing = input_sheets[0].input_generator.frequency_spacing
        except AttributeError:
            min_frequency = 1
            max_frequency = int(divisions) + 1
            frequency_spacing = linspace(min_frequency, max_frequency, num=divisions+1, endpoint=True)
            self.warning("Input generator is missing min_frequency, max_frequency, or frequency_spacing - will present linearly from", str(min_frequency), "to", str(max_frequency), "instead.")

        generator = frequency_mapper(size=1.0/divisions, frequency_spacing=frequency_spacing)
        self.pattern_presenter = PatternPresenter2(pattern_generator=generator)

        return [Feature(name="frequency", range=(min_frequency,max_frequency), step=1)]


pg= create_plotgroup(name='Frequency Preference and Selectivity', category="Auditory",
    pre_plot_hooks=[measure_frequency_preference.instance()], normalize='Individually',
    doc='Measure a best frequency preference and selectivity map for auditory neurons.')

pg.add_plot('[Frequency Preference]', [('Strength','FrequencyPreference')])
pg.add_plot('[Frequency Selectivity]', [('Strength','FrequencySelectivity')])



class log_frequency_mapper(PatternGenerator):
    """Activates a generator sheet at the specified frequency (for all latencies).
        It does so by translating from a frequency to a y position and presenting a line
        at that y position (of the specified size)."""

    __abstract = True

    size = param.Number(default=0.01, bounds=(0.0,None), softbounds=(0.0,1.0),
        doc="Thickness (width) of the frequency band for every presentation.")

    frequency_spacing = param.Array(default=None,
        doc="""The spacing of the available frequency range, this allows us to define
            (and hence map) a non linear spacing by specifying the frequency value at each
            sheet unit.""")


    def __init__(self, **params):
        super(log_frequency_mapper, self).__init__(**params)
        self.frequency_spacing = round(self.frequency_spacing)


    def getFrequency(self):
        sheet_min = (self.bounds.lbrt())[1]
        index = (self.y - sheet_min) * (self.frequency_spacing.size - 1.0)
        return self.frequency_spacing[index]


    def setFrequencyBand(self, new_frequency_band):
        sheet_min = (self.bounds.lbrt())[1]
        y = sheet_min + (new_frequency_band / (self.frequency_spacing.size - 1.0))
        setattr(self, 'y', y)


    frequency = property(getFrequency, setFrequencyBand, "The log frequency band at which to present.")


    def function(self, p):
        return line(self.pattern_y, p.size, 0.001)



class measure_log_frequency_preference(MeasureResponseCommand):
    """Measure a best frequency preference and selectivity map for auditory neurons."""

    display = param.Boolean(True)
    static_parameters = param.List(default=["scale", "offset"])


    def _feature_list(self,p):
        input_sheets = topo.sim.objects(GeneratorSheet).values()

        # BK-NOTE: if anyone wants to generalise this method for heterogeneous sheets, by all means do so,
        # for my personal use the additional code required to generalise was overkill.
        for sheet in range(1, len(input_sheets)-1):
            assert input_sheets[sheet].bounds == input_sheets[sheet-1].bounds
            assert input_sheets[sheet].xdensity == input_sheets[sheet-1].xdensity
            assert input_sheets[sheet].ydensity == input_sheets[sheet-1].ydensity

        divisions = float(input_sheets[0].ydensity)

        try:
            min_frequency = input_sheets[0].input_generator.min_frequency
            max_frequency = input_sheets[0].input_generator.max_frequency
            frequency_spacing = input_sheets[0].input_generator.frequency_spacing
        except AttributeError:
            min_frequency = 1
            max_frequency = int(divisions) + 1
            frequency_spacing = linspace(min_frequency, max_frequency, num=divisions+1, endpoint=True)
            self.warning("Input generator is missing min_frequency, max_frequency, or frequency_spacing - will present linearly from", str(min_frequency), "to", str(max_frequency), "instead.")

        generator = log_frequency_mapper(size=1.0/divisions, frequency_spacing=frequency_spacing)
        self.pattern_presenter = PatternPresenter2(pattern_generator=generator)

        return [Feature(name="frequency", range=(0,divisions), step=1)]


pg= create_plotgroup(name='Log Frequency Band Preference and Selectivity', category="Auditory",
                     pre_plot_hooks=[measure_log_frequency_preference.instance()], normalize='Individually',
                     doc='Measure a best frequency preference and selectivity map for auditory neurons (presents frequencies with logarithmically increasing bandwidth).')

pg.add_plot('[Log Frequency Band Preference]', [('Strength','FrequencyPreference')])
pg.add_plot('[Log Frequency Band Selectivity]', [('Strength','FrequencySelectivity')])



class latency_mapper(PatternGenerator):
    """Activates a generator sheet at the specified latency (for all frequencies).
    It does so by translating from a latency to an x position and presenting a line
    at that x position (of the specified size)."""

    __abstract = True

    size = param.Number(default=0.01, bounds=(0.0,None), softbounds=(0.0,1.0),
        doc="Thickness (width) of the latency band for every presentation.")

    min_latency = param.Integer(default=0, bounds=(0,None), inclusive_bounds=(True,False),
        doc="""Smallest latency on the generator sheet.""")

    max_latency = param.Integer(default=100, bounds=(0,None), inclusive_bounds=(False,False),
        doc="""Largest latency on the generator sheet.""")


    def getLatency(self):
        latency_range = self.max_latency - self.min_latency

        sheet_range = self.bounds.lbrt()
        x_range = sheet_range[2] - sheet_range[0]

        ratio = latency_range / x_range

        return ((self.x - sheet_range[0]) * ratio) + self.min_latency


    def setLatency(self, new_latency):
        latency_range = self.max_latency - self.min_latency

        sheet_range = self.bounds.lbrt()
        x_range = sheet_range[2] - sheet_range[0]

        ratio = latency_range / x_range

        x = ((new_latency-self.min_latency) / ratio) + sheet_range[0]
        setattr(self, 'x', x)


    latency = property(getLatency, setLatency, "The latency at which to present.")


    def function(self, p):
        return line(self.pattern_x, p.size, 0.001)



class measure_latency_preference(MeasureResponseCommand):
    """Measure a best onset latency preference and selectivity map for auditory neurons."""

    display = param.Boolean(True)
    static_parameters = param.List(default=["scale", "offset"])

    def _feature_list(self,p):
        input_sheets = topo.sim.objects(GeneratorSheet).values()

        # BK-NOTE: if anyone wants to generalise this method for heterogeneous sheets, by all means do so,
        # for my personal use the additional code required to generalise was overkill.
        for sheet in range(1, len(input_sheets)-1):
            assert input_sheets[sheet].bounds == input_sheets[sheet-1].bounds
            assert input_sheets[sheet].xdensity == input_sheets[sheet-1].xdensity
            assert input_sheets[sheet].ydensity == input_sheets[sheet-1].ydensity

        divisions = float(input_sheets[0].xdensity)

        try:
            min_latency = input_sheets[0].input_generator.min_latency
            max_latency = input_sheets[0].input_generator.max_latency
        except AttributeError:
            min_latency = 0
            max_latency = int(divisions)
            self.warning("Input generator is missing min_latency or max_latency, setting to", str(min_latency), "&", str(max_latency),"respectively.")

        generator = latency_mapper(size=1.0/divisions, min_latency=min_latency, max_latency=max_latency)
        self.pattern_presenter = PatternPresenter2(pattern_generator=generator)

        return [Feature(name="latency", range=(min_latency,max_latency), step=1)]


pg= create_plotgroup(name='Latency Preference and Selectivity', category="Auditory",
    pre_plot_hooks=[measure_latency_preference.instance()], normalize='Individually',
    doc='Measure a best onset latency preference and selectivity map for auditory neurons.')

pg.add_plot('[Latency Preference]', [('Strength','LatencyPreference')])
pg.add_plot('[Latency Selectivity]', [('Strength','LatencySelectivity')])



import types
__all__ = list(set([k for k,v in locals().items()
                    if isinstance(v,types.FunctionType) or
                    (isinstance(v,type) and issubclass(v,ParameterizedFunction))
                    and not v.__name__.startswith('_')]))
__all__ += [
    "PatternPresenter2",
    "frequency_mapper",
    "gaussian_corner",
    "latency_mapper",
    "log_frequency_mapper",
]
