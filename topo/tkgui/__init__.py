"""
Tk-based graphical user interface (GUI).

This package implements a Topographica GUI based on the Tk toolkit,
through the Tkinter interface to Python.  The rest of Topographica
does not depend on this package or any module in it, and thus other
GUIs or other types of interfaces can also be used.
"""

import sys
import os
import platform
import Tkinter

import paramtk

import topo

from topoconsole import TopoConsole,ControllableMenu

#### notes about tkgui ####
#
## Geometry management
# In several places we use pack() when grid() would probably be
# simpler. Check you know which fits a task better rather than copying
# existing code.
#
## Dialogs
# Don't know how to theme them (can't make them inherit from
# our own class, for instance). Consider making our own dialog
# boxes (subclass of Tkguiwindow) using transient and grab_set:
# http://thread.gmane.org/gmane.comp.python.tkinter/657/focus=659
#
## Mainloop
# Because we don't call mainloop(), it's necessary to call
# update() or update_idletasks() sometimes. Also, I think that sometimes
# current graphics do not update properly (but I'm not sure - I don't
# have a specific example yet). Need to clean up all the scattered
# update() and update_idletasks()...
#
## Window or Frame?
# Maybe one day everything (PlotGroupPanels, ParametersFrameWithApplys,
# ModelEditor, ...) will be Frames inside one master window (for
# e.g. a matlab-like workspace).  Nobody's been worrying too much
# about whether something's a Frame or a window when they've been
# implementing things, so 'close' buttons, title methods, and so on
# are a bit of a mix. This needs to be cleaned up when we have a
# final window organization method in mind.


# When not using the GUI, Topographica does not ordinarily import any of
# the classes in the separate Topographica packages. For example, none
# of the pattern types in topo.patterns is imported in Topographica by
# default.  But for the GUI, we want all such things to be available
# as lists from which the user can select.  To do this, we import all
# pattern types and other such classes here. User-defined classes will
# also appear in the GUI menus if they are derived from any class
# derived from the one specified in each widget, and imported before
# the relevant GUI window starts.
from topo.coordmapper import *  # pyflakes:ignore (see comment above)
from topo.base.ep import *  # pyflakes:ignore (see comment above)
from topo.learningfn import *  # pyflakes:ignore (see comment above)
from topo.transferfn import *  # pyflakes:ignore (see comment above)
from topo.pattern import *  # pyflakes:ignore (see comment above)
from topo.projection import *  # pyflakes:ignore (see comment above)
from topo.responsefn import *  # pyflakes:ignore (see comment above)
from topo.sheet import *  # pyflakes:ignore (see comment above)



##########
### Which os is being used (for gui purposes)?
#
# system_plaform can be:
# "linux"
# "mac"
# "win"
# "unknown"
#
# If you are programming tkgui and need to do something special
# for some other platform (or to further distinguish the above
# platforms), please modify this code.
#
# Right now tkgui only needs to detect if the platform is linux (do I
# mean any kind of non-OS X unix*?) or mac, because there is some
# special-purpose code for both those two: the mac code below, and the
# menu-activating code in topoconsole.  We might have some Windows-
# specific code for the window icons later on, too.
# * actually it's the window manager that's important, right?
# Does tkinter/tk itself give any useful information?
# What about root.tk.call("tk","windowingsystem")?

system_platform = 'unknown'
if platform.system()=='Linux':
    system_platform = 'linux'
elif platform.system()=='Darwin' or platform.mac_ver()[0]:
    system_platform = 'mac'
elif platform.system()=='Windows':
    system_platform = 'win'
##########



#
# Define up the right click (context menu) events. These variables can
# be appended or overridden in .topographicarc, if the user has some
# crazy input device.
#

if system_platform=='mac':
    # if it's on the mac, these are the context-menu events
    right_click_events = ['<Button-2>','<Button-3>','<Control-Button-1>']
    right_click_release_events = ['ButtonRelease-2','ButtonRelease-3','Control-ButtonRelease-1']
else:
    # everywhere else (I think) it's Button-3
    right_click_events = ['<Button-3>']
    right_click_release_events = ['ButtonRelease-3']


global TK_SUPPORTS_DOCK
TK_SUPPORTS_DOCK = True


# CEBALERT: this function needs some cleaning up.
# Some stuff should be moved out to paramtk,
# which could also make this file much simpler.

# gets set to the TopoConsole instance created by start.
console = None
def start(mainloop=False,banner=True,exit_on_quit=True):
    """
    Start Tk and read in an options_database file (if present), then
    open a TopoConsole.

    Does nothing if the method has previously been called (i.e. the
    module-level console variable is not None).

    mainloop: If True, then the command-line is frozen while the GUI
    is open.  If False, then commands can be entered at the command-line
    even while the GUI is operational.  Default is False.
    """
    global console

    ### Return immediately if console already set
    # (console itself might have been destroyed but we still want to
    # quit this function before starting another Tk instance, etc)
    if console is not None: return

    if banner: print 'Launching GUI'

    # tcl equivalent of 'if not hasattr(wm,forget)' would be better
    if system_platform=='mac' or Tkinter.TkVersion<8.5:
        global TK_SUPPORTS_DOCK
        TK_SUPPORTS_DOCK=False

    paramtk.initialize()
    paramtk.root.menubar = ControllableMenu(paramtk.root)
    paramtk.root.configure(menu=paramtk.root.menubar)

    # default,clam,alt,classic
    try:
        paramtk.root.tk.call("ttk::style","theme","use","classic")
    except:
        pass

    # Try to read in options from an options_database file
    # (see http://www.itworld.com/AppDev/1243/UIR000616regex/
    # or p. 49 Grayson)
    try:
        options_database = os.path.join(sys.path[0],"topo","tkgui","options_database")
        paramtk.root.option_readfile(options_database)
        print "Read options database from",options_database
    except Tkinter.TclError:
        pass

    console = TopoConsole(paramtk.root,exit_on_quit)

    # Provide a way for other code to access the GUI when necessary
    topo.guimain=console


    # This alows context menus to work on the Mac.  Widget code should bind
    # contextual menus to the virtual event <<right-click>>, not
    # <Button-3>.
    console.event_add('<<right-click>>',*right_click_events)
    console.event_add('<<right-click-release>>',*right_click_release_events)

    # GUI/threads:
    # http://thread.gmane.org/gmane.comp.python.scientific.user/4153
    # (inc. ipython info)
    # (Also http://mail.python.org/pipermail/python-list/2000-January/021250.html)

    # mainloop() freezes the commandline until the GUI window exits.
    # Without this line the command-line remains responsive.
    if mainloop: paramtk.root.mainloop()






from topo.command import pylabplot
#######################

if __name__ == '__main__':
    start(mainloop=True)
    pylabplot.PylabPlotCommand.display_window = True

