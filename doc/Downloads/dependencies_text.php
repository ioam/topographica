<P>This page gives information about the external packages that are
required or useful for Topographica; installation of these packages is
described on the main <a target="_top" href="index.html">Downloads</a> page.


<H2>Required External Packages</H2>

<P>Topographica makes extensive use of the following external
packages that must be installed to use Topographica.

<P><DL COMPACT>

<P><DT><A href="http://python.org/doc/">Python</A></DT>
<DD>Topographica command and scripting language (essential!).
Topographica is written in Python, so anything that Python can do is
also valid for Topographica. For a good basic introduction, check out
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


<H2>Required IOAM Packages</H2>

<P>Some of the modules developed for Topographica are maintained and
released separately, so that they can be used in other projects, but
are also required for Topographica:

<P><DL COMPACT>

<P><DT><A href="http://ioam.github.com/param/">Param</A> and
  <A href="http://ioam.github.com/paramtk/">ParamTk</A> </DT>
<DD>General-purpose support for full-featured Parameters, extending
  Python attributes to have documentation, bounds, types, etc.
  The Tk interface ParamTk is optional, and only used for
  Topographica's optional tkgui interface.</DD>

<P><DT><A href="http://ioam.github.com/imagen/">ImaGen</A></DT>
<DD>General-purpose support for generating 0D (scalar), 1D (vector),
  and 2D (image) patterns, starting from mathematical functions,
  geometric shapes, random distributions, images, etc.  Useful for any
  program that uses such patterns, e.g. any sensory modelling
  software, not just Topographica.</DD>
</DL>

<P>Again, installation of these packages is described on the main
<a target="_top" href="../Downloads/index.html">Downloads</a> page.



<H2>Typical External Packages</H2>

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
see <A href="http://ipython.scipy.org/moin/Documentation">IPython's
documentation</A> for more detailed information.
</DD>

<P><DT><A href="http://www.scipy.org/Weave">Weave</A></DT>
<DD>Topographica uses weave (shipped with SciPy) to allow snippets of
C or C++ code to be included within Python functions, usually for a
specific speed optimization.  This functionality is available for any
user-defined library function, for cases when speed is crucial.</DD>

<P><DT><A href="http://code.google.com/p/gmpy/">gmpy</A></DT>
<DD>A C-coded Python extension module that wraps the GMP library to
provide Python with fast multiprecision arithmetic. Topographica uses
gmpy's rational type as its default simulation time, to avoid
precision issues inherent in floating-point arithmetic. Since gmpy
requires GMP to be built, Topographica will fall back to a slower,
purely Python implementation of fixed-point numbers (<A
HREF="http://fixedpoint.sourceforge.net/">fixedpoint</A>) if gmpy is
not available.

<P><DT><A href="http://ioam.github.com/lancet/">Lancet</A></DT>
<DD>Support for running large numbers of simulation jobs and collating
  the results to produce figures and analyses, especially for
  publication.</DD>
</DL>

</DL>


 
<H2>Optional External Packages</H2>

<P>A number of other packages are also useful with Topographica, but
are not necessarily required.  Packages listed below are therefore not
part of the default Topographica installation, but many are in use by
Topographica users and/or developers.

<P>In most cases, these packages are included in Python distributions
such
as <a target="_top" href="http://enthought.com/products/epd.php">EPD</a>/<a target="_top" href="http://pythonxy.com">Python(x,y)</a>,
or are available via package managers such as
apt-get/MacPorts. Alternatively, the packages are available for
easy_install/pip install/standard Python installation
via <a target="_top" href="http://pypi.python.org/pypi">PyPI</a>. Many of these 
packages can also be installed using the external directory of
Topographica; see the 
<a target="_top" href="http://pypi.python.org/pypi">github installation instructions</a>. 
Note that, however you choose to install any of these packages, if your
system has more than one copy of Python <em>you must install the package
using the same copy of Python that you are using for
Topographica</em>.

<P>If you encounter problems using these packages, feel free
to <a target="_top" href="http://sourceforge.net/projects/topographica/forums/forum/178312">ask
the Topographica community for help</a>.


<P><DL COMPACT>

<P><DT><A href="http://www.scipy.org/">SciPy</A></DT>
<DD>
SciPy includes many, many functions useful in scientific research,
such as statistics, linear algebra, integration and differential
equation solvers, etc. 
<!--
SciPy is included in many Python distributions
(e.g. <a target="_top" href="http://enthought.com/products/epd.php">EPD</a>), and is
usually available via package managers (e.g. "sudo apt-get install
python-scipy"). If using the fat distribution of Topographica, "make
-C external scipy" will build SciPy (but note that building SciPy is
not always straightforward).
-->
</DD>

<!--CEBALERT: I need to update mlabwrap/check the bug I had on jupiter-->
<P><DT><A name="mlabwrap" href="http://mlabwrap.sourceforge.net/">mlabwrap</A></DT>
<DD>mlabwrap is a high-level Python-to-Matlab bridge, allowing Matlab to look like
a normal Python library:
<PRE>
from mlabwrap import mlab  # start a Matlab session
mlab.plot([1,2,3],'-o')
</PRE>

mlabwrap is transitioning to SciKits (see below), but installation can
be tricky so we describe it further here. First, check you can run
<code>matlab -nodesktop -nosplash</code> successfully, then build from 
source (e.g. from Topographica's fat distribution with
<code>make -C external mlabwrap</code>, or download and build the
source yourself).  If the matlab libraries are not in
your <code>LD_LIBRARY_PATH</code>, there will be a note during the
build telling you to add the libraries to your path. For example:
<pre>
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/matlab-7.5/bin/glnx86
</pre>
You can either add that permanently to your path, or add it each time
before using mlabwrap.
</DD>

<!--CEBALERT: now a scikit, and called audiolab:
http://scikits.appspot.com/audiolab? What version did Bilal use?-->
<P><DT><A href="http://www.ar.media.kyoto-u.ac.jp/members/david/softwares/pyaudiolab/index.html">pyaudiolab</A></DT>
<DD>
pyaudiolab provides an easy way to read from and write to sound files
(it wraps
<A href="http://www.mega-nerd.com/libsndfile/">libsndfile</A>).  In
the fat distribtion, building should be simple: <code>make -C external
pyaudiolab</code>.
</DD>

<P><DT><a target="_top" href="http://scikits-image.org/">scikits-image</a></DT>
<DD>
A collection of algorithms for image processing.
</DD>

<P><DT><A HREF="http://playerstage.sf.net">Player/Stage/Gazebo</A></DT>
<DD>
The Player/Stage/Gazebo project provides interfaces for a large
variety of external hardware and simulation software, such as cameras,
digitizers, and robots. The Gazebo and Stage simulators that support
the Player interface can also be used, as described on the Player
site. Note that a connection to Player is provided in
topo/misc/robotics.py (last tested with player-2.0.4.tar.bz2 from
playerstage.sf.net).
<!--
To install it, just download
player-2.0.4.tar.bz2 from , put it in the externals/
subdirectory, and do <code>make -C external player</code>.  
-->
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

<!--CEBALERT: need to link to Cython tutorial when that's finished.-->
<P><DT><A HREF="http://cython.org">Cython</A></DT>
<DD>
Cython is a language that is very similar to Python, but supports
calling C functions and declaring C types, and will produce and
compile C code. Therefore, the performance benefit of C is available
from a much simpler language. Because Cython can compile almost any
Python code to C, one can start with a component written entirely in
Python and then optimize it step by step (by adding types, for
example). See the Cython documentation for more information.  
</DD>
<!--To
install Cython for Topographica, just enter <code>make -C external
cython</code> from your Topographica directory.-->

<P><DT><A href="http://packages.python.org/quantities">Quantities</A></DT>
<DD>Quantities allows you to use real-world units in your .ty scripts,
such as mm or degrees of visual field, converting them to
Topographica's units.
</DD>

<P><DT><A href="http://scikits.appspot.com/scikits">SciKits</A></DT>
<DD>SciKits provide many useful extensions to SciPy, e.g. for machine
learning and numerical optimization.
</DD>

<P><DT><A href="http://rpy.sourceforge.net/">RPy</A></DT>
<DD>The language R (a free implementation of the S statistical
language) has a nice interface to Python that allows any R
function to be called from Python.  Nearly any statistical
function you might ever need is in R.
</DD>

<!-- theano -->

<!--CEBENHANCEMENT: I'll add mpi stuff and opencv-->

<!--CEBENHANCEMENT: mention things used in projects (e.g. blender)?-->

</DL>

<P>Topographica runs on an unmodified version of the Python language,
and so it can be used with any other Python package that you install
yourself. A good list of potentially useful software is located at 
<A href="http://www.scipy.org/Topical_Software">SciPy.org</A>.  

<P><DL COMPACT>

</DL>

<P>As above, note that if your system has more than one copy of Python,
you must install the package using the same copy of Python that you
are using for Topographica.
