"""
TransferFns: accept and modify a 2d array

$Id$
"""
__version__='$Revision$'

import numpy

import param


class TransferFn(param.Parameterized):
    """
    Function object to modify a matrix in place, e.g. for normalization.

    Used for transforming an array of intermediate results into a
    final version, by cropping it, normalizing it, squaring it, etc.
    
    Objects in this class must support being called as a function with
    one matrix argument, and are expected to change that matrix in place.
    """
    __abstract = True
    
    # CEBALERT: can we have this here - is there a more appropriate
    # term for it, general to output functions?  JAB: Please do rename it!
    norm_value = param.Parameter(default=None)


    def __call__(self,x):
        raise NotImplementedError
    
# Trivial example of a TransferFn, provided for when a default
# is needed.  The other concrete OutputFunction classes are stored
# in transferfn/, to be imported as needed.
class IdentityTF(TransferFn):
    """
    Identity function, returning its argument as-is.

    For speed, calling this function object is sometimes optimized
    away entirely.  To make this feasible, it is not allowable to
    derive other classes from this object, modify it to have different
    behavior, add side effects, or anything of that nature.
    """

    def __call__(self,x,sum=None):
        pass



class Threshold(TransferFn):
    """
    Forces all values below a threshold to zero, and leaves others unchanged.
    """

    threshold = param.Number(default=0.25, doc="""
        Decision point for determining values to clip.""")

    def __call__(self,x):
        minimum(x,self.threshold,x)



class BinaryThreshold(TransferFn):
    """
    Forces all values below a threshold to zero, and above it to 1.0.
    """

    threshold = param.Number(default=0.25, doc="""
        Decision point for determining binary value.""")

    def __call__(self,x):
        above_threshold = x>=self.threshold
        x *= 0.0
        x += above_threshold



class DivisiveNormalizeL1(TransferFn):
    """
    TransferFn that divides an array by its L1 norm.

    This operation ensures that the sum of the absolute values of the
    array is equal to the specified norm_value, rescaling each value
    to make this true.  The array is unchanged if the sum of absolute
    values is zero.  For arrays of non-negative values where at least
    one is non-zero, this operation is equivalent to a divisive sum
    normalization.
    """
    norm_value = param.Number(default=1.0)

    def __call__(self,x):
        """L1-normalize the input array, if it has a nonzero sum."""
        current_sum = 1.0*numpy.sum(abs(x.ravel()))
        if current_sum != 0:
            factor = (self.norm_value/current_sum)
            x *= factor



class DivisiveNormalizeL2(TransferFn):
    """
    TransferFn to divide an array by its Euclidean length (aka its L2 norm).

    For a given array interpreted as a flattened vector, keeps the
    Euclidean length of the vector at a specified norm_value.
    """
    norm_value = param.Number(default=1.0)
    
    def __call__(self,x):
        xr = x.ravel()
        tot = 1.0*numpy.sqrt(numpy.dot(xr,xr))
        if tot != 0:
            factor = (self.norm_value/tot)
            x *= factor



class DivisiveNormalizeLinf(TransferFn):
    """
    TransferFn to divide an array by its L-infinity norm
    (i.e. the maximum absolute value of its elements).

    For a given array interpreted as a flattened vector, scales the
    elements divisively so that the maximum absolute value is the
    specified norm_value.

    The L-infinity norm is also known as the divisive infinity norm
    and Chebyshev norm.
    """
    norm_value = param.Number(default=1.0)
    
    def __call__(self,x):
        tot = 1.0*(numpy.abs(x)).max()
        if tot != 0:
            factor = (self.norm_value/tot)
            x *= factor


    
def norm(v,p=2):
    """
    Returns the Lp norm of v, where p is an arbitrary number defaulting to 2.
    """
    return (numpy.abs(v)**p).sum()**(1.0/p)



class DivisiveNormalizeLp(TransferFn):
    """
    TransferFn to divide an array by its Lp-Norm, where p is specified.

    For a parameter p and a given array interpreted as a flattened
    vector, keeps the Lp-norm of the vector at a specified norm_value.
    Faster versions are provided separately for the typical L1-norm
    and L2-norm cases.  Defaults to be the same as an L2-norm, i.e.,
    DivisiveNormalizeL2.
    """
    p = param.Number(default=2)
    norm_value = param.Number(default=1.0)
    
    def __call__(self,x):
        tot = 1.0*norm(x.ravel(),self.p)
        if tot != 0:
            factor = (self.norm_value/tot)
            x *=factor 



