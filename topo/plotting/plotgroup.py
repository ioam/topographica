"""
Hierarchy of PlotGroup classes, i.e. output-device-independent sets of
plots.

Includes PlotGroups for standard plots of anything in a Sheet
database, plus weight plots for one unit, and projections.
"""

import copy
import Image

import param
from param.parameterized import ParamOverrides, ParameterizedFunction
from param import resolve_path

from imagen.random import UniformRandom
from collections import OrderedDict

from featuremapper import distribution

import topo
from topo.command import pylabplot
from topo.command import analysis
from topo.base.cf import CFSheet,CFProjection
from topo.base.projection import ProjectionSheet
from topo.sheet import GeneratorSheet,Sheet

from plot import make_template_plot, Plot
from plotfilesaver import PlotGroupSaver,CFProjectionPlotGroupSaver

# General CEBALERTs for this file:
# * It is very difficult to understand what is happening in these
#   classes!
# * Improve hierarchy. E.g. GridPlotGroup should be a mixin?
# * Oh yeah, and don't forget about the TestPattern window. It has
#   some kind of PlotGroup in it too...
# * There are missing classes (e.g. currently only the CFProjections
#   can be plotted for CFSheets).
# * There are no unit tests

# General JABALERT:
# We need to clean up this file; there is no need
# for it to be so incomprehensible. Everything to do with _range,
# _kw_for_make_template_plots, _hack, and joint normalization
# needs to be greatly simplified.



def _cmp_plot(plot1,plot2):
    """
    Comparison function for sorting Plots.
    It compares the precedence number first and then the src_name and name attributes.
    """
    if plot1.precedence != plot2.precedence:
        return cmp(plot1.precedence,plot2.precedence)
    else:
        return cmp((plot1.plot_src_name+plot1.name),
                   (plot2.plot_src_name+plot2.name))


class PlotGroup(param.Parameterized):
    """
    Container that has one or more Plots and also knows how to arrange
    the plots and other special parameters.
    """

    pre_plot_hooks = param.HookList(default=[],doc="""
        Commands to execute before updating this plot, e.g. to calculate sheet views.

        The commands can be any callable Python objects, i.e. any x for
        which x() is valid.  The initial value is determined by the
        template for this plot, but various arguments can be passed, a
        modified version substituted, etc.""")

    plot_hooks = param.HookList(default=[],doc="""
        Commands to execute when redrawing a plot rather than regenerating data.

        E.g, for a plot with data measured once but displayed one
        sheet or unit at at time, this command will be called whenever
        the sheet or coordinate of unit to be plotted (or the
        simulator time) has changed.

        The commands can be any callable Python objects, i.e. any x for
        which x() is valid.  The initial value is determined by the
        template for this plot, but various arguments can be passed, a
        modified version substituted, etc.""")

    # I guess the interface for users of the class (I just mean methods
    # likely to be used) is:
    # make_plots()
    # scale_images()
    # + parameters

    # And the interface for subclasses (I mean methods likely to be
    # overridden) is:
    # _generate_plots()      - return the list of plots
    # _generate_labels()     - return the list of labels
    # _sort_plots()          - sort the list of plots
    # _exec_pre_plot_hooks() - run the pre_plot_hooks
    # _exec_plot_hooks()     - run the plot_hooks


    ##############################
    ########## interface for users

    def make_plots(self,update=True):
        """
        Create and scale the plots, after first executing the PlotGroup's pre_plot_hooks
        (if update is True) and plot_hooks.
        """
        if update:self._exec_pre_plot_hooks()
        self._exec_plot_hooks()
        self._create_images(update)
        self.scale_images()

    def scale_images(self,zoom_factor=None):
        """Scale the images by the given zoom factor, if appropriate; default is to do nothing."""
        pass


    ###################################
    ########## interface for subclasses

    def _generate_plots(self):
        """Return the list of Plots"""
        # subclasses may have dynamically generated Plots to add
        return self._static_plots[:]


    def _generate_labels(self):
        return [plot.label() for plot in self.plots]


    def _sort_plots(self):
        """Sort plots according to their precedence, then alphabetically."""
        self.plots.sort(_cmp_plot)


    def __init__(self,**params):
        super(PlotGroup,self).__init__(**params)
        self._static_plots = []
        self.plots = []
        self.labels = []
        self.time = None
        self.filesaver = PlotGroupSaver(self)


    def _exec_pre_plot_hooks(self,**kw):
        for f in self.pre_plot_hooks:
            f(**kw)


    def _exec_plot_hooks(self,**kw):
        for f in self.plot_hooks:
            f(**kw)


    # unlikely to be overridden?
    def _create_images(self,update):
        """
        Generate the sorted and scaled list of plots constituting the PlotGroup.
        """
        self.plots = [plot for plot in self._generate_plots() if plot is not None]

        # Suppress plots in the special case of plots not being updated
        # and having no resizable images, to suppress plotgroups that
        # have nothing but a color key
        resizeable_plots = [plot for plot in self.plots if plot.resize]
        if not update and not resizeable_plots:
            self.plots=[]

        # Take the timestamps from the underlying Plots
        timestamps = [plot.timestamp for plot in self.plots
                      if plot.timestamp >= 0]
        if len(timestamps)>0:
            self.time = max(timestamps)
            if max(timestamps) != min(timestamps):
                self.warning("Combining Plots from different times (%s,%s)" %
                             (min(timestamps),max(timestamps)))

        self._sort_plots()
        self.labels = self._generate_labels()


    @property
    def coords(self):
        """
        Calculate the grid layout of the plots from their precedences
        and row_precedences. Returns a list of triples (row, col, plot).
        """
        # Plots are sorted first by precedence, then grouped by row_precedence
        self._sort_plots()
        precedences = sorted(set(p.row_precedence for p in self.plots))

        coords=[]
        # Can use collections.Counter in Python >= 2.7
        column_counter = dict((i,0) for i,_ in enumerate(precedences))
        for plot in self.plots:
            # Find the row number based on the row_precedences
            row = precedences.index(plot.row_precedence)
            # Look up the current column position of the row
            col = column_counter[row]
            # The next plot on this row will have to be in the next column
            column_counter[row] +=1
            coords.append((row, col, plot))
        return coords

    @property
    def grid(self):
        """
        Return the plots in grid format, i.e., a list of rows, each of
        which is a list of plots. The rows are right padded with None
        as necessary.
        """
        coords = self.coords
        rows = max(r for (r,_,_) in coords) + 1 if coords != [] else 0
        cols = max(c for (_,c,_) in coords) + 1 if coords != [] else 0
        unpadded_grid = [[p for (r,_, p) in coords if r==row] for row in range(rows)]
        return [r + [None]*(cols-len(r)) for r in unpadded_grid]



### In the rest of the file, whenever we do a loop through all the
### simulation's sheets, seems like we should have set the sheet
### Parameter's range instead. sheet's range is set by the GUI.
### i.e. maybe there should be a sheet parameter here, with its range
### set when the plotgroup is instantiated. Then if sheet=None, the
### sheet's range can be used as the list of sheets.

class SheetPlotGroup(PlotGroup):

    # CEBALERT: shouldn't this be abstract? Currently it wouldn't do
    # anything with its sheets if you asked it to make plots.
    #
    # (TemplatePlotGroup and TestPatternPlotGroup are the only two
    # immediate children at the moment.)

    sheet_coords = param.Boolean(default=False,doc="""
        Whether to scale plots based on their relative sizes in sheet
        coordinates.  If true, plots are scaled so that their sizes are
        proportional to their area in sheet coordinates, so that one can
        compare corresponding areas.  If false, plots are scaled to have
        similar sizes on screen, regardless of their corresponding
        sheet areas, which maximizes the size of each plot.""")

    # CEBALERT: in the GUI, this isn't getting the right help text. I
    # suspect I put in a hack for these parameters in parametersframe,
    # sp when used outside of a parametersframe, they don't get the
    # help text.
    normalize = param.ObjectSelector(default='None',
                                     objects=['None','Individually'],
                                  doc="""
        'Individually': scale each plot so that the peak value will be white
        and the minimum value black.

        'None': no scaling - 0.0 will be black and 1.0 will be white.

        Normalization has the advantage of ensuring that any data that
        is present will be visible, but the disadvantage that the
        absolute scale will be obscured.  Non-normalized plots are
        guaranteed to be on a known scale, but only values between 0.0
        and 1.0 will be visibly distinguishable.""")

    integer_scaling = param.Boolean(default=False,doc="""
        When scaling bitmaps, whether to ensure that the scaled bitmap is an even
        multiple of the original.  If true, every unit will be represented by a
        square of the same size.  Typically false so that the overall area will
        be correct, e.g. when using Sheet coordinates, which is often more
        important.""")

    auto_refresh = param.Boolean(default=False,doc="""
        If this plot is being displayed persistently (e.g. in a GUI),
        whether to regenerate it automatically whenever the simulation
        time advances.  The default is False, because many plots are
        slow to generate (including most preference map plots).""")

    desired_maximum_plot_height = param.Number(default=0,bounds=(0,None),doc="""
        User-specified height of the tallest plot in this PlotGroup.
        Other plots will generally be scaled as appropriate, either
        to match this size (when sheet_coords is False), or to
        have the appropriate relative size (when sheet_coords is True).

        If enforce_minimum_plot_height is True, the actual maximum
        plot height may be larger than this parameter's value.  In
        particular, with enforce_minimum_plot_height=True, the default
        value of 0 gives plots that are the size of the underlying
        matrix, which is the most efficient size for saving plots
        directly to disk.  Larger values (e.g. 150) are suitable when
        displaying plots on screen.""")

    enforce_minimum_plot_height = param.Boolean(default=True,doc="""
        If true, ensure that plots are never shown smaller than their
        native size, i.e. with fewer than one pixel per matrix unit.
        This option is normally left on for safety, so that no
        visualization will be missing any units.  However, it may be
        acceptable to turn this check off when working with matrix
        sizes much larger than your screen resolution.""")

    # For users, adds:
    # sheets()
    # update_maximum_plot_height()
    # scale_images()

    #########################
    ########## adds for users

    def sheets(self):
        return topo.sim.objects(Sheet).values()


    def update_maximum_plot_height(self,zoom_factor=None):
        """
        Determine which plot will be the largest, based on the
        settings for minimum plot heights, the specified zoom factor
        (if not None), etc.

        A minimum size (and potentially a maximum size) are enforced,
        as described below.

        If the scaled sizes would be outside of the allowed range,
        False is returned.

        For matrix coordinate plots (sheet_coords=False), the minimum
        size is calculated as the native size of the largest bitmap to
        be plotted.  Other plots are then usually scaled up to (but
        not greater than) this size, so that all plots are
        approximately the same size, and no plot is missing any pixel.

        For Sheet coordinate plots, the minimum plotting density that
        will avoid losing pixels is determined by the maximum density
        from any sheet.  If all plots are then drawn at that density
        (as they must be for them to be in Sheet coordinates), the
        largest plot will then be the one with the largest sheet
        bounds, and the size of that plot will be the maximum density
        times the largest sheet bounds.
        """
        # Apply optional scaling to the overall size
        if zoom_factor:
            self.desired_maximum_plot_height*=zoom_factor

        self.maximum_plot_height=self.desired_maximum_plot_height

        if (self.enforce_minimum_plot_height):
            resizeable_plots = [p for p in self.plots if p.resize]

            # CEBALERT: not sure how I should have handled this...
            if not resizeable_plots:
                return False

            if not self.sheet_coords:
                bitmap_heights = [p._orig_bitmap.height() for p in resizeable_plots]
                minimum_height_of_tallest_plot = max(bitmap_heights)

            else:
                ### JABALERT: Should take the plot bounds instead of the sheet bounds
                ### Specifically, a weights plot with situate=False
                ### doesn't use the Sheet bounds, and so the
                ### minimum_height is significantly overstated.

                sheets = topo.sim.objects(Sheet)
                max_sheet_height = max([(sheets[p.plot_src_name].bounds.lbrt()[3]-
                                         sheets[p.plot_src_name].bounds.lbrt()[1])
                                       for p in resizeable_plots])
                max_sheet_density = max([sheets[p.plot_src_name].xdensity
                                         for p in resizeable_plots])
                minimum_height_of_tallest_plot = max_sheet_height*max_sheet_density
                self.max_sheet_height=max_sheet_height

            if (self.maximum_plot_height < minimum_height_of_tallest_plot):
                self.maximum_plot_height = minimum_height_of_tallest_plot
                # Return failure if trying to reduce but hit the minimum
                if zoom_factor:
                    return zoom_factor>1.0

#       print zoom_factor, self.maximum_plot_height, self.desired_maximum_plot_height
        return True


    ### CEB: At least some of this scaling would be common to all
    ### plotgroups, if some (e.g. featurecurve) didn't open new
    ### windows.
    ###
    ### Could strip out the matrix-coord scaling and put it into
    ### PlotGroup
    def scale_images(self,zoom_factor=None):
        """
        Enlarge or reduce the bitmaps as needed for display.

        The calculated sizes will be multiplied by the given
        zoom_factor, if it is not None.

        If the scaled sizes would be outside of the allowed range, no
        scaling is done, and False is returned.  (One might
        conceivably instead want the scaling to reach the actual
        minimum or maximum allowed, but if we did this, then repeated
        enlargements and reductions would not be reversible, unless we
        were very tricky about how we did it.)
        """

        # No scaling to do if there are no scalable plots, or no desired size
        resizeable_plots = [p for p in self.plots if p.resize]
        if not resizeable_plots or not self.desired_maximum_plot_height:
            return False

        # Calculate maximum_plot_height, and abort if not feasible
        if not self.update_maximum_plot_height(zoom_factor) and zoom_factor:
            return False

        # Scale the images so that each has a size up to the self.maximum_plot_height
        for plot in resizeable_plots:
            if self.sheet_coords:
                s = topo.sim.objects(Sheet)[plot.plot_src_name]
                scaling_factor=self.maximum_plot_height/float(s.xdensity)/self.max_sheet_height
            else:
                scaling_factor=self.maximum_plot_height/float(plot._orig_bitmap.height())

            if self.integer_scaling:
                scaling_factor=max(1,int(scaling_factor))

            plot.set_scale(scaling_factor)

            #print "Scaled %s %s: %d->%d (x %f)" % (plot.plot_src_name, plot.name, plot._orig_bitmap.height(), plot.bitmap.height(), scaling_factor)

        return True



def _get_value_range(plots):
    """
    Helper function to return the (min,max) given by the value_ranges of
    the given plots.

    Return None if there were no plots with value_range.
    """
    mins = []
    maxs = []
    for plot in plots:
        if hasattr(plot,'value_range'):
            mins.append(plot.value_range[0])
            maxs.append(plot.value_range[1])

    if len(mins)==0:
        return None
    else:
        return (min(mins),max(maxs))



def alwaystrue(x): return True



class TemplatePlotGroup(SheetPlotGroup):
    """
    Container that allows creation of different types of plots in a
    way that is independent of particular models or Sheets.

    A TemplatePlotGroup is constructed from a plot_templates list, an
    optional command to run to generate the data, and other optional
    parameters.

    The plot_templates list should contain tuples (plot_name,
    plot_template).  Each plot_template is a list of (name, value)
    pairs, where each name specifies a plotting channel (such as Hue
    or Confidence), and the value is the name of a SheetView (such as
    Activity or OrientationPreference).

    Various types of plots support different channels.  An SHC
    plot supports Strength, Hue, and Confidence channels (with
    Strength usually being visualized as luminance, Hue as a color
    value, and Confidence as the saturation of the color).  An RGB
    plot supports Red, Green, and Blue channels.  Other plot types
    will be added eventually.

    For instance, one could define an Orientation-colored Activity
    plot as::

      plotgroups['Activity'] =
          TemplatePlotGroup(name='Activity', category='Basic',
              pre_plot_hooks=[measure_activity],
              plot_templates=[('Activity',
                  {'Strength': 'Activity', 'Hue': 'OrientationPreference', 'Confidence': None})])

    This specifies that the final TemplatePlotGroup will contain up to
    one Plot named Activity per Sheet, although there could be no
    plots at all if no Sheet has a SheetView named Activity once
    'measure_activity()' has been run.  The Plot will be colored by
    OrientationPreference if such a SheetView exists for that Sheet,
    and the value (luminance) channel will be determined by the
    SheetView Activity.  This plot will be listed in the category
    'Basic' anywhere such categories are relevant (e.g. in the GUI).


    Here's a more complicated example specifying two different plots
    in the same PlotGroup::

      TemplatePlotGroup(name='Orientation Preference', category='Basic'
          pre_plot_hooks=[measure_or_pref.instance()],
          plot_templates=
              [('Orientation Preference',
                  {'Strength': None, 'Hue': 'OrientationPreference'}),
               ('Orientation Selectivity',
                  {'Strength': 'OrientationSelectivity'})])

    Here the TemplatePlotGroup will contain up to two Plots per Sheet,
    depending on which Sheets have OrientationPreference and
    OrientationSelectivity SheetViews.


    The function create_plotgroup provides a convenient way to define plots using
    TemplatePlotGroups; search for create_plotgroup elsewhere in the code to see
    examples.
    """

    doc = param.String(default="",doc="""
        Documentation string describing this type of plot.""")

    plot_immediately=param.Boolean(False,doc="""
        Whether to call the pre-plot hooks at once or only when the user asks for a refresh.

        Should be set to true for quick plots, but false for those that take a long time
        to calculate, so that the user can change the hooks if necessary.""")

    prerequisites=param.List([],doc="""
        List of preference maps that must exist before this plot can be calculated.""")

    category = param.String(default="User",doc="""
        Category to which this plot belongs, which will be created if necessary.""")

    filterfn = param.Callable(default=alwaystrue,doc="""
        Boolean function allowing control over which items will be plotted.
        E.g.: filterfn=lambda x: x.name in ['Retina','V1'] for a plot ranging over
        Sheets, or filterfn=lambda x: x[0]==x[1] for a plot ranging over coordinates.""")

    # CEBALERT: how to avoid repeating documentation?
    # CB: also, documentation for normalization types needs cleaning up.
    normalize = param.ObjectSelector(default='None',
                                     objects=['None','Individually','AllTogether'],doc="""

        'Individually': scale each plot so that its maximum value is
        white and its minimum value black.

        'None': no scaling (0.0 will be black and 1.0 will be white).

        'AllTogether': scale each plot so that the highest maximum value is
        white, and the lowest minimum value is black.


        Normalizing 'Individually' has the advantage of ensuring that
        any data that is present will be visible, but the disadvantage
        that the absolute scale will be obscured.  Non-normalized
        plots are guaranteed to be on a known scale, but only values
        between 0.0 and 1.0 will be visibly distinguishable.""")

    color_channel = param.ObjectSelector(default='None', objects=['None'], doc="""
        Defines the color channel to be displayed in the GUI, can usually be set
        to a measured OrientationMap""")



    # Overrides:
    # _generate_plots() - supports normalize=='AllTogether'

    # For users, adds:
    # add_template()
    # add_static_image()

    # For subclasses, adds:
    # _template_plots()             -
    # _make_template_plot()         -
    # _kw_for_make_template_plots() -


    #####################
    ########## overridden

    def _generate_plots(self):
        if self.normalize=='AllTogether':
            range_ = _get_value_range(self._template_plots(range_=None))
        else:
            range_ = False
        return self._static_plots[:]+self._template_plots(range_=range_)


    def __init__(self,plot_templates=None,static_images=None,**params):
        super(TemplatePlotGroup,self).__init__(**params)
        self.plot_templates = OrderedDict(plot_templates or [])
        # Add plots for the static images, if any
        for image_name,file_path in static_images or []:
            self.add_static_image(image_name,file_path)


    #########################
    ########## adds for users

    # JCALERT! We might eventually write these two functions
    # 'Python-like' by using keyword argument to specify each
    # channel and then get the dictionnary of all remaining
    # arguments.
    #
    # JABALERT: We should also be able to store a documentation string
    # describing each plot (for hovering help text) within each
    # plot template.

    def add_template(self,name,specification_tuple_list):
        dict_={}
        for key,value in specification_tuple_list:
            dict_[key]=value
        self.plot_templates[name] = dict_

    add_plot = add_template # CEBALERT: should be removed when callers updated


    def add_static_image(self,name,file_path):
        """
        Construct a static image Plot (e.g. a color key for an Orientation Preference map).
        """
        image = Image.open(resolve_path(file_path))
        plot = Plot(image,name=name)
        self._static_plots.append(plot)



    ##############################
    ########## adds for subclasses

    def _template_plots(self,range_=False):
        # calls make_template_plot for all plot_templates for all kw returned
        # by _kw_for_make_template_plot!!
        template_plots = []
        for plot_template_name,plot_template in self.plot_templates.items():
            for kw in self._kw_for_make_template_plot(range_):
                template_plots.append(self._make_template_plot(plot_template_name,plot_template,**kw))
        return template_plots


    def _kw_for_make_template_plot(self,range_):
        # Return a list of dictionaries; for each dictionary,
        # _make_template_plot() will be called with that dictionary
        # as keyword arguments.
        #
        # Allows subclasses to control what range of things (sheets,
        # projections) _make_template_plot() is called over, and to
        # control what keyword arguments
        # (sheet=,proj_=,range_=,bounds=,x=,...) are supplied.
        return [dict(sheet=sheet,range_=range_) for sheet in filter(self.filterfn,self.sheets())]


    def _make_template_plot(self,plot_template_name,plot_template,**kw):
        view_dict = {'Strength': kw['sheet'].views.Maps,
                     'Hue': kw['sheet'].views.Maps,
                     'Confidence': kw['sheet'].views.Maps}
        return make_template_plot(plot_template,
                                  view_dict,
                                  kw['sheet'].xdensity,
                                  kw['sheet'].bounds,
                                  self.normalize,
                                  # CEBALERT: after this class, p.t. name never used
                                  name=plot_template_name,
                                  range_=kw['range_'])



def default_measureable_sheet():
    """Returns the first sheet for which measure_maps is True (if any), or else the first sheet, for use as a default value."""

    sheets = [s for s in topo.sim.objects(Sheet).values()
              if hasattr(s,'measure_maps') and s.measure_maps]
    if len(sheets)<1:
        sheets = [s for s in topo.sim.objects(Sheet).values()]
    if len(sheets)<1:
        raise ValueError("Unable to find a suitable measureable sheet.")
    sht=sheets[0]
    if len(sheets)>1:
        param.Parameterized().message("Using sheet %s." % sht.name)
    return sht



class ProjectionSheetPlotGroup(TemplatePlotGroup):
    """Abstract PlotGroup for visualizations of the Projections of one ProjectionSheet."""
    __abstract = True

    # Class attribute; forms part of the key for sheet_views (see
    # the _key() method).
    keyname = "ProjectionSheet"

    sheet = param.ObjectSelector(default=None,
                                 compute_default_fn=default_measureable_sheet,
                                 doc=
        """The Sheet from which to produce plots.""")

    normalize = param.ObjectSelector(default='None',
                                  objects=['None','Individually','AllTogether','JointProjections'],doc="""
        'Individually': scale each plot so that the peak value will be white
        and the minimum value black.

        'None': no scaling - 0.0 will be black and 1.0 will be white.

        'AllTogether': scale each plot so that the peak value of all the plots
        is white, and the minimum value of all the plots will be
        black.

        'JointProjections': as 'Individually', except that plots produced from
        projections whose weights are jointly normalized will be
        jointly normalized.

        Normalization has the advantage of ensuring that any data that
        is present will be visible, but the disadvantage that the
        absolute scale will be obscured.  Non-normalized plots are
        guaranteed to be on a known scale, but only values between 0.0
        and 1.0 will be visibly distinguishable.""")


    sheet_type = ProjectionSheet

    # Overrides:
    # _exec*plot_hooks()           - passes sheet to hooks
    # sheet()                      - returns only a single sheet
    # _kw_for_make_template_plot() - adds projections (+ assumes one sheet)
    # _template_plots()            - support joint normalization
    # _make_template_plot()        -
    # _generate_labels()           -

    # Adds for users:
    # projections() -

    # Adds for subclasses:
    # _key() -
    # _kw_for_one_proj() -
    # _check_sheet_type() -
    # _check_data_exist() -


    #########################
    ########## adds for users

    def projections(self):
        return self.sheet.projections().values()


    #####################
    ########## overridden

    def sheets(self):
        return [self.sheet]

    def _exec_pre_plot_hooks(self,**kw):
        self.params('sheet').compute_default()
        self._check_sheet_type()
        super(ProjectionSheetPlotGroup,self)._exec_pre_plot_hooks(outputs=[self.sheet.name],**kw)


    def _exec_plot_hooks(self,**kw):
        super(ProjectionSheetPlotGroup,self)._exec_plot_hooks(sheet=self.sheet,**kw)


    def _kw_for_make_template_plot(self,range_):
        args = []
        for proj in filter(self.filterfn,self.projections()):
            for d in self._kw_for_one_proj(proj):
                d['range_']=range_[proj.name]
                args.append(d)
        return args

    def _template_plots(self,range_=False):
        # all the extra processing is for normalize=='JointProjections'

        # {name:range_} for the projections
        named_ranges = dict.fromkeys([proj.name for proj in self.projections()],range_)

        if self.normalize=='JointProjections':
            ranges = {}
            for group_key in self.sheet._grouped_in_projections('JointNormalize').keys():
                if group_key is None:
                    ranges[group_key]=False
                else:
                    projlist = self.sheet._grouped_in_projections('JointNormalize')[group_key]
                    self._check_data_exist(projlist)

                    # hack: need a _kw_for_make_template() that works
                    # with a single range value and restricts
                    # projections to those with a specified key.
                    self._group_key = group_key
                    _orig = self._kw_for_make_template_plot
                    self._kw_for_make_template_plot = self._hack

                    plotlist = super(ProjectionSheetPlotGroup,self)._template_plots(range_=None)
                    self._kw_for_make_template_plot = _orig
                    ranges[group_key] = _get_value_range(plotlist)

            for key,proj in self.__keyed_projections():
                named_ranges[proj.name] = ranges[key]

        return super(ProjectionSheetPlotGroup,self)._template_plots(range_=named_ranges)


    def _make_template_plot(self,plot_template_name,plot_template,**kw):#sheet,proj
        view_dict = {'Strength': kw['sheet'].views.Maps,
                     'Hue': kw['sheet'].views.Maps,
                     'Confidence': kw['sheet'].views.Maps}
        return make_template_plot(self._channels(plot_template,**kw),
                                  view_dict,
                                  kw['proj'].src.xdensity,
                                  None,
                                  self.normalize,
                                  name=kw['proj'].name,
                                  range_=kw['range_'])


    def _generate_labels(self):
        return ["%s%s"%(plot.name,
                        (("\n(from %s)" % plot.proj_src_name)
                         if hasattr(plot,"proj_src_name") else ""))
                 for plot in self.plots]


    ##############################
    ########## adds for subclasses

    def _key(self,**kw):
        # the key for sheet_views
        return kw['proj'].name+self.keyname


    def _kw_for_one_proj(self,proj):
        # Return a list of dictionaries; for each dictionary,
        # _make_template_plot() will be called with that dictionary as
        # keyword arguments.
        return [dict(proj=proj)]


    # CB: this isn't really necessary for these classes
    # themselves. Right now we have it provide a useful error message
    # to users (which is useful).
    def _check_sheet_type(self):
        if self.sheet is not None and not isinstance(self.sheet,self.sheet_type):
            raise TypeError(
                "%s's sheet Parameter must be set to a %s instance (currently %s, type %s)." \
                %(self,self.sheet_type,self.sheet,type(self.sheet)))


    def _check_data_exist(self,projlist):
        # for joint normalization, not all data required may be
        # measured and displayed by the PlotGroup (in subclasses that
        # don't display all projections at once).
        pass

    # unlikely to be overridden?
    def _channels(self,plotgroup_template,**kw):
        channels = copy.deepcopy(plotgroup_template)
        channels['Strength']=self._key(**kw)
        return channels


    # CEBALERT: used to temporarily override
    # _kw_for_make_template_plot(), to allow calculation of range for
    # joint normalization. A mess.
    def _hack(self,range_):
        for key,projlist in self.sheet._grouped_in_projections('JointNormalize').items():
            if key==self._group_key:
                args = []
                for proj in projlist or self.projections():
                    for d in self._kw_for_one_proj(proj):
                        d['range_']=range_
                        args.append(d)
                return args
        raise


    def __keyed_projections(self):
        # helper method to return a list of (key,proj) pairs from self.sheet
        keys_and_projns = []
        for key,projlist in self.sheet._grouped_in_projections('JointNormalize').items():
            for proj in projlist:
                keys_and_projns.append((key,proj))
        return keys_and_projns



class ProjectionActivityPlotGroup(ProjectionSheetPlotGroup):
    """Visualize the activity of all Projections into a ProjectionSheet."""

    keyname='ProjectionActivity'

    #####################
    ########## overridden

    def _make_template_plot(self,plot_template_name,plot_template,**kw):
        view_dict = {'Strength': kw['proj'].dest.views.Maps,
                     'Hue': kw['proj'].dest.views.Maps,
                     'Confidence': kw['proj'].dest.views.Maps}
        return make_template_plot(self._channels(plot_template,**kw),
                                  view_dict,
                                  kw['proj'].dest.xdensity,
                                  kw['proj'].dest.bounds,
                                  self.normalize,
                                  name=kw['proj'].name,
                                  range_=kw['range_'])


# CEBALERT: Total mess. should be a mix-in class, or something like
# that.
class GridPlotGroup(ProjectionSheetPlotGroup):
    """
    A ProjectionSheetPlotGroup capable of generating coordinates on a 2D grid.
    """
    ### JPALERT: The bounds are meaningless for large sheets anyway.  If a sheet
    ### is specified in, say, visual angle coordinates (e.g., -60 to +60 degrees), then
    ### the soft min of 5.0/unit will still give a 600x600 array of CFs!
    ### Density should probably be specified WRT to sheet bounds,
    ### instead of per-unit-of-sheet.
    density = param.Number(default=10.0,
                     softbounds=(5.0,50.0),doc="""
                     Number of units to plot per 1.0 distance in sheet coordinates""")

    normalize = param.ObjectSelector(default='None',
                                  objects=['None','Individually','AllTogether']) # joint is removed


    # Adds for subclasses:
    # generate_coords() -

    # Overrides:
    # _sort_plots()
    # _kw_for_make_template_plot() - no projection
    # _key()                       - no projection
    # _make_template_plot()        - no projection

    #####################
    ########## overridden

    def _sort_plots(self):
        """Skips plot sorting to keep the generated order."""
        pass


    def _kw_for_make_template_plot(self,range_):
        args = []
        for x,y in filter(self.filterfn,self.generate_coords()):
            x_center,y_center = self.sheet.closest_cell_center(x,y)
            args.append(dict(x=x_center,y=y_center,sheet=self.sheet,range_=range_))
        return args


    def _key(self,**kw):
        key = (self.keyname,self.sheet.name,kw['x'],kw['y'])
        return key


    def _make_template_plot(self,plot_template_name,plot_template,**kw):
        view_dict = {'Strength': self.sheet.views.Maps,
                     'Hue': self.sheet.views.Maps,
                     'Confidence': self.sheet.views.Maps}
        return make_template_plot(self._channels(plot_template,**kw),
                                  view_dict,
                                  self.input_sheet.xdensity,
                                  self.input_sheet.bounds,
                                  self.normalize,
                                  range_=kw['range_'])

    # (should *skip* the joint normalization additions in
    # projectionsheet for some subclasses (e.g. RFProjectionPlot), but
    # should not for other subclasses (e.g. ProjectionPlotGroup))
#    def _template_plots(self,range_=False):
#        return TemplatePlotGroup._dynamic_plot(self,range_)



    ##############################
    ########## adds for subclasses

    def generate_coords(self):
        """
        Evenly space out the units within the sheet bounding box, so
        that it doesn't matter which corner the measurements start
        from.  A 4 unit grid needs 5 segments.  List is in left-to-right,
        from top-to-bottom.
        """
        def rev(x): y = x; y.reverse(); return y

        (l,b,r,t) = self.sheet.bounds.lbrt()
        x = float(r - l)
        y = float(t - b)
        x_step = x / (int(x * self.density) + 1)
        y_step = y / (int(y * self.density) + 1)
        l = l + x_step
        b = b + y_step
        coords = []
        self.proj_plotting_shape = (int(y * self.density),int(x * self.density))

        for j in rev(range(self.proj_plotting_shape[0])):
            for i in range(self.proj_plotting_shape[1]):
                coords.append((x_step*i + l, y_step*j + b))

        return coords



def default_input_sheet():
    """Returns the first GeneratorSheet defined, for use as a default value."""
    sheets=topo.sim.objects(GeneratorSheet).values()
    if len(sheets)<1:
        raise ValueError("Unable to find a suitable input sheet.")
    sht=sheets[0]
    if len(sheets)>1:
        param.Parameterized().message("Using input sheet %s." % sht.name)
    return sht



class RFProjectionPlotGroup(GridPlotGroup):
    keyname='RFs'
    input_sheet = param.ObjectSelector(default=None,compute_default_fn=default_input_sheet,
                                       doc="The sheet on which to measure the RFs.")


    # Overrides:
    # _template_plots()      - no projection
    # _exec_pre_plot_hooks() -


    #####################
    ########## overridden

    def _template_plots(self,range_=False):
        return TemplatePlotGroup._template_plots(self,range_=range_)


    def _exec_pre_plot_hooks(self,**kw): # RFHACK
        self.params('input_sheet').compute_default()
        super(RFProjectionPlotGroup,self)._exec_pre_plot_hooks(inputs=[self.input_sheet.name],**kw)

    def _make_template_plot(self,plot_template_name,plot_template,**kw):
        input=self.input_sheet.name
        rf_view = self.sheet.views.RFs.get(input, {})
        view_dict = {'Hue': rf_view, 'Strength': rf_view, 'Confidence': rf_view}
        return make_template_plot(self._channels(plot_template, **kw),
                                  view_dict,
                                  self.input_sheet.xdensity,
                                  self.input_sheet.bounds,
                                  self.normalize,
                                  range_=kw['range_'])

    def _key(self,**kw):
        return kw['x'], kw['y']



class TwoOrientationsPlotGroup( TemplatePlotGroup ):
    """Display with small segments the two most preferred orientations for each
    units in the sheet. Only orientation with significative selectivity are
    shown. Darker segments correspond to orientations with more selective
    response."""

    unit_size       = param.Number(default=25,bounds=(9,None),doc="box size of a single unit")

    # Overrides:
    # _make_template_plot	- use density argument slot to parse unit_size

    def _make_template_plot(self,plot_template_name,plot_template,**kw):
        view_dict = {'Strength': kw['sheet'].views.Maps,
                     'Hue': kw['sheet'].views.Maps,
                     'Confidence': kw['sheet'].views.Maps}
        return make_template_plot(plot_template,
                                  view_dict,
                                  self.unit_size,
                                  kw['sheet'].bounds,
                                  self.normalize,
                                  name=plot_template_name,
                                  range_=kw['range_'])




# CEBALERT: haven't modified; might need updating. Doesn't seem to be
# a way to call it from the GUI - is it known to be broken?
class RetinotopyPlotGroup(TemplatePlotGroup):
    input_sheet = param.ObjectSelector(default=None,compute_default_fn=default_input_sheet,
                                       doc="The sheet on which to measure the RFs.")

    def _exec_pre_plot_hooks(self,**kw): # RFHACK
        self.params('input_sheet').compute_default()
        super(RetinotopyPlotGroup,self)._exec_pre_plot_hooks(
            inputs=[self.input_sheet.name],**kw)



class ProjectionPlotGroup(GridPlotGroup):

    keyname='Weights'

    projection = param.ObjectSelector(default=None,doc="The projection to visualize.")

    # ProjectionSheetPlotGroup
    normalize = param.ObjectSelector(default='None',
                                  objects=['None','Individually','AllTogether','JointProjections'])


    # Overrides:
    # _projections()               - one projection
    # _key()                       - restores projection
    # _kw_for_make_template_plot() - restores projection
    # _exec_pre_plot_hooks()       - pass coords to hooks
    # _check_data_exist() - check for data from other jointly normalized projections


    #####################
    ########## overridden

    def projections(self):
        return [self.projection]


    # GridPlotGroup+ProjectionSheetPlotGroup
    def _key(self, **kw):
        return kw['x'], kw['y']


    # ProjectionSheetPlotGroup
    def _check_data_exist(self,projlist):
        nodata = []
        for proj in projlist:
            d = self._kw_for_one_proj(proj)[0] # only checking one (x,y)
            if self._key(**d) not in proj.dest.views.CFs[proj.name]:
                nodata.append(proj.name)
        if len(nodata)>0:
            raise ValueError("Joint normalization cannot proceed unless data has been measured for all jointly normalized projections (no data for %s)"%nodata)


    # GridPlotGroup+ProjectionSheetPlotGroup
    def _kw_for_make_template_plot(self,range_):
        args = self._kw_for_one_proj(self.projection)
        for d in args:
            d['range_']=range_[d['proj'].name]
        return args


    # GridPlotGroup+ProjectionSheetPlotGroup
    def _exec_pre_plot_hooks(self,**kw):
        coords=self.generate_coords() # why not in gridplotgroup?
        super(ProjectionPlotGroup,self)._exec_pre_plot_hooks(coords=coords,projection=self.projection,**kw)



class CFProjectionPlotGroup(ProjectionPlotGroup):
    """Visualize one CFProjection."""

    situate = param.Boolean(default=False,doc="""
    If True, plots the weights on the entire source sheet, using zeros
    for all weights outside the ConnectionField.  If False, plots only
    the actual weights that are stored.""")

    sheet_type = CFSheet

    # Overrides:
    # _make_template_plot()  - add bounds
    # _kw_for_one_proj()     - add bounds
    # _exec_pre_plot_hooks() - check proj type

    # Adds for subclasses:
    # _check_projection_type() -


    #####################
    ########## overridden

    def _make_template_plot(self,plot_template_name,plot_template,**kw):
        view_dict = {'Strength': kw['proj'].dest.views.CFs[kw['proj'].name],
                     'Hue': kw['proj'].src.views.Maps,
                     'Confidence': kw['proj'].src.views.Maps}
        return make_template_plot(self._channels(plot_template,**kw),
                                  view_dict,
                                  kw['proj'].src.xdensity,
                                  kw['bounds'],
                                  self.normalize,
                                  name=kw['proj'].name,
                                  range_=kw['range_'])


    def _kw_for_one_proj(self,proj):
        args = []
        for x,y in filter(self.filterfn,self.generate_coords()):
            if self.situate:
                bounds = proj.src.bounds
            else:
                (r,c) = proj.dest.sheet2matrixidx(x,y)
                bounds = proj.cf_bounds(r,c)
            args.append(dict(x=x,y=y,proj=proj,bounds=bounds))

        return args


    def _exec_pre_plot_hooks(self,**kw):
        self._check_projection_type()
        super(CFProjectionPlotGroup,self)._exec_pre_plot_hooks(**kw)


    def __init__(self,**params):
        super(CFProjectionPlotGroup,self).__init__(**params)
        self.filesaver = CFProjectionPlotGroupSaver(self)


    ##############################
    ########## adds for subclasses

    # CB: same comment for ProjectionSheetPlotGroup's _check_sheet_type.
    def _check_projection_type(self):
        if not isinstance(self.projection,CFProjection):
            raise TypeError(
                "%s's projection Parameter must be set to a %s instance (currently %s, type %s)." \
                %(self,CFProjection,self.projection,type(self.projection)))


# a mix-in?
class UnitPlotGroup(ProjectionSheetPlotGroup):
    """
    Visualize anything related to a unit.
    """

    # JABALERT: need to show actual coordinates of unit returned
    x = param.Number(default=0.0,doc="""x-coordinate of the unit to plot""")
    y = param.Number(default=0.0,doc="""y-coordinate of the unit to plot""")
## """Sheet coordinate location desired.  The unit nearest this location will be returned.
## It is an error to request a unit outside the area of the Sheet.""")

    # Overrides:
    # _key()        - removes projection, adds coords
    # _exec*hooks() - includes coords

    #####################
    ########## overridden

    def _key(self,**kw):
        return (self.keyname,self.sheet.name,self.x,self.y)

    def _exec_pre_plot_hooks(self,**kw):
        super(UnitPlotGroup,self)._exec_pre_plot_hooks(coords=[(self.x,self.y)],**kw)

    def _exec_plot_hooks(self,**kw):
        super(UnitPlotGroup,self)._exec_plot_hooks(coords=[(self.x,self.y)],**kw)



class ConnectionFieldsPlotGroup(UnitPlotGroup):
    """
    Visualize ConnectionField for each of a CFSheet's CFProjections.
    """
    keyname='Weights'

    sheet_type = CFSheet

    situate = param.Boolean(default=False,doc="""
    If True, plots the weights on the entire source sheet, using zeros
    for all weights outside the ConnectionField.  If False, plots only
    the actual weights that are stored.""")

    # Overrides:
    # _key()                - adds projection back
    # _make_template_plot() - adds projection back
    # _kw_for_one_proj()    - includes bounds


    #####################
    ########## overridden

    def _key(self,**kw):
        return self.x, self.y


    def _make_template_plot(self,plot_template_name,plot_template,**kw):
        if kw['proj'].name not in kw['proj'].dest.views.CFs:
            kw['proj']._cf_grid()
        view_dict = {'Strength': kw['proj'].dest.views.CFs.get(kw['proj'].name, {}),
                     'Hue': kw['proj'].src.views.Maps,
                     'Confidence': kw['proj'].src.views.Maps}
        return make_template_plot(self._channels(plot_template,**kw),
                                  view_dict,
                                  kw['proj'].src.xdensity,
                                  kw['bounds'],
                                  self.normalize,
                                  name=kw['proj'].name,
                                  range_=kw['range_'])


    def _kw_for_one_proj(self,proj):
        if self.situate:
            bounds = None
        else:
            (r,c) = proj.dest.sheet2matrixidx(self.x,self.y)
            bounds = proj.cf_bounds(r,c)
        return [dict(proj=proj,bounds=bounds)]



class FeatureCurvePlotGroup(UnitPlotGroup):

    def _exec_pre_plot_hooks(self,**kw):
        super(FeatureCurvePlotGroup,self)._exec_pre_plot_hooks(**kw)
        #self.get_curve_time()

    def _exec_plot_hooks(self,**kw):
        super(FeatureCurvePlotGroup,self)._exec_plot_hooks(**kw)
        #self.get_curve_time()

    def get_curve_time(self):
        """
        Get timestamps from the current SheetViews in the curve_dict and
        use the max timestamp as the plot label
        Displays a warning if not all curves have been measured at the same time.
        """
        timestamps = [curve_view.timestamp for curve_view in self.sheet.views.Curves.itervalues()]

        if timestamps != []:
            self.time = max(timestamps)
            if max(timestamps) != min(timestamps):
                self.warning("Displaying curves from different times (%s,%s)" %
                             (min(timestamps),max(timestamps)))



plotgroups = OrderedDict()
"""
Global repository of PlotGroups, to which users can add their own as
needed.
"""

plotgroup_types = {'Connection Fields': ConnectionFieldsPlotGroup,
                   'Projection': CFProjectionPlotGroup,
                   'RF Projection': RFProjectionPlotGroup,
                   'Retinotopy': RetinotopyPlotGroup,
                   'Projection Activity': ProjectionActivityPlotGroup}


def create_plotgroup(template_plot_type='bitmap',**params):
    """
    Create a new PlotGroup and add it to the plotgroups list.

    Convenience function to make it simpler to use the name of the
    PlotGroup as the key in the plotgroups list.

    template_plot_type: Whether the plots are bitmap images or curves
    ('curve').
    """
    name = params.get('name')

    pg_type = TemplatePlotGroup
    if name:
        if name in plotgroup_types:
            pg_type = plotgroup_types[name]
        elif template_plot_type=='curve':
            pg_type = FeatureCurvePlotGroup

    pg = pg_type(**params)
    plotgroups[pg.name]=pg
    return pg


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



class Subplotting(param.Parameterized):
    """
    Convenience functions for handling subplots (such as colorized
    Activity plots).  Only needed for avoiding typing, as plots can be
    declared with their own specific subplots without using these
    functions.
    """

    plotgroups_to_subplot = param.List(default=
                                       ["Activity", "Connection Fields",
                                        "Projection", "Projection Activity"],
                                       doc="List of plotgroups for which to "
                                           "set subplots.")

    subplotting_declared = param.Boolean(default=False,
                                         doc="Whether set_subplots has "
                                             "previously been called")

    _last_args = param.Parameter(default=())

    @staticmethod
    def set_subplots(prefix=None, hue="", confidence="", force=True):
        """
        Define Hue and Confidence subplots for each of the
        plotgroups_to_subplot.
        Typically used to make activity or weight plots show a
        preference value as the hue, and a selectivity as the
        confidence.

        The specified hue, if any, should be the name of a SheetView,
        such as OrientationPreference.  The specified confidence, if
        any, should be the name of a (usually) different SheetView,
        such as OrientationSelectivity.

        The prefix option is a shortcut making the usual case easier
        to type; it sets hue to prefix+"Preference" and confidence to
        prefix+"Selectivity".

        If force=False, subplots are changed only if no subplot is
        currently defined.  Force=False is useful for setting up
        subplots automatically when maps are measured, without
        overwriting any subplots set up specifically by the user.

        Currently works only for plotgroups that have a plot
        with the same name as the plotgroup, though this could
        be changed easily.

        Examples::

           Subplotting.set_subplots("Orientation")
             - Set the default subplots to OrientationPreference and
             OrientationSelectivity

           Subplotting.set_subplots(hue="OrientationPreference")
             - Set the default hue subplot to OrientationPreference with no
             selectivity

           Subplotting.set_subplots()
             - Remove subplots from all the plotgroups_to_subplot.
        """

        Subplotting._last_args = (prefix, hue, confidence, force)

        if Subplotting.subplotting_declared and not force:
            return

        if prefix:
            hue = prefix + "Preference"
            confidence = prefix + "Selectivity"

        for name in Subplotting.plotgroups_to_subplot:
            if name in plotgroups.keys():
                pg = plotgroups[name]
                if name in pg.plot_templates.keys():
                    pt = pg.plot_templates[name]
                    pt["Hue"] = hue
                    pt["Confidence"] = confidence
                else:
                    Subplotting().warning("No template %s defined for plotgroup"
                                          " %s" % (name, name))
            else:
                Subplotting().warning("No plotgroup %s defined" % name)

        Subplotting.subplotting_declared = True


    @staticmethod
    def restore_subplots():
        args = Subplotting._last_args
        if args != ():
            Subplotting.set_subplots(*(Subplotting._last_args))


pg = create_plotgroup(name='Activity', category='Basic',
                      doc='Plot the activity for all Sheets.',
                      auto_refresh=True, pre_plot_hooks=[analysis.update_activity],
                      plot_immediately=True)
pg.add_plot('Activity', [('Strength', 'ActivityBuffer')])


pg = create_plotgroup(name='Connection Fields', category="Basic",
                     doc='Plot the weight strength in each ConnectionField of a specific unit of a Sheet.',
                     pre_plot_hooks=[analysis.update_connectionfields],
                     plot_immediately=True, normalize='Individually', situate=True)
pg.add_plot('Connection Fields', [('Strength', 'Weights')])


pg = create_plotgroup(name='Projection', category="Basic",
           doc='Plot the weights of an array of ConnectionFields in a Projection.',
           pre_plot_hooks=[analysis.update_projection],
           plot_immediately=False, normalize='Individually', sheet_coords=True)
pg.add_plot('Projection', [('Strength', 'Weights')])


pg = create_plotgroup(name='RGB', category='Other',
             doc='Combine and plot the red, green, and blue activity for all appropriate Sheets.',
             auto_refresh=True, pre_plot_hooks=[analysis.update_rgb_activities],
             plot_immediately=True)
pg.add_plot('RGB', [('Red', 'RedActivity'), ('Green', 'GreenActivity'),
                    ('Blue', 'BlueActivity')])


pg = create_plotgroup(name='Projection Activity', category="Basic",
                      doc='Plot the activity in each Projection that connects '
                          'to a Sheet.',
                      pre_plot_hooks=[analysis.update_projectionactivity.instance()],
                      plot_immediately=True, normalize='Individually',
                      auto_refresh=True)
pg.add_plot('Projection Activity', [('Strength', 'ProjectionActivity')])


pg= create_plotgroup(name='Center of Gravity',category="Preference Maps",
             doc='Measure the center of gravity of each ConnectionField in a Projection.',
             pre_plot_hooks=[analysis.measure_cog.instance()],
             plot_hooks=[pylabplot.topographic_grid.instance(xsheet_view_name="XCoG",ysheet_view_name="YCoG")],
             normalize='Individually')
pg.add_plot('X CoG',[('Strength','XCoG')])
pg.add_plot('Y CoG',[('Strength','YCoG')])
pg.add_plot('CoG',[('Red','XCoG'),('Green','YCoG')])


pg = create_plotgroup(name='RF Projection', category='Other',
                      doc='Measure white noise receptive fields.',
                      pre_plot_hooks=[analysis.measure_rfs.instance(
                          pattern_generator=UniformRandom(name='UniformNoise'))],
                      normalize='Individually')

pg.add_plot('RFs', [('Strength', 'RFs')])


pg = create_plotgroup(name='Orientation Preference', category="Preference Maps",
                      doc='Measure preference for sine grating orientation.',
                      pre_plot_hooks=[analysis.measure_sine_pref.instance(
                          preference_fn=distribution.DSF_WeightedAverage())])
pg.add_plot('Orientation Preference', [('Hue', 'OrientationPreference')])
pg.add_plot('Orientation Preference&Selectivity',
            [('Hue', 'OrientationPreference'),
             ('Confidence', 'OrientationSelectivity')])
pg.add_plot('Orientation Selectivity', [('Strength', 'OrientationSelectivity')])
pg.add_plot('Phase Preference', [('Hue', 'PhasePreference')])
pg.add_plot('Phase Selectivity', [('Strength', 'PhaseSelectivity')])
pg.add_static_image('Color Key', 'static/or_key_white_vert_small.png')


pg = create_plotgroup(name='vonMises Orientation Preference',
                      category="Preference Maps",
                      doc='Measure preference for sine grating orientation '
                          'using von Mises fit.',
                      pre_plot_hooks=[analysis.measure_sine_pref.instance(
                          preference_fn=distribution.DSF_VonMisesFit(),
                          num_orientation=16)])
pg.add_plot('Orientation Preference', [('Hue', 'OrientationPreference')])
pg.add_plot('Orientation Preference&Selectivity',
            [('Hue', 'OrientationPreference'),
             ('Confidence', 'OrientationSelectivity')])
pg.add_plot('Orientation Selectivity', [('Strength', 'OrientationSelectivity')])
pg.add_plot('Phase Preference', [('Hue', 'PhasePreference')])
pg.add_plot('Phase Selectivity', [('Strength', 'PhaseSelectivity')])
pg.add_static_image('Color Key', 'static/or_key_white_vert_small.png')


pg = create_plotgroup(name='Bimodal Orientation Preference',
                      category="Preference Maps",
                      doc='Measure preference for sine grating orientation '
                          'using bimodal von Mises fit.',
                      pre_plot_hooks=[analysis.measure_sine_pref.instance(
                          preference_fn=distribution.DSF_BimodalVonMisesFit(),
                          num_orientation=16)])
pg.add_plot('Orientation Preference', [('Hue', 'OrientationPreference')])
pg.add_plot('Orientation Preference&Selectivity',
            [('Hue', 'OrientationPreference'),
             ('Confidence', 'OrientationSelectivity')])
pg.add_plot('Orientation Selectivity', [('Strength', 'OrientationSelectivity')])
pg.add_plot('Second Orientation Preference',
            [('Hue', 'OrientationMode2Preference')])
pg.add_plot('Second Orientation Preference&Selectivity',
            [('Hue', 'OrientationMode2Preference'),
             ('Confidence', 'OrientationMode2Selectivity')])
pg.add_plot('Second Orientation Selectivity',
            [('Strength', 'OrientationMode2Selectivity')])
pg.add_static_image('Color Key', 'static/or_key_white_vert_small.png')


pg = create_plotgroup(name='Two Orientation Preferences',
                      category='Preference Maps',
                      doc='Display the two most preferred orientations for '
                          'each units, using bimodal von Mises fit.',
                      pre_plot_hooks=[analysis.measure_sine_pref.instance(
                          preference_fn=distribution.DSF_BimodalVonMisesFit(),
                          num_orientation=16)])
pg.add_plot('Two Orientation Preferences', [('Or1', 'OrientationPreference'),
                                            ('Sel1', 'OrientationSelectivity'),
                                            ('Or2', 'OrientationMode2Preference'),
                                            ('Sel2', 'OrientationMode2Selectivity')])
pg.add_static_image('Color Key', 'static/two_or_key_vert.png')


pg = create_plotgroup(name='Spatial Frequency Preference',
                      category="Preference Maps",
                      doc='Measure preference for sine grating orientation '
                          'and frequency.',
                      pre_plot_hooks=[analysis.measure_sine_pref.instance(
                          preference_fn=distribution.DSF_WeightedAverage())])
pg.add_plot('Spatial Frequency Preference',
            [('Strength', 'FrequencyPreference')])
pg.add_plot('Spatial Frequency Selectivity',
            [('Strength', 'FrequencySelectivity')])
# Just calls measure_sine_pref to plot different maps.


pg = create_plotgroup(name='Ocular Preference', category="Preference Maps",
                      doc='Measure preference for sine gratings between two '
                          'eyes.',
                      pre_plot_hooks=[analysis.measure_od_pref.instance()])
pg.add_plot('Ocular Preference', [('Strength', 'OcularPreference')])
pg.add_plot('Ocular Selectivity', [('Strength', 'OcularSelectivity')])


pg= create_plotgroup(name='PhaseDisparity Preference',category="Preference Maps",doc="""
    Measure preference for sine gratings at a specific orentation differing in phase
    between two input sheets.""",
             pre_plot_hooks=[analysis.measure_phasedisparity.instance()],normalize='Individually')
pg.add_plot('PhaseDisparity Preference', [('Hue', 'PhasedisparityPreference')])
pg.add_plot('PhaseDisparity Preference&Selectivity',
            [('Hue', 'PhasedisparityPreference'),
             ('Confidence', 'PhasedisparitySelectivity')])
pg.add_plot('PhaseDisparity Selectivity',
            [('Strength', 'PhasedisparitySelectivity')])
pg.add_static_image('Color Key', 'static/disp_key_white_vert_small.png')


pg = create_plotgroup(name='Direction Preference', category="Preference Maps",
                      doc='Measure preference for sine grating movement '
                          'direction.',
                      pre_plot_hooks=[analysis.measure_dr_pref.instance()])
pg.add_plot('Direction Preference', [('Hue', 'DirectionPreference')])
pg.add_plot('Direction Preference&Selectivity', [('Hue', 'DirectionPreference'),
                                                 ('Confidence',
                                                  'DirectionSelectivity')])
pg.add_plot('Direction Selectivity', [('Strength', 'DirectionSelectivity')])
pg.add_plot('Speed Preference', [('Strength', 'SpeedPreference')])
pg.add_plot('Speed Selectivity', [('Strength', 'SpeedSelectivity')])
pg.add_static_image('Color Key', 'static/dr_key_white_vert_small.png')


pg = create_plotgroup(name='Hue Preference', category="Preference Maps",
                      doc='Measure preference for colors.',
                      pre_plot_hooks=[analysis.measure_hue_pref.instance()],
                      normalize='Individually')
pg.add_plot('Hue Preference', [('Hue', 'HuePreference')])
pg.add_plot('Hue Preference&Selectivity',
            [('Hue', 'HuePreference'), ('Confidence', 'HueSelectivity')])
pg.add_plot('Hue Selectivity', [('Strength', 'HueSelectivity')])


pg = create_plotgroup(name='Second Orientation Preference',
                      category="Preference Maps",
                      doc='Measure the second preference for sine grating '
                          'orientation.',
                      pre_plot_hooks=[
                          analysis.measure_second_or_pref.instance(true_peak=False)])
pg.add_plot('Second Orientation Preference',
            [('Hue', 'OrientationMode2Preference')])
pg.add_plot('Second Orientation Preference&Selectivity',
            [('Hue', 'OrientationMode2Preference'),
             ('Confidence', 'OrientationMode2Selectivity')])
pg.add_plot('Second Orientation Selectivity',
            [('Strength', 'OrientationMode2Selectivity')])
pg.add_static_image('Color Key', 'static/or_key_white_vert_small.png')


pg = create_plotgroup(name='Second Peak Orientation Preference',
                      category="Preference Maps",
                      doc='Measure the second peak preference for sine '
                          'grating orientation.',
                      pre_plot_hooks=[
                          analysis.measure_second_or_pref.instance(true_peak=True)])
pg.add_plot('Second Peak Orientation Preference',
            [('Hue', 'OrientationMode2Preference')])
pg.add_plot('Second Peak Orientation Preference&Selectivity',
            [('Hue', 'OrientationMode2Preference'),
             ('Confidence', 'OrientationMode2Selectivity')])
pg.add_plot('Second Peak Orientation Selectivity',
            [('Strength', 'OrientationMode2Selectivity')])
pg.add_static_image('Color Key', 'static/or_key_white_vert_small.png')


pg = create_plotgroup(name='Two Peaks Orientation Preferences',
                      category='Preference Maps',
                      doc="""Display the two most preferred orientations for
                      all units with a multimodal orientation preference
                      distribution.""",
                      pre_plot_hooks=[
                          analysis.measure_second_or_pref.instance(num_orientation=16,
                                                          true_peak=True)])
pg.add_plot('Two Peaks Orientation Preferences',
            [('Or1', 'OrientationPreference'),
             ('Sel1', 'OrientationSelectivity'),
             ('Or2', 'OrientationMode2Preference'),
             ('Sel2', 'OrientationMode2Selectivity')])
pg.add_static_image('Color Key', 'static/two_or_key_vert.png')


pg = create_plotgroup(name='Corner OR Preference', category="Preference Maps",
                      doc='Measure orientation preference for corner shape ('
                          'or other complex stimuli that cannot be '
                          'represented as fullfield patterns).',
                      pre_plot_hooks=[analysis.measure_corner_or_pref.instance(
                          preference_fn=distribution.DSF_WeightedAverage())],
                      normalize='Individually')
pg.add_plot('Corner Orientation Preference', [('Hue', 'OrientationPreference')])
pg.add_plot('Corner Orientation Preference&Selectivity',
            [('Hue', 'OrientationPreference'),
             ('Confidence', 'OrientationSelectivity')])
pg.add_plot('Corner Orientation Selectivity',
            [('Strength', 'OrientationSelectivity')])


pg = create_plotgroup(name='Corner Angle Preference',
                      category="Preference Maps",
                      doc='Measure preference for angles in corner shapes',
                      normalize='Individually')
pg.pre_plot_hooks = [analysis.measure_corner_angle_pref.instance()]
pg.add_plot('Corner Angle Preference', [('Hue', 'AnglePreference')])
pg.add_plot('Corner Angle Preference&Selectivity',
            [('Hue', 'AnglePreference'), ('Confidence', 'AngleSelectivity')])
pg.add_plot('Corner Angle Selectivity', [('Strength', 'AngleSelectivity')])
pg.add_plot('Corner Orientation Preference', [('Hue', 'OrientationPreference')])
pg.add_plot('Corner Orientation Preference&Selectivity',
            [('Hue', 'OrientationPreference'),
             ('Confidence', 'OrientationSelectivity')])
pg.add_plot('Corner Orientation Selectivity',
            [('Strength', 'OrientationSelectivity')])
pg.add_static_image('Hue Code', 'static/key_angles.png')


pg= create_plotgroup(name='Position Preference',category="Preference Maps",
           doc='Measure preference for the X and Y position of a Gaussian.',
           pre_plot_hooks=[analysis.measure_position_pref.instance(
            preference_fn=distribution.DSF_WeightedAverage(selectivity_scale=(0.,17.) ))],
           plot_hooks=[pylabplot.topographic_grid.instance()],
           normalize='Individually')

pg.add_plot('X Preference',[('Strength','XPreference')])
pg.add_plot('Y Preference',[('Strength','YPreference')])
pg.add_plot('Position Preference',[('Red','XPreference'),
                                   ('Green','YPreference')])


create_plotgroup(template_plot_type="curve",name='Orientation Tuning Fullfield',category="Tuning Curves",doc="""
            Plot orientation tuning curves for a specific unit, measured using full-field sine gratings.
            Although the data takes a long time to collect, once it is ready the plots
            are available immediately for any unit.""",
        pre_plot_hooks=[analysis.measure_or_tuning_fullfield.instance()],
        plot_hooks=[pylabplot.cyclic_tuning_curve.instance(x_axis='orientation')])


create_plotgroup(template_plot_type="curve",name='Orientation Tuning',category="Tuning Curves",doc="""
            Measure orientation tuning for a specific unit at different contrasts,
            using a pattern chosen to match the preferences of that unit.""",
        pre_plot_hooks=[analysis.measure_or_tuning.instance()],
        plot_hooks=[pylabplot.cyclic_tuning_curve.instance(x_axis="orientation")],
        prerequisites=['XPreference'])


create_plotgroup(template_plot_type="curve",name='Size Tuning',category="Tuning Curves",
        doc='Measure the size preference for a specific unit.',
        pre_plot_hooks=[analysis.measure_size_response.instance()],
        plot_hooks=[pylabplot.tuning_curve.instance(x_axis='size')],
        prerequisites=['OrientationPreference','XPreference'])


create_plotgroup(template_plot_type="curve",name='Contrast Response',category="Tuning Curves",
        doc='Measure the contrast response function for a specific unit.',
        pre_plot_hooks=[analysis.measure_contrast_response.instance()],
        plot_hooks=[pylabplot.tuning_curve.instance(x_axis="contrast")],
        prerequisites=['OrientationPreference','XPreference'])


create_plotgroup(template_plot_type="curve",name='Frequency Tuning',category="Tuning Curves",
        doc='Measure the spatial frequency preference for a specific unit.',
        pre_plot_hooks=[analysis.measure_frequency_response.instance()],
                 plot_hooks=[pylabplot.tuning_curve.instance(x_axis="frequency")],
        prerequisites=['OrientationPreference','XPreference'])


create_plotgroup(template_plot_type="curve",name='Orientation Contrast',category="Tuning Curves",
                 doc='Measure the response of one unit to a center and surround sine grating disk.',
                 pre_plot_hooks=[analysis.measure_orientation_contrast.instance()],
                 plot_hooks=[pylabplot.cyclic_tuning_curve.instance(x_axis="orientationsurround", center=False,
                                                                    relative_labels=True)],
                 prerequisites=['OrientationPreference','XPreference'])

