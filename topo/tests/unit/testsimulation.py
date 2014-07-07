"""
Unit test for Simulation
"""

import unittest
import copy
import pickle

import numpy as np
from topo.base.simulation import Simulation,EPConnection,EPConnectionEvent,Event
from topo.base.ep import *

from topo.base.cf import CFSheet, CFProjection

from topo.tests.utils import new_simulation

import topo

# CEBALERT: not a complete test of Simulation

class TestSimulation(unittest.TestCase):


    def test_register_is_true(self):
        sim1 = new_simulation(name="test_singleton")
        assert sim1 is topo.sim

        sid = id(topo.sim['S'])

        sim2 = copy.copy(topo.sim)
        assert sim2 is sim1

        sim3 = copy.deepcopy(topo.sim)
        assert sim3 is sim1

        self.assertEqual(id(sim3['S']),sid)

        topo.sim['S'].precedence=111
        p = pickle.dumps(topo.sim,2)
        topo.sim['S'].precedence=5

        Simulation.register=False # to ensure the object's own register is being used
        sim4 = pickle.loads(p)
        Simulation.register=True

        assert sim4 is sim1
        assert topo.sim['S'].precedence==111,"%s"%topo.sim['S'].precedence





    def test_register_is_false(self):
        sim1 = new_simulation(register=False)
        assert sim1 is not topo.sim

        sid = id(sim1['S'])

        sim2 = copy.copy(sim1)
        assert sim2 is not sim1
        assert sim2 is not topo.sim

        sim3 = copy.deepcopy(sim1)
        assert sim3 is not sim1
        assert sim3 is not topo.sim

        self.assertNotEqual(id(sim3['S']),sid)

        new_simulation(register=True)
        sim1['S'].precedence=111
        p = pickle.dumps(sim1,2)
        topo.sim['S'].precedence=5
        sim4 = pickle.loads(p)

        assert sim4 is not sim1
        assert sim4 is not topo.sim
        assert topo.sim['S'].precedence==5




    def test_event_copy(self):
        """
        Test to make sure that EPConnectionEvent copies the underlying data
        on construction.
        """
        s = Simulation()
        data = np.array([4,3])
        epc = EPConnection()
        se = EPConnectionEvent(1,epc,data)
        se.data[0] = 5
        assert data[0] != se.data[0], 'Matrices should be different'
        se2 = copy.copy(se)
        assert se is not se2, 'Objects are the same'

    def test_state_stack(self):
        s = Simulation()
        s['pulse1'] = PulseGenerator(period = 1)
        s['pulse2'] = PulseGenerator(period = 3)
        s['sum_unit'] = SumUnit()
        s.connect('pulse1','sum_unit',delay=1)
        s.connect('pulse2','sum_unit',delay=1)
        s.run(1.0)
        s.state_push()
        self.assertEqual(len(s._events_stack),1)
        s.state_pop()
        self.assertEqual(len(s._events_stack),0)


    def test_event_cmp(self):

        e1 = Event(1)
        e1a = Event(1)
        e2 = Event(2)

        assert e1 is not e1a
        assert e1 ==  e1a
        assert e1 < e2
        assert e1 == e1
        assert e2 > e1
        assert e2 == e2
        assert e1 != e2
        assert e2 != e1

    def test_event_insert(self):
        s = Simulation()

        e1 = Event(1)
        e1a = Event(1)
        e2 = Event(2)
        e2a = Event(2)

        s.enqueue_event(e1)
        s.enqueue_event(e2)
        s.enqueue_event(e2a)
        s.enqueue_event(e1a)

        s.enqueue_event(Event(0))

        assert len(s.events) == 5, 'Event queue has %d events, should have 5.' % len(s.events)

        assert s.events[1] == e1
        assert s.events[2] == e1a
        assert s.events[3] == e2
        assert s.events[4] == e2a


    def test_get_objects(self):
        s = Simulation()

        s['pulse1'] = PulseGenerator(period = 1)
        s['pulse2'] = PulseGenerator(period = 3)
        s['sum_unit'] = SumUnit()
        n1 = s['pulse1'].name
        n2 = s['pulse2'].name

        s.connect('pulse1','sum_unit',delay=1)
        s.connect('pulse2','sum_unit',delay=1)
        t1 = s.objects()
        e1 = [ep for ep in t1.values() if isinstance(ep,PulseGenerator) and ep.name == n1]
        t2 = s.objects()
        e2 = [ep for ep in t2.values() if isinstance(ep,PulseGenerator) and ep.name == n2]
        assert e1.pop().name == n1, 'Object names do not match'
        assert e2.pop().name == n2, 'Object names do not match'


##     def test_garbage_collection(self):
##         """something"""
##         s = Simulation(register=False)
##         s['v1']=CFSheet(nominal_density=24)
##         s['v2']=CFSheet(nominal_density=24)
##         s.connect('v1','v2',name='Afferent',delay=0.05,connection_type=CFProjection)
##         from weakref import WeakValueDictionary as W
##         w=W()
##         w['v1'] = s['v1']
##         w['v2'] = s['v2']

##         # need to cause s to be deleted: s in this namespace should
##         # be only reference to s (apart from circular ones...)
##         del s

##         try:
##             w['v1']
##         except KeyError:
##             pass
##         else:
##             raise ValueError("v1 was not deleted")

##         try:
##             w['v2']
##         except KeyError:
##             pass
##         else:
##             raise ValueError("v2 was not deleted")

if __name__ == "__main__":
	import nose
	nose.runmodule()
