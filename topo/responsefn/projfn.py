"""
Projection-level response functions.

For CFProjections, these function objects compute a response matrix
when given an input pattern and a set of ConnectionField objects.
"""

import numpy as np
import param

from topo.base.cf import CFPResponseFn
from topo.base.functionfamily import ResponseFn,DotProduct
from topo.base.arrayutil import L2norm

# Imported here so that all ResponseFns will be in the same package
from topo.base.cf import CFPRF_Plugin  # pyflakes:ignore (API import)


# CEBERRORALERT: doesn't use iterator, so ignores
# sheet mask!
class CFPRF_EuclideanDistance(CFPResponseFn):
    """
    Euclidean-distance--based response function.
    """
    def __call__(self, iterator, input_activity, activity, strength, **params):
        cfs = iterator.flatcfs
        rows,cols = activity.shape
        euclidean_dist_mat = np.zeros((rows,cols), np.float)
        for r in xrange(rows):
            for c in xrange(cols):
                flati = r*cols+c
                cf = cfs[flati]
                r1,r2,c1,c2 = cf.input_sheet_slice
                X = input_activity[r1:r2,c1:c2]
                diff = np.ravel(X) - np.ravel(cf.weights)
                euclidean_dist_mat.flat[flati] = L2norm(diff)

        max_dist = max(euclidean_dist_mat.ravel())
        activity *= 0.0
        activity += (max_dist - euclidean_dist_mat)
        activity *= strength



class CFPRF_ActivityBased(CFPResponseFn):
    """
    Calculate the activity of each unit nonlinearly based on the input activity.

    The activity is calculated from the input activity, the weights,
    and a strength that is a function of the input activity. This
    allows connections to have either an excitatory or inhibitory
    effect, depending on the activity entering the unit in question.

    The strength function is a generalized logistic curve (Richards'
    curve), a flexible function for specifying a nonlinear growth
    curve::

    y = l + ( u /(1 + b exp(-r (x - 2m)) ^ (1 / b)) )

    This function has five parameters::

    * l: the lower asymptote, i.e. the value at infinity;
    * u: the upper asymptote minus l, i.e. (u + l) is the value at minus infinity;
    * m: the time of maximum growth;
    * r: the growth rate;
    * b: affects near which asymptote maximum growth occurs.

    Richards, F.J. 1959 A flexible growth function for empirical use.
    J. Experimental Botany 10: 290--300, 1959.
    http://en.wikipedia.org/wiki/Generalised_logistic_curve
    """

    l = param.Number(default=-1.3,doc="Value at infinity")
    u = param.Number(default=1.2,doc="(u + l) is the value at minus infinity")
    m = param.Number(default=0.25,doc="Time of maximum growth.")
    r = param.Number(default=-200,doc="Growth rate, controls the gradient")
    b = param.Number(default=2,doc="Controls position of maximum growth")
    single_cf_fn = param.ClassSelector(ResponseFn,default=DotProduct(),doc="""
        ResponseFn to apply to each CF individually.""")

    def __call__(self, iterator, input_activity, activity, strength):
        single_cf_fn = self.single_cf_fn
        normalize_factor=max(input_activity.flat)

        for cf,r,c in iterator():
            r1,r2,c1,c2 = cf.input_sheet_slice
            X = input_activity[r1:r2,c1:c2]
            avg_activity=np.sum(X.flat)/len(X.flat)
            x=avg_activity/normalize_factor
            strength_fn=self.l+(self.u/(1+np.exp(-self.r*(x-2*self.m)))**(1.0/self.b))
            activity[r,c] = single_cf_fn(X,cf.weights)
            activity[r,c] *= strength_fn

__all__ = [
    "CFPRF_EuclideanDistance",
    "CFPRF_ActivityBased",
    "CFPRF_Plugin",
]
