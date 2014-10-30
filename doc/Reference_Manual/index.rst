****************
Reference Manual
****************

This reference manual contains detailed documentation of each
component making up Topographica, assuming that the user is already
familiar with basic Topographica usage. (See the `User Manual`_ and
`Tutorials`_ for such an introduction.) The reference manual is
generated directly from documentation and declarations in the source
code, and is often much more verbose than necessary, because many
little-used yet often-duplicated methods are listed for each class.
Still, the reference for a given component does provide a
comprehensive listing of all attributes and methods, inherited or
otherwise, which is difficult to obtain from the source code
directly and is not covered by the User Manual or Tutorials.

Topographica's components can be categorized into subprojects
(available separately), core packages (required for Topographica),
library packages (useful families of components not required for
Topographica itself), and other `external dependencies`_ (documented
separately). Everything but the external dependencies is documented
at the `main reference manual page`_, but the different
categories of objects are broken down here in a way that's easier to
follow.

Subprojects
-----------

`param`_
 Support for objects with user-controllable attributes
`paramtk`_
 Optional Tk GUI support for param
`numbergen`_
 Support for generating streams of scalars, e.g. random
 distributions; currently available through the imagen module
 (below)
`holoviews`_
 Support for composable and declarative data structures to hold
 and visualize data and metadata. 
`imagen`_
 Support for generating 1D, and 2D patterns, and for defining
 mappings between continuous 2D space and finite matrices
`featuremapper`_
 Support for the coordinated presentation of input patterns, collating
 and analyzing the responses to measure feature maps, tuning curves,
 receptive fields, PSTHs, etc.

The param, paramtk, numbergen, holoviews, imagen and featuremapper
modules are each developed and maintained separately from
Topographica, because they are general-purpose packages that can be
useful for a wide variety of Python programs. However, they are
documented together with Topographica because they were developed
alongside Topographica and are used extensively within Topographica.

Core Topographica packages
--------------------------

The Topographica simulator itself is implemented in a set of
interrelated packages:

`base`_
 Core Topographica-specific functions and classes
`plotting`_
 Visualization functions and classes
`analysis`_
 Analysis functions and classes (besides plotting)
`misc`_
 Miscellaneous independent utility functions and classes
`tkgui`_
 Tk-based graphical user interface (GUI)

The **base** directory contains the most fundamental Topographica
classes, implementing basic functionality such as Sheets (arrays of
units), Projections (large groups of connections between Sheets),
ConnectionFields (spatially localized groups of connections to one
unit), and the event-driven Simulation. It relies heavily on the
generic support for Parameters (user-controllable attributes) from
the **param** subproject. Together the files in ``base`` are
independent of the rest of the files in ``topo/``, and act as the
primary programming interface on which Topographica is built. The
rest of the directories add components used in specific models, or
add graphical interfaces.

Library
-------

Beyond the basic simulator implemented in the core packages,
Topographica provides an extensive and extensible library of classes
that can be used to implement models of various neural systems:

`sheet`_
 Sheet classes: 2D arrays of processing units
`projection`_
 Projection classes: connections between Sheets
`ep`_
 EventProcessor classes: other simulation objects
`transferfn`_
 Output functions: apply to matrices to do e.g. normalization or
 squashing
`responsefn`_
 Calculate the response of a unit or a Projection
`learningfn`_
 Adjust weights for a unit or a Projection
`coordmapper`_
 Determine mapping from one Projection to another
`command`_
 High-level user commands

All of the library components are optional, in the sense that they
can be deleted or ignored or replaced with custom versions without
affecting the code in any of the core packages. (Of course, any
specific model that depends on the component would not be able to
function without it!)

Each of the library directories can be extended with new classes by
simply defining them in your own files, and then making sure that
your file has been run or imported before you start the GUI or use
the new class in your .ty file. I.e., user-defined classes of these
types have the same status as those shipped with Topographica --
just make sure they have been defined, and Topographica will find
them and use them just like its own classes.

Many of the components come in multiple varieties, to be used at
different levels in a model. For instance, there are learning
functions that operate on a single unit (type LearningFn), and ones
that operate on an entire CFProjection (type CFPLearningFn). The
lower level components can be used by providing them to a "Plugin"
version of the higher level component, which will apply the lower
level version to each unit. For instance, a LearningFn can be used
with a CFPLearningFn of type CFPLF\_Plugin, and will be applied the
same to each unit individually.

Some components also come with an optimized version, usually written
in C for speed. The fastest, but least flexible, components will be
high-level components written in C, such as CFPLF\_Hebbian\_opt.

Apart from the Topographica-specific modules described above,
Topographica also uses many `external libraries`_, each documented
separately.

.. _User Manual: ../User_Manual/index.html
.. _Tutorials: ../Tutorials/index.html
.. _external dependencies: ../Downloads/dependencies.html
.. _main reference manual page: topo.html
.. _param: http://ioam.github.io/param/Reference_Manual/param.html
.. _paramtk: http://ioam.github.io/param/Reference_Manual/paramtk.html
.. _holoviews: http://ioam.github.io/holoviews/Reference_Manual/holoviews.html
.. _imagen: http://ioam.github.io/imagen/Reference_Manual/imagen.html
.. _numbergen: http://ioam.github.io/imagen/Reference_Manual/numbergen.html
.. _featuremapper: http://ioam.github.io/featuremapper/Reference_Manual/featuremapper.html
.. _base: topo.base.html
.. _plotting: topo.plotting.html
.. _analysis: topo.analysis.html
.. _misc: topo.misc.html
.. _tkgui: topo.tkgui.html
.. _sheet: topo.sheet.html
.. _projection: topo.projection.html
.. _ep: topo.ep.html
.. _transferfn: topo.transferfn.html
.. _responsefn: topo.responsefn.html
.. _learningfn: topo.learningfn.html
.. _coordmapper: topo.coordmapper.html
.. _command: topo.command.html
.. _external libraries: ../Downloads/dependencies.html
