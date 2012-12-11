"""
Simple framework to run a set of tests and report the results.
"""

import traceback,sys,inspect

# CB: not sure this file should exist, or what it should be called.


def run(tests,title=None):
    """
    Call tests and print the outcomes.

    Each function in tests will be called. Any unhandled exception is
    recorded as a failure; tracebacks from such failures are printed.

    For each test function, prints the name, the docstring, and
    whether it passed or failed.

    Prints and returns the number of errors.
    """
    if title: print "\n%s\n"%title
    errs = {}
    for test in tests:
        test_info = "%s (%s)"%(test.__name__,inspect.getdoc(test))
        error = _run_test(test)
        if error is None:
            print "PASS: %s"%test_info
        else:
            print "FAIL: %s"%test_info
            errs[(test.__name__,test.__doc__)]=error

    for t,e in errs.items(): print "\n** Error from %s (%s):\n%s\n"%(t[0],t[1],e)
    print "\nNumber of tests: %s"%len(tests)
    print "Number of errors: %s\n"%len(errs)
    return len(errs)


def _run_test(test):
    """Call test and return None on success, or the exception string on failure."""

    import StringIO
    stderr = StringIO.StringIO()
    sys.stderr = stderr

    # CEBALERT: for some reason, this doesn't always catch errors.
    # I guess somehow they are buried? So in addition to this,
    # we check stderr!
    try:
        test()
        X=None
    except:
        X=traceback.format_exc()

    # there's some thing to have bit of code always executed,
    # but can't remember what it is. with it, could make this
    # code cleaner.

    sys.stderr = sys.__stderr__

    if stderr.getvalue(): X = stderr.getvalue()
    stderr.close()

    return X


