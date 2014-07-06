"""
See test_cfsom(self) and ImagePoster for an example of how to use and call
the PlotEngine system from a simulation.
"""

import unittest
import random
from pprint import pprint
from math import pi

import param

import topo
from topo.pattern import Gaussian
from topo.plotting import plot
from topo.plotting.bitmap import *
from topo.base.sheet import Sheet, BoundingBox
from topo.base.simulation import *
from topo.base import patterngenerator
from topo.base.cf import CFProjection, CFSheet
from topo.learningfn.optimized import CFPLF_Hebbian_opt
from topo.sheet import *
from topo import numbergen

### Only for ImageSaver
from topo.base.simulation import EventProcessor
from topo.misc.util import NxN
from pprint import *
import Image, ImageOps

from nose.tools import istest, nottest
### JABALERT: The ImageSaver class should probably be deleted,
### but it is currently used in this test.

@nottest
class ImageSaver(EventProcessor):
    """

    A Sheet that receives activity matrices and saves them as bitmaps.
    Each time an ImageSaver sheet receives an input event on any input
    port, it saves it to a file.  The file name is determined by:

      <file_prefix><name>_<port>_<time>.<file_format>

    Where <name> is the name of the ImageSaver object, <port> is the
    name of the input port used, and <time> is the current simulation time.

    Parameters::
      file_prefix = (default '') A path or other prefix for the
                    filename.
      file_format = (default 'ppm') The file type to use when saving
                    the image. (can be any image format understood by PIL)
      time_format = (default '%f') The format string for the time.
      pixel_scale = (default 255) The amount to scale the
                     activity. Used as parameter to PIL's Image.putdata().
      pixel_offset = (default 0) The zero-offset for each pixel. Used as
                     parameter to PIL's Image.putdata()

    """

    file_prefix = param.Parameter('')
    file_format = param.Parameter('ppm')
    time_format = param.Parameter('%f')
    pixel_scale = param.Parameter(255)
    pixel_offset = param.Parameter(0)



    def input_event(self,conn,data):

        self.verbose("Received %s  input from %s" % (NxN(data.shape),conn.src))
        self.verbose("input max value = %d" % max(data.ravel()))

        # assemble the filename
        filename = self.file_prefix + self.name
        if conn.dest_port:
            filename += "_" + str(conn.dest_port)
        filename += "_" + (self.time_format % self.simulation.time())
        filename += "." + self.file_format

        self.verbose("filename = '%s'" % filename)

        # make and populate the image
        im = Image.new('L',(data.shape[1],data.shape[0]))
        self.verbose("image size = %s" % NxN(im.size))
        im.putdata(data.ravel(),
                   scale=self.pixel_scale,
                   offset=self.pixel_offset)

        self.verbose("put image data.")

        #save the image
        f = open(filename,'w')
        im.save(f,self.file_format)
        f.close()


@istest
class TestCFSom(unittest.TestCase):

    def setUp(self):
        self.s = Simulation()
        self.sheet1 = Sheet()
        self.sheet2 = Sheet()


# CEBALERT: replace with an equivalent example that uses Image
##     def test_imagegenerator(self):
##         """
##         Code moved from __main__ block of cfsom.py.  Gives a tight example
##         of running a cfsom simulation.
##         """
##         from testsheetview import ImageGenerator

##         s = Simulation(step_mode=True)

##         ImageGenerator.nominal_density = 100
##         ImageGenerator.nominal_bounds = BoundingBox(points=((-0.8,-0.8),(0.8,0.8)))
##         input = ImageGenerator(filename='images/ellen_arthur.pgm')


##         save = ImageSaver(pixel_scale=1.5)
##         som = CFSheet()

##         s.add(som,input,save)
##         s.connect(input,som,connection_type=CFProjection,learning_fn=CFPLF_Hebbian_opt())
##         s.connect(som,save)
##         s.run(duration=10)



    def test_cfsom(self):
        """
        """

        gaussian_width = 0.02
        gaussian_height = 0.9

        input_pattern = Gaussian(
            bounds=BoundingBox(points=((-0.8,-0.8),(0.8,0.8))),
            scale=gaussian_height,
            aspect_ratio=gaussian_width/gaussian_height,
            x=numbergen.UniformRandom(lbound=-0.5,ubound=0.5,seed=100),
            y=numbergen.UniformRandom(lbound=-0.5,ubound=0.5,seed=200),
            orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=300))


        # input generation params
        GeneratorSheet.period = 1.0
        GeneratorSheet.nominal_density = 5


        # cf som parameters
        CFSheet.nominal_density = 5

        ###########################################
        # build simulation


        s = Simulation()
        s.verbose("Creating simulation objects...")
        s['retina']=GeneratorSheet(input_generator=input_pattern)

        s['V1'] = CFSheet()

        s.connect('retina','V1',delay=1,connection_type=CFProjection,
                  learning_fn=CFPLF_Hebbian_opt())

        self.assertTrue(topo.sim['V1'].projections().get('retinaToV1',None) != None)
        self.assertTrue(topo.sim['V1'].projections().get('retinaToV1',None) != None)
        s.run(10)

if __name__ == "__main__":
	import nose
	nose.runmodule()
