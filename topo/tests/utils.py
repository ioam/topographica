"""
Utility functions used by the test files.
"""

# CEB: note these from numpy 1.4 - might be handy:
#
# #. assert_array_almost_equal_nulps: new method to compare two arrays of
#    floating point values. With this function, two values are considered
#    close if there are not many representable floating point values in
#    between, thus being more robust than assert_array_almost_equal when the
#    values fluctuate a lot.
#
# #. assert_array_max_ulp: raise an assertion if there are more than N
#    representable numbers between two floating point values.


from numpy.testing import assert_array_equal,assert_array_almost_equal

def assert_array_not_equal(a1,a2,msg=""):
    try:
        assert_array_equal(a1,a2)
    except AssertionError:
        pass
    else:
        raise AssertionError(msg)


def array_almost_equal(*args,**kw):
    try:
        assert_array_almost_equal(*args,**kw)
        return True
    except AssertionError:
        return False

# temp

# this kind of thing is done all over the tests;
# could change to use this function (if the test
# actually needs a new simulation).
#

def new_simulation(name=None,register=True):

    from topo.base.simulation import Simulation
    from topo.base.cf import CFSheet,CFProjection
    from topo.sheet import GeneratorSheet
    from topo.base.boundingregion import BoundingBox

    sim=Simulation(register=register,name=name)
    b= BoundingBox(radius=0.5)
    sim['GS']=GeneratorSheet(nominal_density=2,nominal_bounds=b)
    sim['GS2']=GeneratorSheet(nominal_density=2,nominal_bounds=b)
    sim['S'] = CFSheet(nominal_density=2,nominal_bounds=b)
    sim['S2'] = CFSheet(nominal_density=2,nominal_bounds=b)
    sim.connect('GS','S',connection_type=CFProjection,delay=0.05)
    sim.connect('GS','S2',connection_type=CFProjection,delay=0.05)
    sim.connect('GS2','S2',connection_type=CFProjection,delay=0.05)
    return sim



class Series(object):
    """
    When called, return the next int from the series start,
    start+step, start+step+step, ...

    Used in tests that need predictable dynamic numbers.
    """
    def __init__(self,start=0,step=1):
        self.value = start
        self.step = step
        self.generator=self._generate()

    def _generate(self):
        while True:
            yield self.value
            self.value+=self.step

    def __call__(self):
        return self.generator.next()

