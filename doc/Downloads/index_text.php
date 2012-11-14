<H2><A NAME="installing-topographica">Installing Topographica</A></H2>

<P>Topographica is platform-independent, and all instructions below
apply to Linux, UNIX, Mac, or Windows, unless otherwise specified.  In
Windows, to get a command prompt, you can use the Run command from the
Start menu and enter <kbd>cmd</kbd>; on other systems you can start a
Terminal or similar application.

<P>The instructions below explain how to install Topographica using
<A HREF="#installing-via-pip">pip</a> (for most users),
<A HREF="#installing-via-virtualenv">virtualenv</a> (if you don't have
pip access or want a separate working environment, e.g. just to try
out Topographica), or <A HREF="#git">git</a> (if you want the latest
version, or need to track our files using revision control).


<H3><A NAME="installing-python">First install Python</A></H3>

<P>Topographica is written in Python, which is available for nearly
all operating systems and is usually already installed (try running
<kbd>python --version</kbd> from the command prompt).  If Python version 2.6 or
later is not installed, you can download the latest version for your
system from 
<a target="_top" href="http://www.python.org/download">python.org</A>.  Note that we do
not yet support Python3, so if only python3 is installed you will need
to install python2 as well (e.g. Python 2.7).

<P>If Python isn't already installed, it may be convenient to get
it from one of the integrated scientific Python distributions like
<a target="_top" href="http://www.pythonxy.com">Python(X,Y)</A>,
<a target="_top" href="http://www.enthought.com/products/epd.php">EPD</A>, or
<a target="_top" href="https://store.continuum.io">Anaconda CE</A>.
These distributions are particularly useful for Windows and Mac users,
who might not otherwise have a C compiler (necessary for good
performance in Topographica) and optimized math and matrix libraries.
On any system, the integrated distributions also provide a lot of
useful related packages, including most of Topographica's dependencies.


<H3><A NAME="installing-via-pip">Install via pip</A></H3>

<P>The typical way to install the most recently released version of
Topographica is via
<A target="_top" HREF="http://www.pip-installer.org">pip</A>
from the command prompt:

<PRE>pip install --user topographica</PRE>

<P>This will fetch Topographica and its required dependencies (i.e.,
param, numpy, and PIL, for the 0.9.7 release) from 
<a target="_top" href="http://pypi.python.org/pypi/topographica">PyPI</A> 
and install them into your home directory.  The files will be stored
in a subdirectory called <code>.local</code> on Linux and Mac, and
into the user's <code>%APPDATA%</code> subdirectory on Windows (typically
named <code>Application Data</code>).
<!-- See http://www.python.org/dev/peps/pep-0370/ for details -->

<P>Beyond these absolutely required packages, you will probably also want
to install others necessary for good performance (by at least a factor
of 100), to provide some optional types of plotting, and to improve
the command-line interface:

<PRE>pip install --user gmpy matplotlib scipy ipython</PRE>

<P>Other useful packages are described on our
<a target="_top" href="dependencies.html">dependencies</A> page, and
can usually be installed the same way.

<P>If you have root or adminstrator access to your machine and want
these libraries to be available to all users of your system, you can
omit <kbd>--user</kbd>, or else install the dependencies via your
system's package manager, if any.

<P>If your system does not have pip installed or has an old version
lacking the <kbd>--user</kbd> option, but you do have root or
administrator access, you should first install pip using:

<PRE>easy_install pip</PRE>

or the equivalent for your package manager.  If you don't have
easy_install, you can install pip by downloading 
<a target="_top" href="https://raw.github.com/pypa/pip/master/contrib/get-pip.py">get-pip.py</a>
and running <kbd>python get-pip.py</kbd>.


<H3><A NAME="installing-via-virtualenv">Install via virtualenv</A></H3>

<P>If your machine lacks pip and you do not have root</A> or
administrator access, then you can obtain a local copy of pip by
downloading
<a target="_top" href="https://raw.github.com/pypa/virtualenv/master/virtualenv.py">virtualenv.py</a>.
Just run it using Python to create a clean "virtual environment" that
includes pip and into which you can install Topographica and its
dependencies:

<PRE>
$ python virtualenv.py VENV
$ VENV/bin/pip install topographica
$ VENV/bin/topographica -g
</PRE>

<P>You can then install any other dependencies using 
<A HREF="#installing-via-pip">pip</a> as described above.
Of course, instead of VENV you can use any name you like for your
virtual environment, and you can have multiple different virtual
environments for different purposes.

<P>Many people use 
<a target="_top" href="http://www.virtualenv.org">virtualenv</a> even
if they do have root access, because it allows you to install whatever
you like without affecting any other installations.  Virtualenv is
also an excellent way to try out Topographica, because you can simply
delete the generated VENV directory if you decide not to keep the
installation, with no effect on your system.


<H3><a name="git">Install via Git</a></H3>

<P>If you want the most current version of Topographica (as many users
will as of 11/2012, given how long it has been since a formal
release), or if you want to track Topographica development over time,
you'll want the 
<a target="_top" href="https://github.com/ioam/topographica">github</a> version of
Topographica instead of installing it via pip.

<!-- CEBALERT: put this somewhere
<P>Before starting, note that if you want to run large simulations
(requiring more than about 3 GB of memory), you should install
Topographica on a 64-bit platform.
-->


<H3><A NAME="postinstall">Running Topographica</A></H3>

<P>Because there are many ways a user might install Topographica (or
any other Python package), the next step is to figure out where the
<kbd>topographica</kbd> script (used for launching Topographica) and
the example and model files (used as starting points for your
modelling) ended up.

<P>If you follow the instructions above, the <kbd>topographica</kbd>
script is usually <kbd>~/.local/bin/topographica</kbd> or
<kbd>~/VENV/bin/topographica</kbd> on Linux, UNIX, and Mac.  On
Windows it is usually
<kbd>%APPDATA%\topographica\bin\topographica</kbd> or
<kbd>%HOME%\VENV\bin\topographica</kbd>.  To save typing, it's useful
to put the location of the <kbd>topographica</kbd> script onto your
command prompt path, instructions for which differ by platform, or to
first change to the directory where the <kbd>topographica</kbd> is
stored.

<P>Similarly, the example files files are usually in
<kbd>~/.local/share/topographica/examples/</kbd> on Linux, UNIX, and
Mac systems, and in
<kbd>%APPDATA%/share/topographica/examples/</kbd> on Windows, or in
the corresponding <kbd>VENV</kbd> directories.

<P>Once you've located the script and the examples, you can start the
GUI version of Topographica from the command prompt using something like:
<kbd>topographica -g ~/.local/share/topographica/examples/tiny.ty</kbd> or
<kbd>topographica -g %APPDATA%/share/topographica/examples/tiny.ty</kbd>

<P>Running Topographica interactively is described in detail in
the <A HREF="../User_Manual/scripts.html">User Manual</A>. If you want
to get straight into working with a full network, a good way to begin
is by working through
the <A HREF="../Tutorials/som_retinotopy.html">SOM</A>
or <A HREF="../Tutorials/gcal.html">GCAL</A> tutorials.

<P> Have fun with Topographica, and be sure to subscribe to
the <A HREF="https://lists.sourceforge.net/lists/listinfo/topographica-announce">topographica-announce</A>
mailing list to hear about future updates!
