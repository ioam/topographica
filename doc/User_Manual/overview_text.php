<!-- -*-html-helper-*- mode -- (Hint for Emacs)-->

<H1>Overview of Topographica design and features</H1>

This section will first give an overview of the parts that make up
Topographica, and will then give a guide on how to choose a subset of
them for use in any particular model.



<H2><a name="class-hierarchies">Major Topographica object types</a></H2>

<P>In this section, we outline the basic hierarchies of object types
used by Topographica.  All of these are available to the user when
designing a model, but as the <a target="_top" href="#implementation-levels">
next section</a> indicates, not all of them need to be used for any
particular model, and anything not used can be ignored.  These lists
are only representative of the object 
types available in each general class; see the
<A HREF="../Reference_Manual/index.html">reference manual</A> entry
for each base class (which is typically hyperlinked below), the menus
in the GUI <A HREF="modeleditor.html">model editor</A>, or the files
in topo/*/ to see the full list of the ones available.

<P>In each section, the relationships between the different classes
are shown as an inheritance diagram, in outline format.  As an
example, the indentation in this diagram:
<ul>
<li>Animal
    <ul>
    <li>Dog
        <ul>
        <li>Collie
        <li>Terrier
        </ul>
    </ul>
</ul>

indicates that a Dog is a type of Animal, and that Collies and
Terriers are both types of Dog (and thus also types of Animals).  All
Collies are Dogs, and all Collies are Animals, but not all Dogs are
Collies, and not all Animals are necessarily Dogs.  These
relationships show how the classes fit together; e.g., anything in
Topographica that requires an object of type Animal will accept a
Collie or a Terrier as well, plus any user-defined object of type Dog.


<H3>Parameterized objects and Parameters</H3>

<ul>
<li><?php classref('param.parameterized','Parameterized')?>
<li><?php classref('param.parameterized','Parameter')?>
    <ul>
    <li><?php classref('param','Number')?>
        <ul>
	<li><?php classref('param','Integer')?>
        </ul>
    <li><?php classref('param','Boolean')?>
    <li><?php classref('param','Callable')?>
    <li><?php classref('param','ClassSelector')?>
    </ul>
</ul>

<P>In Python, any object can have <i>attributes</i>, which consist of
a name and a value (of any type).  Topographica provides an extended
version of attributes called <?php
classref('param.parameterized','Parameter')?>s, which have their
own documentation, range and type error checking, and mechanisms for
inheritance of default values.  These features are provided for any
<?php classref('param.parameterized','Parameterized')?> object,
which is a Python object extended to support <?php
classref('param.parameterized','Parameter')?>s.  Most
Topographica objects are <?php
classref('param.parameterized','Parameterized')?>.  <A
HREF="parameters.html">Parameters</A> are discussed in more detail on
<A HREF="parameters.html">a separate page</A>.


<H3>Simulation and Events</H3>

<ul>
<li><?php classref('topo.base.simulation','Simulation')?>
<li><?php classref('topo.base.simulation','Event')?>
<li><?php classref('topo.base.simulation','EventProcessor')?>
    <ul>
    <li><?php classref('topo.base.sheet','Sheet')?>: (see below)
    </ul>
</ul>

<P>The set of objects to be simulated is kept by the 
<?php classref('topo.base.simulation','Simulation')?> class,
which keeps track of the current simulator time along with 
<?php classref('topo.base.simulation','Event')?>s
that are currently occurring or are scheduled to occur in the future.
The objects in the simulation are of type
<?php classref('topo.base.simulation','EventProcessor')?>,
which simply means that they can process events.  Events and
EventProcessors are both very general concepts, because
the Simulation must be able to include any possible process
that could be relevant for a model.


<H3>Sheets</H3>

<P>
<ul>
<li><?php classref('topo.base.sheet','Sheet')?>
    <ul>
    <li><?php classref('topo.base.projection','ProjectionSheet')?>
      Sheet that can calculate activity based on a set of
      <?php classref('topo.base.projection','Projection')?>s.
        <ul>
        <li><?php classref('topo.base.cf','CFSheet')?>
	  ProjectionSheet whose Projections are of type
	  <?php classref('topo.base.cf','CFProjection')?>,
	  which means that they are made up of
  	  <?php classref('topo.base.cf','ConnectionField')?>s
	  (below).  This Sheet type supports a large class of
	  topographic map models as-is, but others need specific
	  extensions.
            <ul>
            <li><?php classref('topo.sheet.lissom','LISSOM')?>: 
	      CFSheet with extensions to support the LISSOM algorithm.
            <li><?php classref('topo.sheet.saccade','SaccadeController')?>: 
             CFSheet with extensions to support saccades.
            </ul>
        </ul>
    </ul>
</ul>

<P>The actual EventProcessors in most current Topographica simulations are
typically of type <?php classref('topo.base.sheet','Sheet')?>.  A
Sheet is a specific type of EventProcessor that occupies a finite 2D
region of the continuous plane, allows indexing of this region using
floating point coordinates, and maintains a rectangular array of
activity values covering this region.


<H3>Connections and Projections</H3>

<!-- ALERT: Does it work better to have the list first or second?  With -->
<!-- explanations or without? -->

<ul>
<li><?php classref('topo.base.simulation','EPConnection')?>
    <ul>
    <li><?php classref('topo.base.projection','Projection')?>
        <ul>
        <li><?php classref('topo.base.cf','CFProjection')?>
            <ul>
            <li><?php classref('topo.projection','SharedWeightCFProjection')?>
            </ul>
        </ul>
    </ul>
</ul>

<P>EventProcessors can be connected together with unidirectional links
called <?php classref('topo.base.simulation','EPConnection')?>s.  These
connections provide a persistent mechanism for data generated by one
EventProcessor to be delivered to another one after some nonzero delay
in simulation time.

<P>Most connections between Sheets are of type 
<?php classref('topo.base.projection','Projection')?>, which can be thought
of as a bulk set of connections that includes many individual
connections between neural units.  More specifically, a Projection is
a Connection that can produce an Activity matrix when given an input
Activity matrix, which will typically be used by the destination Sheet
when it computes its activation.  In the GUI, the Projection activity
can be visualized just as Sheet activity is, though the Sheet activity
is considered the actual response of each unit.  (The Projection
activity is just a handy way of computing and reasoning about the
contribution of each Projection to this overall Sheet activity.)

<P>One specific type of Projection currently implemented is <?php
classref('topo.base.cf','CFProjection')?>, i.e. a Projection that
consists of a set of <?php
classref('topo.base.cf','ConnectionField')?> objects, each of which
contains the connections to one unit in the destination CFSheet.
CFProjection is very general, and with appropriate parameters can
implement either spatially restricted localized CFs, all-to-all
projections (using a nominal_bounds_template BoundingBox with a radius
larger than the source Sheet), or one-to-one projections (using a
nominal_bounds_template sized to cover only a single unit on the
source Sheet).  A special type of CFProjection, <?php
classref('topo.projection','SharedWeightCFProjection')?> is used
to perform the mathematical operation of convolution, i.e., applying a
set of weights to all points in a plane, and is equivalent to having
one ConnectionField shared by every destination neuron.


<H3>PatternGenerators</H3>
<ul>
<li><?php classref('topo.base.patterngenerator','PatternGenerator')?>
    <ul>
    <li><?php classref('topo.pattern','Gaussian')?>
    <li><?php classref('topo.base.patterngenerator','Constant')?>
    <li><?php classref('topo.pattern.random','UniformRandom')?>
    </ul>
</ul>

<P>A large family of flexible, general-purpose function objects for
producing 2D patterns is provided, as described on
<A HREF="patterns.html">a separate page</A>.


<H3>Transfer functions</H3>

<ul>
<li><?php classref('topo.base.functionfamily','TransferFn')?>
    <ul>
    <li><?php classref('topo.transferfn','DivisiveNormalizeL1')?>
    <li><?php classref('topo.transferfn','DivisiveNormalizeL2')?>
    <li><?php classref('topo.transferfn','PiecewiseLinear')?>
    <li><?php classref('topo.transferfn.misc','PatternCombine')?>
    <li><?php classref('topo.base.functionfamily','IdentityTF')?>
    </ul>
</ul>

<ul>
<li><?php classref('topo.base.cf','CFPOutputFn')?>
    <ul>
    <li><?php classref('topo.base.cf','CFPOF_Plugin')?>
    <li><?php classref('topo.transferfn.optimized','CFPOF_DivisiveNormalizeL1')?>
    </ul>
</ul>

<P>A TransferFn is a function object that will accept a matrix argument
and (typically) modify it in some way.  This is a very simple concept,
but it is used many times throughout the Topographica code, and
provides a lot of flexibility.  Any function that can normalize a set
of weights or an input pattern is a TransferFn, as is any Sheet's
activity transfer function.

<P>TransferFns are controlled by a set of parameters that are each
typically called output_fns.  Each such parameter is associated with a
particular processing step of a Sheet or a Projection.  For instance,
CFProjections have output_fns applied after they calculate their
activity, and weights_output_fns applied after a set of weights is
modified.  Sheets have output_fns applied after they calculate their
activity, and PatternGenerators have output_fns applied after
the pattern is calculated.

<P>The output_fns parameters allow the user to control calculations in
a flexible way, without having to write or maintain new code.  For
instance, the PatternCombine TransferFn can be used to add a
user-specified type of random noise to any of the major processing
steps.  Alternatively, it can be used to mask out a specific region
at the end of the calculation, to implement a user-specified lesion or
a non-rectangular neural region.

<P>Multiple TransferFns can be applied in series, e.g. to add random
noise, normalize the results, and then mask out lesioned units.

<P>For the common and very expensive case of normalizing
ConnectionField weights, a family of transfer functions that works on an
entire CFProjection at once is also available (CFPOutputFn).  These
functions can be optimized heavily, and can do such things as
normalizing across an entire Projection.



<H3>Response functions</H3>

<ul>
<li><?php classref('topo.base.functionfamily','ResponseFn')?>
    <ul>
    <li><?php classref('topo.base.functionfamily','DotProduct')?>
    </ul>
</ul>


<ul>
<li><?php classref('topo.base.cf','CFPResponseFn')?>
    <ul>
    <li><?php classref('topo.base.cf','CFPRF_Plugin')?>
    <li><?php classref('topo.responsefn.optimized','CFPRF_DotProduct')?>
    <li><?php classref('topo.responsefn.projfn','CFPRF_EuclideanDistance')?>
    </ul>
</ul>


<P>A ResponseFn is a function object that will compute a matrix of
activity values from a matrix of weights and an input matrix of the
same shape.  This is typically used for a neural response function.

<P>A family of response functions that works on an entire CFProjection
at once is also available (CFPResponseFn).  These functions can be
optimized heavily, and can do such things as normalizing across an
entire Sheet.


<H3>Learning functions</H3>

<ul>
<li><?php classref('topo.base.functionfamily','LearningFn')?>
    <ul>
    <li><?php classref('topo.base.functionfamily','Hebbian')?>
    <li><?php classref('topo.learningfn','Oja')?>
    <li><?php classref('topo.learningfn','Covariance')?>
    </ul>
</ul>

<ul>
<li><?php classref('topo.base.cf','CFPLearningFn')?>
    <ul>
    <li><?php classref('topo.base.cf','CFPLF_Plugin')?>
    <li><?php classref('topo.learningfn.optimized','CFPLF_Hebbian')?>
    <li><?php classref('topo.learningfn.som','CFPLF_HebbianSOM')?>
    </ul>
</ul>



<P>A LearningFn is a function object that will modify a matrix of
weight values given an input activity pattern and an output activity
value.  Most such rules are Hebbian-based, i.e., driven by the product
of the input and output activity values, but there are many variants.

<P>A family of learning functions that works on an entire CFProjection
at once is also available (CFPLearningFn).  These functions can be
optimized heavily, and can do such things as basing the activity
on the single best-responding unit in a Sheet (as in a Kohonen SOM).

<H2><a name="audience">Who should use Topographica?</a></H2>

<P>Topographica's main target audience is computational
neuroscientists who want to simulate large, topographically mapped
brain regions.  Many such researchers initially start coding with
general-purpose languages like Matlab or bare Python, because it is
relatively straightforward to specify an initial fully-connected model
with square connections and hard-coded sizes from scratch.  However,
as soon as the model becomes more complex, the code quickly becomes
unwieldy.  Supporting local rather than full connectivity, circular or
arbitrary connection patterns rather than rectangular arrays, variable
densities of neurons per region rather than hard-coded ones, arbitrary
patterns of connectivity (including feedforward and feedback
connections) between sheets rather than feedforward connections only,
--- all of these will quickly make code be unreadable and
unmaintainable without a clear, clean overall design.  Topographica's
developers have dealt with these cases already, and the result is
highly robust and reliable, making it very straightforward to run
a large class of models without complicated coding or debugging.


<H2><a name="implementation-levels">How much of Topographica to use</a></H2>

<P>Topographica is designed as an extensible framework or toolkit,
rather than as a monolithic application with a fixed list of features.
Users can extend its functionality by writing objects in Python, which
is a fully general-purpose interpreted programming language.  As a result,
Topographica supports any possible model (and indeed, any possible
software program), but as the above lists suggest, it provides much
more specific support for specific types of models of topographic
maps.  This approach allows some models to be built without any
programming, while not limiting the future directions of research.

<P>The following list explains the different levels of support
provided by Topographica for different types of models, depending on
which parts of Topographica you are able to use.  The list is ordered
so that the most general support, suitable for everyone but requiring
the most user effort, is at the top, and the most specific support is
at the bottom.  Note that everything in the levels below where your
model fits in can be ignored, because those files can be deleted with no ill 
effects unless some part of your model uses objects from those
levels.  You can also add items to any level, i.e., to any class
hierarchy listed above; please 
<A HREF="mailto:&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107">contact
us</a> to contribute any of these to the project or to join as a
developer.

<P>Topographica levels:

<ol>
<p><li>Python with C interface (ignoring <i>everything</i> in topo/): 
<dl><dt>Supports:</dt><dd>Anything is possible, with no performance or 
	programming limitations (since anything can be written
	efficiently in C, and the rest can be written in Python).
    <dt>Limitations:</dt><dd>Need to do all programming yourself.  Can't
	mix and match code with other researchers very easily, because
	they are unlikely to choose similar interfaces or make similar 
	assumptions.
</dl>    
<p><li>Everything in 1., plus event-driven simulator with parameterizable objects, debugging 
       output, etc. (using just simulation.py from topo/base/ in addition to Parameter 
       support from the Param package):

<dl><dt>Supports:</dt><dd>Running simulations of any physical system, with 
	good semantics for object parameter specification with inheritance.
    <dt>Limitations:</dt><dd>Basic event structure is in Python, which is
	good for generality but means that performance will be good
        only if the computation in the individual events is big
        compared to the number of events.  This assumption is true for
        existing Topographica simulations, but may not apply to all
	systems being modelled.
</dl>    
<p><li>Everything in 1.-2., plus Sheets (adding topo/base/sheet.py and its dependencies)
<dl><dt>Supports:</dt><dd>Uniform interface for a wide variety of brain 
        models of topographically organized 2D regions.  E.g. can measure
	preference maps for anything supporting the Sheet interface, and
	can do plotting for them uniformly.
    <dt>Limitations:</dt><dd>Not useful if the assumptions of what 
        constitutes a Sheet do not apply to your model -- e.g. ignores
        curvature, sulci, gyrii; has hard boundaries between regions,
        uses Cartesian, not hexagonal grid.  For instance, Sheets are
        not a good way to model how the entire brain is parcellated
        into brain areas during development, because that happens in
        3D and does not start out with very strict boundaries between
        regions.
</dl>    
<p><li>Everything in 1.-3., plus Projections and ConnectionFields (adding the rest 
	of topo/base/)
<dl><dt>Supports:</dt><dd>Anything with topographically organized 
	projections between Sheets, each of which contains an array of
	units, each unit having input from a spatially restricted
	region on another (or the same) sheet.  Any such sheet can be
	plotted and analyzed uniformly.
    <dt>Limitations:</dt><dd>Much more specific limitations on what 
	types of models can be used -- e.g. broad, sparse connectivity
	between regions is less well supported (so far), and
	non-topographic mappings are currently left out.
</dl>    
<p><li>Everything in 1.-4., plus the Topographica primitives library (the rest of topo/)
<dl><dt>Supports:</dt><dd>Can implement a large range of map models without
        coding any new objects -- instead setting parameters and calling
        methods on existing objects.  Easy to mix and match components
        between models, and to add just a few new components for a new
        but similar model.  Easy to compare different models from this
        class under identical conditions.
    <dt>Limitations:</dt><dd>Only a relatively small set of components
	has actually been implemented so far, and so in practice the
	primitives library will need to be expanded to cover most new
	models, even from the class of models described in 4.
</dl>    
</ol>

<P>As one moves down this list, the amount of programming required to
implement a basic model decreases (down to zero if you use only the
primitives we've already implemented), but the limitations governing
what can be done at that level increase.  To the extent that these
limitations are appropriate for what you want to model, Topographica
will be an appropriate tool.  If what you want to do conflicts with
these limitations, you will have to go up to higher levels in this
list, doing more of the implementation work yourself and gaining less
from what the Topographica developers have done.  If everything you
are doing ends up being implemented at level 1 above, then there is
probably no reason to use Topographica at all, except perhaps as an
example of how to use Python and C together with various external
libraries.

<P>Note that different parts of any particular model may be implemented
at different levels from this list.  For instance, even for a model that
is fully supported by the Topographica primitives in level 5, you may
want to add an interface to a custom-built external hardware device, which
would have to be implemented at level 1.  Data from the device would
then presumably appear in a form compatible with one of the lower
layers 3-5, and could then be used with the other Topographica
primitives.

