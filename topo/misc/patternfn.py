from __future__ import with_statement
"""
Family of two-dimensional functions indexed by x and y.

All functions are written to be valid both for scalar x and y, and for
numpy arrays of x and y (in which case the result is also an array);
the functions therefore have the same mathematical behaviour as numpy.

$Id$
"""
__version__='$Revision$'



from math import pi

from numpy.oldnumeric import where,maximum,cos,sqrt,divide,greater_equal,bitwise_xor,exp
from numpy.oldnumeric import arcsin,logical_and,logical_or,less,minimum
from numpy import seterr, log

from contextlib import contextmanager

# CEBALERT: abs() is used in various places in this file, but I don't
# see it on the list of numpy imports. I guess we're mistakenly not
# using numpy's abs...

@contextmanager
def float_error_ignore():
    """
    Many of the functions in this module use Gaussian smoothing, which
    is based on a calculation like exp(divide(x*x,sigma)).  When sigma
    is zero the value of this expression should be zero at all points
    in the plane, because such a Gaussian is infinitely small.
    Obtaining the correct answer using finite-precision floating-point
    array computations requires allowing infinite values to be
    returned from divide(), and allowing exp() to underflow silently
    to zero when given an infinite value.  In numpy this is achieved
    by using its seterr() function to disable divide-by-zero and
    underflow warnings temporarily while these values are being
    computed.
    """
    oldsettings=seterr(divide='ignore',under='ignore')
    yield
    seterr(**oldsettings)


def gaussian(x, y, xsigma, ysigma):
    """
    Two-dimensional oriented Gaussian pattern (i.e., 2D version of a
    bell curve, like a normal distribution but not necessarily summing
    to 1.0).
    """
    if xsigma==0.0 or ysigma==0.0:
        return x*0.0

    with float_error_ignore():
        x_w = divide(x,xsigma)
        y_h = divide(y,ysigma)
        return exp(-0.5*x_w*x_w + -0.5*y_h*y_h)

    
def log_gaussian(x, y, x_sigma, y_sigma, mu):
    """
    Two-dimensional oriented Log Gaussian pattern (i.e., 2D version of a
    bell curve with an independent, movable peak). Much like a normal 
    distribution, but not necessarily placing the peak above the center,
    and not necessarily summing to 1.0).
    """
    if x_sigma==0.0 or y_sigma==0.0:
        return x * 0.0

    with float_error_ignore():
        x_w = divide(log(x)-mu, x_sigma*x_sigma)
        y_h = divide(log(y)-mu, y_sigma*y_sigma)
		
        return exp(-0.5*x_w*x_w + -0.5*y_h*y_h)


def sigmoid(axis, slope):     
    """
    Sigmoid dividing axis into a positive and negative half, 
    with a smoothly sloping transition between them (controlled by the slope).
    
    At default rotation, axis refers to the vertical (y) axis.
    """
    with float_error_ignore():
        return (2.0 / (1.0 + exp(-2.0*slope*axis))) - 1.0   
        
                  
def exponential(x, y, xscale, yscale):
    """
    Two-dimensional oriented exponential decay pattern.
    """
    if xscale==0.0 or yscale==0.0:
        return x*0.0
    
    with float_error_ignore():
        x_w = divide(x,xscale)
        y_h = divide(y,yscale)
        return exp(-sqrt(x_w*x_w+y_h*y_h))


def gabor(x, y, xsigma, ysigma, frequency, phase):
    """
    Gabor pattern (sine grating multiplied by a circular Gaussian).
    """
    if xsigma==0.0 or ysigma==0.0:
        return x*0.0
    
    with float_error_ignore():
        x_w = divide(x,xsigma)
        y_h = divide(y,ysigma)
        p = exp(-0.5*x_w*x_w + -0.5*y_h*y_h)
    return p * 0.5*cos(2*pi*frequency*y + phase)


# JABHACKALERT: Shouldn't this use 'size' instead of 'thickness',
# for consistency with the other patterns?  Right now, it has a
# size parameter and ignores it, which is very confusing.  I guess
# it's called thickness to match ring, but matching gaussian and disk
# is probably more important.
def line(y, thickness, gaussian_width):
    """
    Infinite-length line with a solid central region, then Gaussian fall-off at the edges.
    """
    distance_from_line = abs(y)
    gaussian_y_coord = distance_from_line - thickness/2.0
    sigmasq = gaussian_width*gaussian_width

    if sigmasq==0.0:
        falloff = y*0.0
    else:
        with float_error_ignore():
            falloff = exp(divide(-gaussian_y_coord*gaussian_y_coord,2*sigmasq))

    return where(gaussian_y_coord<=0, 1.0, falloff)


def disk(x, y, height, gaussian_width):
    """
    Circular disk with Gaussian fall-off after the solid central region.
    """
    disk_radius = height/2.0

    distance_from_origin = sqrt(x**2+y**2)
    distance_outside_disk = distance_from_origin - disk_radius
    sigmasq = gaussian_width*gaussian_width

    if sigmasq==0.0:
        falloff = x*0.0
    else:
        with float_error_ignore():
            falloff = exp(divide(-distance_outside_disk*distance_outside_disk,
                                  2*sigmasq))

    return where(distance_outside_disk<=0,1.0,falloff)


def ring(x, y, height, thickness, gaussian_width):
    """
    Circular ring (annulus) with Gaussian fall-off after the solid ring-shaped region.
    """
    radius = height/2.0
    half_thickness = thickness/2.0

    distance_from_origin = sqrt(x**2+y**2)
    distance_outside_outer_disk = distance_from_origin - radius - half_thickness
    distance_inside_inner_disk = radius - half_thickness - distance_from_origin

    ring = 1.0-bitwise_xor(greater_equal(distance_inside_inner_disk,0.0),greater_equal(distance_outside_outer_disk,0.0))

    sigmasq = gaussian_width*gaussian_width

    if sigmasq==0.0:
        inner_falloff = x*0.0
        outer_falloff = x*0.0
    else:
        with float_error_ignore():
            inner_falloff = exp(divide(-distance_inside_inner_disk*distance_inside_inner_disk, 2.0*sigmasq))
            outer_falloff = exp(divide(-distance_outside_outer_disk*distance_outside_outer_disk, 2.0*sigmasq))

    return maximum(inner_falloff,maximum(outer_falloff,ring))


def smooth_rectangle(x, y, rec_w, rec_h, gaussian_width_x, gaussian_width_y):
    """
    Rectangle with a solid central region, then Gaussian fall-off at the edges.
    """

    gaussian_x_coord = abs(x)-rec_w/2.0
    gaussian_y_coord = abs(y)-rec_h/2.0
        
    box_x=less(gaussian_x_coord,0.0)
    box_y=less(gaussian_y_coord,0.0)
    sigmasq_x=gaussian_width_x*gaussian_width_x
    sigmasq_y=gaussian_width_y*gaussian_width_y

    with float_error_ignore():
        falloff_x=x*0.0 if sigmasq_x==0.0 else \
            exp(divide(-gaussian_x_coord*gaussian_x_coord,2*sigmasq_x))
        falloff_y=y*0.0 if sigmasq_y==0.0 else \
            exp(divide(-gaussian_y_coord*gaussian_y_coord,2*sigmasq_y))

    return minimum(maximum(box_x,falloff_x), maximum(box_y,falloff_y))



def arc_by_radian(x, y, height, radian_range, thickness, gaussian_width):
    """
    Radial arc with Gaussian fall-off after the solid ring-shaped
    region with the given thickness, with shape specified by the
    (start,end) radian_range.
    """

    # Create a circular ring (copied from the ring function)
    radius = height/2.0
    half_thickness = thickness/2.0

    distance_from_origin = sqrt(x**2+y**2)
    distance_outside_outer_disk = distance_from_origin - radius - half_thickness
    distance_inside_inner_disk = radius - half_thickness - distance_from_origin

    ring = 1.0-bitwise_xor(greater_equal(distance_inside_inner_disk,0.0),greater_equal(distance_outside_outer_disk,0.0))

    sigmasq = gaussian_width*gaussian_width

    if sigmasq==0.0:
        inner_falloff = x*0.0
        outer_falloff = x*0.0
    else:
        with float_error_ignore():
            inner_falloff = exp(divide(-distance_inside_inner_disk*distance_inside_inner_disk, 2.0*sigmasq))
            outer_falloff = exp(divide(-distance_outside_outer_disk*distance_outside_outer_disk, 2.0*sigmasq))
            
    output_ring = maximum(inner_falloff,maximum(outer_falloff,ring))

    # Calculate radians (in 4 phases) and cut according to the set range)

    # RZHACKALERT:
    # Function float_error_ignore() cannot catch the exception when
    # both dividend and divisor are 0.0, and when only divisor is 0.0
    # it returns 'Inf' rather than 0.0. In x, y and
    # distance_from_origin, only one point in distance_from_origin can
    # be 0.0 (circle center) and in this point x and y must be 0.0 as
    # well. So here is a hack to avoid the 'invalid value encountered
    # in divide' error by turning 0.0 to 1e-5 in distance_from_origin.
    distance_from_origin += where(distance_from_origin == 0.0, 1e-5, 0)

    with float_error_ignore():
        sines = divide(y, distance_from_origin)
        cosines = divide(x, distance_from_origin)
        arcsines = arcsin(sines)

    phase_1 = where(logical_and(sines >= 0, cosines >= 0), 2*pi-arcsines, 0)
    phase_2 = where(logical_and(sines >= 0, cosines <  0), pi+arcsines,   0)
    phase_3 = where(logical_and(sines <  0, cosines <  0), pi+arcsines,   0)
    phase_4 = where(logical_and(sines <  0, cosines >= 0), -arcsines,     0)
    arcsines = phase_1 + phase_2 + phase_3 + phase_4

    if radian_range[0] <= radian_range[1]:
        return where(logical_and(arcsines >= radian_range[0], arcsines <= radian_range[1]),
                     output_ring, 0.0)
    else:
        return where(logical_or(arcsines >= radian_range[0], arcsines <= radian_range[1]),
                     output_ring, 0.0)


def arc_by_center(x, y, arc_box, constant_length, thickness, gaussian_width):
    """
    Arc with Gaussian fall-off after the solid ring-shaped region and specified
    by point of tangency (x and y) and arc width and height.

    This function calculates the start and end radian from the given width and
    height, and then calls arc_by_radian function to draw the curve.
    """

    arc_w=arc_box[0]
    arc_h=abs(arc_box[1])

    if arc_w==0.0: # arc_w=0, don't draw anything
        radius=0.0
        angles=(0.0,0.0)
    elif arc_h==0.0:  # draw a horizontal line, width=arc_w
        return smooth_rectangle(x, y, arc_w, thickness, 0.0, gaussian_width)
    else:
        if constant_length:
            curvature=arc_h/arc_w
            radius=arc_w/(2*pi*curvature)
            angle=curvature*(2*pi)/2.0
        else:  # constant width
            radius=arc_h/2.0+arc_w**2.0/(8*arc_h)
            angle=arcsin(arc_w/2.0/radius)
        if arc_box[1]<0: # convex shape
            y=y+radius
            angles=(3.0/2.0*pi-angle, 3.0/2.0*pi+angle)
        else:  # concave shape
            y=y-radius
            angles=(pi/2.0-angle, pi/2.0+angle)

    return arc_by_radian(x, y, radius*2.0, angles, thickness, gaussian_width)



