"""
Unit tests for bitmap.py

Constructs a few bitmap objects but does not display them or compare them
to a base image.  Primary purpose of testing is to verify that the interface
to the PIL imaging library does all the expected operations such as loading
jpg.

Should be extended as more functionality is added to the Bitmap
classes.

$Id$
"""

import topo
from topo.plotting.bitmap import *
from topo.plotting.bitmap import hsv_to_rgb
import Image
import numpy.oldnumeric as Numeric
import unittest
from param import resolve_path

class TestBitmap(unittest.TestCase):


    def setUp(self):
        """
        Uses testbitmap.jpg in the topographica/tests directory
        """
        miata = Image.open(resolve_path('tests/testbitmap.jpg'))
        miata = miata.resize((miata.size[0]/2,miata.size[1]/2))
        self.rIm, self.gIm, self.bIm = miata.split()
        self.rseq = self.rIm.getdata()
        self.gseq = self.gIm.getdata()
        self.bseq = self.bIm.getdata()
        self.rar = Numeric.array(self.rseq)
        self.gar = Numeric.array(self.gseq)
        self.bar = Numeric.array(self.bseq)
        self.ra = Numeric.reshape(self.rar,miata.size) / 255.0
        self.ga = Numeric.reshape(self.gar,miata.size) / 255.0
        self.ba = Numeric.reshape(self.bar,miata.size) / 255.0


    def test_PaletteBitmap(self):
        p = [j and i for i in range(256) for j in (1,0,0)]
        cmap = PaletteBitmap(self.ra,p)
         # cmap.show()


    def test_HSVBitmap(self):
        a = [j for i in range(16) for j in range(16)]
        b = [i for i in range(16) for j in range(16)]
        c = [max(i,j) for i in range(16) for j in range(16)]
        a = Numeric.reshape(a,(16,16)) / 255.0
        b = Numeric.reshape(b,(16,16)) / 255.0
        c = Numeric.reshape(c,(16,16)) / 255.0
        hsv = HSVBitmap(a,b,c)
        # hsv.show()

    def test_hsv_to_rgb(self):
        h,s,v = 0.0,0.0,0.5
        (r,g,b) = hsv_to_rgb(h,s,v)
        self.assertEqual(r,0.5)
        self.assertEqual(g,0.5)
        self.assertEqual(b,0.5)

        h,s,v = 0.0,0.0,0.01
        (r,g,b) = hsv_to_rgb(h,s,v)
        self.assertEqual(r,0.01)
        self.assertEqual(g,0.01)
        self.assertEqual(b,0.01)

 

    def test_RGBBitmap(self):
        rgb = RGBBitmap(self.ra,self.ga,self.ba)
        # rgb.show()


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestBitmap))
