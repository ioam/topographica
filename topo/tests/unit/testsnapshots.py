import unittest, copy, shutil, tempfile
from numpy.testing import assert_array_equal

from param import normalize_path,resolve_path
import topo
import __main__

from topo.base.sheet import Sheet
from topo.sheet import GeneratorSheet
from topo.command import save_snapshot,load_snapshot
from topo.pattern import Gaussian, Line
from topo.base.simulation import Simulation,SomeTimer


SNAPSHOT_NAME = "testsnapshot.typ"
SIM_NAME = "testsnapshots"

class TestSnapshots(unittest.TestCase):

    # CB: all tests that use topo.sim ought to do make a new topo.sim
    def setUp(self):
        """
        Create a new Simulation as topo.sim (so this test isn't affected by changes
        to topo.sim by other tests).
        """
        Simulation(register=True,name=SIM_NAME)
        self.original_output_path = normalize_path.prefix
        normalize_path.prefix = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(normalize_path.prefix)
        normalize_path.prefix=self.original_output_path

    def basic_save_load_snapshot(self):
        """
        Very basic test to check the activity matrix of a GeneratorSheet
        comes back ok, and that class attributes are pickled.
        """
        assert topo.sim.name==SIM_NAME

        topo.sim['R']=GeneratorSheet(input_generator=Gaussian(),nominal_density=2)

        topo.sim.run(1)

        R_act = copy.deepcopy(topo.sim['R'].activity)
        Line.x = 12.0
        topo.sim.startup_commands.append("z=99")

        save_snapshot(SNAPSHOT_NAME)


        Line.x = 9.0
        exec "z=88" in __main__.__dict__

        topo.sim['R'].set_input_generator(Line())
        topo.sim.run(1)

        load_snapshot(resolve_path(SNAPSHOT_NAME,search_paths=[normalize_path.prefix]))


        # CEBALERT: should also test that unpickling order is correct
        # (i.e. startup_commands, class attributes, simulation)
        assert_array_equal(R_act,topo.sim['R'].activity)
        self.assertEqual(Line.x,12.0)
        self.assertEqual(__main__.__dict__['z'],99)



    def test_basic_save_load_snapshot(self):
        self.basic_save_load_snapshot()




    def test_new_simulation_still_works(self):

        #  Test to make sure the above tests haven't screwed up
        # the ability to construct new simulation objects
        topo.base.simulation.Simulation()


# CB: longer to run test should additionally quit the simulation
# and start again. Should also test scheduled actions.

if __name__ == "__main__":
	import nose
	nose.runmodule()