"""
class TemplatePlotGroupPanel
Panel for displaying preference maps and activity plot groups.
"""


import copy

from Tkinter import DISABLED, NORMAL
from tkFileDialog import asksaveasfilename

import param
from param import normalize_path
import paramtk as tk

import topo.command.pylabplot
from topo.plotting.plotgroup import TemplatePlotGroup

from plotgrouppanel import SheetPanel


### CEBALERT: additional dynamic info/right-click problems:
#
# If I open an Activity plot and then measure an orientation map,
# the plot only shows Activity, but the dynamic info includes the or
# pref and selectivity.  That makes sense, given that the plot would
# show that if it were refreshed, but it's confusing.




# CEBALERT: should  be something in plot or wherever, or maybe I don't see how to get this
# info the easy way from it? Not sure I actually wrote this correctly, anyway.
def available_plot_channels(plot):
    """
    Return the channels+names of the channels that have views.
    """
    available_channels = {}
    for name,channel in plot.channels.items():
        if plot.view_dict.has_key(channel):
            available_channels[name]=channel
    return available_channels




### CB: I'm working here at the moment.

class TemplatePlotGroupPanel(SheetPanel):

    plotgroup_type = TemplatePlotGroup

    strength_only = param.Boolean(default=False,doc="""If true, disables all but the Strength channel of each plot,
disabling all color coding for Strength/Hue/Confidence plots.""")

    ####################################################################
    # CEBALERT: Ugly hack!  Basic idea for method (deleting conf & hue
    # from plot_templates) copied from previous tkgui.  Instead, we
    # probably want a mechanism for doing this from the command line,
    # probably a global 'monochrome' parameter that all plots respect,
    # and then people can modify the plot templates directly if they
    # need more control than that.
    def _strength_only_hack(self):
        # same as superclass, except that if strength only is true
        # it temporarily removes hue&conf from plot_templates
        original_templates = self.plotgroup.plot_templates
        self.plotgroup.plot_templates = copy.deepcopy(self.plotgroup.plot_templates)
        if self.strength_only:
            for name,template in self.plotgroup.plot_templates:
                for c in ['Confidence','Hue']:
                    if c in template:
                        del template[c]
        return original_templates

    def refresh_plots(self):
        # same as superclass, except that if strength only is true
        # it temporarily removes hue&conf from plot_templates
        original_templates = self._strength_only_hack()
        super(TemplatePlotGroupPanel,self).refresh_plots()
        self.plotgroup.plot_templates = original_templates

    def redraw_plots(self):
        # same as superclass, except that if strength only is true
        # it temporarily removes hue&conf from plot_templates
        original_templates = self._strength_only_hack()
        super(TemplatePlotGroupPanel,self).redraw_plots()
        self.plotgroup.plot_templates = original_templates


    ## CB: update init args now we have no pgts.
    def __init__(self,master,plotgroup,**params):

        super(TemplatePlotGroupPanel,self).__init__(master,plotgroup,**params)

        self.pack_param('strength_only',parent=self.control_frame_1,
                        on_set=self.redraw_plots,side='right')

        # Display any plots that can be done with existing data, but
        # don't regenerate the SheetViews unless requested
        if self.plotgroup.plot_immediately:
            self.refresh_plots()
        else:
            self.redraw_plots()
            self.display_labels() # should this be called for any redraw? genuinely needs to be
            # called here because labels might never have been drawn.


        #################### RIGHT-CLICK MENU STUFF ####################
        self._sheet_menu.add_command(label="Save image as PNG",
                                     command=self.__save_to_png)


        self._sheet_menu.add_command(label="Save image as EPS",
                                     command=self.__save_to_postscript)


        self._unit_menu.add_command(label="Print info",
                                    command=self.__print_info)

        # JABALERT: Shouldn't be assuming SHC here; should also work
        # for RGB (or any other channels).
        channel_menus={}
        for chan in ['Strength','Hue','Confidence']:
            newmenu = tk.Menu(self._canvas_menu, tearoff=0)
            self._canvas_menu.add_cascade(menu=newmenu,label=chan+' channel', indexname=chan)

            # The c=chan construction is required so that each lambda has its own copy of the string
            newmenu.add_command(label="Print matrix",          command=lambda c=chan: self.__print_matrix(c))
            newmenu.add_command(label="Plot in sheet coords",  command=lambda c=chan: self.__plot_sheet_matrix(c))
            newmenu.add_command(label="Plot in matrix coords", command=lambda c=chan: self.__plot_matrix(c))
            newmenu.add_command(label="Plot as 3D wireframe",  command=lambda c=chan: self.__plot_matrix3d(c))
            newmenu.add_command(label="Fourier transform",     command=lambda c=chan: self.__fft(c))
            newmenu.add_command(label="Autocorrelation",       command=lambda c=chan: self.__autocorrelate(c))
            newmenu.add_command(label="Histogram",             command=lambda c=chan: self.__histogram(c))
            newmenu.add_command(label="Gradient",              command=lambda c=chan: self.__gradient(c))
            channel_menus[chan]=newmenu


        #self._sheet_menu.add_command(label="Print matrix values",
        #                             command=self.__print_matrix)
        #################################################################





    ### JABALERT: Should remove the assumption that the plot will be
    ### SHC (could e.g.  be RGB).
    ###
    ### Should add the ability to turn off any of the channels
    ### independently (just as the Strength-only button does), and
    ### eventually should allow the user to type in the name of any
    ### SheetView to change the template as desired to visualize any
    ### quantity.
    ###
    # CB: something about these methods does not seem to fit the PlotGroup hierarchy.
    def _canvas_right_click(self,event_info):
        """
        Make whichever of the SHC channels is present in the plot available on the menu.
        """
        super(TemplatePlotGroupPanel,self)._canvas_right_click(event_info,show_menu=False)

        if 'plot' in event_info:
            plot = event_info['plot']

            available_channels =available_plot_channels(plot)

            for channel in ('Strength','Hue','Confidence'):
                if channel in available_channels:
                    self._canvas_menu.entryconfig(channel,
                                                  label="%s channel: %s" %
                                                  (channel,str(plot.channels[channel])),state=NORMAL)
                else:
                    self._canvas_menu.entryconfig(channel,
                                                  label="%s channel: None" %
                                                  (channel),state=DISABLED)

            self._canvas_menu.tk_popup(event_info['event'].x_root,
                                       event_info['event'].y_root)


    def __save_to_png(self):
        plot   = self._right_click_info['plot']
        filename = self.plotgroup.filesaver.filename(plot.label(),file_format="png")
        PNG_FILETYPES = [('PNG images','*.png'),('All files','*')]
        snapshot_name = asksaveasfilename(filetypes=PNG_FILETYPES,
                                          initialdir=normalize_path(),
                                          initialfile=filename)

        if snapshot_name:
            plot.bitmap.image.save(snapshot_name)

    # based on routine in editor.py
    def __save_to_postscript(self):
        plot   = self._right_click_info['plot']
        canvas = self._right_click_info['event'].widget
        filename = self.plotgroup.filesaver.filename(plot.label(),file_format="eps")
        POSTSCRIPT_FILETYPES = [('Encapsulated PostScript images','*.eps'),
                                ('PostScript images','*.ps'),('All files','*')]
        snapshot_name = asksaveasfilename(filetypes=POSTSCRIPT_FILETYPES,
                                          initialdir=normalize_path(),
                                          initialfile=filename)

        if snapshot_name:
            canvas.postscript(file=snapshot_name)

    # CB: these methods assume channel has a view (the menu only displays those that do)
    def __fft(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        m=plot._get_matrix(channel)
        topo.command.pylabplot.fftplot(m, title="FFT Plot: " + description)

    def __autocorrelate(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        m=plot._get_matrix(channel)
        topo.command.pylabplot.autocorrelationplot(m, title="Autocorrelation: " + description)

    def __histogram(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        m=plot._get_matrix(channel)
        topo.command.pylabplot.histogramplot(m,title="Histogram: "+ description)

    def __gradient(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        m=plot._get_matrix(channel)
        view = plot.view_dict[plot.channels[channel]]
        topo.command.pylabplot.gradientplot(m,title="Gradient: " + description,
                                              cyclic=view.cyclic,cyclic_range=view.cyclic_range)

    def __print_matrix(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        print ("#" + description)
        m=plot._get_matrix(channel)
        print m

    def __plot_matrix(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        m=plot._get_matrix(channel)
        topo.command.pylabplot.matrixplot(m, title=description)

    def __plot_sheet_matrix(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        m=plot._get_matrix(channel)
        topo.command.pylabplot.activityplot(topo.sim[plot.plot_src_name], m, title=description)

    def __plot_matrix3d(self,channel):
        plot = self._right_click_info['plot']
        description = "%s %s at time %s" % (plot.plot_src_name, plot.name, topo.sim.timestr())
        m=plot._get_matrix(channel)
        topo.command.pylabplot.matrixplot3d(m, title=description)

    # CEBALERT: decide if and how to allow any of these functions to be used for getting as many
    # channels' info as possible.
    # e.g. in this one...
    def __print_info(self,channel=None):
        plot = self._right_click_info['plot']
        (r,c),(x,y) = self._right_click_info['coords']
        description ="%s %s, row %d, col %d at time %s: " % (plot.plot_src_name, plot.name, r, c, topo.sim.timestr())

        channels_info = ""
        if channel is None:
            for channel,name in available_plot_channels(plot).items():
                m=plot._get_matrix(channel)
                channels_info+="%s:%f"%(name,m[r,c])
        else:
            m=plot._get_matrix(channel)
            channels_info+="%s:%f"%(plot.channels[channel],m[r,c])

        print "%s %s" % (description, channels_info)





    def _dynamic_info_string(self,event_info,basic_text):
        """
        Also print whatever other channels are there and have views.
        """
        plot = event_info['plot']
        r,c = event_info['coords'][0]

        info_string = basic_text

        for channel,channel_name in available_plot_channels(plot).items():
            info_string+=" %s: % 1.3f"%(channel_name,plot._get_matrix(channel)[r,c])

        return info_string





