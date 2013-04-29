 
************
Current work
************



This is the developers' to-do list. There are several sections, with
earlier ones being higher priority than later ones. Tasks within
each section are also ordered approximately by priority.

Most of our current tasks have been moved to GitHub's issue
trackers; those are our primary record of outstanding tasks, so
please check there first. In particular, *new tasks should be
submitted to GitHub rather than added to this list*.

Tasks to be addressed for the upcoming 1.0 release
 What the developers are working on most actively right now.

Things we hope to take care of eventually
 Tasks of lower priority; if you would like to see one of these tasks
 completed any time soon, please volunteer (even if a developer is
 already assigned)!

Ongoing work
 Long-term tasks that are underway, and tasks that the developers
 might currently be investigating: work with uncertain finishing
 times.

By each task, initials in parentheses typically indicate the main
person working on an item, but others may also be involved. Items
with no initials are not (yet) assigned to a specific developer (so
please feel free to volunteer!!!!). Dates indicate when the item was
first added to the list, or a change was made.

ALERTs in topo.base
-------------------

::

    Priorities:
    8: release 1.0
    3: release someday
    0: remove alert

    * (8) boundingregion.py cleanup

    * cf.py
    (8) learning rate moves to learning function rather than cfprojection (CEB)
    (8) where mask created (by cfprojection/cf)  (CEB)
    (8) learning rate a parameter of CFPLearningFn (CEB)
    (8) CFPOutputFn mask parameter could be dropped now a masked iterator 
        can be passed in (CEB)
    (8) JCALERT! We might want to change the default value of the
    ### input value to self.src.activity; but it fails, raising a
    ### type error. It probably has to be clarified why this is
    ### happening (CEB)
    (3) calculation of no. of units (internal)


    * functionfamily.py
    (8) TransferFn: rename norm_value (CEB)
    (8) LearningFn should have learning_rate param 
        (see same alert in cf.py) (CEB)

    * projection.py
    (8) other SheetMask + subclasses cleanup 

    * Slice
    (8) M[slice]-style syntax (first figuring out performance implications
    of attribute access) (CEB)
    (8) general cleanup (CEB)


    * PatternGenerator
    (8) needs to support plasticity of output functions (after fixing
    Pipeline's plasticity support)


    * Simulation
    (3) EPConnectionEvent always deepcopying data: does it need to?
    (8) SomeTimer (also #1432101)
    (8) the mess inside run(); how Forever etc is implemented 
    (3) PeriodicEventSequence
        ## JPHACKALERT: This should really be refactored into a
        ## PeriodicEvent class that periodically executes a single event,
        ## then the user can construct a periodic sequence using a
        ## combination of PeriodicEvent and EventSequence.  This would
        ## change the behavior if the sequence length is longer than the
        ## period, but I'm not sure how important that is, and it might
        ## actually be useful the other way.
    (8) gc alert in simulation.__new__ (CEB)

    * Parameters
    (3) script_repr: 
    # JABALERT: Only partially achieved so far -- objects of the same
    # type and parameter values are treated as different, so anything
    # for which instantiate == True is reported as being non-default.
    (8) ParamOverrides should check_params() (CEB)

Tasks to be addressed by release 1.0
------------------------------------

2007/10/26: Update tutorial
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add a section about plotting 'Orientation tuning fullfield' tuning
curves. CB: would the tutorial benefit from being split up a little
more? Maybe it's getting daunting?

ConnectionField tests
^^^^^^^^^^^^^^^^^^^^^

no guarantee that code in/related to connectionfield is valid at all
densities (tied to c++ comparisons task).

2008/08/15 (JB): Cleanup of examples, especially for afferent radii
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once Kateryna's project completes, should systematically examine the
example files (see above task) and eliminate as many as possible;
several should now be able to be replicated using her master file.
At the same time, should update most of the examples to use explicit
parameters for v1aff\_radius and lgnaff\_radius, so that the sizes
of the LGN and retina sheets can be calculated appropriately.
Currently many of them have a size that includes a term 0.25 as a
buffer, yet the relevant radius to be buffered against is 0.27083.
There is no difference in the resulting matrix sizes at the default
densities, but for high enough LGN densities we would expect that a
few CFs around the edge would be cut off slightly using the current
values.

Things we hope to take care of eventually
-----------------------------------------

(CB) cleanup test\_pattern\_present
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(or wherever I tried to add test for not-run simulation before
presenting patterns/saving generators)

gui: test fullfield x and y work
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

test that shows sim.time() can't be float
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

test for recent run() problems - to catch problems with other future
number types

2006/11/09 (JA): optimizations from c++
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Need to implement more of the optimizations from the C++ LISSOM
code.

2007/03/26: Support for optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Do we need our own simple timing functions to make it easier for
users to optimize their components (as opposed to the overall
Topographica framework, for which the current profile() commands are
appropriate)? A facility for reporting the approximate time spent in
methods of each EventProcessor? In any case, provide more guide for
the user for doing optimization, focusing on the components we
expect to be the bottlenecks. Add general advice for optimization to
the manual pages.

2007/03/26: developer page about efficient array computations.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Measurement of numpy.sum(X)/X.sum()/sum(X) performance. Difference
between simulation results on different platforms (for slow-tests in
Makefile).

some kind of global time\_fn manager?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

defaults to something like lambda:0; the gui could set to
topo.sim.time. Rather than having a default of topo.sim.time in
places that don't know about simulations. In parameterclasses?

2007/12/23: who's tracking the results of...
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  examples/joublin\_bc96.ty
-  examples/lissom\_whisker\_barrels.ty
-  examples/ohzawa\_science90.ty

And others...

2007/07/07: more tests
^^^^^^^^^^^^^^^^^^^^^^

We need a test with non-square input sheets, non-square LISSOM
sheets, etc., with both types of non-squareness...and we also need
to test whatever map measurement that we can (e.g. or maps). Could
also add coverage testing, e.g. using `figleaf`_ or `coverage.py`_.

2007/02/26: consider an alternative debugger
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

http://www.digitalpeers.com/pythondebugger/.

2005/01/01: components from external packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Could consider using or taking components from: SciPy,
ScientificPython, Chaco, Pyro (the robotics package), g, logger
(instead of our custom messaging functions).

2007/02/23: which version of libraries is numpy using?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    - numpy.__config__.show()
    - warn users if they're using a slow version?
    - http://www.scipy.org/Numpy_Example_List?highlight=%28example
      %29#head-c7a573f030ff7cbaea62baf219599b3976136bac
    >>>
    >>> import numpy
    >>> if id(dot) == id(numpy.core.multiarray.dot):
    # A way to know if you use fast blas/lapack or not.
    ...   print "Not using blas/lapack!"

alterdot() numpy.alterdot(...) alterdot() changes all dot functions
to use blas. (but note that dot() is, for some reason, not a dot
product.)

2006/04/20 (JB): Composite & Image test files.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Complete test file for Composite and Image. investigate failing test
in testimage.py (that uses sheet functions). Currently commented
out; may not be a problem.

2005/01/01: porting other simulations from c++ lissom
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Finish porting all categories of simulations from parts II and III
of the LISSOM book (i.e. orientation maps, ocular dominance maps,
direction maps, combined maps, face maps, and two-level maps) to
Topographica.

2007/06/07: plotgrouppanel's plots
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Maybe should be one canvas with bitmaps drawn on. Then we'd get
canvas methods (eg postscript()). But right-click code will need
updating. Should be easy to lay out plots on a canvas, just like the
grid() code that we have at the moment.

Run tkgui in its own thread?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

2006/02/21: read-only objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Might someday be interesting to have read-only objects, aiming at
copy-on-write semantics, but this seems quite difficult to achieve
in Python.

Ongoing work
------------

2006/04/10: optional external packages on platforms other than linux
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Optional packages (e.g. mlabwrap, pyaudio) on Windows and OS X.

2006/02/23 (all): Making more things be Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

And writing doc strings at the same time.

2006/02/23 (all): ensuring classes are declared abstract if they are abstract
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Plus making sure base and simple classes are imported into packages
(i.e. Sheet into topo/sheets/, Projection into topo/projections/,
Constant into topo/patterns/, and so on).

2006/02/21 (all): documentation, unit tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Improving both, plus eliminating ALERTs. Could use Sphinx instead of
epydoc for Reference Manual; apparently searchable.

2007/03/14: building scipy
^^^^^^^^^^^^^^^^^^^^^^^^^^

how to build scipy without requiring any of the external linear
algebra libraries, etc? Then scipy would at least build easily, and
users could install the optimized versions if they wished.
Investigate garnumpy.

2007/07/24 (JB): Matlab Toolbox for Dimensionality Reduction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider interfacing to this toolbox, which contains Matlab
implementations of twenty techniques for dimensionality reduction. A
number of these implementations were developed from scratch, whereas
other implementations are based on software that is already
available on the Web. http://www.cs.unimaas.nl/l.vandermaaten/dr CB:
or consider a python/numpy alternative? E.g.
http://mdp-toolkit.sourceforge.net/

2007/07/24 (JB): Digital Embryo Workshop
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider interfacing to this toolbox, which is handy for generating
novel 3D objects, e.g. to use as training stimuli (perhaps for
somatosensory simulations?).
http://www.psych.ndsu.nodak.edu/brady/downloads.html

.. _figleaf: http://darcs.idyll.org/~t/projects/figleaf/doc/
.. _coverage.py: http://nedbatchelder.com/code/modules/rees-coverage.html
