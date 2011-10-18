<H2>Developing Topographica Using Git</H2>

<P>It is often useful to work on separate copies of the code, e.g. to
develop a new, complicated feature, or to make far-reaching changes
that need extensive testing.  In such cases it can be useful to use
the <a href="http://git-scm.com/">Git</a> version control tool to
establish a local branch of Topographica, so that you can have the
benefits of version control (keeping track of different revisions)
without necessarily affecting the global repository.  If it does turn
out that the local changes would be useful to other Topographica
users, they can then be "pushed" onto the global repository for
everyone to use once they are completed. 

<P>SVN's own branching and merging facilities could be used instead,
but (a) they are only available to Topographica developers, (b) they
require constant access to a centralized server, and thus cannot
provide version control when no network connection is available, and
(c) most operations are slow, in part because of the dependence on the
remote server.  Branches maintained using git have none of these
problems, and because git can work seamlessly with the centralized SVN
server when necessary, git can be very useful for any of the uses
mentioned above. If you do use SVN branches instead of Git, please be
sure you are using SVN version 1.5 or later and know about
the <code>--reintegrate</code> option of <code>svn merge</code>.


<H3>Working with your Git repository</H3>

<P>Once you have the Topographica source code in your own Git
repository (as described on
the <A HREF="../Downloads/git.html">downloads</A> page), you are free
to work on it as you wish. You can commit files, add files, delete
files, and so on. All operations that you perform
with <code>git</code> (such as <code>diff</code> and
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


<H3>Repository backup and sharing work in progress</H3>

<P>With git, you are usually working locally. This means your work is
(a) not backed up and (b) not visible to others. Not backing up your
work is risky, and if others are not aware of your work, unnecessary
duplication or conflict could occur. You can solve (a) alone by making
a copy of your repository elsewhere, but you can solve (a) and (b) by
obtaining a git repository on SourceForge.net. To do so, please
request a repository from us. Once you have your repository
<code>NAME</code> on SourceForge.net, you can mirror your local
repository like this:

<pre>
$ git remote add NAME ssh://username@topographica.git.sourceforge.net/gitroot/topographica/NAME
</pre> 

You can then push your local repository to the remote one as often as
you want by doing e.g. 
<pre>
$ git push --mirror NAME
</pre>

<P>Our git repositories
are <A HREF="http://topographica.git.sourceforge.net/git/gitweb-index.cgi">visible
on the web</A>, and commit messages are sent to the topographica-cvs
mailing list.



<H3>Interacting with Topographica's SVN repository</H3>

<P>To interact with our SVN repository, there are several possible
workflows you could adopt. However, we strongly recommend the
following workflow:

<ol>

<li>To start work on some new feature, create a new branch
called <code>feature</code> from <code>master</code> (the SVN
branch): <code>git checkout -b feature</code></li>

<li>Make your changes, commit them, and test them (probably multiple
iterations, potentially over a long period).</li>

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

<li>As with SVN updates, repeat the "make" command used to install
Topographica (see
the <A HREF="installation.html#installing">installation
instructions</A>).</li>

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
dcommit</code>. If you first want to see what will happen when you
commit to svn, you can do a dry run by passing <code>-n</code> to
<code>dcommit</code>. Note that before sending your changes to SVN,
you should ensure that you have followed
the <A HREF="../revisioncontrol.html">general revision control
guidelines</A>.</li>

<li>Now that your feature is complete and in SVN,
you can branch <code>master</code> again to start on the next
feature!</li>

</ol>

Branching in git is fast, so if you are ever unsure what effect an
operation will have on the <code>master</code> or <code>feature</code>
branches, create new branches from them and test out the command using
the copies.



<!-- ADMIN NOTE: to create an SF.net repository NEWREPONAME

$ ssh -t ceball,topographica@shell.sourceforge.net create

(1) Create repository

[sf.net]$ cd /home/scm_git/t/to/topographica
** BE CAREFUL! OTHER PEOPLE'S REPOSITORIES ARE IN THIS DIRECTORY! **
[sf.net]$ git --git-dir=NEWREPONAME init --shared=all --bare

(2) Edit description (one line e.g. "celiaf - video camera")

[sf.net]$ emacs -nw NEWREPONAME/description 

(3) Configure repository to (a) deny deletes and (b) send emails to topographica-cvs

[sf.net]$ emacs -nw NEWREPONAME/config

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

Then, edit NEWREPONAME/hooks/post-receive.sample so that the line in
there calling "post-receive-email" is uncommented (it's the only line
in there at the moment) and save it as post-receive. Also, chmod +x
post-receive.

-->
