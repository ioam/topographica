************************
Performance optimization
************************

According to C.A.R. Hoare, "Premature optimization is the root of
all evil". Although the performance of Topographica is critically
important, the way to achieve high performance is by spending *all*
of our optimization efforts on the very small portion of the code
that accounts for nearly all of the run time, i.e., the bottlenecks.
The overall architecture of Topographica is designed explicitly to
localize those bottlenecks into specific functions and objects that
can then be heavily optimized without affecting any of the rest of
the code. Only in such small, local regions, behind well-defined
modules with clear semantics, is it possible to optimize effectively
in a way that can be maintained in the long run. If it is precisely
clear what the module is supposed to do, then the implementation can
be polished to achieve that, while reasoning only about the behavior
of that one specific module.

Conversely, finding that good performance requires adding special
hacks in the largest-scale, general-purpose parts of the overall
Topographica architecture means that the architecture is flawed and
needs to be re-thought. For instance, please do not add any special
checks scattered through the code testing for specific
PatternGenerator or Sheet objects, substituting a quicker version of
some operation but falling back to the general case for others. Such
code is impossible to understand and maintain, because changes to
the specific object implementations will not have any effect.
Instead, we can optimize the individual PatternGenerator or Sheet
object heavily. If some special hack needs to be done at a high
level, e.g. at the base Sheet class level, we can add a method there
that then gets overridden in the subclass with the special purpose
code. That way all optimization will be local (and thus
maintainable). If it's not clear how to optimize something cleanly,
first do it uncleanly to see if it will have any effect, but don't
check it in to Git. If it looks like the optimization is worthwhile,
brainstorm with other team members to figure out a way to do it
cleanly and check in the clean version instead.

This document considers runtime performance primarily; optimizing
total memory is considered separately under `Memory usage`_. On the
other hand, the *patterns* of access to memory are crucially
important for performance in large simulations. For a good overview
of how to optimize memory usage patterns, see `Ulrich Drepper's
article`_. If you are ambitious, even the most optimized components
in Topographica could be further improved using these techniques,
possibly substantially.

Optimizing Python code
----------------------

Although dramatic speedups usually require big changes as described
below, sometimes all you need is minor tweaks to Python code to get
it to have reasonable performance. Usually this involves avoiding
unnecessary attribute lookup, as described in various collections of
`Python performance tips`_.

What is usually more important to ensure is that anything that can
use the array-based primitives provided by `numpy`_ does so, because
these generally have underlying C implementations that are quite
fast. Using numpy operations should be the first approach when
optimizing any component, and indeed when writing the component for
the first time (because the numpy primitives are much easier to use
and maintain than e.g. explicitly writing ``for`` loops).

Providing optimized versions of Topographica objects
----------------------------------------------------

However, there are certain cases where the performance of numpy is
not sufficient, or where numpy is unsuitable (for example, some
numpy operations do not act in-place on arrays). Other components
may be able to be implemented much more quickly if certain
assumptions are made about the nature of their arguments, or the
types of computations that can be performed.

In these cases, it is worthwhile to have a reference version of the
object that is simple to understand and does not make any special
assumptions. Then, an optimized version can be offered as an
alternative. The convention we use is to add the suffix ``_optN`` to
the optimized version, where ``N`` is a number that allows to
distinguish between different optimized versions. This is helpful
both for understanding and for ensuring correctness.

For example, consider ``CFPRF_DotProduct``, from
``topo.responsefn.projfn``. If users wish to use a version optimized
by having been written in C, they can instead import
``CFPRF_DotProduct_opt`` from ``topo.responsefn.optimized``. We use
``CFPRF_DotProduct_opt`` as standard in our code because it's much
faster than --- but otherwise identical to --- the unoptimized
version. However, because ``CFPRF_DotProduct_opt`` relies on a more
complex setup (having the weave module installed, as well as a
correctly configured C++ compiler), we cannot assume all users will
have access to it. It is also extremely difficult to read and
understand. Therefore, we provide an automatic fall-back to the
unoptimized version (see ``topo/responsefn/optimized.py`` for an
example of how to do this).

The non-optimized version also acts as a simple specification of
exactly what the optimized version is supposed to do, apart from any
optimizations. The optimized versions are often nearly unreadable,
so having the simple version available is very helpful for
understanding and debugging. The expectation is that the simple
(slow) versions will rarely change, but the optimized ones will get
faster and faster over time, while preserving the same user-visible
behavior.

Finding bottlenecks
-------------------

As discussed above, we wish to spend our time optimizing parts of
the code that account for most of the run time. ``topo.misc.util``
contains the ``profile()`` function, providing a simple way to do
this.

In order to see how basic optimization could be applied, we now show
how optimizing one component can lead to a dramatic improvement. We
will use ``examples/lissom_oo_or.ty`` without its optimized response
function, by replacing
``projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()``
with
``projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct()``.

Now we can run topographica as follows, using the ``profile()``
function to give us information about the performance:

::

  $ ./topographica examples/lissom_oo_or.ty -c "from topo.misc.util import profile; \
  profile('topo.sim.run(99)',n=20)"  

         28148082 function calls (28145508 primitive calls) in 81.806 CPU seconds

     Ordered by: cumulative time, internal time
     List reduced from 245 to 20 due to restriction <20>

     ncalls  tottime  percall  cumtime  percall filename:lineno(function)
          1    0.041    0.041   81.806   81.806 topo/base/simulation.py:1121(run)
       2178    0.006    0.000   79.951    0.037 topo/base/simulation.py:437(__call__)
       2178    0.021    0.000   79.925    0.037 topo/base/projection.py:399(input_event)
       2178    0.003    0.000   79.879    0.037 topo/base/projection.py:527(present_input)
       2178    0.052    0.000   79.875    0.037 topo/base/cf.py:696(activate)
       1980    0.013    0.000   79.816    0.040 topo/sheet/lissom.py:95(input_event)
       1980   19.207    0.010   79.640    0.040 topo/base/cf.py:348(__call__)
    4561920    8.435    0.000   34.585    0.000 topo/base/functionfamily.py:125(__call__)
    4561920   19.912    0.000   19.912    0.000 topo/base/sheetcoords.py:387(submatrix)
    9124038   13.639    0.000   13.639    0.000 {method 'ravel' of 'numpy.ndarray' objects}
    4561920   12.512    0.000   12.512    0.000 {numpy.core._dotblas.dot}
    4563900    5.848    0.000    5.932    0.000 topo/base/cf.py:861(__call__)
       1188    0.010    0.000    1.133    0.001 topo/sheet/lissom.py:113(process_current_time)
       1094    0.005    0.000    0.866    0.001 topo/misc/inlinec.py:72(inline_weave)
       1094    0.017    0.000    0.855    0.001 lib/python2.6/site-packages/weave/inline_tools.py:130(inline)
       1094    0.658    0.001    0.831    0.001 {apply}
         99    0.001    0.000    0.684    0.007 topo/sheet/basic.py:284(learn)
        100    0.002    0.000    0.546    0.005 topo/sheet/basic.py:263(_normalize_weights)
         99    0.000    0.000    0.469    0.005 topo/base/simulation.py:511(__call__)
         99    0.002    0.000    0.469    0.005 topo/sheet/basic.py:140(generate)

The ``n=20`` argument restricts the list to the top 20 functions,
ordered by cumulative time. For more information about the types of
ordering available, ``help(profile)`` provides a link to Python's
documentation.

From ``profile()``'s output above, we see (as expected) that all the
time is spent in ``Simulation``'s ``run()`` method. We must proceed
down the list until we find a less granular function --- one that
does not call many others, but instead performs some atomic task.
The first such function is ``cf.py:352(__call__)`` (``cf.py``, line
352), ``CFPRF_Plugin``'s ``__call__()`` method:

::

    class CFPRF_Plugin(CFPResponseFn):
        """
        Generic large-scale response function based on a simple single-CF function.

        Applies the single_cf_fn to each CF in turn.  For the default
        single_cf_fn of DotProduct(), does a basic dot product of each CF with the
        corresponding slice of the input array.  This function is likely
        to be slow to run, but it is easy to extend with any arbitrary
        single-CF response function.

        The single_cf_fn must be a function f(X,W) that takes two
        identically shaped matrices X (the input) and W (the
        ConnectionField weights) and computes a scalar activation value
        based on those weights.
        """
        single_cf_fn = param.ClassSelector(ResponseFn,default=DotProduct(),
            doc="Accepts a ResponseFn that will be applied to each CF individually.")
            
        def __call__(self, iterator, input_activity, activity, strength):
            single_cf_fn = self.single_cf_fn
            for cf,r,c in iterator():
                X = cf.input_sheet_slice.submatrix(input_activity)
                activity[r,c] = single_cf_fn(X,cf.weights)
            activity *= strength

About 97% of the total run time is spent in this method, so if we
were able to optimize it, this would lead to good optimization of
the simulation in total.

How do we begin to optimize this method? In the first section of
profile()'s output, we have more fine-grained information about the
occupation of the CPU while executing this method:

::

  Function                       called...
                                      ncalls  tottime  cumtime
  ...
  topo/base/cf.py:348(__call__)  ->    1980    0.003    0.004  param/parameterized.py:339(__get__)
                                    4563900    5.848    5.932  topo/base/cf.py:861(__call__)
                                    4561920    8.435   34.585  topo/base/functionfamily.py:125(__call__)
                                    4561920   19.912   19.912  topo/base/sheetcoords.py:387(submatrix)

Over 40% of the time is spent running
``functionfamily.py:151(__call__)``, ``CFPRF_Plugin``'s default
``single_cf_fn``:

::

    class DotProduct(ResponseFn):
        """
        Return the sum of the element-by-element product of two 2D
        arrays.  
        """
        def __call__(self,m1,m2):
            return numpy.dot(m1.ravel(),m2.ravel())

Optimizing this dot product is evidently important, but it is not
the only significant component. About 25% of the time is spent in
the call to submatrix(), which is simply returning a section of the
input activity array. Following this, the next most significant
component is unlisted: about 20% of the time in the CFPRF's
\_\_call\_\_ is spent not calling other functions, i.e. inside this
function itself.

We could simply replace the dot product with an optimized version,
but that would still leave other parts of this function as the
speed-limiting factors. Line-by-line profiling could indicate
exactly where the problems are, but a component such as this is a
good candidate for replacement with an optimized version; we will
describe this in the following section. Line-by-line profiling is
described in a later section.

Considering optimizations with C++ (weave)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Topographica makes it reasonably easy to re-write functions in C++
and offer them as optimized alternatives. We have done this for the
CFPResponseFn described in the previous section, resulting in this
code:

::

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

                npfloat *tact = temp_act;

                for (int r=0; r < num_cfs; ++r) {
                    if((*mask++) == 0.0)
                        *tact = 0;
                    else {
                        PyObject *cf = PyList_GetItem(cfs,r);

                        CONTIGUOUS_ARRAY_FROM_SLOT_OFFSET(float,weights,cf)
                        LOOKUP_FROM_SLOT_OFFSET(int,input_sheet_slice,cf);

                        UNPACK_FOUR_TUPLE(int,rr1,rr2,cc1,cc2,input_sheet_slice);

                        double tot = 0.0;
                        npfloat *xj = X+icols*rr1+cc1;

                        // computes the dot product
                        for (int i=rr1; i < rr2; ++i) {
                            npfloat *xi = xj;
                            float *wi = weights;     
                            for (int j=cc1; j < cc2; ++j) {
                                tot += *wi * *xi;
                                ++wi;
                                ++xi;
                            }
                            xj += icols;
                            weights += cc2-cc1;
                        }  
                        *tact = tot*strength;

                        DECREF_CONTIGUOUS_ARRAY(weights);
                    }
                    ++tact;    
                }
            """
            inline(code, ['mask','X', 'strength', 'icols', 'temp_act','cfs','num_cfs','cf_type'], 
                   local_dict=locals(), headers=[''])

Replacing the CFP function with one written entirely in C++ (by
reverting the line previously edited), we get the following profile:

::

  ./topographica examples/lissom_oo_or.ty -c "from topo.misc.util import profile; profile('topo.sim.run(99)',n=20)"  
     
           778542 function calls (775968 primitive calls) in 4.691 CPU seconds

     Ordered by: cumulative time, internal time
     List reduced from 239 to 20 due to restriction <20>

     ncalls  tottime  percall  cumtime  percall filename:lineno(function)
          1    0.039    0.039    4.691    4.691 topo/base/simulation.py:1121(run)
       3074    0.018    0.000    3.359    0.001 topo/misc/inlinec.py:72(inline_weave)
       3074    0.045    0.000    3.326    0.001 lib/python2.6/site-packages/weave/inline_tools.py:130(inline)
       3074    3.101    0.001    3.273    0.001 {apply}
       2178    0.006    0.000    2.838    0.001 topo/base/simulation.py:437(__call__)
       2178    0.019    0.000    2.814    0.001 topo/base/projection.py:399(input_event)
       2178    0.003    0.000    2.770    0.001 topo/base/projection.py:527(present_input)
       2178    0.055    0.000    2.767    0.001 topo/base/cf.py:696(activate)
       1980    0.012    0.000    2.703    0.001 topo/sheet/lissom.py:95(input_event)
       2178    0.021    0.000    2.642    0.001 topo/responsefn/optimized.py:35(__call__)
       1188    0.010    0.000    1.135    0.001 topo/sheet/lissom.py:113(process_current_time)
         99    0.001    0.000    0.680    0.007 topo/sheet/basic.py:284(learn)
        100    0.003    0.000    0.545    0.005 topo/sheet/basic.py:263(_normalize_weights)
         99    0.000    0.000    0.469    0.005 topo/base/simulation.py:511(__call__)
         99    0.002    0.000    0.468    0.005 topo/sheet/basic.py:140(generate)
     297/99    0.016    0.000    0.451    0.005 topo/base/patterngenerator.py:116(__call__)
       1089    0.112    0.000    0.446    0.000 topo/base/projection.py:462(activate)
         99    0.013    0.000    0.403    0.004 topo/pattern/basic.py:589(function)
        400    0.002    0.000    0.327    0.001 topo/base/cf.py:719(apply_learn_output_fns)
        400    0.003    0.000    0.318    0.001 topo/transferfn/optimized.py:33(__call__)

The simulation is now almost 20 times faster than the Numpy version.

The C++ code adds extra work: for maintenance, for deployment on
different platforms, and for user understanding --- so it has to be
justified, meaning it should provide large speedups. In this case,
the performance improvement justifies the additional costs (which
have been substantial in terms of maintenance and platform support
--- although platform support cost is diluted by all such C++
functions, and any added in the future).

While making this kind of investigation, you must check that
simulations run with different versions of a function are producing
the same results. In particular, when working with optimized C++
functions, it is possible for one version to appear much faster than
another when in fact the computations being performed are not
equivalent.

A final consideration is to ensure that the profile run times are
long enough to obtain reliable results. For shorter runs, it would
be necessary to repeat them to find a reasonable estimate of the
minimum time.

.. _line-by-line:

Line-by-line profiling
~~~~~~~~~~~~~~~~~~~~~~

The profile function described above (which uses Python's inbuilt
profiling) only reports time spent inside functions, but gives no
information about how that time is spent. There is also an optional
line-by-line profiling package available that gives information
about how the time is spent inside one or two specific functions.
So, for instance, if you have a function that does various
operations on arrays, you can now see how long all those operations
take relative to each other. That might allow you to identify a
bottleneck in the function easily. (Note that before doing a
line-by-line profile of a function, you should previously have
identified that function as a bottleneck using the profiling
function described earlier. Otherwise, optimizing the function will
result in little performance gain overall.)

The line-by-line profiling package is not yet built by default. If
you want to build it, execute the following from your Topographica
directory:

::

    $ make -C external line_profiler

Then, the easiest way to use the new package is to:

#. put the following two lines into ``~/ipy_user_conf.py`` (in the
   ``main()`` function):

   ::

       import line_profiler
       ip.expose_magic('lprun',line_profiler.magic_lprun)

#. use ``%lprun`` from the Topographica prompt

Examples
^^^^^^^^

To profile topo.base.cf.ConnectionField's
\_create\_input\_sheet\_slice() method while starting the lissom.ty
script:

::

    $ ./topographica
    topo_t000000.00_c1>>> from topo.base.cf import ConnectionField
    topo_t000000.00_c2>>> %lprun -f ConnectionField._create_input_sheet_slice execfile("examples/lissom.ty")

To profile calling of topo.transferfn.HomeoStaticMaxEnt while
Topographica is running:

::

    $ ./topographica -i contrib/lesi.ty
    topo_t000000.00_c1>>> from topo.transferfn import HomeostaticMaxEnt
    topo_t000000.00_c2>>> %lprun -f HomeostaticMaxEnt.__call__ topo.sim.run(30)

The output you get is something like this:

::

  Timer unit: 1e-06 s

  File: /disk/data1/workspace/v1cball/topographica/topo/transferfn/basic.py
  Function: __call__ at line 749
  Total time: 0.955004 s

  Line Hits   Time  PerHit %Time Line Contents
  ================================================
  749                           def __call__(self,x):      
  750   450  13003   28.9   1.4    if self.first_call:
  751     1      9    9.0   0.0         self.first_call = False
  752     1     20   20.0   0.0         if self.a_init==None:
  753     1    817  817.0   0.1             self.a = self.random_generator.uniform(low=10, high=20,size=x.shape)
  754                                   else:
  755                                       self.a = ones(x.shape, x.dtype.char) * self.a_init
  756     1     27   27.0   0.0         if self.b_init==None:
  757     1    411  411.0   0.0             self.b = self.random_generator.uniform(low=-8.0, high=-4.0,size=x.shape)
  758                                   else:
  759                                       self.b = ones(x.shape, x.dtype.char) * self.b_init
  760     1    128  128.0   0.0        self.y_avg = zeros(x.shape, x.dtype.char) 
  761                            
  762                              # Apply sigmoid function to x, resulting in what Triesch calls y
  763   450  88485  196.6   9.3     x_orig = copy.copy(x)
  764                              
  765   450  24277   53.9   2.5     x *= 0.0
  766   450 662809 1472.9  69.4     x += 1.0 / (1.0 + exp(-(self.a*x_orig + self.b)))
  767                                      
  768                            
  769   450   5979   13.3   0.6    self.n_step += 1
  770   450  34237   76.1   3.6    if self.n_step == self.step:
  771    30    253    8.4   0.0        self.n_step = 0
  772    30    654   21.8   0.1        if self.plastic:                
  773    30  19448  648.3   2.0            self.y_avg = (1.0-self.smoothing)*x + self.smoothing*self.y_avg 
  774                                      
  775                                      # Update a and b
  776    30  65652 2188.4   6.9            self.a += self.eta * (1.0/self.a + x_orig - (2.0 + 1.0/self.mu)*...
  777    30  38795 1293.2   4.1            self.b += self.eta * (1.0 - (2.0 + 1.0/self.mu)*x + x*x/self.mu)


From this output, you can see that 69.4% of the time is spent in
line 766, which is thus the best place to start optimizing (e.g. by
using a lookup table for the sigmoid function, in this case).

.. _Memory usage: memuse.html
.. _Ulrich Drepper's article: http://lwn.net/Articles/250967/
.. _Python performance tips: http://wiki.python.org/moin/PythonSpeed/PerformanceTips
.. _numpy: http://numpy.scipy.org/
