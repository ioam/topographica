"""
Test cases for the numbergen module.

$Id$
"""

import unittest
from topo import numbergen


_seed = 0  # keep tests deterministic
_iterations = 1000


class TestUniformRandom(unittest.TestCase):
    def test_range(self):
        lbound = 2.0
        ubound = 5.0
        gen = numbergen.UniformRandom(
                seed=_seed,
                lbound=lbound,
                ubound=ubound)
        for _ in xrange(_iterations):
            value = gen()
            self.assertTrue(lbound <= value < ubound)

class TestUniformRandomOffset(unittest.TestCase):
    def test_range(self):
        lbound = 2.0
        ubound = 5.0
        gen = numbergen.UniformRandomOffset(
                seed=_seed,
                mean=(ubound + lbound) / 2,
                range=ubound - lbound)
        for _ in xrange(_iterations):
            value = gen()
            self.assertTrue(lbound <= value < ubound)


cases = [
            TestUniformRandom,
            TestUniformRandomOffset,
        ]

suite = unittest.TestSuite()

suite.addTests([unittest.makeSuite(case) for case in cases])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=1).run(suite)
