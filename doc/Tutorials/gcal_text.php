<H1>GCAL Orientation Map</H1>

<p>
This tutorial shows how to use the
<a target="_top" href="http://topographica.org/">Topographica</a> software package
to explore a simple orientation map simulation using test patterns and
weight plots. 

<P>We will use the <!--CEBALERT: need to link to publication when it comes out-->
GCAL model (paper to appear), which is related to the
<a target="_top" href="http://homepages.inf.ed.ac.uk/jbednar/research.html">LISSOM
model</a> but works more robustly with fewer parameters thanks to 
including contrast gain control (GC) in the LGN and homeostatic
adaptation (A) in V1. Although we focus on one model in this tutorial,
Topographica provides support for many other models and is easily
extensible for models not yet supported.
</p>

<p>This tutorial assumes that you have already followed the
instructions for <a target="_top" href="../Downloads/index.html">obtaining and
installing</a> Topographica. Also, you will need to generate a saved
orientation map network (a .typ file), which can be done from a
Unix or Mac  terminal or Windows <A HREF="../Downloads/win32notes.html">command
prompt</A> by running
<blockquote><code class='to_type'>topographica -a -c "generate_example('gcal_10000.typ')"</code></blockquote>


<P>Depending on the speed of your machine, you may want to go get a
snack at this point; on a 3GHz machine this training process
currently takes about 12 minutes.
<!--cortex: 11:24 -->
When training completes, gcal_10000.typ will be saved in
Topographica's <A HREF="../User_Manual/scripts.html#outputpath">output
path</A> ready for use in the tutorial.</p>



<h2>Response of an orientation map</h2>

In this example, we will load a saved network and test its behavior by
presenting different visual input patterns.

<ol> 
<p></p>
<li>First, start the Topographica GUI from a terminal:
<blockquote><code class='to_type'>
  topographica -g
  </code></blockquote>
<p>(Windows users can instead double click on the desktop Topographica icon.)<br>This will open the Topographica console:</p>

<p class='center'>
<img src="images/topographica_console.png" alt="Console Window"
align="middle" WIDTH="409" HEIGHT="127">
</p>
<p>
The window and button style will differ on different platforms, but
similar buttons should be provided.
</p>
<p></p>
</li>
<li> Next, load the saved network by selecting
selecting <span class='t_item'>Load snapshot</span> from the
<span class='t_item'>Simulation</span> menu and selecting
<code>gcal_10000.typ</code>. 
This small orientation map simulation should load in a few seconds,
with a 78x78 retina, a 60x60 LGN (composed of one 60x60 OFF channel
sheet, and one 60x60 ON channel sheet), and a 48x48 V1 with about two
million synaptic weights. The architecture can be viewed in
the <span class='w_title'>Model Editor</span> window (which can be
selected from the <span class='t_item'>Simulation</span> menu), but is
also shown below:
<!--CEBALERT: image needs to be created properly!-->
<p class='center'>
<img src="images/gcal_network_diagram.png" alt="LISSOM network"
align="middle" WIDTH="600" HEIGHT="461">
</p>

<p></p>
</li>

<li> To see how this network responds to a simple visual image,
first open an <a name="Activity-plot"><span
class='t_item'>Activity</span></a> window from
the <span class='t_item'>Plots</span> menu on the <span
class='w_title'>Topographica Console</span>, then 
select <span class='t_item'>Test pattern</span> from the <span
class='t_item'>Simulation</span> menu to get the 
<span class='w_title'>Test Pattern</span> window:

<p class='center'>
<img src="images/gcal_test_pattern.png" alt="Test Pattern window"
align="middle" WIDTH="315" HEIGHT="720">
</p>

<p>
Then select a <span class='t_item'>Line</span> <span
class='t_item'>Pattern generator</span>, and hit <span
class='b_press'>Present</span> to present a horizontal line to the
network.  
</p>

<p></p>
</li>

<li>The <a name="Activity-plot"><span class='w_title'>Activity</span></a> 
window should then show the result:
<p class='center'>
<img src="images/gcal_activity_010000.png" alt="Response to a line"
align="middle" WIDTH="660" HEIGHT="359">
</p>

<P>This window shows the response for each neural area. For now, please 
turn on <span class='t_item'>Normalize</span>
and <span class='t_item'>Strength only</span> (both are usually off by
default).
<!--Considering whether to make initial lgn response visible in the model-->

<P>As you move your mouse over the plots, information about the
location of the mouse cursor is displayed in the status bar at the
bottom of the window. For these plots, you can see the
<a target="_top" href="../User_Manual/space.html#matrix-coords">matrix
coordinates</a> (labeled "Unit"),
<a target="_top" href="../User_Manual/space.html#sheet-coords">sheet coordinates</a>
(labeled "Coord"), and the activity level of the unit currently under
the pointer.

</p><p>In the <span class='t_item'>Retina</span> plot, each
photoreceptor is represented as a pixel whose shade of gray codes the
response level, increasing from black to white.  This pattern is what
was specified in the <span class='w_title'>Test Pattern</span> window.
Similarly, locations in the LGN that have an OFF or ON cell response
to this pattern are shown in the <span class='t_item'>LGNOff</span> and
<span class='t_item'>LGNOn</span> plots.  
At this stage the response level in <span class='t_item'>V1</span> is
also coded in shades of gray, and the numeric values can be found
using the pointer.

<P>From these plots, you can see that the single line presented on the
retina is edge-detected in the LGN, with ON LGN cells responding to
areas brighter than their surround, and OFF LGN cells responding to
areas darker than their surround.  In V1, the response is patchy, as
explained below.
</p>

<p></p>
</li>

<li> To help understand the response patterns in V1, we can look at
the weights to V1 neurons.  These weights were learned previously, 
as a result of presenting 10000 pairs of oriented Gaussian patterns at random angles
and positions.  To plot a single neuron, select
<a name="ConnectionFields-plot"><span class='t_item'>Connection
Fields</span></a> from the <span class='t_item'>Plots</span>
menu. This will plot the synaptic strengths of connections to the
neuron in the center of the cortex (by default):

<p class="center">
<img src="images/gcal_cf_center_010000.png" alt="CF of center neuron"
align="middle" WIDTH="660" HEIGHT="421">
</p>

<P>Again, for now please turn on <span class='t_item'>Strength
only</span>; it is usually off by default.  Here we have selected a
neuron slightly above the center, because it happened to be more
selective than the one at the exact center.

<p> The plot shows the afferent weights to V1 (i.e., connections from
the ON and OFF channels of the LGN), followed by the lateral
excitatory and lateral inhibitory weights to that neuron from nearby
neurons in V1. The afferent weights represent the retinal pattern that
would most excite the neuron.  For the particular neuron shown above,
the optimal retinal stimulus would be a short, bright line oriented at
about 35 degrees (from 7 o'clock to 1 o'clock) in the center of the
retina. (Note that the particular neuron you are viewing may have a
different preferred orientation.)
</p><p></p></li>

<li>If all neurons had the same weight pattern, the response
would not be patchy -- it would just be a blurred version of the
input (for inputs matching the weight pattern), or blank (for other
inputs). To see what the other neurons look like, select 
<a name="Projection-plot"><span class='t_item'>Projection</span></a>
from the <span class='t_item'>Plots</span> menu, then select <span
class='t_item'>LGNOnAfferent</span> from the drop-down <span
class='t_item'>Projection</span> list, followed by the refresh
arrow next to 'Pre plot hooks':
  

<p class="center">
<img src="images/gcal_projection_010000.png" alt="Afferent weights of many neurons"
align="middle" WIDTH="579" HEIGHT="434">
</p>

This plot shows the afferent weights from the LGN ON sheet for every fifth neuron in each
direction.  You can see that most of the neurons are selective
for orientation (not just a circular spot), and each has a slightly
different preferred orientation.  This suggests an explanation for why
the response is patchy: neurons preferring orientations other than
the one present on the retina do not respond.  You can also look at
the <span class='t_item'>LateralInhibitory</span> weights instead of
<span class='t_item'>LGNOnAfferent</span>; those are patchy as well because the typical
activity patterns are patchy.

</p><p></p></li><li>To visualize all the neurons at once
in experimental animals, optical imaging experiments measure responses
to a variety of patterns and record the one most effective at stimulating each
neuron.  The results of a similar procedure can be viewed by selecting
<span class='t_item'>Plots</span> > <span class='t_item'>Preference Maps</span> >
<a name="OrientationPreference-plot"><span class='t_item'>Orientation Preference</span></a>:

<p class="center">
<img src="images/gcal_or_pref_010000.png" alt="Orientation map"
align="middle" WIDTH="607" HEIGHT="400">
</p><br>

<P>
The <span class='t_item'>Orientation Preference</span> plot
is the orientation map for V1 in this model.
Each neuron in the plot is color coded by its preferred orientation,
according to the key shown to the left of the plot.
(If viewing a monochrome printout, see web page for the colors).
Note that phase preference and selectivity are also displayed in the
window, but these are not analyzed here (and are not shown above).
</p>

<P> You can see that nearby neurons have similar orientation
preferences, as found in primate visual cortex. The <span
class='t_item'>Orientation Selectivity</span> plot shows the relative
selectivity of each neuron for orientation on an arbitrary scale; you
can see that in this simulation nearly all neurons became orientation
selective.  The <span class='t_item'>Orientation
Preference&Selectivity</span> plot shows the two other Orientation
plots combined -- each neuron is colored with its preferred
orientation, and the stronger the selectivity, the brighter the color.
In this case, because the neurons are strongly selective, the
Preference&Selectivity plot is nearly identical to the Preference plot.

<P>
<!--CB: I think 'hook' is worse than 'command' in this context--> If
you want to see what happens during map measurement, you can watch the
procedure as it takes place by enabling visualization. Edit the 'Pre
plot hooks' (as described in
the <A HREF="../User_Manual/plotting.html#changing-existing-plots">User
Manual</A>) so that the
<?php classref('topo.command.analysis','measure_sine_pref') ?>
 command's <code>display</code> parameter is turned on. Open an
Activity window and ensure it has Auto-Refresh turned on, then press
Refresh by the Orientation Preference window's 'Pre plot hooks'. You
will see a series of sine gratings presented to the network, and can
observe the response each time in the LGN and V1 sheets.  When you are
done, press Refresh on the pre-plot hooks in the Activity window to
restore the original activity pattern plots.
</p><p>
</p></li>

<li>Now that we have looked at the orientation map, we can see more clearly
why activation patterns are patchy by coloring each neuron with its
orientation preference.  To do this, make sure that <span
class='t_item'>Strength only</span> is now turned <i>off</i> in the 
<span class='w_title'>Activity</span> window:

<p class="center">
<img src="images/gcal_activity_010000_or.png" alt="Color-coded response to a line"
align="middle" WIDTH="660" HEIGHT="359"><br />
<img src="images/or_key_horiz_transparent.png" alt="Orientation key" height="23" width="288">
</p><br>

<p>Each V1 neuron is now color coded by its orientation, with brighter
colors indicating stronger activation.  Additionally, the status bar
beneath the plots now also shows the values of the separate channels
comprising the plot: OrientationPreference (color),
OrientationSelectivity (saturation), and Activity (brightness).

<P>
The color coding allows us to see that the neurons responding are
indeed those that prefer orientations similar to the input pattern,
and that the response is patchy because other nearby neurons do not
respond.  To be sure of that, try selecting a line with a different
orientation, and hit present again -- the colors should be different,
and should match the orientation chosen.
</p>
<p></p>
</li>

<li>If you now turn off <span class='t_item'>Strength only</span>
in the <span class='w_title'>Connection Fields</span>
window, you can see that the neuron whose weights we plotted is
located in a patch of neurons with similar orientation preferences: 

<p class="center">
<img src="images/gcal_cf_center_010000_or.png" alt="Colorized weights of one neuron"
align="middle" WIDTH="660" HEIGHT="421"><br />
<img src="images/or_key_horiz_transparent.png" alt="Orientation key" height="23" width="288">
</p><br>

<P> Look at the <span class='t_item'>LateralExcitatory</span> weights,
which show that the neurons near the above neuron are nearly all
yellow-green, to match its preferred orientation.

<P>
Returning to the <span class='w_title'>Test pattern</span> window,
try presenting a vertical line
(<span_class='t_item'>orientation</span> of <code>pi/2</code>) and
then, in the <span class='w_title'>Activity</span> window, right click
on one of the cyan-colored patches of activity. This will bring up a menu:

<p class="center">
<img src="images/lissom_oo_or_activity_rightclick.png" alt="Right-click menu"
align="middle" WIDTH="444" HEIGHT="125" >
</p><br>

<!--CB: should probably be a list-->
<P>The menu offers operations on different parts of the plot:
the first submenu shows operations available on the single selected unit, and
the second shows operations available on the combined (visible) plot. The final
three submenus show operations available on each of the separate channels that
comprise the plot.

<P>Here we are interested to see the connection fields of the unit we selected,
so we choose <span class='t_item'>Connection Fields</span> from the 
<span class='t_item'>Single unit</span> submenu to get a new plot:

<p class="center">
<img src="images/gcal_cf_vertical_010000_or.png" alt="Colorized weights of one neuron"
align="middle" WIDTH="660" HEIGHT="421"><br />
<img src="images/or_key_horiz_transparent.png" alt="Orientation key" height="23" width="288">
</p><br>

<P>This time we can see from the <span class='t_item'>LateralExcitatory</span> weights
that the neurons near this one are all colored cyan (i.e., are selective for vertical).
</li>

<li>
<P>
Right-click menus are available on most plots, and provide a convenient
method of further investigating and understanding the plots. For instance,
on the <span class='w_title'>Orientation Preference</span> window, the 
connection fields of units at any location can easily be visualized, 
allowing one to see the connection fields of units around different features of the map.
<!-- ...do we want to go further or is this tutorial already ready to split into
more optional sections? -->


<P>As another example, an interesting property of orientation maps
measured in animals is that their Fourier spectrums usually show a
ring shape, because the orientations repeat at a constant spatial
frequency in all directions. Selecting <span class='t_item'>Hue
channel: OrientationPreference</span> > <span class='t_item'>Fourier
transform</span> from the right-click menu allows us to see the same
is true of the map generated by the GCAL network:


<p class="center">
<img src="images/gcal_ormap_ft.png" alt="FT of orientation preference map"
align="middle" WIDTH="416" HEIGHT="470">
</p><br>

</li>

<P>Other right-click options allow you to look at the gradient of each
plot (showing where the values change most quickly across the
surface) or the histogram (showing the distribution of values in the
plot), plot it in a separate window or as a 3D wireframe, or to save
the images to disk.

<li> Now that you have a feel for the various plots, you can try
different input patterns, seeing how the cortex responds to each one.
Just select a <span class='t_item'>Pattern generator</span>, e.g.
<span class='t_item'>Gaussian</span>,
<span class='t_item'>Disk</span>, or <span
class='t_item'>SineGrating</span>, and then hit
<span class='b_press'>Present</span>.

<p> For each <span class='t_item'>Pattern generator</span>, you can change various parameters that
control its size, location, etc.:

</p><blockquote>
<dl compact="compact">
<dt><span class='t_item'>orientation</span></dt><dd> controls the angle (try pi/4 or -pi/4)
</dd><dt><span class='t_item'>x</span> and <span class='t_item'>y</span></dt><dd> 
control the position on the retina (try 0 or 0.5)
</dd><dt><span class='t_item'>size</span></dt><dd>
controls the overall size of e.g. Gaussians and rings
</dd><dt><span class='t_item'>aspect_ratio</span> </dt><dd>
controls the ratio between width and height; will be scaled by the
  size in both directions
</dd><dt><span class='t_item'>smoothing</span>
</dt><dd> controls the amount of Gaussian falloff around the edges of patterns such as rings and lines
</dd><dt><span class='t_item'>scale</span>
</dt><dd> controls the brightness (try 1.0 for a sine grating).  Note
how this model is insensitive to the scale; the response remains orientation
selective even as the scale is varied substantially. (If you try the <a target="_top" href="lissom_oo_or.html">lissom_oo_or
tutorial</a>, you can see the effect of contrast gain control operating in this 
model.)
</dd><dt><span class='t_item'>offset</span></dt><dd> is added to every pixel
</dd><dt><span class='t_item'>frequency</span>
</dt><dd> controls frequency of a sine grating or Gabor 
</dd><dt><span class='t_item'>phase</span></dt><dd> controls phase of a sine grating or Gabor 
</dd><dt><span class='t_item'>mask_shape</span></dt><dd> allows the
pattern to be masked by another pattern (e.g. try a mask_shape of
Disk or Ring with a SineGrating or UniformRandom pattern).  The
parameters of the mask_shape pattern can be edited by right-clicking on it.
</dd></dl>
</blockquote>
</p>

<p> 
To present photographs, select a <span class='t_item'>Pattern generator</span> of type
<span class='t_item'>FileImage</span>. (You can type the path to an
image file of your own (in e.g. PNG, JPG, TIFF, or PGM format) in
the <span class='t_item'>filename</span> box.) For most photographs,
you will probably want to enlarge the image size to look at details.
A much larger, more complicated, and slower map would be required to
see interesting patterns in the response to most images, but even with
this network you may be able to see some orientation-specific
responses to large contours in the image:
</p>

<p class="center">
<img src="images/gcal_natural_image_oo_or.png" alt="Ellen Arthur"
align="middle" WIDTH="579" HEIGHT="365"><br />
</p>

<P>Here we have enabled <span class='t_item'>Sheet coords</span>
so that each plot will be at the correct size relative to each other.
That way, the location of a given feature can be compared between
images.  In this particular network, the Retina and LGN stages each
have an extra "buffer" region around the outside so that no V1 neuron
will have its CF cut off, and the result is that V1 sees only the
central region of the image in the LGN, and the LGN sees only the
central region of the retina.  
(<a target="_top" href="../User_Manual/space.html#sheet-coords">Sheet coordinates</a>
are normally turned off because they make the cortical plots smaller, but they can
be very helpful for understanding how the sheets relate to each
other.)  </p></li>

<li>The procedure above allows you to explore the relationship between
the input and the final response after the cortex has settled due to
the lateral connections.  If you want to understand the settling
process itself, you can also visualize how the activity propagates
from the retina to the LGN, from the LGN to V1, and then within V1.
To do this, first make sure that there is an <span
class='t_item'>Activity</span> window open, with Auto-refresh enabled.  
Then go to the console window and hit "Step" repeatedly. After an
input is presented, you will see the activity arrive first in the LGN,
then change in the LGN, then appear in V1, and then gradually change
within V1. (You might want to turn on Normalize to see some features
more easily, although this can make others more difficult to see.)
The Step button moves to the next scheduled event in the simulation,
which are at even multiples of 0.05 for this particular simulation.
You can also type in the specific duration (e.g. 0.05) to move forward
into the "Run for:" box, and hit "Go" instead.

<P>As explained in the
<A HREF="../User_Manual/time.html">User Manual</A>,
this process is controlled by the network structure and the delays
between nodes.  For simplicity, let's consider time starting at zero.
The first scheduled event is that the Retina will be asked to draw an
input pattern at time 0.05 (the phase of the
<?php classref('topo.sheet','GeneratorSheet') ?>).  Thus
the first visible activity occurs in the Retina, at 0.05.  The
Retina is connected to the LGN with a delay of 0.05, and so the LGN
responds at 0.10.
The LGN has self connections with a delay of 0.05, so the next event
is the LGN settling at 0.15 (the gain control step).
After this step, V1 is initially activated at 0.20.
V1 also has self connections with a delay of 0.05, and so V1 is then
repeatedly activated every 0.05 timesteps.  Eventually, the number of
V1 activations reaches a fixed limit for GCAL (usually about 16
timesteps), and no further events are generated or consumed until the
next input is generated at time 1.05.  Thus the default stepsize of
1.0 lets the user see the results after each input pattern has been
presented and the cortex has come to a steady state, but results can
also be examined at a finer timescale.  Be sure to leave the time
clock at an even multiple of 1.0 before you do anything else, so that
the network will be in a well-defined state.  (To do this, just type
the fractional part into the "Run for:" box, i.e. 0.95 if the time is
currently 10002.05, press "Go", and then change "Run for:" to 1.0.)
</li> </ol>



<h2>Learning (optional)</h2>

The previous examples all used a network trained previously, without
any plasticity enabled.  Many researchers are interested in the
processes of development and plasticity.  These processes can be
studied using the GCAL model in Topographica as follows.

<p>
</p><ol>

<p></p><li>First, quit from any existing simulation, and
<A HREF="../User_Manual/scripts.html#copy_examples">get a copy of the
example files to work with</A> if you do not have them already.  Then
start a new run of Topographica:

<blockquote><code class='to_type'>
  topographica -g
  </code></blockquote>
<p></p>

From the Simulation menu, select Run Script. Then from the <code>examples</code> directory, open <code>gcal.ty</code>.
<p></p></li><li>Next, open an <span class='w_title'>Activity</span> window 
and make sure that it has <span class='t_item'>Auto-refresh</span> enabled.  Unless your machine is 
very slow, also enable <span class='t_item'>Auto-refresh</span> in a
<span class='w_title'>Projection</span> window showing <span
class='t_item'>LGNOnAfferent</span>.  On a very fast machine you could
even <span class='t_item'>Auto-refresh</span> an <span class='w_title'>Orientation Preference</span> window
(probably practical only if you reduce the nominal_density of V1).

<p></p></li><li>Now hit Go a few times on the <span
class='w_title'>Topographica Console</span> window, each time looking
at the random input(s) and the response to them in the <span
class='w_title'>Activity</span> window.  The effect on the network
weights of learning this input can be seen in the <span
class='w_title'>Projection</span> window.

<p></p></li><li>With each new input, you may be able to see small
changes in the weights of a few neurons in the <span
class='t_item'>LGNOnAfferent</span> array (by peering closely).  If
the changes are too subtle for your taste, you can make each input
have an obvious effect by speeding up learning to a highly implausible
level.  To do this, open the <span class='w_title'>Model Editor</span>
window, right click on the LGNOnAfferent projection (the cone-shaped
lines from LGNOn to V1), select Properties, and change Learning Rate
from the default 0.1 to 100, press Apply, and then do the same for
the LGNOffAfferent projection.
<!--
You can also do the same from the
terminal, or from the <span class='w_title'>Command Prompt</span>
window available from the <span class='t_item'>Simulation</span> menu:

<blockquote><code class='to_type'>
topo.sim['V1'].projections('LGNOnAfferent').learning_rate=100
topo.sim['V1'].projections('LGNOffAfferent').learning_rate=100
</code></blockquote>
-->

Now each new pattern generated in a
training iteration will nearly wipe out any existing weights.

<p></p></li><li>For more control over the training inputs, open the 
<span class='w_title'>Test Pattern</span> window, select a
<span class='t_item'>Pattern generator</span>, e.g. <span class='t_item'>Disk</span>, and other
parameters as desired.  Then enable <span class='t_item'>Plastic</span> in that
window, and hit <span class='b_press'>Present</span>.  You should again see how
this input changes the weights, and can experiment with different inputs.

<p><li>Once you have a particular input pattern designed, you can see
how that pattern would affect the cortex over many iterations.  To do
so, open a <span class='w_title'>Model Editor</span> window and right click on the Retina's diagram, then
select <span class='t_item'>Properties</span> from the resulting menu. In the <span class='w_title'>Parameters of Retina</span> window
that opens, select the pattern type you want to use for the <span
class='t_item'>Input Generator</span> item, and then right click on
that pattern, choose <span class='t_item'>Properties</span> and, in the new window, modify any of its parameters as you wish. Note that
you will probably want to have dynamic values for certain
parameters. For instance, to have a random orientation for each
presentation, right click on <span class='t_item'>Orientation</span> and select <span class='t_item'>Enter dynamic
value</span>.  The slider will disappear from the entry box, and you can
type in an expression such as
<code>numbergen.UniformRandom(lbound=-pi,ubound=pi)</code>.
When you have finished configuring your pattern, press
<span class='b_press'>Apply</span> or <span class='b_press'>Close</span> on the <span class='w_title'>Parameters of Gaussian</span> window. Having now set up the
input generator on the <span class='w_title'>Parameters of Retina</span> window, click <span class='b_press'>Apply</span> or
<span class='b_press'>Close</span> on this too. Now when you press <span class='b_press'>Go</span> on the console window
(assuming <span class='t_item'>Run for</span> is set to 1), you should see your pattern being
presented in the Activity Window.

<p></p></li><li>After a few steps (or to do e.g. 20 steps in a row,
change <span class='t_item'>Run for</span> to 20 and press return) you
can plot (or refresh) an <span class='w_title'>Orientation
Preference</span> map to see what sort of orientation map has
developed.  (Press the 'Refresh' button next to the <span
class='t_item'>Pre plot hooks</span> if no plot is visible when
first opening the window.  Measuring a new map will usually take about
15 seconds to complete.)  If you've changed the learning rate to a
high value, or haven't presented many inputs, the map will not
resemble actual animal maps, but it should still have patches
selective for each orientation.
<p></p></li>


<li>If you are patient, you can even run a full, more realistic,
simulation with your favorite type of input. To do this, quit and
start again, then change the Retina's <span class='t_item'>Input
generator</span> as before via the Model Editor, but make sure not to
change the learning rate this time.  Then you can change <span
class='t_item'>Run for</span> to 10000 and press <span
class='b_press'>Go</span> to see how a full simulation would work
with your new inputs.  <!--If you hit the <span
class='b_press'>Activity</span> button ** while it's training, you'll
see a window pop up when it's done (which will be at least several
minutes, for recent machines, or even longer with older machines).-->
Running for 10000 iterations will likely take at least several minutes
for recent machines; if you are less patient, try doing 1000
iterations at a time instead before looking at an
<span class='w_title'>Orientation Preference</span> map.<p></p></li>

<p><li> If you are <em>really</em> patient, you can change the number
of units to something closer to real primate cortex, by quitting
and then restarting with a higher density in V1. To do this, you will need
to specify the example script from the commandline. The path of the
gcal.ty script was printed by Topographica in step 1 of this
Learning section, but if you are not sure where the examples are
located, you can find out by first running

<blockquote><code class='to_type'>
  topographica -c "from topo.misc.genexamples import print_examples_dir; print_examples_dir()"
  </code></blockquote>

Then you can use the path to the example, as well as specifying a higher cortex density:
<blockquote><code class='to_type'>
  topographica -p cortex_density=142 ~/Documents/Topographica/examples/gcal.ty -g
  </code></blockquote>
(<code>~/Documents/Topographica</code> should be replaced with
<code>~/topographica</code> for release 0.9.7 and earlier; Windows
users should refer to our <A
HREF="../Downloads/win32notes.html">command prompt</A> notes).
<p></p>
  
You'll need about a gigabyte of memory and a lot of time, but you can then step
through the simulation as above.  The final result after 10000
iterations (requiring several hours on a 3GHz machine) should be a much
smoother map and neurons that are more orientation selective.  Even
so, the overall organization and function should be similar.
</li>

<!--CEB: not sure if this is worth mentioning yet...
because the history buttons don't quite work perfectly with
or pref windows and because it's current work-->
<!--
<p></p>

<li>
Finally, you might also be interested in observing in more detail how
the orientation map develops over time. c.f. lissom_oo_or, which
starts with big patches that shrink (exc rad shrink vs
homeost);lissom_oo_or map dev less stable
? could include tuning curve width scale invariance
</li>
-->

</ol>


<h2>Exploring further</h2>

<p> To see how the example works, load the gcal.ty file into a
text editor and see how it has been defined, then find the
corresponding Python code for each module and see how that
has been defined.   

<p>Topographica comes with additional examples, and more are
always being added.  In particular, the above examples work
in nearly the same way with the older <code>lissom_or.ty</code> and
<code>lissom_oo_or.ty</code> models.
Any valid Python code can be used to control and extend Topographica;
documentation for Python and existing Topographica commands can be
accessed from the <span class='t_item'>Help</span> menu of the <span
class='w_title'>Topographica Console</span> window.  <p> Please
contact
<A HREF="mailto:&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107?subject=Comments%20on%20Topographica%20tutorial">&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107</a>
if you have questions or suggestions about the software or this
tutorial.  </p>
