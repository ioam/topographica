<H2>Obtaining Topographica using Subversion</H2>

<P><A HREF="http://subversion.tigris.org/">Subversion</A> (SVN) is the
version control system used for managing Topographica development.  SVN
keeps track of every change made to any file, and can reconstruct the
state of the software from any date and time in the history of
Topographica development since January 2004 (see the ChangeLog.txt
file for info on each revision).  The Topographica SVN repository
is hosted by <A HREF="http://sourceforge.net/projects/topographica">
SourceForge.net</A>.

<P>The essentials for using SVN at SourceForge are described below;
see the
<A HREF="http://sourceforge.net/docman/display_doc.php?docid=31070&group_id=1">
SourceForge SVN documentation</A> for more details or if you have any
difficulties.  You will need to run at least SVN 1.4 on your machine;
SVN clients 1.3 and below will complain that they are too old to
communicate with our repository.  

<P>Many platforms (e.g. most Linux and other UNIX platforms) already
have all of the necessary programs and libraries required to obtain
Topographica by SVN.  If your machine does not have <code>svn</code>
installed, you will first need to <A
HREF="http://subversion.apache.org/packages.html">install it</A>.

<H3>Downloading</H3>

<P>Once you have SVN installed, the location (URL) of the Topographica
repository to use is
<tt>https://topographica.svn.sourceforge.net/svnroot/topographica</tt>.
In commands given on this page, <code>$TOPOROOT</code> is used to
represent that URL, so please replace it in commands you enter. E.g.,
for bash-like shells, you can begin by typing the following command to
make <code>$TOPOROOT</code> be substituted properly:

<pre>
export TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica
</pre>

<P><A NAME="linux">The Topographica files can then be checked out by
using the command</A>:

<pre>
svn co $TOPOROOT/trunk/topographica topographica
</pre>

<P>This will create a <code>topographica</code> directory in your
present working directory.

<P>The checkout process will likely take several minutes (probably
appearing to hang at certain points), as some large files are
involved.<!-- and subversion is slow...--> Once it has completed, you
can return to the <a
href="../Developer_Manual/installation.html#installing">developer
installation instructions</a> to go through the build process.


<!--
<H4><A NAME="windows">Cygwin:</A></H4>

<P><A HREF="http://www.cygwin.com/">Cygwin</a> is a set of Unix
commands and libraries that make it possible to compile most Unix
programs under Windows.  In principle, it should be possible to
use Topographica under Cygwin, because all of the core Topographica
files are platform independent.  However, some of the external
packages included with Topographica (e.g. python's Tkinter)
automatically detect that they are running under Windows, and install
non-Cygwin versions of themselves.  Users interested in modifying
these makefiles so that Topographica can be installed under
Cygwin should <A
HREF="mailto:&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107">contact
Jim</a> for more details.
-->


<H3>Updating and selecting versions</H3>

Users who have Topographica checked out via SVN can update their copy
of Topographica by changing to the directory containing the
Topographica files and then doing <code>svn update</code>. Note that
updating the external/ subdirectory sometimes takes a long time, if
some of the external packages have been upgraded.

<P>Following the update, repeat the "make" command you originally used
when installing Topographica (the command depends on how you installed
Topographica; return to the <a
href="../Developer_Manual/installation.html#installing">developer
installation instructions</a> for details).

<P>If you wish, you can switch your copy of Topographica to a
different version of the code.  For instance, to update to a
particular revision from the past (e.g. one known to work, if the
current revision is broken for some reason), just add <code>-r
<i>revno</i></code> to the update command.  E.g., to update to
revision r7472 (which ChangeLog.txt shows is the SVN revision number
of release 0.9.4), you can do <code>svn update -r 7472</code>.

<P>There are also various alternative copies of the code for special
purposes, stored in the tags/ and branches/ sections of the SVN
repository. Currently available tags and branches are listed on the <a
href="http://topographica.svn.sourceforge.net/viewvc/topographica/tags/">tags</a>
and <a
href="http://topographica.svn.sourceforge.net/viewvc/topographica/branches/">branches</a>
pages, or you can run e.g. <code>svn ls --verbose
$TOPOROOT/tags/</code>.

