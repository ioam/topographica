"""
Response functions (see basic.py) and CFProjection response functions
(see projfn.py) written in C to optimize performance.

Requires the weave package; without it unoptimized versions are used.

$Id$
"""
__version__='$Revision$'

import param

from topo.base.functionfamily import ResponseFn,DotProduct
from topo.base.cf import CFPResponseFn, CFPRF_Plugin
from topo.misc.inlinec import inline,provide_unoptimized_equivalent,c_header
from topo.misc.pyxhandler import provide_unoptimized_equivalent_cy
from topo.responsefn.projfn import CFPRF_EuclideanDistance


    

# CEBALERT: the "only works for 1D array" doc is out of date, right?
# Should remove from here and other optimized fns that have been
# flattened.

# CEB: why the double loop for the dot product?

class CFPRF_DotProduct_opt(CFPResponseFn):
    """
    Dot-product response function.

    Written in C for a manyfold speedup; see CFPRF_DotProduct for an
    easier-to-read version in Python.  The unoptimized Python version
    is equivalent to this one, but it also works for 1D arrays.
    """

    single_cf_fn = param.ClassSelector(ResponseFn,DotProduct(),readonly=True)    

    def __call__(self, iterator, input_activity, activity, strength, **params):
       
        temp_act = activity
        irows,icols = input_activity.shape
        X = input_activity.ravel()
        cfs = iterator.flatcfs
        num_cfs = len(cfs)
        mask = iterator.mask.data

        cf_type = iterator.cf_type
    
        code = c_header + """
            DECLARE_SLOT_OFFSET(weights,cf_type);
            DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);

            for (int r=0; r<num_cfs; ++r) {
                if(mask[r] == 0.0)
                    temp_act[r] = 0;
                else {
                    PyObject *cf = PyList_GetItem(cfs,r);

                    CONTIGUOUS_ARRAY_FROM_SLOT_OFFSET(float,weights,cf)
                    LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);

                    UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

                    double tot = 0.0;
                    npfloat *xj = X+icols*rr1+cc1;

                    // computes the dot product
                    for (int i=rr1; i<rr2; ++i) {
                        npfloat *xi = xj;
                        float *wi = weights;                       
                        for (int j=cc1; j<cc2; ++j) {
                            tot += *wi * *xi;
                            ++wi;
                            ++xi;
                        }
                        xj += icols;
                        weights += cc2-cc1;
                    }  
                    temp_act[r] = tot*strength;

                    DECREF_CONTIGUOUS_ARRAY(weights);
                }
            }
        """
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
    from optimized_cy import CFPRF_DotProduct_cyopt
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
        temp_act = activity
        rows,cols = activity.shape
        irows,icols = input_activity.shape
        X = input_activity.ravel()
        cfs = iterator.flatcfs
        num_cfs = len(cfs)

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
