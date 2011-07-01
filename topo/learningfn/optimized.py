"""
Learning functions (see basic.py) and projection-level learning
functions (see projfn.py) written in C to optimize performance.

Requires the weave package; without it unoptimized versions are used.

$Id$
"""
__version__ = "$Revision$"

from numpy import zeros, ones

import param

from topo.base.sheet import activity_type
from topo.base.cf import CFPLearningFn,CFPLF_Plugin
from topo.learningfn.projfn import CFPLF_PluginScaled
from topo.base.functionfamily import Hebbian,LearningFn
from topo.misc.inlinec import inline,provide_unoptimized_equivalent,c_header
from topo.learningfn.basic import BCMFixed

from projfn import CFPLF_Trace




class CFPLF_Hebbian_opt(CFPLearningFn):
    """
    CF-aware Hebbian learning rule.

    Implemented in C for speed.  Should be equivalent to
    CFPLF_Plugin(single_cf_fn=Hebbian), except faster.

    As a side effect, sets the norm_total attribute on any cf whose
    weights are updated during learning, to speed up later operations
    that might depend on it.

    May return without modifying anything if the learning rate turns
    out to be zero.
    """
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),readonly=True)
    
    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        if single_connection_learning_rate==0:
            return

        cfs = iterator.flatcfs
        num_cfs = len(cfs)
        irows,icols = input_activity.shape
        cf_type = iterator.cf_type

        # CEBALERT: this function *always* skips inactive units,
        # because it uses the output_activity directly rather than
        # going through the iterator. That's ok since we know this
        # function can always skip inactive units. But the unoptimized
        # equivalent should be made to do the same, because right now
        # it respects the iterator.  (Just a case of setting the
        # iterator's active_units_mask to be True before calling the
        # iterator in the unoptimized version.)

        sheet_mask = iterator.get_sheet_mask()

        code = c_header + """
            DECLARE_SLOT_OFFSET(weights,cf_type);
            DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);
            DECLARE_SLOT_OFFSET(mask,cf_type);

            for (int r=0; r<num_cfs; ++r) {
                double load = output_activity[r];
                if (load != 0 && sheet_mask[r] != 0) {
                    load *= single_connection_learning_rate;

                    PyObject *cf = PyList_GetItem(cfs,r);

                    LOOKUP_FROM_SLOT_OFFSET(float,weights,cf);
                    LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);
                    LOOKUP_FROM_SLOT_OFFSET(float,mask,cf);

                    UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

                    double total = 0.0;

                    // modify non-masked weights
                    npfloat *inpj = input_activity+icols*rr1+cc1;
                    for (int i=rr1; i<rr2; ++i) {
                        npfloat *inpi = inpj;
                        for (int j=cc1; j<cc2; ++j) {
                            // The mask is floating point, so we have to 
                            // use a robust comparison instead of testing 
                            // against exactly 0.0.
                            if (*(mask++) >= 0.000001) {
                                *weights += load * *inpi;
                                total += fabs(*weights);
                            }
                            ++weights;
                            ++inpi;
                        }
                        inpj += icols;
                    }

                    // store the sum of the cf's weights
                    PyObject *total_obj = PyFloat_FromDouble(total);  //(new ref)
                    PyObject_SetAttrString(cf,"_norm_total",total_obj);
                    PyObject_SetAttrString(cf,"_has_norm_total",Py_True);
                    Py_DECREF(total_obj);
                }
            }
        """

        inline(code, ['input_activity', 'output_activity','sheet_mask','num_cfs',
                      'icols', 'cfs', 'single_connection_learning_rate','cf_type'],
               local_dict=locals(),
               headers=['<structmember.h>'])               


class CFPLF_Hebbian(CFPLF_Plugin):
    """Same as CFPLF_Plugin(single_cf_fn=Hebbian()); just for non-optimized fallback."""
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),readonly=True)
provide_unoptimized_equivalent("CFPLF_Hebbian_opt","CFPLF_Hebbian",locals())


# CBERRORALERT: classes from here on probably ignore the sheet mask 

# JABALERT: Is this really a fixed-threshold BCM rule?  If so, is that really useful?
class CFPLF_BCMFixed_opt(CFPLearningFn):
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
    
    unit_threshold=param.Number(default=0.5,bounds=(0,None),doc="Threshold between LTD and LTP.")
    
    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        rows,cols = output_activity.shape
        cfs = iterator.flatcfs
        num_cfs = len(cfs)
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        if single_connection_learning_rate==0:
            return
        
        unit_threshold=self.unit_threshold
        
        irows,icols = input_activity.shape
        cf_type = iterator.cf_type
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

            ///// GET MASK OFFSET
            PyMemberDescrObject *mask_descr = (PyMemberDescrObject *)PyObject_GetAttrString(cf_type,"mask");
            Py_ssize_t mask_offset = mask_descr->d_member->offset;
            Py_DECREF(mask_descr);


            npfloat *x = output_activity;

            for (int r=0; r<num_cfs; ++r) {
                double load = *x++;
                double unit_activity= load;
                if (load != 0) {
                    load *= single_connection_learning_rate;

                    PyObject *cf = PyList_GetItem(cfs,r);

                    PyArrayObject *weights_obj = *((PyArrayObject **)((char *)cf + weights_offset));
                    PyArrayObject *slice_obj = *((PyArrayObject **)((char *)cf + slice_offset));
                    PyArrayObject *mask_obj = *((PyArrayObject **)((char *)cf + mask_offset));

                    float *wi = (float *)(weights_obj->data);
                    int *slice = (int *)(slice_obj->data);
                    float *m = (float *)(mask_obj->data);

                    int rr1 = *slice++;
                    int rr2 = *slice++;
                    int cc1 = *slice++;
                    int cc2 = *slice;

                    double total = 0.0;

                    // modify non-masked weights
                    npfloat *inpj = input_activity+icols*rr1+cc1;
                    for (int i=rr1; i<rr2; ++i) {
                        npfloat *inpi = inpj;
                        for (int j=cc1; j<cc2; ++j) {
                            // The mask is floating point, so we have to 
                            // use a robust comparison instead of testing 
                            // against exactly 0.0.
                            if (*(m++) >= 0.000001) {
                                *wi += load * *inpi * (unit_activity - unit_threshold);
                                if (*wi<0) { *wi = 0;}
                                total += fabs(*wi);
                            }
                            ++wi;
                            ++inpi;
                        }
                        inpj += icols;
                    }

                    // store the sum of the cf's weights
                    PyObject *total_obj = PyFloat_FromDouble(total);  //(new ref)
                    PyObject_SetAttrString(cf,"_norm_total",total_obj);
                    PyObject_SetAttrString(cf,"_has_norm_total",Py_True);
                    Py_DECREF(total_obj);
                }
            }
        """

        inline(code, ['input_activity', 'output_activity','num_cfs',
                      'icols', 'cfs', 'single_connection_learning_rate',
                      'unit_threshold','cf_type'],
               local_dict=locals(),
               headers=['<structmember.h>'])               


class CFPLF_BCMFixed(CFPLF_Plugin):
    """Same as CFPLF_Plugin(single_cf_fn=BCMFixed()); just for non-optimized fallback."""
    single_cf_fn = param.ClassSelector(LearningFn,default=BCMFixed(),readonly=True)
provide_unoptimized_equivalent("CFPLF_BCMFixed_opt","CFPLF_Hebbian",locals())


# CEBALERT: 2009/04/03 - when used in GCA-LISSOM, causes Python to crash.
class CFPLF_Scaled_opt(CFPLF_PluginScaled):
    """
    CF-aware Scaled Hebbian learning rule.

    Implemented in C for speed.  Should be equivalent to
    CFPLF_PluginScaled(single_cf_fn=Hebbian), except faster.  

    As a side effect, sets the norm_total attribute on any cf whose
    weights are updated during learning, to speed up later operations
    that might depend on it.
    """
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),readonly=True)
    
    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        
        if self.learning_rate_scaling_factor is None:
            self.learning_rate_scaling_factor = ones(output_activity.shape)*1.0

        learning_rate_scaling_factor = self.learning_rate_scaling_factor

        cfs = iterator.flatcfs
        num_cfs = len(cfs)
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        if single_connection_learning_rate==0:
            return
        
        irows,icols = input_activity.shape
        code = c_header + """
            npfloat *x = output_activity;
            double *sclr = learning_rate_scaling_factor;

            for (int r=0; r<num_cfs; ++r) {
                double load = *x++;
                double  a= *sclr++;
                load = load * a;
                if (load != 0) {
                    load *= single_connection_learning_rate;
                    PyObject *cf = PyList_GetItem(cfs,r);
                    PyObject *weights_obj = PyObject_GetAttrString(cf,"weights");
                    PyObject *slice_obj   = PyObject_GetAttrString(cf,"input_sheet_slice");
                    PyObject *mask_obj    = PyObject_GetAttrString(cf,"mask");

                    float *wi = (float *)(((PyArrayObject*)weights_obj)->data);
                    int *slice =  (int *)(((PyArrayObject*)slice_obj)->data);
                    float *m  = (float *)(((PyArrayObject*)mask_obj)->data);

                    int rr1 = *slice++;
                    int rr2 = *slice++;
                    int cc1 = *slice++;
                    int cc2 = *slice;

                    double total = 0.0;

                    // modify non-masked weights
                    npfloat *inpj = input_activity+icols*rr1+cc1;
                    for (int i=rr1; i<rr2; ++i) {
                        npfloat *inpi = inpj;
                        for (int j=cc1; j<cc2; ++j) {
                            // The mask is floating point, so we have to 
                            // use a robust comparison instead of testing 
                            // against exactly 0.0.
                            if (*(m++) >= 0.000001) {
                                *wi += load * *inpi;
                                total += fabs(*wi);
                            }
                            ++wi;
                            ++inpi;
                        }
                        inpj += icols;
                    }

                    // Anything obtained with PyObject_GetAttrString must be explicitly freed
                    Py_DECREF(weights_obj);
                    Py_DECREF(slice_obj);
                    Py_DECREF(mask_obj);

                    // store the sum of the cf's weights
                    PyObject *total_obj = PyFloat_FromDouble(total);  //(new ref)
                    PyObject_SetAttrString(cf,"_norm_total",total_obj);
                    PyObject_SetAttrString(cf,"_has_norm_total",Py_True);
                    Py_DECREF(total_obj);
                }
            }
            
        """

        inline(code, ['input_activity','learning_rate_scaling_factor', 'output_activity','num_cfs', 'icols', 'cfs', 'single_connection_learning_rate'], local_dict=locals())


class CFPLF_Scaled(CFPLF_PluginScaled):
    """Same as CFPLF_PluginScaled(single_cf_fn=Hebbian()); just for non-optimized fallback."""
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),readonly=True)
provide_unoptimized_equivalent("CFPLF_Scaled_opt","CFPLF_Scaled",locals())



class CFPLF_Trace_opt(CFPLearningFn):
    """
    Optimized version of CFPLF_Trace; see projfn.py for more info 
    """

    trace_strength=param.Number(default=0.5,bounds=(0.0,1.0),doc="""
       How much the learning is dominated by the activity trace, relative to the current value.""")

    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),readonly=True,
        doc="LearningFn that will be applied to each CF individually.")              

    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        cfs = iterator.flatcfs
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        irows,icols = input_activity.shape
        
        if single_connection_learning_rate==0:
            return
        
        ##Initialise traces to zero if they don't already exist
        if not hasattr(self,'traces'):
            self.traces=zeros(output_activity.shape,activity_type)
        
        self.traces = (self.trace_strength*output_activity)+((1-self.trace_strength)*self.traces)
        traces = self.traces
        
        code = c_header + """
            npfloat *x = traces;

            for (int r=0; r<num_cfs; ++r) {
                double load = *x++;
                if (load != 0) {
                    load *= single_connection_learning_rate;
                    PyObject *cf = PyList_GetItem(cfs,r);
                    PyObject *weights_obj = PyObject_GetAttrString(cf,"weights");
                    PyObject *slice_obj   = PyObject_GetAttrString(cf,"input_sheet_slice");
                    PyObject *mask_obj    = PyObject_GetAttrString(cf,"mask");

                    float *wi = (float *)(((PyArrayObject*)weights_obj)->data);
                    int *slice =  (int *)(((PyArrayObject*)slice_obj)->data);
                    float *m  = (float *)(((PyArrayObject*)mask_obj)->data);

                    int rr1 = *slice++;
                    int rr2 = *slice++;
                    int cc1 = *slice++;
                    int cc2 = *slice;

                    double total = 0.0;

                    // modify non-masked weights
                    npfloat *inpj = input_activity+icols*rr1+cc1;
                    for (int i=rr1; i<rr2; ++i) {
                        npfloat *inpi = inpj;
                        for (int j=cc1; j<cc2; ++j) {
                            // The mask is floating point, so we have to 
                            // use a robust comparison instead of testing 
                            // against exactly 0.0.
                            if (*(m++) >= 0.000001) {
                                *wi += load * *inpi;
                                total += fabs(*wi);
                            }
                            ++wi;
                            ++inpi;
                        }
                        inpj += icols;
                    }

                    // Anything obtained with PyObject_GetAttrString must be explicitly freed
                    Py_DECREF(weights_obj);
                    Py_DECREF(slice_obj);
                    Py_DECREF(mask_obj);

                    // store the sum of the cf's weights
                    PyObject *total_obj = PyFloat_FromDouble(total);  //(new ref)
                    PyObject_SetAttrString(cf,"norm_total",total_obj);
                    PyObject_SetAttrString(cf,"_has_norm_total",Py_True);
                    Py_DECREF(total_obj);
                }
            }
        """

        inline(code, ['input_activity', 'traces','num_cfs', 'icols', 'cfs', 'single_connection_learning_rate'], local_dict=locals())


provide_unoptimized_equivalent("CFPLF_Trace_opt","CFPLF_Trace",locals())
