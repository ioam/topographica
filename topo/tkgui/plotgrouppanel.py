"""
Classes providing GUI windows for PlotGroups, allowing sets of related plots
to be displayed.
"""


import copy

import ImageTk

import Tkinter
from Tkinter import  Frame, TOP, YES, BOTH, X, LEFT, \
     RIGHT, DISABLED, NORMAL, Canvas, Label, NSEW, \
     NO, NONE,TclError

import param
# CEBALERT: here and elsewhere, change tk to paramtk
import paramtk as tk

from topo.base.sheet import Sheet
from topo.base.cf import CFSheet

from topo.command.pylabplot import matrixplot

from topo.base.generatorsheet import GeneratorSheet

import topo

def with_busy_cursor(fn):
    """
    Decorator to show busy cursor for duration of fn call.
    """
    def busy_fn(widget,*args,**kw):
        if 'cursor' in widget.configure():
            old_cursor=widget['cursor']
            widget['cursor']='watch'
            widget.update_idletasks()

        try:
            fn(widget,*args,**kw)
        finally:
            # ensure old cursor is replaced even if fn() raises an
            # error
            if 'cursor' in widget.configure():
                widget['cursor']=old_cursor

    return busy_fn


class PlotGroupPanel(tk.TkParameterized,Frame):

    __abstract = True


    dock = param.Boolean(default=False,doc="on console or not")

    maximum_plot_history_length = param.Integer(default=20,bounds=(-1,None),doc="""
        Value of maximum plots history length. Larger number means a longer history 
        is kept and hence more memory is used. A length of -1 means keep all.""")

    # Default size for images used on buttons
    button_image_size=(20,20)

    Refresh = tk.Button(image_path="tkgui/icons/redo-small.png",
        size=button_image_size,
        doc="""
        Refresh the current plot (i.e. force the current plot to be regenerated
        by executing pre_plot_hooks and plot_hooks).""")

    Redraw = tk.Button(image_path="tkgui/icons/redo-small.png",
        size=button_image_size,
        doc="""Redraw the plot from existing data (i.e. execute plot_hooks only).""")

    Enlarge = tk.Button(image_path="tkgui/icons/viewmag+_2.2.png",
        size=button_image_size,
        doc="""Increase the displayed size of the current plots by about 20%.""")

    Reduce = tk.Button(image_path="tkgui/icons/viewmag-_2.1.png",
        size=button_image_size,doc="""
        Reduce the displayed size of the current plots by about 20%.
        A minimum size that preserves at least one pixel per unit is
        enforced, to ensure that no data is lost when displaying.""")

    Fwd = tk.Button(image_path="tkgui/icons/forward-2.0.png",
        size=button_image_size,doc="""
        Move forward through the history of all the plots shown in this window.""")

    Back = tk.Button(image_path="tkgui/icons/back-2.0.png",
        size=button_image_size,doc="""
        Move backward through the history of all the plots shown in
        this window.  When showing a historical plot, some functions
        will be disabled, because the original data is no longer
        available.""")

    gui_desired_maximum_plot_height = param.Integer(default=150,bounds=(0,None),doc="""
        Value to provide for PlotGroup.desired_maximum_plot_height for
        PlotGroups opened by the GUI.  Determines the initial, default
        scaling for the PlotGroup.""")

    # CB: is there a better way than using a property?
    def get_plotgroup(self):
        return self._extraPO
    def set_plotgroup(self,new_pg):
        self.change_PO(new_pg)

    plotgroup = property(get_plotgroup,set_plotgroup)


    def __init__(self,master,plotgroup,**params):
        """
        If your parameter should be available in history, add its name
        to the params_in_history list, otherwise it will be disabled
        in historical views.
        """

        tk.TkParameterized.__init__(self,master,extraPO=plotgroup,
                                    msg_handler=master.status,
                                    **params)
        Frame.__init__(self,master.content)

        self.parent = master #CEBALERT
        self.setup_plotgroup()





        self.canvases = []
        self.plot_labels = []

        ### JCALERT! Figure out why we need that!
        self._num_labels = 0

        self.plotgroups_history=[]
        self.history_index = 0
        self.params_in_history = [] # parameters valid to adjust in history

        # Factor for reducing or enlarging the Plots (where 1.2 = 20% change)
        self.zoom_factor = 1.2

        # CEBALERT: rename these frames
        self.control_frame_1 = Frame(master.noscroll)
        self.control_frame_1.pack(side=TOP,expand=NO,fill=X)

        self.control_frame_2 = Frame(master.noscroll)
        self.control_frame_2.pack(side=TOP,expand=NO,fill=X)

        self.plot_frame = Tkinter.LabelFrame(self,text=self.plotgroup.name)
        self.plot_frame.pack(side=TOP,expand=YES,fill=BOTH)#,padx=5,pady=5)

        # CB: why did I need a new frame after switching to 8.5?
        # I've forgotten what i changed.
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


        self.control_frame_3 = Frame(master.noscroll_bottom)
        self.control_frame_3.pack(side=TOP,expand=NO,fill=X)

        self.control_frame_4 = Frame(self)
        self.control_frame_4.pack(side=TOP,expand=NO,fill=NONE)

        self.updatecommand_frame = Frame(self.control_frame_3)
        self.updatecommand_frame.pack(side=TOP,expand=YES,fill=X)

        self.plotcommand_frame = Frame(self.control_frame_3)
        self.plotcommand_frame.pack(side=TOP,expand=YES,fill=X)


        # CEBALERT: replace
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


        self.pack_param('Enlarge',parent=self.control_frame_1,
                        on_set=self.enlarge_plots,side=LEFT)
        self.params_in_history.append('Enlarge') # CEBNOTE: while it's a GUI op

        self.pack_param('Reduce',parent=self.control_frame_1,
                        on_set=self.reduce_plots,side=LEFT)
        self.params_in_history.append('Reduce')


        if topo.tkgui.TK_SUPPORTS_DOCK:
            self.pack_param("dock",parent=self.control_frame_1,
                            on_set=self.set_dock,side=LEFT)


        # Don't need to add these two to params_in_history because their
        # availability is controlled separately (determined by what's
        # in the history)
        self.pack_param('Back',parent=self.control_frame_2,
                        on_set=lambda x=-1: self.navigate_pg_history(x),
                        side=LEFT)

        self.pack_param('Fwd',parent=self.control_frame_2,
                        on_set=lambda x=+1: self.navigate_pg_history(x),
                        side=LEFT)




        #################### RIGHT-CLICK MENU STUFF ####################
        ### Right-click menu for canvases; subclasses can add cascades
        ### or insert commands on the existing cascades.
        self._canvas_menu = tk.Menu(self, tearoff=0) #self.context_menu

        self._unit_menu = tk.Menu(self._canvas_menu, tearoff=0)
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

        self._sheet_menu = tk.Menu(self._canvas_menu, tearoff=0)
        self._canvas_menu.add_cascade(menu=self._sheet_menu,state=DISABLED,
                                      indexname='sheet_menu')
        self._canvas_menu.add_separator()


        self.update_plot_frame(plots=False)

        #################################################################

        # CB: don't forget to include ctrl-q
        # import __main__; __main__.__dict__['qqq']=self


    def set_dock(self):
        if self.dock:
            topo.guimain.some_area.consume(self.parent)
            self.refresh_title()
        else:
            topo.guimain.some_area.eject(self.parent)
            self.refresh_title()



    def setup_plotgroup(self):
        """
        Perform any necessary initialization of the plotgroup.

        Subclasses can use this to set Parameters on their PlotGroups.
        """
        self.plotgroup.desired_maximum_plot_height=self.gui_desired_maximum_plot_height


    def __process_canvas_event(self,event,func):
        """
        Return a dictionary containing the event itself, and, if the
        event occurs on a plot of a sheet, store the plot and the
        coordinates ((r,c) and (x,y) for the cell center) on the sheet.

        Then, call func.
        """
        # CB: I want this to be called for all the canvas events - see
        # ALERT by canvas button bindings. Surely can do better than
        # just passing func through.
        plot=event.widget.plot
        event_info = {'event':event} # store event in case more info needed elsewhere

        # Later functions assume that if event_info does not contain
        # 'plot', then the event did not occur on a plot of a sheet.
        if plot.plot_src_name is not '':
            plot_width,plot_height=plot.bitmap.width(),plot.bitmap.height()
            if 0<=event.x<plot_width and 0<=event.y<plot_height:
                left,bottom,right,top=plot.plot_bounding_box.lbrt()
                # float() to avoid integer division
                x = (right-left)*float(event.x)/plot_width + left
                y = top - (top-bottom)*float(event.y)/plot_height
                r,c = topo.sim[plot.plot_src_name].sheet2matrixidx(x,y)
                event_info['plot'] = plot
                event_info['coords'] = [(r,c),(x,y)]

        func(event_info)


    def _canvas_right_click(self,event_info,show_menu=True):
        """
        Update labels on right-click menu and popup the menu, plus store the event info
        for access by any menu commands that require it.

        If show_menu is False, popup menu is not displayed (in case subclasses
        wish to add extra menu items first).
        """
        if 'plot' in event_info:
            plot = event_info['plot']

            self._canvas_menu.entryconfig("sheet_menu",
                label="Combined plot: %s %s"%(plot.plot_src_name,plot.name),
                state=NORMAL)
            (r,c),(x,y) = event_info['coords']
            self._canvas_menu.entryconfig("unit_menu",
                label="Single unit:(% 3d,% 3d) Coord:(% 2.2f,% 2.2f)"%(r,c,x,y),
                state=NORMAL)
            self._right_click_info = event_info

            # CB: part of disable items hack
            for v in self._unit_menu_updaters.values(): v(plot)

            if show_menu:
                self._canvas_menu.tk_popup(event_info['event'].x_root,
                                           event_info['event'].y_root)




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


    # rename (not specific to plot_frame)
    # document, and make display_* methods semi-private methods
    def update_plot_frame(self,plots=True,labels=True,geom=False):
        """

        set geom True for any action that user would expect to lose
        his/her manual window size (e.g. pressing enlarge button)
        """

        if plots:
            self.plotgroup.scale_images()
            self.display_plots()
        if labels: self.display_labels()
        self.refresh_title()

        if len(self.canvases)==0:
            # CEB: check that pack's ok here
            self.no_plot_note.grid(row=1,column=0,sticky='nsew')
            self.no_plot_note_enabled=True
            self.representations['Enlarge']['widget']['state']=DISABLED
            self.representations['Reduce' ]['widget']['state']=DISABLED

        elif self.no_plot_note_enabled:
            self.no_plot_note.grid_forget()
            self.no_plot_note_enabled=False
            self.representations['Enlarge']['widget']['state']=NORMAL
            self.representations['Reduce' ]['widget']['state']=NORMAL

        self.__update_widgets_for_history()
        # have a general update_widgets method instead (that calls
        # update_widgets_for_history; can it also include
        # enlarge/reduce alterations?)

        # CBALERT: problem when docked: this event isn't being caught,
        # ie it doesn't end up going to the right place... (i.e. no
        # scrollbars when docked).
        #self.event_generate("<<SizeRight>>")
        self.parent.sizeright()
        if geom:
            try:
                self.parent.geometry('')
            except TclError:
                pass


    @with_busy_cursor
    def refresh_plots(self, update=True):
        """
        Call plotgroup's make_plots with update=True (i.e. run
        pre_plot_hooks and plot_hooks), then display the result.
        """
        self.plotgroup.make_plots(update)
        self.update_plot_frame()
        self.add_to_plotgroups_history()


    @with_busy_cursor
    def redraw_plots(self):
        """
        Call plotgroup's make_plots with update=False (i.e. run only
        plot_hooks, not pre_plot_hooks), then display the result.
        """
        self.plotgroup.make_plots(update=False)
        self.update_plot_frame(labels=False)


    def rescale_plots(self):
        """
        Rescale the existing plots, without calling either the
        plot_hooks or the pre_plot_hooks, then display the result.
        """
        self.plotgroup.scale_images()
        self.update_plot_frame(labels=False,geom=True)


    def refresh(self,update=True):
        """
        Main steps for generating plots in the Frame.

        # if update is True, the SheetViews are re-generated
        """

        # if we've been looking in the history, now need to return to the "current time"
        # plotgroup (but copy it: don't update the old one, which is a record of the previous state)
        if self.history_index!=0:
            self._switch_plotgroup(copy.copy(self.plotgroups_history[-1]))
            self.history_index = 0

        if update:
            self.refresh_plots()
        else:
            self.redraw_plots()


    # CEBALERT: this method needs cleaning, along with its versions in subclasses.
    def display_plots(self):
        """

        This function should be redefined in subclasses for interesting
        things such as 2D grids.
        """
        self._rows = [r*2 for (r,_,_) in self.plotgroup.coords] # Alternate rows for labelling
        self._cols = [c for (_,c,_) in self.plotgroup.coords]
        plots =      [p for (_,_,p) in self.plotgroup.coords]
        self.zoomed_images = [ImageTk.PhotoImage(p.bitmap.image) for p in plots]

        new_sizes = [(str(zi.width()),
                      str(zi.height()))
                     for zi in self.zoomed_images]
        old_sizes = [(canvas['width'],canvas['height'])
                     for canvas in self.canvases]

        # If the number of canvases or their sizes has changed, then
        # create a new set of canvases.  If the new images will fit into the
        # old canvases, reuse them (prevents flicker)


        if len(self.zoomed_images) != len(self.canvases) or \
               new_sizes != old_sizes:
            # Need new canvases...
            old_canvases = self.canvases
            self.canvases = [Canvas(self.plot_container,
                                    width=image.width(),
                                    height=image.height(),
                                    borderwidth=1,highlightthickness=0,
                                    relief='groove')
                             for image in self.zoomed_images]
            for i,image,canvas in zip(range(len(self.zoomed_images)),
                                      self.zoomed_images,self.canvases):
                canvas.create_image(1,1,anchor="nw",image=image)
                canvas.grid(row=self._rows[i],column=self._cols[i],padx=5)


            for c in old_canvases:
                c.grid_forget()


        else:
            # Don't need new canvases...
            for i,image,canvas in zip(range(len(self.zoomed_images)),
                                      self.zoomed_images,self.canvases):
                canvas.create_image(1,1,anchor="nw",image=image)
                canvas.grid(row=self._rows[i],column=self._cols[i],padx=5)

        self._add_canvas_bindings()


    def _add_canvas_bindings(self):
        ### plotting over; bind events to each canvas
        for plot,canvas in zip(self.plotgroup.plots,self.canvases):
            # Store the corresponding plot with each canvas so that the
            # plot information (e.g. scale_factor) will be available
            # for the right_click menu.
            canvas.plot=plot
            # CEBALERT: I want process_canvas_event to be called for
            # all of these bindings, with an additional method also
            # called to do something specific to the action. I'm sure
            # python has something that lets this be done in a clearer
            # way.
            canvas.bind('<<right-click>>',lambda event: \
                        self.__process_canvas_event(event,self._canvas_right_click))
            canvas.bind('<Motion>',lambda event: \
                        self.__process_canvas_event(event,self._update_dynamic_info))

            canvas.bind('<Leave>',lambda event: \
                        self.__process_canvas_event(event,self._update_dynamic_info))
            # When user has a menu up, it's often natural to click
            # elsewhere to make the menu disappear. Need to update the
            # dynamic information in that case. (Happens on OS X
            # anyway, but needed on Win and linux.)
            canvas.bind('<Button-1>',lambda event: \
                        self.__process_canvas_event(event,self._update_dynamic_info))






    def display_labels(self):
        """
        This function should be redefined by subclasses to match any
        changes made to display__plots().  Depending on the situation,
        it may be useful to make this function a stub, and display the
        labels at the same time the images are displayed.
        """

        if len(self.canvases) == 0:
            pass
        elif self._num_labels != len(self.canvases):
            old_labels = self.plot_labels
            self.plot_labels = [Label(self.plot_container,text=each)
                                 for each in self.plotgroup.labels]
            for i in range(len(self.plot_labels)):
                self.plot_labels[i].grid(row=self._rows[i]+1,column=self._cols[i],sticky=NSEW)
            for l in old_labels:
                l.grid_forget()
            self._num_labels = len(self.canvases)
        else:  # Same number of labels; reuse to avoid flickering.
            for i in range(len(self.plot_labels)):
                self.plot_labels[i].configure(text=self.plotgroup.labels[i])



    # CEBERRORALERT (minor): if no plot's displayed and I click
    # enlarge, then the enlarge button gets disabled. If I then press
    # refresh to get a plot, I can't enlarge it because the button's
    # disabled. Probably need to reset button status if the plots
    # change.
    def reduce_plots(self):
        """Function called by widget to reduce the plot size, when possible."""
        if (not self.plotgroup.scale_images(1.0/self.zoom_factor)):
            self.representations['Reduce']['widget']['state']=DISABLED
        self.representations['Enlarge']['widget']['state']=NORMAL
        self.update_plot_frame(labels=False,geom=True)

    def enlarge_plots(self):
        """Function called by widget to increase the plot size, when possible."""
        if (not self.plotgroup.scale_images(self.zoom_factor)):
            self.representations['Enlarge']['widget']['state']=DISABLED
        self.representations['Reduce']['widget']['state']=NORMAL
        self.update_plot_frame(labels=False,geom=True)


######################################################################
### HISTORY METHODS

    # CEBERRORALERT: history grows and grows! Consider what happens when
    # a window's open with auto-refresh and many plots are generated
    # (e.g. measure_rfs). And plotgroups might be much bigger than they
    # need to be.

    # CEBALERT: in a history research, a disabled widget does not display
    # up-to-date information (e.g. normalize checkbutton doesn't change).
    def add_to_plotgroups_history(self):
        """
        If there are plots on display, and we're not doing a history research,
        the plotgroup is stored in the history depending on the parameter 
        maximum_plot_history_length. If this parameter is -1, history is unlimited
        (except by your machine memory!!). If it is 0, then no history is saved. If
        it is N, then up to N plots are saved in history.
        """
        if self.history_index==0 and not len(self.canvases)==0:
            # Only keep history length
            if len(self.plotgroups_history) > self.maximum_plot_history_length:
                try:
                    del self.plotgroups_history[0]
                except IndexError:
                    pass
            if self.maximum_plot_history_length > 0:
                self.plotgroups_history.append(copy.copy(self.plotgroup))
        self.__update_widgets_for_history()

    def __set_widget_state(self,widget,state):
        # sets the widget's state to state, unless state=='normal'
        # and the widget's current state is 'readonly', in which
        # case readonly is preserved.
        # If a widget state was set to 'disabled' deliberately, this
        # will have the unwanted effect of enabling that widget.
        # Surely there's a better way than this!
        # (Probably the history stuff should store the old state
        # on the widget somewhere. That would also eliminate the
        # combobox-specific hack.)

        # CEBALERT: I guess some widgets don't have state?
        try:
            current_state = widget.configure('state')[3]  # pyflakes:ignore (try/except test)
        except TclError:
            return

        ### hack to deal with combobox: see tkparameterizedobject's
        ###  create_selector_widget().
        if state=='normal':
            if hasattr(widget,'_readonly_'):
                state='readonly'
        ###########################################################

        widget.configure(state=state)


    def __update_widgets_for_history(self):
        """
        The plotgroup's non-history widgets are all irrelevant when the plotgroup's from
        history.
        """
        if self.history_index!=0:
            state= 'disabled'
        else:
            state = 'normal'

        widgets_to_update = [self.representations[p_name]['widget']
                             for p_name in self.representations
                             if p_name not in self.params_in_history]

        for widget in widgets_to_update:
            self.__set_widget_state(widget,state)

        self.__update_history_buttons()


    def __update_history_buttons(self):
        """
        Enable/disable the back and forward buttons depending on
        where we are in a history research.
        """
        space_back = len(self.plotgroups_history)+self.history_index-1
        space_fwd  = -self.history_index

        back_button = self.representations['Back']['widget']
        forward_button = self.representations['Fwd']['widget']

        if space_back>0:
            back_button['state']='normal'
        else:
            back_button['state']='disabled'

        if space_fwd>0:
            forward_button['state']='normal'
        else:
            forward_button['state']='disabled'

    # JLENHANCEMENT: It would be nice to be able to scroll back through many
    # iterations.  Could put in a box for entering either the iteration
    # number you want to view, or perhaps how many you want to jump...
    def navigate_pg_history(self,steps):
        self.history_index+=steps
        self._switch_plotgroup(self.plotgroups_history[len(self.plotgroups_history)+self.history_index-1])
        self.update_plot_frame()

######################################################################


    def _switch_plotgroup(self,newpg):
        """
        Switch to a different plotgroup, e.g. one from the history buffer.
        Preserves some attributes from the current plotgroup that can apply
        across history, but leaves the others as-is.
        """
        oldpg=self.plotgroup

        newpg.desired_maximum_plot_height=oldpg.desired_maximum_plot_height
        newpg.sheet_coords=oldpg.sheet_coords
        newpg.integer_scaling=oldpg.integer_scaling

        self.plotgroup=newpg


###########################################################



    def _plot_title(self):
        """
        Provide a string describing the current set of plots.

        Override in subclasses to provide more information.
        """
        return "%s at time %s"%(self.plotgroup.name,topo.sim.timestr(self.plotgroup.time))


    # rename to refresh_titles
    def refresh_title(self):
        """
        Set Window title and plot frame's title.
        """
        title = self._plot_title()

        self.plot_frame.configure(text=title)
        self.parent.title(str(topo.sim.name)+": "+title)
        # JABALERT: Used to say .replace(" at time ","/"); was there a reason?

    def destroy(self):
        """overrides toplevel destroy, adding removal from autorefresh panels"""
        if self in topo.guimain.auto_refresh_panels:
            topo.guimain.auto_refresh_panels.remove(self)
        Frame.destroy(self)



class SheetPanel(PlotGroupPanel):

    sheet_type = Sheet

    @classmethod
    def valid_context(cls):
        """
        Return true if there appears to be data available for this type of plot.

        To avoid confusing error messages, this method should be
        defined to return False in the case where there is no
        appropriate data to plot.  This information can be used to,
        e.g., gray out the appropriate menu item.
        By default, PlotPanels are assumed to be valid only for
        simulations that contain at least one Sheet.  Subclasses with
        more specific requirements should override this method with
        something more appropriate.
        """
        if topo.sim.objects(cls.sheet_type).items():
            return True
        else:
            return False


    def __init__(self,master,plotgroup,**params):
        super(SheetPanel,self).__init__(master,plotgroup,**params)

        self.pack_param('auto_refresh',parent=self.control_frame_1,
                        on_set=self.set_auto_refresh,
                        side=RIGHT)
        self.params_in_history.append('auto_refresh')

        if self.auto_refresh:
            topo.guimain.auto_refresh_panels.append(self)


        self.pack_param('normalize',parent=self.control_frame_1,
                        on_set=self.redraw_plots,side="right")
        self.pack_param('integer_scaling',parent=self.control_frame_2,
                        on_set=self.rescale_plots,side='right')
        self.pack_param('sheet_coords',parent=self.control_frame_2,
                        on_set=self.rescale_plots,side='right')

        self.params_in_history.append('sheet_coords')
        self.params_in_history.append('integer_scaling')



        self._unit_menu.add_command(label='Connection Fields',indexname='connection_fields',
                                    command=self._connection_fields_window)

        self._unit_menu.add_command(label='Receptive Field',
                                    indexname='receptive_field',
                                    command=self._receptive_field_window)

        self._unit_menu.add_command(label='Orientation Tuning Curves',
                                    indexname='or tuning curve',
                                    command=self._or_tuning_curve_window)

###### part of disable items hack #####
        self._unit_menu_updaters['connection_fields'] = self.check_for_cfs
        self._unit_menu_updaters['receptive_field'] = self.check_for_rfs

    def check_for_cfs(self,plot):
        show_cfs = False
        if plot.plot_src_name in topo.sim.objects():
            if isinstance(topo.sim[plot.plot_src_name],CFSheet):
                show_cfs = True
        self.__showhide("connection_fields",show_cfs)

    def check_for_rfs(self,plot):
        show_rfs = False
        if plot.plot_src_name in topo.sim.objects():
            sheet = topo.sim[plot.plot_src_name]

            # RFHACK: if any one generator has RF views for this sheet, then enable the menu option
            # At the moment, just a hack to prevent menu option for generator sheets.
            if not isinstance(sheet,GeneratorSheet):
                show_rfs = True
            else:
                show_rfs = False

        self.__showhide("receptive_field",show_rfs)

    def __showhide(self,name,show):
        if show:
            state = 'normal'
        else:
            state = 'disabled'
        self._unit_menu.entryconfig(name,state=state)
#######################################


    def set_auto_refresh(self):
        """
        Add or remove this panel from the console's
        auto_refresh_panels list.
        """
        if self.auto_refresh:
            if not (self in topo.guimain.auto_refresh_panels):
                topo.guimain.auto_refresh_panels.append(self)
        else:
            if self in topo.guimain.auto_refresh_panels:
                topo.guimain.auto_refresh_panels.remove(self)



    def _connection_fields_window(self):
        """
        Open a Connection Fields plot for the unit currently
        identified by a right click.
        """
        if 'plot' in self._right_click_info:
            sheet = topo.sim[self._right_click_info['plot'].plot_src_name]
            # CEBERRORALERT: should avoid requesting cf out of range.
            center_x,center_y = self._right_click_info['coords'][1]
            topo.guimain['Plots']["Connection Fields"](x=center_x,y=center_y,sheet=sheet)


    def _receptive_field_window(self):
        """
        Open a Receptive Field plot for the unit currently
        identified by a right click.
        """
        if 'plot' in self._right_click_info:
            plot = self._right_click_info['plot']
            sheet = topo.sim[plot.plot_src_name]
            center_x,center_y=self._right_click_info['coords'][1]
            r,c = self._right_click_info['coords'][0]

            # RFHACK:
            # just matrixplot for whatever generators have the views
            for g in topo.sim.objects(GeneratorSheet).values():
                try:
                    view = sheet.views.RFs[g.name][center_x, center_y]
                    matrixplot(view.last.data,title=("Receptive Field of %s unit (%d,%d) at coord (%3.0f, %3.0f) at time %s" %
                                                    (sheet.name,r,c,center_x,center_y,topo.sim.timestr(view.timestamp))))
                except:
                    # maybe lose this warning
                    topo.sim.warning("No RF measurements are available yet for input_sheet %s; run the Receptive Field plot for that input_sheet to see the RF."%g.name)


    def _or_tuning_curve_window(self):
        """
        Open a Tuning Curve plot for the unit currently
        identified by a right click.
        """
        if 'plot' in self._right_click_info:
            plot = self._right_click_info['plot']
            sheet = topo.sim[plot.plot_src_name]
            center_x,center_y=self._right_click_info['coords'][1]
            r,c = self._right_click_info['coords'][0]

            try:
                from topo.command.pylabplot import cyclic_tuning_curve
                cyclic_tuning_curve(x_axis="orientation",coords=[(center_x,center_y)],sheet=sheet)
            except AttributeError:
                topo.sim.warning("No orientation tuning curve measurements are available yet for sheet %s; run the Orientation Tuning (Fullfield) command and try again."%sheet.name)


    def conditional_refresh(self):
        """
        Only calls refresh() if auto_refresh is enabled.
        """
        if self.auto_refresh:self.refresh()

    def conditional_redraw(self):
        """
        Only calls redraw_plots() if auto_refresh is enabled.
        """
        if self.auto_refresh:self.redraw_plots()
