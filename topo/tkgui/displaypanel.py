"""
Class providing GUI windows for PlotGroupPanels, a panel in which sets of relatedplots
to be displayed.

$Id$
"""
__version__='$Revision$'


import Tkinter
from Tkinter import  Frame, TOP, BOTTOM, YES, BOTH, X, LEFT, \
     RIGHT, DISABLED, Canvas, Label, \
     NO, NONE

import param
import paramtk as paramtk

import topo


class DisplayPanel(paramtk.TkParameterized,Frame):

    __abstract = True

    # the Following Parameters will be displayed by default on any subclass implementing DisplayPanel
    # This is done for consistency reasons


    dock = param.Boolean(default=False,doc="on console or not")

    button_image_size=(20,20)

    Refresh = paramtk.Button(image_path="tkgui/icons/redo-small.png",
        size=button_image_size,
        doc="""
        Refresh the current plot (i.e. force the current plot to be regenerated
        by executing pre_plot_hooks and plot_hooks).""")

    Redraw = paramtk.Button(image_path="tkgui/icons/redo-small.png",
        size=button_image_size,
        doc="""Redraw the plot from existing data (i.e. execute plot_hooks only).""")
    
    Enlarge = paramtk.Button(image_path="tkgui/icons/viewmag+_2.2.png",
        size=button_image_size,
        doc="""Increase the displayed size of the current plots by about 20%.""")
                          
    Reduce = paramtk.Button(image_path="tkgui/icons/viewmag-_2.1.png",
        size=button_image_size,doc="""
        Reduce the displayed size of the current plots by about 20%.
        A minimum size that preserves at least one pixel per unit is
        enforced, to ensure that no data is lost when displaying.""")

    Fwd = paramtk.Button(image_path="tkgui/icons/forward-2.0.png",
        size=button_image_size,doc="""
        Move forward through the history of all the plots shown in this window.""")

    Back = paramtk.Button(image_path="tkgui/icons/back-2.0.png",
        size=button_image_size,doc="""
        Move backward through the history of all the plots shown in
        this window.  When showing a historical plot, some functions
        will be disabled, because the original data is no longer
        available.""")

    gui_desired_maximum_plot_height = param.Integer(default=150,bounds=(0,None),doc="""
        Value to provide for PlotGroup.desired_maximum_plot_height for
        PlotGroups opened by the GUI.  Determines the initial, default
        scaling for the PlotGroup.""")
    

    def __init__(self,master,_extraPO=None,**params):
        """
        If your parameter should be available in history, add its name
        to the params_in_history list, otherwise it will be disabled
        in historical views.
        """
        paramtk.TkParameterized.__init__(self,master,extraPO=_extraPO,
                                        msg_handler=master.status,
                                        **params)
        Frame.__init__(self,master.content)

        self.parent = master
        self.canvases = []
        self.plot_labels = []
        self.params_in_history=[]


        self._num_labels = 0
        self.history_index = 0
        
                                  
        # Factor for reducing or enlarging the Plots (where 1.2 = 20% change)
        self.zoom_factor = 1.2
        
        # These frames define the area that the standard Parameters will be packed. They are displayed in two rows
        # represented by two frames    

        self.standard_frame_top = Frame(master.noscroll)    # Used to be control_frame_1
        self.standard_frame_top.pack(side=TOP,expand=NO,fill=X)

        self.standard_frame_bottom = Frame(master.noscroll) # Used to be control_frame_2
        self.standard_frame_bottom.pack(side=TOP,expand=NO,fill=X)

        self.plot_frame = Tkinter.LabelFrame(self,text=self._extraPO.name)
        self.plot_frame.pack(side=TOP,expand=YES,fill=BOTH)    

        self.plot_container = Tkinter.Frame(self.plot_frame)
        self.plot_container.pack(anchor="center")


        # Label does have a wraplength option...but it's in screen
        # units. Surely tk has a function to convert between
        # text and screen units?
        no_plot_note_text = """      
Press Refresh on the pre-plot hooks to generate the plot, after modifying the hooks below if necessary. Note that Refreshing may take some time.

Many hooks accept 'display=True' so that the progress can be viewed in an open Activity window, e.g. for debugging.
"""

        self.no_plot_note=Label(self.plot_container,text=no_plot_note_text,
                                justify="center",wraplength=350)
        self.no_plot_note_enabled=False

        # The frame that holds the two hook bars
        self.hooks_frame = Frame(master.noscroll_bottom)    # Used to be control_frame_3
        self.hooks_frame.pack(side=BOTTOM,expand=NO,fill=X)

        self.control_frame_4 = Frame(self)
        self.control_frame_4.pack(side=TOP,expand=NO,fill=NONE)

        self.updatecommand_frame = Frame(self.hooks_frame)
        self.updatecommand_frame.pack(side=TOP,expand=YES,fill=X)

        self.plotcommand_frame = Frame(self.hooks_frame)
        self.plotcommand_frame.pack(side=TOP,expand=YES,fill=X)


        self.messageBar = self.parent.status 

        self.pack_param('pre_plot_hooks',parent=self.updatecommand_frame,
                        expand='yes',fill='x',side='left')

        self.pack_param('Refresh',parent=self.updatecommand_frame,
                        on_set=self.refresh,side='right')
        self.params_in_history.append('Refresh')

        self.pack_param('plot_hooks',parent=self.plotcommand_frame,
                        expand='yes',fill='x',side='left')
        # CEBALERT: should disable unless data exists.
        self.pack_param('Redraw',parent=self.plotcommand_frame,
                        on_set=self.redraw_plots,side='right')
        
            
        self.pack_param('Enlarge',parent=self.standard_frame_top,
                        on_set=self.enlarge_plots,side=LEFT)
        self.params_in_history.append('Enlarge')

        self.pack_param('Reduce',parent=self.standard_frame_top,
                        on_set=self.reduce_plots,side=LEFT)
        self.params_in_history.append('Reduce')


        if topo.tkgui.TK_SUPPORTS_DOCK:
            self.pack_param("dock",parent=self.standard_frame_top,
                            on_set=self.set_dock,side=LEFT)


        # Don't need to add these two to params_in_history because their
        # availability is controlled separately (determined by what's
        # in the history)
        self.pack_param('Back',parent=self.standard_frame_bottom,
                        on_set=lambda x=-1: self.navigate_pg_history(x),
                        side=LEFT)

        self.pack_param('Fwd',parent=self.standard_frame_bottom,
                        on_set=lambda x=+1: self.navigate_pg_history(x),
                        side=LEFT)


        #################### RIGHT-CLICK MENU STUFF ####################
        ### Right-click menu for canvases; subclasses can add cascades
        ### or insert commands on the existing cascades.
        self._canvas_menu = paramtk.Menu(self, tearoff=0) #self.context_menu 

        self._unit_menu = paramtk.Menu(self._canvas_menu, tearoff=0)
        self._canvas_menu.add_cascade(menu=self._unit_menu,state=DISABLED,
                                      indexname='unit_menu')

        self._canvas_menu.add_separator()
        
        # CEBALERT: scheme for enabling/disabling menu items ('disable
        # items hack') needs to be generalized. What we have now is
        # just a mechanism to disable/enable cfs/rfs plots as
        # necessary. Hack includes the attribute below as well as
        # other items marked 'disable items hack'.
        # (Note that tk 8.5 has better handling of state switching
        # (using flags for each state, I think), so presumably this
        # can be cleaned up easily.)
        self._unit_menu_updaters = {}
        
        self._sheet_menu = paramtk.Menu(self._canvas_menu, tearoff=0)
        self._canvas_menu.add_cascade(menu=self._sheet_menu,state=DISABLED,
                                      indexname='sheet_menu')
        self._canvas_menu.add_separator()


        #################################################################


    # This will give all subclasses of DisplayPanel the ability to dock to the main window    

    def set_dock(self):
        if self.dock:
            topo.guimain.some_area.consume(self.parent)
            self.refresh_title()
        else:
            topo.guimain.some_area.eject(self.parent)
            self.refresh_title()
            

    def _update_dynamic_info(self,event_info):
        """
        Update dynamic information.
        """
        if 'plot' in event_info:
            plot = event_info['plot']
            (r,c),(x,y) = event_info['coords']
            location_string="%s Unit:(% 3d,% 3d) Coord:(% 2.2f,% 2.2f)"%(plot.plot_src_name,r,c,x,y)
            # CB: isn't there a nicer way to allow more info to be added?
            self.messageBar.dynamicinfo(self._dynamic_info_string(event_info,location_string))
        else:
            self.messageBar.dynamicinfo('')

        
    def _dynamic_info_string(self,event_info,x):
        """
        Subclasses can override to add extra relevant information.
        """
        return x


    def _plot_title(self):
        """
        Provide a string describing the current set of plots.

        Override in subclasses to provide more information.
        """
        return "%s at time %s"%(self._extraPO.name,topo.sim.timestr(self._extraPO.time))        

   
    def refresh_title(self):
        """
        Set Window title and plot frame's title.
        """
        title = self._plot_title()
        
        self.plot_frame.configure(text=title)
        self.parent.title(str(topo.sim.name)+": "+title)
    
    def destroy(self):
        """overrides toplevel destroy, adding removal from autorefresh panels"""
        if self in topo.guimain.auto_refresh_panels:
            topo.guimain.auto_refresh_panels.remove(self)
        Frame.destroy(self)        
