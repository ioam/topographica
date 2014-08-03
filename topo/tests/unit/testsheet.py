"""
Unit tests for sheet and sheetcoords.
"""

import unittest

from nose.tools import istest, nottest
import numpy as np

from topo.base.sheetcoords import Slice
from topo.base.sheet import *
from topo.base.boundingregion import BoundingBox


# CEBALERT:
# Changes that need to be made to this file:
# - don't create a new ct every time, just change its density
# - test array versions of coordinate transform functions
# - ensure methods of Slice are tested

@nottest
class TestCoordinateTransforms(unittest.TestCase):
    """
    Tests for sheet.

    Subclassed for use; the subclasses have a setUp method to create
    the particular coordinates to use each time.
    """
    def makeBox(self):
        self.box = BoundingBox(points=((self.left,self.bottom),
                                       (self.right,self.top)))

        self.ct = SheetCoordinateSystem(self.box,self.density,self.density)

        # float bounds for matrix coordinates: these
        # values are actually outside the matrix
        self.rbound = self.density*(self.top-self.bottom)
        self.cbound = self.density*(self.right-self.left)

        #self.cbound = int(self.density*(self.right-self.left)) / float((self.right-self.left))
        #self.rbound = int(self.density*(self.top-self.bottom)) / float((self.top-self.bottom))


        # CEBALERT: this is supposed to be a small distance
        D = 0.00001

        # Sheet values around the edge of the BoundingBox
        self.just_in_right_x = self.right - D
        self.just_in_bottom_y = self.bottom + D
        self.just_out_top_y = self.top + D
        self.just_out_left_x = self.left - D

        # Matrix values around the edge of the matrix
        self.just_out_right_idx = self.rbound + D
        self.just_out_bottom_idx = self.cbound + D
        self.just_out_top_idx = 0.0 - D
        self.just_out_left_idx = 0.0 - D



    ### sheet2matrix() tests
    #
    def test_sheet2matrix_center(self):
        """
        Check that the center of the Sheet corresponds to the center
        of the matrix.
        """
        x_center = self.left+(self.right-self.left)/2.0
        y_center = self.bottom+(self.top-self.bottom)/2.0
        row, col = self.ct.sheet2matrix(x_center,y_center)
        self.assertEqual((row,col),(self.rbound/2.0,self.cbound/2.0))


    def test_sheet2matrix_left_top(self):
        """
        Check that the top-left of the Sheet is [0,0] in matrix
        coordinates.
        """
        row, col = self.ct.sheet2matrix(self.left,self.top)
        self.assertEqual((row,col),(0,0))


    def test_sheet2matrix_right_bottom(self):
        """
        Check that the bottom-right of the Sheet is [rbound,cbound] in matrix
        coordinates.
        """
        row, col = self.ct.sheet2matrix(self.right,self.bottom)
        self.assertEqual((row,col),(self.rbound,self.cbound))


    def test_sheet2matrix_matrix2sheet(self):
        """
        Check that matrix2sheet() is the inverse of sheet2matrix().
        """
        # top-right corner
        row, col = self.ct.sheet2matrix(self.right,self.top)
        x_right, y_top = self.ct.matrix2sheet(row,col)
        self.assertEqual((x_right,y_top),(self.right,self.top))

        # bottom-left corner
        row, col = self.ct.sheet2matrix(self.left,self.bottom)
        x_left, y_bottom = self.ct.matrix2sheet(row,col)
        self.assertEqual((x_left,y_bottom),(self.left,self.bottom))


    def test_matrix2sheet_sheet2matrix(self):
        """
        Check that sheet2matrix() is the inverse of matrix2sheet().
        """
        # top-right corner
        x,y = self.ct.matrix2sheet(float(0),float(self.last_col))
        top_row,right_col = self.ct.sheet2matrix(x,y)
        self.assertEqual((top_row,right_col),(float(0),float(self.last_col)))

        # bottom-left corner
        x,y = self.ct.matrix2sheet(float(self.last_row),float(0))
        bottom_row,left_col = self.ct.sheet2matrix(x,y)
        self.assertEqual((bottom_row,left_col),(float(self.last_row),float(0)))


    ### sheet2matrixidx() tests
    #
    def test_sheet2matrixidx_left_top(self):
        """
        Test a point just inside the top-left corner of the BoundingBox, and
        one just outside.
        """
        # inside
        r,c = 0,0
        x,y = self.left,self.top
        self.assertEqual(self.ct.sheet2matrixidx(x,y), (r,c))

        # outside
        r,c = -1,-1
        x,y = self.just_out_left_x,self.just_out_top_y
        self.assertEqual(self.ct.sheet2matrixidx(x,y), (r,c))


    def test_sheet2matrixidx_left_bottom(self):
        """
        Test a point just inside the left-bottom corner of the BoundingBox, and
        one just outside.
        """
        # inside
        r,c = self.last_row, 0
        x,y = self.left, self.just_in_bottom_y
        self.assertEqual(self.ct.sheet2matrixidx(x,y),(r,c))

        # outside
        r,c = self.last_row+1, -1
        x,y = self.just_out_left_x, self.bottom
        self.assertEqual(self.ct.sheet2matrixidx(x,y),(r,c))


    def test_sheet2matrixidx_right_top(self):
        """
        Test a point just inside the top-right corner of the BoundingBox, and
        one just outside.
        """
        # inside
        r,c = 0,self.last_col
        x,y = self.just_in_right_x,self.top
        self.assertEqual(self.ct.sheet2matrixidx(x,y),(r,c))

        # outside
        r,c = -1,self.last_col+1
        x,y = self.right,self.just_out_top_y
        self.assertEqual(self.ct.sheet2matrixidx(x,y),(r,c))


    def test_sheet2matrixidx_right_bottom(self):
        """
        Test a point just inside the bottom-right corner of the BoundingBox,
        and the corner itself - which should not be inside.
        """
        # inside
        r,c = self.last_row,self.last_col
        x,y = self.just_in_right_x,self.just_in_bottom_y
        self.assertEqual(self.ct.sheet2matrixidx(x,y),(r,c))

        # not inside
        r,c = self.last_row+1,self.last_col+1
        x,y = self.right,self.bottom
        self.assertEqual(self.ct.sheet2matrixidx(x,y),(r,c))


    ### matrix2sheet() tests
    #
    def test_matrix2sheet_left_top(self):
        """
        Check that Sheet's (0,0) is the top-left of the matrix.

        Check that just outside the top-left in matrix coordinates
        comes back to Sheet coordinates that are outside the
        BoundingBox.
        """
        x,y = self.ct.matrix2sheet(0,0)
        self.assertEqual((x,y), (self.left,self.top))

        x,y = self.ct.matrix2sheet(self.just_out_left_idx,self.just_out_top_idx)
        self.assertFalse(self.box.contains(x,y))


    def test_matrix2sheet_right_bottom(self):
        """
        Check that Sheet's (right,bottom) is the bottom-right in
        matrix coordinates i.e. [rbound,cbound]

        Check that just outside the bottom-right in matrix coordinates
        comes back to Sheet coordinates that are outside the
        BoundingBox.
        """
        x,y = self.ct.matrix2sheet(self.rbound,self.cbound)
        self.assertEqual((x,y), (self.right,self.bottom))

        x,y = self.ct.matrix2sheet(self.just_out_right_idx,self.just_out_bottom_idx)
        self.assertFalse(self.box.contains(x,y))


    def test_matrix2sheet_center(self):
        """
        Check that the center in Sheet coordinates corresponds to
        the center in continuous matrix coordinates.
        """
        x_center = self.left+(self.right-self.left)/2.0
        y_center = self.bottom+(self.top-self.bottom)/2.0
        center_float_row = self.rbound/2.0
        center_float_col = self.cbound/2.0
        x,y = self.ct.matrix2sheet(center_float_row,center_float_col)
        self.assertEqual((x,y),(x_center,y_center))



    ### matrixidx2sheet() tests
    #
    def test_matrixidx2sheet_left_top(self):
        """
        The top-left matrix cell [0,0] should be given back in Sheet
        coordinates at the center of that cell.

        The cell [-1,-1] outside this corner should come back out of
        the BoundingBox
        """
        # inside
        r,c = 0,0
        x,y = self.left+self.half_unit,self.top-self.half_unit

        test_x, test_y = self.ct.matrixidx2sheet(r,c)
        self.assertEqual((test_x,test_y), (x,y))
        self.assertTrue(self.box.contains(test_x,test_y))

        # outside
        r,c = -1,-1
        test_x, test_y = self.ct.matrixidx2sheet(r,c)
        self.assertFalse(self.box.contains(test_x,test_y))


    def test_matrixidx2sheet_left_bottom(self):
        """
        The bottom-left matrix cell [0,rbound] should be given back
        in Sheet coordinates at the center of that cell.

        The cell [last_row+1,-1] outside this corner should come back out of
        the BoundingBox.
        """
        # inside
        r,c = self.last_row,0
        x,y = self.left+self.half_unit,self.bottom+self.half_unit
        self.assertEqual(self.ct.matrixidx2sheet(r,c), (x,y))

        # outside
        r,c = self.last_row+1,-1
        test_x, test_y = self.ct.matrixidx2sheet(r,c)
        self.assertFalse(self.box.contains(test_x,test_y))


    def test_matrixidx2sheet_right_top(self):
        """
        The top-right matrix cell [cbound,0] should be given back
        in Sheet coordinates at the center of that cell.

        The cell [-1,last_col+1] outside this corner should come back out of
        the BoundingBox.
        """
        # inside
        r,c = 0,self.last_col
        x,y = self.right-self.half_unit,self.top-self.half_unit
        self.assertEqual(self.ct.matrixidx2sheet(r,c), (x,y))

        # outside
        r,c = -1,self.last_col+1
        test_x, test_y = self.ct.matrixidx2sheet(r,c)
        self.assertFalse(self.box.contains(test_x,test_y))


    def test_matrixidx2sheet_right_bottom(self):
        """
        The bottom-right matrix cell [cbound,rbound] should be given back
        in Sheet coordinates at the center of that cell.

        The cell [last_row+1,last_col+1] outside this corner should come back out of
        the BoundingBox.
        """
        r,c = self.last_row,self.last_col
        x,y = self.right-self.half_unit,self.bottom+self.half_unit
        self.assertEqual(self.ct.matrixidx2sheet(r,c), (x,y))

        # outside
        r,c = self.last_row+1,self.last_col+1
        test_x, test_y = self.ct.matrixidx2sheet(r,c)
        self.assertFalse(self.box.contains(test_x,test_y))


    def test_matrixidx2sheet_center(self):
        """
        The row and col *index* of the center unit in the matrix should come
        back as the Sheet coordinates of the center of that center unit.
        """
        r,c = self.center_unit_idx
        x_center = self.left+(self.right-self.left)/2.0
        y_center = self.bottom+(self.top-self.bottom)/2.0
        x,y = x_center+self.half_unit, y_center-self.half_unit
        self.assertEqual(self.ct.matrixidx2sheet(r,c), (x,y))

    def test_matrixidx2sheet_sheet2matrixidx(self):
        """
        Check that sheet2matrixidx() is the inverse of matrix2sheetidx().
        """
        # top-right corner
        x,y = self.ct.matrixidx2sheet(float(0),float(self.last_col))
        top_row,right_col = self.ct.sheet2matrixidx(x,y)
        self.assertEqual((top_row,right_col),(float(0),float(self.last_col)))

        # bottom-left corner
        x,y = self.ct.matrixidx2sheet(float(self.last_row),float(0))
        bottom_row,left_col = self.ct.sheet2matrixidx(x,y)
        self.assertEqual((bottom_row,left_col),(float(self.last_row),float(0)))

@istest
class TestBox1Coordinates(TestCoordinateTransforms):
    """
    Test coordinate transformations using the standard, origin-centered unit box
    with density 10.

    A 10x10 matrix.
    """
    def setUp(self):
        self.left = -0.5
        self.bottom = -0.5
        self.top = 0.5
        self.right = 0.5
        self.density = 10
        self.half_unit = 0.05

        # for the matrix representation - I think having this manual statement is
        # safer than a calculation...
        self.last_row = 9
        self.last_col = 9
        self.center_unit_idx = (5,5)  # by the way sheet2matrixidx is defined

        self.makeBox()

@istest
class TestBox2Coordinates(TestCoordinateTransforms):
    """
    Test coordinate transformations on the box defined by (1,1), (3,4),
    with density 8.

    A 24 x 16 matrix.
    """
    def setUp(self):
        self.left = 1
        self.bottom = 1
        self.right = 3
        self.top  = 4
        self.density = 8
        self.half_unit = 0.0625

        # for the matrix representation - I think having this manual statement is
        # safer than a calculation...
        self.last_row = 23
        self.last_col = 15
        self.center_unit_idx = (12,8)  # by the way sheet2matrixidx is defined

        self.makeBox()

# CEB: unfinished and unused - still making tests for TestBox3Coordinates...

@nottest
class TestBox3Coordinates(TestCoordinateTransforms):
    def setUp(self):
        self.left = -0.8
        self.bottom = -0.8
        self.top = 0.8
        self.right = 0.8
        self.density = 16
        self.half_unit = 0.03125

        # for the matrix representation - I think having this manual statement is
        # safer than a calculation...
        self.last_row = 24
        self.last_col = 24
        self.center_unit_idx = (12,12)  # by the way sheet2matrixidx is defined

        self.makeBox()

@istest
class ExtraSheetTests(unittest.TestCase):
    """
    sheet tests that were written independently of the framework above.

    Each of these tests runs once and is independent of the rest of the file.
    """

    def test_slice2bounds_bounds2slice(self):

        bb = BoundingBox(points=((-0.5,-0.5),(0.5,0.5)))
        ct = SheetCoordinateSystem(bb,10)

        slice_ =(0,3,7,8)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        slice_ =(4,7,8,10)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        slice_ =(2,3,4,8)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        slice_ =(0,3,9,10)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        bb = BoundingBox(points=((-0.75,-0.5),(0.75,0.5)))
        ct = SheetCoordinateSystem(bb,20,20)

        slice_ =(9,14,27,29)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        slice_ =(0,6,0,7)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        slice_ =(6,10,11,29)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        bb = BoundingBox(points=((-0.5,-0.5),(0.5,0.5)))
        ct = SheetCoordinateSystem(bb,7)

        slice_ =(4,7,2,3)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)

        slice_ =(0,7,0,7)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        test_slice = Slice(bounds,ct)

        for a,b in zip(slice_,test_slice):
            self.assertEqual(a,b)


    def test_coordinate_position(self):
        """
        these tests duplicate some of the earlier ones,
        except these use a matrix with non-integer
        (right-left) and (top-bottom). This is an important
        test case for the definition of density; without it,
        the tests above could be passed by a variety of
        sheet2matrix, bounds2shape functions, etc.

        CEBALERT: transfer the box to TestBox3Coordinates and have
        these tests run in the framework.
        """
        l,b,r,t = (-0.8,-0.8,0.8,0.8)
        # mimics that a sheet recalculates its density)
        density = int(16*(r-l)) / float(r-l)

        bounds = BoundingBox(points=((l,b),(r,t)))

        ct = SheetCoordinateSystem(bounds,density,density)

        self.assertEqual(ct.sheet2matrixidx(0.8,0.8),(0,24+1))
        self.assertEqual(ct.sheet2matrixidx(0.0,0.0),(12,12))
        self.assertEqual(ct.sheet2matrixidx(-0.8,-0.8),(24+1,0))
        self.assertEqual(ct.matrixidx2sheet(24,0),
                         (((r-l) / int(density*(r-l)) / 2.0) + l,
                          (t-b) / int(density*(t-b)) / 2.0 + b))
        self.assertEqual(ct.matrixidx2sheet(0,0),
                         (((r-l) / int(density*(r-l)) / 2.0) + l ,
                          (t-b) / int(density*(t-b)) * (int(density*(t-b)) - 0.5) + b))

        x,y = ct.matrixidx2sheet(0,0)
        self.assertTrue(bounds.contains(x,y))
        self.assertEqual((0,0),ct.sheet2matrixidx(x,y))

        x,y = ct.matrixidx2sheet(25,25)
        self.assertFalse(bounds.contains(x,y))
        self.assertNotEqual((24,24),ct.sheet2matrixidx(x,y))

        x,y = ct.matrixidx2sheet(0,24)
        self.assertTrue(bounds.contains(x,y))
        self.assertEqual((0,24),ct.sheet2matrixidx(x,y))

        x,y = ct.matrixidx2sheet(24,0)
        self.assertTrue(bounds.contains(x,y))
        self.assertEqual((24,0),ct.sheet2matrixidx(x,y))


    def test_Sheet_creation(self):

        # Example where the nominal x and y densities would not be equal.
        # density along x =10
        # density along y <10
        # The density along y should become 10, by adjusting the height to be 2.0
        # in this case.
        # The y center of the bounds should remain -0.0025. Hence we should get
        # a bottom bound of -1.0025 and a top one of 0.9975.
        sheet = Sheet(nominal_density=10,
                      nominal_bounds=BoundingBox(points=((-0.5,-1.005),(0.5,1.0))))

        self.assertEqual(sheet.xdensity,10)
        self.assertEqual(sheet.xdensity,sheet.ydensity)

        l,b,r,t = sheet.lbrt
        self.assertEqual(l,-0.5)
        self.assertEqual(r,0.5)
        self.assertAlmostEqual(t,0.9975)
        self.assertAlmostEqual(b,-1.0025)



    # CEBALERT: this test should probably be somewhere else and
    # called something different
    def test_connection_field_like(self):
        # test a ConnectionField-like example
        sheet = Sheet(nominal_density=10,nominal_bounds=BoundingBox(radius=0.5))
        cf_bounds = BoundingBox(points=((0.3,0.3),(0.6,0.6)))

        slice_ = Slice(cf_bounds,sheet)
        slice_.crop_to_sheet(sheet)

        # check it's been cropped to fit onto sheet...
        self.assertEqual(slice_.tolist(),[0,2,8,10])

        # now check that it gives the correct bounds...
        cropped_bounds = slice_.compute_bounds(sheet)

        true_cropped_bounds = BoundingBox(points=((0.3,0.3),(0.5,0.5)))
        for a,b in zip(cropped_bounds.lbrt(),true_cropped_bounds.lbrt()):
            self.assertAlmostEqual(a,b)

        # and that bounds2shape() gets the correct size
#        rows,cols = bounds2shape(cropped_bounds,sheet.density,sheet.ydensity)
#        self.assertEqual((rows,cols),(2,2))


    def test_bounds2slice(self):

        # test that if you ask to slice the matrix with the sheet's BoundingBox, you
        # get back the whole matrix
        sheet_bb = BoundingBox(points=((-0.5,-0.5),(0.5,0.5)))
        ct = SheetCoordinateSystem(sheet_bb,10)

        slice_ = Slice(sheet_bb,ct)
        true_slice = (0,10,0,10) # inclusive left boundary, exclusive right boundary
        self.assertEqual(tuple(slice_.tolist()),true_slice)

        # for the following tests, the values have been all computed by hand and then
        # tested (by JC). The boundingbox and density tested have been chosen randomly,
        # then drawn to get the slice from it.

        # Test with 20 density.
        ct = SheetCoordinateSystem(sheet_bb,20,20)
        bb = BoundingBox(points=((-0.05,-0.20),(0.20,0.05)))
        slice_ = Slice(bb,ct)

        true_slice = (9,14,9,14)
        self.assertEqual(tuple(slice_.tolist()),true_slice)

        bb = BoundingBox(points=((-0.40,0),(-0.30,0.30)))
        slice_ = Slice(bb,ct)
        true_slice = (4,10,2,4)
        self.assertEqual(tuple(slice_.tolist()),true_slice)

        bb = BoundingBox(points=((0.15,0.10),(0.30,0.30)))
        slice_ = Slice(bb,ct)
        true_slice = (4,8,13,16)
        self.assertEqual(tuple(slice_.tolist()),true_slice)

        bb = BoundingBox(points=((-0.05,-0.45),(0.10,-0.25)))
        slice_ = Slice(bb,ct)
        true_slice = (15,19,9,12)
        self.assertEqual(tuple(slice_.tolist()),true_slice)

        # test with 7 density sheet.

        bb = BoundingBox(points=((-0.5+2.0/7.0,0.5-2.0/7.0),(-0.5+4.0/7.0,0.5)))
        ct = SheetCoordinateSystem(sheet_bb,7)

        slice_ = Slice(bb,ct)
        true_slice = (0,2,2,4)
        self.assertEqual(tuple(slice_.tolist()),true_slice)

        #(4x4 matrix)
        ct = SheetCoordinateSystem(BoundingBox(radius=0.2),xdensity=10,ydensity=10)
        test_bounds = BoundingBox(radius=0.1)
        slice_=Slice(test_bounds,ct)
        r1,r2,c1,c2 = slice_
        self.assertEqual((r1,r2,c1,c2),(1,3,1,3))

        # Note: this test fails because units that fall on the
        # boundaries should all be included; bounds2slice does not
        # include the ones on the left boundary because of floating point
        # representation.
        #test_bounds.translate(0.05,-0.05)
        #r1,r2,c1,c2 = ct.bounds2slice(test_bounds)
        #self.assertEqual((r1,r2,c1,c2),(1,4,1,4))


    def test_slice2bounds(self):

        # test that if you ask to slice the matrix with the sheet's BoundingBox, you
        # get back the whole matrix
        # (I chose to use a 7 density, I don't know why I like 7 so much, it is kind of mystical)

        sheet_bb = BoundingBox(points=((-0.5,-0.5),(0.5,0.5)))
        ct = SheetCoordinateSystem(sheet_bb,7)
        slice_ = (0,7,0,7)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        true_bounds_lbrt = (-0.5,-0.5,0.5,0.5)
        for a,b in zip(bounds.lbrt(),true_bounds_lbrt):
            self.assertAlmostEqual(a,b)

        # for the following tests, the values have been all computed
        # by hand and then tested (by JC). The boundingbox and density
        # tested have been chosen randomly, then drawn to get the slice
        # from it.

        # Test for 10 density
        ct = SheetCoordinateSystem(sheet_bb,10)
        slice_ = (0,9,1,5)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        true_bounds_lbrt = (-0.4,-0.4,0,0.5)
        for a,b in zip(bounds.lbrt(),true_bounds_lbrt):
            self.assertAlmostEqual(a,b)

        slice_ = (2,3,7,10)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        true_bounds_lbrt = (0.2,0.2,0.5,0.3)
        for a,b in zip(bounds.lbrt(),true_bounds_lbrt):
            self.assertAlmostEqual(a,b)

        # Test for 7 density
        ct = SheetCoordinateSystem(sheet_bb,7)
        slice_ = (3,7,2,5)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        true_bounds_lbrt = (-0.5+2.0/7.0,-0.5,-0.5+5.0/7.0,0.5-3.0/7.0)
        for a,b in zip(bounds.lbrt(),true_bounds_lbrt):
            self.assertAlmostEqual(a,b)

        slice_ = (2,6,0,1)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        true_bounds_lbrt = (-0.5,0.5-6.0/7.0,-0.5+1.0/7.0,0.5-2.0/7.0)
        for a,b in zip(bounds.lbrt(),true_bounds_lbrt):
            self.assertAlmostEqual(a,b)

        # Test for 25 density
        ct = SheetCoordinateSystem(sheet_bb,25)
        slice_ = (0,25,4,10)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        true_bounds_lbrt = (-0.5+4.0/25.0,-0.5,-0.5+10.0/25.0,0.5)
        for a,b in zip(bounds.lbrt(),true_bounds_lbrt):
            self.assertAlmostEqual(a,b)


        slice_ = (7,18,3,11)
        bounds = BoundingBox(points=Slice._slicespec2boundsspec(slice_,ct))
        true_bounds_lbrt = (-0.5+3.0/25.0,0.5-18.0/25.0,-0.5+11.0/25.0,0.5-7.0/25.0)
        for a,b in zip(bounds.lbrt(),true_bounds_lbrt):
            self.assertAlmostEqual(a,b)


##     # bounds2shape() tests
##     #
##     def test_bounds2shape(self):
##         """
##         Check that the shape of the matrix based on the BoundingBox and
##         density is correct.
##         """
##         n_rows,n_cols = bounds2shape(self.box,self.density)
##         self.assertEqual((n_rows,n_cols),(self.last_row+1,self.last_col+1))


    def test_sheetview_release(self):
        s = Sheet()
        s.activity = np.array([[1,2],[3,4]])
        # Call s.sheet_view(..) with a parameter
        sv2 = SheetView(s.activity,bounds=s.bounds)
        sv2.metadata = dict(src_name=s.name)
        self.assertEqual(len(s.views.Maps.keys()),0)
        s.views.Maps['Activity']=sv2
        self.assertEqual(len(s.views.Maps.keys()),1)
        s.release_sheet_view('Activity')
        self.assertEqual(len(s.views.Maps.keys()),0)

if __name__ == "__main__":
	import nose
	nose.runmodule()
