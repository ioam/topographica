<P>Topographica is under very active development, and there are many
features we have not yet been able to add.  This page describes some
of the major ones; the rest are listead in SourceForge's
<a href="http://sourceforge.net/tracker/?group_id=53602">trackers</a>.

<!--  
<H2>Most urgent (Summer 2010):</H2>
<DL COMPACT>
<P><DT>Stable APIs</DT><DD>
The Topographica API (determined by the classes in base/) is gradually
becoming more stable, and by the time of the 1.0 release it should be
possible to build add-in components and model scripts and expect them
to be usable in future versions (or to have a conversion program
available for them).
</DL>
-->

<DL COMPACT>

<!--  
<P><DT>Archival state saving</DT><DD>

Model state saving is currently implemented using Python "pickling"
(persistent storage).  As the Topographica classes change, these files
quickly become out of date, and often cannot be loaded into more recent
versions.  By the 1.0 release we plan to provide an upgrade path, so
that old saved files can be used with new versions.  To make this
simpler, we are working on an alternative implementation of state
saving using XML, which is designed to be an archival, readable
format.  In the meantime, users should be aware that saved snapshot
files will not necessarily be readable by future versions of
Topographica, and should be considered temporary.
-->  
<!-- Also consider HDF5 or possibly netCDF4 for binary files, -->
<!-- e.g. through PyTables, http://www.pytables.org/docs/manual/ch04.html#id2553542 -->
  
<!-- From: fwh@inf.ed.ac.uk ; Oct  5 08:41:59 2005 +0100:

  Consider http://www.neurogems.org/nmlparser/index.html ; see
  message in mail/research/Topographica from the above date.

  Also: binary file formats for XML:

  XOP 
  http://www.w3.org/TR/2005/REC-xop10-20050125/
  
  w3 Binary XML working group
  http://www.tarari.com/PDF/BinaryXML/
  Existing binary XML formats include: ASN.1, BiM, BXML, CMF-B, esXML,
  Efficient XML, FastInfoSet, FastSchema, XBIS, XBVM, Xebu, XEUS and
  XFSB.
  
  DFDL
  https://forge.gridforum.org/projects/dfdl-wg/
  
  BinX
  http://www.edikt.org/binx/
-->

							 
<P><DT>Parallelization</DT><DD>
Due to their weakly interconnected graph structure, Topographica
models lend themselves naturally to coarse-grained parallelization.
Each event processor (e.g. a Sheet) can run on a different physical
processor, exchanging information with other event processors using
either shared memory or message passing protocols such as MPI.
Implementing this type of parallelization is not likely to require
significant changes to the simulator.  We are also working on a
GPU-based implementation, to use the processors available on modern
graphics cards.
<!-- 
  Should be able to do this without significant
  changes to the code, by adding a parallel Simulator class and proxies
  for the EPs and Connections. E.g. for shared memory threads, need
  two new classes ThreadedSimulator and EPThreadProxy:

  - Each time an EP is added to  the simulator it's wrapped in an
    EPThreadProxy that intercepts all calls between the Simulator
    and the EP (i.e. the EP's .sim attribute points to the proxy,
    instead of the simulator) (jprovost)

  Should also be able to do it using RPC or MPI.

  May also be able to distribute Projections, not just Sheets,
  automatically. 
-->

<P>Fine-grained parallelism is also possible, distributing computation
for different units or subregions of a single Sheet, or different
parts of a Projection across different
processors.  This has been implemented on a prototype version for a
shared-memory Cray MPP machine, and may be brought into the main
release if it can be made more general.  Such fine-grained parallelism
will be restricted to specific Sheet and/or Projection types, because
it requires access to the inner workings of the Sheet.


  <!-- Should consider sparse layers with patchy distribution of units -->
<!--
<P><DT>Bitmap plotting enhancements</DT><DD>

The current basic support for two-dimensional bitmap plotting will
eventually need to be expanded to allow the user to control plot
brightness scaling, allow custom colormaps, and add an "overload" or "cropped"
indicator to show if some values are too large to be displayed in the
selected range.
-->							 

<P><DT>Automatic line-based 2D plotting</DT><DD>
There are currently 1D (line), 2D (contour or vector field),
and 3D (wireframe mesh) plots available based on
<A HREF="http://matplotlib.sourceforge.net/">MatPlotLib</A> for any
program object selected by the user.  We will also eventually be
making the general-purpose template-based plotting use the 2D plots,
which will make it simpler to do
<A HREF="http://matplotlib.sourceforge.net/screenshots/pcolor_demo_large.png">contour</A>
plots, as well as matrix plots showing axis ticks and labels.
<!--
  We also plan to use MatPlotLib 2D plots to allow any SheetView(s) to be
used as a contour or vector field overlay on top of a bitmap, e.g. for joint
preference maps (such as direction arrows on top of an orientation
bitmap plot); currently some of these are implemented but they could
be done more generally. -->
<!-- Plan: Templates accept a Contours parameter, which can be a list
of (sheetview, threshold) pairs, which will be drawn in order. -->

<!--
<P>Other minor changes planned include adding outlining of
ConnectionField extents, plotting histograms for each bitmap,
and separate default colors for onscreen and publication plots.
-->							 
<!-- plus user-defined arbitrary colormaps ("KRYW", "BbKrR", etc.), 
including allowing a threshold so that a colormap plot can be
shown on top of a monochrome background plot, e.g. an activity blob on
top of an ocular dominance or other grayscale map. -->
<P><DT>Spiking support</DT><DD>
Topographica primarily supports firing-rate (scalar) units, but
spiking models are currently under development, and preliminary
versions are included already.  We will be developing interfaces
between spiking and non-spiking Sheets and analysis tools for spiking
neurons.  We primarily expect to support integrate-and-fire and
related computationally tractable spiking unit models.  More detailed
compartmental models can be simulated in NEST, Neuron or Genesis instead,
and packaged up using the Sheet interface so that they can be used
in Topographica.

<!-- Consider implementing:
  Neural Computation Volume 21, Number 3, 2009, "A Canonical Model for
  Event-Driven Neural Simulators", Stefan Mihalas and Ernst Niebur
-->

<!--  
<P><DT>Animating plot histories</DT><DD>
GUI plot windows save a history of each plot, and it should be
feasible to add animations of these plots over time, as a helpful
visualization.

<P><DT>Registry editor</DT><DD>
In a large network with components of different types, each having
various parameters and default values, it can be difficult to
determine the values that will be used for new objects of a certain
type.  We plan to add a hierarchical global variable display and
editor to allow these values to be inspected and changed more easily.

<P>We also plan to add the ability to track which parameters have
actually been used by a given object, so that it is clear how
to modify the behavior of that object.
-->
  
<P><DT>User-defined scales</DT><DD>
The simulator is written in terms of abstract dimensions, such as
Sheet areas that default to 1.0.  This helps ensure that the simulator
is general enough to model a variety of systems.  However, it is often
desirable to calibrate the system for specific scales, such as degrees
of visual angle, millimeters in cortex, etc.  We plan to add
user-defined scales on top of the arbitrary scales, mapping from
values in the simulator to user-defined quantities for display.
<!-- See http://ipython.scipy.org/doc/manual/node11.html for bg on handling arbitrary units. -->

<P><DT>Data import/export</DT><DD>   We would like to provide
easy-to-use interfaces for exchanging data and calling code in other
simulators, such as Matlab (see the optional external package
<A HREF="../Reference_Manual/index.html#mlabwrap">mlabwrap</A>).
These will be used both for analyzing Topographica data, and for
allowing connection patterns and/or map organization to be specified
from experimental data.  Meanwhile, the Python command-line interface
can be used to display or save any element of the model.

</DL>

<H2>Ongoing:</H2>
<DL COMPACT>

<DT>ALERTs</DT><DD>
There are a large number of relatively small problems noted in the
source code for the simulator; these are marked with comments
containing the string ALERT.  These comments help clarify how the code
should look when it is fully polished, and act as our to-do list.
They also help prevent poor programming style from being propagated to
other parts of the code before we have a chance to correct it.  We are
slowly working to correct these issues.

<P><DT>Improve documentation</DT><DD>
The reference manual is generated automatically from the source code,
and needs significant attention to ensure that it is readable and
consistent.  For instance, not all parameters are documented yet, but
all will need to be.

<P><DT>More testing code</DT><DD>
Topographica has a fairly complete test library, but there are still
classes and functions without corresponding tests.  Eventually, there
should be tests for everything.

<P><DT>Pycheck/pylint</DT><DD>
It would be helpful to go through the output from the pycheck and
pylint programs (included with Topographica), fixing any suspicious
things, and disabling the remaining warnings.  That way, new code
could be automatically checked with those programs and the warnings
would be likely to be meaningful.

<P><DT>More non-visual modalities</DT><DD>
Most of the specific support in Topographica is designed with visual
areas in mind, but is written generally so that it applies to any
topographically organized region.  We are implementing specific
models of non-visual areas, providing input generation, models of
subcortical processing, and appropriate visualizations.  For instance,
there are now models of somatosensory areas, such as hand surfaces and
rat whisker barrels, motor areas controlling eye movements, and auditory inputs. 
Additional contributions from Topographica users with experience in
these domains will be particularly helpful.

<P><DT>More library components</DT><DD>
Topographica currently includes examples of each type of library
component, such as Sheets, Projections, TransferFns, ResponseFunctions,
LearningFunctions, and PatternGenerators.  However, many other types
are used in the literature, and as these are implemented in
Topographica they will be added to the library.  Again, user
contributions are very welcome!

<P><DT>More example models</DT><DD>
Topographica currently includes a number of example models,
mostly from the visual system but also from somatosensory,
auditory, and motor areas.  As additional models are implemented,
they will be added as examples and starting points.  Again, user
contributions are very welcome!

</DL>
