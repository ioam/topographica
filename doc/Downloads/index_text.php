<H2><A NAME="installing-topographica">Installing Topographica</A></H2>

<P>Topographica is based on a suite of commonly used tools for
scientific software development, including Python, NumPy, and
PIL. This page describes how to install Topographica and a suitable
scientific Python environment.

<P>If you already have a Python environment that you wish to use for
Topographica, or if your platform is not listed below, instead follow
our instructions for <A HREF="existingpython.html">installing
Topographica into an existing Python environment</A>. 

<P>Developers, as well as users who wish to access the most recent
changes or edit the version-controlled source code, should instead
follow the <A HREF="../Developer_Manual/installation.html">developers'
installation guide</A>.

<!-- CEBALERT: put this somewhere
<P>Before starting, note that if you want to run large simulations
(requiring more than about 3 GB of memory), you should install
Topographica on a 64-bit platform.
-->

<H3><A NAME="win">Windows</A></H3>

<P>Install the <A
HREF="http://code.google.com/p/pythonxy/wiki/Downloads">Python(x,y)</A>
scientific Python environment, which by default includes all the tools
needed by Topographica. Following this, run the self-installing
Topographica <a
href="http://pypi.python.org/packages/any/t/topographica/topographica-0.9.7.win.exe">exe</a>
for Windows. Once complete, proceed to the <A
HREF="#postinstall">After Installation</A> section below.


<H3><A NAME="mac">Mac</H3>

<P>Install the <A
HREF="http://www.enthought.com/products/getepd.php">EPD</A> scientific
Python environment, then run Topographica's <A
HREF="https://sourceforge.net/projects/topographica/files/topographica/0.9.7/topographica-0.9.7-py2.6-macosx10.6.mpkg.zip/download">installer
for EPD on Mac</A>. Once complete, proceed to the <A
HREF="#postinstall">After Installation</A> section below.

<P>Topographica's developers have limited access to OS X, so packaging
contributions from Mac users are welcome!


<H3><A NAME="lin">Linux</A></H3>

<P>We provide packages for Debian-based systems (e.g. Ubuntu), and
RPM-based systems (e.g. Fedora Core). Installing one of these packages
with your package manager will install both the necessary Python
environment and Topographica itself. Users of linux systems that
cannot make use of either of these packaging systems should instead
follow our instructions for <A HREF="existingpython.html">installing
Topographica into an existing Python environment</A>.

<P>If using Ubuntu, you can add <A
HREF="https://launchpad.net/~topographica-developers/+archive/topographica">Topographica's
PPA</A> to your software sources and then install Topographica from
the graphical package manager (Synaptic). This allows Topographica and
its dependencies to be updated automatically for future releases.

<P>Alternatively, download the appropriate deb or rpm for your
platform (currently available: <a
href="http://download.opensuse.org/repositories/home:/ceball:/topographica/Fedora_13/noarch/topographica-0.9.7-9.1.noarch.rpm">Fedora
Core 13</a>; Ubuntu <A
HREF="https://launchpad.net/~topographica-developers/+archive/topographica/+files/topographica_0.9.7-0ubuntu3~lucid_all.deb">Lucid</A>
<A
HREF="https://launchpad.net/~topographica-developers/+archive/topographica/+files/topographica_0.9.7-0ubuntu3~karmic_all.deb">Karmic</A>
<A
HREF="https://launchpad.net/~topographica-developers/+archive/topographica/+files/topographica_0.9.7-0ubuntu3~jaunty_all.deb">Jaunty</A>
<A
HREF="https://launchpad.net/~topographica-developers/+archive/topographica/+files/topographica_0.9.7-0ubuntu3~hardy_all.deb">Hardy</A>)
and install using your graphical software manager (usually launched by
double clicking on the downloaded package). We also recommend that RPM
users install the "Development Tools" package collection from their
graphical software manager (to get access to Topographica's optional
optimized components).

<P>Once the Topographica package has been installed, you can proceed
to the <A HREF="#postinstall">After Installation</A> section below.

<H3><A NAME="postinstall">After installation</A></H3>

<P>Linux and Mac users can run <code>topographica -g</code> from a
terminal to start Topographica. Windows users can double click on the
Topographica icon on the desktop.

<P>Running Topographica interactively is described in detail in
the <A HREF="../User_Manual/scripts.html">User Manual</A>. If you want
to get straight into working with a full network, a good way to begin
is by working through
the <A HREF="../Tutorials/som_retinotopy.html">SOM</A>
or <A HREF="../Tutorials/lissom_oo_or.html">LISSOM</A> tutorials.

<P> Have fun with Topographica, and be sure to subscribe to
the <A HREF="https://lists.sourceforge.net/lists/listinfo/topographica-announce">topographica-announce</A>
mailing list to hear about future updates!
