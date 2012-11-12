<H1>Revision control</H1>

<P>Topographica source code and development is managed using
<a target="_top" href="https://git-scm.com">Git</a> hosting services provided by
<a target="_top" href="https://github.com/ioam/topographica">GitHub</a>.  Git is a
distributed version control system, providing support for a wide range
of ways of interacting with other developers.  In particular, it
allows you to keep track of your own changes locally, without
involving the "official" Topographica developers, if you want to have
changes specific to your own needs.

<P>If you're working on changes intended to end up in the public
repository, it is essential that you follow the guidelines below.

<P>Every Git commit <em>must</em> include an informative log message,
summarizing the reason for the changes in easily understandable terms,
and avoiding pejorative language (i.e., no comments like "Lord only
knows what idiot coded it that way!"). If your change fixes a bug or
addresses some other known issue, include text in the commit log
message specifically mentioning the issue number that is being
addressed (e.g. "Fixes #17" or "Closes #17"); that way GitHub will
automatically close the associated issue and link back to the change
that closed it.

<P>When describing the changes, it is crucial to examine
every single line produced by <CODE>git diff</CODE> to verify that
only intentional changes (and not stray characters or temporary
changes) are checked in, and that the log message covers all the
important changes.  You should also do <CODE>git status</CODE> to make
sure that you don't have any important files not yet checked into Git,
as <CODE>git diff</CODE> will not report these.

<P>If so many items were changed that any single log message would
have to be very general (e.g. "Misc changes to many files"), then take
a step back and try to find smaller groups of files that can be
checked in, each with a meaningful log message.  Git commits are
initially stored locally, and can be deleted later, which should
encourage you to commit whenever things come together into something
coherent -- there's almost no cost to doing a commit, and it provides
a record of your work and a checkpoint to fall back on if problems
occur later.  Using smaller, meaningful chunks also makes debugging
much easier later, allowing the source of a new bug to be tracked down
to a small, understandable set of related changes.  Conversely, if the
same trivial changes were made to a large group of files, please check
in all of those at once, with the same log message, so that it will be
clear that they go together.

<P>Ideally, each commit should reflect a single purpose (e.g. addition
of a new feature or a bug fix).  When committing files, please do it
in the appropriate order and grouping so that the code works at every
time in the Git repository history, if at all possible.  That is, if
you change several files, adding a function to one file and then
calling it in another, consider if you should check in the file with
the new function first, or if you should check in the two files
together. In this situation you should certainly <EM>not</EM> check in
the file that calls the function before checking in the file
containing the function. In this opposite order, the repository would
temporarily be in a state where it could not supply working code.
Such gaps cause needless errors with our automated tests, and make it
much more difficult to debug problems using the Git revision history,
because they make it impractical to roll back history one change at a
time to try to find the source of a bug.

<P>When making and checking in particularly extensive changes, please
keep refactoring completely separate from new features whenever
possible.  That is, if you have to change or clean up a lot of old
code in order to add a new feature, follow something like this
procedure:

<PRE>
  git commit -a	  # Commit all outstanding edits
  make tests	  # Verify that things work when you start
  emacs		  # Refactor old code, not changing behavior at all
  make tests      # Verify that nothing has been broken
  git diff        # Will have many widespread changes
  git commit -a -m "No visible changes"
  emacs		  # Add new feature and new test for it
  make tests      # See if tests still work, fixing if necessary
  git diff	  # Short list: only the new code
  git commit -a -m "Added feature Y"
</PRE>
  
That way nearly all of the lines and files you changed can be tested
thoroughly using the existing test suite as-is, and any tests added
can be tested equally well on both the old and new code.  Then the few
lines implementing the new feature can be added and debugged on their
own, so that it will be very simple to see whether the new feature was
the source of a bug, or whether it was all those other changes that
<i>shouldn't</i> have changed anything.


<!-- Need to update this for git; disabled until then 

<H2>Revision info</H2>

<P>Finally, when making a change that will cause a new file to be
produced on other users' systems (e.g. adding an external package that
will be unpacked and built), it is important to tell Git that it
should ignore such generated files. For instance, if you add the
external package <code>my_package-1.0.tar.gz</code>, when it is built
it will probably generate <code>external/my_package-1.0/</code> and
<code>external/my-package</code>. When you (or another user) subsequently
types <code>git status</code>, git will output something like:
<pre>
?  external/my_package
?  external/my_package-1.0
</pre>

To prevent this, you need to edit the <code>git:ignore</code> property
on the <code>external/</code> directory by doing something like this:

<pre>
git propget git:ignore external/ > tmp
emacs tmp   # edit tmp to include the entries above
git propset git:ignore external/ -F tmp
rm tmp
</pre>

<P>Similarly, when removing a file, please update any relevant
<code>git:ignore</code> property so that unused files become apparent
to all users.
-->

<H2>Other Notes</H2>

<P>Mac users: when adding a directory, please be sure not to add
all the temporary files that OS X creates (i.e. ones beginning <code>.DS_</code>
and <code>._</code>). To delete all those files recursively, you can use
commands like the following:
<pre>
find . -name "._*" -exec rm -f {} ;
find . -name ".DS_*" -exec rm -f {} ;
</pre>

<P>Other users should similarly make sure not to add any temporary
editor files or other irrelevant items; the repository needs to be
kept clean so that we can focus on the files that matter.

<H2>Suggested Git Workflows</H2>

The information above is primarily policies that apply to official
Topographica developers.  We also have <a target="_top" href="git.html">specific
suggestions</a> for useful workflows using Git, but these are just
suggestions rather than policies such as the above.
