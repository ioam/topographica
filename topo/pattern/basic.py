from __future__ import with_statement
"""
Simple two-dimensional mathematical or geometrical pattern generators.

$Id$
"""
__version__='$Revision$'

#from math import pi, sqrt

import numpy
from numpy.oldnumeric import around, bitwise_and, bitwise_or
from numpy import abs, add, alltrue, array, ceil, clip, cos, fft, flipud, \
        floor, exp, hstack, Infinity, linspace, multiply, nonzero, pi, \
        repeat, sin, sqrt, subtract, tile, zeros, sum, max

import param
from param.parameterized import ParamOverrides
from param import ClassSelector

import topo
# Imported here so that all PatternGenerators will be in the same package
from topo.base.patterngenerator import Constant, PatternGenerator

from topo.base.arrayutil import wrap
from topo.base.sheetcoords import SheetCoordinateSystem
from topo.misc.patternfn import gaussian,exponential,gabor,line,disk,ring,\
    sigmoid,arc_by_radian,arc_by_center,smooth_rectangle,float_error_ignore, \
    log_gaussian

from topo import numbergen
from topo.transferfn import DivisiveNormalizeL1


# Could add a Gradient class, where the brightness varies as a
# function of an equation for a plane.  This could be useful as a
# background, or to see how sharp a gradient is needed to get a
# response.

# CEBALERT: do we need this? If so, please remove this question.
class Null(Constant):
    """
    A constant pattern of zero activity.
    """
    scale = param.Number(default=0,constant=True,precedence=-1)


class HalfPlane(PatternGenerator):
    """
    Constant pattern on in half of the plane, and off in the rest,
    with optional Gaussian smoothing.
    """
    
    smoothing = param.Number(default=0.02,bounds=(0.0,None),softbounds=(0.0,0.5),
                             precedence=0.61,doc="Width of the Gaussian fall-off.")

    def function(self,p):
        if p.smoothing==0.0:
            falloff=self.pattern_y*0.0
        else:
            with float_error_ignore():
                falloff=numpy.exp(numpy.divide(-self.pattern_y*self.pattern_y,
                                                2*p.smoothing*p.smoothing))

        return numpy.where(self.pattern_y>0.0,1.0,falloff)


class Gaussian(PatternGenerator):
    """
    2D Gaussian pattern generator.

    The sigmas of the Gaussian are calculated from the size and
    aspect_ratio parameters:

      ysigma=size/2
      xsigma=ysigma*aspect_ratio

    The Gaussian is then computed for the given (x,y) values as::
    
      exp(-x^2/(2*xsigma^2) - y^2/(2*ysigma^2)
    """
    
    aspect_ratio = param.Number(default=1/0.31,bounds=(0.0,None),softbounds=(0.0,6.0),
        precedence=0.31,doc="""
        Ratio of the width to the height.
        Specifically, xsigma=ysigma*aspect_ratio (see size).""")
    
    size = param.Number(default=0.155,doc="""
        Overall size of the Gaussian, defined by:
        exp(-x^2/(2*xsigma^2) - y^2/(2*ysigma^2)
        where ysigma=size/2 and xsigma=size/2*aspect_ratio.""")

    def function(self,p):
        ysigma = p.size/2.0
        xsigma = p.aspect_ratio*ysigma
        
        return gaussian(self.pattern_x,self.pattern_y,xsigma,ysigma)


class ExponentialDecay(PatternGenerator):
    """
    2D Exponential pattern generator.

    Exponential decay based on distance from a central peak,
    i.e. exp(-d), where d is the distance from the center (assuming
    size=1.0 and aspect_ratio==1.0).  More generally, the size and
    aspect ratio determine the scaling of x and y dimensions:

      yscale=size/2
      xscale=yscale*aspect_ratio

    The exponential is then computed for the given (x,y) values as::
    
      exp(-sqrt((x/xscale)^2 - (y/yscale)^2))
    """
    
    aspect_ratio = param.Number(default=1/0.31,bounds=(0.0,None),softbounds=(0.0,2.0),
        precedence=0.31,doc="""Ratio of the width to the height.""")
    
    size = param.Number(default=0.155,doc="""
        Overall scaling of the x and y dimensions.""")

    def function(self,p):
        yscale = p.size/2.0
        xscale = p.aspect_ratio*yscale
        
        return exponential(self.pattern_x,self.pattern_y,xscale,yscale)


class SineGrating(PatternGenerator):
    """2D sine grating pattern generator."""
    
    frequency = param.Number(default=2.4,bounds=(0.0,None),softbounds=(0.0,10.0),
                       precedence=0.50, doc="Frequency of the sine grating.")
    
    phase     = param.Number(default=0.0,bounds=(0.0,None),softbounds=(0.0,2*pi),
                       precedence=0.51,doc="Phase of the sine grating.")

    def function(self,p):
        """Return a sine grating pattern (two-dimensional sine wave)."""
        return 0.5 + 0.5*sin(p.frequency*2*pi*self.pattern_y + p.phase)        



class Gabor(PatternGenerator):
    """2D Gabor pattern generator."""
    
    frequency = param.Number(default=2.4,bounds=(0.0,None),softbounds=(0.0,10.0),
        precedence=0.50,doc="Frequency of the sine grating component.")
    
    phase = param.Number(default=0.0,bounds=(0.0,None),softbounds=(0.0,2*pi),
        precedence=0.51,doc="Phase of the sine grating component.")
    
    aspect_ratio = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,2.0),
        precedence=0.31,doc=
        """
        Ratio of pattern width to height.
        The width of the Gaussian component is size*aspect_ratio (see Gaussian).
        """)
    
    size = param.Number(default=0.25,doc="""
        Determines the height of the Gaussian component (see Gaussian).""")

    def function(self,p):
        height = p.size/2.0
        width = p.aspect_ratio*height
        
        return gabor(self.pattern_x,self.pattern_y,width,height,
                     p.frequency,p.phase)


class Line(PatternGenerator):
    """2D line pattern generator."""

    thickness   = param.Number(default=0.006,bounds=(0.0,None),softbounds=(0.0,1.0),
                         precedence=0.60,
                         doc="Thickness (width) of the solid central part of the line.")
    smoothing = param.Number(default=0.05,bounds=(0.0,None),softbounds=(0.0,0.5),
                       precedence=0.61,
                       doc="Width of the Gaussian fall-off.")

    def function(self,p):
        return line(self.pattern_y,p.thickness,p.smoothing)


class Disk(PatternGenerator):
    """
    2D disk pattern generator.

    An elliptical disk can be obtained by adjusting the aspect_ratio of a circular
    disk; this transforms a circle into an ellipse by stretching the circle in the
    y (vertical) direction.

    The Gaussian fall-off at a point P is an approximation for non-circular disks,
    since the point on the ellipse closest to P is taken to be the same point as
    the point on the circle before stretching that was closest to P.
    """

    aspect_ratio  = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,2.0),
        precedence=0.31,doc=
        "Ratio of width to height; size*aspect_ratio gives the width of the disk.")

    size  = param.Number(default=0.5,doc="Top to bottom height of the disk")
    
    smoothing = param.Number(default=0.1,bounds=(0.0,None),softbounds=(0.0,0.5),
                       precedence=0.61,doc="Width of the Gaussian fall-off")
    
    def function(self,p):
        height = p.size

        if p.aspect_ratio==0.0:
            return self.pattern_x*0.0

        return disk(self.pattern_x/p.aspect_ratio,self.pattern_y,height,
                    p.smoothing)


class Ring(PatternGenerator):
    """
    2D ring pattern generator.

    See the Disk class for a note about the Gaussian fall-off.
    """

    thickness = param.Number(default=0.015,bounds=(0.0,None),softbounds=(0.0,0.5),
        precedence=0.60,doc="Thickness (line width) of the ring.")
    
    smoothing = param.Number(default=0.1,bounds=(0.0,None),softbounds=(0.0,0.5),
        precedence=0.61,doc="Width of the Gaussian fall-off inside and outside the ring.")
    
    aspect_ratio = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,2.0),
        precedence=0.31,doc=
        "Ratio of width to height; size*aspect_ratio gives the overall width.")
    
    size = param.Number(default=0.5)

    def function(self,p):
        height = p.size
        if p.aspect_ratio==0.0:
            return self.pattern_x*0.0

        return ring(self.pattern_x/p.aspect_ratio,self.pattern_y,height,
                    p.thickness,p.smoothing)
    

class OrientationContrast(SineGrating):
    """
    Circular pattern for testing responses to differences in contrast.

    The pattern contains a sine grating ring surrounding a sine grating disk, each
    with parameters (orientation, size, scale and offset) that can be
    changed independently.
    """
 
    orientationcenter   = param.Number(default=0.0,bounds=(0.0,2*pi), doc="Orientation of the center grating.")
    orientationsurround = param.Number(default=0.0,bounds=(0.0,2*pi), doc="Orientation of the surround grating.")
    sizecenter     = param.Number(default=0.5,bounds=(0.0,None),softbounds=(0.0,10.0), doc="Size of the center grating.")
    sizesurround   = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,10.0), doc="Size of the surround grating.")
    scalecenter    = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,10.0), doc="Scale of the center grating.")
    scalesurround  = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,10.0), doc="Scale of the surround grating.")
    offsetcenter   = param.Number(default=0.0,bounds=(0.0,None),softbounds=(0.0,10.0), doc="Offset of the center grating.")
    offsetsurround = param.Number(default=0.0,bounds=(0.0,None),softbounds=(0.0,10.0), doc="Offset of the surround grating.")
    smoothing      = param.Number(default=0.0,bounds=(0.0,None),softbounds=(0.0,0.5),  doc="Width of the Gaussian fall-off inside and outside the ring.")
    thickness      = param.Number(default=0.015,bounds=(0.0,None),softbounds=(0.0,0.5),doc="Thickness (line width) of the ring.")
    aspect_ratio   = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,2.0),  doc="Ratio of width to height; size*aspect_ratio gives the overall width.")
    size           = param.Number(default=0.5)

    def __call__(self,**params_to_override):
        p = ParamOverrides(self,params_to_override)
        input_1=SineGrating(mask_shape=Disk(smoothing=0,size=1.0),phase=p.phase, frequency=p.frequency,
                            orientation=p.orientationcenter,
                            scale=p.scalecenter, offset=p.offsetcenter,
                            x=p.x, y=p.y,size=p.sizecenter)
        input_2=SineGrating(mask_shape=Ring(thickness=p.thickness,smoothing=0,size=1.0),phase=p.phase, frequency=p.frequency,
                            orientation=p.orientationsurround, scale=p.scalesurround, offset=p.offsetsurround,
                            x=p.x, y=p.y, size=p.sizesurround)

        patterns = [input_1(xdensity=p.xdensity,ydensity=p.ydensity,bounds=p.bounds),
                    input_2(xdensity=p.xdensity,ydensity=p.ydensity,bounds=p.bounds)]
                      
        image_array = numpy.add.reduce(patterns)
        return image_array



class RawRectangle(PatternGenerator):
    """
    2D rectangle pattern generator with no smoothing, for use when drawing
    patterns pixel by pixel.
    """
    
    aspect_ratio   = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,2.0),
        precedence=0.31,doc=
        "Ratio of width to height; size*aspect_ratio gives the width of the rectangle.")
    
    size  = param.Number(default=0.5,doc="Height of the rectangle.")

    def function(self,p):
        height = p.size
        width = p.aspect_ratio*height
        return bitwise_and(abs(self.pattern_x)<=width/2.0,
                           abs(self.pattern_y)<=height/2.0)



class Rectangle(PatternGenerator):
    """2D rectangle pattern, with Gaussian smoothing around the edges."""

    aspect_ratio = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,6.0),
        precedence=0.31,doc=
        "Ratio of width to height; size*aspect_ratio gives the width of the rectangle.")
    
    size = param.Number(default=0.5,doc="Height of the rectangle.")

    smoothing = param.Number(default=0.05,bounds=(0.0,None),softbounds=(0.0,0.5),
        precedence=0.61,doc="Width of the Gaussian fall-off outside the rectangle.")

    def function(self,p):
        height=p.size
        width=p.aspect_ratio*height

        return smooth_rectangle(self.pattern_x, self.pattern_y, 
                                width, height, p.smoothing, p.smoothing)



class Arc(PatternGenerator):
    """
    2D arc pattern generator.
    
    Draws an arc (partial ring) of the specified size (radius*2),
    starting at radian 0.0 and ending at arc_length.  The orientation
    can be changed to choose other start locations.  The pattern is
    centered at the center of the ring.

    See the Disk class for a note about the Gaussian fall-off.
    """

    aspect_ratio = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,6.0),
        precedence=0.31,doc="""
        Ratio of width to height; size*aspect_ratio gives the overall width.""")

    thickness = param.Number(default=0.015,bounds=(0.0,None),softbounds=(0.0,0.5),
        precedence=0.60,doc="Thickness (line width) of the ring.")
    
    smoothing = param.Number(default=0.05,bounds=(0.0,None),softbounds=(0.0,0.5),
        precedence=0.61,doc="Width of the Gaussian fall-off inside and outside the ring.")

    arc_length = param.Number(default=pi,bounds=(0.0,None),softbounds=(0.0,2.0*pi),
                              inclusive_bounds=(True,False),precedence=0.62, doc="""
        Length of the arc, in radians, starting from orientation 0.0.""")

    size = param.Number(default=0.5)

    def function(self,p):
        if p.aspect_ratio==0.0:
            return self.pattern_x*0.0

        return arc_by_radian(self.pattern_x/p.aspect_ratio, self.pattern_y, p.size,
                             (2*pi-p.arc_length, 0.0), p.thickness, p.smoothing)


class Curve(Arc):
    """
    2D curve pattern generator.

    Based on Arc, but centered on a tangent point midway through the
    arc, rather than at the center of a ring, and with curvature
    controlled directly rather than through the overall size of the
    pattern.

    Depending on the size_type, the size parameter can control either
    the width of the pattern, keeping this constant regardless of
    curvature, or the length of the curve, keeping that constant
    instead (as for a long thin object being bent).

    Specifically, for size_type=='constant_length', the curvature
    parameter determines the ratio of height to width of the arc, with
    positive curvature for concave shape and negative for convex. The
    size parameter determines the width of the curve.

    For size_type=='constant_width', the curvature parameter
    determines the portion of curve radian to 2pi, and the curve
    radius is changed accordingly following the formula::

      size=2pi*radius*curvature

    Thus, the size parameter determines the total length of the
    curve. Positive curvature stands for concave shape, and negative
    for convex.

    See the Disk class for a note about the Gaussian fall-off.
    """

    # Hide unused parameters
    arc_length = param.Number(precedence=-1.0)
    aspect_ratio = param.Number(default=1.0, precedence=-1.0)

    size_type = param.ObjectSelector(default='constant_length',
        objects=['constant_length','constant_width'],precedence=0.61,doc="""
        For a given size, whether to draw a curve with that total length, 
        or with that width, keeping it constant as curvature is varied.""")

    curvature = param.Number(default=0.5, bounds=(-0.5, 0.5), precedence=0.62, doc="""
        Ratio of height to width of the arc, with positive value giving
        a concave shape and negative value giving convex.""")

    def function(self,p):
        return arc_by_center(self.pattern_x/p.aspect_ratio,self.pattern_y, 
                             (p.size,p.size*p.curvature),
                             (p.size_type=='constant_length'), 
                             p.thickness, p.smoothing)



#JABALERT: Can't this be replaced with a Composite?
class TwoRectangles(Rectangle):
    """Two 2D rectangle pattern generator."""

    x1 = param.Number(default=-0.15,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                doc="X center of rectangle 1.")
    
    y1 = param.Number(default=-0.15,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                doc="Y center of rectangle 1.")
    
    x2 = param.Number(default=0.15,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                doc="X center of rectangle 2.")
    
    y2 = param.Number(default=0.15,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                doc="Y center of rectangle 2.")

    # YC: Maybe this can be implemented much more cleanly by calling
    # the parent's function() twice, but it's hard to see how to 
    # set the (x,y) offset for the parent.
    def function(self,p):
        height = p.size
        width = p.aspect_ratio*height

        return bitwise_or(
               bitwise_and(bitwise_and(
                        (self.pattern_x-p.x1)<=p.x1+width/4.0,
                        (self.pattern_x-p.x1)>=p.x1-width/4.0),
                      bitwise_and(
                        (self.pattern_y-p.y1)<=p.y1+height/4.0,
                        (self.pattern_y-p.y1)>=p.y1-height/4.0)),
               bitwise_and(bitwise_and(
                        (self.pattern_x-p.x2)<=p.x2+width/4.0,
                        (self.pattern_x-p.x2)>=p.x2-width/4.0),
                      bitwise_and(
                        (self.pattern_y-p.y2)<=p.y2+height/4.0,
                        (self.pattern_y-p.y2)>=p.y2-height/4.0)))


class SquareGrating(PatternGenerator):
    """2D squarewave grating pattern generator."""
    
    frequency = param.Number(default=2.4,bounds=(0.0,None),softbounds=(0.0,10.0),
        precedence=0.50,doc="Frequency of the square grating.")
    
    phase     = param.Number(default=0.0,bounds=(0.0,None),softbounds=(0.0,2*pi),
        precedence=0.51,doc="Phase of the square grating.")

    # We will probably want to add anti-aliasing to this,
    # and there might be an easier way to do it than by
    # cropping a sine grating.

    def function(self,p):
        """
        Return a square-wave grating (alternating black and white bars).
        """
        return around(0.5 + 0.5*sin(p.frequency*2*pi*self.pattern_y + p.phase))


# CB: I removed motion_sign from this class because I think it is
# unnecessary. But maybe I misunderstood the original author's
# intention?
#
# In any case, the original implementation was incorrect - it was not
# possible to get some motion directions (directions in one whole
# quadrant were missed out).
#
# Note that to get a 2pi range of directions, one must use a 2pi range
# of orientations (there are two directions for any given
# orientation).  Alternatively, we could generate a random sign, and
# use an orientation restricted to a pi range.

class Sweeper(PatternGenerator):
    """
    PatternGenerator that sweeps a supplied PatternGenerator in a direction
    perpendicular to its orientation.
    """

    generator = param.Parameter(default=Gaussian(),precedence=0.97, doc="Pattern to sweep.")

    speed = param.Number(default=0.25,bounds=(0.0,None),doc="""
        Sweep speed: number of sheet coordinate units per unit time.""")

    step = param.Number(default=1,doc="""
        Number of steps at the given speed to move in the sweep direction.
        The distance moved is speed*step.""")

    # Provide access to value needed for measuring maps
    def __get_phase(self): return self.generator.phase
    def __set_phase(self,new_val): self.generator.phase = new_val
    phase = property(__get_phase,__set_phase)

    def function(self,p):
        """Selects and returns one of the patterns in the list."""
        pg = p.generator
        motion_orientation=p.orientation+pi/2.0

        new_x = p.x+p.size*pg.x
        new_y = p.y+p.size*pg.y
        
        image_array = pg(xdensity=p.xdensity,ydensity=p.ydensity,bounds=p.bounds,
                         x=new_x + p.speed*p.step*cos(motion_orientation),
                         y=new_y + p.speed*p.step*sin(motion_orientation),
                         orientation=p.orientation,
                         scale=pg.scale*p.scale,offset=pg.offset+p.offset)
        
        return image_array


class Composite(PatternGenerator):
    """
    PatternGenerator that accepts a list of other PatternGenerators.
    To create a new pattern, asks each of the PatternGenerators in the
    list to create a pattern, then it combines the patterns to create a 
    single pattern that it returns.
    """

    # The Accum_Replace operator from LISSOM is not yet supported,
    # but it should be added once PatternGenerator bounding boxes
    # are respected and/or GenericImage patterns support transparency.
    operator = param.Parameter(numpy.maximum,precedence=0.98,doc="""
        Binary Numpy function used to combine the individual patterns.

        Any binary Numpy array "ufunc" returning the same
        type of array as the operands and supporting the reduce
        operator is allowed here.  Supported ufuncs include::

          add
          subtract
          multiply
          divide
          maximum
          minimum
          remainder
          power
          logical_and
          logical_or
          logical_xor

        The most useful ones are probably add and maximum, but there
        are uses for at least some of the others as well (e.g. to
        remove pieces of other patterns).

        You can also write your own operators, by making a class that
        has a static method named "reduce" that returns an array of the
        same size and type as the arrays in the list.  For example::
        
          class return_first(object):
              @staticmethod
              def reduce(x):
                  return x[0]
              
        """)
    
    generators = param.List(default=[Constant(scale=0.0)],precedence=0.97,
        class_=PatternGenerator,doc="""
        List of patterns to use in the composite pattern.  The default is
        a blank pattern, and should thus be overridden for any useful work.""")

    size  = param.Number(default=1.0,doc="Scaling factor applied to all sub-patterns.")

    
    def _advance_pattern_generators(self,p):
        """
        Subclasses can override this method to provide constraints on
        the values of generators' parameters and/or eliminate
        generators from this list if necessary.
        """
        return p.generators

        
    # JABALERT: To support large numbers of patterns on a large input region,
    # should be changed to evaluate each pattern in a small box, and then
    # combine them at the full Composite Bounding box size.
    def function(self,p):
        """Constructs combined pattern out of the individual ones."""
        generators = self._advance_pattern_generators(p)

        assert hasattr(p.operator,'reduce'),repr(p.operator)+" does not support 'reduce'."

        # CEBALERT: mask gets applied by all PGs including the Composite itself
        # (leads to redundant calculations in current lissom_oo_or usage, but
        # will lead to problems/limitations in the future).
        patterns = [pg(xdensity=p.xdensity,ydensity=p.ydensity,
                       bounds=p.bounds,mask=p.mask,
                       x=p.x+p.size*(pg.x*cos(p.orientation)- pg.y*sin(p.orientation)),
                       y=p.y+p.size*(pg.x*sin(p.orientation)+ pg.y*cos(p.orientation)),
                       orientation=pg.orientation+p.orientation,
                       size=pg.size*p.size)
                    for pg in generators]
        image_array = p.operator.reduce(patterns)
        return image_array



class SeparatedComposite(Composite):
    """
    Generalized version of the Composite PatternGenerator that enforces spacing constraints
    between pattern centers.

    Currently supports minimum spacing, but can be generalized to
    support maximum spacing also (and both at once).
    """

    min_separation = param.Number(default=0.0, bounds = (0,None),
                            softbounds = (0.0,1.0), doc="""
        Minimum distance to enforce between all pairs of pattern centers.

        Useful for ensuring that multiple randomly generated patterns
        do not overlap spatially.  Note that as this this value is
        increased relative to the area in which locations are chosen,
        the likelihood of a pattern appearing near the center of the
        area will decrease.  As this value approaches the available
        area, the corners become far more likely to be chosen, due to
        the distances being greater along the diagonals.
        """)
        ### JABNOTE: Should provide a mechanism for collecting and
        ### plotting the training pattern center distribution, so that
        ### such issues can be checked.

    max_trials = param.Integer(default = 50, bounds = (0,None),
                         softbounds = (0,100), precedence=-1, doc="""
        Number of times to try for a new pattern location that meets the criteria.
        
        This is an essentially arbitrary timeout value that helps
        prevent an endless loop in case the requirements cannot be
        met.""")

        
    def __distance_valid(self, g0, g1, p):
        """
        Returns true if the distance between the (x,y) locations of two generators
        g0 and g1 is greater than a minimum separation.

        Can be extended easily to support other criteria.
        """
        dist = sqrt((g1.x - g0.x) ** 2 +
                    (g1.y - g0.y) ** 2)
        return dist >= p.min_separation


    def _advance_pattern_generators(self,p):
        """
        Advance the parameters for each generator for this presentation.

        Picks a position for each generator that is accepted by __distance_valid
        for all combinations.  Returns a new list of the generators, with
        some potentially omitted due to failure to meet the constraints.
        """
        
        valid_generators = []
        for g in p.generators:
            
            for trial in xrange(self.max_trials):
                # Generate a new position and add generator if it's ok
                
                if alltrue([self.__distance_valid(g,v,p) for v in valid_generators]):
                    valid_generators.append(g)
                    break
                
                g.force_new_dynamic_value('x')
                g.force_new_dynamic_value('y')
                
            else:
                self.warning("Unable to place pattern %s subject to given constraints" %
                             g.name)

        return valid_generators



class Selector(PatternGenerator):
    """
    PatternGenerator that selects from a list of other PatternGenerators.
    """

    generators = param.List(precedence=0.97,class_=PatternGenerator,bounds=(1,None),
        default=[Disk(x=-0.3,aspect_ratio=0.5), Rectangle(x=0.3,aspect_ratio=0.5)],
        doc="List of patterns from which to select.")

    size = param.Number(default=1.0,doc="Scaling factor applied to all sub-patterns.")

    # CB: needs to have time_fn=None
    index = param.Number(default=numbergen.UniformRandom(lbound=0,ubound=1.0,seed=76),
        bounds=(-1.0,1.0),precedence=0.20,doc="""
        Index into the list of pattern generators, on a scale from 0
        (start of the list) to 1.0 (end of the list).  Typically a
        random value or other number generator, to allow a different item
        to be selected each time.""")


    def function(self,p):
        """Selects and returns one of the patterns in the list."""
        int_index=int(len(p.generators)*wrap(0,1.0,p.index))
        pg=p.generators[int_index]

        image_array = pg(xdensity=p.xdensity,ydensity=p.ydensity,bounds=p.bounds,
                         x=p.x+p.size*(pg.x*cos(p.orientation)-pg.y*sin(p.orientation)),
                         y=p.y+p.size*(pg.x*sin(p.orientation)+pg.y*cos(p.orientation)),
                         orientation=pg.orientation+p.orientation,size=pg.size*p.size,
                         scale=pg.scale*p.scale,offset=pg.offset+p.offset)
                       
        return image_array

    def get_current_generator(self):
        """Return the current generator (as specified by self.index)."""
        int_index=int(len(self.generators)*wrap(0,1.0,self.inspect_value('index')))
        return self.generators[int_index]




### JABALERT: This class should be eliminated if at all possible; it
### is just a specialized version of Composite, and should be
### implementable directly using what is already in Composite.    
class GaussiansCorner(PatternGenerator):
    """
    Two Gaussian pattern generators with a variable intersection point, 
    appearing as a corner or cross.
    """
    
    x = param.Number(default=-0.15,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                doc="X center of the corner")
    
    y = param.Number(default=-0.15,bounds=(-1.0,1.0),softbounds=(-0.5,0.5),
                doc="Y center of the corner")
                
    size = param.Number(default=0.5,bounds=(0,None), softbounds=(0.1,1),
                doc="The size of the corner")
    
    aspect_ratio = param.Number(default=1/0.31, bounds=(0,None), softbounds=(1,10),
                doc="Ratio of the width to the height for both Gaussians")
                
    angle = param.Number(default=0.5*pi,bounds=(0,pi), softbounds=(0.01*pi,0.99*pi),
                doc="The angle of the corner")
                
    cross = param.Number(default=0.4, bounds=(0,1), softbounds=(0,1),
                doc="Where the two Gaussians cross, as a fraction of their half length")
    

    def __call__(self,**params_to_override):
        p = ParamOverrides(self,params_to_override)
        
        g_1 = Gaussian()
        g_2 = Gaussian()
        
        x_1 = g_1(orientation = p.orientation, bounds = p.bounds, xdensity = p.xdensity,
                            ydensity = p.ydensity, offset = p.offset, size = p.size,
                            aspect_ratio = p.aspect_ratio,
                            x = p.x + 0.7 * cos(p.orientation) * p.cross * p.size * p.aspect_ratio,
                            y = p.y + 0.7 * sin(p.orientation) * p.cross * p.size * p.aspect_ratio)
        x_2 = g_2(orientation = p.orientation+p.angle, bounds = p.bounds, xdensity = p.xdensity,
                            ydensity = p.ydensity, offset = p.offset, size = p.size,
                            aspect_ratio = p.aspect_ratio,
                            x = p.x + 0.7 * cos(p.orientation+p.angle) * p.cross * p.size * p.aspect_ratio,
                            y = p.y + 0.7 * sin(p.orientation+p.angle) * p.cross * p.size * p.aspect_ratio)
        
        return numpy.maximum( x_1, x_2 )



class Translator(PatternGenerator):
    """
    PatternGenerator that translates another PatternGenerator over
    time.

    This PatternGenerator will create a series of episodes, where in
    each episode the underlying generator is moved in a fixed
    direction at a fixed speed.  To begin an episode, the Translator's
    x, y, and direction are evaluated (e.g. from random
    distributions), and the underlying generator is then drawn at
    those values plus changes over time that are determined by the
    speed.  The orientation of the underlying generator should be set
    to 0 to get motion perpendicular to the generator's orientation
    (which is typical).

    Note that at present the parameter values for x, y, and direction
    cannot be passed in when the instance is called; only the values
    set on the instance are used.
    """
    generator = param.ClassSelector(default=Gaussian(),
        class_=PatternGenerator,doc="""Pattern to be translated.""")

    direction = param.Number(default=0.0,softbounds=(-pi,pi),doc="""
        The direction in which the pattern should move, in radians.""")
    
    speed = param.Number(default=0.01,bounds=(0.0,None),doc="""
        The speed with which the pattern should move,
        in sheet coordinates per simulation time unit.""")

    reset_period = param.Number(default=1,bounds=(0.0,None),doc="""
        Period between generating each new translation episode.""")

    episode_interval = param.Number(default=0,doc="""
        Interval between successive translation episodes.
        
        If nonzero, the episode_separator pattern is presented for
        this amount of simulation time after each episode, e.g. to
        allow processing of the previous episode to complete.""")

    episode_separator = param.ClassSelector(default=Constant(scale=0.0),
         class_=PatternGenerator,doc="""
         Pattern to display during the episode_interval, if any.
         The default is a blank pattern.""")
                                                                              

    def _advance_params(self):
        """
        Explicitly generate new values for these parameters only
        when appropriate.
        """
        for param in ['x','y','direction']:
            self.force_new_dynamic_value(param)
        self.last_time = topo.sim.time()

       
    def __init__(self,**params):
        super(Translator,self).__init__(**params)
        self._advance_params()

        
    def __call__(self,**params_to_override):
        p=ParamOverrides(self,params_to_override)
        
        if topo.sim.time() >= self.last_time + p.reset_period:
            ## Returns early if within episode interval
            if topo.sim.time()<self.last_time+p.reset_period+p.episode_interval:
                return p.episode_separator(xdensity=p.xdensity,
                                           ydensity=p.ydensity,
                                           bounds=p.bounds)
            else:
                self._advance_params()

        # JABALERT: Does not allow x, y, or direction to be passed in
        # to the call; fixing this would require implementing
        # inspect_value and force_new_dynamic_value (for
        # use in _advance_params) for ParamOverrides.
        #
        # Access parameter values without giving them new values
        assert ('x' not in params_to_override and
                'y' not in params_to_override and
                'direction' not in params_to_override)
        x = self.inspect_value('x')
        y = self.inspect_value('y')
        direction = self.inspect_value('direction')

        # compute how much time elapsed from the last reset
        # float(t) required because time could be e.g. gmpy.mpq
        t = float(topo.sim.time()-self.last_time)

        ## CEBALERT: mask gets applied twice, both for the underlying
        ## generator and for this one.  (leads to redundant
        ## calculations in current lissom_oo_or usage, but will lead
        ## to problems/limitations in the future).
        return p.generator(
            xdensity=p.xdensity,ydensity=p.ydensity,bounds=p.bounds,
            x=x+t*cos(direction)*p.speed+p.generator.x,
            y=y+t*sin(direction)*p.speed+p.generator.y,
            orientation=(direction-pi/2)+p.generator.orientation)



class DifferenceOfGaussians(PatternGenerator):
    """
    Two-dimensional difference of gaussians pattern.
    """

    positive_size = param.Number(default=0.1, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(1), 
        doc="""Size of the positive region of the pattern.""")
    
    positive_aspect_ratio = param.Number(default=1.5, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(2), 
        doc="""Ratio of width to height for the positive region of the pattern.""")
    
    positive_x = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0), precedence=(3), 
        doc="""X position for the central peak of the positive region.""")
    
    positive_y = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0), precedence=(4), 
        doc="""Y position for the central peak of the positive region.""")


    negative_size = param.Number(default=0.3, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(5), 
        doc="""Size of the negative region of the pattern.""")
    
    negative_aspect_ratio = param.Number(default=1.5, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(6), 
        doc="""Ratio of width to height for the negative region of the pattern.""")
    
    negative_x = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0), precedence=(7), 
        doc="""X position for the central peak of the negative region.""")
    
    negative_y = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0), precedence=(8), 
        doc="""Y position for the central peak of the negative region.""")
    
    
    def function(self, p):
        positive = Gaussian(x=p.positive_x+p.x, y=p.positive_y+p.y,
            size=p.positive_size*p.size, aspect_ratio=p.positive_aspect_ratio,
            orientation=p.orientation, output_fns=[DivisiveNormalizeL1()])
                                    
        negative = Gaussian(x=p.negative_x+p.x, y=p.negative_y+p.y,
            size=p.negative_size*p.size, aspect_ratio=p.negative_aspect_ratio,
            orientation=p.orientation, output_fns=[DivisiveNormalizeL1()])
        
        return Composite(generators=[positive,negative], operator=numpy.subtract,
            xdensity=p.xdensity, ydensity=p.ydensity, bounds=p.bounds)()
              
                                  
                        
class Sigmoid(PatternGenerator):
    """
    Two-dimensional sigmoid pattern, dividing the plane into positive
    and negative halves with a smoothly sloping transition between them.
    """
    
    slope = param.Number(default=10.0, bounds=(None,None), softbounds=(-100.0,100.0),
        doc="""Parameter controlling the smoothness of the transition 
        between the two regions; high values give a sharp transition.""")


    def function(self, p):
        return sigmoid(self.pattern_y, p.slope)
         
         

class SigmoidedDoG(PatternGenerator):
    """
    Sigmoid multiplicatively combined with a difference of Gaussians,
    such that one part of the plane can be the mirror image of the other.
    """
    
    size = param.Number(default=0.5)
    
    positive_size = param.Number(default=0.15, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(1), 
        doc="""Size of the positive Gaussian pattern.""")
    
    positive_aspect_ratio = param.Number(default=2.0, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(2), 
        doc="""Ratio of width to height for the positive Gaussian pattern.""")
    
    negative_size = param.Number(default=0.25, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(3), 
        doc="""Size of the negative Gaussian pattern.""")
    
    negative_aspect_ratio = param.Number(default=1.0, bounds=(0.0,None), softbounds=(0.0,5.0), precedence=(4), 
        doc="""Ratio of width to height for the negative Gaussian pattern.""")
    
    sigmoid_slope = param.Number(default=10.0, bounds=(None,None), softbounds=(-100.0,100.0), precedence=(5), 
        doc="""Parameter controlling the smoothness of the transition between the two regions; 
            high values give a sharp transition.""")
            
    sigmoid_position = param.Number(default=0.0, bounds=(None,None), softbounds=(-1.0,1.0), precedence=(6), 
        doc="""X position of the transition between the two regions.""")
                 
                                                                                                                                                             
    def function(self, p):
        diff_of_gaussians = DifferenceOfGaussians(positive_x=p.x, positive_y=p.y, negative_x=p.x, negative_y=p.y,
            positive_size=p.positive_size*p.size, positive_aspect_ratio=p.positive_aspect_ratio,
            negative_size=p.negative_size*p.size, negative_aspect_ratio=p.negative_aspect_ratio)

        sigmoid = Sigmoid(slope=p.sigmoid_slope, orientation=p.orientation+pi/2, x=p.x+p.sigmoid_position)

        return Composite(generators=[diff_of_gaussians, sigmoid], bounds=p.bounds,
            operator=numpy.multiply, xdensity=p.xdensity, ydensity=p.ydensity)()



class LogGaussian(PatternGenerator):
    """
    2D Log Gaussian pattern generator allowing standard gaussian 
    patterns but with the added advantage of movable peaks.

    The spread governs decay rates from the peak of the Gaussian,
    mathematically this is the sigma term.

    The center governs the peak position of the Gaussian,
    mathematically this is the mean term.
    """
    
    aspect_ratio = param.Number(default=0.5, bounds=(0.0,None), inclusive_bounds=(True,False), softbounds=(0.0,1.0),
        doc="""Ratio of the pattern's width to height.""")
    
    x_shape = param.Number(default=0.8, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,5.0),
        doc="""The length of the tail along the x axis.""")

    y_shape = param.Number(default=0.35, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,5.0),
        doc="""The length of the tail along the y axis.""")
    

    def __call__(self, **params_to_override):
        """
        Call the subclass's 'function' method on a rotated and scaled coordinate system.

        Creates and fills an array with the requested pattern.  If
        called without any params, uses the values for the Parameters
        as currently set on the object. Otherwise, any params
        specified override those currently set on the object.
        """
        p = ParamOverrides(self, params_to_override)

        self._setup_xy(p)
        fn_result = self.function(p)
        self._apply_mask(p, fn_result)
        
        scale_factor = p.scale / max(fn_result)
        result = scale_factor*fn_result + p.offset
                    
        for of in p.output_fns:
            of(result)
                               
        return result
                               

    def _setup_xy(self, p):
        """
        Produce pattern coordinate matrices from the bounds and
        density (or rows and cols), and transforms them according to
        x, y, and orientation.
        """
        self.debug(lambda:"bounds=%s, xdensity=%s, ydensity=%s, x=%s, y=%s, orientation=%s"%(p.bounds, p.xdensity, p.ydensity, p.x, p.y, p.orientation))

        x_points,y_points = SheetCoordinateSystem(p.bounds, p.xdensity, p.ydensity).sheetcoordinates_of_matrixidx()

        self.pattern_x, self.pattern_y = self._create_and_rotate_coordinate_arrays(x_points-p.x, y_points-p.y, p)
        
    
    def _create_and_rotate_coordinate_arrays(self, x, y, p):
        """
        Create pattern matrices from x and y vectors, and rotate
        them to the specified orientation.
        """
        
        if p.aspect_ratio == 0 or p.size == 0:
            x = x * 0.0
            y = y * 0.0
        else:
            x = (x*10.0) / (p.size*p.aspect_ratio)
            y = (y*10.0) / p.size
        
        offset = exp(p.size)
        pattern_x = add.outer(sin(p.orientation)*y, cos(p.orientation)*x) + offset
        pattern_y = subtract.outer(cos(p.orientation)*y, sin(p.orientation)*x) + offset
        
        clip(pattern_x, 0, Infinity, out=pattern_x)
        clip(pattern_y, 0, Infinity, out=pattern_y)
        
        return pattern_x, pattern_y


    def function(self, p):
        return log_gaussian(self.pattern_x, self.pattern_y, p.x_shape, p.y_shape, p.size)


        
class SigmoidedDoLG(PatternGenerator):
    """
    Sigmoid multiplicatively combined with a difference of Log Gaussians, such that one part of the plane can be 
    the mirror image of the other, and the peaks of the gaussians are movable.
    """    
    
    size = param.Number(default=1.5)
    
    
    positive_size = param.Number(default=0.5, bounds=(0.0,None), inclusive_bounds=(True,False), softbounds=(0.0,10.0),
        doc="""Size of the positive LogGaussian pattern.""")
    
    positive_aspect_ratio = param.Number(default=0.5, bounds=(0.0,None), inclusive_bounds=(True,False), softbounds=(0.0,1.0),
        doc="""Ratio of width to height for the positive LogGaussian pattern.""")
    
    positive_x_shape = param.Number(default=0.8, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,5.0),
        doc="""The length of the tail along the x axis for the positive LogGaussian pattern.""")

    positive_y_shape = param.Number(default=0.35, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,5.0),
        doc="""The length of the tail along the y axis for the positive LogGaussian pattern.""")

    positive_scale = param.Number(default=1.5, bounds=(0.0,None), inclusive_bounds=(True,False), softbounds=(0.0,10.0),
        doc="""Multiplicative scale for the positive LogGaussian pattern.""")


    negative_size = param.Number(default=0.8, bounds=(0.0,None), inclusive_bounds=(True,False), softbounds=(0.0,10.0),
        doc="""Size of the negative LogGaussian pattern.""")
    
    negative_aspect_ratio = param.Number(default=0.3, bounds=(0.0,None), inclusive_bounds=(True,False), softbounds=(0.0,1.0),
        doc="""Ratio of width to height for the negative LogGaussian pattern.""")
    
    negative_x_shape = param.Number(default=0.8, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,5.0),
        doc="""The length of the tail along the x axis for the negative LogGaussian pattern.""")

    negative_y_shape = param.Number(default=0.35, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,5.0),
        doc="""The length of the tail along the y axis for the negative LogGaussian pattern.""")

    negative_scale = param.Number(default=1.0, bounds=(0.0,None), inclusive_bounds=(True,False), softbounds=(0.0,10.0),
        doc="""Multiplicative scale for the negative LogGaussian pattern.""")
    
    
    sigmoid_slope = param.Number(default=50.0, bounds=(None,None), softbounds=(-100.0,100.0),
        doc="""Parameter controlling the smoothness of the transition between the two regions; 
            high values give a sharp transition.""")
            
    sigmoid_position = param.Number(default=0.05, bounds=(None,None), softbounds=(-1.0,1.0),
        doc="""X position of the transition between the two regions.""")


    def function(self, p):
        positive = LogGaussian(size=p.positive_size*p.size, aspect_ratio=p.positive_aspect_ratio, x_shape=p.positive_x_shape, 
            y_shape=p.positive_y_shape, scale=p.positive_scale*p.scale, orientation=p.orientation, x=p.x, y=p.y,
            output_fns=[])

        negative = LogGaussian(size=p.negative_size*p.size, aspect_ratio=p.negative_aspect_ratio, x_shape=p.negative_x_shape, 
            y_shape=p.negative_y_shape, scale=p.negative_scale*p.scale, orientation=p.orientation, x=p.x, y=p.y,
            output_fns=[])

        diff_of_log_gaussians = Composite(generators=[positive, negative], operator=subtract, 
            xdensity=p.xdensity, ydensity=p.ydensity, bounds=p.bounds)
        
        sigmoid = Sigmoid(x=p.x+p.sigmoid_position, slope=p.sigmoid_slope, orientation=p.orientation+pi/2.0)
        
        return Composite(generators=[diff_of_log_gaussians, sigmoid], bounds=p.bounds,
            operator=multiply, xdensity=p.xdensity, ydensity=p.ydensity, output_fns=[DivisiveNormalizeL1()])()



class TimeSeries(param.Parameterized):
    """
    Generic class to return intervals of a discretized time series.
    """
    
    time_series = param.Array(default=repeat(array([0,1]),50), 
        doc="""An array of numbers that form a series.""")

    sample_rate = param.Integer(default=50, allow_None=True, bounds=(0,None), inclusive_bounds=(False,False), softbounds=(0,44100),
        doc="""The number of samples taken per second to form the series.""")
    
    seconds_per_iteration = param.Number(default=0.1, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,1.0),
        doc="""Number of seconds advanced along the time series on each iteration.""")

    interval_length = param.Number(default=0.1, bounds=(0.0,None), inclusive_bounds=(False,False), softbounds=(0.0,1.0),
        doc="""The length of time in seconds to be returned on each iteration.""")
    
    repeat = param.Boolean(default=True, 
        doc="""Whether the signal loops or terminates once it reaches its end.""")
        
    
    def __init__(self, **params):
        super(TimeSeries, self).__init__(**params)
        self._next_interval_start = 0

        if self.seconds_per_iteration > self.interval_length:
            self.warning("Seconds per iteration > interval length, some signal will be skipped.")
    
    
    def append_signal(self, new_signal):
        self.time_series = hstack((self.time_series, new_signal))
    
    
    def extract_specific_interval(self, interval_start, interval_end):
        """
        Overload if special behaviour is required when a series ends.
        """
        
        interval_start = int(interval_start)
        interval_end = int(interval_end)
        
        if interval_start >= interval_end:
            raise ValueError("Requested interval's start point is past the requested end point.")
        
        elif interval_start > self.time_series.size:
            if self.repeat:
                interval_end = interval_end - interval_start
                interval_start = 0                
            else:
                raise ValueError("Requested interval's start point is past the end of the time series.")
            
        if interval_end < self.time_series.size:
            interval = self.time_series[interval_start:interval_end]
            
        else:
            requested_interval_size = interval_end - interval_start
            remaining_signal = self.time_series[interval_start:self.time_series.size]

            if self.repeat:
                if requested_interval_size < self.time_series.size:
                    self._next_interval_start = requested_interval_size-remaining_signal.size
                    interval = hstack((remaining_signal, self.time_series[0:self._next_interval_start]))
                
                else:
                    repeated_signal = repeat(self.time_series, floor(requested_interval_size/self.time_series.size))
                    self._next_interval_start = requested_interval_size % self.time_series.size

                    interval = (hstack((remaining_signal, repeated_signal)))[0:requested_interval_size]
                    
            else:
                self.warning("Returning last interval of the time series.")
                self._next_interval_start = self.time_series.size + 1
            
                samples_per_interval = self.interval_length*self.sample_rate
                interval = hstack((remaining_signal, zeros(samples_per_interval-remaining_signal.size)))
            
        return interval
    
    
    def __call__(self): 
        interval_start = self._next_interval_start
        interval_end = int(floor(interval_start + self.interval_length*self.sample_rate))
        
        self._next_interval_start += int(floor(self.seconds_per_iteration*self.sample_rate))
        return self.extract_specific_interval(interval_start, interval_end)



def generate_sine_wave(duration, frequency, sample_rate):
    time_axis = linspace(0.0, duration, duration*sample_rate)
    return sin(2.0*pi*frequency * time_axis)
    


class TimeSeriesParam(ClassSelector):
    """
    Parameter whose value is a TimeSeries object.
    """
    
    def __init__(self, **params):
        super(TimeSeriesParam, self).__init__(TimeSeries, **params)
            
            
            
class PowerSpectrum(PatternGenerator):
    """
    Outputs the spectral density of a rolling interval of the input
    signal each time it is called. Over time, the results could be
    arranged into a spectrogram, e.g. for an audio signal.
    """
    
    x = param.Number(precedence=(-1))
    y = param.Number(precedence=(-1))
    size = param.Number(precedence=(-1))
    orientation = param.Number(precedence=(-1))

    scale = param.Number(default=0.01, bounds=(0,None), inclusive_bounds=(False,False), softbounds=(0.001,1000),
        doc="""The amount by which to scale amplitudes by. This is useful if we want to rescale to say a range [0:1].
            
        Note: Constant scaling is preferable to dynamic scaling so as not to artificially ramp down loud sounds while ramping
        up hiss and other background interference.""")

    signal = TimeSeriesParam(default=TimeSeries(time_series=generate_sine_wave(0.1,5000,20000), sample_rate=20000), 
        doc="""A TimeSeries object on which to perfom the Fourier Transform.""")
        
    min_frequency = param.Integer(default=0, bounds=(0,None), inclusive_bounds=(True,False), softbounds=(0,10000),
        doc="""Smallest frequency for which to return an amplitude.""")

    max_frequency = param.Integer(default=9999, bounds=(0,None), inclusive_bounds=(False,False), softbounds=(0,10000),
        doc="""Largest frequency for which to return an amplitude.""")
    
    windowing_function = param.Parameter(default=None, 
        doc="""This function is multiplied with the current interval, i.e. the most recent portion of the 
        waveform interval of a signal, before performing the Fourier transform.  It thus shapes the interval, 
        which is otherwise always rectangular.

        The function chosen here dictates the tradeoff between resolving comparable signal strengths with similar 
        frequencies, and resolving disparate signal strengths with dissimilar frequencies.

        numpy provides a number of options, e.g. bartlett, blackman, hamming, hanning, kaiser; see
        http://docs.scipy.org/doc/numpy/reference/routines.window.html
        
        You may also supply your own.""")
        
        
    def __init__(self, **params):
        super(PowerSpectrum, self).__init__(**params) 
        
        self._previous_min_frequency = self.min_frequency
        self._previous_max_frequency = self.max_frequency
        
            
    def _create_frequency_indices(self):
        if self.min_frequency >= self.max_frequency:
            raise ValueError("PowerSpectrum: min frequency must be lower than max frequency.")     
            
        # calculate the discrete frequencies possible for the given sample rate.
        sample_rate = self.signal.sample_rate        
        available_frequency_range = fft.fftfreq(sample_rate, d=1.0/sample_rate)[0:sample_rate/2]

        if not available_frequency_range.min() <= self.min_frequency or not available_frequency_range.max() >= self.max_frequency:
            raise ValueError("Specified frequency interval [%s:%s] is unavailable, available range is [%s:%s]. Adjust to these frequencies or modify the sample rate of the TimeSeries object." %(self.min_frequency, self.max_frequency, available_frequency_range.min(), available_frequency_range.max()))

        min_freq = nonzero(available_frequency_range >= self.min_frequency)[0][0]
        max_freq = nonzero(available_frequency_range <= self.max_frequency)[0][-1]
        
        self._set_frequency_spacing(min_freq, max_freq)
          
              
    def _set_frequency_spacing(self, min_freq, max_freq): 
        """
        Frequency spacing to use, i.e. how to map the available frequency range to the discrete sheet rows.
        
        NOTE: We're calculating the spacing of a range between the highest and lowest frequencies, the actual 
        segmentation and averaging of the frequencies to fit this spacing occurs in _getAmplitudes().
        
        This method is here solely to provide a minimal overload if custom spacing is required.
        """
        
        self.frequency_spacing = linspace(min_freq, max_freq, num=self._sheet_dimensions[0]+1, endpoint=True)
            
            
    def _get_row_amplitudes(self):
        """
        Perform a real Discrete Fourier Transform (DFT; implemented using a Fast Fourier Transform algorithm, FFT) 
        of the current sample from the signal multiplied by the smoothing window.

        See numpy.rfft for information about the Fourier transform.
        """
        
        signal_interval = self.signal()
        sample_rate = self.signal.sample_rate        

        # A signal window *must* span one sample rate
        signal_window = tile(signal_interval, ceil(1.0/self.signal.interval_length))

        if self.windowing_function:
            smoothed_window = signal_window[0:sample_rate] * self.windowing_function(sample_rate)  
        else:
            smoothed_window = signal_window[0:sample_rate]
        
        amplitudes = (abs(fft.rfft(smoothed_window))[0:sample_rate/2] + self.offset) * self.scale
        
        for index in range(0, self._sheet_dimensions[0]-2):
            start_frequency = self.frequency_spacing[index]
            end_frequency = self.frequency_spacing[index+1]
             
            normalisation_factor =  end_frequency - start_frequency
            if normalisation_factor == 0:
                amplitudes[index] = amplitudes[start_frequency]
            else:
                amplitudes[index] = sum(amplitudes[start_frequency:end_frequency]) / normalisation_factor
        
        return flipud(amplitudes[0:self._sheet_dimensions[0]].reshape(-1,1))


    def set_matrix_dimensions(self, bounds, xdensity, ydensity):
        super(PowerSpectrum, self).set_matrix_dimensions(bounds, xdensity, ydensity) 
        
        self._sheet_dimensions = SheetCoordinateSystem(bounds, xdensity, ydensity).shape
        self._create_frequency_indices()


    def _shape_response(self, row_amplitudes):
        if self._sheet_dimensions[1] > 1:
            row_amplitudes = repeat(row_amplitudes, self._sheet_dimensions[1], axis=1)
        
        return row_amplitudes

    
    def __call__(self):        
        if self._previous_min_frequency != self.min_frequency or self._previous_max_frequency != self.max_frequency:
            self._previous_min_frequency = self.min_frequency
            self._previous_max_frequency = self.max_frequency
            self._create_frequency_indices()
        
        return self._shape_response(self._get_row_amplitudes())



class Spectrogram(PowerSpectrum):
    """
    Extends PowerSpectrum to provide a temporal buffer, yielding
    a 2D representation of a fixed-width spectrogram.
    """
    
    min_latency = param.Integer(default=0, precedence=1,
        bounds=(0,None), inclusive_bounds=(True,False), softbounds=(0,1000),
        doc="""Smallest latency (in milliseconds) for which to return amplitudes.""")

    max_latency = param.Integer(default=500, precedence=2,
        bounds=(0,None), inclusive_bounds=(False,False), softbounds=(0,1000),
        doc="""Largest latency (in milliseconds) for which to return amplitudes.""")


    def __init__(self, **params):
        super(Spectrogram, self).__init__(**params) 
        
        self._previous_min_latency = self.min_latency
        self._previous_max_latency = self.max_latency
                        
    
    def _shape_response(self, new_column):
        
        millisecs_per_iteration = self.signal.seconds_per_iteration * 1000
    
        if millisecs_per_iteration > self.max_latency:
            self._spectrogram[0:,0:] = new_column
        else:
            # Slide old values along, add new data to left hand side.
            self._spectrogram[0:, millisecs_per_iteration:] = self._spectrogram[0:, 0:self._spectrogram.shape[1]-millisecs_per_iteration]
            self._spectrogram[0:, 0:millisecs_per_iteration] = new_column
        
        sheet_representation = zeros(self._sheet_dimensions)
        
        for column in range(0,self._sheet_dimensions[1]):
            start_latency = self._latency_spacing[column]
            end_latency = self._latency_spacing[column+1]
                        
            normalisation_factor = end_latency - start_latency
            if normalisation_factor > 1:
                sheet_representation[0:, column] = sum(self._spectrogram[0:, start_latency:end_latency], axis=1) / normalisation_factor
            else:
                sheet_representation[0:, column] = self._spectrogram[0:, start_latency]
                        
        return sheet_representation
    
                 
    def set_matrix_dimensions(self, bounds, xdensity, ydensity):
        super(Spectrogram, self).set_matrix_dimensions(bounds, xdensity, ydensity)
        self._create_latency_indices()
        
    
    def _create_latency_indices(self):
        if self.min_latency >= self.max_latency:
            raise ValueError("Spectrogram: min latency must be lower than max latency.")     

        self._latency_spacing = floor(linspace(self.min_latency, self.max_latency, num=self._sheet_dimensions[1]+1, endpoint=True))
        self._spectrogram = zeros([self._sheet_dimensions[0],self.max_latency])
        

    def __call__(self):        
        if self._previous_min_latency != self.min_latency or self._previous_max_latency != self.max_latency:
            self._previous_min_latency = self.min_latency
            self._previous_max_latency = self.max_latency
            self._create_latency_indices()
        
        return super(Spectrogram, self).__call__() 



__all__ = list(set([k for k,v in locals().items() if isinstance(v,type) and issubclass(v,PatternGenerator)]))
