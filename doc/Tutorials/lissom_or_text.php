<H1>LISSOM Orientation Map</H1>

<!-- TO DO: fix indentation; make standards-compliant so it will -->
<!-- display properly on different browsers (I'll fix spacing at the -->
<!-- same time); sort blockquotes -->

<p>
This tutorial shows how to use the
<a target="_top" href="http://topographica.org/">Topographica</a> software to explore a
simple orientation map simulation using weight plots and test pattern
images.  This particular example uses a
<a target="_top" href="http://nn.cs.utexas.edu/keyword?rflissom">LISSOM model</a>
cortex, although Topographica provides support for many other models
and is easily extensible for models not yet supported.

</p>

<p>This tutorial assumes that you have already followed the
instructions for <a target="_top" href="../Downloads/index.html">obtaining and
installing</a> Topographica.  Also, you will need to generate a saved
orientation map network, which can be done by changing to the
<code>examples/</code> directory and running "make
lissom_or_20000.typ".  Depending on the speed of your machine, you
may want to go out for coffee at this point; on a 3GHz machine
this training process currently takes about forty minutes.
</p>


<h2>Response of an orientation map</h2>

In this example, we will load a saved network and test its behavior by
presenting different visual input patterns.

<ol> 
<p></p>
<li>First, change to your topographica directory, e.g.:

<blockquote><code class='to_type'>cd ~/Documents/Topographica/</code></blockquote>
<p></p>
</li>

<li> Next, start the Topographica GUI:
<blockquote><code class='to_type'>./topographica -g</code></blockquote>
<p></p>
You should see a new window for the GUI:
<p class='center'>
<img src="images/topographica_console.png" alt="Console Window"
align="middle" width="496" height="215">
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
<code>lissom_or_20000.typ</code> in the examples/ directory. This
simulation is a small orientation map, with a 24x24
retina and a 48x48 V1 with about two million
synaptic weights. The architecture can be viewed in the <span class='w_title'>Model Editor</span> window (which can be selected from the <span class='t_item'>Simulation</span> menu), but is also shown below:
<p class='center'>
<img src="images/lissom_network_diagram.png" alt="LISSOM network."
align="middle" width="270" height="397">
</p>

<p></p>
</li>

<li> To see how this network responds to a simple visual image,
select <span class='t_item'>Test pattern</span> from the <span class='t_item'>Simulation</span> menu to get the
<span class='w_title'>Test Pattern</span> window, select a <span class='t_item'>Line</span> <span class='t_item'>Input type</span>, then hit <span class='b_press'>Present</span>:

<p class='center'>
<img src="images/test_pattern.png" alt="Test Pattern window"
align="middle" width="342" height="612">
</p>

<p>
This will present a horizontal line.  
</p>

<p></p>
</li>

<li>To see the result, select <span class='t_item'>Activity</span> from
the <span class='t_item'>Plots</span> menu on the <span class='w_title'>Topographica Console</span> to get:
<p class='center'>
<img src="images/activity_line.png" alt="Response to a line" align="middle" width="426" height="340">
</p>



This window shows the response for each neural area, <span
class='t_item'>Retina</span> on the left
and <span class='t_item'>V1</span> on the right.  

</p><p>In the <span class='t_item'>Retina</span> plot, each photoreceptor is represented as
a pixel whose shade of grey codes the response level, increasing from black to
white.  These patterns are what was specified in
the <span class='w_title'>Test Pattern</span> window. At this stage, in V1, the response
level is also coded in shades of grey. Note that the response is patchy, as
explained below.

</p>

<p></p>
</li>

<li> To help understand the response patterns in V1, we can look at
the weights to V1 neurons.  These weights were learned previously, by
presenting 20000 inputs like the one we just saw but at random angles
and positions.  To plot a single neuron, select 
<span class='t_item'>Unit weights</span> from the <span class='t_item'>Plots</span> menu. This will plot the synaptic strengths of
the neuron in the center of the cortex by default. On this particular map, this neuron is not clearly selective for a particular orientation. Instead, try for example the unit at x=0.2 and y=0.0 by changing <span class='t_item'>Unit X:</span> to 0.2:



<p class="center">
<img src="images/unit_weights_0.2_0.0.png" alt="Weights of one
neuron" align="middle" width="576" height="348">
</p>

<p>
The plot shows the afferent weights to V1 (i.e., connections from the
retina), followed by the  lateral excitatory and lateral inhibitory
weights to that neuron from nearby neurons in V1. The afferent
weights represent the retinal pattern that would most excite the neuron.
For this particular neuron, the optimal retinal stimulus would be a
bright line oriented at about -45 degrees (10 o'clock) to the right
of the retina's center.
</p><p></p></li><li>If all neurons had the same weight pattern, the response
would not be patchy -- it would just be a blurred version of the
input (for inputs matching the weight pattern), or blank (for other
inputs). To see what the other neurons look like, select <span class='t_item'>Projection</span> from the <span class='t_item'>Plots</span> menu:

<p class="center">
<img src="images/projection.png" alt="Afferent weights of many
neurons" align="middle" width="623" height="499">
</p>

This plot shows the afferent weights for every seventh neuron in each
direction.  You can see that most of the other neurons are selective
for orientation (not just a circular spot), and each has a slightly
different preferred orientation.  This suggests an explanation for why
the response is patchy: neurons preferring orientations other than
the one present on the retina do not respond.  You can also look at
the <span class='t_item'>LateralInhibitory</span> weights instead of
<span class='t_item'>Afferent0</span>; those are patchy as well because the typical
activity patterns are patchy.

</p><p></p></li><li>To visualize all the neurons at once
in experimental animals, optical imaging experiments measure responses
to a variety of patterns and record the one most effective at stimulating each
neuron.  A similar procedure can be performed in the model by selecting
<span class='t_item'>Orientation Preference</span> from the <span class='t_item'>Plots</span> menu:

<p class="center">
<img src="images/or_map.png" alt="Orientation map" width="553" height="292">
<br />
<img src="images/or_key_horiz_transparent.png" alt="Orientation key" height="23" width="288">
</p><br>


<P>
(This will usually take about 30 seconds to complete.)
The plot on the left is the orientation map for V1 in this network.
Each neuron in the plot is color coded by its preferred orientation,
according to the key beneath the image.
(If viewing a monochrome printout, see web page for the colors).
</p>

<p>
You can see that nearby neurons have similar orientation preferences,
as found in primate visual cortex. The V1 plot on the right shows the
relative selectivity of each neuron for orientation; you can see that
there are patches of neurons near the borders that are not very
orientation selective, and smaller patches in the center, but that
most are selective.  The V1 plot in the center shows the two
previously mentioned plots combined -- each neuron is colored with its
preferred orientation, and the stronger the selectivity, the brighter
the color.  From this plot it is clear that the unselective patches
tend to lie between patches of different colors (i.e. different
preferred orientations).

</p><p>
</p></li>

<li>Now that we have the orientation map, we can see more clearly
why activation patterns are patchy by pressing <span class='b_press'>Present</span>
on the <span class='w_title'>Test pattern</span> window and then looking
at the refreshed image in the <span class='w_title'>Activity</span> window:

<p class="center">
<img src="images/activity_line_or.png" alt="Color-coded response to a line" width="426" height="340"><br />
<img src="images/or_key_horiz_transparent.png" alt="Orientation key" height="23" width="288">
</p><br>


(Alternatively, if you want to keep the old plot for comparison, you
can make sure that <span class='t_item'>Auto-refresh</span> is not enabled in it, then
generate a new plot by selecting <span class='t_item'>Activity</span> in the
<span class='t_item'>Plots</span> menu of the <span class='w_title'>Topographica Console</span> window.  This technique also applies to all of the other window types as well.)
</p>
<p> The V1 activity plots are colorized now that the orientation map
has been measured.  Each V1 neuron is now color coded by its
orientation, with brighter colors indicating stronger activation.  We
can now see that the neurons responding are indeed those that prefer
orientations similar to the input pattern, and that the response is
patchy because other nearby neurons do not respond.  To be sure of
that, try rotating the image by adjusting the orientation, then present 
it again -- the colors should be different, and match the orientation chosen.
</p>
<p></p>
</li>

<li> If you now <span class='b_press'>Refresh</span> the
<span class='w_title'>Unit weights</span>
window, you can see that the neuron whose weights we plotted is
located in a patch of neurons responding to similar orientations:


<p class="center">
<img src="images/unit_weights_0.2_0.0_or.png" alt="Colorized weights of
one neuron" align="middle" width="576" height="348" ><br />
<img src="images/or_key_horiz_transparent.png" alt="Orientation key" height="23" width="288">


</p>
<p>
Look at the <span class='t_item'>LateralInhibitory</span> weights, which show that
the neurons around the location to the right of the retina's center are primarily purple. 
</p>
<p></p></li>


<li> Now that you have a feel for the various plots, you can try
different input patterns, seeing how the cortex responds to each one.
Just select an <span class='t_item'>Input type</span>, e.g.  <span class='t_item'>Gaussian</span>,
<span class='t_item'>Disk</span>, or <span
class='t_item'>SineGrating</span>, and then hit
<span class='b_press'>Present</span>.

<p> For each <span class='t_item'>Input type</span>, you can change various parameters that
control its size, location, etc.:

</p><blockquote>
<dl compact="compact">
<dt><span class='t_item'>orientation</span>                          </dt><dd> controls the angle (try PI/4 or -PI/4)
</dd><dt><span class='t_item'>x</span> and <span class='t_item'>y</span>         </dt><dd> control the position on the retina (try 0 or 0.5)
</dd><dt><span class='t_item'>width</span> and
<span class='t_item'>height</span> </dt><dd>
control the width and height of e.g. Gaussians and rings
</dd><dt><span class='t_item'>smoothing</span>
</dt><dd> controls the amount of Gaussian falloff around the edges of patterns such as rings and lines
</dd><dt><span class='t_item'>scale</span>

</dt><dd> controls the brightness (try 0.5 for a sine grating).  Note
that this relatively simple model is very sensitive to the scale, and
scales higher than about 0.5 will result in a broad,
orientation-unselective response.  More complex models (and actual brains!)
are less sensitive to the scale or contrast.
</dd><dt><span class='t_item'>offset</span>                         </dt><dd> is added to every pixel
</dd><dt><span class='t_item'>frequency</span>
</dt><dd> controls frequency of a sine grating or Gabor 
</dd><dt><span class='t_item'>phase</span>                          </dt><dd> controls phase of a sine grating or Gabor 
</dd></dl>
</blockquote>
</p>

<!-- CEBHACKALERT: image support not yet completed -->
<!--
<p> 
(**update) To present photographs, select an <span class='t_item'>Input type</span> of
<span class='t_item'>Image</span>, then select one of the photographs in the
list at the bottom.  You can also type the path to a PGM file of your
own in the <span class='t_item'>filename:</span> box.  For most photographs you will
need to increase the <span class='t_item'>scale</span> to 1.5 or 2.0 to see any
response from this network.  A much larger (and slower) network would
be required to see detailed patterns in the response to most images,
but even with this network you can see some orientation-specific
responses to large contours in the image.  Be aware when comparing the
Retina and V1 plots for a photograph that each processing stage
eliminates some of the outer edges of the image, so that V1 is
only looking at the center of the image on the Retina.
</p></li></ol>
-->


<h2>Learning (optional)</h2>

The previous examples all used a network trained previously, without
any plasticity enabled.  Many researchers are interested in the
processes of development and plasticity.  These processes can be
studied using the LISSOM model in Topographica as follows.

<p>
</p><ol>

<p></p><li>First, quit from any existing simulation, and start with a fresh copy:

<blockquote><code class='to_type'>
  ./topographica examples/lissom_or.ty -g
  </code></blockquote>
<p></p>

<p></p></li><li>Next, open an <span class='w_title'>Activity</span> window 
and make sure that it has <span class='t_item'>Auto-refresh</span> enabled.  Unless your machine is 
very slow, also enable <span class='t_item'>Auto-refresh</span> in a
<span class='w_title'>Projection</span> window.  On a very fast machine you could
even <span class='t_item'>Auto-refresh</span> an <span class='w_title'>Orientation Preference</span> window
(highly optional).

<p></p></li><li>Now click the mouse into the <span class='t_item'>Learning iterations</span> field
of the <span class='w_title'>Topographica Console</span> window, and press return a few
times, each time looking at
the random input(s) and the response to them in the
<span class='w_title'>Activity</span> window.  The effect on the network weights of
learning this input can be seen in the <span class='w_title'>Projection</span>
window.

<p></p></li><li>With each new input, you should be able to see small changes in the
weights of a few neurons in the array (by peering closely).  If the changes are too subtle for your taste,
you can make each input have a obvious effect by speeding up learning
to a highly implausible level.  To do this, type: 

<blockquote><code class='to_type'>V1.projections()['Afferent0'].learning_rate</code></blockquote>

in the <span class='t_item'>Command</span> box or at the Topographica
terminal prompt. The current learning rate will be
displayed in your terminal window. Next, type:

<blockquote><code class='to_type'>V1.projections()['Afferent0'].learning_rate=0.1</code></blockquote>

Now each new pattern generated in a
training iteration will nearly wipe out any existing weights.

<p></p></li><li>For more control over the training inputs, open the
<span class='w_title'>Test Pattern</span> window, select an
<span class='t_item'>Input type</span>, e.g. <span class='t_item'>Disk</span>, and other
parameters as desired.  Then enable <span class='t_item'>Network learning</span> in that
window, and hit <span class='b_press'>Present</span>.  You should again see how
this input changes the weights, and can experiment with different inputs.


<!--CEBHACKALERT: use for learning button not complete -->
<!--
<p><li>Once you have a particular input pattern designed, you can see
how that pattern would affect the cortex over many iterations.  To do
so, press the <span class='b_press'>Use for Training</span> button.  Now when you
train for more iterations you'll see the new pattern and its effect on
the weights.  (Note that the position and orientation of the new
training pattern will always be (**FIXED!) for this simulation, and that
training with (**UPDATE:) a photograph works only for photos named image.pgm.)</li></p>


<p></p></li><li>After a few steps (or to do e.g. 20 steps in a row, change
<span class='t_item'>Learning iterations</span> to 20 and press return), you can
plot (or refresh) an <span class='w_title'>Orientation
Preference</span> map to see what sort of
orientation map has developed.  If you've changed the learning rate to
a high value, or haven't presented many inputs, the map will not
resemble actual animal maps, but it should still have patches
selective for each orientation. 
<p></p></li>

<li>If you are patient, you can even run a full, more realistic,
simulation with your favorite type of input. (**no you can't, or at
least not this way: UPDATE.)  To do this, quit and
start again and change the
<span class='t_item'>Input type</span> as before, but make sure not to change
<code>alpha_input</code>.  Then you can change
<span class='t_item'>Learning iterations</span> to 10000 and ** <span class='b_press'>Train</span>), to see how
a full simulation would work with your new inputs.  If you hit the
<span class='b_press'>Activity</span> button ** while it's training, you'll see a window
pop up when it's done (which will be at least several minutes, for
recent machines, or even longer with older machines).  If you are less
patient, try doing 1000 iterations at a time instead before looking at
an Orientation Map</b></span>.<p></p></li>
-->

<p><li> If you are <em>really</em> patient, you can change the number
of units to something closer to real primate cortex, by quitting,
editing the Python code file <code>examples/lissom_or.ty</code> to
change the <code>nominal_density</code> of V1 from 48 to 150,
and doing:
<blockquote><code class='to_type'>
  ./topographica examples/lissom_or.ty -g
  </code></blockquote>
<p></p>
  
You'll need a lot of memory and a lot of time, but you can then step
through the simulation as above.  The final result after 20000
iterations (requiring several hours, if not days) should be a much
smoother map and neurons that are more orientation selective.  Even
so, the overall organization and function should be similar.
</li></ol>



<h2>Exploring further</h2>

<p> Topographica comes with
additional examples, and more are currently being added. Any valid Python code can
be used to control and extend Topographica; documentation for Python and existing Topographica commands
can be accessed from the <span class='t_item'>Help</span> menu of the
<span class='w_title'>Topographica Console</span> window.
<p>
 Please contact 
<A HREF="mailto:&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107?subject=Comments%20on%20Topographica%20tutorial">&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107</a>
if you have questions or suggestions about the software or this
tutorial.
</p>
