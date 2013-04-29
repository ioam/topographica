NOSE UNIT TESTS
===============

Before I start with the actual README, here are the two most important things I have to say:

1. WRITE UNIT TESTS.

2. EMBED DOCTESTS IN CODE MODULES.


REASONING
---------

From the old README:

   Ideally, the 'unit' target (i.e. unit tests) would be all that people
   need to run. Developers, for checking they haven't messed obvious
   stuff up. Users, for checking a Topographica installation functions ok
   on their system. The other, slower targets would only need to be run
   by buildbot (on behalf of everyone).
   
   Unfortunately, the unit tests do not currently cover enough! It's an
   important project to improve them. Until then, the default is to run
   more of the tests (but not all, since that takes too long).

These tests were separated from the remainder of the test suite for two reasons. The first is this:

   [L]arge-scale integration or functional tests should be
   separated out from these unit tests, because the unit tests are
   designed to be easily updated when units change, and need to run
   quickly so that the unit tests can be run at least daily, and usually
   more often, during development.

The second is a derivative of the first; in order to keep track of how well code modules are covered, it would be helpful to have a directory
and module structure similar to that of the actual ``topo`` module structure. This should be achieved when the unit tests are reworked and expanded.

   Note that there need not be a 1-1 correspondence between test modules
   and topographica modules.  For example, a special test module designed
   to test the interaction between two topographica modules would be
   fine.

A further important are to consider is the unharnessed power and flexibility of `doctest <http://docs.python.org/2/library/doctest.html>`_ which allows to include tests in the form of comments in the actual code modules. The advantages of doctest are twofold:

- testing basic functionalities quickly, while the change is still fresh in your mind, without having to write separate test modules. It will be
  therefore easy to change the test if the functionality changes.

- this also serves as documentation, showing sample input and expected output to describe how the tested method is supposed to behave.

This flexibility was negated by the fact that previously, the only use of doctests in Topographica was in .txt files, put separately with the unit
test modules. While separate doctests may be useful, the remainder of Topographica contains no doctests whatsoever. The sole exception are a few
third-party modules in ``topo.misc``, which is a shame. The previous runner did not contain code for searching inside code modules.

To meet all of the above requirements, the unit tests were converted to the `nose runner <https://nose.readthedocs.org/en/latest/index.html>`_
in order to "outsource" hundreds of lines of not-particularly-robust (and also insufficient) custom Topographica code to a well working external
library that provides a plethora of other options and flexible functionalities. Details follow below.


FINDING AND RUNNING THE TESTS
-----------------------------

Except for a few little tweaks (discussed later), there is almost nothing that needs to be done to an out-of-the-box test module written with Python's
unittest in order to run it with nose. The simplest case is to type ``nosetests`` at the top-level Topographica directory; nose will then look at all
packages and modules in the directory tree below, and will pick up modules containing the word ``test`` in their name (observe how modules in this
package are named), or ones that subclass ``unittest.TestCase``. See `nose docs <https://nose.readthedocs.org/en/latest/finding_tests.html>`_ .

This will be sufficient to discover all dedicated test modules and run them.

To see detailed output of each test case that nose picked up, use ``nosetests -v``.

To run an individual module, type ``nosetests testmodule.py``. To run a set of modules, type ``nosetests test1.py test2.py test3.py``.

USING DOCTEST
-------------

Nose uses a `built-in plugin <https://nose.readthedocs.org/en/latest/plugins/doctests.html>`_ to enable running doctests.

To make nose look for doctests in modules that are not named "testsomething", pass the option ``--with-doctest``. It will then look inside all other
modules. To make it look in non-Python files containing doctests (there are several such files here), pass the option ``--doctest-extension=txt``.
See buildbot logs.

Running ``nosetests`` at the ``topo/tests/unit`` level will produce errors because relative paths have been tweaked for running from the top-level
Topographica directory; this is the advised way to run since it enables nose to look in other Topographica packages for doctests.

SKIPPING TESTS
--------------

Nose documentation is not clear about what nose does when it looks for doctests inside a given module. One thing I've found from experience is that
it follows imports; i.e. it will raise an exception if an import failed. To circumvent this, use SkipTest::

   from nose.plugins.skip import SkipTest
   
   try:
       import playerc
   except ImportError:
       raise SkipTest("Module requires the Player/Stage package to be run")

This has been used in ``topo/misc/playerrobot.py`` and ``topo/misc/unitsupport.py`` which are included in the repository for reference and are not 
used anywhere in Topographica; thus, any nose-related errors should be suppressed. If these modules are to be used elsewhere, SkipTest code should
be removed.

SkipTest has been further used in the following unit test modules:

- ``testAudio``, which requires an audio file that is not included in the Topographica repository

- ``testgmpynumber``, which requires the gmpy library to be installed

- ``testmatplotlib_tk``, ``testparameterizedobject_tk`` and ``testparametersframe_tk``, which require the Linux DISPLAY environmental variable and
  are skipped on Windows.
  
A further mechanism for skipping classes and methods that "look like" tests is to use the `@nottest decorator <https://nose.readthedocs.org/en/latest/testing_tools.html?highlight=nottest#nose.tools.nottest>`_ ::

   from nose.tools import nottest
   
   @nottest
   def test_script(script,decimal=None):

This has been used to exclude functional tests from the nose runner (see README in topo/tests) and to exclude "test batteries" from running (see below).

COVERAGE AND OTHER PLUGINS
--------------------------

Nose's default `plugin <https://nose.readthedocs.org/en/latest/plugins/cover.html>`_ for running coverage does not work well. It requires careful
tweaking, fails to omit Python libraries from coverage reports, and fails to take into account `.coveragerc <http://nedbatchelder.com/code/coverage/config.html>`_ files.

For this reason, Topographica's nose runner now uses the third-party plugin `nose-cov <https://pypi.python.org/pypi/nose-cov>`_ which works
substantially better. Coverage will only be run by buildbot so installing a lightweight external library on one slave is not a problem.

The plugin is enabled with the option ``--with-cov``, and HTML reports are generated with ``--cov-report html``. See buildbot logs.

Many additional plugins are `already available <https://nose.readthedocs.org/en/latest/plugins/builtin.html>`_ from nose itself. Many others are
available from PyPI or `Nose Plugins <http://nose-plugins.jottit.com/>`_ .

WRITING TESTS
-------------

When writing tests, don't forget to include the word "test" in module and attribute names (without using underscores in filenames) so that nose
can pick up these tests. See current modules for reference.

There are two types of tests used. The basic type is as follows::

   class TestSomething(unittest.TestCase):
   
       def setUp(self):
           ...
   
       def test_x(self):
           ...
   
       def test_y(self):
           ...
   
       def extra(self):
           ...

This is the most common type, and is also the one seen in examples everywhere. The second type consists of running several test cases through
one "battery" of tests::

   class TestSomething(unittest.TestCase):
   
       def test_x(self):
           ...
   
       def test_y(self):
           ...
   
   class TestCase1(TestSomething):
   
       def setUp(self):
           ...
   
   class TestCase2(TestSomething):
   
       def setUp(self):
           ...
		   
To use this, put a ``@nottest`` decorator before the definition of ``class TestSomething`` because if nose attempts to run it, it will fail
since no ``setUp`` methods have been run yet.

Using ``nosetests testmodule.py`` allows to run the module separately but the default behaviour (i.e. when running ``python testmodule.py``) should
also be specified with a "boilerplate" at the bottom of the module::

   if __name__ == "__main__":
      import nose
      nose.runmodule()

PROBLEMS AND FURTHER WORK
-------------------------

The following problems have been identified with existing test modules:

- `nosetests` produces sinister warning messages when running on DICE; see Buildbot logs.

- ``testaudio.py`` should not be skipped because of not finding a given audio file in the Topographica repository. It should get the file from the
  ``ioam/dataset-sounds/complex`` repository (file called ``daisy.wav``).

- The ``_tk`` test files should not be skipped on Windows because of missing DISPLAY variable from Linux. Instead, the tests should find the Windows
  equivalent i.e. a platform-independent method should be used.

- many of the test modules are riddled with ALERTs and are marked as incomplete. Some of them have hundreds of lines of code commented out and
  replaced with a ``pass`` statement.

- enable tests for external packages (e.g. ImaGen, Param) to be run separately from the main Topographica suite. Use attributes via the
  `attrib plugin <https://nose.readthedocs.org/en/latest/plugins/attrib.html>`_ to mark tests into different categories and run them separately. Possibly even move these tests to their respective packages.
  
Once these issues are fixed, the suite should be restructured as necessary and expanded to cover more of Topographica.