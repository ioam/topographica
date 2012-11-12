<!-- Updated from svn-based instructions by JAB; probably has some inconsistencies -->

<H2>Developing Topographica Using Git</H2>

<P>It is often useful to work on separate copies of the code, e.g. to
develop a new, complicated feature, or to make far-reaching changes
that need extensive testing.  Git makes this easy, by allowing you to
establish a local branch of Topographica, so that you can have the
benefits of version control (keeping track of different revisions)
without necessarily affecting the global repository.  If it does turn
out that the local changes would be useful to other Topographica
users, they can then be "pushed" onto the global repository for
everyone to use once they are completed. 

<P>Git's branches work locally (without internet access), and are very
fast, which makes them usable for even small and frequent changes.

<H3>Working with your Git repository</H3>

<P>Once you have the Topographica source code in your own Git
repository (as described on
the <A HREF="../Downloads/git.html">downloads</A> page), you are free
to work on it as you wish. You can commit files, add files, delete
files, and so on. All operations that you perform
with <code>git</code> (such as <code>diff</code> and
<code>commit</code>) are local; only operations with <code>git
push</code> have the potential to modify the Git repository, and those
work only if you have commit rights to the public repository. If you are
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
obtaining a git repository of your own on github. To do so, please
visit github.com. You can then clone the Topographica repository
using the instructions on the 
<a target="_top" href="https://github.com/ioam/topographica">Topographica page at GitHub</a>.  

You can then push your local repository to the remote one as often as
you want by doing e.g. 
<pre>
$ git push
</pre>


<H3><a name="pullrequest">Pull requests</a></H3>

<P>If you don't have push rights, or want to ensure that your code is
reviewed first, you are encouraged to submit a "pull request" at
GitHub.  Pull requests package up your changes into an easy-to review
and discuss format, allowing the core Topographica developers to
evaluate the changes before approving them.

<P>Creating a pull request can be done with something like the
following workflow:

<ol>
<li>Clone the repository you wish to be pushing to.
<li>Make the required changes in your clone, and commit to your own
  repository.
<li>Navigate to <em>your cloned repository's</em> github page.
<li>Click on the "Pull Request" button near the top (note -- this is
  different from the list of existing pull requests labeled "Pull
  Requests")
<li>You should be taken to a configuration page, where you can select
  the appropriate head and local repositories and branches, add
  comments to describe your submission, etc.
<li>Every time you commit to the local branch that you have submitted,
  the corresponding pull request will also be updated.
</ol>
  

<H3>Interacting with Topographica's Git repository</H3>

<P>To interact with our Git repository, there are several possible
workflows you could adopt. However, we strongly recommend the
following workflow:

<ol>

<li>To start work on some new feature, create a new branch called
<code>feature</code> from <code>master</code> (the main public
branch): <code>git checkout -b feature</code></li>

<li>Make your changes, commit them, and test them (probably multiple
iterations, potentially over a long period).</li>

<li><i>(Optional)</i> If you have made a lot of commits and they do
not form a coherent story, collapse them using git's
<a target="_top" href="http://book.git-scm.com/4_rebasing.html">rebase</a>. The safest
way to do this is to first create a new branch of <code>feature</code>
(<code>git checkout -b feature_clean</code>); this way, what you
actually did is preserved in the <code>feature</code> branch. In the
new branch, run <code>git rebase --interactive HEAD~i</code>, where
<code>i</code> is the number of commits back from the current position
that you want to sort out. This will open an editor (as specified by
the <code>GIT_EDITOR</code> environment variable) where you can
rearrange, squash, or remove individual commits. The end result should
be a single commit with a log message describing the new feature.

<li>Update your branch to get changes made by others while you
were working on your feature: <code>git checkout master; git
pull</code>.</li> 

<li>Rebase your changes onto the public repository. First, change
to the feature branch: <code>git checkout feature</code> (or <code>git
checkout feature_clean</code> if you followed step 3). Then, perform
the rebase (moving your "feature" commits to appear after the latest
Git changes): <code>git rebase master</code>. Your changes need to
appear at the tip in this way (i.e. they need to be 'fast forwarded'),
since that is the point at which they will actually be committed to
the master.</li>

<li>Test your changes and commit fixes if necessary. Other people
might have introduced incompatibilities with your code into Git while
you were working on step 2, so it is important to check your changes
are still valid (and not just that they merge without conflict). If
you followed optional step 3, you probably now want to run <code>git
rebase --interactive HEAD~j</code> again to incorporate any new
commits into the one you created earlier.</li>

<li>Merge your feature branch back into the main branch, then commit
to Git: <code>git checkout master; git merge feature</code> (or
<code>feature_clean</code> if you followed step 3), then <code>git
commit -a</code>. If you first want to see what will happen when you
commit to Git, you can do a dry run by passing <code>-n</code> to
<code>commit</code>. Note that before sending your changes to Git,
you should ensure that you have followed
the <A HREF="revisioncontrol.html">general revision control
guidelines</A>.</li>

<li>Now that your feature is complete and in Git,
you can branch <code>master</code> again to start on the next
feature!</li>

</ol>

<P>Branching in Git is fast, so if you are ever unsure what effect an
operation will have on the <code>master</code> or <code>feature</code>
branches, create new branches from them and test out the command using
the copies.
