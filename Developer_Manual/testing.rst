**********
Test suite
**********

Every Python module should have a corresponding unit test in
``tests/``. The tests should be nearly exhaustive, in the sense that
it should be unlikely that a good-faith re-implementation of the
module would pass the tests but have significant bugs. Obviously,
truly exhaustive tests capable of detecting arbitrary (e.g.
deliberate) errors would be impractical.

The default set of unit tests that are run must complete very
quickly, with no extraneous output, no GUI windows popping up, etc.,
because these tests are (and should be) run automatically many times
each day during active development. All the output from such tests
must be checked automatically, with any output generated for the
user representing something the user really does have to do
something about.

Additional more expensive tests, GUI tests, or those requiring user
input or user examination of the output are also encouraged, but all
these must be kept separate from the main automated regression
tests.

Note that, due to previous oversights, one cannot assume that any
existing file has a corresponding test file already. Moreover,
existing test files should *not* be assumed to be exhaustive or even
particularly useful; they vary a lot in how comprehensive they are.
So please always check the test file when coding, especially when
debugging, because it probably needs work too. You can check how
well a particular test file covers a particular file by running
coverage. Here is an example of checking to see how well
topo/tests/testimage.py covers topo/pattern/image.py:

::

  ./topographica -c "import topo.tests;t=topo.tests.run_coverage( \   runner_fn=topo.tests.run_named,runner_args=('testimage.py',), \   targets=['topo/pattern/image.py'])"

Unittests and Doctests
----------------------

Topographica's test suite supports test cases that use Python's
`unittest`_ module or its `doctest`_ module. Unittest provides a
framework for writing test cases as objects containing a set of test
methods plus common initialization and clean-up code. This framework
is useful for constructing heavy-duty tests, but can be cumbersome
when only a simple set of correctness tests are required. All
unittests in modules with names matching the pattern
``topo/tests/test*.py`` can be automatically discovered and run by
the topographica command ``topo.tests.run()``

Python's doctest module allows tests to be specified as a sequence
of Python expressions to be evaluated, each followed by the expected
result of the command. The entire sequence should be formatted like
a trace of an interactive python session. For example:

::

  >>> def f(x):
  ...    return x+1
  ... 
  >>> f(3)
  4
  >>> f(2)
  3
  >>> f('foo')
  Traceback (most recent call last):
    File "", line 1, in ?
    File "", line 2, in f
  TypeError: cannot concatenate 'str' and 'int' objects
  >>> 

As long as each command produces the expected output (including any
errors), the test passes. See the `doctest documentation`_ for
details. As with unittest testsuites, all doctest files with names
matching ``topo/tests/test*.txt`` can be found and run automatically
with the function ``topo.tests.run()``.

Important notes:

-  To construct a doctest file from an interactive topographica
   trace, the entire ``topographica_tXXX`` prefix must be removed
   from every line. Lines with the prefix will be ignored.
-  The testrunner used by ``topo.tests.run()`` will happily run an
   empty doctest file and report no errors (since there were no
   tests). Make sure to manually check new or modified doctest files
   with ``doctest.testfile(filename,verbose=True)`` to make sure
   that the tests are actually being run before running
   ``make tests`` or ``topo.tests.run()``.
-  Topographica does not currently run doctests embedded in code
   documentation.

Automatic testing
-----------------

Currently, topographica is periodically checked out, built, and
tested on Linux, OS X, and Windows (automatically, using
`buildbot`_). The results of these builds and tests can be seen at
`buildbot.topographica.org`_.

.. _unittest: http://docs.python.org/lib/module-unittest.html
.. _doctest: http://docs.python.org/lib/module-doctest.html
.. _doctest documentation: http://docs.python.org/lib/module-doctest.html
.. _buildbot: http://buildbot.net/
.. _buildbot.topographica.org: http://buildbot.topographica.org/
