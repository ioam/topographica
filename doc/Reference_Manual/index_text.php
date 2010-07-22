This reference manual contains detailed documentation of each
component making up Topographica, assuming that the user is already
familiar with basic Topographica usage.  See the <A
HREF="../User_Manual/index.html">User Manual</A> and <A
HREF="../Tutorials/index.html">Tutorials</A> for such an introduction.
Note that the documentation of these components is gradually being
improved, and not every component is properly documented yet.
Moreover, the documentation is often much more verbose than necessary,
because many little-used yet often duplicated methods are included for
each class.  Still, the reference for a given component does
provide a comprehensive listing of all attributes and methods,
inherited or otherwise, which is difficult to obtain from the
source code.


<H2><A NAME="core">Core packages</A></H2>

<P>Topographica is designed as a collection of packages from which
elements can be selected to model specific neural systems.  For more
information, see the individual subpackages of the <A
href="topo.html"><strong>topo</strong></A> package.  The most 
essential of these are:

<P><DL COMPACT>
<P><DT><A href="topo.base-module.html"><strong>base</strong></A></DT>
<DD>Core Topographica-specific functions and classes</DD>
<P><DT><A href="param-module.html"><strong>param</strong></A></DT>
<DD>Support for objects with user-controllable attributes</DD>
<P><DT><A href="topo.plotting-module.html"><strong>plotting</strong></A></DT>
<DD>Visualization functions and classes</DD>
<P><DT><A href="topo.analysis-module.html"><strong>analysis</strong></A></DT>
<DD>Analysis functions and classes (besides plotting)</DD>
<P><DT><A href="topo.misc-module.html"><strong>misc</strong></A></DT>
<DD>Miscellaneous independent utility functions and classes</DD>
<P><DT><A href="topo.tkgui-module.html"><strong>tkgui</strong></A></DT>
<DD>Tk-based graphical user interface (GUI)</DD>
</dl>

The <strong>base</strong> directory contains the most fundamental
Topographica classes, implementing basic functionality such as Sheets
(arrays of units), Projections (large groups of connections between
Sheets), ConnectionFields (spatially localized groups of connections
to one unit), and the event-driven Simulation.  It relies heavily on
the generic support for Parameters (user-controllable attributes) from
the <strong>param</strong> directory.  Together these files are
independent of the rest of the files in topo/, and act as the primary
programming interface on which Topographica is built.  The rest of the
directories add components used in specific models, or add graphical
interfaces.

<H2><A NAME="library">Library</A></H2>

<P>The Topographica primitives library consists of an extensible
family of classes that can be used with the above functions and
classes:

<P><DL COMPACT>
<P><DT><A href="topo.pattern-module.html"><strong>pattern</strong></A></DT>
<DD>PatternGenerator classes: 2D input or weight patterns</DD>
<P><DT><A href="topo.numbergen-module.html"><strong>numbergen</strong></A></DT>
<DD>NumberGenerator classes: scalars drawn from some distribution</DD>
<P><DT><A href="topo.sheet-module.html"><strong>sheet</strong></A></DT>
<DD>Sheet classes: 2D arrays of processing units</DD>
<P><DT><A href="topo.projection-module.html"><strong>projection</strong></A></DT>
<DD>Projection classes: connections between Sheets</DD>
<P><DT><A href="topo.ep-module.html"><strong>ep</strong></A></DT>
<DD>EventProcessor classes: other simulation objects</DD>
<P><DT><A href="topo.transferfn-module.html"><strong>transferfn</strong></A></DT>
<DD>Output functions: apply to matrices to do e.g. normalization or squashing</DD>
<P><DT><A href="topo.responsefn-module.html"><strong>responsefn</strong></A></DT>
<DD>Calculate the response of a unit or a Projection</DD>
<P><DT><A href="topo.learningfn-module.html"><strong>learningfn</strong></A></DT>
<DD>Adjust weights for a unit or a Projection</DD>
<P><DT><A href="topo.coordmapper-module.html"><strong>coordmapper</strong></A></DT>
<DD>Determine mapping from one Projection to another</DD>
<P><DT><A href="topo.command-module.html"><strong>command</strong></A></DT>
<DD>High-level user commands</DD>
</DL>

<P>All of the library components are optional, in the sense that they
can be deleted or ignored or replaced with custom versions without
affecting the code in any of the main packages.  (Of course, any
specific model that depends on the component would not be able to
function without it.)

<P>Each of the library directories can be extended with new classes
of the appropriate type, just by adding a new .py file to that
directory.  E.g. a file of new PatternGenerator classes can be copied
into pattern/, and will then show up in the GUI menus as potential
input patterns.  The GUI will also show any class derived from those
in the library directories, even if it is defined in your own files,
as long as that file has been run or imported before the GUI window 
is opened.

<P>Many of the components come in multiple varieties, to be used at
different levels in a model.  For instance, there are learning
functions that operate on a single unit (type LearningFn), and ones
that operate on an entire CFProjection (type CFPLearningFn).  The
lower level components can be used by providing them to a "Plugin"
version of the higher level component, which will apply the lower
level version to each unit.  For instance, a LearningFn can be used
with a CFPLearningFn of type CFPLF_Plugin, and will be applied the
same to each unit individually.

<P>Some components also come with an optimized version, usually
written in C for speed.  The fastest, but least flexible, components
will be high-level components written in C, such as CFPLF_Hebbian_opt.


<!-- JABALERT! This should probably move to its own page. -->
<H2>Required external Packages</H2>

<P>Topographica makes extensive use of the following external
packages that must be installed to use Topographica:

<!-- Should we make these point to the local copy instead? -->
<P><DL COMPACT>

<P><DT><A href="http://python.org/doc/">Python</A></DT>
<DD>Topographica command and scripting language (essential!).
Topographica is built on an unmodified copy of Python, so anything
that Python can do is also valid for Topographica. For a good basic
introduction, check out
the <A HREF="http://docs.python.org/tut/tut.html">Python
tutorial</A>. Those already familiar with programming might find
<A href="http://wiki.python.org/moin/BeginnersGuide/Programmers">Python
for Programmers</A>
or <A href="http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html">Idiomatic
Python</A> useful.
<BR>

</DD>

<P><DT><A href="http://numpy.scipy.org/">NumPy</A></DT>
<DD>Topographica makes heavy use of NumPy arrays and math functions;
these provide high-level operations for dealing with matrix data.  The
interface and options
are <A href="http://www.scipy.org/NumPy_for_Matlab_Users">similar to
Matlab</A> and other high-level array languages.  These operations are
generally much higher performance than explicitly manipulating each
matrix element, as well as being simpler, and so they should be used
whenever possible. See
the <A href="http://www.scipy.org/Documentation">NumPy documentation
list</A> (especially the Guide to Numpy, NumPy Example List, and NumPy
Functions by Category) to learn about the full range of available
functions.
</DD>

<P><DT><A href="http://www.pythonware.com/products/pil/">PIL</A></DT>
<DD>Topographica uses the Python Imaging Library for reading and
writing bitmap images of various types.  PIL also provides a variety
of <A HREF="http://www.pythonware.com/library/pil/handbook/index.htm">image
processing and graphics routines</A>, which are available for use in
Topographica components and scripts.</DD>
</DL>

For full use of the features of these packages, see their
documentation.  

<H2>Typical external Packages</H2>

Most Topographica users will also want these additional packages:

<P><DL COMPACT>

<P><DT><A href="http://matplotlib.sourceforge.net/">MatPlotLib</A></DT>
<DD>Matplotlib is used for generating 1D (line) and 2D (plane) plots,
such as topographic grid plots.  It
provides <A href="http://matplotlib.sourceforge.net/matplotlib.pylab.html">PyLab</A>,
a very general Matlab-like interface for creating plots of any
quantities one might wish to visualize, including any array or vector
in the program.
</DD>

<P><DT><A href="http://ipython.scipy.org/">IPython</A></DT>
<DD>IPython provides Topographica with an enhanced Python shell,
allowing efficient interactive work. The 
<A href="http://ipython.scipy.org/doc/manual/html/interactive/tutorial.html">
IPython tutorial</A> explains the most immediately useful features;
see
<A href="http://ipython.scipy.org/moin/Documentation">IPython's
documentation</A> for more detailed information.
</DD>

<P><DT><A href="http://www.scipy.org/Weave">Weave</A></DT>
<DD>Topographica uses weave to allow snippets of C or C++ code to be
included within Python functions, usually for a specific speed optimization.
This functionality is available for any user-defined library function, 
for cases when speed is crucial.</DD>

<P><DT><A href="http://code.google.com/p/gmpy/">gmpy</A></DT>
<DD>A C-coded Python extension module that wraps the GMP library to
provide Python with fast multiprecision arithmetic. Topographica uses
gmpy's rational type as its default simulation time. Since gmpy
requires GMP to be built, Topographica will fall back to a slower,
purely Python implementation of fixed-point numbers (<A
HREF="http://fixedpoint.sourceforge.net/">fixedpoint</A>).

<!--CBENHANCEMENT: add gnosis when (if) we begin to advertise it-->

</DL>

<P>They are included in the source distribution, or can be installed via
your regular package manager.
 
<H3>Optional External Packages</H3>

<P>A number of other packages are also useful with Topographica, but
can sometimes be difficult to install.  They include:

<P><DL COMPACT>

<P><DT><A href="http://www.scipy.org/">SciPy</A></DT>
<DD>
<!--CBALERT: update this text. JA has more information already?
It's easy on Ubuntu linux because you can get the package manager
to add the libraries. Also on Windows, it's already working.-->
SciPy includes many, many functions useful in scientific research,
such as statistics, linear algebra, image processing, integration and
differential equation solvers, etc.  However, because of all the
external libraries that it uses, getting SciPy to work 
on a particular installation can be difficult. You can try with
<code>make -C external scipy</code> if you installed Topographica from
source; otherwise install Scipy described in its documentation.</DD>

<P><DT><A name="mlabwrap" href="http://mlabwrap.sourceforge.net/">mlabwrap</A></DT>
<DD>mlabwrap is a high-level Python-to-Matlab bridge, allowing Matlab to look like
a normal Python library:
<PRE>
from mlabwrap import mlab  # start a Matlab session
mlab.plot([1,2,3],'-o')
</PRE>
To use this package, first check you can run 
<code>matlab -nodesktop -nosplash</code> successfully, then build with
<code>make -C external mlabwrap</code>.
If the matlab libraries are not in your <code>LD_LIBRARY_PATH</code>,
there will be a note during the build telling you to add the libraries 
to your path. For example:
<pre>
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/matlab-7.5/bin/glnx86
</pre>
You can either add that permanently to your path, or add it each time
before using mlabwrap.
</DD>

<P><DT><A href="http://www.ar.media.kyoto-u.ac.jp/members/david/softwares/pyaudiolab/index.html">pyaudiolab</A></DT>
<DD>
pyaudiolab provides an easy way to read from and write to sound files (it wraps 
<A href="http://www.mega-nerd.com/libsndfile/">libsndfile</A>).
On Linux source installations, building should require nothing more than <code>make -C external pyaudiolab</code>.
<!--Currently: untested on OSX, not present on Windows-->
</DD>

<!--
<P><DT><A HREF="http://gnuplot-py.sourceforge.net">gnuplotpy</A></DT>
<DD>
You can use the external <code>gnuplot</code> command to generate plots on
some platforms (at least UNIX, and also probably Mac OS X).  To build
it on Linux or Mac, first install Numeric (which you can download <A HREF="http://sourceforge.net/project/showfiles.php?group_id=1369&package_id=1351">here</A>),
and then do <code>make -C external gnuplotpy</code>.  At that point 
you can e.g. use <code>matrixplot3d_gnuplot()</code> in place of 
<A href="../User_Manual/commandline.html#gnuplotpy"><code>matrixplot3d()</code></A>
or <code>matrixplot()</code>, or modify
  <code>matrixplot3d_gnuplot()</code> to create any other gnuplot visualization.
</DD>
  Currently: untested on OSX, not present on Windows
-->

<P><DT><A HREF="http://playerstage.sf.net">Player/Stage/Gazebo</A></DT>
<DD>
The Player/Stage/Gazebo project provides interfaces for a large
variety of external hardware and simulation software, such as cameras,
digitizers, and robots.  A connection to Player is provided in
topo/misc/robotics.py, but the Player software is not distributed
directly with Topographica.  To install it, just download
player-2.0.4.tar.bz2 from playerstage.sf.net, put it in the externals/
subdirectory, and do <code>make -C external player</code>.  
<!--Currently: untested on OSX, not present on Windows-->
The Gazebo and Stage simulators that support the Player interface
can also be used, as described on the Player site.
</DD>

<P><DT><A HREF="http://pypi.python.org/pypi/processing">Processing</A></DT>
<DD>
Because of the "global interpreter lock" it is not possible to do true
multiprocessing in Python using the language's built-in threads.
The <i>processing</i> module provides support for multiprocessing
using an API similar to that of Python's <i>threading</i> module.
(Although, unlike threads, processes don't share memory.)  The module
also provides a number of other useful features including process-safe
queues, worker pools, and factories ("managers") that allow the
creation of python objects in other processes that communicate through
proxies. 
</DD>

<P><DT><A HREF="http://cython.org">Cython</A></DT>
<DD>
Cython is a language that is very similar to Python, but supports
calling C functions and declaring C types, and will produce and
compile C code. Therefore, the performance benefit of C is available
from a much simpler language. Because Cython can compile almost any
Python code to C, one can start with a component written entirely in
Python and then optimize it step by step (by adding types, for
example). See the Cython documentation for more information.  To
install Cython for Topographica, just enter <code>make -C external
cython</code> from your Topographica directory.
</DD>


</DL>


<P>Topographica runs on an unmodified version of the Python language,
and so it can be used with any Python package that you install
yourself.  To install such a package in Topographica, just run its
<code>setup.py</code> as usual, being sure to use whichever copy of
Python that you use for Topographica
<code>topographica/bin/python</code>.  For instance, if you are
currently in the main topographica source directory and the new package has
been unpacked in your home directory <code>/home/user/pkg</code>, just type
<code>bin/python /home/user/pkg/setup.py</code>.
Running setup in this way ensures that the package will be installed
in Topographica's copy of python, rather than any other copy of Python
that might be present on your system.

<P>A good list of potentially useful software is located at 
<A href="http://www.scipy.org/Topical_Software">SciPy.org</A>.
Some packages of note:

<P><DL COMPACT>

<P><DT><A href="http://rpy.sourceforge.net/">RPy</A></DT>
<DD>The language R (a free implementation of the S statistical
language) has a nice interface to Python that allows any R
function to be called from Python.  Nearly any statistical
function you might ever need is in R.
</DD>

</DL>

