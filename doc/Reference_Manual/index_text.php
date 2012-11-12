<P>This reference manual contains detailed documentation of each
component making up Topographica, assuming that the user is already
familiar with basic Topographica usage.  (See the <A
HREF="../User_Manual/index.html">User Manual</A> and <A
HREF="../Tutorials/index.html">Tutorials</A> for such an introduction.)
The reference manual is generated directly from documentation and
declarations in the source code, and is often much more verbose than
necessary, because many little-used yet often-duplicated methods are
listed for each class.  Still, the reference for a given component
does provide a comprehensive listing of all attributes and methods,
inherited or otherwise, which is difficult to obtain from the source
code directly and is not covered by the User Manual or Tutorials.

<P>Topographica's components can be categorized into subprojects
(available separately), core packages (required for Topographica),
library packages (useful families of components not required for
Topographica itself), and other
<a target="_top" href="../Downloads/dependencies.html">external dependencies</a>
(documented separately).  Everything but the external dependencies is
documented at the <A href="hierarchy.html"><strong>main reference manual
page</strong></A>, but the different categories of objects are broken
down here in a way that's easier to follow.



<H2><A NAME="core">Subprojects</A></H2>

<P><DL COMPACT>
<P><DT><A href="param-module.html"><strong>param</strong></A></DT>
<DD>Support for objects with user-controllable attributes</DD>
<P><DT><A href="paramtk-module.html"><strong>paramtk</strong></A></DT>
<DD>Optional Tk GUI support for param</DD>
<P><DT><A href="numbergen-module.html"><strong>numbergen</strong></A></DT>
<DD>Support for generating streams of scalars, e.g. random
  distributions; currently available through the imagen module (below)</DD>
<P><DT><A href="imagen-module.html"><strong>imagen</strong></A></DT>
<DD>Support for generating 1D, and 2D patterns, and for defining
  mappings between continuous 2D space and finite matrices</DD>
</dl>

The param, paramtk, numbergen, and imagen modules are each developed
and maintained separately from Topographica, because they are
general-purpose packages that can be useful for a wide variety of
Python programs.  However, they are documented together with
Topographica because they were developed alongside Topographica and
are used extensively within Topographica.


<H2><A NAME="core">Core Topographica packages</A></H2>

<P>The Topographica simulator itself is implemented in a set of
interrelated packages:

<P><DL COMPACT>
<P><DT><A href="topo.base-module.html"><strong>base</strong></A></DT>
<DD>Core Topographica-specific functions and classes</DD>
<P><DT><A href="topo.plotting-module.html"><strong>plotting</strong></A></DT>
<DD>Visualization functions and classes</DD>
<P><DT><A href="topo.analysis-module.html"><strong>analysis</strong></A></DT>
<DD>Analysis functions and classes (besides plotting)</DD>
<P><DT><A href="topo.misc-module.html"><strong>misc</strong></A></DT>
<DD>Miscellaneous independent utility functions and classes</DD>
<P><DT><A href="topo.tkgui-module.html"><strong>tkgui</strong></A></DT>
<DD>Tk-based graphical user interface (GUI)</DD>
</dl>

The <strong>base</strong> directory contains the most fundamental
Topographica classes, implementing basic functionality such as Sheets
(arrays of units), Projections (large groups of connections between
Sheets), ConnectionFields (spatially localized groups of connections
to one unit), and the event-driven Simulation.  It relies heavily on
the generic support for Parameters (user-controllable attributes) from
the <strong>param</strong> subproject.  Together the files in
<tt>base</tt> are independent of the rest of the files in
<tt>topo/</tt>, and act as the primary programming interface on which
Topographica is built.  The rest of the directories add components
used in specific models, or add graphical interfaces.



<H2><A NAME="library">Library</A></H2>

<P>Beyond the basic simulator implemented in the core packages,
Topographica provides an extensive and extensible library of 
classes that can be used to implement models of various neural
systems: 

<P><DL COMPACT>
<P><DT><A href="topo.sheet-module.html"><strong>sheet</strong></A></DT>
<DD>Sheet classes: 2D arrays of processing units</DD>
<P><DT><A href="topo.projection-module.html"><strong>projection</strong></A></DT>
<DD>Projection classes: connections between Sheets</DD>
<P><DT><A href="topo.ep-module.html"><strong>ep</strong></A></DT>
<DD>EventProcessor classes: other simulation objects</DD>
<P><DT><A href="topo.transferfn-module.html"><strong>transferfn</strong></A></DT>
<DD>Output functions: apply to matrices to do e.g. normalization or squashing</DD>
<P><DT><A href="topo.responsefn-module.html"><strong>responsefn</strong></A></DT>
<DD>Calculate the response of a unit or a Projection</DD>
<P><DT><A href="topo.learningfn-module.html"><strong>learningfn</strong></A></DT>
<DD>Adjust weights for a unit or a Projection</DD>
<P><DT><A href="topo.coordmapper-module.html"><strong>coordmapper</strong></A></DT>
<DD>Determine mapping from one Projection to another</DD>
<P><DT><A href="topo.command-module.html"><strong>command</strong></A></DT>
<DD>High-level user commands</DD>
</DL>

<P>All of the library components are optional, in the sense that they
can be deleted or ignored or replaced with custom versions without
affecting the code in any of the core packages.  (Of course, any
specific model that depends on the component would not be able to
function without it!)

<P>Each of the library directories can be extended with new classes by
simply defining them in your own files, and then making sure that your
file has been run or imported before you start the GUI or use the new
class in your .ty file.  I.e., user-defined classes of these types
have the same status as those shipped with Topographica -- just make
sure they have been defined, and Topographica will find them and use
them just like its own classes.

<P>Many of the components come in multiple varieties, to be used at
different levels in a model.  For instance, there are learning
functions that operate on a single unit (type LearningFn), and ones
that operate on an entire CFProjection (type CFPLearningFn).  The
lower level components can be used by providing them to a "Plugin"
version of the higher level component, which will apply the lower
level version to each unit.  For instance, a LearningFn can be used
with a CFPLearningFn of type CFPLF_Plugin, and will be applied the
same to each unit individually.

<P>Some components also come with an optimized version, usually
written in C for speed.  The fastest, but least flexible, components
will be high-level components written in C, such as CFPLF_Hebbian_opt.

<P>Apart from the Topographica-specific modules described above,
Topographica also uses many
<a target="_top" href="../Downloads/dependencies.html">external libraries</a>, each
documented separately.
