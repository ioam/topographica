"""
Unit tests for Topographica.

Use the 'run' function to run all the tests.


We use unittest and doctest to create tests. The run() function calls
tests in files in topo/tests/ that:

* have a name beginning with 'test' and ending with '.py', if the file
defines the 'suite' attribute;
* have a name beginning with 'test' and ending with '.txt'.

If Tkinter cannot be imported, files that have a name ending with
'_tk' are not imported (hence any tests that they contain are
skipped).


unittest
========

We use unittest in two different ways. The first is simply
to run a series of tests:


class TestSomething(unittest.TestCase):

    def setUp(self):
        ...

    def test_x(self):
        ...

    def test_y(self):
        ...

    def extra(self):
        ...
        

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestSomething))


In the example above, setUp will be called, followed by test_x and
test_y (i.e. the methods setUp and test_* are called automatically);
the extra() method will not be called (unless your code calls it).
setUp does not have to exist.


The second way we use unittest is to pass a series of scenarios
through one battery of tests:


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


suite = unittest.TestSuite()

cases = [TestScenario1,TestScenario2]
suite.addTests([unittest.makeSuite(case) for case in cases])


In this second example, TestScenario1.setUp will be called, followed
by test_x and test_y. After this, TestScenario2.setUp will be called,
followed again by test_x and test_y. setUp in the two TestScenarios is
therefore used to create some different data or situations to pass
through the tests.



To be run() automatically, unittest files must (a) be named test*.py, and
(b) must define the 'suite' attribute.


Additionally, unittest files should:

(a) contain the following code to allow the file to be run on its own:

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)

    
(b) set suite.requires_display=True if the tests require a DISPLAY.

(c) call topo.tests.start_tkgui() before running tests (e.g. in
    setUP()) if they require the GUI to be running




doctest
=======





"""

# CEBALERT: It might be good if tests/ were a directory at the top
# level, with a subdirectory structure mirroring that of topo/. Then
# it is more likely we'd have a separate test file for each module,
# and we could also simply name the files the same as what they are
# testing, which could make it simpler to find the right test file.

# CEBALERT: tests often affect each other. Make sure test authors are
# aware of that, and have some kind of policy.  (Setting class
# attributes, sharing a sim, etc)

# CEBALERT: some of the test modules are missing code to handle running
# (i.e. running as './topographica topo/tests/testsheet.py').



import unittest,doctest,os,re,fnmatch,socket
import param

# Automatically discover all test*.py files in this directory
__all__ = [re.sub('\.py$','',f)
           for f in fnmatch.filter(os.listdir(__path__[0]),'test*.py')]

all_doctest = sorted(fnmatch.filter(os.listdir(__path__[0]),'test*.txt'))

# location in which to create semi-permanent test data
output_path = param.normalize_path.prefix
tests_output_path = os.path.join(output_path,'tests',socket.gethostname())
if not os.path.exists(tests_output_path):
    print "Creating %s"%tests_output_path
    os.makedirs(tests_output_path)



try:
    import Tkinter
except ImportError:
    tk_tests = fnmatch.filter(__all__,'*_tk')
    tk_doctests = fnmatch.filter(all_doctest,'*_tk')
    param.Parameterized().warning('no Tkinter module: skipping %s'%str(tk_tests+tk_doctests))
    for t in tk_tests:
        __all__.remove(t)
    for t in tk_doctests:
        all_doctest.remove(t)
    

try:
    import gmpy
    gmpy_imported=True
except ImportError:
    gmpy_imported=False

if gmpy_imported and gmpy.__file__ is None:
    gmpy_imported=False

if not gmpy_imported:
    import param
    param.Parameterized().warning('no gmpy module: testgmpynumber.txt skipped')
    all_doctest.remove('testgmpynumber.txt')

# CEBALERT: we need to rename these/reorganize the tests
__all__.remove('test_script')
__all__.remove('test_map_measurement')   

try:
    import scikits.audiolab
except ImportError:
    import param
    param.Parameterized().message("no scikits.audiolab: testaudio.py skipped")
    __all__.remove('testaudio')

# CEBALERT: should be using python warnings, and having unittest
# report warnings.
try:
    import matplotlib
except ImportError:
    import param
    param.Parameterized().warning("Matplotlib is not available; skipping Matplotlib tests.")
    __all__.remove('testmatplotlib')
    __all__.remove('testmatplotlib_tk')


__all__.sort()


def all_suite():
    """
    __all__:
    For each test module that defines a 'suite' attribute, add its
    tests.  Only adds tests requiring a display if the DISPLAY
    environment variable is set.

    all_doctest:
    Add each doctest file to the suite.
    """
    suite = unittest.TestSuite()

    for test_name in __all__:
        # import the module
        exec 'import '+test_name

        test_module = locals()[test_name]
        try:        
            print 'Loading suite from module %s ...' % test_name,
            new_test = getattr(test_module,'suite')

            if _check_for_display(new_test):
                print 'ok.'
                suite.addTest(new_test)
            else:
                print 'skipped: No $DISPLAY.'
                
        except AttributeError,err:
            print err

    for filename in all_doctest:
        print 'Loading doctest file', filename
        suite.addTest(doctest.DocFileSuite(filename))
    return suite


# Note that this is set up so that if all the tests are run and
# there's no DISPLAY, tests requiring DISPLAY are skipped - but if a
# test is run individually via run_named() and it requires DISPLAY, an
# error will be raised.
def _check_for_display(suite):
    """
    Return True if no DISPLAY required or DISPLAY is required and it exists,
    otherwise return False.
    """
    if not hasattr(suite,'requires_display'):
        return True
    elif os.getenv('DISPLAY'):
        return True
    else:
        return False    


def run(verbosity=1,test_modules=None):
    """
    Run tests in all test_modules; test_modules defaults to all_suit().

    E.g. to run all tests:
      ./topographica -c 'from topo.tests import run; run()'

    
    verbosity specifies the level of information printed during the
    tests (see unittest.TextTestRunner).


    To run only a subset of the tests, specify a list of test modules or doctest
    file names. For example:

      ./topographica -c 'from topo.tests import run, testimage, testsheet; run(test_modules=[testimage,testsheet,"testDynamicParameter.txt"])'
    """
    import types
         
    if not test_modules:
        run_suite = all_suite()
    else:
        assert isinstance(test_modules,list), 'test_modules argument must be a list of test modules or doctest filenames.'
        
        run_suite = unittest.TestSuite()
        
        for test_module in test_modules:
            if isinstance(test_module,types.ModuleType):
                if _check_for_display(test_module.suite):
                    run_suite.addTest(test_module.suite)
                else:
                    raise Exception("Cannot run test without a valid DISPLAY.")
            elif isinstance(test_module,str):
                if test_module in all_doctest:
                    run_suite.addTest(doctest.DocFileSuite(test_module))
                else:
                    raise ValueError, '"%s" is not an available doctest file.' % test_module
            else:
                raise ValueError, '%s is not a valid test module' % str(test_module)
                                 

    return unittest.TextTestRunner(verbosity=verbosity).run(run_suite)



# CB: if the unit tests were faster, I wouldn't keep needing this...
def run_named(name,verbosity=2):
    """
    Run the named test module.

    Convenience function to make it easy to run a single test module.

    Examples:
      ./topographica -c 'import topo.tests; topo.tests.run_named("testsnapshots.py")'
      ./topographica -c 'import topo.tests; topo.tests.run_named("testDynamicParameter.txt")'
    """
    if name.endswith('.py'):
        module_name = "topo.tests."+name[0:-3]
        import __main__
        exec "import %s"%module_name in __main__.__dict__
        test_module = eval(module_name,__main__.__dict__)
    else:
        test_module = name
    
    run(verbosity,test_modules=[test_module])
