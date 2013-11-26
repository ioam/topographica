TOPOGRAPHICA TESTS
==================

This directory contains the test suite for Topographica. The tests are categorised as follows:

- unit tests in package ``tests.unit``. See the README in that package.
- functional tests (a.k.a. "slow", "system" or "all" tests) run a variety of scripts and simulations
- speed tests -- which are by no means fast -- deal with simulation timings

Here is a basic explanation of what the individual types of functional tests (referred to as "targets") do:

- the ``training`` tests run a number of scripts through a simulation and compare their output against previous results stored in data files.
  They fail if the results differ beyond the accuracy margin; the required decimal point precision is passed on to the test before running.
  The current list of trainscripts is the following:
  
  - examples/hierarchical.ty
  - models/lissom_or.ty
  - models/lissom_oo_or.ty
  - examples/som_retinotopy.ty
  - models/sullivan_neurocomputing04.ty
  - models/lissom.ty
  - examples/gcal.ty
  
  The data files which store previous results are named ``scriptname._DATA`` and are located in the ``data_traintests`` directory. It is not
  absolutely required to have them in the repository; if they are not found, the test scripts will generate new data files. However,
  having them readily available is more convenient since generating new files takes a long time.

- ``unopt`` do the same as ``training`` but without using the `Weave package <http://www.scipy.org/Weave>`_ for optimisation.
  
- ``speedtests`` and ``startupspeedtests`` compare the time it takes to run certain test scripts against previously stored results. Since runtime
  is machine-dependent, timing results are not checked in with the repository but rather generated the first time speedtests are run on a given
  machine. The data files are named ``scriptname._SPEEDDATA`` and ``scriptname._STARTUPSPEEDDATA``, and are stored in
  ``~/Topographica/tests/hostname/``, wherever HOME is on the respective machine.
  
  Speed tests use (almost) the same script list as training tests; see comments in ``runtests.py`` as to why certain scripts are excluded.
  Startupspeedtests use ``models/lissom.ty`` and ``examples/gcal.ty``.
  
  Unless there is some error, these tests will always "pass"; they do not perform any assertions but rather simply report current timings and compare
  them against previous results. To make this set of tests truly useful, they should probably be included in performance tracking and plotting
  in buildbot once that is restored.

- ``maps`` check the results from map measurements obtained by running a simulation with the ``models/lissom_oo_or.ty`` script, and compare
  the results against previous data stored in the data_maptests directory.

- ``snapshots`` and ``pickle`` which deal with saving and restoring legacy code to and from bytecode, using ``instances-r11275.pickle``

- ``gui tests`` perform more elaborate tests on the GUI in addition to the GUI unit tests

- the more "lightweight" targets ``scriptrepr`` and ``batch``; I'm not quite sure what these do.

For detailed explanation of what any of these test targets does, consult someone competent in how Topographica works.

DIRECTORY STRUCTURE
-------------------

- As mentioned above, ``topo/tests/data_maptests`` and ``topo/tests/data_traintests`` contain control data for maps and training tests, respectively.
  Speed data is written in ``~/Topographica/tests/hostname/`` since it varies for each machine and should not be checked in. If desired, training
  and maps test data can also be written in ``~``.

- ``topo/tests/data_disabled`` contains various data files which have been excluded from the tests for one reason or another. Carefully inspect
  comments in the test scripts to see what happened exactly; usually such omissions have an accompanying ALERT with them.

- the ``reference`` directory contains "c++ lissom comparisons". I have no idea what this means.

- ``runtests.py`` is the "crude Makefile replacement" which contains a list of commands and runner code to choose which set of commands to run. Start
  here when trying to find out how each command works.

- ``test_script.py`` is a mammoth script containing a huge number of methods for running training, speedtests, and snapshottests. This should be
  broken down and separated into different scripts by someone who knows how Topographica and the tests work, i.e. has a vision as to how to best
  optimise and improve the tests.

- ``gui_tests.py`` and ``functionaltest.py`` deal with the GUI tests. ``functionaltest`` is only used with the GUI tests so the module should
  probably be removed and its methods moved to ``gui_tests``.

- ``test_map_measurement.py`` contains the scripts for the map tests

- ``utils.py`` contains several convenience methods used throughout the functional and the unit tests.

RUNNING
-------

To run any of the above targets, use ``./topographica -p "targets=['targets']" topo/tests/runtests.py`` where 'targets' would mean any subset of
the tests, e.g. ``"targets=['training']"`` or ``"targets=['training,'unopt,'snapshots']"``. ``"targets=['all']"`` is a shortcut for
running the entire set of functional tests except speedtests. ``"targets=['speed']"`` is a convenience shortcut for ``speedtests`` and
``startupspeedtests``.

Each target basically runs a set of commands, e.g. ``training`` would run a series of commands such as
``./topographica -c "from topo.tests.test_script import test_script; test_script(script='scriptpath',decimal=6)"``

NB: on Linux, single and double quotes mean the same but on Windows, always use double quotes on the outside since single quotes are not treated
as string delimiters. Thus, running ``'targets=["all"]'`` on Windows will only read ``'targets`` and ``runtests`` will treat it as if no targets were
specified. It will then run the default set (see ``runtests``) instead of ``all`` tests.

To troubleshoot an error with any particular test, the following would be a good checklist:

1. Know what each target does; run each of them separately to become familiar with their output. Buildbot logs contain the output from "all" tests
   so they're often difficult to navigate; also, output is sometimes mixed up.

2. Look at the ``runtests.py`` runner to see how the commands run by these targets are generated.

3. The test runner will report how many (and which) targets had errors; use these to track down the failed target.

4. Finding out what exact command was run can be tricky; these are usually obtained by combining a number of strings and arguments so, if necessary,
   search the buildbot logs to find what exactly should be run.

5. Once the specific error has been reproduced, go on from there.


PROBLEMS AND FURTHER WORK
-------------------------

Currently, the functional tests are very mixed up and difficult to understand. The following are specific issues that need to be addressed:

1. Understand what the tests do.

2. Separate the methods in ``test_script`` into different Python scripts for improved work efficiency, and document them (including code comments).

3. Dispose of the ``runtests`` runner whatsoever by moving the stuff in it to the respective test scripts. Currently, it **appears** necessary;
   it contains code for handling optional parameters (e.g. whether to use xvfb or timing) which would otherwise need to be copied many times -- but
   it would be better to handle these parameters in whatever is running the tests, e.g. buildbot.
   
   E.g. instead of having code in ``runtests`` which puts ``/usr/bin/xvfb-run -a`` in front of
   ``./topographica -p timing=True -p 'targets=["speed"]' topo/tests/runtests.py``, this can be done by buildbot or whoever wants to use xvfb
   with the tests. Timing is not used anywhere in buildbot, and can be explicitly included if someone wants to use it, while Precision values are
   hardcoded anyway. Writing custom code to automate all possible contingencies often overcomplicates things, and this is a chronic issue here.
   
4. If the above discussion of eliminating ``runtests`` was not convincing, the runner should be removed anyway because the functional tests
   will need to be `"nosified" <https://nose.readthedocs.org/en/latest/index.html>`_ in order to achieve uniformity and consistency throughout the test suite. Nose picks up different types of
   ``assertions``, not only ones from unittest, but also e.g. ``assert_array_equal`` from Numpy. Doing this will require a good understanding of
   what the tests do, though.
   
   Currently, functional tests are marked as `@nottest <https://nose.readthedocs.org/en/latest/testing_tools.html?highlight=nottest#nose.tools.nottest>`_ in order to not mess up the nose runner.
   
   Nose will allow to easily run different sets of tests by using the `attrib plugin <https://nose.readthedocs.org/en/latest/plugins/attrib.html>`_ 
   instead of specifically writing code to differentiate the types of tests.
   
5. Coverage: currently, no code coverage is observed for functional tests because ``runtests`` evoked `coverage.py <http://nedbatchelder.com/code/coverage/>`_ separately
   (see the Makefile; commands are still there). However, coverage reports whould also be "outsourced" to nose because it handles them much better
   (see the README for ``topo.tests.unit``). E.g. there is no need to manually issue commands for deleting previous output or combining reports.
   
   It is arguable whether coverage is appropriate for functional tests which run a large body of code and only check its final output; coverage will
   only report code as having been **run**, but this doesn't mean that it has been **tested**, so it's not particularly reliable for tests other than
   unit. However, it can be used as a reverse metric: seeing that code has been run does not mean that it's tested but seeing that it has **not** been
   run means that it definitely is **not** tested. Therefore, it can be useful to have coverage restored for the functional tests as part of the nose
   suite and remove the old commands.
   
6. Clean up ALERTs and issues identified throughout the comments in the modules, e.g. why certain tests have been ommitted.

7. Expand the tests, using coverage reports (see 5) as reference if necessary.
