# cython: profile=True
# cython: boundscheck=False
# cython: wraparound=False

"""
Work in progress: Cython version of CFPRF_DotProduct.

Untested and currently missing at least handling of mask, check for
contiguous weights array (if necessary?), and possibly more.

By Aistis Stankevicius; see topographica-cython branch in SVN for
additional versions.

$Id$
"""
__version__='$Revision$'

import param
import numpy as np

cimport numpy as np
cimport cython

from topo.base.cf import CFPResponseFn


# CB: unlikely to be either the clearest or the fastest way to write
# this function. I just pulled out and cleaned up a version I could
# get working from the svn branch.
class CFPRF_DotProduct_cyopt(CFPResponseFn):

   
   def __call__(self, object iterator, np.ndarray[np.double_t,  ndim=2] input_activity, 
                np.ndarray[np.double_t,  ndim=2] activity, np.float strength):
      cdef int i,  j
      cdef int r1,r2,c1,c2
      for i in range(len(iterator.flatcfs)):
         r1,r2,c1,c2 = iterator.flatcfs[i].input_sheet_slice
         activity.flat[i] = dp(input_activity[r1:r2,c1:c2], iterator.flatcfs[i].weights)

      for i in range(activity.shape[0]):
         for j in range(activity.shape[1]):
            activity[<unsigned int>i, <unsigned int>j] *= strength


def dp(np.ndarray[np.double_t,  ndim=2] A, np.ndarray[np.float32_t, ndim=2] B):
    cdef float total = 0.0
    cdef int i,  j
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            total += A[<unsigned int>i, <unsigned int>j] * B[<unsigned int>i, <unsigned int>j]
    return total
