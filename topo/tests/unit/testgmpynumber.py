import os, sys
sys.path = [os.path.join(os.getcwd(), '..', '..', '..', 'external', 'param')] + sys.path

import unittest
import param

from nose.plugins.skip import SkipTest
try:
    import gmpy
except ImportError:
    raise SkipTest("No gmpy module: testgmpynumber.txt skipped") 

mpq = gmpy.mpq

class TestGMPY(unittest.TestCase):

    def setUp(self):
        
        class TestPO1(param.Parameterized):
            z = param.Number(default=mpq(1),bounds=(-1,1))

        self.t1 = TestPO1()

    def testNumberAcceptsmpq(self):
        ### Check Number accepts gmpy.mpq
        assert isinstance(self.t1.z,type(mpq(1))) and self.t1.z==1
    
        try:
            self.t1.z+=1
        except ValueError:
            pass
        else:
            raise AssertionError("Number's bounds were not respected.")

    def testGMPWorks(self):
        ### Check gmpy works for simulation time
        import topo
        original_type = topo.sim.time.time_type
        topo.sim.initialized=False
        assert topo.sim.time(0.0, time_type = mpq) == mpq(0,1)
        self.t1.z = mpq(0.999)
        self.t1.z-=topo.sim.convert_to_time_type(0.0004)
        assert self.t1.z == mpq(4993,5000)
        topo.sim.time(0.0, time_type = original_type)
        topo.sim.initialized=True


