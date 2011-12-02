<H2><A NAME="installing-topographica">Installing Topographica with
version control</A></H2>

<P>Version control allows you to keep up to date with the latest
changes made by other developers, and allows you to keep track of your
own changes. Topographica's source code is held in a
central <A HREF="http://subversion.tigris.org/">Subversion</A> (SVN)
repository on <A HREF="http://sourceforge.net/projects/topographica">
SourceForge.net</A>; the repository contains the files making up
Topographica itself (including its documentation), plus source code
versions of most of the various external libraries needed by
Topographica.

<P>Note that documentation may change between releases, so developers
(and others) who want to use a version-controlled copy of Topographica
should be reading the
<A HREF="http://buildbot.topographica.org/doc/Developer_Manual/installation.html">
nightly documentation build</A> rather than the previous release's
documentation at topographica.org.

<P>Also note that the SVN version is occasionally not usable due to
work in progress, but you can check to see if the code currently
builds on a specific platform, or if our suite of code tests pass, by
visiting our
<A HREF="http://buildbot.topographica.org/">automatic tests page</A>.
<!--If you don't need the very latest updates, you can simply
<a href="../Downloads/index.html">download a released version</a>
instead of using SVN.-->

<P>Finally, please bear in mind that most of Topographica's
development occurs under Linux, so if you have a choice that is the
best-supported option.



<H3><A NAME="downloading">Downloading Topographica</A></H3>

<P>To install a version-controlled copy of Topographica, you first
need to obtain a copy of the SVN repository, either by using SVN as
described in our <A HREF="../Downloads/cvs.html">SVN instructions</A>,
or by using an alternative version control system that can interact
with SVN. We ourselves also use and support the distributed version
control system
<A HREF="http://git-scm.com">Git</A>; developers who wish to use this should instead
follow our <A HREF="../Downloads/git.html">git instructions</A>.

<H3><A NAME="installing">Installing Topographica</A></H3>

<P>Once you have obtained the
version-controlled <code>topographica</code> directory, you need to
install Topographica's dependencies. There are two options for
this. The first is to install the required dependencies yourself
(e.g. using your system's package manager, or by installing a
scientific Python package).  The second is to use the Makefile to
build all Topographica's dependencies. If your system has a good
package manager, or a good scientific Python package is available, you
may wish to use the first option, but the second option is frequently
tested and uses versions of external packages that we know to work
well together.


<H4>(Option 1) Installing Topographica's dependencies on your system</H4>

<!-- I want one place to specify dependencies and read that in
elsewhere. Or at least have links in one place only. -->

<P>Binaries of Topographica's dependencies are available for many
platforms, and many package managers also include them. Alternatively,
all Topographica's dependencies (and more!) are available for many
platforms in scientific Python distributions such as <A
HREF="http://www.enthought.com/products/epd.php">EPD</A> (free for
academic use).

<P>If installing the dependencies yourself, you will need at
least <A HREF="http://www.python.org/download/releases/2.6.5/">Python</A>, 
<A HREF="http://www.scipy.org/Download">NumPy</A>, and <A HREF="http://www.pythonware.com/products/pil/">PIL</A>, and preferably
<A HREF="http://sourceforge.net/projects/matplotlib/files/">MatPlotLib</A>, 
<A HREF="http://code.google.com/p/gmpy/">gmpy</A>, 
<A HREF="http://www.scipy.org/Download">SciPy</A>, and 
 <A HREF="http://ipython.scipy.org/moin/">IPython</A> as
 well. Step-by-step instructions: <a href="macinstall.html">Mac
 OSX</a>;
<a href="aptinstall.html">Ubuntu</a> (and other apt-based systems).

<P>Once you have installed the necessary environment, you can create
a <code>topographica</code> script that uses your copy of Python:

<blockquote><code>make PYTHON="/usr/bin/python26" topographica-external-python</code></blockquote>

(where <code>PYTHON="/usr/bin/python26"</code> should be adapted to the
location of your copy of Python if necessary).

<P>Note that you should not run setup.py, since that would install
Topographica into your system's Python directory, whereas we want to
use the version-controlled directory. Also, you can delete
the <code>external</code> directory, since you have already installed
the external dependencies. Now you can skip to
the <A HREF="#postinstall">after installation</A> section below.



<H4>(Option 2) Build all Topographica's dependencies</H4>

Building Topographica's dependencies is usually straightforward on Mac
and Linux. Before beginning, you need to ensure your system has the
prerequisites described below.

<H5><A NAME="mac-prerequisites">Mac OS X</A></H5>

<P>Building Topographica on OS X should be straightforward. Assuming
you are using OS X 10.6 (Snow Leopard), you need to install
Apple's <A HREF="http://developer.apple.com/tools/xcode/">Xcode3</A>
if your system does not already have it. Xcode provides the required
GCC C/C++ compiler (among other development utilities). You can then
follow the instructions below for <A HREF="#building">building</A>
Topographica.

<!--
<P><em>Optional</em>: If you want to compile a local copy of the HTML
documentation, you will also need imagemagick, transfig, and php (if
these are not already installed).
-->

<H5><A NAME="linux-prerequisites">Linux</A></H5>

<P>Most Linux systems will already have the required libraries
installed, so usually no action will be required here.

<P>On some Linux distributions that start with a minimal set of
packages included, such as Ubuntu or the various "live CD" systems,
you may need to install "build tools".  On Ubuntu, for instance, these
are installed via <code>sudo apt-get install build-essential</code>.

<P>Also on these minimal linux distributions, if you want to build and
use the GUI you may need to specify explicitly that some standard
libraries be installed: <code>libx11-dev</code> and
<code>libxft-dev</code>. Note that on some systems the
<code>-dev</code> packages are called <code>-devel</code>, and
sometimes specific versions must be specified. Example for Ubuntu
9.10: 
<blockquote>
<code>sudo apt-get install libx11-dev libxft-dev</code>
</blockquote>

<P>Once any necessary libraries are installed, you can proceed to the
<A HREF="#building">Building</A> instructions below.


<H5><A NAME="building">Building Topographica</A></H5>

<P>The instructions below assume you have followed any necessary
platform-specific instructions described above. You will need a
writable directory with approximately 1.2 GB of space
available (as of July 2010).

<P>Enter the directory where topographica is located and type
<code>make</code> (which may be called <code>gmake</code> on some
systems).  It is best to do this as a regular user in the user's own
directory, not as a root user with special privileges, because
Topographica does not need any special access to your system.  The
build process will take a while to complete (e.g. about 10 minutes
on a 3 GHz Core 2 Duo machine with a local disk).

<P>If you have problems during the build process, try
adding <code>-k</code> to the <code>make</code> command, which will
allow the make process to skip any components that do not build
properly on your machine. Topographica is highly modular, and most
functionality should be accessible even without some of those
components.

<P><i>optional</i>: If desired, you can also make local copies of the
HTML documentation from the web site. To do so, you must have the php,
bibtex, convert, and fig2dev commands installed; type <code>make
all</code> instead of (or after) <code>make</code>.  (If you don't
have those commands, in most distributions you can get them by
installing the php5-cli, tetex, imagemagick, and transfig
<!--CEBALERT: tetex not in ubuntu 9.04; not sure what the new package
is--> packages).  <code>make all</code> will also run the regression
tests and example files, to ensure that everything is functioning
properly on your system.

<P>If building was successful, a script
named <code>topographica</code> will have been created in the
topographica directory, and you can proceed to
the <A HREF="#postinstall">after installation</A> section below.


<H3><A NAME="postinstall">After installation</A></H3>

<P>To launch Topographica itself, you can enter <code>./topographica
-g</code> (or just <code>./topographica</code> for no GUI) from within
the version-controlled topographica directory, or else enter the full
path to the script.

<P>For actual use, you will probably want to add a symbolic link in a
directory that is in your regular path, pointing to the topographica
script. The instructions elsewhere in the documentation assume that
you have done so, so that you only need to type
<code>topographica</code> instead of <code>cd /path/to/topographica ;
./topographica</code>.

<P>You can check that Topographica is working as expected by running
<code>make tests</code> within the topographica directory. If you do
the tests on a machine without a functioning DISPLAY, such as a remote
text-only session, there will be some warnings about GUI tests being
skipped.



  

