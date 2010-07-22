<H2>Installing into an existing Python environment</H2>

<P>Topographica itself is platform independent, but it depends on
external packages, the installation of which varies by platform. This
page assumes you already have <A
HREF="http://www.python.org/download/releases/2.6.5/">Python
installed</A> (with Tkinter, if you wish to use the GUI), so is most
useful for people who already have a Python environment they want to
use, or who are using a platform other than those <A
HREF="index.html">already described</A>, and who do not need <A
HREF="../Developer_Manual/installation.html">version control</A>. We
have tested Topographica with Python 2.5 and 2.6.

<P>There are two options for ensuring your Python environment has the
appropriate dependencies and then installing Topographica: the first
is to use
Python's <A HREF="http://peak.telecommunity.com/DevCenter/EasyInstall">easy_install</A>
or <A HREF="http://pypi.python.org/pypi/pip">pip</A>, which will get
the dependencies automatically and then install Topographica; the
second is to get the dependencies first yourself, then install
Topographica from the Python source (the "python setup.py install"
way).

<!--the third is to build
Topographica and all its dependencies from source (which is usually
straightforward because we provide an archive and Makefile).-->

<H3>(1) easy_install or pip</H3>

<P>Assuming your system already has easy_install or pip,
typing <code>easy_install topographica</code> or <code>pip install
topographica</code> (with administrative privileges,
e.g. with <code>sudo</code>) should install Topographica into your
system Python directory. Alternatively, you can use the appropriate
options (e.g. <code>--prefix</code>) for easy_install or pip to choose
a different location.

<P>If you want to install Topographica's optional dependencies, you
can use easy_install or pip to additionally install IPython,
MatPlotLib, gmpy, and SciPy (e.g. <code>sudo easy_install ipython gmpy
matplotlib scipy</code>).

<P>Sometimes, easy_install and pip can encounter problems while
installing the packages on which Topographica depends. Fixing these
problems is usually straightforward, as described in the <A
HREF="../FAQ/index.html#easyinstall">FAQ</A>.

<P>Once installation has completed, you can proceed to
the <A HREF="index.html#postinstall">After Installation</A>
instructions.


<H3>(2) Install from Python source ("python setup.py install")</H3>

<!-- CEBALERT: need to update these links and include version information -->

<P>Binaries of Topographica's dependencies are available for many
platforms, and many package managers also include them (e.g. apt-get
on Ubuntu or Fink/Macports on Mac). First install the required
dependencies <A HREF="http://www.scipy.org/Download">NumPy</A>
and <A HREF="http://www.pythonware.com/products/pil/">PIL</A>.
Optionally, then install the other recommended dependencies 
<A HREF="http://sourceforge.net/projects/matplotlib/files/">MatPlotLib</A>,
<A HREF="http://code.google.com/p/gmpy/">gmpy</A>, 
<A HREF="http://www.scipy.org/Download">SciPy</A>, and 
<A HREF="http://ipython.scipy.org/moin/">IPython</A>.

<P>Once the dependencies are installed, download
the <A HREF="http://pypi.python.org/packages/source/t/topographica/topographica-0.9.7.tar.gz">source
distribution</A>, unpack the archive, and type <code>python setup.py
install</code>. Alternatively, choose a different installation
location by passing the appropriate option (e.g. <code>--user</code>
or <code>--prefix</code>).

<P>Once complete, proceed to
the <A HREF="index.html#postinstall">After Installation</A>
instructions.
