from __future__ import with_statement
"""
Simple two-dimensional mathematical or geometrical pattern generators.

$Id$
"""
__version__='$Revision$'

from math import pi, sqrt

import numpy
from numpy.oldnumeric import around,bitwise_and,sin,cos,bitwise_or
from numpy import asarray, float32, nonzero, zeros, shape, hstack, \
    linspace, abs, round, fft, alltrue, add, subtract, clip, Infinity

import param
from param.parameterized import ParamOverrides,as_uninitialized

import topo
# Imported here so that all PatternGenerators will be in the same package
from topo.base.patterngenerator import Constant, PatternGenerator

from topo.base.arrayutil import wrap
from topo.base.sheetcoords import SheetCoordinateSystem
from topo.misc.patternfn import gaussian,exponential,gabor,line,disk,ring,\
    sigmoid,arc_by_radian,arc_by_center,smooth_rectangle,float_error_ignore, \
    log_gaussian

from topo import numbergen


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
                
                vals = (g.force_new_dynamic_value('x'), g.force_new_dynamic_value('y'))
                
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

    positive_size = param.Number(default=0.5, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(1), doc="""Size parameter for the positive Gaussian.""")
    
    positive_aspect_ratio = param.Number(default=2.0, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(2), doc="""Aspect_ratio parameter for the positive Gaussian.""")
    
    positive_x = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0),
        precedence=(3), doc="""X position for the central peak of the positive gaussian.""")
    
    positive_y = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0),
        precedence=(4), doc="""Y position for the central peak of the positive gaussian.""")

    negative_size = param.Number(default=1.0, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(5), doc="""Size parameter for the negative Gaussian.""")
    
    negative_aspect_ratio = param.Number(default=2.0, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(6), doc="""Aspect_ratio parameter for the negative Gaussian.""")
    
    negative_x = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0),
        precedence=(7), doc="""X position for the central peak of the negative gaussian.""")
    
    negative_y = param.Number(default=0.0, bounds=(None,None), softbounds=(-2.0,2.0),
        precedence=(8), doc="""Y position for the central peak of the negative gaussian.""")
    
    def function(self, p):
        positive = Gaussian(x=p.positive_x+p.x, y=p.positive_y+p.y,
            size=p.positive_size*p.size, aspect_ratio=p.positive_aspect_ratio,
            orientation=p.orientation, output_fns=[topo.transferfn.DivisiveNormalizeL1()])
                                    
        negative = Gaussian(x=p.negative_x+p.x, y=p.negative_y+p.y,
            size=p.negative_size*p.size, aspect_ratio=p.negative_aspect_ratio,
            orientation=p.orientation, output_fns=[topo.transferfn.DivisiveNormalizeL1()])
        
        return Composite(generators=[positive,negative], operator=numpy.subtract,
            xdensity=p.xdensity, ydensity=p.ydensity, bounds=p.bounds)()
                        
                        
class Sigmoid(PatternGenerator):
    """
    Two-dimensional sigmoid pattern, dividing the plane into positive
    and negative halves with a smoothly sloping transition between them.
    """
    
    slope = param.Number(default=10.0, bounds=(None,None), softbounds=(-100.0,100.0),doc="""
        Multiplicative parameter controlling the smoothness of the transition 
        between the two regions; high values give a sharp transition.""")

    def function(self, p):
        return sigmoid(self.pattern_y, p.slope)
         

class SigmoidedDoG(PatternGenerator):
    """
    Sigmoid multiplicatively combined with a difference of Gaussians,
    such that one part of the plane can be the mirror image of the other.
    """
        
    positive_size = param.Number(default=0.5, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(1), doc="""Size parameter for the positive Gaussian.""")
    
    positive_aspect_ratio = param.Number(default=2.0, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(2), doc="""Aspect_ratio parameter for the positive Gaussian.""")
    
    negative_size = param.Number(default=1.0, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(3), doc="""Size parameter for the negative Gaussian.""")
    
    negative_aspect_ratio = param.Number(default=1.0, bounds=(0.0,None), softbounds=(0.0,5.0),
        precedence=(4), doc="""Aspect_ratio parameter for the negative Gaussian.""")
    
    sigmoid_slope = param.Number(default=10.0, bounds=(None,None), softbounds=(-100.0,100.0),
        precedence=(5), doc="""Slope parameter for the Sigmoid.""")
    
    sigmoid_x = param.Number(default=0.0, bounds=(None,None), softbounds=(-1.0,1.0),
        precedence=(6), doc="""X parameter for the Sigmoid.""")

    sigmoid_y = param.Number(default=0.0, bounds=(None,None), softbounds=(-1.0,1.0),
        precedence=(7), doc="""Y parameter for the Sigmoid.""")
                                                                                       
    def function(self, p):
        diff_of_gaussians = DifferenceOfGaussians(positive_x=p.x, positive_y=p.y, 
            negative_x=p.x, negative_y=p.y,
            positive_size=p.positive_size*p.size, positive_aspect_ratio=p.positive_aspect_ratio,
            negative_size=p.negative_size*p.size, negative_aspect_ratio=p.negative_aspect_ratio)

        sigmoid = Sigmoid(slope=p.sigmoid_slope, orientation=p.orientation+pi/2,
            x=p.sigmoid_x+p.x, y=p.sigmoid_y+p.y)

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
        
    size = param.Number(default=0.5)
    x = param.Number(default=0.0)
    y = param.Number(default=0.0)
    
    x_spread = param.Number(default=0.6,bounds=(0.0,2.0),softbounds=(0.0,1.5),
        doc="""Parameter controlling decay rate and distance from the peak of 
            the Gaussian in the x direction.""")
    
    y_spread = param.Number(default=0.6,bounds=(0.0,2.0),softbounds=(0.0,1.5),
        doc="""Parameter controlling decay rate and distance from the peak of 
            the Gaussian in the y direction.""")
                 
    x_center = param.Number(default=2.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the peak position of the Gaussian, in the 
            x direction.""")
                
    y_center = param.Number(default=2.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the peak position of the Gaussian, in the 
            y direction.""")
                    
    def _create_and_rotate_coordinate_arrays(self, x, y, orientation):
        """
        Create pattern matrices from x and y vectors, and rotate
        them to the specified orientation.
        """
        # Using this two-liner requires that x increase from left to
        # right and y decrease from left to right; I don't think it
        # can be rewritten in so little code otherwise - but please
        # prove me wrong.
        
        # Offset by 7.35 to make sure intial pattern is centred and all rotaions
        # occur about that point.
        pattern_x = add.outer(sin(orientation)*y, cos(orientation)*x) + 7.35
        pattern_y = subtract.outer(cos(orientation)*y, sin(orientation)*x) + 7.35
        
        clip(pattern_x, 0, Infinity, out=pattern_x)
        clip(pattern_y, 0, Infinity, out=pattern_y)
        
        return pattern_x, pattern_y
    
    def function(self, p):
        x_sigma = p.x_spread * self.size
        y_sigma = p.y_spread * self.size

        return log_gaussian(self.pattern_x, self.pattern_y, x_sigma, y_sigma, p.x_center, p.y_center)

        
class SigmoidedDoLG(PatternGenerator):
    """
    Sigmoid multiplicatively combined with a difference of Log Gaussians,
    such that one part of the plane can be the mirror image of the other,
    and the peaks of the gaussians are movable.
    """
    
    # center gaussian parameters
    positive_size = param.Number(default=0.4,bounds=(0.0,None),softbounds=(0.0,5.0),
        doc="""Parameter controlling the size of the positive Gaussian, independant of
            the negative Gaussian size.""")
                
    positive_x = param.Number(default=0.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the x position of the positive Gaussian, independant of
            the negative Gaussian x position.""")

    positive_y = param.Number(default=0.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the y position of the positive Gaussian, independant of
            the negative Gaussian y position.""")
        
    positive_x_spread = param.Number(default=1.0,bounds=(0.0,2.0),softbounds=(0.0,1.5),
        doc="""Parameter controlling decay rate and distance from the peak of the 
            positive Gaussian in the x direction.""")    

    positive_y_spread = param.Number(default=0.6,bounds=(0.0,2.0),softbounds=(0.0,1.5),
        doc="""Parameter controlling decay rate and distance from the peak of the 
            positive Gaussian in the y direction.""")     

    positive_x_center = param.Number(default=1.93,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the peak position of the positive Gaussian, 
            in the x direction.""")
                
    positive_y_center = param.Number(default=2.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the peak position of the positive Gaussian, 
            in the y direction.""")
            
    positive_orientation = param.Number(default=0.0,softbounds=(0.0,2*pi),
        doc="""Parameter controlling the rotation of the positive Gaussian, independant of
            the negative Gaussian orientation.""")

    # surround gaussian parameters
    negative_size = param.Number(default=0.6,bounds=(0.0,None),softbounds=(0.1,5.0),
        doc="""Parameter controlling the size of the negative Gaussian, independant of
            the positive Gaussian size.""")
             
    negative_x = param.Number(default=0.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the x position of the negative Gaussian, independant of
            the positive Gaussian x position.""")

    negative_y = param.Number(default=0.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the y position of the negative Gaussian, independant of
            the positive Gaussian y position.""")
        
    negative_x_spread = param.Number(default=0.6,bounds=(0.0,2.0),softbounds=(0.0,1.5),
        doc="""Parameter controlling decay rate and distance from the peak of the 
            negative Gaussian in the x direction.""")    
                
    negative_y_spread = param.Number(default=0.6, bounds=(0.0,2.0),softbounds=(0.0,1.5),
        doc="""Parameter controlling decay rate and distance from the peak of the 
            negative Gaussian in the y direction.""")   
                 
    negative_x_center = param.Number(default=2.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the peak position of the negative Gaussian, 
            in the x direction.""")
                
    negative_y_center = param.Number(default=2.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the peak position of the negative Gaussian, 
            in the y direction.""")
                
    negative_orientation = param.Number(default=0.0,softbounds=(0.0,2*pi),
        doc="""Parameter controlling the rotaion of the negative Gaussian, independant of
            the positive Gaussian orientation.""")
    
    # sigmoid parameters
    sigmoid_slope = param.Number(default=3.0,
        doc="""Parameter controlling the degree of slope (sharpness) of the Sigmoid.""")
    
    sigmoid_x = param.Number(default=0.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the x position of the Sigmoid, independant of
            the Difference of Gaussians.""")
                
    sigmoid_y = param.Number(default=0.0,softbounds=(-10.0,10.0),
        doc="""Parameter controlling the y position of the Sigmoid, independant of
            the Difference of Gaussians.""")
                
    sigmoid_orientation = param.Number(default=pi/2,softbounds=(0.0,2*pi),
        doc="""Parameter controlling the rotation of the Sigmoid, independant of
            the Difference of Gaussians.""")

    def function(self, p):
        positive = LogGaussian(size=p.positive_size*p.size, 
            orientation=p.positive_orientation+p.orientation, 
            x_spread=p.positive_x_spread, y_spread=p.positive_y_spread,
            x_center=p.positive_x_center, y_center=p.positive_y_center,
            x=p.positive_x+p.x, y=p.positive_y+p.y,
            output_fns=[topo.transferfn.DivisiveNormalizeL1()])
                                
        negative = LogGaussian(size=p.negative_size*p.size, 
            orientation=p.negative_orientation+p.orientation, 
            x_spread=p.negative_x_spread, y_spread=p.negative_y_spread,
            x_center=p.negative_x_center, y_center=p.negative_y_center,
            x=p.negative_x+p.x, y=p.negative_y+p.y,
            output_fns=[topo.transferfn.DivisiveNormalizeL1()])

        diff_of_log_gaussians = pattern.Composite(generators=[positive, negative], 
            operator=subtract, xdensity=p.xdensity, ydensity=p.ydensity, bounds=p.bounds)
        
        sigmoid = pattern.Sigmoid(x=p.sigmoid_x+p.x, y=p.sigmoid_y+p.y,
            slope=p.sigmoid_slope, orientation=p.sigmoid_orientation+p.orientation)
                
        return pattern.Composite(generators=[diff_of_log_gaussians, sigmoid], bounds=p.bounds,
            operator=multiply, xdensity=p.xdensity, ydensity=p.ydensity)()   


def rectangular(signal_size):
    """
    Generates a Rectangular signal smoothing window,
    """
    return [1.0]*int(signal_size)

    
class PowerSpectrum(PatternGenerator):
    """
    Outputs the spectral density of a rolling window of the input
    signal each time it is called. Over time, the results could be
    arranged into a spectrogram, e.g. for an audio signal.
    """
    # Can be instantiated by hand, but it makes little sense to do so
    # in e.g. a GUI, since it requires a "signal" array parameter to
    # do anything useful.  Alternatively, could provide a useful
    # default for "signal" (and presumably make it a parameter), so
    # that it could be instantiated at least as an example.
    __abstract=True 
    
    window_increment = param.Number(default=1,constant=True,doc="""
        The most recent portion of the signal on which to perform the Fourier
        transform, in units of 1/sample_rate, i.e., the length of a
        sliding window on which to operate.

        Note that the Fourier transform algorithm is most efficient
        for matrix sizes that are powers of 2, or that can be
        decomposed into small prime factors; see numpy.fft.rfft.""" )
        
    window_length = param.Number(default=0.0001,constant=True,doc="""
        The amount of overlap between each window, in units of 1/sample_rate.""")

    sample_rate = param.Number(default=44100,constant=True,doc="""
        Number of samples per second, which defines the range for frequency.""")

    windowing_function = param.Parameter(default=rectangular,constant=True,doc="""
        This function is multiplied with the current window, i.e. the
        most recent portion of the waveform interval of a signal, before
        performing the Fourier transform.  It thus shapes the
        interval, which would otherwise always be rectangular.

        The function chosen here dictates the tradeoff between
        resolving comparable signal strengths with similar
        frequencies, and resolving disparate signal strengths with
        dissimilar frequencies.

        numpy provides a number of options, e.g. bartlett, blackman,
        hamming, hanning, kaiser; see
        http://docs.scipy.org/doc/numpy/reference/routines.window.html
        You can also supply your own.""")

    min_frequency = param.Number(default=1,doc="""
        Smallest frequency for which to return an amplitude.""")

    max_frequency = param.Number(default=20000,doc="""
        Largest frequency for which to return an amplitude.""")
                
    def __init__(self, signal, **params):
        super(PowerSpectrum, self).__init__(**params)
        self._initialize_window_parameters(signal, **params)

    @as_uninitialized
    def _initialize_window_parameters(self, signal, **params):                
        # For subclasses: to specify the values of parameters on this, the parent class,
        # subclasses might first need access to their own parameter values. 
        # Having the window initialization in this separate method allows subclasses
        # to make the usual super.__init__(**params) call.
        for parameter,value in params.items():
            setattr(self,parameter,value)
        
        self.signal = asarray(signal, dtype=float32)        
        assert len(self.signal) > 0
        
        self._next_window_start = 0
        self._samples_per_window = int(self.window_length*self.sample_rate)
        assert self._samples_per_window > 0
        self._smoothing_window = self.windowing_function(self._samples_per_window)  

        # calculate the discrete frequencies possible through decomposition, for the given sample rate & window size.
        self._all_frequencies = fft.fftfreq(self._samples_per_window, d=1.0/self.sample_rate)[0:self._samples_per_window/2]
        assert self._all_frequencies.min() >= 0
      
    def _map_frequencies_to_rows(self, index_min_freq, index_max_freq): 
        """
        Frequency spacing to use, i.e. how to map the available frequency range
        to the discrete sheet rows.
        
        NOTE: We're actually spacing a range between the *indicies* of the highest and lowest
        frequencies, the actual frequency spacing occurs at a later stage.
        
        This method is here solely to provide a minimal overload if custom spacing is required.
        """
        self._frequency_spacing_indices = round(linspace(index_max_freq, index_min_freq, 
            num=(index_max_freq-index_min_freq), endpoint=True)).astype(int)
    
    # CEBALERT: given all the constant params, could do some caching
    def _create_frequency_indices(self, p):
        if not self._all_frequencies.min() <= p.min_frequency \
            or not self._all_frequencies.max() >= p.max_frequency:
            raise ValueError("Specified frequency interval [%s,%s] is unavailable \
                (actual interval is [%s,%s]. Adjust sample_rate and/or window_length."
                %( p.min_frequency, p.max_frequency, self._all_frequencies.min(), \
                self._all_frequencies.max()))
                
        min_freq_index = nonzero(self._all_frequencies >= p.min_frequency)[0][0]
        max_freq_index = nonzero(self._all_frequencies <= p.max_frequency)[0][-1]
        
        self._map_frequencies_to_rows(min_freq_index, max_freq_index)
    
    def _extract_sample_window(self, p):
        """
        Overload if special behaviour is required when a signal ends.
        """
        window_start = self._next_window_start
        window_end = window_start+self._samples_per_window
        
        if window_end > self.signal.size:
            raise ValueError("Reached the end of the signal.")
        
        self._next_window_start += int(self.window_increment * self.sample_rate) 
        return self.signal[window_start:window_end]
            
    def _get_amplitudes(self, p):
        """
        Perform a real Discrete Fourier Transform (DFT; implemented
        using a Fast Fourier Transform algorithm, FFT) of the current
        sample from the signal multiplied by the smoothing window.

        See numpy.rfft for information about the Fourier transform.
        """
        signal_sample = self._extract_sample_window(p)
        assert shape(signal_sample)[0] == shape(self._smoothing_window)[0]
        
        amplitudes_by_frequency = abs(fft.rfft(signal_sample * self._smoothing_window))[0 : len(signal_sample)/2]
        amplitudes_by_row = [0.0]*self._sheet_dimensions[0]
        
        indices_per_row = len(self._frequency_spacing_indices)/self._sheet_dimensions[0]
        
        for row in range(0, self._sheet_dimensions[0]):
            freq_end_index = self._frequency_spacing_indices[row*indices_per_row]+1
            freq_start_index = self._frequency_spacing_indices[(row*indices_per_row)+indices_per_row]

            amplitudes_by_row[row] = sum(amplitudes_by_frequency[freq_start_index:freq_end_index])/indices_per_row
            
        return (asarray(amplitudes_by_row, float32).reshape(-1,1))        
        
    def __call__(self, **params_to_override):
        p = ParamOverrides(self, params_to_override)
        
        self._sheet_dimensions = SheetCoordinateSystem(p.bounds, p.xdensity, p.ydensity).shape
        self._create_indices(p)
        
        return self._get_amplitudes(p)
    

class Spectrogram(PowerSpectrum):
    """
    Extends PowerSpectrum to provide a temporal buffer, yielding
    a 2D representation of a fixed-width spectrogram.
    """
    # See comments on PowerSpectrum; this could be instantiated by
    # hand, but in a GUI it would not be useful at present due to the
    # signal parameter.
    __abstract=True
    
    seconds_per_timestep=param.Number(default=1.0,doc="""
        Number of seconds represented by 1 simulation time step.""")

    sample_window=param.Number(default=1.0,doc="""
        The length of interval of the signal (in seconds) on which to
        perform the Fourier transform.

        How much history of the signal to include in the window.
        sample_window > seconds_per_timestep -> window overlap
                                         
        The Fourier transform algorithm is most efficient if the
        resulting window_length(sample_window * sample_rate) is a
        power of 2, or can be decomposed into small prime factors; see
        numpy.fft.""")
     
    def __init__(self, signal, **params):
        # will resize as soon as sheet dimensions are available.
        self._spectrogram = zeros(1, dtype=float32)
            
        for parameter,value in params.items():
            if parameter == "sample_window" or \
               parameter == "seconds_per_timestep":
                setattr(self,parameter,value)
        
        if self.sample_window < self.seconds_per_timestep:
            self.warning("sample_window < seconds_per_timestep; some signal will be skipped.")
        
        super(Spectrogram, self).__init__(signal, window_increment=self.seconds_per_timestep,
            window_length=self.sample_window, **params)
        
    def _create_frequency_indices(self, p):
        super(Spectrogram, self)._create_frequency_indices(p)
        
        if self._spectrogram.size == 1:
            self._spectrogram = zeros(self._sheet_dimensions, dtype=float32)
        
    def __call__(self, **params_to_override):
        p = ParamOverrides(self, params_to_override)
        
        self._sheet_dimensions = SheetCoordinateSystem(p.bounds, p.xdensity, p.ydensity).shape
        self._create_frequency_indices(p)
        
        amplitudes = self._get_amplitudes(p)
        assert shape(amplitudes)[0] == shape(self._spectrogram)[0]
        self._spectrogram = hstack((amplitudes, self._spectrogram))
        
        # knock off oldest spectral information, i.e. right-most column.
        self._spectrogram = self._spectrogram[0:, 0:self._spectrogram.shape[1]-1]
        return self._spectrogram
        
        
__all__ = list(set([k for k,v in locals().items() if isinstance(v,type) and issubclass(v,PatternGenerator)]))
