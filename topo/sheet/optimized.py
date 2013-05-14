"""
Inline-optimized Sheet classes
"""

import param

from topo.base.cf import CFIter
from topo.base.projection import NeighborhoodMask
from topo.misc.inlinec import inline,provide_unoptimized_equivalent,c_header
from topo.sheet import SettlingCFSheet
from topo.sheet import compute_joint_norm_totals  # pyflakes:ignore (optimized version provided)

def compute_joint_norm_totals_opt(projlist,active_units_mask):
    """
    Compute norm_total for each CF in each projections from a
    group to be normalized jointly.  The same assumptions are
    made as in the original function.
    """
    # Assumes that all Projections in the list have the same r,c size
    length = len(projlist)
    assert length>=1

    proj = projlist[0]
    iterator = CFIter(proj,active_units_mask=active_units_mask)
    num_cfs = len(proj.flatcfs)  # pyflakes:ignore (passed to weave C code)
    active_units_mask = iterator.get_active_units_mask()
    sheet_mask = iterator.get_sheet_mask()  # pyflakes:ignore (passed to weave C code)
    cf_type = iterator.cf_type  # pyflakes:ignore (passed to weave C code)

    # CEBALERT: Not consistent with other C code. E.g. could be
    # simplified to use active_units_mask[] and sheet_mask[]?

    code = c_header + """
        DECLARE_SLOT_OFFSET(_norm_total,cf_type);
        DECLARE_SLOT_OFFSET(_has_norm_total,cf_type);
        DECLARE_SLOT_OFFSET(weights,cf_type);
        DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);
        DECLARE_SLOT_OFFSET(mask,cf_type);

        npfloat *x = active_units_mask;
        npfloat *m = sheet_mask;
        for (int r=0; r<num_cfs; ++r) {
            double load = *x++;
            double msk = *m++;
            if (msk!=0 && load != 0) {
                double nt = 0;

                for(int p=0; p<length; p++) {
                    PyObject *proj = PyList_GetItem(projlist,p);
                    PyObject *cfs = PyObject_GetAttrString(proj,"flatcfs");
                    PyObject *cf = PyList_GetItem(cfs,r);
                    LOOKUP_FROM_SLOT_OFFSET(int,_has_norm_total,cf);
                    LOOKUP_FROM_SLOT_OFFSET(double,_norm_total,cf);
                    if (_has_norm_total[0] == 0) {
                        LOOKUP_FROM_SLOT_OFFSET(float,weights,cf);
                        LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);

                        UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

                        SUM_NORM_TOTAL(cf,weights,_norm_total,rr1,rr2,cc1,cc2);
                    }
                    nt += _norm_total[0];
                    Py_DECREF(cfs);
                }

                for(int p=0; p<length; p++) {
                    PyObject *proj = PyList_GetItem(projlist,p);
                    PyObject *cfs = PyObject_GetAttrString(proj,"flatcfs");
                    PyObject *cf = PyList_GetItem(cfs,r);

                    LOOKUP_FROM_SLOT_OFFSET(double,_norm_total,cf);
                    _norm_total[0] = nt;
                    LOOKUP_FROM_SLOT_OFFSET(int,_has_norm_total,cf);
                    _has_norm_total[0] = 1;

                    Py_DECREF(cfs);
                }
            }

        }
    """
    inline(code, ['projlist','active_units_mask','sheet_mask','num_cfs','length','cf_type'],
           local_dict=locals(),
           headers=['<structmember.h>'])

provide_unoptimized_equivalent("compute_joint_norm_totals_opt",
                               "compute_joint_norm_totals",locals())

# CEBALERT: not tested
class SettlingCFSheet_Opt(SettlingCFSheet):
    """
    Faster but potentially unsafe optimized version of SettlingCFSheet.

    Adds a NeighborhoodMask that skips computation for neurons
    sufficiently distant from all those activated in the first few
    steps of settling.  This is safe only if activity bubbles reliably
    shrink after the first few steps; otherwise the results will
    differ from SettlingCFSheet.

    Typically useful only for standard SettlingCFSheet simulations with
    localized (e.g. Gaussian) inputs and that shrink the lateral
    excitatory radius, which results in small patches of activity in
    an otherwise inactive sheet.

    Also overrides the function
    JointNormalizingCFSheet.__compute_joint_norm_totals with
    C-optimized code for SettlingCFSheets.
    """

    joint_norm_fn = param.Callable(default=compute_joint_norm_totals_opt)

    def __init__(self,**params):
        super(SettlingCFSheet_Opt,self).__init__(**params)
        # CEBALERT: this wipes out any user-specified sheet mask.
        self.mask = NeighborhoodMask_Opt(threshold = 0.00001,radius = 0.05,sheet = self)

provide_unoptimized_equivalent("SettlingCFSheet_Opt","SettlingCFSheet",locals())

# Legacy declaration for backwards compatibility
LISSOM_Opt=SettlingCFSheet_Opt


class NeighborhoodMask_Opt(NeighborhoodMask):

    def calculate(self):
        rows,cols = self.data.shape
        ignore1,matradius = self.sheet.sheet2matrixidx(self.radius,0)
        ignore2,x = self.sheet.sheet2matrixidx(0,0)
        matradius = int(abs(matradius -x))
        thr = self.threshold  # pyflakes:ignore (passed to weave C code)
        activity = self.sheet.activity  # pyflakes:ignore (passed to weave C code)
        mask = self.data  # pyflakes:ignore (passed to weave C code)

        code = c_header + """
            #define min(x,y) (x<y?x:y)
            #define max(x,y) (x>y?x:y)

            npfloat *X = mask;
            npfloat *A = activity;
            for (int r=0; r<rows; ++r) {
                for (int l=0; l<cols; ++l) {
                    int lbx = max(0,r-matradius);
                    int lby = max(0,l-matradius);
                    int hbx = min(r+matradius+1,rows);
                    int hby = min(l+matradius+1,cols);

                    *X = 0.0;
                    int breakFlag = 0;
                    for(int k=lbx;k<hbx;k++)
                    {
                        for(int l=lby;l<hby;l++)
                        {
                            npfloat *a = A+k*rows + l;
                            if(*a > thr)
                            {
                                *X = 1.0;
                                //JAALERT HACK. Want to jump out both nested loops!!!
                                breakFlag = 1;
                                break;
                            }
                        }
                        if(breakFlag)break;
                    }

                    X++;
                }
            }
        """
        inline(code, ['thr','activity','matradius','mask','rows','cols'], local_dict=locals())

provide_unoptimized_equivalent("NeighborhoodMask_Opt","NeighborhoodMask",locals())


__all__ = [
    "compute_joint_norm_totals",
    "SettlingCFSheet",
    "NeighborhoodMask",
]
