<H1>SOM Retinotopic Map</H1>

<p>
This tutorial shows how to use the
<a target="_top" href="http://topographica.org/">Topographica</a> simulator to explore a
simple retinotopic map simulation.  This particular example, taken
from Chapter 3 of the book <A
href="http://computationalmaps.org">Computational Maps in the Visual
Cortex</A>, uses a Kohonen-type Self-Organizing Map (SOM).
Topographica also supports a wide range of other models, and is easily
extensible for models not yet supported.
</p>

<p>This tutorial assumes that you have already followed the
instructions for <a target="_top" href="../Downloads/index.html">obtaining and
installing</a> Topographica. 


<h2>Self-organization</h2>

In this example, we will see how a simple model cortical network
develops a mapping of the dimensions of variance in the input space.

<ol> 
<p></p>

<li>First, 
  <A target="_top" HREF="../User_Manual/scripts.html#copy_examples">get a copy of the
  example files to work with</A> if you do not have them already, and
  open a terminal in the examples directory (the path of the examples directory is 
  printed by Topographica when you are getting a copy of the example files).

<P><li>To start the full simulation from the book using the
  Topographica GUI, you could run:
<pre>
  topographica -p retina_density=24 -p cortex_density=40 \
    som_retinotopy.ty -g
</pre>
  (all on one line, with no backslash).  These changes can also be
  made in the .ty file itself, if you do not want to type them each
  time you run the program.

  <p>However, the default is to use a much smaller network that is
  faster to run while getting similar results.  To do this, start
  topographica:
<pre>
  topographica -g
</pre>

<p>
You should now see a window for the GUI:
<p class='center'>
<img src="images/som_topographica_console.png" alt="Console Window"
align="middle" width="409" height="127">
</p>
  
<p>
The font, window, and button style will differ on different platforms,
but similar controls should be provided.
</p>

  Then, from the <span class='t_item'>Simulation menu</span>,
  select <span class='t_item'>Run Script</span> and
  open <code>som_retinotopy.ty</code> from the <code>examples</code>
  directory.
  
  <P>(The plots below show the results from the full density of the
  book simulation, but results are similar for the default (lower)
  densities.)

</li>

<li>This simulation is a small, fully connected map, with one input
sheet and one cortical sheet. The architecture can be viewed in the
  <span class='w_title'>Model Editor</span> window (which can be
  selected from the <span class='t_item'>Simulation</span> menu), but
  is also shown below: 
<p class='center'>
<img src="images/som_network_diagram.png" alt="SOM network."
align="middle" WIDTH="272" HEIGHT="265" border=2>
</p>

<P>The large circle indicates that these two Sheets are fully connected.

<p></p>
</li>

<li>To see the initial state of this network, select <span
class='t_item'>Projection</span> from the <span
class='t_item'>Plots</span> menu to get the <span
class='w_title'>Projection</span> window, and press the Pre plot hooks'
refresh arrow as the window suggests.  This plot shows the
initial set of weights from a 10x10 subset of the V1 neurons:
<!-- (i.e., all neurons for this small network): -->

<p class='center'>
<img src="images/som_projection_000000.png" alt="Projection window at 0"
align="middle" WIDTH="496" HEIGHT="505">
</p>

<p> Each neuron is fully connected to the input units, and thus has a
24x24 array of weights as shown above, or a 10x10 array if using the
default (reduced) density.  Initially, the weights are uniformly
random.
</p>

<p></p>
</li>

<li>We can visualize the mapping from the input space into the
cortical space using a Center of Gravity plot.  To get one, open the
<span class='t_item'>Plots</span> menu from the <span
class='w_title'>Topographica Console</span>, select <span
class='t_item'>Preference Maps</span> and then <span
class='t_item'>Center of Gravity</span>, and press the Refresh button
by the Pre-plot hooks to get several plots.  These plots show the
results of computing the <i>center of gravity</i>
(a.k.a. <i>centroid</i> or <i>center of mass</i>) of the set of input
weights for each neuron.

<P>This data is presented in several forms, of which the easiest to
interpret at this stage is the <span class='w_title'>Topographic
mapping</span> window.  This plot shows the CoG for each V1 neuron,
plotted on the Retina:

<p class='center'>
<IMG WIDTH="420" HEIGHT="475" SRC="images/som_grid_000000.png" align="middle" alt="CoG bitmap plots">
</p>

<P>Each neuron is represented by a point, and a line segment is drawn
from each neuron to each of its four immediate neighbors so that
neighborhood relationships (if any) will be visible.  From this plot
is is clear that all of the neurons have a CoG near the center of the
retina, which is to be expected because the weights are fully
connected and evenly distributed (and thus all have an average (X,Y)
value near the center of the retina).

<P>The same data is shown in the <span class='w_title'>Center of
Gravity</span> plot window, although it is more difficult to interpret
at this stage:

<p class='center'>
<IMG WIDTH="505" HEIGHT="360" SRC="images/som_cog_000000.png"  align="middle" alt="CoG bitmap plots">
</p>

where the V1 X CoG plot shows the X location preferred by each neuron,
and the V1 Y CoG plot shows the preferred Y locations.  The monochrome
values are scaled so that the neuron with the smallest X preference is
colored black, and that with the largest is colored white, regardless
of the absolute preference values (due to Normalization being
enabled).  Thus the absolute values of the X or Y preferences are not
visible in these plots.  (Without normalization, values below 0.0 are
cropped to black, so only normalized plots are useful for this
particular example.)

<P>The colorful plot labeled "V1 CoG" shows a false-color
visualization of the CoG values, where the amount of red in the plot
is proportional to the X CoG, and the amount of green in the plot is
proportional to the Y CoG.  Where both X and Y are low, the plot is
black or very dark, and where both are high the plot is yellow
(because red and green light together appears yellow).  This provides
a way to visualize how smoothly the combined (X,Y) position is mapped,
although at this stage of training it is not particularly useful.

<P><li>The behavior of this randomly connected network can be visualized
by plotting the activation of each neuron, which shows the final
cortical response to the given input pattern.  Select
<span class='t_item'>Activity</span> from
the <span class='t_item'>Plots</span> menu to get the following plot:

<p class='center'>
<IMG WIDTH="402" HEIGHT="360" SRC="images/som_activity_000000.png" align="middle" alt="Activity at 0">
</p>

<p>This window shows the response for each Sheet in the model, which
is zero at the start of the simulation (and thus both plots are
black).

<P><li>To run one input generation, presentation, activation, and
learning iteration, click in the <span class='t_item'>Run
for</span> field of the <span class='w_title'>Topographica
Console</span> window, make sure it says 1, and hit Go.  The
<span class='w_title'>Activity</span> window should then refresh to
show something like:

<p class='center'>
<IMG WIDTH="402" HEIGHT="360" SRC="images/som_activity_000001.png" align="middle" alt="Activity at 1">
</p>

<p>In the <span class='t_item'>Retina</span> plot, each photoreceptor
is represented as a pixel whose shade of grey codes the response
level, increasing from black to white.  The
<code>som_retinotopy.ty</code> file specified that the input be a
circular Gaussian at a location that is random in each iteration, and
in this particular example the location is near the border of the
retina. The <span class='t_item'>V1</span> plot shows the response
to that input, which for a SOM is initially a large Gaussian-shaped
blob centered around the maximally responding unit.

<P><a name="Projection-activity-plot">To see more detail about what
the responses were before SOM's neighborhood function forced them into
a Gaussian shape, you can look at the Projection Activity plot</a>,
which shows the feedforward activity in V1:

<p class='center'>
<IMG WIDTH="402" HEIGHT="380" SRC="images/som_projection_activity_000001.png" align="middle" alt="Projection Activity at 1">
</p>

<P>Here these responses are best thought of as Euclidean proximity,
not distance.  This formulation of the SOM response function actually
subtracts the distances from the max distance, to ensure that the
response will be larger for smaller Euclidean distances (as one
intuitively expects for a neural response).  The V1 feedforward
activity appears random because the Euclidean distance from the input
vector to the initial random weight vector is random.

<P><li> If you now hit the <span class='t_item'>Refresh</span> arrow
for the pre-plot hooks in the <span class='w_title'>Projection</span>
window, you'll see that most of the neurons have learned new weight
patterns based on this input.

<p class='center'>
<img src="images/som_projection_000001.png" alt="Projection window at 1"
align="middle" WIDTH="496" HEIGHT="505">
</p>

(You should probably turn on the <span
class='t_item'>Auto-refresh</span> button so that this plot will stay
updated for the rest of this session.)  Some of the weights to each
neuron have now
changed due to learning.  In the SOM algorithm, the unit with the
maximum response (i.e., the minimum Euclidean distance between its
weight vector and the input pattern) is chosen, and the weights of
units within a circular area defined by a Gaussian-shaped
<i>neighborhood function</i> around this neuron are updated.

<P>This effect is visible in the <span
class='w_title'>Projection</span> plot -- a few neurons around the
winning unit at the top middle have changed their weights.
Continue pressing Go in the Console window to learn a few more
patterns, each time noticing that a new input pattern is generated and
the weights are updated.  After a few iterations it should be clear
that the input patterns are becoming represented in the weight
patterns, though not very cleanly yet:

<p class='center'>
<img src="images/som_projection_000005.png" alt="Projection window at 5"
align="middle" WIDTH="496" HEIGHT="505">
</p>

If you look at the Projection Activity window, you will see that the
activation patterns are becoming smoother, since the weight vectors
are now similar between neighboring neurons.

<P><li>Continue training for a while and looking at the activation and
weight patterns.  Instead of 1, you can change the
<span
class='t_item'>Run for</span> field to any number to train
numerous iterations in a batch, e.g. 1000.  Using a large number at
once is fine, because it is safe to interrupt training by pressing the
Stop button, and plots can safely be refreshed even during training.
After 5000 iterations, updating the <span class='w_title'>Center of
Gravity</span> should result in something like:

<p class='center'>
<IMG WIDTH="505" HEIGHT="360" SRC="images/som_cog_005000.png"  align="middle" alt="CoG bitmap plots">
</p>

The X and Y CoG plots are now smooth, but not yet the axis-aligned gradients
(e.g. left to right and bottom to top) that an optimal topographic
mapping would have. Similarly, the topographic grid plot:

<p class='center'>
<IMG WIDTH="420" HEIGHT="475" SRC="images/som_grid_005000.png" align="middle" alt="Grid at 100">
</p>

shows that the network is now responding to different regions of the
input space, but that most regions of the input space are not covered
properly.  Additional training up to 10000 iterations (which becomes
faster due to a smaller neighborhood radius) leads to a flat, square
map:

<p class='center'>
<IMG WIDTH="420" HEIGHT="475" SRC="images/som_grid_010000.png" align="middle" alt="Grid at 10000">
</p>

although the weight patterns are still quite broad and not very
selective for typical input patterns:

<P class='center'>
<img src="images/som_projection_010000.png" alt="Projection window at 10000"
align="middle" WIDTH="496" HEIGHT="505">
</p>


and by 40000 the map has good coverage of the available portion of the
input space:

<p class='center'>
<IMG WIDTH="420" HEIGHT="475" SRC="images/som_grid_040000.png" align="middle" alt="Grid at 40000">
</p>

<LI>The final projection window at 40000 now shows that each neuron
has developed weights concentrated in a small part of the input space,
matching a prototypical input at one location:

<p class='center'>
<img src="images/som_projection_040000.png" alt="Projection window at 40000"
align="middle" WIDTH="496" HEIGHT="505">
</p>

For this particular example, the topographic mapping for the x
dimension happens to be in the same orientation as the retina, while
the mapping for the y dimension is flipped so that the neurons along
the top edge of V1 respond to the bottom edge of the retina.  Nothing
in the network drives it to have any particular overall orientation or
mapping apart from aligning to the square shape, and the map may turn
out to be flipped or rotated by 90 degrees along any axis with
equivalent results.

<P><LI>Now, re-run the basic simulation by quitting and restarting
Topographica.  This time, change one of the parameter values, either
by editing the <code>som_retinotopy.ty</code> file before starting, or
by providing it on the command line before the script name (for those
parameters set via global_params).  For
instance, the starting value of the neighborhood radius (from which
all future values are calculated according to exponential decay) is
1.0.  You can change this value as you see fit, e.g. to 0.1, by
passing <code>-p radius_0=0.1</code> on the command line
<emph>before</emph> the .ty file.  With such a small learning radius,
global ordering is unlikely to happen, and one can expect the
topographic grid not to flatten out (despite local order in patches).
<br>

<P>Similarly, consider changing the initial learning rate from
<code>0.42</code> to e.g. <code>1.0</code> (e.g. by passing <code>-p
alpha_0=1.0</code> on the command line).  The retina and V1 densities
cannot be changed after the simulation has started, but again, they
can be changed by providing their values on the command line as above
(or by editing the <code>som_retinotopy.ty</code> file) and starting
Topographica again.

<P>You can also try changing the input_seed ("-p input_seed=XX"), to
get a different stream of inputs, or weight_seed ("-p
weight_seed=XX"), to get a different set of initial weights.
With some of these values, you may encounter cases where the SOM
fails to converge even though it seems to be working properly
otherwise.  For instance, some seed values result in topological
defects like a 'kink':

<p class='center'>
<IMG WIDTH="420" HEIGHT="474" SRC="images/som_grid_kink.png" align="middle" alt="Grid with a kink">
</p>

<P>This condition represents a local optimum from which the network
has difficulty escaping, where there is local order over most of the
map except for a discontinuity.

<P>Finally, you could change the input pattern to get a different type
of map.  E.g. if an oriented pattern is used, with random
orientations, neurons will become selective for orientation and not
just position.  <!--See the <code>examples/obermayer_pnas90.ty</code> file
for more details, though that simulation is quite
processor-intensive compared to this one. --> In general, the map
should form a representation of the dimensions over which the input
varies, with each neuron representing one location in this space, and
the properties of nearby neurons typically varying smoothly in all
dimensions.

</ol>

<h2>Exploring further</h2>

<p> To see how the example works, load the som_retinotopy.ty file into a
text editor and see how it has been defined, then find the
corresponding Python code for each module and see how that
has been defined.   

<P>Topographica comes with additional examples, and more are
always being added.  
Any valid Python code can be used to control and extend Topographica;
documentation for Python and existing Topographica commands can be
accessed from the <span class='t_item'>Help</span> menu of the <span
class='w_title'>Topographica Console</span> window.  <p> Please
contact
<A HREF="mailto:&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107?subject=Comments%20on%20Topographica%20tutorial">&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107</a>
if you have questions or suggestions about the software or this
tutorial.  </p>
