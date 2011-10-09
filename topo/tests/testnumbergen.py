"""
Test cases for the numbergen module.

$Id$
"""
__version__ = '$Revision$'

import unittest
from topo import numbergen


class TestUniformRandomMeanRange(unittest.TestCase):
    def test_lbound_ubound(self):
        lbound = 3.0
        ubound = 5.0
        d = numbergen.UniformRandom(lbound=lbound, ubound=ubound)
        self.assertEqual(d.lbound, lbound)
        self.assertEqual(d.ubound, ubound)

    def test_mean_range(self):
        d = numbergen.UniformRandom(mean=4.0, range=2.0)
        self.assertEqual(d.lbound, 3.0)
        self.assertEqual(d.ubound, 5.0)

    def test_default_mean(self):
        d = numbergen.UniformRandom(range=2.0)
        self.assertEqual(d.lbound, -1.0)
        self.assertEqual(d.ubound, 1.0)

    def test_lbound_ubound_mean_range(self):
        def f():
            numbergen.UniformRandom(lbound=1.0, ubound=2.0, mean=2.0)
        self.assertRaises(TypeError, f)


cases = [
            TestUniformRandomMeanRange,
        ]

suite = unittest.TestSuite()

suite.addTests([unittest.makeSuite(case) for case in cases])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=1).run(suite)
