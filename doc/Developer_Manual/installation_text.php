<H2><A NAME="installing-topographica">Installing Topographica with
version control</A></H2>

<P>Version control allows you to keep up to date with the latest
changes made by other developers, and allows you to keep track of your
own changes. Topographica's source code is held in a
central Git repository on GitHub.com; the repository contains the files making up
Topographica itself (including its documentation).  Source code
versions of most of the various external libraries needed by
Topographica are kept at <A
HREF="http://sourceforge.net/projects/topographica">SourceForge</a>,
but few developers will need these.

<P>Note that documentation may change between releases, so developers
(and others) who want to use a version-controlled copy of Topographica
should be reading the
<A HREF="http://buildbot.topographica.org/doc/Developer_Manual/installation.html">
nightly documentation build</A> rather than the previous release's
documentation at topographica.org.

<P>Also note that the Git version is occasionally not usable due to
work in progress, but you can check to see if the code currently
builds on a specific platform, or if our suite of code tests pass, by
visiting our
<A HREF="http://buildbot.topographica.org/">automatic tests page</A>.

<P>Finally, please bear in mind that most of Topographica's
development occurs under Linux, so if you have a choice that is the
best-supported option.


<H3><A NAME="installing">Installing Topographica</A></H3>

<P><A NAME="downloading"></a>First, clone the public Topographica
repository as described at
<a target="_top" href="https://github.com/ioam/topographica">github</a>.  You can then
either install the dependencies as described there and then skip to
the <A HREF="#postinstall">after installation</A> instructions, or
you can build them all yourself (described below).

<H4>(Optional) Build all Topographica's dependencies</H4>

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

<P><em>Optional</em>: If you want to compile a local copy of the HTML
documentation, you will also need imagemagick, transfig, and php (if
these are not already installed).

<H5><A NAME="linux-prerequisites">Linux</A></H5>

<P>Many Linux systems will already have the required libraries
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
installing the php5-cli, tetex (or texlive), imagemagick, and transfig
packages).  <code>make all</code> will also run the regression
tests and example files, to ensure that everything is functioning
properly on your system.

<P>If building was successful, you can proceed to
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



  

