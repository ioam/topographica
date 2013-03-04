"""
Output functions (see basic.py) and projection-level output functions
(see projfn.py) written in C to optimize performance.

Requires the weave package; without it unoptimized versions are used.
"""

import param

from topo.base.cf import CFPOutputFn
from topo.base.functionfamily import TransferFn, IdentityTF
from topo.misc.inlinec import inline,provide_unoptimized_equivalent,\
     c_header,c_decorators

from topo.transferfn import DivisiveNormalizeL1


# For backwards compatibility when loading pickled files; can be deleted
DivisiveNormalizeL1_opt=DivisiveNormalizeL1


# JABALERT: Need to remove 0.0000000000001 constant;
# currently needed to avoid divide-by-zero issues
# in some cases, but should be replaced.

# CEBALERT: not documented: unlike unoptimized equivalent, requires
# _norm_total to have been set.
class CFPOF_DivisiveNormalizeL1_opt(CFPOutputFn):
    """
    Performs divisive normalization of the weights of all cfs.
    Intended to be equivalent to, but faster than,
    CFPOF_DivisiveNormalizeL1.
    """
    single_cf_fn = param.ClassSelector(
        TransferFn,DivisiveNormalizeL1(norm_value=1.0),readonly=True)

    def __call__(self, iterator, **params):
        cf_type=iterator.cf_type  # pyflakes:ignore (passed to weave C code)
        cfs = iterator.flatcfs  # pyflakes:ignore (passed to weave C code)
        num_cfs = len(iterator.flatcfs)  # pyflakes:ignore (passed to weave C code)

        # CB: for performance, it is better to process the masks in
        # the C code (rather than combining them before).
        active_units_mask = iterator.get_active_units_mask()  # pyflakes:ignore (passed to weave C code)
        sheet_mask = iterator.get_sheet_mask()  # pyflakes:ignore (passed to weave C code)

        code = c_header + """

            DECLARE_SLOT_OFFSET(weights,cf_type);
            DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);
            DECLARE_SLOT_OFFSET(_norm_total,cf_type);
            DECLARE_SLOT_OFFSET(_has_norm_total,cf_type);
            DECLARE_SLOT_OFFSET(mask,cf_type);

            %(cfs_loop_pragma)s
            for (int r=0; r<num_cfs; ++r) {
                if (active_units_mask[r] != 0 && sheet_mask[r] != 0) {
                    PyObject *cf = PyList_GetItem(cfs,r);

                    LOOKUP_FROM_SLOT_OFFSET(float,weights,cf);
                    LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);
                    LOOKUP_FROM_SLOT_OFFSET(double,_norm_total,cf);
                    LOOKUP_FROM_SLOT_OFFSET(int,_has_norm_total,cf);

                    UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

                    // if normalized total is not available, sum the weights
                    if (_has_norm_total[0] == 0) {
                        SUM_NORM_TOTAL(cf,weights,_norm_total,rr1,rr2,cc1,cc2);
                    }

                    // normalize the weights
                    double factor = 1.0/_norm_total[0];
                    int rc = (rr2-rr1)*(cc2-cc1);
                    for (int i=0; i<rc; ++i) {
                        *(weights++) *= factor;
                    }

                    // Indicate that norm_total is stale
                    _has_norm_total[0]=0;
                }
            }
        """%c_decorators
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
__all__.remove("CFPOutputFn")
__all__.remove("TransferFn")
__all__.remove("IdentityTF")
__all__.remove("DivisiveNormalizeL1")
