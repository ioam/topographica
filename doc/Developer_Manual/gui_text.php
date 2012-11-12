<H1>Implementing the GUI</H1>

<P>When coding, the GUI should be considered an optional component.
No part of Topographica should import GUI files, rely on the presence
of a particular GUI or any GUI at all, or assume that the data it
generates will be used only by a GUI unless it is absolutely
necessary, e.g. for the actual GUI implementation.  This is a special
case of the <A HREF="ood.html">general principles of object-oriented
design</A> discussed elsewhere.

<P>Many components that would at first glance seem to be GUI-related
are, in, fact much more general.  Such code should be written for the general
case, not in terms of the GUI (and not even with names or comments
that suggest they are in any way limited to being part of a GUI).

<P>For instance, many of the analysis and plotting routines will
commonly be used in the context of a GUI.  However, the vast majority
of this code is not specific to a GUI, i.e. it does not require a user
to actually move a mouse or manipulate widgets.  E.g. a SheetView is a
bitmap representation of a Sheet; the resulting bitmap can of course
be displayed in a GUI window, but it could also be saved to a file,
and in batch mode or unit tests often <i>will</i> be saved directly to a
file, with no GUI window ever created.  Most of the important code for
plotting is independent of the output device, and any such code should
be written using general terminology like Plotting, not GUI.
Similarly for other analysis routines --- they should be implemented
and named in terms of some general module name like Analysis, not GUI.

<P>Obviously, it's very helpful for plots, etc. to have interactive
widgets to set the scales, select subplots, etc.  But these can
generally be implemented in a way that can also be specified
textually, i.e. without a mouse, so that they can be used without a
GUI, or at least without any particular GUI.  Even for things that are
inherently mouse-based, like data exploration tools that change
viewpoints dynamically based on the mouse position, as much code as
possible should be extracted out, made general, and kept out of the
GUI code.

<P>If you want more information on this approach, search the web for
Model-View-Controller.  Writing the code in this way helps ensure that
the core of the simulator is not dependent on any particular output
device, which is crucial because different output devices are
appropriate in different contexts, e.g. over the web, in
non-interactive runs, in batch testing, supporting different
look-and-feel standards, etc.  The approach also greatly eases
maintenance, because GUI libraries often vary significantly over time
and across platforms.  To be able to maintain our code over the long
term, we need to minimize the amount of our code that depends on such
varying details.  Finally, this approach ensures that scientific users
can ignore all of the GUI details, which are irrelevant to what
Topographica actually computes.  Allowing users to focus on the core
code is absolutely crucial for them to be able to understand and trust
what they are actually simulating.


<!--CB: work in progress-->

<H2><A NAME='programming-tkgui'>Programming with tkgui</H2>

<P>tkgui
uses <a target="_top" href="http://wiki.python.org/moin/TkInter">Tkinter</a> to draw
the GUI components, but simplifies GUI implementation by handling
linkage of Parameters with their representations in the GUI.

<!--(Tkinter is very flexible, but often quite a large amount of code
is required to keep track of variables and display components
('widgets') ).-->

<P>The
classes <a target="_top" href="../Reference_Manual/param.tk.TkParameterized-class.html">TkParameterized</a>
and <a target="_top" href="../Reference_Manual/param.tk.ParametersFrame-class.html">ParametersFrame</a>
are the ones most often used for creating a new GUI representation of
some Topographica component. Which to use depends on how much you wish
to customize the display: a ParametersFrame displays all of a
Parameterized's Parameters as a list in one Frame, whereas a
TkParameterized can display any number of the Parameters in any number
of Frames (which you specify). Hence the PlotGroupPanels, which
display Parameters from multiple Parameterizeds in a custom layout,
are based on TkParameterized, whereas editing properties of an object
in the model editor simply brings up a ParametersFrame for that
object.

<H3>ParametersFrame</H3>

<P>If you wish to display and/or edit the Parameters of a
Parameterized in the GUI, you can simply insert a ParametersFrame for
that object into an existing container (a window such as a
param.tk.AppWindow or a Tkinter.Toplevel, or a frame such as a
Tkinter.Frame):

<pre>
from topo import pattern
from param import tk

# existing component and existing window
g = pattern.Gaussian()
w = tk.AppWindow()

# display all parameters of g in w
f = tk.ParametersFrame(w,g)
</pre>
 
<P>All the non-hidden Parameters of <code>p</code> will be displayed
in a new Frame in <code>w</code>. Changing the Parameter's value in
the GUI immediately changes the actual Parameter value; the class
<A href="../Reference_Manual/param.tk.ParametersFrameWithApply-class.html">
param.tk.ParametersFrameWithApply</A> is a version of
ParametersFrame that does not immediately apply changes, instead
waiting for confirmation via an Apply button.


<!--CB: mention buttons, two types of PF-->


<H3>TkParameterized</H3>

<P>ParametersFrame extends TkParameterized, the basic class for
representing Parameters in the GUI. TkParameterized is more
flexible, but also slightly more complex to use. In the ParametersFrame
example above, we display all the Parameters of the Gaussian pattern;
if instead we wanted to display only its size, x, and y Parameters, we
could do the following:

<pre>
from topo import pattern
from param import tk

# existing component and existing window
g = pattern.Gaussian()
w = tk.AppWindow()

# display selected parameters of g in w
t = tk.TkParameterized(w,g)
t.pack_param('size')
t.pack_param('x')
t.pack_param('y')
</pre>

<P>As for ParametersFrame, changes to values in the GUI are
immediately reflected in the actual Parameters. TkParameterized's
flexibility for custom arrangements comes from the pack_param()
method, which takes several optional arguments to control the
positioning of the Parameter.


<H2>Tkinter references</H2>

<P>The following links provide useful reference material for
programming with Tkinter and Tcl/Tk:

<ul>
<li><A HREF="http://www.tkdocs.com/">TkDocs</A></li>
<li><A HREF="http://effbot.org/tkinterbook/">An Introduction to Tkinter</A></li>
<li><A HREF="http://www.nmt.edu/tcc/help/lang/python/tkinter.html">Tkinter: GUI programming with Python</A></li>
<li><A HREF="http://www.ferg.org/thinking_in_tkinter/index.html">Thinking in Tkinter</A></li>
<li><A HREF="http://wiki.tcl.tk/">The Tcler's Wiki</A></li>
<li><A HREF="http://sebsauvage.net/python/gui/">Building a basic GUI application step-by-step in Python with Tkinter and wxWidgets</A></li>
<li><A HREF="http://tkinter.unpythonic.net/wiki/">Tkinter Wiki</A></li>
<li><A HREF="http://news.gmane.org/group/gmane.comp.python.tkinter">comp.python.tkinter</A></li>
</ul>
