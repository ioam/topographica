"""
Tests for the tkParameterized classes.
"""


## CB: add test for change of po


import __main__
import unittest
from Tkinter import Frame,Toplevel

import param
import paramtk as tk

from topo.base.simulation import Simulation
from topo.base.patterngenerator import PatternGenerator
from topo.base.sheet import Sheet

from topo.pattern import Gaussian, Ring, Rectangle
from topo.transferfn import PiecewiseLinear


# CEBALERT: will be replaced with call to param.tk.initialize() when
# param.tk doesn't depend on anything from tkgui.__init__ (plus this
# test will move to the param package...)
import os
from nose.plugins.skip import SkipTest
from nose.tools import istest, nottest

if os.getenv("DISPLAY"):
    import topo.tkgui
    topo.tkgui.start()
else: raise SkipTest("No DISPLAY found")

@nottest
class SomeFrame(tk.TkParameterized,Frame):
    boo = param.Boolean(default=True)
    osp = param.ObjectSelector()
    csp = param.ClassSelector(class_=PatternGenerator)
    const = param.Parameter(1.0,constant=True)
    pa = param.Parameter(default="test")
    nu = param.Number(default=1.0,bounds=(-1,1))
    st = param.String("string1")

    def __init__(self,master,extraPO=None,**params):
        tk.TkParameterized.__init__(self,master,extraPO=extraPO,**params)
        Frame.__init__(self,master)
        self.boocount=0

    def upboocount(self):
        self.boocount+=1

@nottest
class TestPO(param.Parameterized):
    bool_param = param.Boolean(default=False)


@istest
class TestTkParameterized(unittest.TestCase):


    def setUp(self):
        pass

    def test_basic(self):
        """
        Check basic setting and getting of attributes (via
        object.attribute and GUI set()/get()).
        """
        f = SomeFrame(Toplevel())
        f.pack()

        f.pack_param('const')

        f.pack_param('boo',on_set=f.upboocount)

        self.assertEqual(f.boo,True); self.assertEqual(f.boocount,0)

        f.boo = False
        self.assertEqual(f.boocount,1) # check that on_set was called
        self.assertEqual(f.boo,False)  # check that f.boo was set
        self.assertEqual(f._tkvars['boo'].get(),False) # simulate GUI get & check result


        f._tkvars['boo'].set(True) # simulate GUI set
        self.assertEqual(f.boocount,2) # check that on_set was called
        self.assertEqual(f.boo,True) # check that f.boo was actually set
        self.assertEqual(f._tkvars['boo'].get(),True) # simulate GUI get



    def test_basic_shadow(self):
        """
        Check shadowing of a PO's parameters.
        """
        t = TestPO()
        f = SomeFrame(Toplevel(),extraPO=t)
        f.pack()

        f.pack_param('bool_param') # (from the TestPO)

        # test that setting f.bool_param (where bool_param is
        # shadow of t.bool_param) actually sets t.bool_param
        self.assertEqual(t.bool_param,False) # so we know start state
        f.bool_param=True
        self.assertEqual(t.bool_param,True)

        # simulate a GUI set (typing then Return) & then and check
        # g.bool_param is set
        f._tkvars['bool_param'].set(False)
        self.assertEqual(t.bool_param,False)

        # check that up-to-date value is returned when g got changed elsewhere
        t.bool_param=True
        self.assertEqual(f.bool_param,True)

        # simulate a GUI get & check up-to-date value returned
        t.bool_param=False
        self.assertEqual(f._tkvars['bool_param'].get(),False)


        # CEB: the following doesn't work:
        #  self.assertRaises(AttributeError,f.does_not_exist)
        # An AttributeError *is* raised, but it doesn't seem to be
        # caught by testing mechanism. Below is equivalent test...
        try:
            f.does_not_exist
        except AttributeError:
            pass
        else:
            raise("Failed to raise AttributeError on looking up non-existent attribute 'does_not_exist'")

        f.did_not_exist = 9
        assert 'did_not_exist' in f.__dict__ # check that new attribute added to f's dict...
        self.assertEqual(f.did_not_exist,9)  # ...and that it was set





    def test_on_set(self):

        f = SomeFrame(Toplevel())

        self.z = 0
        f.pack_param('boo',on_set=self.upzcount)
        f.boo=True
        self.assertEqual(self.z,1)

        f._tkvars['boo'].set(True)
        self.assertEqual(self.z,2)


    def test_on_modify(self):

        f = SomeFrame(Toplevel(),boo=True)

        self.z = 0
        f.pack_param('boo',on_modify=self.upzcount)

        f._tkvars['boo'].set(True)
        self.assertEqual(self.z,0)

        f._tkvars['boo'].set(False)
        self.assertEqual(self.z,1)


    def upzcount(self): self.z+=1  # minor helper method



    def test_direct_getting_and_setting(self):
        """
        Test the methods used to set and get Parameter values.
        """

        g = Gaussian()
        f = SomeFrame(Toplevel(),extraPO=g)

        g.size=0.95
        self.assertNotEqual(f.size,g.size)
        self.assertEqual(f.get_parameter_value('size'),g.size)

        f.set_parameter_value('size',0.23)
        self.assertEqual(g.size,0.23)

        try:
            f.set_parameter_value('does_not_exist',100)
        except AttributeError:
            pass
        else:
            raise("Failed to raise AttributeError on setting non-existent *Parameter* 'does_not_exist'")

        try:
            f.get_parameter_value('does_not_exist')
        except AttributeError:
            pass
        else:
            raise("Failed to raise AttributeError on getting non-existent *Parameter* 'does_not_exist'")


@istest
class TestParameterTypeRepresentations(unittest.TestCase):


##         In the GUI, objects must sometimes be represented by strings (e.g. for an OptionMenu):
##         test that such conversion is handled correctly


    def setUp(self):
        self.f = SomeFrame(Toplevel())
        import __main__
        __main__.__dict__['f']=self.f


    def test_number_parameter(self):

        self.f.pack_param('nu')

        nu_param = self.f.get_parameter_object('nu')
        nu_tkvar = self.f._tkvars['nu']
        nu_widget = self.f.representations['nu']['widget']

        # check standard gui setting (includes resolution test)
        self.f.nu = 0.1
        nu_tkvar.set(0.9999999)
        self.f.update_idletasks()
        self.f.update() # seems to be required on OS X
        nu_widget._tag_press_return()
        self.assertEqual(self.f.nu,0.9999999)

        # ...and check the slider moved
        self.assertEqual(nu_widget.slider.get(),0.9999999)

        # check setting the slider
        # CB: note that we can't test actually moving the
        # slider with the mouse...
        nu_widget.slider.set(0.8)
        nu_widget._slider_used()
        self.assertEqual(self.f.nu,0.8)
        self.assertEqual(nu_widget.slider.get(),0.8)
        self.assertEqual(eval(nu_widget.tag.get()),eval('0.8'))
        self.assertEqual(eval(nu_tkvar.get()),eval('0.8'))

        # now make immediate and test that
        self.f.param_immediately_apply_change[param.Number]=True
        self.f.nu = 0.1
        nu_tkvar.set(0.4)
        self.assertEqual(self.f.nu,0.4)

        self.f.param_immediately_apply_change[param.Number]=False

        # check gui getting
        self.f.nu = 0.2
        self.assertEqual(eval(nu_tkvar.get()),eval('0.2'))

        # try to set tag beyond the 1 upper bound
        nu_tkvar.set(40.0)
        nu_widget._tag_press_return()
        self.assertEqual(self.f.nu,1) # stays at old value

        # check we can retrieve a value from main
        __main__.__dict__['testA'] = 0.075
        nu_widget.tag.delete(0,"end")
        nu_widget.tag.insert(0,"testA")
        nu_widget._tag_press_return()
        self.assertEqual(self.f.nu,0.075)
        self.assertEqual(nu_widget.tag.get(),'testA') # variable name not overwritten

        # check we can do some basic maths
        exec "from math import sin,pi" in __main__.__dict__
        nu_widget.tag.delete(0,"end")
        nu_widget.tag.insert(0,"sin(pi)")
        nu_widget._tag_press_return()
        from math import sin,pi
        self.assertAlmostEqual(self.f.nu,sin(pi))



    def test_object_selector_parameter(self):
        """
        Test that ObjectSelectorParameter representation works.
        """
        some_pos = [param.Parameterized(name='cat'),
                    param.Parameterized(name='rat'),
                    param.Parameterized(name='bat')]
        osp_param = self.f.get_parameter_object('osp')

        osp_param.objects = some_pos
        #self.f.r.default = some_pos[0]

        self.f.pack_param('osp')  # have to pack AFTER populating range for OptionMenu widget to work (see ALERT in tkparameterizedobject.py)


        # (otherwise, could do the following:
##         f = SomeFrame(Toplevel())
##         f.pack_param('r')
##         f.initialize_ranged_parameter('r',
##                                       [Parameterized(name='cat'),Parameterized(name='rat'),Parameterized(name='bat')])

        self.assertEqual(self.f.translators['osp'].string2object('cat'),some_pos[0])
        self.assertEqual(self.f.translators['osp'].string2object('rat'),some_pos[1])
        self.assertEqual(self.f.translators['osp'].string2object('bat'),some_pos[2])

        gnat = param.Parameterized(name='gnat')
        osp_param.objects.append(gnat)

        self.f.unpack_param('osp')
        self.f.pack_param('osp') # again, note the need to pack after updating range.
##         self.f.initialize_ranged_parameter('r',Parameterized)
        self.assertEqual(self.f.translators['osp'].string2object('gnat'),gnat)

        self.assertEqual(self.f._object2string('osp',some_pos[0]),'cat')
        self.assertEqual(self.f._object2string('osp',some_pos[1]),'rat')
        self.assertEqual(self.f._object2string('osp',some_pos[2]),'bat')


        # Simulate a GUI set
        self.f._tkvars['osp'].set('bat')
        self.assertEqual(self.f.osp,some_pos[2])

        # Test sorting
        # CB: add


    def test_class_selector_parameter(self):
        self.f.pack_param('csp')

        csp_param = self.f.get_parameter_object('csp')
        csp_tkvar = self.f._tkvars['csp']

        # should maintain instances once created (allows persistence
        # of edits to properties of the classes during the lifetime of
        # a window).

        csp_tkvar.set('Ring')
        self.assertEqual(type(self.f.csp),Ring)
        ring_id = id(self.f.csp)

        csp_tkvar.set('Rectangle')
        self.assertEqual(type(self.f.csp),Rectangle)
        rectangle_id = id(self.f.csp)

        csp_tkvar.set('Ring')
        self.assertEqual(id(self.f.csp),ring_id)
        csp_tkvar.set('Rectangle')
        self.assertEqual(id(self.f.csp),rectangle_id)

        # test sorting
        # CB: add instantiation test, switching test, etc



    def test_string_parameter(self):

        def test_fn(param_name):
            self.f.pack_param(param_name)
            w = self.f.representations[param_name]['widget']

            test_string = "new test string"
            w.delete(0,"end")
            w.insert(0,test_string)
            self.f._update_param_from_tkvar(param_name,force=True)

            self.assertEqual(getattr(self.f,param_name),test_string)
            self.assertEqual(w.get(),test_string)

        # unlike when typed by a user, everything's immediate when simulating set()
        self.f.param_immediately_apply_change[param.String] = True
        test_fn('st')

        # and now check the test actually works by making sure
        # it doesn't work for a Parameter (there'll be an extra
        # pair of quotes, stopping a match)
        try:
            test_fn('pa')
        except AssertionError:
            pass
        else:
            raise("Test should fail for Parameter")


# CB: need to add test
##     def test_boolean_parameter(self):

##         self.f.pack_param('boo')




    def test_parameter(self):
        self.f.pack_param('pa')
        w = self.f.representations['pa']['widget']
        w.delete(0,"end")
        w.insert(0,"AnObjectNamedThisWillNotExist")
        self.f._update_param_from_tkvar('pa',True)
        self.assertEqual(self.f.pa,'test') # didn't get set to wrong value

        # Check that we can create an object from a class in __main__
        exec "from topo.transferfn import IdentityTF" in __main__.__dict__
        w.delete(0,"end")
        w.insert(0,"IdentityTF()")
        self.f._update_param_from_tkvar('pa',force=True)
        import topo.transferfn
        self.assertEqual(type(self.f.pa),topo.transferfn.IdentityTF)




###########################################################

if __name__ == "__main__":
	import nose
	nose.runmodule()