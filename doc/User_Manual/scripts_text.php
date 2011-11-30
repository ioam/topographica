<H1>Starting Topographica scripts interactively</H1>

<P>
Once you have <A HREF="../Downloads/index.html">installed
Topographica</A> you are ready to try running it. You can choose to
run Topographica interactively (with or without a graphical display),
or in 'batch mode'. This section introduces how to run Topographica
interactively; batch mode is described <A
HREF="batch.html">separately</A>.

<!--<H2>Running Topographica Interactively with the GUI</H2>-->


<H2>Starting Topographica</H2>

<P>To start Topographica with one of our example scripts, on most
systems just open a terminal window and type <code>topographica
-g</code> (Windows: double click on the desktop Topographica
icon). Once Topographica has loaded, you can then click on Help,
followed by Examples, to choose an example script to run. We have
tutorials
for <A HREF="../Tutorials/lissom_oo_or.html">lissom_oo_or.ty</A>
and <A HREF="../Tutorials/som_retinotopy.ty">som_retinotopy.ty</A>,
which make a good starting point for using Topographica.

<P>Alternatively, instead of selecting an example from the GUI, you
can pass the name of a script to run when you start Topographica from
the terminal, e.g.

<blockquote>
  <code>topographica /path/to/some_script.ty -g</code>
</blockquote>

(Windows users can use the 
<A HREF="../Downloads/win32notes.html">command prompt</A>,
although on Windows it is usually easier to use the GUI menus.) This
command will run a script located at the specified path.

<A NAME="copy_examples"><P>To be able to run the examples easily</A>,
you will first need to get your own personal copy of the example
scripts:

<blockquote>
  <code>topographica -c "from topo.misc.genexamples import copy_examples; copy_examples()"</code>
</blockquote>

<!--CEBALERT: output path is probably not the best term.-->

During installation, the Topographica example scripts are installed
into a location that varies by operating system and installation type;
this command copies those to an examples subdirectory of your <A
HREF="#outputpath">output path</A> (see below), typically
<code>~/Documents/Topographica/examples</code> (or
<code>~/topographica/examples</code> for release 0.9.7 or earlier).

<P>Now you can run an example script using a command like the
following:

<blockquote>
  <code>topographica ~/Documents/Topographica/examples/som_retinotopy.ty -g</code>
</blockquote>

<P>Topographica can also be run without the GUI by omitting
the <code>-g</code> flag from the startup command.

<P>Finally, note that the first time Topographica is run on a given example,
there may be a short pause while the program compiles some of the
optimized components used in that example.  (Some components,
generally those with <code>_opt</code> in their names, use code
written in C++ internally for speed, and this code must be compiled.)
The compiled versions are stored in <code>~/.python26_compiled/</code>
on most systems (or in the temporary directory
<code>%TEMP%\%USERNAME%</code> on Windows), and they will be reused on
the next run unless the source files have changed.  Thus you should
only notice such pauses the first time you use a particular component,
at which time you may also notice various inscrutable messages from
the compiler. These messages vary depending on platform (because they
come from the compiler), and may generally be ignored.




<!--CEBALERT: describe Simulation/Run script GUI?-->


<H2><a name="outputpath">Output path</a></H2>

By default, output from Topographica is stored in a particular folder,
which is typically a folder named "Topographica" inside your home
directory's documents folder.  The name and location of the documents
folder depends on your platform, e.g. "My Documents" on some versions
of Windows, or "Documents" on most other platforms.   Topographica
attempts to determine the platform-specific 
documents folder, or falls back to <code>~/Documents/Topographica</code>. The
output path is printed on startup when running topographica interactively.
(Windows users should see our notes about the <A HREF="../Downloads/win32notes.html">command prompt</A>.)

<P>For release 0.9.7 and earlier, the default output path is instead always <code>~/topographica</code>.

<P>You can override the default output path by 
setting the value of <A
HREF="../Reference_Manual/param.normalize_path-class.html">param.normalize_path</A>'s
<code>prefix</code> parameter, e.g.:

<blockquote>
<code>
import param<BR>
param.normalize_path.prefix = "/some/other/path/"
</code>
</blockquote>

To override the default location every time you use Topographica, you
can put these two lines in a <A HREF="#toporc">user configuration
file</A>.


<H2><a name="toporc">User configuration file</a></H2>

On startup, Topographica will look for and run the following files in order:
<blockquote>
<code>~/.topographicarc</code> (typically for UNIX/Linux/Mac OS X systems) <br />
<code>%USERPROFILE%\topographica.ini</code> (on Windows, where
<code>%USERPROFILE%</code> is typically 
<code>C:\Users\username</code> on Vista/7 or <code>c:\Documents and Settings\username</code> on XP).
</blockquote>
If you want to have any code run every time you start Topographica,
you can create the appropriate user configuration file for your
platform and add your preferred startup commands to it.  The user
configuration file is particularly useful for overriding various
default settings such as the <A HREF="#outputpath">output path</A> (as
described above), or the
<A HREF="commandline.html#promptformat">command prompt format</A>. The file can
contain any valid Python code.


<H2><a name="ty-files">Topographica Scripts</a></H2>

<P>Topographica scripts consist of a collection of Python commands,
usually intended to define and build a particular model. Our
convention is to give script filenames the suffix <code>.ty</code> to
distinguish them from ordinary Python scripts (conventionally
<code>.py</code> files). 

<P>As illustrated above, we provide a number of sample scripts in the
examples/ directory, but you are free to write your own and run them
in just the same way. The same commands are valid in script files as
at the <A HREF="commandline.html">commandline</A>: running a script
file is equivalent to entering the commands manually at the
commandline.

<P>Our example scripts, while quite various, have some common
sections, and we anticipate that your own scripts will also contain
some of these. The first such section is the list of imports.

<H3><A NAME="imports">Imports</A></H3>

<P>Python requires that each command and class be imported (i.e.,
loaded and declared) from the appropriate file before use.  This
avoids confusion between similar commands defined in different files
(see the Python documentation for <A
HREF="http://docs.python.org/tut/node8.html">more information about
imports</A>). Therefore, most scripts begin with a list of imports
similar to the following:

<pre>
from math import exp, sqrt
import numpy
import param

from topo import learningfn,numbergen,transferfn,pattern,\
                 projection,responsefn,sheet
</pre>

<P>As described in the <A
HREF="overview.html#class-hierarchies">overview</A>, Topographica
provides a number of component libraries such as <A
HREF="../Reference_Manual/topo.pattern-module.html">pattern</A>, <A
HREF="../Reference_Manual/topo.numbergen-module.html">numbergen</A>, and so
on. Within each of these, a number of related classes and functions
are available. Topographica uses Python's idea of 'namespaces' to make
expressions written for use with Topographica more readable. For
example, Topographica provides a class called UniformRandom, used to
generate a sequence of numbers from a uniform random
distribution. Topographica also provides a class with the same name
that is used to generate two-dimensional patterns. The two are in
different files: the first is topo/numbergen/basic.py, and the second
is topo/pattern/random.py. Were you to type the following:

<pre>
from topo.numbergen import UniformRandom
from topo.pattern.random import UniformRandom
</pre>

you would only have access to the pattern.random version in your
script (and at the commandline), because its name would have
overwritten the numbergen version. To avoid this kind of confusion, we
recommend not importing classnames alone for library components, but
instead qualifying the names. Using the <code>from topo import
numbergen</code> style of import allows you to refer to
<code>numbergen.UniformRandom</code> throughout your script, which,
while involving more typing, cuts out confusion about which class you
might be referring to (making your script easier to read and less
prone to errors).

<!--CEBALERT: ...other sections include defining input pattern,
sheets, connections-->


<H2>Startup options</H2>

<P>Topographica accepts a number of startup options. Details are
available by passing -h to Topographica (<code>topographica
-h</code>), but a few in particular are often useful. We have already
seen <code>-g</code>, which starts an interactive session with the
GUI. To run a script interactively without the GUI, pass
<code>-i</code> instead of <code>-g</code>. (Note that
<code>-g</code>, as well as starting the GUI, also imports a number of
useful commands; you can use <code>-a</code> as described in the <A
HREF="commandline.html#option-a">commandline</A> section to perform
the same without the GUI.)

<P>Please note that when writing a script, you should not rely on
anything to have been automatically imported (as is done by
<code>-g</code> and <code>-a</code>), because other users will not
necessarily start Topographica in the same way as you: scripts should
explicitly import everything they need.

<P>In addition to startup options for the Topographica program,
scripts themselves can also be controlled by options passed at
startup. For instance, many of our examples read parameters that can
optionally be set at startup, such as
<code>retina_density</code>, <code>lgn_density</code>,
and <code>cortex_density</code>, e.g.:

<pre>topographica -i -p retina_density=12 -p cortex_density=12 \
~/Documents/Topographica/examples/lissom_oo_or.ty 
</pre>

In this case, we are specifying that the retina and V1 sheets in a
LISSOM simulation should have a density of 12 rather than the default
of 24 and 48, respectively. Using lower densities is useful during
initial testing or exploration of a model; higher densities can be
used to produce results for publication. <!--CEBALERT: link to
book/scaling paper?-->

<P>Your own scripts can read any startup parameters you require (see
<?php classref('topo.misc.commandline','GlobalParams') ?> and our
example scripts for how to read any such parameter). Note that startup
parameters must be set before the script is executed, i.e.  they
should be passed on the commandline before the script.

<P>In addition to setting startup parameters, arbitrary Python
commands can be specified at the commandline by using the
<code>-c</code> option. For instance:

<pre>
topographica -c 'from topo.command.analysis import measure_sine_pref'\
-c 'measure_sine_pref.num_directions=12' ~/Documents/Topographica/examples/tiny.ty
</pre>

would import <code>measure_sine_pref</code> and set its
<code>num_directions</code> attribute to <code>12</code>, and then
execute the <code>tiny.ty</code> example script. As with ordinary
Python commands, you can use a semicolon <code>;</code> to separate
statements within one command.





