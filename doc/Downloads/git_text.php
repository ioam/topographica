<H2>Developing Topographica with Git</H2>

<!-- CEBALERT: this page should be in Developer_Manual/ -->

<P>The master repository for Topographica code is stored by <a
href="cvs.html">Subversion</a> (SVN) at SourceForge.net.  It is often
useful to work on separate copies of the code, e.g. to develop a new,
complicated feature, or to make far-reaching changes that need
extensive testing.  In such cases it can be useful to use the <a
href="http://git.or.cz/">Git</a> version control tool to establish a
local branch of Topographica, so that you can have the benefits of
version control (keeping track of different revisions) without
necessarily affecting the global repository.  If it does turn out that
the local changes would be useful to other Topographica users, they
can then be "pushed" onto the global repository for everyone to use
once they are completed.

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
others you can get installation packages from <a
href="http://git.or.cz/">git.or.cz</a>.  The git-svn package allows
git to connect to Topographica's SVN repository. Note that you should
try to get a Git version of at least 1.7 so that all the features
described on this page are available to you. If you are building from
source, you can skip git-doc, which can be difficult to compile, and
is anyway <a
href="http://www.kernel.org/pub/software/scm/git/docs/">available
online</a>.


<H3>Getting the Topographica code</H3>

<P>First, you need to select the revision from which you would like your
git history to begin. For most work, a recent revision is fine (but make
sure the path you want to get actually existed in that revision). Then,
you can execute the following:

<pre>
# Location of SVN repository
$ export TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica

# Create a new Git repository in the current directory and retrieve
# the SVN files and history
# (you can choose a value for r to get more or less history)
$ git svn clone -r11340 $TOPOROOT/trunk/topographica .

# If you specified a value of r other than HEAD, you need to update
$ git svn rebase
</pre>

If you're getting a recent revision of the <code>topographica</code>
code, the new directory will occupy about 426 megabytes (as of August
2010).

<P>After you have the source code, you probably want to instruct git
to ignore the same files as SVN ignores:

<pre>
(echo; git svn show-ignore) >> .git/info/exclude
</pre>


<H3>Working with your Git repository</H3>

<P>Now that you have the Topographica source code in your own Git
repository, you are free to work on it as you wish. You can commit
files, add files, delete files, and so on. All operations that you
perform with <code>git</code> (such as <code>diff</code> and
<code>commit</code>) are local; only operations with <code>git
svn</code> have the potential to modify the SVN repository. If you are
new to Git, <A HREF="http://git-scm.com/documentation">Git's
documentation page</A> has various tutorials for people with different
backgrounds (including those coming from Subversion).

<P>Note that before committing to your repository for the first time,
you should identify yourself to git:
<pre>
$ git config --global user.email user@address.ext
$ git config --global user.name "User Name"
</pre>

You should also check that your machine has the correct time and date,
otherwise your history can become confusing. 


<H3>Interacting with Topographica's SVN repository</H3>

<P>To interact with our SVN repository, there are several possible
workflows you could adopt. We recommend the following workflow:




<ol>

<li>To start work on some new feature, create a new branch
called <code>feature</code> from <code>master</code> (the SVN
branch): <code>git checkout -b feature</code></li>

<li>Make your changes, commit them, and test them (probably multiple
iterations).</li>

<li><i>(Optional)</i> If you have made a lot of commits and they do
not form a coherent story, collapse them using git's <a
href="http://book.git-scm.com/4_rebasing.html">rebase</a>. The safest
way to do this is to first create a new branch of <code>feature</code>
(<code>git checkout -b feature_clean</code>); this way, what you
actually did is preserved in the <code>feature</code> branch. In the
new branch, run <code>git rebase --interactive HEAD~i</code>, where
<code>i</code> is the number of commits back from the current position
that you want to sort out. This will open an editor (as specified by
the <code>GIT_EDITOR</code> environment variable) where you can
rearrange, squash, or remove individual commits. The end result should
be a single commit with a log message describing the new feature.

<li>Update your SVN branch to get changes made by others while you
were working on your feature: <code>git checkout master; git svn
rebase</code>.</li>

<li>Rebase your changes onto the tip of the SVN branch. First, change
to the feature branch: <code>git checkout feature</code> (or <code>git
checkout feature_clean</code> if you followed step 3). Then, perform
the rebase (moving your "feature" commits to appear after the latest
SVN changes): <code>git rebase master</code>. Your changes need to
appear at the tip in this way (i.e. they need to be 'fast forwarded'),
since that is the point at which they will actually be committed to
SVN.</li>

<li>Test your changes and commit fixes if necessary. Other people
might have introduced incompatibilities with your code into SVN while
you were working on step 2, so it is important to check your changes
are still valid (and not just that they merge without conflict). If
you followed optional step 3, you probably now want to run <code>git
rebase --interactive HEAD~j</code> again to incorporate any new
commits into the one you created earlier.</li>

<li>Merge your feature branch back into the main branch, then commit
to SVN: <code>git checkout master; git merge feature</code> (or
<code>feature_clean</code> if you followed step 3), then <code>git svn
dcommit</code>. (If you first want to see what will happen when you
commit to svn, you can do a dry run by passing <code>-n</code> to
<code>dcommit</code>.</li>

<li>Now that your feature is complete and in SVN,
you can branch <code>master</code> again to start on the next
feature!</li>

</ol>

Branching in git is fast, so if you are ever unsure what effect an
operation will have on the <code>master</code> or <code>feature</code>
branches, create new branches from them and test out the command using
the copies. An unwanted <code>test</code> branch can be deleted with
<code>git branch -d test</code>.


<H3>Repository backup and sharing work in progress</H3>

<P>With git, you are usually working locally. Therefore, it is a good
idea to back up your repository. You could simply copy the repository
elsewhere to do this, but this does not make your work visible to
others (until you dcommit back to SVN). Please request a remote
git repository on SourceForge.net from the Topographica admins. Then, with your repository
<code>NAME</code> on SourceForge.net, you can mirror your local
repository like this:

<pre>
$ git remote add NAME ssh://username@topographica.git.sourceforge.net/gitroot/topographica/NAME
</pre> 

You can then push your local repository to the remote one as often as
you want:

<pre>
$ git push NAME
</pre>

Note that you should read the documentation for <code>push</code> to
ensure that you share the branch(es) you are expecting to. You probably
want to use the <code>--all</code> or <code>--mirror</code> options to
share everything.

<P>
Your repository on SourceForge will be visible on the web:
<pre>
http://topographica.git.sourceforge.net/git/gitweb.cgi?p=topographica/NAME
</pre>



<!-- ADMIN NOTE: to create ceball_houzi2 repository

$ ssh -t ceball,topographica@shell.sourceforge.net create

(1) Create repository

[sf.net]$ cd /home/scm_git/t/to/topographica
[sf.net]$ git --git-dir=ceball_houzi2 init --shared=all --bare

(2) Edit description (one line e.g. "celiaf - video camera")

[sf.net]$ emacs -nw ceball_houzi2/description 

(3) Configure repository to (a) deny deletes and (b) send emails to topographica-cvs

[sf.net]$ emacs -nw ceball_houzi2/config

---config---
[receive]
        ...
	denyDeletes = true

[hooks]
        mailinglist = "topographica-cvs@lists.sourceforge.net"
        announcelist =
        envelopesender =
        emailprefix = "SF.net Git: "
        showrev = "git show -C %s; echo"
        emailmaxlines = 500
---config---

Then, edit ceball_houzi2/hooks/post-receive.sample so that the line in
there calling "post-receive-email" is uncommented (it's the only line
in there at the moment) and save it as post-receive. Also, chmod +x
post-receive.

-->

<!--
# Backups (currently no rsync access? docs on sf.net out of date?)
$ rsync -av topographica.git.sourceforge.net::gitroot/topographica/* date-topographica-git
-->



<!-- OTHER NOTES

with all the manipulations git can do, "git reflog" comes in handy to
tell you what you've been doing 

-->
