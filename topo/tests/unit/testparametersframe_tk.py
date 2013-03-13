"""
Tests for the ParametersFrame classes.
"""

import __main__
import unittest
import Tkinter

import param
import paramtk as tk

from topo.base.patterngenerator import PatternGenerator

# CEBALERT: will be replaced with call to param.tk.initialize() when
# param.tk doesn't depend on anything from tkgui.__init__ (plus this
# test will move to the param package...)
import os
from nose.plugins.skip import SkipTest

if os.getenv("DISPLAY"):
    import topo.tkgui
    topo.tkgui.start()
else: raise SkipTest("No DISPLAY found")


class TestPO(param.Parameterized):
    boo = param.Boolean(default=True)
    osp = param.ObjectSelector()
    csp = param.ClassSelector(class_=PatternGenerator)
    const = param.Parameter(1.0,constant=True)
    pa = param.Parameter(default="test")
    nu = param.Number(default=1.0,bounds=(-1,1))
    st = param.String("string1")



class TestParametersFrameWithApply(unittest.TestCase):


    def setUp(self):

        self.some_pos = [param.Parameterized(),param.Parameterized(),
                         param.Parameterized()]

        self.testpo1 = TestPO()
        self.testpo1.params()['osp'].objects = self.some_pos

        self.testpo2 = TestPO()
        self.testpo1.params()['osp'].objects = self.some_pos

        self.toplevel = Tkinter.Toplevel()
        self.f = tk.ParametersFrameWithApply(self.toplevel,self.testpo1)



    def test_set_PO(self):
        self.assertEqual(self.f._extraPO,self.testpo1)
        self.f.set_PO(self.testpo2)
        self.assertEqual(self.f._extraPO,self.testpo2)



    def test_apply_button_1(self):
        """
        Check:
          when pressing apply after no changes, objects should remain
          unchanged, and should still be displayed the same as before.
        """
        ## check that update doesn't affect the variable values
        orig_values = {}
        for param_name,tkvar in self.f._tkvars.items():
            orig_values[param_name] = tkvar._original_get()

        self.f.Apply()

        for param_name,val in orig_values.items():
            self.assertEqual(self.f._tkvars[param_name].get(),val)

        ## and check that *displayed* values don't change
        orig_values = {}
        for param_name,representation in self.f.representations.items():
            widget = representation['widget']

            # button-type widgets don't have a value
            widget_has_value = not 'command' in widget.config()

            if widget_has_value:
                orig_values[param_name] = widget.get()

        self.f.Apply()

        for param_name,val in orig_values.items():
            widget = self.f.representations[param_name]['widget']
            self.assertEqual(widget.get(),val)


    def test_apply_button_2(self):
        """
        Check:
          When code to instantiate an object is typed into the entry
          representing a Parameter, if that object exists in main it
          should be instantiated. Further, the display should NOT then
          include quote marks.

          (Only time should get quotation marks is when editing a
          Parameter and trying to create an instance of a class that
          hasn't been imported: then string is assumed, and quotes are
          added - since it's not a StringParameter.)

          Finally, check that when the string remains the same in a box
          that a new object is not instantiated each time Apply is pressed.
        """
        exec "from topo.tests.unit.testparametersframe_tk import TestPO" in __main__.__dict__
        w = self.f.representations['pa']['widget']
        w.delete(0,"end")
        w.insert(0,"TestPO()")
        self.f.Apply()
        content = w.get()
        self.assertEqual(type(self.f.pa),TestPO) # get the object?
        self.assertEqual(content[0:7],"TestPO(") # object displayed right?

        # Now check that pressing apply over and over does not
        # create a new object each time when the same string remains
        # in the widget
        testpo_id = id(self.f.pa)
        self.f.Apply()
        self.assertEqual(id(self.f.pa),testpo_id)
        # ...but that we do get a new object when the string really changes
        w.delete(0,"end")
        w.insert(0,"TestPO(name='fred')")
        self.f.Apply()
        self.assertNotEqual(id(self.f.pa),testpo_id)


    # (CB: this isn't the place for this test)
    def test_link_to_topo_sim(self):
        """Indicate there's a bug. Have yet to investigate where it actually comes from."""
        import topo
        from topo.tests.utils import new_simulation
        new_simulation()
        e = tk.edit_parameters(topo.sim['S'])
        e.gui_set_param('precedence',7)
        e.Apply()
        self.assertEqual(topo.sim['S'].precedence,7)
        # problem with Simulation no longer being singleton?



# CEBALERT: need test for defaults button. Check that works ok
# for non-instantiated params etc


# test apply disabling etc





###########################################################

if __name__ == "__main__":
	import nose
	nose.runmodule()