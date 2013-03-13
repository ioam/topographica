"""
Tests PatternGenerator (position and orientation), and some of the
basic patterns.
"""

import unittest

from numpy.oldnumeric import array, pi
from numpy.oldnumeric.mlab import rot90
from numpy.testing import assert_array_equal

from topo.base.patterngenerator import Constant,PatternGenerator
from topo.base.boundingregion import BoundingBox

from topo.pattern import Rectangle,Gaussian,Composite,Selector
from topo import numbergen


class TestPatternGenerator(unittest.TestCase):

    def test_a_basic_patterngenerator(self):
        pattern_bounds = BoundingBox(points=((0.3,0.2),(0.5,0.5)))

        pattern_target = array([[1,1],
                                [1,1],
                                [1,1]])

        r = Rectangle(bounds=pattern_bounds,xdensity=10,
                      ydensity=10,aspect_ratio=1,size=1,smoothing=0.0)
        assert_array_equal(r(),pattern_target)


    def test_constant(self):
        """
        Constant overrides PatternGenerator's usual matrix creation.
        """
        pattern_bounds = BoundingBox(points=((0.3,0.2),(0.5,0.5)))

        pattern_target = array([[1,1],
                                [1,1],
                                [1,1]])

        c = Constant(bounds=pattern_bounds,xdensity=10.0,ydensity=10)
        assert_array_equal(c(),pattern_target)


    def test_position(self):
        """
        Test that a pattern is drawn correctly at different
        locations.
        """

        initial = array([[0,0,0,0],
                         [0,1,1,0],
                         [0,1,1,0],
                         [0,0,0,0]])

        r = Rectangle(bounds=BoundingBox(radius=2),xdensity=1,
                      ydensity=1,aspect_ratio=1,size=2,smoothing=0.0)
        assert_array_equal(r(),initial)

        ### x offset
        x_offset = array([[0,0,0,0],
                          [0,0,1,1],
                          [0,0,1,1],
                          [0,0,0,0]])

        assert_array_equal(r(x=1),x_offset)

        ### y offset
        y_offset = rot90(x_offset)
        assert_array_equal(r(y=1),y_offset)

        ### x and y offset
        target = array([[0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [1,1,0,0,0,0,0,0,0,0],
                        [1,1,0,0,0,0,0,0,0,0],
                        [1,1,0,0,0,0,0,0,0,0],
                        [1,1,0,0,0,0,0,0,0,0]])

        width  = 0.2
        height = 0.4

        r = Rectangle(bounds=BoundingBox(radius=0.5),
                      xdensity=10,ydensity=10,smoothing=0.0,
                      aspect_ratio=width/height,size=height)

        assert_array_equal(r(x=-0.4,y=-0.3),target)

        ### x and y offset with bounds offset by the same
        target = array([[0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,1,1,0,0,0,0],
                        [0,0,0,0,1,1,0,0,0,0],
                        [0,0,0,0,1,1,0,0,0,0],
                        [0,0,0,0,1,1,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0,0]])

        width  = 0.2
        height = 0.4

        bounds = BoundingBox(points=((-0.9,-0.8),(0.1,0.2)))
        r = Rectangle(bounds=bounds,xdensity=10,ydensity=10,smoothing=0.0,
                      aspect_ratio=width/height,size=height)

        assert_array_equal(r(x=-0.4,y=-0.3),target)



    def test_orientation_and_rotation(self):
        """
        Test that a pattern is drawn with the correct orientation,
        and is rotated correctly.
        """
        ### Test initial orientation and 90-degree rotation
        target = array([[0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 0, 0],
                        [0, 0, 1, 1, 0, 0],
                        [0, 0, 1, 1, 0, 0],
                        [0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0]])

        bounds = BoundingBox(radius=0.3)
        xdensity = 10
        ydensity = 10
        width = 2.0/xdensity
        height = 4.0/ydensity

        rect = Rectangle(size=height,
                         aspect_ratio=width/height,smoothing=0.0,
                         xdensity=xdensity,ydensity=ydensity,bounds=bounds)

        assert_array_equal(rect(),target)
        assert_array_equal(rect(orientation=pi/2),rot90(target))


        ### 45-degree rotation about the origin
        rot_45 = array([[0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0],
                        [0, 1, 1, 1, 0, 0],
                        [0, 0, 1, 1, 1, 0],
                        [0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0]])

        assert_array_equal(rect(orientation=pi/4),rot_45)


        ### 45-degree rotation that's not about the origin
        rot_45_offset = array([[0, 1, 0, 0, 0, 0],
                               [1, 1, 1, 0, 0, 0],
                               [0, 1, 1, 1, 0, 0],
                               [0, 0, 1, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0]])

        assert_array_equal(rect(x=-1.0/xdensity,y=1.0/ydensity,orientation=pi/4),
                           rot_45_offset)



    def test_composite_pattern_basic(self):
        """
        Test that a composite pattern consisting of just one Gaussian
        is the same as that actual Gaussian pattern, and that a
        composite pattern of two rectangles is the same as adding the
        two individual matrices.
        """
        bbox=BoundingBox(radius=0.5)
        g = Gaussian(size=0.2,aspect_ratio=0.5,orientation=0,x=0.2,y=-0.03)
        c = Composite(generators=[g],bounds=bbox,xdensity=7,ydensity=7)
        assert_array_equal(g(bounds=bbox,xdensity=7,ydensity=7),c())

        r1=Rectangle(size=0.2,aspect_ratio=1,x=0.3,y=0.3,orientation=0,smoothing=0.0)
        r2=Rectangle(size=0.2,aspect_ratio=1,x=-0.3,y=-0.3,orientation=0,bounds=BoundingBox(radius=0.8),xdensity=2,smoothing=0.0)
        c_true = r1(bounds=bbox,xdensity=7,ydensity=7)+r2(bounds=bbox,xdensity=7,ydensity=7)
        c = Composite(generators=[r1,r2],bounds=bbox,xdensity=7,ydensity=7)
        assert_array_equal(c(),c_true)


    def test_composite_pattern_moves(self):
        """
        Test that moving a composite pattern yields the correct pattern.
        """
        bbox=BoundingBox(radius=0.5)
        g = Gaussian(size=0.2,aspect_ratio=0.5,orientation=pi/3,x=0,y=0)
        c = Composite(generators=[g],x=-0.3,y=0.4,xdensity=4,ydensity=4,bounds=bbox)
        g_moved = g(x=-0.3,y=0.4,xdensity=4,ydensity=4,bounds=bbox)

        assert_array_equal(c(),g_moved)

    # Should also test rotating, resizing...


    def test_bug__dynamic_param_advanced_by_repr(self):
        """Check for bug where repr of a PatternGenerator causes a DynamicNumber to change."""
        # CEB: can probably remove this test now we have time-controlled dynamic parameters
        import topo

        p=PatternGenerator(x=numbergen.UniformRandom(lbound=-1,ubound=1,seed=1))

        x0 = p.x
        topo.sim.run(1)
        x1 = p.x
        self.assertNotEqual(x0,x1) # check we have setup something that actually changes

        x2 = p.inspect_value('x')
        repr(p)
        x3 = p.inspect_value('x')
        self.assertEqual(x2,x3) # value of x should not have been changed by repr(p)



# CB: does not test most featurs of Selector!
class TestSelector(unittest.TestCase):

    def setUp(self):
        self.g1 = Gaussian(x=numbergen.UniformRandom())
        self.g2 = Gaussian(x=numbergen.UniformRandom())
        self.s = Selector(generators=[self.g1,self.g2])
        self.s.set_dynamic_time_fn(None,'generators')

    def test_dynamic_index(self):
        """index should always vary"""
        self.assertNotEqual(self.s.index,self.s.index)

    def test_dynamic_inheritance(self):
        """time_fn should have been applied to subpatterns"""
        self.assertNotEqual(self.g1.x,self.g1.x)

if __name__ == "__main__":
	import nose
	nose.runmodule()