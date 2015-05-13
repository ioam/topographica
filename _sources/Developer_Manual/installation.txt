********************************************
Installing Topographica with version control
********************************************

Version control allows you to keep up to date with the latest changes
made by other developers, and allows you to keep track of your own
changes. Topographica's source code is held in a central Git
repository on GitHub.com; the repository contains the files making up
Topographica itself (including its documentation).  Please see the
`Topographica github`_ homepage for instructions for installing via
Git.  Once installed, you can check that Topographica is working as
expected by running ``nosetests`` within the topographica directory,
for the simple and fast unit tests, or ``make slow-tests``, for the
more comprehensive but slower tests.  If you do the tests on a machine
without a functioning DISPLAY, such as a remote text-only session,
there will be some warnings about GUI tests being skipped.  You can
also check the test output from the latest automatic builds at our
`bautomatic tests page`_, to see if the latest version is working well
on a specific platform.

Please bear in mind that most of Topographica's development occurs
under Linux, so if you have a choice, Linux (e.g. via a virtual
machine) is the best-supported option.  On the other hand, we welcome
contributions from Mac and Windows developers, who can help detect and
solve platform-specific issues.

.. _SourceForge: http://sourceforge.net/projects/topographica
.. _Topographica github: https://github.com/ioam/topographica
.. _nightly documentation build: http://buildbot.topographica.org/doc/Developer_Manual/installation.html
.. _automatic tests page: http://buildbot.topographica.org/
