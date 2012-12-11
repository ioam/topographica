# cython: profile=False
# cython: boundscheck=False
# cython: wraparound=False
"""
Work in progress: Cython version of CFPRF_DotProduct.

Should be considered untested.

Originally by Aistis Stankevicius; see topographica-cython branch in
SVN for additional versions.
"""

# Current weave vs cython timings (lissom_or, no scheduled events)

#$ svn diff examples/lissom_or.ty
#Index: examples/lissom_or.ty
#===================================================================
#--- examples/lissom_or.ty	(revision 11402)
#+++ examples/lissom_or.ty	(working copy)
#@@ -123,7 +123,7 @@
#
#
# ### Actions scheduled to occur as the simulation proceeds.
#-sheet.lissom.schedule_events("topo.sim['V1']",st=1.0/num_inputs,aff_name="Afferent")
#+#sheet.lissom.schedule_events("topo.sim['V1']",st=1.0/num_inputs,aff_name="Afferent")

# $ diff examples/lissom_or.ty examples/cylissom_or.ty
# 65c65
# < projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()
# ---
# > projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_cyopt()

# $ ./topographica -c "import_pyx=False" examples/lissom_or.ty -c "from topo.misc.util import profile" -c "topo.sim.run(1)" -c "profile('topo.sim.run(100)')" -c "print topo.sim['V1'].activity.sum()"
# ...
# 581059 function calls (578459 primitive calls) in 5.092 CPU seconds
# ...
# 160.402682361

# $ ./topographica -c "import_pyx=True" examples/cylissom_or.ty -c "from topo.misc.util import profile" -c "topo.sim.run(1)" -c "profile('topo.sim.run(100)')" -c "print topo.sim['V1'].activity.sum()"
# ...
# 552559 function calls (549959 primitive calls) in 8.938 CPU seconds
# ...
# 160.402678767


import param
import numpy as np

cimport numpy as np
cimport cython

from topo.base.cf import CFPResponseFn
from topo.base.functionfamily import DotProduct,ResponseFn



class CFPRF_DotProduct_cyopt(CFPResponseFn):

    single_cf_fn = param.ClassSelector(ResponseFn,DotProduct(),readonly=True)


    def __call__(self, object iterator, np.ndarray[np.double_t,  ndim=2] input_activity,
                 np.ndarray[np.double_t,  ndim=2] activity, np.double_t strength):

        cdef np.ndarray[np.int32_t] input_sheet_slice
        cdef np.ndarray[np.float32_t, ndim=2] weights
        cdef np.ndarray[np.double_t, ndim=2] mask

        # internal counting variables
        cdef unsigned int r1,r2,c1,c2,i,row,col,p,q,iR,iC
        cdef float total

        cfs = iterator.flatcfs
        mask = iterator.mask.data

        for i in range(len(cfs)):

            # index into 2D activity and mask arrays
            iR,iC = i/activity.shape[1],i%activity.shape[1]

            if mask[iR,iC]==0.0:
                activity[iR,iC]=0.0
            else:
                cf = cfs[i] # slow?

                #####
                # r1,r2,c1,c2 = cf.input_sheet_slice
                input_sheet_slice = <np.ndarray>cf.input_sheet_slice # slow?
                r1=input_sheet_slice[0]
                r2=input_sheet_slice[1]
                c1=input_sheet_slice[2]
                c2=input_sheet_slice[3]
                #####

                weights = cf.weights # slow?

                #####
                # activity = dot(input_activity[r1:r2,c1:c2],weights) * strength
                total = 0.0
                p = 0
                for row in range(r1,r2):
                    q=0
                    for col in range(c1,c2):
                        total += (input_activity[row,col] * weights[p,q])
                        q+=1
                    p+=1
                activity[iR,iC]=total*strength
                #####

