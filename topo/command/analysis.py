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

$Id$
"""
__version__='$Revision$'


from math import pi, sin, cos

import Image,ImageDraw
    
import copy

from numpy.oldnumeric import array, maximum

import param
from param.parameterized import ParameterizedFunction
from param.parameterized import ParamOverrides

import topo
from topo.base.cf import Projection
from topo.base.sheet import Sheet
from topo.base.sheetview import SheetView
from topo.misc.distribution import Distribution
from topo.pattern.basic import GaussiansCorner, RawRectangle, Line
from topo.analysis.featureresponses import ReverseCorrelation
from topo.plotting.plotgroup import create_plotgroup, plotgroups

from topo.plotting.plotgroup import UnitMeasurementCommand,ProjectionSheetMeasurementCommand
from topo.analysis.featureresponses import Feature, PatternPresenter
from topo.analysis.featureresponses import SinusoidalMeasureResponseCommand, PositionMeasurementCommand, SingleInputResponseCommand


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



def decode_feature(sheet, preference_map = "OrientationPreference", axis_bounds=(0.0,1.0), cyclic=True, weighted_average=True):
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
    """
    d = Distribution(axis_bounds, cyclic)
    
    if not (preference_map in sheet.sheet_views):
        topo.sim.warning(preference_map + " should be measured before calling decode_orientations.")
    else:
        map = sheet.sheet_views[preference_map]
        d.add(dict(zip(map.view()[0].ravel(), sheet.activity.ravel())))
    
    if weighted_average:
        return d.weighted_average()
    else:
        return d.max_value_bin()



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

    Presents a large collection of input patterns, typically pixel
    by pixel on and off, keeping track of which units in the specified
    input_sheet were active when each unit in other Sheets in the
    simulation was active.  This data can then be used to plot
    receptive fields for each unit.  Note that the results are true
    receptive fields, not the connection fields usually presented in
    lieu of receptive fields, because they take all circuitry in
    between the input and the target unit into account.

    Note also that it is crucial to set the scale parameter properly when
    using units with a hard activation threshold (as opposed to a
    smooth sigmoid), because the input pattern used here may not be a
    very effective way to drive the unit to activate.  The value
    should be set high enough that the target units activate at least
    some of the time there is a pattern on the input.
    """  
    static_parameters = param.List(default=["offset","size"])
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
    
        # Obtain sheet dimensions and density.
        left, bottom, right, top = p.input_sheet.nominal_bounds.lbrt()
        sheet_density = float(p.input_sheet.nominal_density)
        
        # Cannot assume square sheet so two independent values for axes divisions.
        vertical_divisions = (sheet_density * (top - bottom)) - 1
        horizontal_divisions = (sheet_density * (right - left)) - 1

        # Calculate size of a division.
        unit_size = 1.0 / sheet_density
        half_unit_size = unit_size / 2.0 # saves repeated calculation.
        p['size'] = unit_size
        
        # Set the x and y max values down by half a unit so patterns are presented in the centre of each unit.
        y_range = (top - half_unit_size, bottom)
        x_range = (right - half_unit_size, left)

        return [Feature(name="x", range=x_range, step=float(x_range[1]-x_range[0])/horizontal_divisions), 
                Feature(name="y", range=y_range, step=float(y_range[1]-y_range[0])/vertical_divisions),
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
            [Feature(name="frequency",values=p.frequencies)]

        if p.num_direction==0: features += \
            [Feature(name="orientation",range=(0.0,pi),step=pi/p.num_orientation,cyclic=True)]

        features += \
            [Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True)]

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
                         compute_fn=compute_orientation_from_direction)]

        return features


# Here as the simplest possible example; could be moved elsewhere.
class measure_or_pref(SinusoidalMeasureResponseCommand):
    """Measure an orientation preference map by collating the response to patterns."""

    subplot = param.String("Orientation")
    
    def _feature_list(self,p):
        return [Feature(name="frequency",values=p.frequencies),
                Feature(name="orientation",range=(0.0,pi),step=pi/p.num_orientation,cyclic=True),
                Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True)]


pg= create_plotgroup(name='Orientation Preference',category="Preference Maps",
             doc='Measure preference for sine grating orientation.',
             pre_plot_hooks=[measure_sine_pref.instance()])
pg.add_plot('Orientation Preference',[('Hue','OrientationPreference')])
pg.add_plot('Orientation Preference&Selectivity',
            [('Hue','OrientationPreference'), ('Confidence','OrientationSelectivity')])
pg.add_plot('Orientation Selectivity',[('Strength','OrientationSelectivity')])
pg.add_plot('Phase Preference',[('Hue','PhasePreference')])
pg.add_plot('Phase Selectivity',[('Strength','PhaseSelectivity')])
pg.add_static_image('Color Key','command/or_key_white_vert_small.png')


pg= create_plotgroup(name='Spatial Frequency Preference',category="Preference Maps",
             doc='Measure preference for sine grating orientation and frequency.',
             pre_plot_hooks=[measure_sine_pref.instance()])
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

    def _feature_list(self,p):
        # orientation is computed from direction
        dr = Feature(name="direction",range=(0.0,2*pi),step=2*pi/p.num_direction,cyclic=True)
        or_values = list(set([compute_orientation_from_direction([("direction",v)]) for v in dr.values]))

        return [Feature(name="speed",values=[0],cyclic=False) if p.num_speeds is 0 else
                Feature(name="speed",range=(0.0,p.max_speed),step=float(p.max_speed)/p.num_speeds,cyclic=False),
                Feature(name="frequency",values=p.frequencies),
                Feature(name="direction",range=(0.0,2*pi),step=2*pi/p.num_direction,cyclic=True),
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



gaussian_corner = topo.pattern.basic.Composite(
    operator = maximum, generators = [
        topo.pattern.basic.Gaussian(size = 0.06,orientation=0,aspect_ratio=7,x=0.3),
        topo.pattern.basic.Gaussian(size = 0.06,orientation=pi/2,aspect_ratio=7,y=0.3)])


class measure_second_or_pref(SinusoidalMeasureResponseCommand):
    """Measure the secondary  orientation preference maps."""

    weighted_average	= param.Boolean( False ) 
    num_orientation	= param.Integer( default=16, bounds=(1,None), softbounds=(1,64),
                                    doc="Number of orientations to test.")
    true_peak 	 	= param.Boolean( default=True, doc="""If set the second
	    orientation response is computed on the true second mode of the
	    orientation distribution, otherwise is just the second maximum response""" ) 

    subplot		= param.String("Second Orientation")
    
    def _feature_list(self,p):
    	fs	= [ Feature(name="frequency",values=p.frequencies) ]
    	if p.true_peak:
	    fs.append(
		Feature(name="orientation",range=(0.0,pi),step=pi/p.num_orientation,cyclic=True,second_peak=True,second_response=False) )
	else:
	    fs.append(
		Feature(name="orientation",range=(0.0,pi),step=pi/p.num_orientation,cyclic=True,second_peak=False,second_response=True) )
	fs.append( Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True) )

	return fs


pg= create_plotgroup(name='Second Orientation Preference',category="Preference Maps",
             doc='Measure the second preference for sine grating orientation.',
             pre_plot_hooks=[measure_second_or_pref.instance( true_peak=False )])
pg.add_plot('Second Orientation Preference',[('Hue','SecondOrientationPreference')])
pg.add_plot('Second Orientation Preference&Selectivity',
            [('Hue','SecondOrientationPreference'), ('Confidence','SecondOrientationSelectivity')])
pg.add_plot('Second Orientation Selectivity',[('Strength','SecondOrientationSelectivity')])
pg.add_static_image('Color Key','command/or_key_white_vert_small.png')


pg= create_plotgroup(name='Second Peak Orientation Preference',category="Preference Maps",
             doc='Measure the second peak preference for sine grating orientation.',
             pre_plot_hooks=[measure_second_or_pref.instance( true_peak=True )])
pg.add_plot('Second Peak Orientation Preference',[('Hue','SecondPeakOrientationPreference')])
pg.add_plot('Second Peak Orientation Preference&Selectivity',
            [('Hue','SecondPeakOrientationPreference'), ('Confidence','SecondPeakOrientationSelectivity')])
pg.add_plot('Second Peak Orientation Selectivity',[('Strength','SecondPeakOrientationSelectivity')])
pg.add_static_image('Color Key','command/or_key_white_vert_small.png')

        
pg = create_plotgroup(name='Two Orientation Preferences',category='Preference Maps',
    doc='Display the two most preferred orientations for each units.',
    pre_plot_hooks=[
		measure_sine_pref.instance(num_orientation=16,weighted_average=False),
    		measure_second_or_pref.instance(num_orientation=16,weighted_average=False,true_peak=False)
])
pg.add_plot( 'Two Orientation Preferences', [
		( 'Or1',	'OrientationPreference' ),
		( 'Sel1',	'OrientationSelectivity' ),
		( 'Or2',	'SecondOrientationPreference' ),
		( 'Sel2',	'SecondOrientationSelectivity' )
])
pg.add_static_image('Color Key','command/two_or_key_vert.png')

        
pg = create_plotgroup(name='Two Peaks Orientation Preferences',category='Preference Maps',
    doc="""Display the two most preferred orientations for all units with a
    multimodal orientation preference distribution.""",
    pre_plot_hooks=[
		measure_sine_pref.instance(num_orientation=16,weighted_average=False),
    		measure_second_or_pref.instance(num_orientation=16,weighted_average=False,true_peak=True)
])
pg.add_plot( 'Two Peaks Orientation Preferences', [
		( 'Or1',	'OrientationPreference' ),
		( 'Sel1',	'OrientationSelectivity' ),
		( 'Or2',	'SecondPeakOrientationPreference' ),
		( 'Sel2',	'SecondPeakOrientationSelectivity' )
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
        return [Feature(name="x",range=p.x_range,step=width/p.divisions),
                Feature(name="y",range=p.y_range,step=height/p.divisions),
                Feature(name="orientation",range=(0,2*pi),step=2*pi/p.num_orientation,cyclic=True)]


pg= create_plotgroup(name='Corner OR Preference',category="Preference Maps",
             doc='Measure orientation preference for corner shape (or other complex stimuli that cannot be represented as fullfield patterns).',
             pre_plot_hooks=[measure_corner_or_pref.instance()],
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
            Feature( name = "x",           range = p.x_range, step = x_step ),
            Feature( name = "y",           range = p.y_range, step = y_step ),
            Feature( name = "orientation", range = (0, 2*pi), step = o_step, cyclic = True ),
            Feature( name = "angle",       range = a_range,   step = a_step,
                     value_offset     = - angle_0,
                     value_multiplier = 1. / ( angle_1 - angle_0 ) )
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

	hues	= [ "hsl(%2d,100%%,50%%)" % h		for h in range( 0, 255, 255 / n_a) ]
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


# Measure sound frequency preference maps
class measure_frequency_pref(PositionMeasurementCommand):
    """Measure a frequency preference and selectivity map"""
        
    display = param.Boolean(True) 
    pattern_presenter = param.Callable(PatternPresenter(Line(smoothing=0.0001,thickness=0.05)))
    
    # BK-ALERT: These are hard coded to the lissom audio sheet dimensions.
    # i'm not sure how to avoid that, PositionMeasurementCommand isn't
    # actually able to access the sheet dimensions.
    y_range = param.NumericTuple((-0.5,0.5))
    divisions = param.Integer(100)
    
    def _feature_list(self,p):
        return [Feature(name="x", values=[0.0]), 
                Feature(name="y", range=p.y_range, step=(p.y_range[1]-p.y_range[0])/float(p.divisions))]


pg= create_plotgroup(name='Frequency Preference and Selectivity',category="Preference Maps",
                     pre_plot_hooks=[measure_frequency_pref.instance()], normalize='Individually',
                     doc='Measure best frequency preference and selectivity for auditory neurons.')

pg.add_plot('[Frequency Preference]', [('Strength','YPreference')])
pg.add_plot('[Frequency Selectivity]', [('Strength','YSelectivity')])


import types
__all__ = list(set([k for k,v in locals().items()
                    if isinstance(v,types.FunctionType) or 
                    (isinstance(v,type) and issubclass(v,ParameterizedFunction))
                    and not v.__name__.startswith('_')]))


