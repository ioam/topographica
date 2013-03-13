import unittest

class TestMatPlotLib(unittest.TestCase):

    def test_matplotlib(self):
        try: import matplotlib
        except ImportError: havematplotlib = False
        else: havematplotlib = True
        if not havematplotlib:
            raise "MatPlotLib has not properly been installed.  Failed to import"

    def test_agg(self):
        import matplotlib
        #matplotlib.use('Agg')
        try: import pylab
        except ImportError: haveagg = False
        else: haveagg = True
        if not haveagg:
            raise 'MatPlotLib has not properly been installed.  Failed to import PyLab Agg backend.'

if __name__ == "__main__":
	import nose
	nose.runmodule()