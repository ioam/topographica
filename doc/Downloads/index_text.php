<H2><A NAME="installing-topographica">Installing Topographica</A></H2>

<P>The typical way to install the most recently released version of
Topographica is via
<A target="_top" HREF="http://www.pip-installer.org">pip</A>
from the commandline in Linux, Mac, or Windows:

<PRE>pip install --user topographica</PRE>

<P>This will install Topographica and its required dependencies
(currently numpy and PIL for the 0.9.7 release) using
<a target="_top" href="http://pypi.python.org/pypi/topographica">PyPI</A>.
Beyond these absolutely required packages, you will probably also want
to install others necessary for good performance (by at least a factor
of 100), to provide some optional types of plotting, and to improve
the command-line interface:

<PRE>pip install --user gmpy matplotlib scipy ipython</PRE>

<P>Other useful packages are described on our
<a target="_top" href="dependencies.html">dependencies</A> page, and
can usually be installed the same way.

<P>If you have root or adminstrator access to your machine and want
these libraries to be available to all users of your system, you can
omit <code>--user</code> or install the dependencies via your system's
package manager, if any.

<P>If your system does not have pip installed but you do have root or
administrator access, you can install pip using:

<PRE>easy_install pip</PRE>

or the equivalent for your package manager.


<H3><a name="virtualenv">Virtualenv</a></H3>

<P>If your machine lacks pip and you do not have root</A> or
administrator access, then you can obtain a local copy of pip by
downloading
<a target="_top" href="https://raw.github.com/pypa/virtualenv/master/virtualenv.py">virtualenv.py</a>.
Just run it using Python to create a clean "virtual environment" that
includes pip and into which you can install Topographica and its
dependencies:

<PRE>
$ python ./virtualenv.py VENV
$ VENV/bin/pip install topographica
$ VENV/bin/topographica -g
</PRE>

<P>Of course, instead of VENV you can use any name you like for your
virtual environment, and you can have multiple different virtual
environments for different purposes.

<P>Many people use 
<a target="_top" href="http://www.virtualenv.org">virtualenv</a> even
if they do have root access, because it allows you to install whatever
you like without affecting any other installations.  Virtualenv is
also an excellent way to try out Topographica, because you can simply
delete the generated VENV directory if you decide not to keep the
installation, with no effect on your system.


<H3><a name="git">Revision-controlled version</a></H3>

<P>If you want the most current version of Topographica (as most users
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


<H3><A NAME="postinstall">After installation</A></H3>

<P>Linux and Mac users can run <code>topographica -g</code> from a
terminal to start Topographica. Windows users can double click on the
Topographica icon on the desktop if an icon is present, or else
run <code>topographica -g</code> from a cmd terminal window.

<P>Running Topographica interactively is described in detail in
the <A HREF="../User_Manual/scripts.html">User Manual</A>. If you want
to get straight into working with a full network, a good way to begin
is by working through
the <A HREF="../Tutorials/som_retinotopy.html">SOM</A>
or <A HREF="../Tutorials/gcal.html">GCAL</A> tutorials.

<P> Have fun with Topographica, and be sure to subscribe to
the <A HREF="https://lists.sourceforge.net/lists/listinfo/topographica-announce">topographica-announce</A>
mailing list to hear about future updates!
