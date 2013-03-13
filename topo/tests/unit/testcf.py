import unittest
import numpy

from topo.base.simulation import Simulation
from topo.base.boundingregion import BoundingBox
from topo.base.cf import CFIter,ResizableCFProjection,CFSheet

class TestCFIter(unittest.TestCase):

    iter_type = CFIter

    def setUp(self):

        self.sim = Simulation()

        self.sim['Dest'] = CFSheet(nominal_density=10,nominal_bounds=BoundingBox(radius=0.5))
        self.sim['Src'] = CFSheet(nominal_density=10,nominal_bounds=BoundingBox(radius=0.5))

        self.sim.connect('Src','Dest',
                         connection_type = ResizableCFProjection,
                         )

    def test_iterate_all(self):
        """
        Test to make sure the iterator hits every CF
        """
        total = 0
        dest = self.sim['Dest']
        proj = dest.projections()['SrcToDest']
        rows,cols = dest.shape
        iterator = self.iter_type(proj)
        for cf,i in iterator():
            total += 1
            self.failUnless(0 <= i < 100, "CFIter generated bogus CF index")
            cfxy = (proj.X_cf.flat[i],proj.Y_cf.flat[i])
            r,c = i/cols,i%cols
            self.failUnlessEqual(cfxy,dest.matrixidx2sheet(r,c))
        self.failUnlessEqual(total,100)


    def test_iterate_some_nil(self):
        """
        Test to make sure iterator skips nil CFs (i.e cf == None)
        """
        dest = self.sim['Dest']
        proj = dest.projections()['SrcToDest']
        total = 0
        proj.flatcfs[24] = None
        for cf,i in self.iter_type(proj)():
            total += 1
            self.failIfEqual(i,24)
        self.failUnlessEqual(total,99)


    def test_iterate_masked(self):
        """
        Test if iterator skips masked CFs
        """
        total = 0
        dest = self.sim['Dest']
        proj = dest.projections()['SrcToDest']
        dest.mask.data = numpy.zeros(dest.activity.shape)
        dest.mask.data.flat[24] = 1
        for cf,i in self.iter_type(proj)():
            total += 1
            self.failUnlessEqual(i,24)
            self.failUnless(cf is proj.flatcfs[24])
        self.failUnlessEqual(total,1)

if __name__ == "__main__":
	import nose
	nose.runmodule()