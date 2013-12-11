"""
PlotgroupPanels for displaying ProjectionSheet plotgroups.
"""


import ImageTk
### JCALERT! Try not to have to use chain and delete this import.
from itertools import chain
from Tkinter import Canvas
from numpy import sometrue

import param

import topo
from topo.base.cf import CFProjection
from topo.base.projection import ProjectionSheet, Projection
from topo.base.generatorsheet import GeneratorSheet

from templateplotgrouppanel import SheetPanel



def cmp_projections(p1,p2):
    """
    Comparison function for Plots.
    It compares the precedence number first and then the src_name and name attributes.
    """
    if p1.src.precedence != p2.src.precedence:
        return cmp(p1.src.precedence,p2.src.precedence)
    else:
        return cmp(p1,p2)


UNIT_PADDING = 1



class ProjectionSheetPanel(SheetPanel):
    """
    Abstract base class for panels relating to ProjectionSheets.
    """
    __abstract = True

    sheet_type = ProjectionSheet
    projection_type = Projection

    @classmethod
    def valid_context(cls):
        """
        Return True if there is at least one instance of
        projection_type among all projections in the simulation.
        """
        for p in chain(*[sheet.projections().values()
                         for sheet in topo.sim.objects(cls.sheet_type).values()]):
            if isinstance(p,cls.projection_type):
                return True

        return False


    def __init__(self,master,plotgroup,**params):
        super(ProjectionSheetPanel,self).__init__(master,plotgroup,**params)

        self.plotgroup.auto_refresh=False

        self.pack_param('sheet',parent=self.control_frame_3,
            on_modify=self.sheet_change,side='left',expand=1,
            widget_options={'new_default':True,
                            'sort_fn_args':{'cmp':lambda x, y: cmp(-x.precedence,-y.precedence)}})


    def setup_plotgroup(self):
        super(ProjectionSheetPanel,self).setup_plotgroup()
        self.populate_sheet_param()
        self.populate_color_channel_param()

    def sheet_change(self):
        self.refresh_plots()


    def populate_sheet_param(self):
        sheets = [s for s in topo.sim.objects(self.sheet_type).values()
                  if sometrue([isinstance(p,self.projection_type)
                               for p in s.in_connections])]
        self.plotgroup.params()['sheet'].objects = sheets
        self.plotgroup.sheet = sheets[0] # CB: necessary?



class ProjectionActivityPanel(ProjectionSheetPanel):

    def __init__(self,master,plotgroup,**params):
        super(ProjectionActivityPanel,self).__init__(master,plotgroup,**params)
        self.auto_refresh = True

    def _plot_title(self):
        return "Activity in projections to %s at time %s"%(self.plotgroup.sheet.name,topo.sim.timestr(self.plotgroup.time))



class UnitsPanel(ProjectionSheetPanel):


    def __init__(self,master,plotgroup,**params):
        self.initial_args=params # CEBALERT: store the initial arguments so we can get sheet,x,y in
                                 # sheet_change if any of them were specified. Isn't there a cleaner
                                 # way?
        super(UnitsPanel,self).__init__(master,plotgroup,**params)
        self.pack_param('x',parent=self.control_frame_4,on_set=self.refresh_plots)
        self.pack_param('y',parent=self.control_frame_4,on_set=self.refresh_plots)
        self.sheet_change()


##############################################################################
        # CEBALERT:
        # - Need to couple taggedslider to a Number parameter in a better way
        # somewhere else.
        # - Clean up or document: passing the params, setting the bounds
        #
        # Also:
        # e.g. bound on parameter is 0.5 but means <0.5, taggedslider
        #   still lets you set to 0.5 -> error

    def sheet_change(self):
        # CEBHACKALERT: get an inconsequential but scary
        # cf-out-of-range error if you e.g. set y < -0.4 on sheet V1
        # and then change to V2 (which has smaller bounds).
        # x and y don't seem to be updated in time...
        #self.x,self.y = 0.0,0.0

        # CEBALERT: need to crop x,y (for e.g. going to smaller sheet) rather
        # than set to 0

        if 'sheet' in self.initial_args: self.sheet=self.initial_args['sheet']

        for coord in ['x','y']:
            self._tkvars[coord].set(self.initial_args.get(coord,0.0))

        l,b,r,t = self.sheet.bounds.lbrt()
        # CEBALERT: see "CEBERRORALERT: doesn't take account of
        # exclusive bounds" in topo/param/__init.__.py.
        D=0.0000000001
        bounds = {'x':(l,r-D),
                  'y':(b,t-D)}

        inclusive_bounds = {'x':(True,False),  # GUI knows about exclusive sheet bounds
                            'y':(False,True)}

        for coord in ['x','y']:
            param_obj=self.get_parameter_object(coord)
            param_obj.bounds = bounds[coord]
            param_obj.inclusive_bounds = inclusive_bounds[coord]

            # (method can be called before x,y widgets added)
            if coord in self.representations:
                w=self.representations[coord]['widget']
                w.set_bounds(param_obj.bounds[0],param_obj.bounds[1],
                             inclusive_bounds=param_obj.inclusive_bounds)
                w.tag_set()

        self.initial_args = {} # reset now we've used them
        super(UnitsPanel,self).sheet_change()
##############################################################################


class ConnectionFieldsPanel(UnitsPanel):

    projection_type = CFProjection

    def __init__(self,master,plotgroup,**params):
        super(ConnectionFieldsPanel,self).__init__(master,plotgroup,**params)
        self.pack_param('situate',parent=self.control_frame_3,on_set=self.situate_change,side='left',expand=1)

    def situate_change(self):
        self.redraw_plots()

    def _plot_title(self):
        return 'Connection Fields of %s unit (%4.3f,%4.3f) at time %s' % \
               (self.sheet.name, self.plotgroup.x,self.plotgroup.y,
                topo.sim.timestr(self.plotgroup.time))


class PlotMatrixPanel(ProjectionSheetPanel):
    """
    PlotGroupPanel for visualizing an array of bitmaps, such as for
    a projection involving a matrix of units.
    """

    gui_desired_maximum_plot_height = param.Integer(default=5,bounds=(0,None),doc="""
        Value to provide for PlotGroup.desired_maximum_plot_height for
        PlotGroups opened by the GUI.  Determines the initial, default
        scaling for the PlotGroup.""")

    def sheet_change(self): # don't want to refresh_plots (measure new data) each time
        self.redraw_plots()

    def refresh(self,update=True):
        super(PlotMatrixPanel,self).refresh(update)
        # take the size of the plot as the desired size
        self.plotgroup.update_maximum_plot_height()
        self.desired_maximum_plot_height = self.plotgroup.maximum_plot_height


    def display_plots(self):
        """
        CFProjectionPanel requires a 2D grid of plots.
        """
        plots=self.plotgroup.plots
        # Generate the zoomed images.
        self.zoomed_images = [ImageTk.PhotoImage(p.bitmap.image)
                              for p in plots]
        old_canvases = self.canvases

        self.canvases = [Canvas(self.plot_container,
                                width=image.width(),
                                height=image.height(),
                                borderwidth=1,highlightthickness=0,
                                relief='groove')
                         for image in self.zoomed_images]

        # Lay out images
        for i,image,canvas in zip(range(len(self.zoomed_images)),
                                  self.zoomed_images,self.canvases):
            canvas.grid(row=i//self.plotgroup.proj_plotting_shape[1],
                        column=i%self.plotgroup.proj_plotting_shape[1],
                        padx=UNIT_PADDING,pady=UNIT_PADDING)
            canvas.create_image(1,1,anchor='nw',image=image)


        # Delete old ones.  This may resize the grid.
        for c in old_canvases:
            c.grid_forget()

        self._add_canvas_bindings()


    def display_labels(self):
        """Do not display labels for these plots."""
        pass


class RFProjectionPanel(PlotMatrixPanel):

    sheet_type = ProjectionSheet

    def __init__(self,master,plotgroup,**params):
        super(RFProjectionPanel,self).__init__(master,plotgroup,**params)
        self.pack_param('input_sheet',parent=self.control_frame_3,
                        on_modify=self.redraw_plots,side='left',expand=1)

        self.pack_param('density',parent=self.control_frame_4)

    def setup_plotgroup(self):
        super(RFProjectionPanel,self).setup_plotgroup()
        self.populate_input_sheet_param()

    def populate_input_sheet_param(self):
        sheets = topo.sim.objects(GeneratorSheet).values()
        self.plotgroup.params()['input_sheet'].objects = sheets
        self.plotgroup.input_sheet=sheets[0]

    def _plot_title(self):
        return 'RFs of %s on %s at time %s'%(self.sheet.name,self.plotgroup.input_sheet.name,
                                             topo.sim.timestr(self.plotgroup.time))


class ProjectionPanel(PlotMatrixPanel):
    def __init__(self,master,plotgroup,**params):
        super(ProjectionPanel,self).__init__(master,plotgroup,**params)
        self.pack_param('projection',parent=self.control_frame_3,
                        on_modify=self.redraw_plots,side='left',expand=1,
                        widget_options={'sort_fn_args':{'cmp':cmp_projections},
                                        'new_default':True})

        self.pack_param('density',parent=self.control_frame_4)


    def _plot_title(self):
        return self.projection.name + ' projection from ' + self.projection.src.name + ' to ' \
               + self.sheet.name + ' at time ' + topo.sim.timestr(self.plotgroup.time)

    def setup_plotgroup(self):
        super(ProjectionPanel,self).setup_plotgroup()
        self.populate_projection_param()


    def sheet_change(self):
        self.refresh_projections()
        super(ProjectionPanel,self).sheet_change()


    def populate_projection_param(self):
        prjns = [proj for proj in self.plotgroup.sheet.projections().values()
                 if isinstance(proj,self.projection_type)]
        self.plotgroup.params()['projection'].objects = prjns
        self.plotgroup.projection = prjns[0] # CB: necessary?


    def refresh_projections(self):
        self.populate_projection_param()

        self.update_selector('projection')

##         #################
##         # CEBALERT: How do you change list of tkinter.optionmenu options? Use pmw's optionmenu?
##         # Or search the web for a way to alter the list in the tkinter one.
##         # Currently, replace widget completely: looks bad and is complex.
##         # When fixing, remove try/except marked by the 'for projectionpanel' CEBALERT in
##         # tkparameterizedobject.py.
##         if 'projection' in self.representations:
##             w  = self.representations['projection']['widget']
##             l  = self.representations['projection']['label']
##             l.destroy()
##             w.destroy()
##             self.pack_param('projection',parent=self.representations['projection']['frame'],
##                             on_modify=self.refresh_plots,side='left',expand=1,
##                             widget_options={'sort_fn_args':{'cmp':cmp_projections},
##                                             'new_default':True})
##         #################



class CFProjectionPanel(ProjectionPanel):
    """
    Panel for displaying CFProjections.
    """

    projection_type = CFProjection

    def __init__(self,master,plotgroup,**params):
        super(CFProjectionPanel,self).__init__(master,plotgroup,**params)
        self.pack_param('situate',parent=self.control_frame_3,on_set=self.situate_change,side='left',expand=1)

    def situate_change(self):
        self.redraw_plots()




## Need to add test file:
# check projection, sheet ordering
# check sheet changes, check projection changes



