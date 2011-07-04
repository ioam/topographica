"""
PatternGenerator abstract class and basic example concrete class.

$Id$
"""
__version__='$Revision$'


from math import pi

from numpy import add,subtract,cos,sin

import param
from param.parameterized import ParamOverrides

from boundingregion import BoundingBox, BoundingRegionParameter
from sheetcoords import SheetCoordinateSystem
from functionfamily import TransferFn


# CEBALERT: PatternGenerator has become a bit of a monster abstract
# class.  Can it be split into the minimum required to specify the
# interface, with a subclass implementing the rest (this subclass
# still being above the rest of the PatternGenerators)?  We want to
# make it easy to add new types of PatternGenerator that don't match
# the assumptions of the current ones (OneDPowerSpectrum is an example
# of a PG that doesn't match the current assumptions), but still lets
# them be used like the current ones.
# (PatternGenerator-->TwoDPatternGenerator?)

# JLALERT: PatternGenerator should have
# override_plasticity_state/restore_plasticity_state functions which
# can override the plasticity of any output_fn that has state, in case
# anyone ever uses such an object in a PatternGenerator.  Will also
# need to support Composite patterns.


class PatternGenerator(param.Parameterized):
    """
    A class hierarchy for callable objects that can generate 2D patterns.

    Once initialized, PatternGenerators can be called to generate a
    value or a matrix of values from a 2D function, typically
    accepting at least x and y.
    
    A PatternGenerator's Parameters can make use of Parameter's
    precedence attribute to specify the order in which they should
    appear, e.g. in a GUI. The precedence attribute has a nominal
    range of 0.0 to 1.0, with ordering going from 0.0 (first) to 1.0
    (last), but any value is allowed.

    The orientation and layout of the pattern matrices is defined by
    the SheetCoordinateSystem class, which see.

    Note that not every parameter defined for a PatternGenerator will
    be used by every subclass.  For instance, a Constant pattern will
    ignore the x, y, orientation, and size parameters, because the
    pattern does not vary with any of those parameters.  However,
    those parameters are still defined for all PatternGenerators, even
    Constant patterns, to allow PatternGenerators to be scaled, rotated,
    translated, etc. uniformly.
    """
    __abstract = True
    
    bounds  = BoundingRegionParameter(
        default=BoundingBox(points=((-0.5,-0.5), (0.5,0.5))),precedence=-1,
        doc="BoundingBox of the area in which the pattern is generated.")
    
    xdensity = param.Number(default=10,bounds=(0,None),precedence=-1,doc="""
        Density (number of samples per 1.0 length) in the x direction.""")

    ydensity = param.Number(default=10,bounds=(0,None),precedence=-1,doc="""
        Density (number of samples per 1.0 length) in the y direction.
        Typically the same as the xdensity.""")

    x = param.Number(default=0.0,softbounds=(-1.0,1.0),precedence=0.20,doc="""
        X-coordinate location of pattern center.""")

    y = param.Number(default=0.0,softbounds=(-1.0,1.0),precedence=0.21,doc="""
        Y-coordinate location of pattern center.""")


    position = param.Composite(attribs=['x','y'],precedence=-1,doc="""
        Coordinates of location of pattern center.
        Provides a convenient way to set the x and y parameters together
        as a tuple (x,y), but shares the same actual storage as x and y
        (and thus only position OR x and y need to be specified).""")
    
    orientation = param.Number(default=0.0,softbounds=(0.0,2*pi),precedence=0.40,doc="""
        Polar angle of pattern, i.e., the orientation in the Cartesian coordinate
        system, with zero at 3 o'clock and increasing counterclockwise.""")
    
    size = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,6.0),
        precedence=0.30,doc="""Determines the overall size of the pattern.""")

    scale = param.Number(default=1.0,softbounds=(0.0,2.0),precedence=0.10,doc="""
        Multiplicative strength of input pattern, defaulting to 1.0""")
    
    offset = param.Number(default=0.0,softbounds=(-1.0,1.0),precedence=0.11,doc="""
        Additive offset to input pattern, defaulting to 0.0""")

    mask = param.Parameter(default=None,precedence=-1,doc="""
        Optional object (expected to be an array) with which to multiply the
        pattern array after it has been created, before any output_fns are
        applied. This can be used to shape the pattern.""")

    # Note that the class type is overridden to PatternGenerator below
    mask_shape = param.ClassSelector(param.Parameterized,default=None,precedence=0.06,doc="""
        Optional PatternGenerator used to construct a mask to be applied to
        the pattern.""")
    
    output_fns = param.HookList(default=[],class_=TransferFn,precedence=0.08,doc="""
        Optional function(s) to apply to the pattern array after it has been created.
        Can be used for normalization, thresholding, etc.""")


    def __init__(self,**params):
        super(PatternGenerator, self).__init__(**params) 
        self.set_matrix_dimensions(self.bounds, self.xdensity, self.ydensity)
        

    def __call__(self,**params_to_override):
        """
        Call the subclass's 'function' method on a rotated and scaled coordinate system.

        Creates and fills an array with the requested pattern.  If
        called without any params, uses the values for the Parameters
        as currently set on the object. Otherwise, any params
        specified override those currently set on the object.
        """
        p=ParamOverrides(self,params_to_override)

        # CEBERRORALERT: position parameter is not currently
        # supported. We should delete the position parameter or fix
        # this.
        #
        # position=params_to_override.get('position',None) if position
        # is not None: x,y = position

        self._setup_xy(p.bounds,p.xdensity,p.ydensity,p.x,p.y,p.orientation)
        fn_result = self.function(p)
        self._apply_mask(p,fn_result)
        result = p.scale*fn_result+p.offset
            
        for of in p.output_fns:
            of(result)
                               
        return result
                               

    def _setup_xy(self,bounds,xdensity,ydensity,x,y,orientation):
        """
        Produce pattern coordinate matrices from the bounds and
        density (or rows and cols), and transforms them according to
        x, y, and orientation.
        """
        self.debug(lambda:"bounds=%s, xdensity=%s, ydensity=%s, x=%s, y=%s, orientation=%s"%(bounds,xdensity,ydensity,x,y,orientation))
        # Generate vectors representing coordinates at which the pattern
        # will be sampled.

        # CB: note to myself - use slice_._scs if supplied?
        x_points,y_points = SheetCoordinateSystem(bounds,xdensity,ydensity).sheetcoordinates_of_matrixidx()
            
        # Generate matrices of x and y sheet coordinates at which to
        # sample pattern, at the correct orientation
        self.pattern_x, self.pattern_y = self._create_and_rotate_coordinate_arrays(x_points-x,y_points-y,orientation)


    def function(self,p):
        """
        Function to draw a pattern that will then be scaled and rotated.

        Instead of implementing __call__ directly, PatternGenerator
        subclasses will typically implement this helper function used
        by __call__, because that way they can let __call__ handle the
        scaling and rotation for them.  Alternatively, __call__ itself
        can be reimplemented entirely by a subclass (e.g. if it does
        not need to do any scaling or rotation), in which case this
        function will be ignored.
        """
        raise NotImplementedError

        
    def _create_and_rotate_coordinate_arrays(self, x, y, orientation):
        """
        Create pattern matrices from x and y vectors, and rotate
        them to the specified orientation.
        """
        # Using this two-liner requires that x increase from left to
        # right and y decrease from left to right; I don't think it
        # can be rewritten in so little code otherwise - but please
        # prove me wrong.
        pattern_y = subtract.outer(cos(orientation)*y, sin(orientation)*x)
        pattern_x = add.outer(sin(orientation)*y, cos(orientation)*x)
        return pattern_x, pattern_y


    def _apply_mask(self,p,mat):
        """Create (if necessary) and apply the mask to the given matrix mat."""
        mask = p.mask
        ms=p.mask_shape
        if ms is not None:
            mask = ms(x=p.x+p.size*(ms.x*cos(p.orientation)-ms.y*sin(p.orientation)),
                      y=p.y+p.size*(ms.x*sin(p.orientation)+ms.y*cos(p.orientation)),
                      orientation=ms.orientation+p.orientation,size=ms.size*p.size,
                      bounds=p.bounds,ydensity=p.ydensity,xdensity=p.xdensity)
        if mask is not None:
            mat*=mask
    
    
    def set_matrix_dimensions(self, bounds, xdensity, ydensity):
        """
        Change the dimensions of the matrix into which the pattern will be drawn.
        Users of this class should call this method rather than changing
        the bounds, xdensity, and ydensity parameters directly.  Subclasses
        can override this method to update any internal data structures that
        may depend on the matrix dimensions.
        """
        self.bounds = bounds
        self.xdensity = xdensity
        self.ydensity = ydensity
        
        

# Override class type; must be set here rather than when mask_shape is declared,
# to avoid referring to class not yet constructed
PatternGenerator.params('mask_shape').class_=PatternGenerator


# Trivial example of a PatternGenerator, provided for when a default is
# needed.  The other concrete PatternGenerator classes are stored in
# patterns/, to be imported as needed.
from numpy.oldnumeric import ones, Float

class Constant(PatternGenerator):
    """Constant pattern generator, i.e., a solid, uniform field of the same value."""

    # The orientation is ignored, so we don't show it in
    # auto-generated lists of parameters (e.g. in the GUI)
    orientation = param.Number(precedence=-1)

    # Optimization: We use a simpler __call__ method here to skip the
    # coordinate transformations (which would have no effect anyway)
    def __call__(self,**params_to_override):
        p = ParamOverrides(self,params_to_override)
        
        shape = SheetCoordinateSystem(p.bounds,p.xdensity,p.ydensity).shape

        result = p.scale*ones(shape, Float)+p.offset
        self._apply_mask(p,result)

        for of in p.output_fns:
            of(result)

        return result

