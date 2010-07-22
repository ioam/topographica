<H2>Developing Topographica with Git</H2>

<!-- CEBALERT: this page should be in Developer_Manual/ -->

<P>The master repository for Topographica code is stored by
<a href="cvs.html">Subversion</a> (SVN) at SourceForge.net.  It is
often useful to work on separate copies of the code, either to develop
a new, complicated feature, to make far-reaching changes that need
extensive testing, or to keep track of changes useful only at your
local site (such as private research code).  In such cases it can be
useful to use the <a href="http://git.or.cz/">Git</a> version control
tool to establish a local branch of Topographica, so that you can have
the benefits of version control (keeping track of different revisions)
without necessarily affecting the global repository.  If it does turn
out that the local changes would be useful to other Topographica
users, they can then be "pushed" onto the global repository for
everyone to use once they are completed.

<P>SVN's own branching and merging facilities can be used in some
cases, but (a) they are only available to Topographica developers, (b)
they are far more difficult to use and error-prone than those from git
and other
<a href="http://www.inf.ed.ac.uk/teaching/courses/sapm/2007-2008/readings/uvc/version-control.html">
distributed version control systems</a>, (c) they require constant
access to a centralized server, and thus cannot provide version
control when no network connection is available, and (d) most
operations are slow, in part because of the dependence on the remote
server.  Branches maintained using git have none of these problems,
and because git can work seamlessly with the centralized SVN server
when necessary, git can be very useful for any of the uses mentioned
above.

<H3>Installing git on your machine</H3>

<P>Although git is not typically installed in most Linux
distributions, it is usually easy to add it.  E.g. for Debian or
Ubuntu Linux, just do 'apt-get install git git-svn git-doc'; for
others you can get installation packages from
<a href="http://git.or.cz/">git.or.cz</a>.  The git-svn package allows
git to connect to Topographica's SVN repository. Note that you should
try to get Git version 1.6.5.3 (used while writing this document) or
later. If you are building from source, you can skip git-doc, which
can be difficult to compile, and is anyway <a href="http://www.kernel.org/pub/software/scm/git/docs/">available online</a>.


<H3>Getting the Topographica code</H3>

<P>First, you need to select the revision from which you would like your
git history to begin. For most work, a recent revision is fine (but make
sure the path you want to get actually existed in that revision). Then,
you can execute the following:

<pre>
# location of SVN repository
$ export TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica

# create directory to hold new files
$ mkdir topographica; cd topographica

# create a new Git repository
$ git svn init $TOPOROOT/trunk/topographica

# retrieve the SVN files and history
# (you can choose a value for r - choose a recent svn revision)
$ git svn fetch -r10782; git svn rebase
</pre>

(substituting values appropriate for what you wish to do; e.g. you can
get more history by changing <code>-r</code>). If you're getting a
recent revision of the <code>topographica</code> code (and not
<code>facespace</code>), the new directory will occupy about 124
megabytes (as of February 2008).

<P>If you wished, you <i>could</i> get the complete history of the
Topographica project, using:
<pre>
 git svn clone $TOPOROOT/trunk/topographica topographica
</pre>
instead of all of the above commands after <code>export</code>, to
make a new directory <code>topographica/</code> with a copy of the
entire repository (620MB as of 2/2008) plus a working copy.  This will
usually take 2-3 hours to run, although you would only need to do it
once (because after that you could use branches to create different
versions).  Note that this only gets the trunk; if you want all tags
and branches as well (which seems unlikely), you can use the -T and -B
options described in the git manual.  In any case, this method is not
usually necessary, unless you want to do some comparison across a wide
range of historical versions of Topographica.

<P>After you have the source code, you probably want to
<A HREF="index.html#building-topographica">build Topographica</A>. You
probably also want to instruct git to ignore the same files as SVN
ignores:
<pre>
(echo; git svn show-ignore) >> .git/info/exclude
</pre>
If <code>svn:ignore</code> properties are subsequently changed in the
SVN repository, you will have to update your <code>exclude</code>
information.


<H3>Working with your Git repository</H3>

<P>Now that you have the Topographica source code in your own Git
repository, you are free to work on it as you wish. You can commit
files, add files, delete files, and so on. All operations that you
perform with <code>git</code> (such as <code>diff</code>
and <code>commit</code>) are local; only operations
with <code>git svn</code> have the potential to modify the SVN
repository.

<P>If you are new to Git, you might find
the <A HREF="http://www.kernel.org/pub/software/scm/git/docs/tutorial.html">Git
tutorial</A> useful. We recommend that you read through the 
<A HREF="http://git.or.cz/course/svn.html">crash course for SVN
users</A>, which will help you to avoid being surprised by differences
between similarly named git and svn commands. If you are still puzzled
by a particular operation in Git,
the <A HREF="http://git.or.cz/gitwiki/GitFaq">Git FAQ</A> is often
helpful.

<!--
<P>Note that for subversion users, <code>git revert</code> the behavior of <code>git
commit</code> in particular might be surprising when adding new files,
so be sure to take a look at
the <A HREF="http://www.kernel.org/pub/software/scm/git/docs/git-commit.html">git-commit
man page</A> or see the FAQ
entry <A HREF="http://git.or.cz/gitwiki/GitFaq#head-3aa45c7d75d40068e07231a5bf8a1a0db9a8b717">Why
is "git commit -a" not the default?</A>.
-->

<P>Before committing to your repository for the first time, you should
identify yourself to git:
<pre>
ceball@doozy:~/g$ git config --global user.email user@address.ext
ceball@doozy:~/g$ git config --global user.name "User Name"
</pre>

You should also check that your machine has the correct time and date,
otherwise your history can become confusing. Other configuration
options are available by reading <code>man git-config</code>.

<P>After working on your own repository, there are a couple of
operations that you will probably want to perform at some stage:
tracking other peoples' changes to the Topographica SVN repository,
adding your changes to the Topographica SVN repository, and sharing
your Git repository. These are discussed in the following sections.


<H4>Tracking Topographica's SVN repository</H4>

<P>To get updates from the Topographica SVN repository, your own copy
should have no uncommitted changes. (If you do have uncommitted
changes,
the <A HREF="http://www.kernel.org/pub/software/scm/git/docs/git-stash.html">git
stash</A> command allows you to store those changes for later
retrieval.)

<pre>
# (git stash if required)
$ git svn rebase
# (git stash apply; git stash clear if required)
</pre>

<code>rebase</code> moves a whole branch to a newer "base" commit;
see <A HREF="http://www.kernel.org/pub/software/scm/git/docs/user-manual.html#using-git-rebase">Keeping
a patch series up to date using git-rebase</A> from the Git user
manual for further explanation.


<H4>Sending your changes to Topographica's SVN trunk</H4>

<P>Changes that you have committed in your local git repository are
not automatically exported to the main SVN repository for
Topographica, letting you use version control even for things that are
not meant to be part of the main Topographica distribution.  If you do
want your changes to be made public, then run:

<pre>
git svn dcommit
</pre>

This will send each of your git commits, in order, to the SVN
repository, preserving their log messages, so that to an SVN user it
appears you made each of those changes one after the other in a
batch. 

<P>If you want to see exactly what is going to happen without making
any actual changes, you might wish to try a 'dry run' first by
specifying <code>-n</code>:

<P>As with SVN, before committing to the central repository you should
first check that you have updated and tested your code with changes
from others (<code>git svn rebase; make tests</code>) to ensure that
your changes are compatible (and not just that they apply
cleanly). Any actual conflict encountered by <code>git svn</code>
(e.g.  you try to commit a file which has been updated by someone else
while you were working on it) will stop the <code>dcommit</code>
process, and the SVN error will be reported. At this point, you can
use the usual git commands to deal with such merge conflicts.

<P>Finally, note that it is possible to rewrite your history before
sending your changes to SVN. This can be very useful to turn a large
number of small changes into a few coherent ones. See the
documentation of <code>git rebase</code> for more information.


<H3>Taking advantage of more of Git's capabilities</H3>

<P>Git is very flexible, and provides far more than is mentioned
above.  There are many useful git tutorials on the web explaining more
advanced git usage (e.g. <a
href="http://www-cs-students.stanford.edu/~blynn/gitmagic/">Git
Magic</a>). Below, we describe a few particular features. 


<H4>Working on multiple independent features</H4>

One thing that you will probably want to do as soon as you are
familiar with basic git-svn operation is to use one branch to track
the svn repository, and then use a new branch for each independent set
of changes:

<pre>
$ git checkout -b testing123
Switched to a new branch 'testing123'
# (edit code)
$ git commit -m "Added x." somefile
# (more editing)
$ git commit -m "Added y." anotherfile
</pre>

At this point, your new changes exist only on the testing123
branch. If you switch back to the master branch, the recent changes
will not show up:

<pre>
$ git checkout master
Switched to branch 'master'
$ git log
# recent commits don't show
</pre>

You could now work on another feature by creating a new branch. Or, if
you have finished the work on the testing123 branch, you can merge the
changes into your master branch, and then commit them to the central
SVN repository:

<pre>
$ git merge testing123
# info about merge appears
$ git svn dcommit
# info about svn commit appears
$ git branch -d testing123
Deleted branch testing123 (was d8d6b8d).
</pre>

To keep a long-term branch up to date with svn:
<pre>
$ git checkout master
$ git svn rebase
$ git checkout testing123
$ git rebase master 
</pre>

The procedures described above are only suggestions. The only requirement
is that, at the point of interaction with our SVN repository, you


<H4>Sharing your work</H4>

<P>If you are working on a complex new feature over a long period of
time, you might want to share your work before it is finished. To do
this, ask one of the Topographica admins to create a git repository
for the feature on SourceForge.net. The admin will give you a remote
repository name (e.g. NAME), which you should tell git about:

<!--
ssh -t ceball,topographica@shell.sourceforge.net create
cd /home/scm_git/t/to/topographica
git --git-dir=ceball_houzi2 init --shared=all --bare
emacs -nw ceball_houzi2/description
emacs -nw ceball_houzi2/config # allow fastforwards - see above

[receive]
        denyNonFastforwards = false

You should NOT do this if others are also actively developing on the
remote, because the remote's history will be rewritten and they will
get very confused.

# Backups:
rsync -av topographica.git.sourceforge.net::gitroot/topographica/* date-topographica-git
 

# emails:

create hook email file in hooks directory (copy from another repo on there
or get ://git.kernel.org/?p=git/git.git;a=blob_plain;f=contrib/hooks/post-receive-email
chmod a+x post-receive

in git config,

[hooks]
        mailinglist = "name@address"
        announcelist =
        envelopesender =
        emailprefix = "SF.net Git: "
        showrev =
-->

<pre>
$ git remote add NAME ssh://username@topographica.git.sourceforge.net/gitroot/topographica/NAME
</pre> 

Then, you can push your repository to the host:

<pre>
$ git push NAME
</pre>

Note that you should read the documentation for <code>push</code> to
ensure that you share the branch you are expecting to (you might want
to use the <code>--all</code> or <code>--mirror</code> options).

<P>
If your repository is on SourceForge, it will be visible on the web:
<pre>
http://topographica.git.sourceforge.net/git/gitweb.cgi?p=topographica/NAME
</pre>

Others can get a copy of your repository using the following command:

<pre>
$ git clone git://topographica.git.sourceforge.net/gitroot/topographica/NAME
</pre>

They can see your branches, and then change into your
<code>newfeature</code> branch:

<pre>
$ git branch -r
$ git checkout origin/newfeature
</pre>

In the future, they can get your latest changes with <code>git
pull</code>, or by rebasing:

<pre>
$ git checkout master
$ git fetch origin
$ git rebase origin
</pre>

See e.g. the
tutorial <A HREF="http://toroid.org/ams/git-central-repo-howto">Using
Git with a central repository</A> for more information about working
with a central, shared repository.

<P>One thing to bear in mind is that if you are using git to
collaborate with others on a feature, you will not easily be able to
keep your repository up to date with SVN by using <code>rebase</code>,
since that will change your history, making it difficult to share
changes with others.  If, however, no other user will be making
changes to your published repostitory, then there will not be a
problem.

<P> Finally, once your feature is complete, you can commit all your
work to the central SVN repository using <code>git svn dcommit</code>
as described earlier. After this point, it is highly unlikely that you
will be able to continue using the remote repository (because svn does
not have all the features of git, the "git svn dcommit" command
necessarily alters the history of your local repository in a way that
will likely leave it incompatible with that of the copy on the remote
host). You will likely want to have the remote git repository archived
at this point. Your local repository of course remains usable, and you
can create a new remote copy if you begin working on another extended
feature.


<!-- based on http://sourceforge.net/apps/trac/sourceforge/wiki/Git, http://www.naildrivin5.com/daveblog5000/?p=102 and
http://projects.scipy.org/numpy/wiki/GitMirror to some extent -->


<!-- with all the manipulations git can do, "git reflog" comes in handy
to tell you what you've been doing -->

<!--
gitk readable fonts

[ -r ~/.gitk ] || cat > ~/.gitk << EOF
set mainfont {Arial 10}
set textfont { Courier 10}
set uifont {Arial 10 bold}
EOF
-->

<H4>Sharing research code between machines</H4>

<P>If you are doing modeling work and want to use your version of
Topographica on multiple machines, you can use git to keep multiple
copies of a repository in sync. Of course, you could just use svn to
keep separate Topographica installations in sync, but this has the
disadvantage that you will also get other people's changes (i.e. you
will have to use the latest svn version of Topographica), and your
code will be publicly visible. You could use an svn branch to solve
the first problem (though not the second), but it can be difficult
later on to merge svn branches (i.e. to recombine your work with other
people's work in svn). You could also use e.g. rsync to maintain
identical copies, but this does not have the flexibility of git
(e.g. of allowing easy machine-specific modifications), and you would
need to exclude built, binary files.

<P>Assuming your work is already in a git repository (as described
earlier), you can use <code>git clone</code> on any other machine
where you'd like to get a copy of your repository. The git
documentation covers cloning, but here is an example over ssh:
<pre>
git clone ssh://user@machine/path/to/repository
</pre>

<P>While working on your code on the 'master' copy, take advantage of
git (as described earlier: git commits are local, not broadcast to
others, and can easily be changed/undone later). When you have
committed changes that you'd like to appear on the other machine, do
the following on that machine's copy of the repository: 
<pre>
$ git fetch origin
$ git rebase origin
</pre>

<P>
If you only ever make changes to the master copy, =git rebase= will be
a simple operation and will only ever need to happen 'one way' (from
the master copy to the other machine). Note, however, that git is very
flexible, and it is easy to make changes to multiple copies while
keeping them all in sync (use branches and <code>pull</code>
or <code>fetch</code>+<code>rebase</code>).

<P>
Additionally, you can use git to track modifications that should
remain local to one machine. For instance, perhaps one copy is on a
machine that needs special modifications to the code in order to run
(e.g. a job submission command). You don't want to share such
modifications, but it is still useful to have them under version
control:

<pre>
[oddmachine]$ git checkout -b oddbranch
[oddmachine]$ # make oddmachine-specific modifications
[oddmachine]$ git commit -m "Special modifications for oddmachine." 

[normalmachine]$ # make modifications to be shared
[normalmachine]$ git commit -m "Did something." 

# get changes made on normalmachine
[oddmachine]$ git checkout master
[oddmachine]$ git fetch origin
[oddmachine]$ git rebase origin

# get changes from master branch into oddbranch
[oddmachine]$ git checkout oddbranch
[oddmachine]$ git rebase master

[oddmachine]$ # run simulations (from oddbranch)
</pre>
