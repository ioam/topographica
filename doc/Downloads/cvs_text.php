<H2>Developing Topographica using Subversion</H2>

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
communicate with our repository.  Note that the SVN version is not
always usable due to work in progress, but you can check to see if the
code currently builds on a specific platform, or if our suite of code
tests pass, by visiting our
<A HREF="http://buildbot.topographica.org/">automatic tests page</A>.
If you don't need the very latest updates, you can simply
<a href="index.html">download a released version</a> instead of using
SVN.

<P>Many platforms (e.g. most Linux and other UNIX platforms) already
have all of the necessary programs and libraries required to obtain
Topographica by SVN.  If your machine does not have <code>svn</code>
installed, you will first need to <A
HREF="http://subversion.apache.org/packages.html">install it</A>.

<H3>Downloading via Subversion</H3>

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
present working directory; omitting the final
<code>topographica</code> will put the files directly into your
present directory.

<P>The checkout process will likely take several minutes (probably
appearing to hang at certain points), as there are some extremely
large files involved. Once it has completed, you can return to the
instructions
for <a href="../Developer_Manual/installation.html">installing
Topographica</a> to go through the build process.




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


<H3>Updating and selecting versions using Subversion</H3>

Users who have Topographica checked out via SVN can update their copy
of Topographica by changing to the directory containing the
Topographica files and then doing:

<pre>
  svn update 
  make
</pre>

<P>Note that updating the external/ subdirectory sometimes takes a
long time, if some of the external packages have been upgraded, and in
that case "make" can also take some time to build.

<P>If you wish, you can switch your copy of Topographica to a
different version of the code.  For instance, to update to a
particular revision from the past (e.g. one known to work, if the
current revision is broken for some reason), just add <code>-r
<i>revno</i></code> to the update command.  E.g., to update to
revision r7472 (which ChangeLog.txt shows is the SVN revision number
of release 0.9.4), you can do <code>svn update -r 7472</code>.

<P>There are also various alternative copies of the code for
special purposes, stored in the tags/ and branches/ sections of the
SVN repository.  For instance, if you currently have the 
trunk version as described above, you can switch to the version tagged
LATEST_STABLE (usually the latest release) by typing:
<pre>
svn switch $TOPOROOT/tags/LATEST_STABLE/topographica
</pre>

<P>To switch from the LATEST_STABLE version back to the trunk version,
replace <code>tags/LATEST_STABLE</code> with <code>trunk</code> and
run the command again.  The currently available tags are listed on the 
<a href="http://topographica.svn.sourceforge.net/viewvc/topographica/tags/">tags
page</a>, or you can run the command <code>svn ls --verbose
$TOPOROOT/tags/</code>.

<P>Similarly, to switch to a separate branch named 'some-branch',
replace <code>tags/LATEST_STABLE</code> with
<code>branches/some-branch</code>.  Branches are listed on the 
<a href="http://topographica.svn.sourceforge.net/viewvc/topographica/branches/">branches
page</a>, or you can run the command <code>svn ls --verbose
$TOPOROOT/branches/</code>.

<P>You can discover if your copy is from the trunk or a particular
branch or tag by typing <code>svn info | grep URL</code>.  Again, note
that tags and branches are usually only for very specific purposes;
most people will want the trunk or else some specific recent revision.

