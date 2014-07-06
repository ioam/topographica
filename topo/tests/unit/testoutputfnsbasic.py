"""
TestFeatureMap
"""


# To do:
# - Remove the commented line from when it was calling a function
# - finish to transform the call to be to a procedure in the last test
# - Also clean up the original file to this purpose


import unittest
import copy

from topo.transferfn import PiecewiseLinear, DivisiveNormalizeL1
from topo.transferfn import DivisiveNormalizeL2, DivisiveNormalizeLinf
from topo.transferfn import DivisiveNormalizeLp, HomeostaticMaxEnt

import numpy as np
from numpy.testing import assert_array_equal
from math import sqrt

from topo.tests.utils import assert_array_not_equal

class TestPiecewiseLinear(unittest.TestCase):

    def setUp(self):

        self.a1 = np.array([[0.5,-1.0,0.99],
                            [1.001,-0.001,0.6]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,11.0]])

        self.fn1 = PiecewiseLinear()
        self.fn2 = PiecewiseLinear(lower_bound = 0.1,upper_bound = 0.5)
        self.fn3 = PiecewiseLinear(lower_bound = 0, upper_bound = 10.0)

    def test_piecewiselinear(self):
        # Test as a procedure

        fn1_a1 = np.array([[0.5,0.0,0.99],
                           [1.0,0.0,0.6]])

        fn2_a1 = np.array([[1.0, 0.0, 1.0],
                           [1.0,0.0, 1.0]])

        fn3_a2 = np.array([[0.1,0.0,0.7],
                           [0.4,0.3,1.0]])


        self.fn1(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn1_a1.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.a1 = np.array([[0.5,-1.0,0.99],
                            [1.001,-0.001,0.6]])
        self.fn2(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn2_a1.ravel()):
            self.assertAlmostEqual(item1, item2)


        self.fn3(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn3_a2.ravel()):
            self.assertAlmostEqual(item1, item2)


class TestDivisiveNormalizeL1(unittest.TestCase):

    def setUp(self):

        self.a1 = np.array([[0.3,0.6,0.7],
                            [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,11.0]])

        self.fn1 = DivisiveNormalizeL1()
        self.fn2 = DivisiveNormalizeL1(norm_value=4.0)

    def test_divisive_sum_normalize(self):
        # Test as a procedure

        fn1_a1 = self.a1/3.0

        fn1_a2 = self.a2/27.0

        fn2_a1 = (self.a1/3.0)*4.0

        fn2_a2 = (self.a2/27.0)*4.0


        self.fn1(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn1_a1.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.fn1(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn1_a2.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.a1 = np.array([[0.3,0.6,0.7],
                            [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,11.0]])

        self.fn2(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn2_a1.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.fn2(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn2_a2.ravel()):
            self.assertAlmostEqual(item1, item2)


class TestDivisiveLengthNormalize(unittest.TestCase):

    def setUp(self):

        self.a1 = np.array([[0.3,0.6,0.7],
                            [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,11.0],
                            [2.0,5.0,9.0]])

        self.fn1 = DivisiveNormalizeL2()
        self.fn2 = DivisiveNormalizeL2(norm_value=4.0)

    def test_divisive_length_normalize(self):
        # Test as a procedure

        eucl_norm_a1 = sqrt(0.3**2+0.6**2+0.7**2+0.8**2+0.4**2+0.2**2)
        # eucl_norm_a2 = sqrt(307)

        fn1_a1 = self.a1/eucl_norm_a1
        fn1_a2 = self.a2/sqrt(307)
        fn2_a1 = (self.a1/eucl_norm_a1)*4.0
        fn2_a2 = (self.a2/sqrt(307))*4.0


        self.fn1(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn1_a1.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.fn1(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn1_a2.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.a1 = np.array([[0.3,0.6,0.7],
                            [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,11.0],
                            [2.0,5.0,9.0]])


        self.fn2(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn2_a1.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.fn2(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn2_a2.ravel()):
            self.assertAlmostEqual(item1, item2)


class TestDivisiveMaxNormalize(unittest.TestCase):

    def setUp(self):

        self.a1 = np.array([[0.3,0.6,0.7],
                            [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,-11.0],
                            [2.0,5.0,9.0]])

        self.fn1 = DivisiveNormalizeLinf()
        self.fn2 = DivisiveNormalizeLinf(norm_value=3.0)

    def test_divisive_max_normalize(self):
        # Test as a procedure:

        fn1_a1 = self.a1/0.8
        fn1_a2 = self.a2/11.0
        fn2_a1 = (self.a1/0.8)*3.0
        fn2_a2 = (self.a2/11.0)*3.0


        self.fn1(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn1_a1.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.fn1(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn1_a2.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.a1 = np.array([[0.3,0.6,0.7],
                            [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,-11.0],
                            [2.0,5.0,9.0]])

        self.fn2(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn2_a1.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.fn2(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn2_a2.ravel()):
            self.assertAlmostEqual(item1, item2)


class TestDivisiveLpNormalize(unittest.TestCase):

    def setUp(self):

        self.a1 = np.array([[0.3,0.6,0.7],
                            [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                            [4.0,3.0,-11.0],
                            [2.0,5.0,9.0]])

        # The default value of p is 2, so in this case, same as L2
        self.fn1 = DivisiveNormalizeLp()
        self.fn2 = DivisiveNormalizeLp(p=3.0)
        self.fn3 = DivisiveNormalizeLp(p=4.0,norm_value=2.0)

    def test_divisive_lp_normalize(self):

        ### JCALERT! As already said above; this method does not work as a procedure
        ### because of a problem when using x *= factor instead of x = x * factor
        ### it is not understood why because it does work fine in all others transferfn?
        ### Therefore it is only tested as a function

        # Test as a function

        eucl_norm_a1 = sqrt(0.3**2+0.6**2+0.7**2+0.8**2+0.4**2+0.2**2)

        fn1_a1 = self.a1/eucl_norm_a1
        fn1_a2 = self.a2/sqrt(307)

        l3norm_a1 = pow(0.3**3+0.6**3+0.7**3+0.8**3+0.4**3+0.2**3,1.0/3.0)
        l3norm_a2 = pow(2.0+7.0**3+4.0**3+3.0**3+11.0**3+2.0**3+5.0**3+9.0**3,1.0/3.0)
        fn2_a1 = self.a1/l3norm_a1
        fn2_a2 = self.a2/l3norm_a2

        self.fn1(self.a1)
        self.fn1(self.a2)
        for item1,item2 in zip(self.a1.ravel(),fn1_a1.ravel()):
            self.assertAlmostEqual(item1, item2)
        for item1,item2 in zip(self.a2.ravel(),fn1_a2.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.a1 = np.array([[0.3,0.6,0.7],
                        [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                         [4.0,3.0,-11.0],
                         [2.0,5.0,9.0]])

        self.fn2(self.a1)
        self.fn2(self.a2)
        for item1,item2 in zip(self.a1.ravel(),fn2_a1.ravel()):
            self.assertAlmostEqual(item1, item2)
        for item1,item2 in zip(self.a2.ravel(),fn2_a2.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.a1 = np.array([[0.3,0.6,0.7],
                        [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                         [4.0,3.0,-11.0],
                         [2.0,5.0,9.0]])

        l4norm_a1 = pow(0.3**4.0+0.6**4.0+0.7**4.0+0.8**4.0+0.4**4.0+0.2**4.0,1.0/4.0)
        l4norm_a2 = pow(1.0**4.0+1.0**4.0+7.0**4.0+4.0**4.0+3.0**4.0+11.0**4.0+2.0**4.0+5.0**4.0+9.0**4.0,1.0/4.0)
        fn3_a1 = (self.a1/l4norm_a1)*2.0
        fn3_a2 = (self.a2/l4norm_a2)*2.0


        self.fn3(self.a1)
        self.fn3(self.a2)
        for item1,item2 in zip(self.a1.ravel(),fn3_a1.ravel()):
            self.assertAlmostEqual(item1, item2)
        for item1,item2 in zip(self.a2.ravel(),fn3_a2.ravel()):
            self.assertAlmostEqual(item1, item2)

        # The rest of this procedure might be redundant (already covered above)

        self.a1 = np.array([[0.3,0.6,0.7],
                        [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                         [4.0,3.0,-11.0],
                         [2.0,5.0,9.0]])


        self.fn1(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn1_a1.ravel()):
            self.assertAlmostEqual(item1, item2)
        self.fn1(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn1_a2.ravel()):
            self.assertAlmostEqual(item1, item2)

        self.a1 = np.array([[0.3,0.6,0.7],
                        [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                         [4.0,3.0,-11.0],
                         [2.0,5.0,9.0]])

        self.fn2(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn2_a1.ravel()):
            self.assertAlmostEqual(item1, item2)
        self.fn2(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn2_a2.ravel()):
            self.assertAlmostEqual(item1, item2)



        self.a1 = np.array([[0.3,0.6,0.7],
                        [0.8,0.4,0.2]])

        self.a2 = np.array([[1.0,-1.0,7.0],
                         [4.0,3.0,-11.0],
                         [2.0,5.0,9.0]])

        self.fn3(self.a1)
        for item1,item2 in zip(self.a1.ravel(),fn3_a1.ravel()):
            self.assertAlmostEqual(item1, item2)
        self.fn3(self.a2)
        for item1,item2 in zip(self.a2.ravel(),fn3_a2.ravel()):
            self.assertAlmostEqual(item1, item2)



class TestTransferFnWithRandomState(unittest.TestCase):
    """Currently just tests whether random generator state is handled
    by state_push() and state_pop()."""

    def setUp(self):

        self.a = np.array([[0.3,0.6,0.7],
                        [0.8,0.4,0.2]])

        self.hme = HomeostaticMaxEnt()

    def test_random_state(self):

        a1 = copy.copy(self.a)

        ###
        # CEBALERT: hack because homeostaticmaxent doesn't get some
        # of its state until it's been called once!
        self.hme(a1)

        start_array = copy.copy(a1)

        ## save the state then generate some results...
        self.hme.state_push()

        self.hme(a1)
        res1 = copy.copy(a1)
        self.hme(a1)
        res2 = copy.copy(a1)

        # (check results do actually change so the test is valid)
        assert_array_not_equal(res1,res2)

        a2 = copy.copy(start_array)

        ### ...then restore the state & check results are the same
        self.hme.state_pop()
        self.hme(a2)
        assert_array_equal(a2,res1)

        self.hme(a2)
        assert_array_equal(a2,res2)

if __name__ == "__main__":
	import nose
	nose.runmodule()
