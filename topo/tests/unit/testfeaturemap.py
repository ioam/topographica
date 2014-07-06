"""
TestFeatureMap
"""



# CEBALERT: this isn't finished.


import unittest

from topo.base.arrayutil import arg, wrap
from math import pi
import numpy as np
from numpy import exp
from topo.base.sheet import Sheet
from topo.base.boundingregion import BoundingBox

# for making a simulation:
from topo.sheet import GeneratorSheet
from topo.base.cf import CFProjection, CFSheet
from topo.base.simulation import Simulation
from topo.learningfn.optimized import CFPLF_Hebbian
from topo.analysis.featureresponses import pattern_response

from imagen import SineGrating
from featuremapper import Feature, DistributionMatrix, FeatureMaps
from featuremapper.distribution import DSF_WeightedAverage

# globals to use weighted_average, selectivity, vector_sum, which are not methods
# of DistributionMatrix any more
weighted_average    = ( lambda x: x.apply_DSF( DSF_WeightedAverage() )['']['preference'] )
selectivity         = ( lambda x: x.apply_DSF( DSF_WeightedAverage() )['']['selectivity'] )

class TestDistributionMatrix(unittest.TestCase):


    def setUp(self):

        # sheet to test. As it is, its activity matrix dimension is (3,2)
        Sheet.nominal_density = 1
        Sheet.nominal_bounds = BoundingBox(points=((-1,-2),(1,1)))
        test_sheet = Sheet()
        # simple activity arrays use to update the feature maps
        self.a1 = np.array([[1,1], [1,1], [1,1]])
        self.a2 = np.array([[3,3], [3,3], [3,3]])
        self.a3 = np.array([[0,1], [0,1], [0,1]])

        # object to test for non-cyclic distributions
        self.fm1 = DistributionMatrix(test_sheet.shape, axis_range=(0.0,1.0), cyclic=False)
        self.fm1.update(self.a1,0.5)

        # object to for cyclic distributions
        self.fm2 = DistributionMatrix(test_sheet.shape, axis_range=(0.0,1.0), cyclic=True)
        self.fm2.update(self.a1,0.5)


    # need to add a test_update()


    def test_preference(self):

        for i in range(3):
            for j in range(2):
                self.assertAlmostEqual( weighted_average( self.fm1 )[i,j], 0.5)
                self.assertAlmostEqual( weighted_average( self.fm2 )[i,j], 0.5)


        # To test the update function
        self.fm1.update(self.a1,0.7)
        self.fm2.update(self.a1,0.7)

        for i in range(3):
            for j in range(2):
                self.assertAlmostEqual( weighted_average( self.fm1 )[i,j], 0.6)
                vect_sum = wrap(0,1,arg(exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/(2*pi))
                self.assertAlmostEqual( weighted_average( self.fm2 )[i,j],vect_sum)




        # To test the keep_peak=True
        self.fm1.update(self.a1,0.7)
        self.fm2.update(self.a1,0.7)

        for i in range(3):
            for j in range(2):
                self.assertAlmostEqual( weighted_average( self.fm1 )[i,j], 0.6)
                vect_sum =wrap(0,1,arg(exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/(2*pi))
                self.assertAlmostEqual( weighted_average( self.fm2 )[i,j],vect_sum)

        self.fm1.update(self.a2,0.7)
        self.fm2.update(self.a2,0.7)

        for i in range(3):
            for j in range(2):
                self.assertAlmostEqual( weighted_average( self.fm1 )[i,j], 0.65)
                vect_sum =wrap(0,1,arg(3*exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/(2*pi))
                self.assertAlmostEqual( weighted_average( self.fm2 )[i,j],vect_sum)

        # to even test more....

        self.fm1.update(self.a3,0.9)
        self.fm2.update(self.a3,0.9)

        for i in range(3):
            self.assertAlmostEqual( weighted_average( self.fm1 )[i,0], 0.65)
            self.assertAlmostEqual( weighted_average( self.fm1 )[i,1], 0.7)
            vect_sum = wrap(0,1,arg(3*exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/(2*pi))
            self.assertAlmostEqual( weighted_average( self.fm2 )[i,0],vect_sum)
            vect_sum = wrap(0,1,arg(3*exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j)+exp(0.9*2*pi*1j))/(2*pi))
            self.assertAlmostEqual( weighted_average( self.fm2 )[i,1],vect_sum)


    def test_selectivity(self):

        for i in range(3):
            for j in range(2):
                # when only one bin the selectivity is 1 (from C code)
                self.assertAlmostEqual( selectivity( self.fm1 )[i,j], 1.0)
                self.assertAlmostEqual( selectivity( self.fm2 )[i,j], 1.0)

        # To test the update function
        self.fm1.update(self.a1,0.7)
        self.fm2.update(self.a1,0.7)

        for i in range(3):
            for j in range(2):
                proportion = 1.0/2.0
                offset = 1.0/2.0
                relative_selectivity = (proportion-offset)/(1.0-offset)  ## gives 0 ..?
                self.assertAlmostEqual( selectivity( self.fm1 )[i,j],relative_selectivity)
                vect_sum = abs(exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/2.0
                self.assertAlmostEqual( selectivity( self.fm2 )[i,j],vect_sum)




        # To test the keep_peak=True
        self.fm1.update(self.a1,0.7)
        self.fm2.update(self.a1,0.7)

        for i in range(3):
            for j in range(2):
                proportion = 1.0/2.0
                offset = 1.0/2.0
                relative_selectivity = (proportion-offset)/(1.0-offset)
                self.assertAlmostEqual( selectivity( self.fm1 )[i,j],relative_selectivity)
                vect_sum = abs(exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/2.0
                self.assertAlmostEqual( selectivity( self.fm2 )[i,j],vect_sum)


        self.fm1.update(self.a2,0.7)
        self.fm2.update(self.a2,0.7)

        for i in range(3):
            for j in range(2):
                proportion = 3.0/4.0
                offset = 1.0/2.0
                relative_selectivity = (proportion-offset)/(1.0-offset)
                #self.assertAlmostEqual( selectivity( self.fm1 )[i,j],relative_selectivity)
                vect_sum = abs(3*exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/4.0
                self.assertAlmostEqual( selectivity( self.fm2 )[i,j],vect_sum)

        # to even test more....

        self.fm1.update(self.a3,0.9)
        self.fm2.update(self.a3,0.9)

        for i in range(3):
            proportion = 3.0/4.0
            offset = 1.0/3.0 ### Carefull, do not create bins when it is 0
            ### Check with Bednar what is num_bins in the original C-file and see what he wants
            ### now for the selectivity ....
            relative_selectivity = (proportion-offset)/(1.0-offset)
            self.assertAlmostEqual( selectivity( self.fm1 )[i,0], relative_selectivity)
            proportion = 3.0/5.0
            offset = 1.0/3.0
            relative_selectivity = (proportion-offset)/(1.0-offset)
            ### to fix this test as well
            #self.assertAlmostEqual( selectivity( self.fm1 )[i,1], relative_selectivity)

            vect_sum = abs(3*exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j))/4.0
            self.assertAlmostEqual( selectivity( self.fm2 )[i,0],vect_sum)
            vect_sum = abs(3*exp(0.7*2*pi*1j)+exp(0.5*2*pi*1j)+exp(0.9*2*pi*1j))/5.0
            self.assertAlmostEqual( selectivity( self.fm2 )[i,1],vect_sum)





class TestFeatureMaps(unittest.TestCase):

    def setUp(self):
        """
        Create a CFSheet ('V1') connected to a GeneratorSheet ('Retina').
        """
        self.s = Simulation()
        self.s['Retina']=GeneratorSheet(nominal_density=4.0)
        self.s['V1']= CFSheet(nominal_density=4.0)
        self.s['V2'] = CFSheet(nominal_density=4.0)

        self.s.connect('Retina','V1',delay=0.5,connection_type=CFProjection,
                       name='RtoV1',learning_fn=CFPLF_Hebbian())

        self.s.connect('Retina','V2',delay=0.5,connection_type=CFProjection,
                       name='RtoV2',learning_fn=CFPLF_Hebbian())



    def test_measurefeaturemap(self):
        """

        """

        self.feature_param = [Feature(name="phase",range=(0.0,1.0),values=[0.2,0.4,0.6],cyclic=False),
                              Feature(name="orientation",range=(0.0,1.0),step=0.5,cyclic=True)]

        self.x = FeatureMaps(self.feature_param,
                             pattern_response_fn=pattern_response.instance(),
                             pattern_generator=SineGrating())
        #print self.V1.activity
        #### test has to be written!!!

if __name__ == "__main__":
	import nose
	nose.runmodule()
