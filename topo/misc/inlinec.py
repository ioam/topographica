"""
Interface class for inline C/C++ functions.  Based on the SciPy Weave package.

Weave (from SciPy) allows programmers to implement Python methods or
functions using C code written as a string in the Python file.  This
is generally done to speed up code that would be slow if written
directly in Python.  Because not all users can be assumed to have a
working C/C++ compiler, it is crucial for such optimizations to be
optional.  This file provides an interface for processing the inline
C/C++ code in a way that can gracefully revert back to the
unoptimized version when Weave is not available.

The fallback is implemented by making use of the way Python allows
function names to be overwritten, as in these simple examples:

  def x(y = 5): return y
  def x2(y = 6): return y*y
  print 'x:', x(), 'x2:', x2()  # Result -- x: 5 x2: 36
  x = x2
  print 'x:', x(), 'x2:', x2()  # Result -- x: 36 x2: 36

In this file, inline() is overwritten to call inline_weave() if Weave
is available.  If Weave is not available, inline() will raise a
NotImplementedError exception.  For a program to be usable without
Weave, just test inlinec.optimized after defining each optimized
component, replacing it with a non-optimized equivalent if
inlinec.optimized is False.

For more information on weave, see:
http://old.scipy.org/documentation/weave/weaveusersguide.html

Some of the C functions also support OpenMP, which allows them to use
multiple threads automatically on multi-core machines to give better
performance.  To enable OpenMP support for those functions, set
openmp=True in the main namespace before importing this file, and
(optionally) set openmp_threads to the number of threads desired.  If
openmp_threads is not set, then a thread will be allocated for each
available core by default.

Note that in order to use OpenMP, the C functions are obliged to use the
thread-safe portions of the Python/Numpy C API. In general, the Python
C API cannot be assumed to be thread safe.  Calls to PyObject_SetAttrString
are a common hazard which can often be avoided using LOOKUP_FROM_SLOT_OFFSET.
This makes use of Python's __slots__ mechanism with the added benefit of
bypassing the GIL.
"""

import collections
import os
from copy import copy

# If import_weave is not defined, or is set to True, will attempt to
# import weave.  Set import_weave to False if you want to avoid weave
# altogether, e.g. if your installation is broken.
import __main__
import_weave = __main__.__dict__.get('import_weave',True)

# Dictionary of strings used to allow optional substituions
# (e.g. pragmas) into inline C code.
#
# CB: default value is empty string for convenience of not
# having to do e.g.
# if openmp:
#     c_decorators['xyz']='abc'
# else:
#     c_decorators['xyz']=''
c_decorators = collections.defaultdict(lambda:'')

# Setting to true will cause OpenMP to be used while compiling some C
# code (search for cfs_loop_pragma to see which routines use
# OpenMP). Good multi-threaded performance requires a machine with
# separate memory subsystems for each core, such as a Xeon. See Marco
# Elver's report at http://homepages.inf.ed.ac.uk/s0787712/stuff/melver_project-report.pdf.
openmp_threads = __main__.__dict__.get('openmp_threads',False)

# Variable that will be used to report whether weave was successfully
# imported (below).
weave_imported = False

# Variable that will be used to report whether simple compilation test
# was successful.
compiled = False

def inline(*params,**nparams): raise NotImplementedError



##########
# Windows: hack to allow weave to work when a user name contains a
# space (see
# http://thread.gmane.org/gmane.comp.python.scientific.devel/14275)
if import_weave:
    import sys
    if sys.platform.startswith("win"):
        try:
            # catch the initial use of USERNAME by weave
            original_user = os.environ.get("USERNAME")
            os.environ["USERNAME"]=original_user.replace(" ","")
            # now dynamically patch weave and restore USERNAME
            import scipy.weave.catalog
            iam = scipy.weave.catalog.whoami().replace(" ","")
            scipy.weave.catalog.whoami = lambda: iam
            os.environ["USERNAME"]=original_user
        except:
            pass
##########

try:
    if import_weave:
        # We supply weave separately with the source distribution, but
        # e.g. the ubuntu package uses scipy.
        try:
            import weave
        except ImportError:
            from scipy import weave  # pyflakes:ignore (try/except import)

        weave_imported = True

    # Default parameters to add to the inline_weave() call.
    inline_named_params = {
        'extra_compile_args':['-O2','-Wno-unused-variable -fomit-frame-pointer','-funroll-loops'],
        'extra_link_args':['-lstdc++'],
        'compiler':'gcc',
        'verbose':0}

    if openmp_threads != 1:
        c_decorators['cfs_loop_pragma']="#pragma omp parallel for schedule(guided, 8)"
        inline_named_params['extra_compile_args'].append('-fopenmp')
        inline_named_params['extra_link_args'].append('-fopenmp')


    def inline_weave(*params,**nparams):
        named_params = copy(inline_named_params) # Make copy of defaults.
        named_params.update(nparams)             # Add newly passed named parameters.
        weave.inline(*params,**named_params)

    # Overwrites stub definition with full Weave definition
    inline = inline_weave # pyflakes:ignore (try/except import)

except ImportError:
    # CEBALERT: where does 'caution' fit in our warnings system? (Also
    # used in other places in this file.)
    print 'Caution: Unable to import Weave.  Will use non-optimized versions of most components.'


if weave_imported:
    import random
    try:
        # to force recompilation each time
        inline('double x=%s;'%random.random())
        compiled = True
    except Exception, e:
        print "Caution: Unable to use Weave to compile: \"%s\". Will use non-optimized versions of most components."%str(e)

# Flag available for all to use to test whether to use the inline
# versions or not.
optimized = weave_imported and compiled

warn_for_each_unoptimized_component = False


# JABALERT: I can't see any reason why this function accepts names rather
# than the more pythonic option of accepting objects, from which names
# can be extracted if necessary.
def provide_unoptimized_equivalent(optimized_name, unoptimized_name, local_dict):
    """
    If not using optimization, replace the optimized component with its unoptimized equivalent.

    The objects named by optimized_name and unoptimized_name should be
    plug-compatible.  The local_dict argument should be given the
    contents of locals(), so that this function can replace the
    optimized version with the unoptimized one in the namespace from
    which it has been called.

    As an example, calling this function as::

      provide_unoptimized_equivalent("sort_opt","sort",locals())

    is equivalent to putting the following code directly into the
    calling location::

      if not optimized:
        sort_opt = sort
        print 'module: Inline-optimized components not available; using sort instead of sort_opt.'
    """
    if not optimized:
        local_dict[optimized_name] = local_dict[unoptimized_name]
        if warn_for_each_unoptimized_component:
            print '%s: Inline-optimized components not available; using %s instead of %s.' \
                  % (local_dict['__name__'], optimized_name, unoptimized_name)

if not optimized and not warn_for_each_unoptimized_component:
    print "Note: Inline-optimized components are currently disabled; see topo.misc.inlinec"


# Definitions useful for working with optimized Python code;
# prepend to the code for an inlinec call if you want to use them.
c_header = """
/* Declaration for interfacing to numpy floats */
typedef double npfloat;

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
  for (int i=rr1; i<rr2; ++i) { \
    for (int j=cc1; j<cc2; ++j) { \
      if (*(mask++) >= MASK_THRESHOLD) { \
        total += fabs(*weights_init); \
      } \
      ++weights_init; \
    } \
  } \
  _norm_total[0] = total
"""

# Simple test
if __name__ == '__main__':
    inline('printf("Hello World!!\\n");')


