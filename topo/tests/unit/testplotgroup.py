"""
Test for the PlotGroup class
"""

import unittest
import topo.base.simulation
from pprint import pprint
from topo.plotting import plot
from topo.base.sheet import *
from topo.plotting.plotgroup import *
import numpy as np

SHOW_PLOTS = False

plotgroup_templates = {}

### JCALERT! This file has to be re-written when the fundamental changes in plot.py
### plotengine.py and plotgroup.py will be finished.
### for the moment, the tests are commented out...
### Also it has to performed the test that were previously performed in testplotengine.py


class TestPlotGroup(unittest.TestCase):

    def setUp(self):
        pass

#         pgt = PlotGroupTemplate([('Activity',
#                                   PlotTemplate({'Strength'   : 'Activity',
#                                                 'Hue'        : None,
#                                                 'Confidence' : None}))],
#                                 name='Activity')
#         plotgroup_templates[pgt.name] = pgt
#         pgt = PlotGroupTemplate([('Unit Weights',
#                                   PlotTemplate({'Location'   : (0.0,0.0),
#                                                 'Sheet_name' : 'V1'}))],
#                                 name='Unit Weights')
#         plotgroup_templates[pgt.name] = pgt
#         pgt = PlotGroupTemplate([('Projection',
#                                   PlotTemplate({'Density'         : 25,
#                                                 'Projection_name' : 'None'}))],
#                                 name='Projection')
#         plotgroup_templates[pgt.name] = pgt
#         pgt = PlotGroupTemplate([('Preference',
#                                   PlotTemplate({'Strength'   : 'Activity',
#                                                 'Hue'        : 'Activity',
#                                                 'Confidence' : 'Activity'}))],
#                                 name='Preference Map')
#         plotgroup_templates[pgt.name] = pgt


#     def test_plotgroup_release(self):
#         self.s = Sheet()
#         self.s.activity = np.array([[1,2],[3,4]])
#         # Call s.sheet_view(..) with a parameter
#         sv2 = self.s.sheet_view('Activity')
#         self.s.sheet_views['key']=sv2
#         self.assertEqual(len(self.s.sheet_views.keys()),1)
#         y = plot.Plot(('key',None,None),plot.HSV,self.s)
#         z = plot.Plot(('key',None,None),plot.HSV,self.s)
#         self.pg1 = PlotGroup(plot_list=[y,z])
#         tuples = self.pg1.plots()
#         self.pg1.release_sheetviews()
#         self.assertEqual(len(self.s.sheet_views.keys()),0)



#     def test_plotgroup(self):
#         self.s2 = Sheet()
#         ig = ImageGenerator(filename='topo/tests/testsheetview.ppm',
#                          density=100,
#                          bounds=BoundingBox(points=((-0.8,-0.8),(0.8,0.8))))
#         x = plot.Plot((None,None,ig.sheet_view('Activity')),plot.HSV)
#         y = plot.Plot(('Activity',None,None),plot.COLORMAP,ig)
#         z = plot.Plot(('Activity',None,'Activity'),plot.HSV,ig)
#         self.pg1 = PlotGroup(plot_list=[x])
#         self.pg1.add(y)
#         self.pg1.add(z)
#         plot_list = self.pg1.plots()
#         for each in plot_list:
#             (r,g,b) = each.matrices
#             map = RGBMap(r,g,b)
#             if SHOW_PLOTS: map.show()

#     def test_make_plot_group(self):
#         sim = topo.base.simulation.Simulation()
#         pe = topo.plotting.plotengine.PlotEngine(sim)
#       filter = lambda s: True
#         pg = pe.make_plot_group('Activity',
#                                 plotgroup_templates['Activity'],
#                               filter,'BasicPlotGroup')

#     def test_get_plot_group(self):
#         sim = topo.base.simulation.Simulation()
#         pe = topo.plotting.plotengine.PlotEngine(sim)
#         pg = pe.get_plot_group('Activity',
#                                plotgroup_templates['Activity'])
#         pg = pe.get_plot_group('Activity',
#                                plotgroup_templates['Activity'])



#     def test_keyedlist(self):
#         kl = KeyedList()
#         kl = KeyedList(((2,3),(4,5)))
#         self.assertEqual(kl[2],3)
#         self.assertEqual(kl[4],5)
#         kl.append((6,7))
#         self.assertEqual(kl[6],7)
#         kl[2] = 8
#         self.assertEqual(kl[2],8)
#         self.assertEqual(kl.has_key(5),False)
#         self.assertTrue(kl.has_key(6))
#         self.assertEqual(len(kl),3)
#         kl.append((3,8))
#         l = list(kl)


#     def test_plotgrouptemplate(self):
#         pgt = PlotGroupTemplate()

#         pt1 = plot.PlotTemplate({'Strength'   : None,
#                                  'Hue'        : 'HueP',
#                                  'Confidence' : None})
#         pt2 = plot.PlotTemplate({'Strength'   : 'HueSel',
#                                  'Hue'        : 'HueP',
#                                  'Confidence' : None})
#         pt3 = plot.PlotTemplate({'Strength'   : 'HueSel',
#                                  'Hue'        : None,
#                                  'Confidence' : None})
#         pgt = PlotGroupTemplate([('HuePref', pt1),
#                                  ('HuePrefAndSel', pt2),
#                                  ('HueSelect', pt3)])

#         pgt2 = PlotGroupTemplate(
#             [('HuePref', PlotTemplate({'Strength'   : None,
#                                        'Hue'        : 'HueP',
#                                        'Confidence' : None})),
#              ('HuePrefAndSel', PlotTemplate({'Strength'   : 'HueSel',
#                                              'Hue'        : 'HueP',
#                                              'Confidence' : None})),
#              ('HueSelect', PlotTemplate({'Strength'   : 'HueSel',
#                                          'Hue'        : None,
#                                          'Confidence' : None}))])


################## PREVIOUSLY IN TESTPLOTENGINE:

### JC: My new statements.
import unittest
from topo.base.simulation import Simulation
from topo.plotting.plotgroup import TemplatePlotGroup, ConnectionFieldsPlotGroup

import topo.pattern.random
from topo.learningfn.som import CFPLF_HebbianSOM
from topo.base.cf import CFProjection, CFSheet
from topo.responsefn.optimized import CFPRF_DotProduct_opt
from topo.base.patterngenerator import BoundingBox

### JCALERT! This file has to be re-written when the fundamental changes in plot.py
### plotengine.py and plotgroup.py will be finished.
### for the moment, the tests are commented out...

# class TestPlotEngine(unittest.TestCase):

#       def setUp(self):

#           self.sim = Simulation()

#           CFSheet.nominal_density = 10

#           V1 = CFSheet(name='V1')
#           V2 = CFSheet(name='V2')
#           V3 = CFSheet(name='V3')

#           CFProjection.weights_generator = topo.pattern.random.UniformRandom(bounds=BoundingBox(points=((-0.1,-0.1),(0.1,0.1))))
#           CFProjection.weights_generator = topo.pattern.random.UniformRandom(bounds=BoundingBox(points=((-0.1,-0.1),(0.1,0.1))))
#           CFProjection.response_fn = CFPRF_DotProduct_opt()
#           CFProjection.learning_fn = CFPLF_HebbianSOM()

#           self.sim.connect(V1,V2,delay=0.5,connection_type=CFProjection,name='V1toV2')
#           self.sim.connect(V3,V2,delay=0.5,connection_type=CFProjection,name='V2toV3')

#           self.pe = PlotEngine(self.sim)

#       def test_make_plot_group(self):

#           ### Activity PlotGroup
#           pgt1 = plotgroup_templates['Activity']

#           self.pe.make_plot_group('Activity',pgt1,'BasicPlotGroup',None)
#           test_plot_group = BasicPlotGroup(self.sim,pgt1,'Activity',None,None)
#           test = self.pe.plot_group_dict.get('Activity',None)

#           ### JCALERT! HOW TO TEST THAT TWO PLOTGROUP ARE THE SAME?
#           #self.assertEqual(test_plot_group,test)

#           ### Orientation Preference PlotGroup
#           pgt2 = plotgroup_templates['Orientation Preference']

#           self.pe.make_plot_group('Orientation Preference',pgt2,'BasicPlotGroup',None)
#           test_plot_group = BasicPlotGroup(self.sim,pgt2,'Orientation Preference',None,None)
#           test = self.pe.plot_group_dict.get('Orientation Preference',None)
#           #self.assertEqual(test_plot_group,test)

#           ### UnitWeight PlotGroup
#           pgt3 = plotgroup_templates['Unit Weights']

#           pg_key1=('Weights','V1',0,0)
#           pg_key2=('Weights','V2',0.4,0.4)
#           pg_key3=('Weights','V3',0.1,0.1)
#           self.pe.make_plot_group(pg_key1,pgt3,'UnitWeightsPlotGroup','V1')
#           self.pe.make_plot_group(pg_key2,pgt3,'UnitWeightsPlotGroup','V2')
#           self.pe.make_plot_group(pg_key3,pgt3,'UnitWeightsPlotGroup','V3')

#           test_plot_group1 = UnitWeightsPlotGroup(self.sim,pgt3,pg_key1,'V1',None)
#           test_lambda = lambda s: s.name == 'V2'
#           test_plot_group2 = UnitWeightsPlotGroup(self.sim,pgt3,pg_key2,test_lambda,None)
#           test_plot_group3 = UnitWeightsPlotGroup(self.sim,pgt3,pg_key3,'V3',None)


#           test1 = self.pe.plot_group_dict.get(pg_key1,None)
#           #self.assertEqual(test_plot_group1,test1)

#           test2 = self.pe.plot_group_dict.get(pg_key2,None)
#           #self.assertEqual(test_plot_group2,test2)

#           test3 = self.pe.plot_group_dict.get(pg_key3,None)
#           #self.assertEqual(test_plot_group3,test3)

#           pgt4 = plotgroup_templates['Projection']

if __name__ == "__main__":
	import nose
	nose.runmodule()
