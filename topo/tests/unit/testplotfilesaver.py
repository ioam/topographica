"""
Tests for the PlotFileSaver classes. Also tests analysis commands.
"""

import unittest
import os
import tempfile
import shutil
import glob

from param import normalize_path

from topo.base.simulation import Simulation
from topo.base.cf import CFSheet, CFProjection
from topo.sheet import GeneratorSheet

from topo.plotting.plotgroup import save_plotgroup


import __main__
exec "from topo.command.analysis import *" in __main__.__dict__

from nose.tools import istest, nottest

@nottest
class TestPlotGroupSaverBase(unittest.TestCase):

    def exists(self,name):
        target = os.path.join(normalize_path.prefix,name)
        files = glob.glob(os.path.join(normalize_path.prefix,"*"))
        self.assert_(os.path.exists(target),
                     "'%s' not among '%s'"%(os.path.basename(target),
                                            [os.path.basename(f) for f in files]))

    def setUp(self):
        self.original_output_path = normalize_path.prefix
        normalize_path.prefix = tempfile.mkdtemp()
        self.sim = Simulation(register=True,name="testplotfilesaver")
        self.sim['A'] = GeneratorSheet(nominal_density=2)
        self.sim['B'] = CFSheet(nominal_density=2)
        self.sim.connect('A','B',connection_type=CFProjection,name='Afferent')

    def tearDown(self):
        shutil.rmtree(normalize_path.prefix)
        normalize_path.prefix = self.original_output_path

@istest
class TestPlotGroupSaver(TestPlotGroupSaverBase):

    def test_activity_saving(self):
        save_plotgroup('Activity')
        self.exists("testplotfilesaver_000000.00_A_Activity.png")
        self.exists("testplotfilesaver_000000.00_B_Activity.png")

    def test_orientation_preference_saving(self):
        save_plotgroup('Orientation Preference')
        self.exists("testplotfilesaver_000000.00_B_Orientation_Preference.png")
        self.exists("testplotfilesaver_000000.00_B_Orientation_PreferenceAndSelectivity.png")
        self.exists("testplotfilesaver_000000.00_B_Orientation_Selectivity.png")
        self.exists("testplotfilesaver_000000.00__Color_Key.png")

    def test_cf_saving(self):
        save_plotgroup("Connection Fields",sheet=self.sim['B'])
        self.exists("testplotfilesaver_000000.00_Afferent.png")

@istest
class TestCFProjectionPlotGroupSaver(TestPlotGroupSaverBase):

    def test_cfprojection_saving(self):
        save_plotgroup('Projection',
                       projection=self.sim['B'].projections('Afferent'))
        self.exists("testplotfilesaver_000000.00_B_Afferent.png")


###########################################################

if __name__ == "__main__":
	import nose
	nose.runmodule()