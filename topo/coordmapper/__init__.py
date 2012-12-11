"""
A family of function objects for transforming one set of coordinates into
another.

Coordinate mapper functions are useful for defining magnifications and
other kinds of transformations on sheet coordinates, e.g. for defining
retinal magnification using a CFProjection.  A CoordinateMapperFn
(e.g. MagnifyingMapper), is applied to an (x,y) pair and returns a new
(x,y) pair.  To apply a mapping to a CF projection, set the
CFProjection's coord_mapper parameter to an instance of the desired
CoordinateMapperFn.
"""

from math import atan,pi,atan2

from numpy import exp,log,sqrt,sin,cos,ones,dot
from numpy.matlib import matrix

import param

from topo.base.functionfamily import CoordinateMapperFn
from topo.misc.util import signabs
from topo import numbergen




class ConstantMapper(CoordinateMapperFn):
    """
    Map all values to the same constant, pre-specified coordinates.
    """

    x_cons = param.Number(default=0.0,doc="""
       Constant x value returned by the mapping.""")

    y_cons = param.Number(default=0.0, doc="""
       Constant y value returned by the mapping.""")

    def __call__(self, x, y):
        # Ignores all (x,y), always returning (x_cons,y_cons)
        return self.x_cons, self.y_cons


class Pipeline(CoordinateMapperFn):
    """
    Applies a sequence of coordmappers, left to right.
    """

    mappers=param.List(default=[],
        doc="The sequence of mappers to apply.")

    def __call__(self,x,y):
        return reduce( lambda args,f: apply(f,args),
                       [(x,y)] + self.mappers )


class Jitter(CoordinateMapperFn):
    """
    Additively modifies calculated x,y coordinates, e.g. with random noise.
    """

    scale = param.Parameter(default=0.0,doc="Amount of jitter.")

    gen = param.Parameter(default=numbergen.UniformRandom(),doc=
        "Number generator to use, typically a random distribution.")

    def __call__(self,x,y):
        return x+(self.gen()-0.5)*self.scale,y+(self.gen()-0.5)*self.scale


class NormalJitter(CoordinateMapperFn):
    """
    Additively modifies calculated x,y coordinates with Gaussian random noise.
    """

    gen = param.Parameter(default=numbergen.NormalRandom(),doc=
         "Number generator to use, typically a Gaussian distribution.")

    def __call__(self,x,y):
        return x+self.gen(),y+self.gen()


class Grid(CoordinateMapperFn):
    """
    Divides the 2D area into a grid, where all points within each grid
    element map to the same location.
    """

    xdensity = param.Number(default=1, bounds=(0,None), doc="""
        Number of columns per 1.0 input sheet distance horizontally.""")

    ydensity = param.Number(default=1, bounds=(0,None), doc="""
        Number of rows per 1.0 input sheet distance vertically.""")

    def __call__(self,x,y):
        xd=self.xdensity
        yd=self.ydensity

        xquant=(1.0/xd)*(int(xd*(x+0.5))-(0.5*(xd-1)))
        yquant=(1.0/yd)*(int(yd*(y+0.5))-(0.5*(yd-1)))

        return  xquant,yquant


class Polar2Cartesian(CoordinateMapperFn):
    """
    Map from polar (radius,angle) to Cartesian (x,y) coordinates.
    """

    degrees=param.Boolean(default=True,
        doc="Indicates whether the input angle is in degrees or radians.")

    def __call__(self, r, theta):

        if self.degrees:
            theta = theta * pi/180

            return r*cos(theta), r*sin(theta)


class Cartesian2Polar(CoordinateMapperFn):
    """
    Maps from Cartesian (x,y) to polar (radius,angle).
    """

    degrees = param.Boolean(default=True,
        doc="Indicates whether the output angle is in degrees or radians.")

    negative_radii = param.Boolean(default = False,
        doc="""If true, coordinates with negative x values will be
        given negative radii, and angles between -90 and 90
        degrees. (useful for mapping to saccade amplitude/direction space)""")

    def __call__(self, x, y):

        if self.negative_radii:
            xsgn,xabs = signabs(x)
            radius = xsgn * sqrt(x*x+y*y)
            angle = atan2(y,xabs)
        else:
            radius = sqrt(x*x+y*y)
            angle = atan2(y,x)

        if self.degrees:
            angle *= 180/pi

        return radius,angle




class AffineTransform(CoordinateMapperFn):
    """
    Remaps the input with an affine transform.

    This mapper allows the specification of an arbitrary combination
    of translation, rotation and scaling via a transform
    matrix. Single translations, etc, can be specified more simply
    with the subclasses Translate2d, Rotate2d, and Scale2d.
    """

    matrix = param.Parameter(default=ones((3,3)),doc="""
       The affine transformation matrix.  The functions
       Translate2dMat, Rotate2dMat, and Scale2dMat generate affine
       transform matrices that can be multiplied together to create
       combination transforms.  E.g. the matrix::

         Translate2dMat(3,0)*Rotate2d(pi/2)

       will shift points to the right by 3 units and rotate them around
       the origin by 90 degrees.""")

    def __init__(self, **kw):
        super(AffineTransform,self).__init__(**kw)

        # This buffer prevents having to allocate memory for each point.
        self._op_buf = matrix([[0.0],
                               [0.0],
                               [1.0]])

    def __call__(self, x, y):

        ## JPHACKALERT: If the coordmapper interface took a matrix of
        ## x/y column vectors, instead of x and y separately, affine
        ## transforms could be applied to all the points in a single
        ## matrix operation.  This would probably require revision of
        ## some of the other coordmapper functions, but it might allow
        ## some optimization in, e.g., CFProjection intialization by
        ## allowing all the CF positions to be computed at once.

        ## JPALERT: This is the easy way, but it allocates a matrix
        ## for the result.  It might be faster to unroll the
        ## computation.

        self._op_buf[0] = x
        self._op_buf[1] = y
        result = dot(self.matrix,self._op_buf)

        return result[0,0],result[1,0]


def Translate2dMat(xoff,yoff):
    """
    Return an affine transformation matrix that translates points by
    the offset (xoff,yoff).
    """
    return matrix([[1, 0, xoff],
                   [0, 1, yoff],
                   [0, 0,   1 ]])


def Rotate2dMat(t):
    """
    Return an affine transformation matrix that rotates the points
    around the origin by t radians.
    """
    return matrix([[cos(t), -sin(t), 0],
                   [sin(t),  cos(t), 0],
                   [  0   ,    0   , 1]])


def Scale2dMat(sx,sy):
    """
    Return an affine translation matrix that scales the points
    toward/away from the origin by a factor of sx on x-axis and sy on
    the y-axis.
    """
    return matrix([[sx,  0, 0],
                   [ 0, sy, 0],
                   [ 0,  0, 1]])


class Translate2d(AffineTransform):
    """
    Translate the input by xoff,yoff.
    """
    xoff = param.Number(default=0.0)
    yoff = param.Number(default=0.0)

    def __init__(self,**kw):
        super(Translate2d,self).__init__(**kw)
        self.matrix = Translate2dMat(self.xoff,self.yoff)


class Rotate2d(AffineTransform):
    """
    Rotate the input around the origin by an angle in radians.
    """
    angle = param.Number(default=0.0)

    def __init__(self,**kw):
        super(Rotate2d,self).__init__(**kw)
        self.matrix = Rotate2dMat(self.angle)


class Scale2d(AffineTransform):
    """
    Scale the input along the x and y axes by sx and sy, respectively.
    """
    sx = param.Number(default=1.0)
    sy = param.Number(default=1.0)

    def __init__(self,**kw):
        super(Scale2d,self).__init__(**kw)
        self.matrix = Scale2dMat(self.sx,self.sy)


class SingleDimensionMapper(CoordinateMapperFn):
    """
    Coordinate Mapper that uses an origin-centered 1-D mapping function.

    An abstract mapping function for coordinate mappers that remap
    based on the radius, x, or y individually. Subclasses should override
    _map_fn(self,z).
    """
    __abstract = True

    in_range = param.Number(default=0.5*sqrt(2),bounds=(0,None),doc="""
       The maximum range of the mapping input.""")
    out_range = param.Number(default=0.5*sqrt(2),bounds=(0,None), doc="""
       The maximum range of the output.""")
    remap_dimension = param.ObjectSelector(default='radius',
        objects=['radius','x','y','xy'],doc="""
        The dimension to remap. ('xy' remaps x and y independently.)""")


    def __call__(self,x,y):

        if self.remap_dimension == 'radius':
            r = sqrt(x**2 + y**2)
            a = atan2(x,y)
            new_r = self._map_fn(r)
            xout = new_r * sin(a)
            yout = new_r * cos(a)
        else:
            if 'x' in self.remap_dimension:
                xout = self._map_fn(x)
            else:
                xout = x

            if 'y' in self.remap_dimension:
                yout = self._map_fn(y)
            else:
                yout = y

        return xout,yout

    def _map_fn(self,z):
        raise NotImplementedError


class MagnifyingMapper(SingleDimensionMapper):
    """
    Exponential (magnifying) mapping function.

    Provides a mapping that magnifies the center of the activity image.
    Parameter k indicates amount of magnification, where 0 means no
    magnification.
    """

    k = param.Number(default=1.0,bounds=(0,None))

    def _map_fn(self,z):
        k = self.k
        if k == 0:
            return z
        else:
            sgn,z = signabs(z)
            return sgn * self.out_range * (exp(z/self.in_range*k)-1)/(exp(k)-1)


class ReducingMapper(SingleDimensionMapper):
    """
    Provides a mapping that reduces the center of the activity.

    Roughly the inverse of MagnifyingMapper.  k indicates amount of reduction.
    """
    k = param.Number(default=1.0,bounds=(0,None))

    def _map_fn(self,z):
        k = self.k
        sgn,z = signabs(z)
        return sgn * self.out_range * log(z/self.in_range*k+1)/log(k+1)


class OttesSCMapper(CoordinateMapperFn):
    """
    Abstract class for superior colliculus mappings.

    Subclasses of this class implement afferent and efferent mappings
    from Ottes et al. (1986) Vision Research 26:857-873.

    Default constant values are from Table 1, ibid.
    """
    __abstract = True


    A = param.Number(default=5.3, doc="""
       Shape parameter A, in degrees""")
    Bu = param.Number(default=1.8, doc="""
       Rostral-caudal scale parameter, in mm""")
    Bv = param.Number(default=1.8, doc="""
       Orthogonal (medial-lateral?) scale paraemter in mm/deg""")

    mm_scale = param.Number(default=8.0,doc="""
       Scale factor to convert constants Bu and Bv from mm to sheet
       units.  Expressed in mm/unit. """)

    amplitude_scale = param.Number(default=1,doc="""
        Scale factor for saccade command amplitude, expressed in
        degrees per unit of sheet.  Indicates how large a
        saccade is represented by the x-component of the command
        input.""")

    direction_scale = param.Number(default=1,doc="""
        Scale factor for saccade command direction, expressed in
        degrees per unit of sheet.  Indicates what direction of saccade
        is represented by the y-component of the command input.""")


    def __call__(self,x,y):
        raise NotImplementedError


class OttesSCMotorMapper(OttesSCMapper):
    """
    Efferent superior colliculus mapping.

    Provides the output/motor mapping from SC as defined by Ottes et al.
    (see superclass docs for reference)

    The mapping allows the creation of a single sheet representing
    both colliculi, one in the x-positive hemisheet and the other in
    the x-negative hemisheet.
    """
    def __call__(self,x,y):

        A = self.A
        Bu = self.Bu / self.mm_scale
        Bv = self.Bv / self.mm_scale

        R = x * self.amplitude_scale
        phi = y * self.direction_scale

        Rsign,R = signabs(R)

        u,v = ottes_mapping(R,phi,A,Bu,Bv)
        return Rsign*u,v



class OttesSCSenseMapper(OttesSCMapper):
    """
    Afferent superior colliculus mapping.

    Provides the input/retinal mapping to SC as defined by Ottes et al.
    (see superclass docs for reference)

    The mapping allows the creation of a single sheet representing
    both colliculi, one in the x-positive hemisheet and the other in
    the x-negative hemisheet.

    [NOTE: see warning in docs for ottes_inverse_mapping().]
    """

    def __call__(self,x,y):

        A  = self.A
        Bu = self.Bu
        Bv = self.Bv

        u = x * self.mm_scale
        v = y * self.mm_scale

        usgn,u = signabs(u)

        R,phi = ottes_inverse_mapping(u,v,A,Bu,Bv)

        return (usgn*R/self.amplitude_scale,
                phi/self.direction_scale)


def ottes_mapping(R,phi,A,Bu,Bv):
    """
    The efferent mapping function from Ottes et al. (1986)
    Vision Research 26:857-873.

    Takes saccade with amplitude R (in degrees) and direction
    phi (in degrees), and returns a location u,v on the colliculus
    in mm, where the u axis is rostral/caudal, and the v axis is
    medial/lateral.
    """

    phi *= pi/180
    u = Bu * (log(sqrt(R**2 + A**2 + 2*A*R*cos(phi))) - log(A))
    v = Bv * atan((R*sin(phi))/(R*cos(phi)+A))
    return u,v


def ottes_inverse_mapping(u,v,A,Bu,Bv):
    """
    Approximate inverse of ottes_mapping(), using the inverse function
    provided in the appendix of Ottes et al. (1986) Vision Research 26:857-873

    Takes takes a location u,v on the colliculus in mm and maps
    to a retinal eccentricity R and direction phi, in degrees.
    Inverse is approximate, with increasing error as positions near the
    edges of the collicular sheet. (I.e. with high absolute v value).
    """

    rads = pi/180
    R   = A * sqrt(exp(2*u/Bu) - 2*exp(u/Bu)*cos(rads*v/Bv) + 1)
    #phi = atan( (exp(u/Bu)*sin(rads*v/Bv)) / (exp(u/Bu)*cos(rads*v/Bv) -1) )
    phi = atan2( (exp(u/Bu)*sin(rads*v/Bv)), (exp(u/Bu)*cos(rads*v/Bv) -1) ) * 180/pi

    # JPALERT: Don't know why we have to multiply by 180/pi twice, but the answers
    # are way off without it.  Is the bug in my code, or in the original formula?
    return R,phi*180/pi


# JPALERT: Temporary testing function.  Will disappear eventually.
def test_ottes_inverse():

    A,Bu,Bv = 5.3,1.8,1.8

    print '%10s %10s | %10s %10s | %10s %10s | %s' \
          % ('R in','phi in','R out','phi out','R err','phi err','phi ratio')
    for r in range(10,60,10):
        for phi in range(-60,60,10):
            if  phi != 0:
                u,v = ottes_mapping(r,phi,A,Bu,Bv)
                r2,phi2 = ottes_inverse_mapping(u,v,A,Bu,Bv)
                print '%10.2f %10.2f | %10.2f %10.2f | %10.2f %10.2f | %.2f' \
                      % (r,phi,r2,phi2,r2-r,phi2-phi,phi/phi2)


_public = list(set([_k for _k,_v in locals().items()
                    if isinstance(_v,type) \
                    and issubclass(_v,CoordinateMapperFn)]))

# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = _public + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch
