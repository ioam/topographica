"""
Unit test for SheetView
"""

import unittest

import numpy.oldnumeric as Numeric

from topo.base.sheet import Sheet
from topo.base.boundingregion import BoundingBox
from topo.base.sheetview import *
from topo.plotting.bitmap import PaletteBitmap

# Turn False once development is complete and this module is to be
# included as part of the system unit testing.
DEV = False


### JCALERT! This testfile has to be finished (I would say entirely reviewed)
### It does not really test efficiently has it is now.
### Also, it should be included in tests/__init__.py

class TestSheetView(unittest.TestCase):

    def setUp(self):
        self.s = Sheet()
        self.s.activity = Numeric.array([[1,2],[3,4]])
        self.s2 = Sheet()
        self.s2.activity = Numeric.array([[4,3],[2,1]])

    def test_init(self):

        sv1 = SheetView((self.s.activity,self.s.bounds),
                          src_name=self.s.name)
        # s.sheet_view() returns a SheetView
        self.s.sheet_views['sv1']=sv1
        sv2 = SheetView((self.s.activity,self.s.bounds),
                                 src_name=self.s.name)
        # s.sheet_view() returns a SheetView
        self.s.sheet_views['sv2']=sv2

        # Define a type 1 SheetView, with matrix and bounding box.
        sv3 = SheetView((self.s.activity, self.s.bounds))
        sv4 = SheetView((self.s2.activity,self.s2.bounds))
        # Define a type 2 SheetView,
        sv5 = SheetView((ADD,((sv3,None),(sv4,None))))
        sv6 = SheetView((ADD,[(sv3,None),
                              (sv4,None),
                              (self.s2.activity,self.s2.bounds)]))
        sv7 = SheetView((SUBTRACT,[(sv3,None),
                              (sv4,None),
                              (self.s2.activity,self.s2.bounds)]))

        # Define a type 3 SheetView
        sv8 = SheetView((self.s,'Activity'))
        if DEV:
            sv3.message(sv3.view())
            sv6.message('sv6.debug', sv6._view_list)
            sv6.message(sv6.view())


# CEBALERT: replace with test using FileImage
##     def test_view(self):
##         ImageGenerator.nominal_bounds = BoundingBox(points=((-0.8,-0.8),(0.8,0.8)))
##         ImageGenerator.nominal_density = 100

##         input = ImageGenerator(filename='topo/tests/testsheetview.ppm')
##      sv = SheetView((input.activity,input.bounds),
##                           src_name=input.name)
##         input.sheet_views['Activity']=sv
##         sv_tuple = sv.view()
##         map = PaletteBitmap(sv_tuple[0])
##         # map.show()


#     def test_generate_coords(self):
#         sv = UnitViewArray((self.s.activity, self.s.bounds))
#         print sv.generate_coords(1,self.s.bounds)
#


    def test_sum_maps(self):
        """Stub"""
        self.assertEqual(1+1,2)



# CB: I think this class can be removed now. We have topo/patterns/image.py, which uses a Sheet.

## # CEBALERT: Used in a number of test files. Maybe one day topo/patterns/image.py
## # will be based on a Sheet, in which case this could be removed.
## from numpy.oldnumeric import resize,array
## from topo.base.sheet import Sheet
## from topo.base.simulation import EventProcessor
## from topo.misc.util import NxN
## from param import Parameter
## from pprint import *
## import Image, ImageOps

## class ImageGenerator(Sheet):
##     """

##     parameters:

##       filename = The path to the image file.

##     A sheet that reads a pixel map and uses it to generate an activity
##     matrix.  The image is converted to grayscale and scaled to match
##     the bounds and density of the sheet.

##     NOTE: A bare ImageGenerator only sends a single event, containing
##     its image when it gets the .start() call, to repeatedly generate
##     images, it must have a self-connection.  More elegant, however,
##     would be to convert the ImageGenerator from a sheet to a generator
##     function suitable for use with the GeneratorSheet class (see
##     topo/sheets/generator.py).

##     """
##     filename = param.Parameter(None)

##     def __init__(self,**params):

##         super(ImageGenerator,self).__init__(**params)

##         self.verbose("filename = " + self.filename)

##         image = Image.open(self.filename)
##         image = ImageOps.grayscale(image)
##         image = image.resize(self.activity.shape)
##         self.activity = resize(array([x for x in image.getdata()]),
##                                  (image.size[1],image.size[0]))

##      self.verbose("Initialized %s activity from %s" % (NxN(self.activity.shape),self.filename))
##         max_val = float(max(self.activity.ravel()))
##         self.activity = self.activity / max_val


##     def start(self):
##      assert self.simulation
##      self.simulation.enqueue_event_rel(0,self,self,data=self.activity)

##     def input_event(self,src,src_port,dest_port,data):
##         self.send_output(data=self.activity)

if __name__ == "__main__":
	import nose
	nose.runmodule()