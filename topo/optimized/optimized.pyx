import numpy as np
cimport numpy as np

import param

from topo.base.cf import CFPResponseFn, CFPLearningFn, CFPOutputFn
from topo.base.functionfamily import ResponseFn, DotProduct, LearningFn, Hebbian
from topo.base.sheet import activity_type

cdef extern from "optimized.h":
    void dot_product(double*, double*, np.float64_t, np.int64_t,
                     double*, cfs, np.int64_t, cf_type)

    void euclidean_response(double*, np.float64_t, np.int64_t, double*, cfs,
                            np.int64_t)

    void hebbian(double*, double*, double*, np.int64_t,
                 np.int64_t, cfs, np.float64_t, cf_type)

    void bcm_fixed(double*, double*, np.int64_t, np.int64_t,
                   cfs, np.float64_t, np.float64_t, cf_type)

    void trace_learning(double*, double*, np.int64_t, np.int64_t, cfs,
                        np.float64_t, cf_type)

    void divisive_normalize_l1(double*, double*, cfs, cf_type,
                               np.int64_t)


class CFPRF_DotProduct_cython(CFPResponseFn):
    """
    Dot-product response function.

    Written in C for a manyfold speedup; see CFPRF_DotProduct for an
    easier-to-read version in Python.  The unoptimized Python version
    is equivalent to this one, but it also works for 1D arrays.
    """

    single_cf_fn = param.ClassSelector(ResponseFn, DotProduct(),readonly=True)

    def __call__(self, iterator, np.ndarray[np.float64_t, ndim=2] input_activity,
                 np.ndarray[np.float64_t, ndim=2] activity, np.float64_t strength,
                 **params):
        cdef np.int64_t icols = input_activity.shape[1]
        cdef np.ndarray[np.float64_t, ndim=1] X = input_activity.ravel()

        cfs = iterator.flatcfs
        cdef np.int64_t num_cfs = len(cfs)
        cdef np.ndarray[np.float64_t, ndim=2] mask = iterator.mask.data

        cf_type = iterator.cf_type

        dot_product(<double*> mask.data, <double*> X.data, strength, icols,
                    <double*> activity.data, cfs, num_cfs, cf_type)


class CFPRF_EuclideanDistance_cython(CFPResponseFn):
    """
    Euclidean-distance response function.

    Written in C for a several-hundred-times speedup; see
    CFPRF_EuclideanDistance for an easier-to-read (but otherwise
    equivalent) version in Python.
    """
    def __call__(self, iterator, np.ndarray[np.float64_t, ndim=2] input_activity,
                 np.ndarray[np.float64_t, ndim=2] activity, np.float64_t strength,
                 **params):
        cdef np.int64_t icols = input_activity.shape[1]
        cdef np.ndarray[np.float64_t, ndim=1] X = input_activity.ravel()

        cfs = iterator.flatcfs
        cdef np.int64_t num_cfs = len(cfs)

        euclidean_response(<double*> X.data, strength, icols, <double*> activity.data,
                           cfs, num_cfs)



class CFPLF_Hebbian_cython(CFPLearningFn):

    def __call__(self, iterator, np.ndarray[np.float64_t, ndim=2] input_activity,
                 np.ndarray[np.float64_t, ndim=2] output_activity,
                 np.float64_t learning_rate, **params):

        cdef np.float64_t single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        if single_connection_learning_rate==0:
            return

        cfs = iterator.flatcfs
        cdef np.int64_t num_cfs = len(cfs)
        cdef np.int64_t icols = input_activity.shape[1]
        cf_type = iterator.cf_type

        cdef np.ndarray[np.float64_t, ndim=2] sheet_mask = iterator.get_sheet_mask()

        hebbian(<double*> input_activity.data, <double*> output_activity.data,
                <double*> sheet_mask.data, num_cfs, icols, cfs,
                single_connection_learning_rate, cf_type)



class CFPLF_BCMFixed_cython(CFPLearningFn):
    """
    CF-aware BCM learning rule.

    Implemented in C for speed.  Should be equivalent to
    BCMFixed for CF sheets, except faster.

    As a side effect, sets the norm_total attribute on any cf whose
    weights are updated during learning, to speed up later operations
    that might depend on it.

    May return without modifying anything if the learning rate turns
    out to be zero.
    """

    unit_threshold=param.Number(default=0.5, bounds=(0, None), doc="""
        Threshold between LTD and LTP.""")

    def __call__(self, iterator, np.ndarray[np.float64_t, ndim=2] input_activity,
                 np.ndarray[np.float64_t, ndim=2] output_activity,
                 np.float64_t learning_rate, **params):

        cdef np.float64_t single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        if single_connection_learning_rate==0:
            return

        cfs = iterator.flatcfs
        cf_type = iterator.cf_type
        cdef np.int64_t num_cfs = len(cfs)


        cdef np.float64_t unit_threshold=self.unit_threshold

        cdef np.int64_t icols = input_activity.shape[1]

        bcm_fixed(<double*> input_activity.data, <double*> output_activity.data,
                  num_cfs, icols, cfs, single_connection_learning_rate,
                  unit_threshold, cf_type)



class CFPLF_Trace_cython(CFPLearningFn):
    """
    Optimized version of CFPLF_Trace; see projfn.py for more info
    """

    trace_strength=param.Number(default=0.5,bounds=(0.0,1.0),doc="""
       How much the learning is dominated by the activity trace, relative to the current value.""")

    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),readonly=True,
        doc="LearningFn that will be applied to each CF individually.")

    def __call__(self, iterator, np.ndarray[np.float64_t, ndim=2] input_activity,
                 np.ndarray[np.float64_t, ndim=2] output_activity,
                 np.float64_t learning_rate, **params):

        cdef np.float64_t single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        if single_connection_learning_rate==0:
            return

        cfs = iterator.flatcfs
        cdef np.int64_t num_cfs = len(cfs)
        cf_type = iterator.cf_type

        ##Initialise traces to zero if they don't already exist
        cdef np.int64_t orows = output_activity.shape[0]
        cdef np.int64_t ocols = output_activity.shape[1]
        cdef np.ndarray[np.float64_t, ndim=2] traces
        if not hasattr(self,'traces'):
            traces = np.zeros((orows, ocols), activity_type)
            self.traces = traces

        self.traces = (self.trace_strength*output_activity)+((1-self.trace_strength)*self.traces)
        traces = self.traces

        cdef np.int64_t icols = input_activity.shape[1]

        trace_learning(<double*> input_activity.data, <double*> traces.data,
                       num_cfs, icols, cfs, single_connection_learning_rate, cf_type)



class CFPOF_DivisiveNormalize_L1_cython(CFPOutputFn):
    """
    Performs divisive normalization of the weights of all cfs.
    Intended to be equivalent to, but faster than,
    CFPOF_DivisiveNormalizeL1.
    """

    def __call__(self, iterator, **params):
        cf_type=iterator.cf_type
        cfs = iterator.flatcfs
        cdef np.int64_t num_cfs = len(iterator.flatcfs)
        cdef np.ndarray[np.float64_t, ndim=2] active_units_mask = iterator.get_active_units_mask()
        cdef np.ndarray[np.float64_t, ndim=2] sheet_mask = iterator.get_sheet_mask()

        divisive_normalize_l1(<double*> sheet_mask.data, <double*> active_units_mask.data,
                              cfs, cf_type, num_cfs)
