<H1>Topographica Command Line</H1>

The GUI interface of Topographica provides the most commonly used
plots and displays, but it is often useful to be able to manipulate
the underlying program objects interactively.  The Topographica
command prompt allows you to do this easily, using the same syntax as
in Topographica scripts.  This section will
eventually include detailed information on how to do this, but
hopefully the current information will help you get started.
<!-- JABALERT: Needs much expansion -->

<P>The command prompt gives you direct access to
<A href="http://python.org/doc/">Python</A>, and so any expression
valid for Python can be entered.  For instance, if your script defines
a Sheet named V1, you can display and change V1's parameters using
Python commands:

<pre>
[cloud]v1cball: topographica -i ~/Documents/Topographica/examples/tiny.ty 

Welcome to Topographica!

Type help() for interactive help with python, help(topo) for general
information about Topographica, help(commandname) for info on a
specific command, or topo.about() for info on this release, including
licensing information.



topo_t000000.00_c1&gt;&gt;&gt; topo.sim['V1'].density
               Out[1]:5.0

topo_t000000.00_c2&gt;&gt;&gt; topo.sim['V1'].output_fns[0]
               Out[2]:PiecewiseLinear(lower_bound=...)

topo_t000000.00_c3&gt;&gt;&gt; from topo.transferfn import *

topo_t000000.00_c4&gt;&gt;&gt; topo.sim['V1'].output_fns=[IdentityTF()]

topo_t000000.00_c5&gt;&gt;&gt; topo.sim['V1'].output_fns[0]
               Out[5]:IdentityTF(name=...)

topo_t000000.00_c6&gt;&gt;&gt; topo.sim['V1'].activity
               Out[6]:
array([[ 0.,  0.,  0.,  0.,  0.],
       [ 0.,  0.,  0.,  0.,  0.],
       [ 0.,  0.,  0.,  0.,  0.],
       [ 0.,  0.,  0.,  0.,  0.],
       [ 0.,  0.,  0.,  0.,  0.]])
...
</pre>

<P>For very large arrays, numpy will suppress printing the array data
to avoid filling your terminal with numbers.  If you do want to see
the data, you can tell numpy to print even the largest arrays:

<pre>
topo_t000000.00_c7&gt;&gt;&gt; numpy.set_printoptions(threshold=2**30)
</pre>

<P>To see what is available for inspection or manipulation for any
object, you can use <code>dir()</code>:

<pre>
topo_t000000.00_c10&gt;&gt;&gt; dir(topo.sim['V1'])
               Out[10]:
['_EventProcessor__abstract',
...
 'activity',
 'activity_len',
 'apply_output_fns',
 'bounds',
...]
</pre>

Note the directory will typically include many items that are not
useful to inspect, including those starting with an underscore
(<code>_</code>), but it gives a good idea what an object contains.
You can also get information about most objects by typing
<code>?</code> after the name, or by using the <code>help()</code>
function for more detailed information:

<pre>
topo_t000000.00_c11>>> PiecewiseLinear?
...
Docstring:
    Piecewise-linear TransferFn with lower and upper thresholds.
    
    Values below the lower_threshold are set to zero, those above
    the upper threshold are set to 1.0, and those in between are
    scaled linearly.

Constructor information:
Definition:     PiecewiseLinear(self, **params)
Docstring:
    Initialize this Parameterized instance.
    
    The values of parameters can be supplied as keyword arguments
    to the constructor (using parametername=parametervalue); these
    values will override the class default values for this one
    instance.
    
    If no 'name' parameter is supplied, self.name defaults to the
    object's class name with a unique number appended to it.


topo_t000000.00_c12&gt;&gt;&gt; help(topo.sim['Retina'])

Help on GeneratorSheet in module topo.sheet object:

class GeneratorSheet(topo.base.sheet.Sheet)
 |  Sheet for generating a series of 2D patterns.
 |  
 |  Typically generates the patterns by choosing parameters from a
 |  random distribution, but can use any mechanism.
 |  
...
 |  Methods defined here:
 |  
 |  __init__(self, **params)
 |  
 |  generate(self)
 |      Generate the output and send it out the Activity port.
 |  
...
 |  ----------------------------------------------------------------------
 |  Data descriptors defined here:
 |  
 |  apply_output_fns
 |      Whether to apply the output_fns after computing an Activity matrix.
 |  
 |  input_generator
 |      Specifies a particular PatternGenerator type to use when creating patterns.
 |  
... 
 |  ----------------------------------------------------------------------
 |  Data and other attributes defined here:
 |  
 |  src_ports = ['Activity']
 |  
... 
</pre>

<P>Topographica uses <A href="http://ipython.scipy.org/">IPython</A>
for its interactive prompt, providing many convenient facilities for
interactive work (such as tab completion). The 
<A href="http://ipython.scipy.org/doc/manual/html/interactive/tutorial.html">
IPython Quick Tutorial</A> is a good place to learn about these.


<H3>Recreating results from interactive sessions</H3>

<P>While interactive creation and exploration of a simulation can be
very helpful, often you will want to create a representation of your
simulation that you can use again. One way of doing this is to save an
existing simulation that you have already created at the commandline
(see <A
HREF="../Reference_Manual/topo.command-module.html#save_script_repr">save_script_repr</A>
for how to save a runnable specification of your simulation (but not
its internal state), or <A
HREF="../Reference_Manual/topo.command-module.html#save_snapshot">save_snapshot</A>
for how to save your simulation's current state). Another way is to
create a .ty script file yourself, and then run it with Topographica.
As discussed in the <A HREF="scripts.html#ty-files">Topographica
scripts</A> section, exactly the same commands can be entered in a .ty
file as at the commandline, and running the .ty file (either by
passing it at startup to the topographica program on the commandline,
or by passing it as an argument to <code>execfile()</code>) is
equivalent to entering its commands manually.

<!--CEB: also mention IPython session recording...-->



<H2>Plotting from the command line</H2>

<A NAME="pylab">If the GUI is running, you can also plot any vector or matrix in the
program:</A>

<pre>
$ topographica -g ~/Documents/Topographica/examples/tiny.ty
Topographica&gt; topo.sim.run(1)
Topographica&gt; from topo.command.pylabplot import *
Topographica&gt; V1 = topo.sim['V1']
Topographica&gt; matrixplot(V1.activity)
Topographica&gt; vectorplot(V1.activity[0])
Topographica&gt; vectorplot(V1.activity[1])
Topographica&gt; vectorplot(V1.activity[10])
Topographica&gt;
</pre>

<P>Result:

<center>
<IMG src="images/matrixvectorplot.png" WIDTH="420" HEIGHT="473">
</center>

<P>
<A NAME="3d-plotting">You can also try replacing matrixplot with
matrixplot3d to get a 3D wireframe plot</A>:

<pre>
Topographica&gt; matrixplot3d(V1.activity)
</pre>

<P>Result:

<center>
<IMG src="images/matrixplot3d_matplotlib.png" WIDTH="596" HEIGHT="499">
</center>

<P>Be sure to try clicking and dragging on the plot, to rotate the viewpoint.

<P>The prompt can also be used for any mathematical calculation or
plotting one might wish to do, a la Matlab:

<pre>
$ topographica -g
Topographica&gt; from numpy import *
Topographica&gt; 2*pi*exp(1.6)
31.120820554943471
Topographica&gt; t = arange(0.0, 1.0+0.01, 0.01)
Topographica&gt; s = cos(2*2*pi*t)
Topographica&gt; from pylab import *
Topographica&gt; plot(s)
[&lt;matplotlib.lines.Line2D instance at 0xb6b1aeac&gt;]
Topographica&gt; show._needmain = False
Topographica&gt; show()
</pre>

Resulting plot:

<center>
<IMG src="images/sine_plot.png" WIDTH="658" HEIGHT="551">
</center>

<P>See the <A
href="http://scipy.org/Documentation">numpy documentation</A>
for more details on the mathematical expressions and
functions supported, and the <A
href="http://matplotlib.sourceforge.net/">MatPlotLib documentation</A> 
for how to make new plots and change their axes, labels, titles, line
styles, etc.

<H2><A NAME="saving-bitmaps">Saving or accessing Topographica bitmaps</A></H2>

A command save_plotgroup is provided to allow you to automate the
process of generating and saving the various bitmap images visible in
the Topographica GUI.  For instance, to measure an orientation map and
save the resulting bitmaps to disk, just do:

<pre>
Topographica&gt; from topo.command.analysis import save_plotgroup, measure_or_pref
Topographica&gt; measure_or_pref()
Topographica&gt; save_plotgroup("Orientation Preference")
</pre>

<P>The name "Orientation Preference" here is just the name used in the
Plots menu, and the command "measure_or_pref()" is listed at the
bottom of the Orientation Preference window.  These names and
functions are typically defined in topo/command/analysis.py, and are
used to present testing images and store the resulting responses.  The
command save_plotgroup then uses this data to generate the bitmap
images, and saves them to disk.

<P>By default, all output from Topographica goes into
<code>Topographica</code> folder in your
<code>Documents</code> directory (this can be customized, and
is <code>~/topographica</code> in release 0.9.7 and earlier; see the
note about the <A HREF="scripts.html#outputpath">default output
path</A> for more information).


<P>Other examples:

<pre>
save_plotgroup("Activity")
save_plotgroup("Projection",projection=topo.sim['V1'].projections('Afferent'))
</pre>

<P>As shown above, some plotgroups (such as Projection) accept
optional parameters.  Using these commands makes it possible to run
simulations without any GUI, for batch or remote processing.

<P>It is also possible to access these bitmaps from the command line,
if you want to analyze them rather than save them.  For example to see
the matrix of values for the OrientationPreference, plus the bounding
box in Sheet coordinates, do:

<pre>
measure_or_pref()
(mat,bbox)=topo.sim['V1'].sheet_views['OrientationPreference'].view()
print mat
print bbox.lbrt()
</pre>

<H2><a name="importing">Imports</a></H2>

<P>In the sample code above, each command is imported (i.e., loaded
and declared) from the appropriate file before it is used.  Python
requires such importing to avoid confusion between similar commands
defined in different files; see the Python documentation for
<A HREF="http://docs.python.org/tut/node8.html">more information about imports</A>.

<!-- do we really recommend this? -->
<P>To avoid confusion, we recommend you take advantage of Python's
namespaces (as mentioned earlier in the <A
HREF="scripts.html#imports">Imports</A> section of the
Topographica Scripts page) when working interactively at the
commandline. For instance, <code>pattern.random.UniformRandom</code>
is clearly distinct from <code>numbergen.UniformRandom</code>;
importing one or the other (or both!) as only
<code>UniformRandom</code> (e.g. <code>from numbergen import
UniformRandom</code>) could lead to confusion. Of course you might
decide that in many cases, using the namespace at the command-line
involves too much typing; you are free to use whichever technique you
prefer.

<H3><a name="option-a">Simplifying imports during interactive runs</a></H3>

When working interactively, typing common import lines (such as
<code>from topo.command.analysis import save_plotgroup,
measure_or_pref</code>, from the earlier example) can be tedious.
Topographica therefore provides the "-a" command-line option, which
automatically imports every command in topo/command/*.py.  The "-g"
option also automatically enables "-a", so that the commands will be
available in the GUI as well.  Thus if you start Topographica as
"topographica -a" or "topographica -g", then you can omit the
<code>from topo.command... import ...</code> lines above.  Still, it
is best never to rely on this behavior when writing .ty script files
or .py code, because of the great potential for confusion, so please
use "-a" only for interactive debugging.




<H2><A NAME="promptformat">Customizing the command prompt</A></H2>

<P>The contents of the command prompt itself are controlled by the
<A HREF="../Reference_Manual/topo.misc.commandline.CommandPrompt-class.html">CommandPrompt</A> class, and can be set to
any Python code that evaluates to a string.  As of 09/2008, the
default prompt is <code>topo_t000000.00_c1>>></code>, where
<code>t000000.00</code> is the current value of
<code>topo.sim.time()</code> when the prompt is printed, and the
<code>1</code> following <code>c</code> is IPython's record of your command number (IPython
caches your input and output in the lists <code>In</code> and
<code>Out</code> respectively; the command number allows you to access
a specific entry as e.g. <code>In[1]</code>).

<P>You can change the prompt format by doing something like:

<pre>
  from topo.misc.commandline import CommandPrompt
  CommandPrompt.set_format('${my_var}>>> ')        
</pre>

where in this case the value of a variable <code>my_var</code> will be
checked each time before the prompt is printed. IPython allows the
prompt to be configured in many ways; see IPython's <A
HREF="http://ipython.scipy.org/doc/manual/html/config/index.html">
User Manual</A> for full details about what you can pass as an argument
to <code>CommandPrompt.set_format</code> in Topographcia.

<P>In addition to the input prompt described above, there is also an
output prompt (e.g. <code>Out[3]:</code>) and a continuation prompt
(e.g. <code>....:</code>). You can also customize these in the same
way as the input prompt by using the <A
HREF="../Reference_Manual/topo.misc.commandline.OutputPrompt-class.html">OutputPrompt</A>
and <A
HREF="../Reference_Manual/topo.misc.commandline.CommandPrompt2-class.html">CommandPrompt2</A>
classes, respectively, in the same way.

<!--
If your terminal supports ANSI colors, you
can use those in your prompt if you wish:

<pre>
  CommandPrompt.format = '"\x1b[32;40;1mTopographica\x1b[33;40;1m_t%g>\x1b[m " % topo.sim.time()'
</pre>

We've provided a shortcut for the above format to make it easier:

<pre>
  CommandPrompt.format = CommandPrompt.ansi_format
</pre>

<P>The result should be something like:

<P><IMG HEIGHT=66 WIDTH=283 SRC="../images/ansiprompt.png">

<P>Note that ANSI colors are not used by default, because terminals
that do not support them will display them as unrecognizable symbols.
-->
<!-- Could use TerminalController from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/475116 for portable output... -->  

				    
<H2><A name="toporc">Site-specific customizations</A></H2>

<P>If you have any commands that you want to be executed whenever you
start Topographica, you can put them into the <A
HREF="scripts.html#toporc">user configuration file</A>.  For
instance, to use the ANSI colors every time, just add these lines to
your user configuration file:

<pre>
from topo.misc.commandline import CommandPrompt
CommandPrompt.format = CommandPrompt.ansi_format
</pre>


<H2><A NAME="min_print_level">Debugging or verbose messaging</A></H2>

If you want to study exactly how Topographica is operating, e.g. to
extend it or control it from the command line, you can consider
changing the <code>param.parameterized.min_print_level</code>
parameter so that messages will be printed whenever Topographica
performs an action.  For instance, you can enable verbose messaging
by starting Topographica as:

<pre>
  topographica -c "import param" \
  -c "param.parameterized.min_print_level=param.parameterized.VERBOSE" ...
</pre>

Instead of VERBOSE, you can use any of the other message levels
defined in parameterized.py, such as DEBUG, which gives even
more information (typically much more than is useful).


<H2><A NAME="scripting-gui">Controlling the GUI from scripts or the command line</A></H2>

<P>The code for the Topographica GUI is kept strictly separate from
the non-GUI code, so that Topographica simulations can be run
remotely, automated using scripts, and upgraded to newer graphical
interface libraries as they become available.  Thus in most cases it
is best to ensure that your scripts do not contain any GUI-specific
code.  Even so, in certain cases it can be very helpful to automate
GUI operations using scripts or from the command line, e.g. if you
always want to open a standard set of windows for analysis.

<P>For such situations, Topographica provides a simple interface for
controlling the GUI from within Python.  For instance, to open an
Activity window, which is under the Plots menu, type:

<pre>
  import topo
  topo.guimain['Plots']['Activity']()
</pre>

Some menu items accept optional arguments, which can be supplied as follows:

<pre>
  import topo
  topo.guimain['Plots']['Connection Fields'](x=0.1,y=0.2,sheet=topo.sim['V1'])
  topo.guimain['Plots']['Activity'](normalize=True,auto_refresh=False)
</pre>

Other examples:

<pre>
  topo.guimain['Plots']['Preference Maps']['Orientation Preference']();

  p=topo.guimain['Plots']
  p['Activity']();
  p['Connection Fields']()
  p['Projection']()
  p['Projection Activity']()
  p['Tuning Curves']['Orientation Tuning']()

  topo.guimain['Simulation']['Test Pattern']()
  topo.guimain['Simulation']['Model Editor']()
</pre>

<P>In each case, the syntax for calling the command reflects the position
of that command in the menu structure.  Thus these examples will no
longer work as the menu structure changes; no backwards compatibility
will be provided.  These commands should be treated only as a
shortcut way to invoke GUI menu items, not as an archival
specification for how a model works.

<P>Note that if you are doing any of these operations from a
Topographica script, it is safest to check first that there is a GUI
available, because otherwise the script cannot be executed when
Topographica is started without the -g option.  Topographica defines
the <code>guimain</code> attribute of the <code>topo</code> namespace
only when there is a GUI available in this run.  Thus if you check to
make sure that guimain is defined before running your GUI commands:

<pre>
  if hasattr(topo,'guimain'):
     topo.guimain['Plots']['Activity']()
</pre>

then your scripts should still work as usual without the GUI (apart
from opening GUI-related windows, which would not work anyway).

<P>Additionally, it is possible to script more complex GUI
operations. For instance, one can open an Orientation Preference
window and request that the map be measured by invoking the 'Refresh'
button:

<pre>
  o = topo.guimain['Plots']['Preference Maps']['Orientation Preference']()
  o.Refresh() # measure the map: equivalent to pressing the Refresh button
</pre>
  
<P>Parameters of the plots can also be set. Continuing from the
previous example, we can switch the plots to be in sheet coordinates,
and alter the pre-plot hooks so that progress will be displayed in an
open Activity window:

<pre>
  o.sheet_coords=False
  for f in o.pre_plot_hooks:
     f.display=True
</pre>

<P>At present, not all GUI operations can be controlled easily from the commandline,
but eventually all will be available. <!--because things like topoconsole haven't
yet been converted to use tkparameterizedobject-->

<!--Probably need an example of changing a SelectorParameter-->

<!--Also note that if you alter the plotgroup directly from the commandline,
changes won't show in open GUI windows until they are refreshed. But that's 
not going to be a problem here - will need this note for ParmetersFrame in
the model editor instructions, etc.-->

<P>Note that in some cases the GUI will reformat the name of a
parameter to make it match look-and-feel expectations for GUI
interfaces, such as removing underscores from names, making the
initial letter capital, etc. (e.g. in the Test Pattern window).  If
you want to disable this behavior so that you can tell exactly which
parameter name to use from the command line or in a script, you can
turn off the parameter name reformatting:

<pre>
  from param.tk import TkParameterized
  TkParameterized.pretty_parameters=False
</pre>

<!--CB: this document sounds like we keep adding things
to the end of it...-->

<P>One can also open a GUI window to inspect or edit any Parameterized object: 

<pre>
 from param.tk import edit_parameters
 edit_parameters(topo.sim['V1']) 
</pre>

This gives a ParametersFrame representing the Parameters
of <code>topo.sim['V1']</code>, allowing values to be inspected and
changed. (This is the same editing window as is available through
the <a target="_top" href="modeleditor.html#parameters">model editor</a>.)


