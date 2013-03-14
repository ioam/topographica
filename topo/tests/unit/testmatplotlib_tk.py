"""
Unit test for the matplot lib in tkgui
"""

import os
from nose.plugins.skip import SkipTest

if os.getenv("DISPLAY"):
    import topo.tkgui
    topo.tkgui.start()
else: raise SkipTest("No DISPLAY found")

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

if __name__ == "__main__":
	import nose
	nose.runmodule()