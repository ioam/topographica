"""
Inline-optimized Sheet classes

$Id$
"""
__version__='$Revision$'

import param

from topo.base.cf import MaskedCFIter
from topo.base.functionfamily import TransferFn, IdentityTF
from topo.base.projection import Projection, NeighborhoodMask
from topo.misc.inlinec import inline,provide_unoptimized_equivalent,c_header
from topo.sheet.lissom import LISSOM, JointScaling
from topo.sheet.basic import compute_joint_norm_totals

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
    iterator = MaskedCFIter(proj,active_units_mask=active_units_mask)
    num_cfs = len(proj.flatcfs)
    active_units_mask = iterator.get_active_units_mask()
    sheet_mask = iterator.get_sheet_mask()

    code = c_header + """
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
                    PyObject *o = PyObject_GetAttrString(cf,"norm_total");
                    nt += PyFloat_AsDouble(o);
                    Py_DECREF(cfs);
                    Py_DECREF(o);
                }

                for(int p=0; p<length; p++) {
                    PyObject *proj = PyList_GetItem(projlist,p);
                    PyObject *cfs = PyObject_GetAttrString(proj,"flatcfs");
                    PyObject *cf = PyList_GetItem(cfs,r);
                    PyObject *total_obj = PyFloat_FromDouble(nt);  //(new ref)
                    PyObject_SetAttrString(cf,"_norm_total",total_obj);
                    PyObject_SetAttrString(cf,"_has_norm_total",Py_True);
                    Py_DECREF(cfs);
                    Py_DECREF(total_obj);
                }
            }

        }
    """    
    inline(code, ['projlist','active_units_mask','sheet_mask','num_cfs','length'], 
           local_dict=locals())

provide_unoptimized_equivalent("compute_joint_norm_totals_opt",
                               "compute_joint_norm_totals",locals())

# CEBALERT: not tested
class LISSOM_Opt(LISSOM):
    """
    Faster but potentially unsafe optimized version of LISSOM.

    Adds a NeighborhoodMask that skips computation for neurons
    sufficiently distant from all those activated in the first few
    steps of settling.  This is safe only if activity bubbles reliably
    shrink after the first few steps; otherwise the results will
    differ from LISSOM.

    Typically useful only for standard LISSOM simulations with
    localized (e.g. Gaussian) inputs and that shrink the lateral
    excitatory radius, which results in small patches of activity in
    an otherwise inactive sheet.

    Also overrides the function
    JointNormalizingCFSheet.__compute_joint_norm_totals with
    C-optimized code for LISSOM sheets.
    """
    
    joint_norm_fn = param.Callable(default=compute_joint_norm_totals_opt)

    def __init__(self,**params):
        super(LISSOM_Opt,self).__init__(**params)
        # CEBALERT: this wipes out any user-specified sheet mask.
        self.mask = NeighborhoodMask_Opt(threshold = 0.00001,radius = 0.05,sheet = self)

provide_unoptimized_equivalent("LISSOM_Opt","LISSOM",locals())



class NeighborhoodMask_Opt(NeighborhoodMask):
    
    def calculate(self):
        rows,cols = self.data.shape
        ignore1,matradius = self.sheet.sheet2matrixidx(self.radius,0)
        ignore2,x = self.sheet.sheet2matrixidx(0,0)
        matradius = int(abs(matradius -x))
        thr = self.threshold
        activity = self.sheet.activity
        mask = self.data
        
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
