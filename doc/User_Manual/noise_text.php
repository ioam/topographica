<H1>Adding noise to Topographica</H1>

Most of the default settings in Topographica give precise, repeatable,
noise-free results, in order to make the behavior predictable and
understandable.  However, there are many ways to increase realism by
adding noise, a few of which are outlined below.

<H2>Additive and multiplicative noise in output_fns</H2>

One easy way to add noise in Topographica is by using a
<i>TransferFn</i>.  A TransferFn is simply a function that maps an
array into another array of the same size and shape.  At many
locations in the Topographica code, a parameter named output_fns is
provided to allow the user to put in any desired functions of this
type.  For instance, the output_fns of a Sheet (e.g. the Retina or V1)
constitute its activation or transfer function.  The output_fns of a
Projection (e.g. Afferent or LateralExcitatory) are applied to the
activity in that Projection after it has been computed, and thus are
also transfer functions.

<p>Multiple TransferFns can be placed in Topographica output_fns, and
will be applied sequentially. For instance, LISSOM V1 Sheets typically
have one PiecewiseLinear() TransferFn in the list of output_fns; noise
can be added to this by appending to output_fns a TransferFn that adds
noise.  Others that have an empty list of output_fns by default can
again just append the new output_function to the list. Suitable
transfer functions for noise include variants of:

<blockquote><small>
  transferfn.misc.PatternCombine(generator=pattern.random.UniformRandom(scale=1.0,offset=1.0),operator=numpy.multiply)<br>

  transferfn.misc.PatternCombine(generator=pattern.random.GaussianRandom(scale=0.1,offset=-0.05),operator=numpy.add))
</small></blockquote>

where the offset and scale parameters determine the mean value and the
range of the variation, respectively, the operator determines whether
the noise is multiplicative, divisive, or some other type of
combination, and the noise itself can either be Uniform or Gaussian
(i.e., normal), or even some some user-defined distribution.  There
are also some other noise-related TransferFns available, such as
ProportionalGaussian (variance proportional to the mean).

<P>Hints: For additive UniformRandom noise, if you are modelling
non-zero background levels of activity in a Sheet or Projection, you
can use an offset of zero and a scale that is the level of noise you
want.  In other cases where you want to avoid changing the average
activity levels, you can get zero-mean UniformRandom additive noise by
making the offset be a negative number that is half of the scale.  To
keep the average activity levels constant with multiplicative noise
requires an offset of 1.0-scale/2.0; the scale then determines the
noise level.  You can of course combine both types of noise in
succession, in which case you will typically want to do the
multiplicative noise first, to avoid scaling the additive noise.
Note that GaussianRandom noise is zero mean already; the difference
compared to UniformRandom is for historical reasons.

<P>As an example, to inject zero-mean additive uniform random noise
into the LateralExcitatory Projection of a LISSOM-based model, just change e.g.

<pre>
  output_fns=[]
</pre>

(if output_fns are specified) to e.g.:

<pre>
  output_fns=[transferfn.misc.PatternCombine(generator=pattern.random.\
      UniformRandom(scale=0.1,offset=-0.05),operator=numpy.add)]
</pre>


Some networks may not state "output_fns=[]" explicitly, in which case
just add the entire string above to the definition of that projection
in the .ty file.  To see the results immediately, just run the network
for one step, then visualize the Projection Activity and the final
Activity.  The long-term effects of this noise can then be evaluated
by running for longer periods.

<H2>Projection mapping jitter</H2>

<P>Another important way to add variability is to add jitter when the
initial mapping between sheets is set up, i.e. to disturb the
topographic mapping of a CFProjection's Connection Fields from the
input sheet.  The mapping of a CFProjection is controlled by a
parameter "coord_mapper", which by default does a perfect topographic
mapping that makes analysis easier, but is too ideal to be
realistic. Instead, you can specify a jittered mapping for the
CFProjection, by adding:

<pre>
  coord_mapper = coordmapper.Jitter(gen=numbergen.UniformRandom(seed=1023),scale=0.2)
</pre>

to the topo.sim.connect command, to offset the values by a random
amount in the range plus or minus 0.1 Sheet coordinates around the
precisely topographic mapped value.  The results can be visualized by
plotting the Projection and enabling "Situate".  Once set up, the
jitter of the CF boundaries will always be present, but the weights
inside the boundaries may reorganize to remove the effect of the
jittering.

<P>Note that the seed value allows you to control which specific
pattern of jitter is used, e.g. if you want two different Projections
of the same shape to have the same specific jittered values (e.g. for
matching ON and OFF projections).  Different seeds will allow the
projections to be jittered independently of each other.

<P>Also note that the coord_mapper varies the <i>incoming</i> connection
field location.  Because of how connection fields are currently
implemented, it is much more difficult to vary the outgoing connection
field location.  In the case of the LGN->V1 projection, one can
instead add jitter to the Retina->LGN projection, which effectively
varies the outgoing connection field of the LGN.  


<H2>ConnectionField shape noise</H2>

Another type of noise is differences in the connection field shapes
between neurons in the same projection.  Most of the example .ty files
specify simple circular weights outlines, and to save memory by
default all CFs in a projection share the same weight outline.  If you
want to try using noisy outlines where only some values within the
circle have any effect, first set
CFProjection.same_cf_shape_for_all_cfs=False, then set
CFProjection.cf_shape to a PatternGenerator that returns different
results each time it is evaluated. By default, dynamic parameters in
Topographica only advance once per simulation time, so it is next
necessary to call CFProjection.cf_shape.set_dynamic_time_fn(None),
causing the PatternGenerator's dynamic values to change each time it is
evaluated. Note that one further command may be necessary in some
cases: by default, the PatternGenerator used for cf_shape has its size
set automatically; if instead you want to control the size, set
CFProjection.autosize_mask to be False.  
<!--CEBALERT: all this awkwardness is SF bug #2716972!-->



<H2>Weight adjustment noise</H2>

<P>One could imagine the process of adjusting weights to be a
stochastic or quantized process, either of which would give some
variability to the process of updating weight values.  For instance,
this could be modeled with additive or multiplicative noise before or
after any weight normalization.  

<!-- CEBALERT: SF #2716954

E.g., a script that uses CFPOF_DivisiveNormalizeL1_opt or
CFPOF_DivisiveNormalizeL1 could be changed to:

<pre>
  CFProjection.weights_output_fns=[CFPOF_DivisiveNormalizeL1(single_cf_fn=(\
     PatternCombine(generator=topo.pattern.random.UniformRandom(scale=0.1,offset=-0.05),operator=numpy.add)+\
     DivisiveNormalizeL1(norm_value=1.0)))]
</pre>

(or those parameters could be set on a specific projection).  To model
noise arising in the normalization step itself, just exchange
DivisiveNormalizeL1 and PatternCombine, or add another PatternCombine
after DivisiveNormalizeL1.

<P>Note that weights_output_fns are used when setting up the initial
weights, so if you mean for it to apply only to learning, you may want
to add the noise only after the network has been initialized.  For
LISSOM networks this can be achieved by setting
LISSOM.post_initialization_weights_output_fns instead of
CFProjection.weights_output_fns. 
-->


<H2>Spatially correlated noise</H2>

<P>The examples above focus on types of noise that are spatially
uncorrelated, i.e. where the noise for each unit or weight or
Connection Field is chosen independently of all others of that type.
Many kinds of "noise" in biological systems will have spatial
correlations, e.g. due to some underlying source that has a spatial
extent (such as the vasculature, some diffusible chemical, etc.).  To
include such effects for the noise sources described above (output_fns),
you could add new classes in topo.pattern.random that generate
spatially correlated noise rather than noise that is independent per
pixel.  E.g., the noise matrix could be convolved with a small
blurring kernel before it is added or multiplied with the activity, or
the noise matrix could be low-pass filtered, e.g. to create the 1/f
noise (pink noise) that is common in physical systems.


<H2>Measurement noise</H2>

<P>One could also consider the effects of measurement noise, e.g. on
computing preference maps, which could be done by temporarily
modifying the output_fns of each sheet so that what is measured is no
longer the actual activity value, but a transformation of it.  A
better approach would probably be to add an output_fns parameter to the
commands for measuring maps, so that such functions could be supplied
for any measurement.
