****************
Developer Manual
****************



This manual gives guidelines for developers working on the source
code for the Topographica simulator. Users will not usually need to
refer to this material, unless they plan to submit significant
blocks of code to the project (which is, of course, strongly
`encouraged`_!).

By default, all the text in this manual refers to program code
written in the Python language. There are also some bits of C/C++
code in the simulator, which use different conventions.

Note that Topographica's documentation may change between releases,
so developers should usually be reading either their locally built
copy of the documentation, or the online `nightly documentation
build`_. The documentation at topographica.org applies to the
previous release, so may be out of date with respect to the current
version of Topographica in Git.

`Installation instructions`_
    Before starting, you will need a version-controlled copy of
    Topographica.
`Revision control`_
    How we keep track of changes to the code and other files
`General guidelines`_
    General info on writing Python, plus Topographica-specific
    conventions such as guidelines for naming, comments,
    documentation, parameters, units, and external imports.
`Object-oriented design`_
    How to design well-structured code
`Importing files and packages`_
    How to import Topographica and external code
`ALERTs`_
    How to flag incorrect or confusing code or documentation
`GUI programming`_
    How to add functionality to the GUI
`Performance optimization`_
    When (and when not!) to optimize for performance, and how to do
    it
`Memory usage`_
    How to measure memory usage and reduce it
`Refactoring/testing tips`_
    Tips for improving existing code by refactoring
`Test suite`_
    Rationale behind unit tests; should eventually include
    information about how to set up tests
`Releases`_
    How to make a new public release of Topographica

Joining
-------
Anyone interested in Topographica is welcome to join as a
Topographica developer to get read/write access, so that your
changes can become part of the main distribution. Just sign up
for a free account at `GitHub.com`_, then email `Jim`_ your
username and what you want to do, and he'll tell you how to
proceed from there. Alternatively, you can start immediately by
cloning Topographica, developing your feature, and `submitting
it as a public pull request`_ only once it's done.

.. _encouraged: #joining
.. _nightly documentation build: http://buildbot.topographica.org/doc/Developer_Manual/index.html
.. _Installation instructions: installation.html
.. _Revision control: revisioncontrol.html
.. _General guidelines: coding.html
.. _Object-oriented design: ood.html
.. _Importing files and packages: imports.html
.. _ALERTs: alerts.html
.. _GUI programming: gui.html
.. _Performance optimization: optimization.html
.. _Memory usage: memuse.html
.. _Refactoring/testing tips: refactoring.html
.. _Test suite: testing.html
.. _Releases: releases.html
.. _GitHub.com: http://github.com/
.. _Jim: mailto:jbednar@inf.ed.ac.uk?subject=Request%20to%20be%20a%20Topographica%20developer
.. _submitting it as a public pull request: git.html#pullrequest
