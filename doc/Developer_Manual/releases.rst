***************
Making Releases
***************

The latest version of Topographica is always available by Git, but we
also make more stable versions available periodically. To make such a
release, the steps we have followed in the past are listed below.
However, please note that as of version 0.9.8 several steps in these
instructions are out of date, and will need to be updated as part of
the next release.

#. Ensure that no one besides yourself has any modified files
   checked out in Git; if they do, make sure all of it gets checked
   in or does not need to be included in the release, and ensure
   that none of it will be checked in until the release is complete.
#. Increment the RELEASE number in ./Makefile, and do "make
   new-version".
#. Update the documentation files, especially README.txt,
   doc/News/index\_text.php, doc/Home/news\_text.php and
   doc/Downloads/index\_text.php (check the download links will be
   correct). The rest should be read through, making sure that the
   auto-generated pages are working properly, that the citations in
   the User Manual work, and that pages written by hand match the
   current version of the code. In particular,
   doc/Reference\_Manual/index\_text.php needs to match the current
   version of the reference manual (don't forget to
   ``make -C doc reference-manual`` and check the dot graphs).
#. Update the tutorials to match changes to the GUI, if necessary. A
   simple way to get updated versions of each image is to:

   #. Change to the doc/Tutorials/images/ directory
   #. Launch ``xv`` on all of the images (``xv * &``)
   #. Select the image you want to update, using xv's right-click
      menu
   #. Select Grab from xv's right-click menu
   #. Select Save from xv's right-click menu

   The advantage of this method is that you never need to type in
   filenames, make sure they match the .html or .php file, and so
   on.

   Be sure to work through the tutorial once it is updated, to make
   sure all of the instructions still make sense for the new
   release.

#. Update Changelog.txt (by making a copy of ChangeLog.txt, doing
   "make Changelog.txt", and pasting the new items at the top of the
   copy (so that any fixes to the old items are preserved). Also
   summarize major changes in it for the release notes in News/.
#. Update the issues trackers and the remaining work lists in
   Future\_Work/index\_text.php and Future\_Work/current\_text.php
   to reflect completed tasks and changes in priority.
#. Check any modified files into Git.
#. Are all the buildbot tests still passing? You might need to
   trigger new builds to check all platforms are ok.
#. Save all open files from within any editor, and do a "make -f
   -f platform/Makefile dist" to create a candidate distribution archive. (To
   ensure that all files are saved in Emacs, you can do "M-x compile
   RET make -f platform/Makefile dist".) Note that this step is best done on a
   local disk rather than on a network drive. (Additionally, using a
   scratch copy of Topographica on which you have run 'make -C
   external clean' will speed things up, but this is not necessary.)
#. Unpack the distribution archive and examine it:

   #. Use "ls -lFRA" or "find ." to ensure that no stray files were
      included; if they were, edit "distclean:" in ./platform/Makefile to
      delete them from the generated distribution.
   #. Double-check the generated documentation to ensure that it is
      complete and was generated properly.
   #. Try out the source on various platforms, ensuring that there
      are no errors. Also perform a self-test on the various
      platforms ("./topographica -t quick -t exhaustive").

#. If you find problems, go back to step 6 and start over.
#. Now generate the tar.gz
   (``make -f platform/Makefile dist-pysource dist-pysource-sdist``) and check its
   contents in the same way as above.
#. At this point, it is a good idea to test the packages. Buildbot
   does not yet check that the packages it generates work on all
   platforms. You should use clean virtual machines to test the
   process of installing and using the packages it has generated.
#. When the package is ready for release, make a commit stating the
   version number (e.g. 'git commit -m "Version 0.9.8"'). Notify the
   other developers that they may once again commit new code to the
   Git repository.
#. Create tar.gz and upload them to pypi:
   ``make -f platform/Makefile dist-pysource-sdist; make -f platform/Makefile dist-pypi-upload``.
#. check the public web site (should be updated automatically
anyway). 
#. Send an announcement to topographica-announce at lists.sf.net.

