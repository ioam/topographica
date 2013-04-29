*********************************
Developing Topographica Using Git
*********************************

It is often useful to work on separate copies of the code, e.g. to
develop a new, complicated feature, or to make far-reaching changes
that need extensive testing. Git makes this easy, by allowing you to
establish a local branch of Topographica, so that you can have the
benefits of version control (keeping track of different revisions)
without necessarily affecting the global repository. If it does turn
out that the local changes would be useful to other Topographica
users, they can then be "pushed" onto the global repository for
everyone to use once they are completed.

Git's branches work locally (without internet access), and are very
fast, which makes them usable for even small and frequent changes.

Working with your Git repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have the Topographica source code in your own Git
repository (as described on the `downloads`_ page), you are free to
work on it as you wish. You can commit files, add files, delete
files, and so on. All operations that you perform with ``git`` (such
as ``diff`` and ``commit``) are local; only operations with
``git push`` have the potential to modify the Git repository, and
those work only if you have commit rights to the public repository.
If you are new to Git, `Git's documentation page`_ has various
tutorials for people with different backgrounds (including those
coming from Subversion).

Note that before committing to your repository for the first time,
you should identify yourself to git:

::

    $ git config --global user.email user@address.ext
    $ git config --global user.name "User Name"

You should also check that your machine has the correct time and
date, otherwise your history can become confusing.

Repository backup and sharing work in progress
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With git, you are usually working locally. This means your work is
(a) not backed up and (b) not visible to others. Not backing up your
work is risky, and if others are not aware of your work, unnecessary
duplication or conflict could occur. You can solve (a) alone by
making a copy of your repository elsewhere, but you can solve (a)
and (b) by obtaining a git repository of your own on github. To do
so, please visit github.com. You can then clone the Topographica
repository using the instructions on the `Topographica page at
GitHub`_. You can then push your local repository to the remote one
as often as you want by doing e.g.

::

    $ git push

.. _pullrequest:

Pull requests
~~~~~~~~~~~~~

If you don't have push rights, or want to ensure that your code is
reviewed first, you are encouraged to submit a "pull request" at
GitHub. Pull requests package up your changes into an easy-to review
and discuss format, allowing the core Topographica developers to
evaluate the changes before approving them.

Creating a pull request can be done with something like the
following workflow:

#. Clone the repository you wish to be pushing to.
#. Make the required changes in your clone, and commit to your own
   repository.
#. Navigate to *your cloned repository's* github page.
#. Click on the "Pull Request" button near the top (note -- this is
   different from the list of existing pull requests labeled "Pull
   Requests")
#. You should be taken to a configuration page, where you can select
   the appropriate head and local repositories and branches, add
   comments to describe your submission, etc.
#. Every time you commit to the local branch that you have
   submitted, the corresponding pull request will also be updated.

Interacting with Topographica's Git repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To interact with our Git repository, there are several possible
workflows you could adopt. However, we strongly recommend the
following workflow:

#. To start work on some new feature, create a new branch called
   ``feature`` from ``master`` (the main public branch):
   ``git checkout -b feature``
#. Make your changes, commit them, and test them (probably multiple
   iterations, potentially over a long period).
#. *(Optional)* If you have made a lot of commits and they do not
   form a coherent story, collapse them using git's `rebase`_. The
   safest way to do this is to first create a new branch of
   ``feature`` (``git checkout -b feature_clean``); this way, what
   you actually did is preserved in the ``feature`` branch. In the
   new branch, run ``git rebase --interactive HEAD~i``, where ``i``
   is the number of commits back from the current position that you
   want to sort out. This will open an editor (as specified by the
   ``GIT_EDITOR`` environment variable) where you can rearrange,
   squash, or remove individual commits. The end result should be a
   single commit with a log message describing the new feature.
#. Update your branch to get changes made by others while you were
   working on your feature: ``git checkout master; git pull``.
#. Rebase your changes onto the public repository. First, change to
   the feature branch: ``git checkout feature`` (or
   ``git checkout feature_clean`` if you followed step 3). Then,
   perform the rebase (moving your "feature" commits to appear after
   the latest Git changes): ``git rebase master``. Your changes need
   to appear at the tip in this way (i.e. they need to be 'fast
   forwarded'), since that is the point at which they will actually
   be committed to the master.
#. Test your changes and commit fixes if necessary. Other people
   might have introduced incompatibilities with your code into Git
   while you were working on step 2, so it is important to check
   your changes are still valid (and not just that they merge
   without conflict). If you followed optional step 3, you probably
   now want to run ``git rebase --interactive HEAD~j`` again to
   incorporate any new commits into the one you created earlier.
#. Merge your feature branch back into the main branch, then commit
   to Git: ``git checkout master; git merge feature`` (or
   ``feature_clean`` if you followed step 3), then
   ``git commit -a``. If you first want to see what will happen when
   you commit to Git, you can do a dry run by passing ``-n`` to
   ``commit``. Note that before sending your changes to Git, you
   should ensure that you have followed the `general revision
   control guidelines`_.
#. Now that your feature is complete and in Git, you can branch
   ``master`` again to start on the next feature!

Branching in Git is fast, so if you are ever unsure what effect an
operation will have on the ``master`` or ``feature`` branches,
create new branches from them and test out the command using the
copies.

.. _downloads: ../Downloads/index.html#install-via-git
.. _Git's documentation page: http://git-scm.com/documentation
.. _Topographica page at GitHub: https://github.com/ioam/topographica
.. _rebase: http://book.git-scm.com/4_rebasing.html
.. _general revision control guidelines: revisioncontrol.html
