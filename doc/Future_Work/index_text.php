<P>Topographica is under very active development, but there are always
more features that we have not yet been able to implement or bugs that
we have not been able to address.  These will be listed in our GitHub
<a target="_top" href="https://github.com/ioam/topographica/issues">Issues</a> list,
or or in the issues for a specific
<a target="_top" href="https://github.com/ioam">subproject</a> if appropriate.  Feel
free to add suggestions of your own to those lists, or to
<A HREF="../Developer_Manual/index.html#joining">tackle one of the
existing problems listed</A> if you need that feature for your work.
Other general, ongoing tasks include:

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

<DL COMPACT>

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
<!--
<P><DT>Parallelization</DT><DD>
Parallel support using MPI and OpenMP has been implemented, and should
soon be part of the Topographica release.  GP-GPU support has also been
prototyped, but has not yet delivered significant performance gains,
and so it is not an area of current focus.
-->
<!-- Should consider sparse layers with patchy distribution of units -->
<!--
<P><DT>Bitmap plotting enhancements</DT><DD>

The current basic support for two-dimensional bitmap plotting will
eventually need to be expanded to allow the user to control plot
brightness scaling, allow custom colormaps, and add an "overload" or "cropped"
indicator to show if some values are too large to be displayed in the
selected range.
-->							 
<!--
<P>Other minor changes planned include adding outlining of
ConnectionField extents, plotting histograms for each bitmap,
and separate default colors for onscreen and publication plots.
-->							 
<!-- plus user-defined arbitrary colormaps ("KRYW", "BbKrR", etc.), 
including allowing a threshold so that a colormap plot can be
shown on top of a monochrome background plot, e.g. an activity blob on
top of an ocular dominance or other grayscale map. 
-->
<!--  
<P><DT>Spiking support</DT><DD>
Topographica primarily supports firing-rate (scalar) units, but a
small spiking model is included with topographica
(examples/leaky_lissom_or.ty), and other models can be implemented in
external spiking simulators and
<A HREF="http://dx.doi.org/10.3389/neuro.11.008.2009">easily
interfaced to Topographica</A>).
  
  Consider implementing:
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
<!--  
<P><DT>User-defined scales</DT><DD>
The simulator is written in terms of abstract dimensions, such as
Sheet areas that default to 1.0.  This helps ensure that the simulator
is general enough to model a variety of systems.  However, it is often
desirable to calibrate the system for specific scales, such as degrees
of visual angle, millimeters in cortex, etc.  We have developed 
simple support for making user-defined scales explicit, and eventually
hope to make it part of the standard distribution.

<P><DT>Data import/export</DT><DD>
We would like to provide easy-to-use interfaces for exchanging data
(e.g. in HDF5 format) and calling code in other simulators, such as
Matlab (see the optional external package
<A HREF="../Reference_Manual/index.html#mlabwrap">mlabwrap</A>).
These will be used both for analyzing Topographica data, and for
allowing connection patterns and/or map organization to be specified
from experimental data.  Meanwhile, the Python command-line interface
can be used to display or save any element of the model.
</DL>

<H2>Ongoing:</H2>
-->

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
Topographica code is automatically checked using pyflakes, and
should but more stringent tests can be performed by the pycheck and
pylint programs.  It would be very useful to fix any suspicious items
reported by those programs, and to disable the remaining warnings.
That way, new code could be automatically checked with those programs
and the warnings would be likely to be meaningful.  (Right now,
the real issues detected by those programs are buried in a sea of
spurious warnings.)

<P><DT>More non-visual modalities</DT><DD>
Much of the neural-specific code in Topographica was designed with
visual areas in mind, but it is written generally so that it applies
  to any topographically organized region.  Examples are provided for
somatosensory inputs (e.g. rodent whisker barrels), auditory inputs,
and motor outputs (for controlling eye movements) that show how to
work with those modalities, but additional contributions for other
types of sensory inputs or motor outputs would be very welcome from
Topographica users with experience in these domains.

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
