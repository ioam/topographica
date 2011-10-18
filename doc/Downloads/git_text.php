<H2>Obtaining Topographica using Git</H2>

<P>The master repository for Topographica code is stored
by <a href="cvs.html">Subversion</a> (SVN) at
SourceForge.net. However, many other version control systems can
interact with an SVN repository, so you are free to use an
alternative. In particular, Git (along with other distributed version
control systems) allows one to take advantage of version control
without having to be a registered Topographica developer.

<P>Although git is not typically installed in most Linux
distributions, it is usually easy to add it.  E.g. for Debian or
Ubuntu Linux, just do 'apt-get install git git-svn git-doc'; for
others you can get installation packages
from <a href="http://git-scm.com/">git-scm.com</a>.  The git-svn
package allows git to connect to Topographica's SVN repository. Note
that you should try to get a Git version of at least 1.7 so that all
the features described on this page are available to you. If you are
building from source, you can skip git-doc, which can be difficult to
compile, and is
anyway <a href="http://git-scm.com/documentation">available
online</a>.


<H3>Downloading</H3>

<P>First, you need to select the SVN revision from which you would
like your git history to begin (for most work, the current
revision -- <code>HEAD</code> -- is fine). Then, execute the following:

<pre>
# Location of SVN repository
$ export TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica

# Create a new Git repository in the current directory and retrieve
# the SVN files and history
# (you can choose a value for r to get more or less history)
$ git svn clone -rHEAD $TOPOROOT/trunk/topographica .

# If you specified a value of r other than HEAD, you need to update
$ git svn rebase
</pre>

If you're getting a recent revision of the <code>topographica</code>
code, the new directory will occupy about 430 megabytes (as of October
2011).

<P>After you have the source code, you probably want to instruct git
to ignore the same files as SVN ignores:

<pre>
(echo; git svn show-ignore) >> .git/info/exclude
</pre>

<P>The checkout process will likely take several minutes (probably
appearing to hang at certain points). Once it has completed, you can
return to
the <a href="../Developer_Manual/installation.html#installing">developer
installation instructions</a> to go through the build process.


<H3>Updating</H3>

<P>Assuming Topographica's SVN files are in your git <code>master</code> branch, you can
update them by changing to the master branch and typing <code>git svn rebase</code>.

<P>Following any update, repeat the "make" command you originally used
when installing Topographica (the command depends on how you installed
Topographica; return to the <a
href="../Developer_Manual/installation.html#installing">developer
installation instructions</a> for details).
