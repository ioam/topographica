"""
Output functions (see basic.py) and projection-level output functions
(see projfn.py) written in C to optimize performance.

Requires the weave package; without it unoptimized versions are used.
"""

from numpy.oldnumeric import sum
import numpy

import param

from topo.base.cf import CFPOutputFn,CFPOF_Plugin
from topo.base.functionfamily import TransferFn, IdentityTF
from topo.misc.inlinec import inline,provide_unoptimized_equivalent,c_header

from basic import DivisiveNormalizeL1


# For backwards compatibility when loading pickled files; can be deleted
DivisiveNormalizeL1_opt=DivisiveNormalizeL1


# JABALERT: Need to remove 0.0000000000001 constant;
# currently needed to avoid divide-by-zero issues
# in some cases, but should be replaced.
class CFPOF_DivisiveNormalizeL1_opt(CFPOutputFn):
    """
    Performs divisive normalization of the weights of all cfs.
    Intended to be equivalent to, but faster than,
    CFPOF_DivisiveNormalizeL1.
    """
    single_cf_fn = param.ClassSelector(
        TransferFn,DivisiveNormalizeL1(norm_value=1.0),readonly=True)
    
    def __call__(self, iterator, **params):
        cf_type=iterator.cf_type
        cfs = iterator.flatcfs
        num_cfs = len(iterator.flatcfs)
        
        # CB: for performance, it is better to process the masks in
        # the C code (rather than combining them before).
        active_units_mask = iterator.get_active_units_mask()
        sheet_mask = iterator.get_sheet_mask()

        code = c_header + """
            // CEBALERT: should provide a macro for getting offset

            ///// GET WEIGHTS OFFSET
            PyMemberDescrObject *weights_descr = (PyMemberDescrObject *)PyObject_GetAttrString(cf_type,"weights");
            Py_ssize_t weights_offset = weights_descr->d_member->offset;
            Py_DECREF(weights_descr);

            ///// GET SLICE OFFSET
            PyMemberDescrObject *slice_descr = (PyMemberDescrObject *)PyObject_GetAttrString(cf_type,"input_sheet_slice");
            Py_ssize_t slice_offset = slice_descr->d_member->offset;
            Py_DECREF(slice_descr);

            // CB: I doubt norm_total can be a property and a slot, but maybe
            // it could be, or maybe we could use the actual attribute...
            
            npfloat *x = active_units_mask;
            npfloat *m = sheet_mask;

            for (int r=0; r<num_cfs; ++r) {
                double load = *x++;
                double msk = *m++;
                if (load != 0 && msk != 0) {
                    PyObject *cf = PyList_GetItem(cfs,r);

                    PyArrayObject *weights_obj = *((PyArrayObject **)((char *)cf + weights_offset));
                    PyArrayObject *slice_obj = *((PyArrayObject **)((char *)cf + slice_offset));

                    PyObject *sum_obj     = PyObject_GetAttrString(cf,"norm_total");

                    float *wi = (float *)(weights_obj->data);
                    int *slice = (int *)(slice_obj->data);

                    double total = PyFloat_AsDouble(sum_obj); // sum of the cf's weights

                    if( total > 0.0000000000001 ) {

                        int rr1 = *slice++;
                        int rr2 = *slice++;
                        int cc1 = *slice++;
                        int cc2 = *slice;
    
                        // normalize the weights
                        double factor = 1.0/total;
                        int rc = (rr2-rr1)*(cc2-cc1);
                        for (int i=0; i<rc; ++i) {
                            *(wi++) *= factor;
                        }

                    }

                    // Anything obtained with PyObject_GetAttrString must be explicitly freed
                    Py_DECREF(sum_obj);

                    // Indicate that norm_total is stale
                    PyObject_SetAttrString(cf,"_has_norm_total",Py_False);
                }
                
            }
        """    
        inline(code, ['sheet_mask','active_units_mask','cfs','cf_type','num_cfs'], 
               local_dict=locals(),
               headers=['<structmember.h>'])


class CFPOF_DivisiveNormalizeL1(CFPOutputFn):
    """
    Non-optimized version of CFPOF_DivisiveNormalizeL1_opt.

    Same as CFPOF_Plugin(single_cf_fn=DivisiveNormalizeL1()), except
    that it supports joint normalization using the norm_total
    property of ConnectionField.
    """

    single_cf_fn = param.ClassSelector(
        TransferFn,default=DivisiveNormalizeL1(norm_value=1.0),constant=True)

    def __call__(self, iterator, **params):
        """
        Uses the cf.norm_total attribute to allow optimization
        by computing the sum separately, and to allow joint
        normalization.  After use, cf.norm_total is deleted because
        the value it would have has been changed.
        """
        # CEBALERT: fix this here and elsewhere
        if type(self.single_cf_fn) is not IdentityTF:
            single_cf_fn = self.single_cf_fn
            norm_value = self.single_cf_fn.norm_value                
            for cf,i in iterator():
                current_sum=cf.norm_total
		if current_sum > 0.0000000000001:
                    factor = norm_value/current_sum
                    cf.weights *= factor
                del cf.norm_total


provide_unoptimized_equivalent("CFPOF_DivisiveNormalizeL1_opt","CFPOF_DivisiveNormalizeL1",locals())


__all__ = list(set([k for k,v in locals().items() if isinstance(v,type) and
                    (issubclass(v,TransferFn) or issubclass(v,CFPOutputFn))]))

