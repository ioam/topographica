<H1>Making Releases</H1>

<P>The latest version of Topographica is always available by Git, but
we also make more stable versions available periodically.  To make
such a release, the steps we generally follow are:

<ol>
<li><P>Ensure that no one besides yourself has any modified files checked
  out in Git; if they do, make sure all of it gets checked in or
  does not need to be included in the release, and ensure that none
  of it will be checked in until the release is complete.

<li><P>Increment the RELEASE number in ./Makefile, and do "make
new-version".
   
<li><P>Update the documentation files, especially README.txt,
  doc/News/index_text.php, doc/Home/news_text.php and
  doc/Downloads/index_text.php (check the download links will be
  correct).  The rest should be read through, making sure that the
  auto-generated pages are working properly, that the citations in the
  User Manual work, and that pages written by
  hand match the current version of the code.  In particular,
  doc/Reference_Manual/index_text.php needs to match the current
  version of the reference manual (don't forget to <code>make
  reference-manual</code> and check the dot graphs).

<li><P>Update the tutorials to match changes to the GUI, if necessary.
  A simple way to get updated versions of each image is to:

  <ol>
  <li>Change to the doc/Tutorials/images/ directory
  <li>Launch <code>xv</code> on all of the images (<code>xv * &</code>)
  <li>Select the image you want to update, using xv's right-click menu
  <li>Select Grab from xv's right-click menu
  <li>Select Save from xv's right-click menu
  </ol>

  <P>The advantage of this method is that you never need to type in
  filenames, make sure they match the .html or .php file, and so on.

  <P>Be sure to work through the tutorial once it is updated, to make
  sure all of the instructions still make sense for the new release.
  
<li><P>Update Changelog.txt (by making a copy of ChangeLog.txt, doing
  "make Changelog.txt", and pasting the new items at the top of the
  copy (so that any fixes to the old items are preserved).  Also
  summarize major changes in it for the release notes in News/.

<li><P>Update the issues trackers and the remaining work lists in
  Future_Work/index_text.php and Future_Work/current_text.php to
  reflect completed tasks and changes in priority.

<li><P>Check any modified files into Git.

<li><P>Are all the buildbot tests still passing? You might need to
 trigger new builds to check all platforms are ok. 

<li><P>Save all open files from within any editor, and do a "make dist"
  to create a candidate distribution archive.  (To ensure that
  all files are saved in Emacs, you can do "M-x compile RET make
  dist".) Note that this step is best done on a local disk rather 
  than on a network drive. (Additionally, using a scratch copy of 
  Topographica on which you have run 'make -C external clean' will
  speed things up, but this is not necessary.)
  
<li><P>Unpack the distribution archive and examine it:
    <ol>
    <li><P>Use "ls -lFRA" or "find ." to ensure that no stray files were
      included; if they were, edit "distclean:" in ./Makefile to
      delete them from the generated distribution.
   
    <li><P>Double-check the generated documentation to ensure that it is
      complete and was generated properly.
      
<!--CEBALERT: need to make slow-tests' list of scripts only
include those present in release-->


    <li><P>Try out the source on various platforms, ensuring that
      there are no errors.  Also perform a self-test on the various
      platforms ("make tests; make slow-tests").
<!-- now done by buildbot, so probably no need to try on all platforms at this point -->
    </ol>
    
<li><P>If you find problems, go back to step 6 and start over.

<li><P>Now generate the tar.gz (<code>make dist-pysource
dist-pysource-sdist</code>) and check its contents in the same way as 
above.

<li><P>At this point, it is a good idea to test the packages. Buildbot
does not yet check that the packages it generates work on all
platforms. You should use clean virtual machines to test the process
of installing and using the packages it has generated.

<li><P>When the package is ready for release, make a commit stating
the version number (e.g. <kbd>git commit -m "Version 0.9.8"</kbd> and
tag this release <kbd>git tag -a v0.9.8 -m "Version 0.9.8 release
candidate"</kbd> Notify the other developers that they may once again
commit new code to the Git repository.

<li><P>Create tar.gz and upload them to pypi (requires ioam pypi account
    password, under Jim's email address):
<pre>
make dist-pysource
make dist-pysource-sdist
python setup.py register
python setup.py sdist upload 
</pre>

<!--upload requires account on opensuse build service-->
<!--    
<li><P>Create rpm: <code>make dist-rpm</code>; upload spec file and
tar.gz manually to opensuse build service.
-->

<!--CEBALERT: currently only as ceball@fiver.inf-->
<!--    
<li><P>Create .deb and upload to launchpad: <code>make DEBSTATUS= deb
deb-backports deb-ppa</code>

<li><P>Create mpkg and upload to GitHub using their admin
interface: <code>make dist-setup.py-bdist_mpkg</code>. (This step must
be done on a Mac.)
-->

<li><P>update the public web site. Change to the copy of Topographica
    you created for distribution so that no stray files from doc/ are
    included and do "make sf-web-site".

<li><P>Send an announcement to topographica-announce at lists.sf.net.
</ol>

