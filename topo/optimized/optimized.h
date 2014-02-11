#include <structmember.h>
#include <omp.h>
#include <math.h>

/* For a given class cls and an attribute attr, defines a variable
   attr_offset containing the offset of that attribute in the class's
   __slots__ data structure. */
#define DECLARE_SLOT_OFFSET(attr,cls) \
  PyMemberDescrObject *attr ## _descr = (PyMemberDescrObject *)PyObject_GetAttrString(cls,#attr); \
  Py_ssize_t attr ## _offset = attr ## _descr->d_member->offset; \
  Py_DECREF(attr ## _descr)

/* After a previous declaration of DECLARE_SLOT_OFFSET, for an
   instance obj of that class and the given attr, retrieves the value
   of that attribute from its slot. */
#define LOOKUP_FROM_SLOT_OFFSET(type,attr,obj) \
  PyArrayObject *attr ## _obj = *((PyArrayObject **)((char *)obj + attr ## _offset)); \
  type *attr = (type *)(attr ## _obj->data)

/* LOOKUP_FROM_SLOT_OFFSET without declaring data variable */
#define LOOKUP_FROM_SLOT_OFFSET_UNDECL_DATA(type,attr,obj) \
  PyArrayObject *attr ## _obj = *((PyArrayObject **)((char *)obj + attr ## _offset));

/* Same as LOOKUP_FROM_SLOT_OFFSET but ensures the array is contiguous.
   Must call DECREF_CONTIGUOUS_ARRAY(attr) to release temporary.
   Does PyArray_FLOAT need to be an argument for this to work with doubles? */

// This code is optimized for contiguous arrays, which are typical,
// but we make it work for noncontiguous arrays (e.g. views) by
// creating a contiguous copy if necessary.
//
// CEBALERT: I think there are better alternatives
// e.g. PyArray_GETCONTIGUOUS (PyArrayObject*) (PyObject* op)
// (p248 of numpybook), which only acts if necessary...
// Do we have a case where we know this code is being
// called, so that I can test it easily?

// CEBALERT: weights_obj appears below. Doesn't that mean this thing
// will only work when attr is weights?

#define CONTIGUOUS_ARRAY_FROM_SLOT_OFFSET(type,attr,obj) \
  PyArrayObject *attr ## _obj = *((PyArrayObject **)((char *)obj + attr ## _offset)); \
  type *attr = 0; \
  PyArrayObject * attr ## _array = 0; \
  if(PyArray_ISCONTIGUOUS(weights_obj)) \
      attr = (type *)(attr ## _obj->data); \
  else { \
      attr ## _array = (PyArrayObject*) PyArray_ContiguousFromObject((PyObject*)attr ## _obj,PyArray_FLOAT,2,2); \
      attr = (type *) attr ## _array->data; \
  }

#define DECREF_CONTIGUOUS_ARRAY(attr) \
   if(attr ## _array != 0) { \
       Py_DECREF(attr ## _array); }

#define UNPACK_FOUR_TUPLE(type,i1,i2,i3,i4,tuple) \
  type i1 = *tuple++; \
  type i2 = *tuple++; \
  type i3 = *tuple++; \
  type i4 = *tuple

#define MASK_THRESHOLD 0.5

#define SUM_NORM_TOTAL(cf,weights,_norm_total,rr1,rr2,cc1,cc2) \
  LOOKUP_FROM_SLOT_OFFSET(float,mask,cf); \
  double total = 0.0; \
  float* weights_init = weights; \
  int i, j; \
  for (i=rr1; i<rr2; ++i) { \
    for (j=cc1; j<cc2; ++j) { \
      if (*(mask++) >= MASK_THRESHOLD) { \
        total += fabs(*weights_init); \
      } \
      ++weights_init; \
    } \
  } \
  _norm_total[0] = total



void dot_product(double mask[], double X[], double strength, int icols,
                 double temp_act[], PyObject* cfs, int num_cfs, PyObject* cf_type) {

    DECLARE_SLOT_OFFSET(weights,cf_type);
    DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);

    int r, i, j;

    #pragma omp parallel for schedule(guided, 8)
    for (r=0; r<num_cfs; ++r) {
        if(mask[r] == 0.0) {
            temp_act[r] = 0;
        } else {
            PyObject *cf = PyList_GetItem(cfs,r);

            LOOKUP_FROM_SLOT_OFFSET_UNDECL_DATA(float,weights,cf);
            char *data = weights_obj->data;
            int s0 = weights_obj->strides[0];
            int s1 = weights_obj->strides[1];

            LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);

            UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

            double tot = 0.0;
            double *xj = X+icols*rr1+cc1;

            // computes the dot product
            for (i=rr1; i<rr2; ++i) {
                double *xi = xj;

           for (j=cc1; j<cc2; ++j) {
              tot += *((float *)(data + (i-rr1)*s0 + (j-cc1)*s1)) * *xi;
              ++xi;
           }
                xj += icols;
            }
            temp_act[r] = tot*strength;
        }
    }
}


void euclidean_response(double input_activity[], double strength, int icols,
                        double temp_act[], PyObject* cfs, int num_cfs) {
    double *tact = temp_act;
    double max_dist=0.0;

    int r;

    for (r=0; r<num_cfs; ++r) {
        PyObject *cf = PyList_GetItem(cfs,r);

        PyObject *weights_obj = PyObject_GetAttrString(cf,"weights");
        PyObject *slice_obj   = PyObject_GetAttrString(cf,"input_sheet_slice");

        float *wj = (float *)(((PyArrayObject*)weights_obj)->data);
        int *slice =  (int *)(((PyArrayObject*)slice_obj)->data);

        int rr1 = *slice++;
        int rr2 = *slice++;
        int cc1 = *slice++;
        int cc2 = *slice;

        double *xj = input_activity+icols*rr1+cc1;

        int i, j;

        // computes the dot product
        double tot = 0.0;
        for (i=rr1; i<rr2; ++i) {
            double *xi = xj;
            float *wi = wj;
            for (j=cc1; j<cc2; ++j) {
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
    for (r=0; r<num_cfs; ++r) {
        *tact = strength*(max_dist - *tact);
        ++tact;
    }
}


/* Learning Functions including simple Hebbian, BCM etc. */

void hebbian(double input_activity[], double output_activity[],
             double sheet_mask[], const int num_cfs, const int icols,
             PyObject* cfs, double single_connection_learning_rate, PyObject* cf_type) {
    DECLARE_SLOT_OFFSET(weights,cf_type);
    DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);
    DECLARE_SLOT_OFFSET(mask,cf_type);
    DECLARE_SLOT_OFFSET(_norm_total,cf_type);
    DECLARE_SLOT_OFFSET(_has_norm_total,cf_type);

    int r;

    #pragma omp parallel for schedule(guided, 8)
    for (r=0; r<num_cfs; ++r) {
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
            double *inpj = input_activity+icols*rr1+cc1;
            int i, j;
            for (i=rr1; i<rr2; ++i) {
                double *inpi = inpj;
                for (j=cc1; j<cc2; ++j) {
                    // The mask is floating point, so we have to
                    // use a robust comparison instead of testing
                    // against exactly 0.0.
                    if (*(mask++) >= MASK_THRESHOLD) {
                          *weights += load * *inpi;
                          total += fabs(*weights);
                    }
                    ++weights;
                    ++inpi;
                }
                inpj += icols;
            }
            // store the sum of the cf's weights
            LOOKUP_FROM_SLOT_OFFSET(double,_norm_total,cf);
            _norm_total[0]=total;
            LOOKUP_FROM_SLOT_OFFSET(int,_has_norm_total,cf);
            _has_norm_total[0]=1;
        }
    }
}


void bcm_fixed(double input_activity[], double output_activity[], int num_cfs,
               int icols, PyObject* cfs, double single_connection_learning_rate,
               double unit_threshold, PyObject* cf_type) {
    DECLARE_SLOT_OFFSET(weights,cf_type);
    DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);
    DECLARE_SLOT_OFFSET(mask,cf_type);
    DECLARE_SLOT_OFFSET(_norm_total,cf_type);
    DECLARE_SLOT_OFFSET(_has_norm_total,cf_type);

    int r;

    #pragma omp parallel for schedule(guided, 8)
    for (r=0; r<num_cfs; ++r) {
        double load = output_activity[r];
        double unit_activity= load;
        if (load != 0) {
            load *= single_connection_learning_rate;

            PyObject *cf = PyList_GetItem(cfs,r);

            LOOKUP_FROM_SLOT_OFFSET(float,weights,cf);
            LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);
            LOOKUP_FROM_SLOT_OFFSET(float,mask,cf);

            UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

            double total = 0.0;
            int i, j;

            // modify non-masked weights
            double *inpj = input_activity+icols*rr1+cc1;
            for (i=rr1; i<rr2; ++i) {
                double *inpi = inpj;
                for (j=cc1; j<cc2; ++j) {
                    // The mask is floating point, so we have to
                    // use a robust comparison instead of testing
                    // against exactly 0.0.
                    if (*(mask++) >= MASK_THRESHOLD) {
                        *weights += load * *inpi * (unit_activity - unit_threshold);
                        if (*weights<0) { *weights = 0;}
                        total += fabs(*weights);
                    }
                    ++weights;
                    ++inpi;
                }
                inpj += icols;
            }
            // store the sum of the cf's weights
            LOOKUP_FROM_SLOT_OFFSET(double,_norm_total,cf);
            _norm_total[0]=total;
            LOOKUP_FROM_SLOT_OFFSET(int,_has_norm_total,cf);
            _has_norm_total[0]=1;
        }
    }
}



void trace_learning(double input_activity[], double traces[], int num_cfs,
                    int icols, PyObject* cfs, double single_connection_learning_rate,
                    PyObject* cf_type) {
    DECLARE_SLOT_OFFSET(weights,cf_type);
    DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);
    DECLARE_SLOT_OFFSET(mask,cf_type);
    DECLARE_SLOT_OFFSET(_norm_total,cf_type);
    DECLARE_SLOT_OFFSET(_has_norm_total,cf_type);

    int r;

    #pragma omp parallel for schedule(guided, 8)
    for (r=0; r<num_cfs; ++r) {
        double load = traces[r];
        if (load != 0) {
            load *= single_connection_learning_rate;
            PyObject *cf = PyList_GetItem(cfs,r);

            LOOKUP_FROM_SLOT_OFFSET(float,weights,cf);
            LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);
            LOOKUP_FROM_SLOT_OFFSET(float,mask,cf);

            UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

            double total = 0.0;
            int i, j;

            // modify non-masked weights
            double *inpj = input_activity+icols*rr1+cc1;
            for (i=rr1; i<rr2; ++i) {
                double *inpi = inpj;
                for (j=cc1; j<cc2; ++j) {
                    // The mask is floating point, so we have to
                    // use a robust comparison instead of testing
                    // against exactly 0.0.
                    if (*(mask++) >= MASK_THRESHOLD) {
                        *weights += load * *inpi;
                        total += fabs(*weights);
                    }
                    ++weights;
                    ++inpi;
                }
                inpj += icols;
            }
            // store the sum of the cf's weights
            LOOKUP_FROM_SLOT_OFFSET(double,_norm_total,cf);
            _norm_total[0]=total;
            LOOKUP_FROM_SLOT_OFFSET(int,_has_norm_total,cf);
            _has_norm_total[0]=1;
        }
    }
}


void divisive_normalize_l1(double sheet_mask[], double active_units_mask[],
                           PyObject* cfs, PyObject* cf_type, int num_cfs) {
    DECLARE_SLOT_OFFSET(weights,cf_type);
    DECLARE_SLOT_OFFSET(input_sheet_slice,cf_type);
    DECLARE_SLOT_OFFSET(_norm_total,cf_type);
    DECLARE_SLOT_OFFSET(_has_norm_total,cf_type);
    DECLARE_SLOT_OFFSET(mask,cf_type);

    int r;

    #pragma omp parallel for schedule(guided, 8)
    for (r=0; r<num_cfs; ++r) {
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
            int i;
            for (i=0; i<rc; ++i) {
                *(weights++) *= factor;
            }

            // Indicate that norm_total is stale
            _has_norm_total[0]=0;
        }
    }
}