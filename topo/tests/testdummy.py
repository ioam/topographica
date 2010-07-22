"""
$Id$
"""

### JCALERT: Does this file is of any interrest now?

__version__='$Revision$'

import unittest

class TestDummy(unittest.TestCase):
    def test_add(self):
        self.assertEqual(1+1,2)



suite = unittest.TestSuite()
#  Uncomment the following line of code, to disable the test if
#  $DISPLAY is undefined.  Used mainly for GUI testing.
# suite.requires_display = True
suite.addTest(unittest.makeSuite(TestDummy))
