"""

$Id$
"""
__version__='$Revision$'

# CEBHACKALERT: we should delete this file, right?

import unittest

from numpy.oldnumeric import array, Float32

# Currently empty; should be expanded
cases = []

suite = unittest.TestSuite()
suite.addTests(unittest.makeSuite(case) for case in cases)
              
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=1).run(suite)
    


        
