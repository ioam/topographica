"""
Test for Palette

$Id$
"""
__version__='$Revision$'


import unittest
from topo.plotting.palette import *

class TestPalette(unittest.TestCase):
    def test_Palette(self):
        p2 = Palette(background=WHITE_BACKGROUND)
        p3 = Palette()
        # print p3, p3.ravel()()
        # print p2, p2.ravel()()
        # print '128 =', p3.color(128)
        

    def test_Monochrome(self):
        p = Monochrome()
        p2 = Monochrome(background=WHITE_BACKGROUND)
        # print p2, p2.ravel()()
        # print p, p.ravel()()
        # print '64 =', p.color(64), p2.color(64)
        


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestPalette))
