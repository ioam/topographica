"""
Two-dimensional pattern generators drawing from various random distributions.

$Id$
"""
__version__='$Revision$'

import numpy

from numpy.oldnumeric import zeros,floor,where,choose,less,greater,Int,random_array 

import param
from param.parameterized import ParamOverrides

from topo.base.patterngenerator import PatternGenerator
from topo.pattern import Composite, Gaussian
from topo.base.sheetcoords import SheetCoordinateSystem



def seed(seed=None):
    """
    Set the seed on the shared RandomState instance.

    Convenience function: shortcut to RandomGenerator.random_generator.seed().
    """
    RandomGenerator.random_generator.seed(seed)
    

class RandomGenerator(PatternGenerator):
    """2D random noise pattern generator abstract class."""

    __abstract = True

    # The orientation is ignored, so we don't show it in
    # auto-generated lists of parameters (e.g. in the GUI)
    orientation = param.Number(precedence=-1)

    random_generator = param.Parameter(
        default=numpy.random.RandomState(seed=(500,500)),precedence=-1,doc=
        """
        numpy's RandomState provides methods for generating random
        numbers (see RandomState's help for more information).

        Note that all instances will share this RandomState object,
        and hence its state. To create a RandomGenerator that has its
        own state, set this parameter to a new RandomState instance.
        """)

        
    def _distrib(self,shape,p):
        """Method for subclasses to override with a particular random distribution."""
        raise NotImplementedError
    
    # Optimization: We use a simpler __call__ method here to skip the
    # coordinate transformations (which would have no effect anyway)
    def __call__(self,**params_to_override):
        p = ParamOverrides(self,params_to_override)

        shape = SheetCoordinateSystem(p.bounds,p.xdensity,p.ydensity).shape

        result = self._distrib(shape,p)
        self._apply_mask(p,result)

        for of in p.output_fns:
            of(result)
                
        return result



class UniformRandom(RandomGenerator):
    """2D uniform random noise pattern generator."""

    def _distrib(self,shape,p):
        return p.random_generator.uniform(p.offset, p.offset+p.scale, shape)



class BinaryUniformRandom(RandomGenerator):
    """
    2D binary uniform random noise pattern generator.

    Generates an array of random numbers that are 1.0 with the given
    on_probability, or else 0.0, then scales it and adds the offset as
    for other patterns.  For the default scale and offset, the result
    is a binary mask where some elements are on at random.
    """

    on_probability = param.Number(default=0.5,bounds=[0.0,1.0],doc="""
        Probability (in the range 0.0 to 1.0) that the binary value
        (before scaling) is on rather than off (1.0 rather than 0.0).""")

    def _distrib(self,shape,p):
        rmin = p.on_probability-0.5
        return p.offset+p.scale*(p.random_generator.uniform(rmin,rmin+1.0,shape).round())



class GaussianRandom(RandomGenerator):
    """
    2D Gaussian random noise pattern generator.

    Each pixel is chosen independently from a Gaussian distribution
    of zero mean and unit variance, then multiplied by the given
    scale and adjusted by the given offset.
    """

    scale  = param.Number(default=0.25,softbounds=(0.0,2.0))
    offset = param.Number(default=0.50,softbounds=(-2.0,2.0))

    def _distrib(self,shape,p):
        return p.offset+p.scale*p.random_generator.standard_normal(shape)


# CEBALERT: in e.g. script_repr, an instance of this class appears to
# have only pattern.Constant() in its list of generators, which might
# be confusing. The Constant pattern has no effect because the
# generators list is overridden in __call__. Shouldn't the generators
# parameter be hidden for this class (and possibly for others based on
# pattern.Composite)? For that to be safe, we'd at least have to have
# a warning if someone ever sets a hidden parameter, so that having it
# revert to the default value would always be ok.

class GaussianCloud(Composite):
    """Uniform random noise masked by a circular Gaussian."""

    operator = param.Parameter(numpy.multiply)
    
    gaussian_size = param.Number(default=1.0,doc="Size of the Gaussian pattern.")

    aspect_ratio  = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,2.0),
        precedence=0.31,doc="""
        Ratio of gaussian width to height; width is gaussian_size*aspect_ratio.""")

    def __call__(self,**params_to_override):
        p = ParamOverrides(self,params_to_override)
        p.generators=[Gaussian(aspect_ratio=p.aspect_ratio,size=p.gaussian_size),
                      UniformRandom()]
        return super(GaussianCloud,self).__call__(**p)



### JABHACKALERT: This code seems to work fine when the input regions
### are all the same size and shape, but for
### e.g. examples/hierarchical.ty the resulting images in the Test
### Pattern preview window are square (instead of the actual
### rectangular shapes), matching between the eyes (instead of the
### actual two different rectangles), and with dot sizes that don't
### match between the eyes.  It's not clear why this happens.

class RandomDotStereogram(PatternGenerator):
    """
    Random dot stereogram using rectangular black and white patches.

    Based on Matlab code originally from Jenny Read, reimplemented
    in Python by Tikesh Ramtohul (2006).
    """

    # Suppress unused parameters
    x = param.Number(precedence=-1)
    y = param.Number(precedence=-1)
    size = param.Number(precedence=-1)
    orientation = param.Number(precedence=-1)

    # Override defaults to make them appropriate
    scale  = param.Number(default=0.5)
    offset = param.Number(default=0.5)

    # New parameters for this pattern

    #JABALERT: Should rename xdisparity and ydisparity to x and y, and simply
    #set them to different values for each pattern to get disparity
    xdisparity = param.Number(default=0.0,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                        precedence=0.50,doc="Disparity in the horizontal direction.")
    
    ydisparity = param.Number(default=0.0,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                        precedence=0.51,doc="Disparity in the vertical direction.")
    
    dotdensity = param.Number(default=0.5,bounds=(0.0,None),softbounds=(0.1,0.9),
                        precedence=0.52,doc="Number of dots per unit area; 0.5=50% coverage.")

    dotsize    = param.Number(default=0.1,bounds=(0.0,None),softbounds=(0.05,0.15),
                        precedence=0.53,doc="Edge length of each square dot.")

    random_seed=param.Integer(default=500,bounds=(0,1000),
                        precedence=0.54,doc="Seed value for the random position of the dots.")


    def __call__(self,**params_to_override):
        p = ParamOverrides(self,params_to_override)

        xsize,ysize = SheetCoordinateSystem(p.bounds,p.xdensity,p.ydensity).shape
        xsize,ysize = int(round(xsize)),int(round(ysize))
        
        xdisparity  = int(round(xsize*p.xdisparity))  
        ydisparity  = int(round(xsize*p.ydisparity))   
        dotsize     = int(round(xsize*p.dotsize))
        
        bigxsize = 2*xsize
        bigysize = 2*ysize
        ndots=int(round(p.dotdensity * (bigxsize+2*dotsize) * (bigysize+2*dotsize) /
                        min(dotsize,xsize) / min(dotsize,ysize)))
        halfdot = floor(dotsize/2)
    
        # Choose random colors and locations of square dots
        random_seed = p.random_seed

        random_array.seed(random_seed*12,random_seed*99)
        col=where(random_array.random((ndots))>=0.5, 1.0, -1.0)

        random_array.seed(random_seed*122,random_seed*799)
        xpos=floor(random_array.random((ndots))*(bigxsize+2*dotsize)) - halfdot
    
        random_array.seed(random_seed*1243,random_seed*9349)
        ypos=floor(random_array.random((ndots))*(bigysize+2*dotsize)) - halfdot
      
        # Construct arrays of points specifying the boundaries of each
        # dot, cropping them by the big image size (0,0) to (bigxsize,bigysize)
        x1=xpos.astype(Int) ; x1=choose(less(x1,0),(x1,0))
        y1=ypos.astype(Int) ; y1=choose(less(y1,0),(y1,0))
        x2=(xpos+(dotsize-1)).astype(Int) ; x2=choose(greater(x2,bigxsize),(x2,bigxsize))
        y2=(ypos+(dotsize-1)).astype(Int) ; y2=choose(greater(y2,bigysize),(y2,bigysize))

        # Draw each dot in the big image, on a blank background
        bigimage = zeros((bigysize,bigxsize))
        for i in range(ndots):
            bigimage[y1[i]:y2[i]+1,x1[i]:x2[i]+1] = col[i]
            
        result = p.offset + p.scale*bigimage[ (ysize/2)+ydisparity:(3*ysize/2)+ydisparity ,
                                              (xsize/2)+xdisparity:(3*xsize/2)+xdisparity ]

        for of in p.output_fns:
            of(result)

        return result
