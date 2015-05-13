***************
Making Releases
***************

The latest version of an IOAM project is always available by Git, but
we also make more stable versions available periodically. To make such
a release, the steps we have followed in the past are listed below.
Here <package> should be replaced with the GitHub project name of the
package being released, e.g. param or imagen.

#. Ensure that no one besides yourself has any modified files
   checked out in Git; if they do, make sure all of it gets checked
   in or does not need to be included in the release, and ensure
   that none of it will be checked in until the release is complete.
#. Increment the release number in ``<project>.__init__.__version__``,
   setup.py, and the release notes in doc/index.rst. Note that 
   some ioam projects (e.g. param) contain more than one package 
   (param and numbergen in param's case).
#. Update the documentation files, especially README.rst,
   doc/News/index\_text.rst, doc/Home/news\_text.rst and
   doc/Downloads/index\_text.rst (check the download links will be
   correct). The rest should be read through, making sure that the
   auto-generated pages are working properly, that the citations in
   the User Manual work, and that pages written by hand match the
   current version of the code. In particular,
   doc/Reference\_Manual/index\_text.rst needs to match the current
   version of the reference manual, and remember to check the
   inheritance graphs.
#. Update the tutorials to match changes to the GUI or graphing
   support, if necessary. For the old non-notebook tutorials, a
   simple way to get updated versions of each image is to:

   #. Change to the doc/Tutorials/images/ directory
   #. Launch ``xv`` on all of the images (``xv * &``)
   #. Select the image you want to update, using xv's right-click
      menu
   #. Select Grab from xv's right-click menu
   #. Select Save from xv's right-click menu

   The advantage of this method is that you never need to type in
   filenames, make sure they match the .html or .rst file, and so
   on.

   Be sure to work through the tutorial once it is updated, to make
   sure all of the instructions still make sense for the new
   release.  The newer notebook tutorials should be tested
   automatically, but be sure to check buildbot to make sure.

#. Update Changelog.txt, if any, by making a copy of ChangeLog.txt, doing
   "make Changelog.txt", and pasting the new items at the top of the
   copy (so that any fixes to the old items are preserved). Also
   summarize major changes in it for the release notes in News/.
   (if present) or in README.rst.
#. Update the issues trackers and the remaining work lists in
   Future\_Work/index\_text.rst and Future\_Work/current\_text.rst
   (if present) to reflect completed tasks and changes in priority.
#. Check any modified files into Git.
#. Are all the buildbot and other continuous tests still passing? You
   might need to trigger new builds to check all platforms are ok.
#. Save all open files from within any editor, and sure that they 
   have all been committed to git and pushed to github.
#. Tag the repository::

     git tag -a v1.2.1 -m 'Release version 1.2.1'

   If you have to repeat this step, the next time you
   will need ``-f -a``, not just ``-a``.
#. In python, do ``import <project> ; project.__version__.verify()`` to test
   that the version information has been declared properly.
#. Push your tag to github::

     git push origin v1.2.1

   Note that if you are repeating the tagging, you may need to push 
   using ``git push -f origin v1.2.1``.
#. Test creating a distribution and inspect the results:

   #. ``python setup.py sdist``
   #. ``cd dist; tar xvf <package>``
   #. Use ``ls -lFRA`` or ``find .`` to ensure that no stray files were
      included and nothing is missing.
   #. Double-check the generated documentation to ensure that it is
      complete and was generated properly.
   #. Try out the source on various platforms, e.g. using virtual
      machines, ensuring that there are no errors. Also perform a
      self-test on the various platforms (``nosetests`` or
      ``./topographica -t quick -t exhaustive``).
#. Make a PyPI release by running::

     python setup.py register sdist upload
   
#. Download the new package from https://pypi.python.org/pypi?name=<package>,
   again testing the issues listed in the previous step, but now
   installing via virtualenv using ``pip install``, ``pip install
   --upgrade``, etc.
#. If you find problems, go back to step 7 and start over.
#. Publish Windows exe files on PyPi (from a Windows machine with git
   installed):: 
   
      python setup.py bdist_wininst --plat-name=win32 --user-access-control=auto upload
      python setup.py bdist_wininst --plat-name=win-amd64 --user-access-control=auto upload
   
#. Check that the exe runs and installs correctly on Windows.
#. When the package is ready, notify the other developers that they
   may once again push new code to the Git repository.
#. Force build for the public web site for this project, and check
   the results (should eventually be updated automatically anyway). 
#. Send an announcement to topographica-announce at lists.sf.net and
   neuroinfo@incf.org, if appropriate.
