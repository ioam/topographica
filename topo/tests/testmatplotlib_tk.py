"""
Unit test for the matplot lib in tkgui

"""

import unittest
import matplotlib

class TestMatPlotLibTk(unittest.TestCase):

    def test_TkAgg(self):
        import matplotlib
        #matplotlib.use('TkAgg')
        try: import pylab
        except ImportError: havetkagg = False
        else: havetkagg = True
        if not havetkagg:
            raise 'TkAgg is not available.  When MatPlotLib was built it did not find Tkinter.'



suite = unittest.TestSuite()
#  Uncomment the following line of code, to disable the test if
#  $DISPLAY is undefined.  Used mainly for GUI testing.
suite.requires_display = True
suite.addTest(unittest.makeSuite(TestMatPlotLibTk))
