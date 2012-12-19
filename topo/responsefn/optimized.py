"""
Response functions and CFProjection response functions (see projfn.py) written
in C to optimize performance.

Requires the weave package; without it unoptimized versions are used.
"""

import param

from topo.base.functionfamily import ResponseFn,DotProduct
from topo.base.cf import CFPResponseFn, CFPRF_Plugin
from topo.misc.inlinec import inline,provide_unoptimized_equivalent,\
     c_header,c_decorators
from topo.misc.pyxhandler import provide_unoptimized_equivalent_cy
from topo.responsefn.projfn import CFPRF_EuclideanDistance  # pyflakes:ignore (optimized version provided)


# CEBALERT: this function works for 1D arrays; the docstring below is
# out of date. Need to update for this and other optimized fns that
# have been flattened.

class CFPRF_DotProduct_opt(CFPResponseFn):
    """
    Dot-product response function.

    Written in C for a manyfold speedup; see CFPRF_DotProduct for an
    easier-to-read version in Python.  The unoptimized Python version
    is equivalent to this one, but it also works for 1D arrays.
    """

    single_cf_fn = param.ClassSelector(ResponseFn,DotProduct(),readonly=True)

    def __call__(self, iterator, input_activity, activity, strength, **params):

        temp_act = activity  # pyflakes:ignore (passed to weave C code)
        irows,icols = input_activity.shape
        X = input_activity.ravel()  # pyflakes:ignore (passed to weave C code)
        cfs = iterator.flatcfs
        num_cfs = len(cfs)  # pyflakes:ignore (passed to weave C code)
        mask = iterator.mask.data  # pyflakes:ignore (passed to weave C code)

        cf_type = iterator.cf_type  # pyflakes:ignore (passed to weave C code)

        # Note: no performance hit from array indexing of mask and
        # temp_act (r11447).
        code = c_header + """
            DECLARE_SLOT_OFFSET(weights,cf_type);
            DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);

            %(cfs_loop_pragma)s
            for (int r=0; r<num_cfs; ++r) {
                if(mask[r] == 0.0) {
                    temp_act[r] = 0;
                } else {
                    PyObject *cf = PyList_GetItem(cfs,r);

                    // CONTIGUOUS_ARRAY_FROM_SLOT_OFFSET(float,weights,cf) <<<<<<<<<<<

                    LOOKUP_FROM_SLOT_OFFSET_UNDECL_DATA(float,weights,cf);
                    char *data = weights_obj->data;
                    int s0 = weights_obj->strides[0];
                    int s1 = weights_obj->strides[1];

                    LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);

                    UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

                    double tot = 0.0;
                    npfloat *xj = X+icols*rr1+cc1;

                    // computes the dot product
                    for (int i=rr1; i<rr2; ++i) {
                        npfloat *xi = xj;


                    //    float *wi = weights;
                    //    for (int j=cc1; j<cc2; ++j) {
                    //        tot += *wi * *xi;
                    //        ++wi;
                    //        ++xi;
                    //    }


                   for (int j=cc1; j<cc2; ++j) {
                      tot += *((float *)(data + (i-rr1)*s0 + (j-cc1)*s1)) * *xi;
                      ++xi;
                   }

                        xj += icols;
                 //       weights += cc2-cc1;
                    }
                    temp_act[r] = tot*strength;

                //    DECREF_CONTIGUOUS_ARRAY(weights);
                }
            }
        """%c_decorators
        inline(code, ['mask','X', 'strength', 'icols', 'temp_act','cfs','num_cfs','cf_type'],
               local_dict=locals(), headers=['<structmember.h>'])

class CFPRF_DotProduct(CFPRF_Plugin):
    """
    Wrapper written to allow transparent non-optimized fallback;
    equivalent to CFPRF_Plugin(single_cf_fn=DotProduct()).
    """
    # CB: should probably have single_cf_fn here & readonly
    def __init__(self,**params):
        super(CFPRF_DotProduct,self).__init__(single_cf_fn=DotProduct(),**params)

provide_unoptimized_equivalent("CFPRF_DotProduct_opt","CFPRF_DotProduct",locals())


try:
    from optimized_cy import CFPRF_DotProduct_cyopt  # pyflakes:ignore (optimized version)
except:
    pass

provide_unoptimized_equivalent_cy("CFPRF_DotProduct_cyopt","CFPRF_DotProduct",locals())



# CEBERRORALERT: ignores the sheet mask!
class CFPRF_EuclideanDistance_opt(CFPResponseFn):
    """
    Euclidean-distance response function.

    Written in C for a several-hundred-times speedup; see
    CFPRF_EuclideanDistance for an easier-to-read (but otherwise
    equivalent) version in Python.
    """
    def __call__(self, iterator, input_activity, activity, strength, **params):
        temp_act = activity  # pyflakes:ignore (passed to weave C code)
        rows,cols = activity.shape
        irows,icols = input_activity.shape
        X = input_activity.ravel()  # pyflakes:ignore (passed to weave C code)
        cfs = iterator.flatcfs
        num_cfs = len(cfs)  # pyflakes:ignore (passed to weave C code)

        code = c_header + """
            #include <math.h>
            npfloat *tact = temp_act;
            double max_dist=0.0;

            for (int r=0; r<num_cfs; ++r) {
                PyObject *cf = PyList_GetItem(cfs,r);

                PyObject *weights_obj = PyObject_GetAttrString(cf,"weights");
                PyObject *slice_obj   = PyObject_GetAttrString(cf,"input_sheet_slice");

                float *wj = (float *)(((PyArrayObject*)weights_obj)->data);
                int *slice =  (int *)(((PyArrayObject*)slice_obj)->data);

                int rr1 = *slice++;
                int rr2 = *slice++;
                int cc1 = *slice++;
                int cc2 = *slice;

                npfloat *xj = X+icols*rr1+cc1;

                // computes the dot product
                double tot = 0.0;
                for (int i=rr1; i<rr2; ++i) {
                    npfloat *xi = xj;
                    float *wi = wj;
                    for (int j=cc1; j<cc2; ++j) {
                        double diff = *wi - *xi;
                        tot += diff*diff;
                        ++wi;
                        ++xi;
                    }
                    xj += icols;
                    wj += cc2-cc1;
                }

                double euclidean_distance = sqrt(tot);
                if (euclidean_distance>max_dist)
                    max_dist = euclidean_distance;

                *tact = euclidean_distance;
                ++tact;

                // Anything obtained with PyObject_GetAttrString must be explicitly freed
                Py_DECREF(weights_obj);
                Py_DECREF(slice_obj);
            }
            tact = temp_act;
            for (int r=0; r<num_cfs; ++r) {
                *tact = strength*(max_dist - *tact);
                ++tact;
            }
        """
        inline(code, ['X', 'strength', 'icols', 'temp_act','cfs','num_cfs'],
               local_dict=locals())

provide_unoptimized_equivalent("CFPRF_EuclideanDistance_opt","CFPRF_EuclideanDistance",locals())
