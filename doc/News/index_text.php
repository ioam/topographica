<!-- TimeSeries - generic container for sequential data -->
<!-- Legacy support can now be tied to particular releases/versions, so we can control what support is installed.-->
<!-- Removed apparently unmaintained Gnosis Utils.  Removed experimental xml snapshot saving.-->
<!-- multiprocessor support (via MPI) ADD DOC LINK -->
<!--
  <div class="i2">- Added <A target="_top" href="../Developer_Manual/cython.html">Cython tutorial</A> for writing fast components more easily</div>
-->

<!-- Updated to Fri Nov 23 00:45:31 GMT 2012 version -->
<p><b><a name="23-nov-2012">23 Nov 2012:</a></b> Version 0.9.8 released, including:

<center>
<table width="100%" cellpadding="5">
<tr>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>General improvements:</dt>
<dd>
  <div class="i2">- now uses native Python by default, making it much
  easier to integrate Topographica into your scientific workflow</div> 
  <div class="i2">- <A target="_top" href="../User_Manual/multicore.html">shared-memory multiple-core support (via OpenMP)</A></div>
  <div class="i2">- support for Python 2.7, NumPy 1.6, IPython 0.11-0.12, and Matplotlib 1.1.0</div>
  <div class="i2">- Mac OS X: right click supported on more platforms, automatic .ty file syntax colouring in Xcode 3</div>
  <div class="i2">- snapshots created by version 0.9.7 and above will be supported</div>
  <div class="i2">- default output path now in a Topographica subfolder of
  your system's Documents directory (often ~ on Linux; typically
  Documents elsewhere)</div>
  <div class="i2">- simpler installation using pip on all platforms</div>
  <div class="i2">- no longer need to build <kbd>topographica</kbd> script on installation</div>
<!--  <div class="i2">- support for real-world units using Quantities</div> -->
  <div class="i2">- minor bugfixes</div>
</dd>
<br>
<dt>Command-line and batch:</dt>
<dd>
  <div class="i2">- --pdb calls debugger after every unhandled exception</div>
</dd>
<br>
<dt>Example scripts:</dt>
<dd>
  <div class="i2">- ptztracker.ty: example of controlling a pan/tilt/zoom camera to track objects in real time</div>
  <div class="i2">- new "models" subdirectory for published work; "examples" is now meant only for simpler starting points</div>
</dd>
</font>
</dl>
</td>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>GUI:</dt>
<dd>
  <div class="i2">- Model Editor allows text labels to be suppressed so that .eps output can be labeled in an illustration program (e.g. Inkscape) for use in publications</div>
  <div class="i2">- New plot options for right-clicking: plot in sheet
  coords, plot in matrix coords, autocorrelation (requires SciPy)</div>
</dd>
<br>
<dt>Component library:</dt>
<dd>
  <div class="i2">- PatternGenerators:
<!--  <?php classref('imagen','SpiralGrating')?>, -->
<!--  <?php classref('imagen','HyperbolicGrating')?>, -->
<!--  <?php classref('imagen','RadialGrating')?>, -->
<!--  <?php classref('imagen','ConcentricRings')?>, -->
<!--  <?php classref('imagen','ArcCentered')?>, -->
  <?php classref('imagen','Sigmoid')?> (half plane with sigmoidal border),
  <?php classref('imagen','LogGaussian')?> (Gaussian with skew),
  <?php classref('imagen','SigmoidedDoG')?> (auditory RF with a DoG multiplied by a sigmoid),
  <?php classref('imagen','SigmoidedDoLG')?> (auditory RF with two DoLGs multiplied by a sigmoid),
  <?php classref('imagen.opencvcamera','CameraImage')?> (OpenCV live camera import) pattern families
  </div>
  <div class="i2">- <?php classref('topo.misc.distribution','DistributionStatisticFn')?>
  classes for controlling map and tuning curve measurement:
  <?php classref('topo.misc.distribution','DSF_MaxValue')?>
  (preference is peak value)
  <?php classref('topo.misc.distribution','DSF_WeightedAverage')?>
  (pref is weighted average)
  <?php classref('topo.misc.distribution','DSF_VonMisesFit')?>, (from von
  Mises circular normal fit), 
  <?php classref('topo.misc.distribution','DSF_BimodalVonMisesFit')?>
  (bimodal distribution fit; also see 
  <?php classref('topo.misc.distribution','DSF_TopTwoValues')?> and
  <?php classref('topo.misc.distribution','DSF_BimodalPeaks')?>).
  </div>
  <div class="i2">- <?php classref('param','Array')?> parameter</div>
  <div class="i2">- Simulation and EventProcessors now support tab completion and "."
access to their Sheets and EPConnections (e.g. "topo.sim.V1.Afferent")</div>
  <div class="i2">- greatly expanded support for auditory input; see
  <A HREF="../Reference_Manual/imagen.audio-module.html">imagen.audio</a></div>
</dd>
</font>
</dl>
</td>
</tr>
</table>
</center>


<p><b>3 Oct 2012:</b> Topographica development moved from
  <a target="_top" href="http://sourceforge.net/projects/topographica">SourceForge
  SVN</a> to <a target="_top" href="http://github.com/ioam/topographica">
  GitHub git</a>.

  <P>SVN write access has now been disabled.  See the
  <a target="_top" href="https://git.wiki.kernel.org/index.php/GitSvnCrashCourse">Git
  Crash Course</a> to translate your SVN commands to Git.  All
  features since 0.9.7 are now available from
  <a target="_top" href="https://github.com/ioam/topographica">github</a>, and all
  sf.net bugs and feature requests have been converted to GitHub issues.
  The Param and ImaGen subprojects now accompany Topographica as git
  submodules, allowing easy editing while leaving them as separate
  projects.  Installation is now via either
  <a target="_top" href="https://github.com/ioam/topographica">git
  (for developers)</a> or
  <a target="_top" href="../Downloads/index.html">pip (for users)</a>.<BR> 
  
<p><b>18 Jul 2012:</b> New subprojects at GitHub have been created for
  elements of Topographica that are widely reusable in other projects:
  <DL>
  <P><DT><A href="http://ioam.github.com/param/">Param</A> and
  <A href="http://ioam.github.com/paramtk/">ParamTk</A> </DT>
  <DD>General-purpose support for full-featured Parameters, extending
    Python attributes to have documentation, bounds, types, etc., with
    optional Tk support.</DD>

  <P><DT><A href="http://ioam.github.com/imagen/">ImaGen</A></DT>
  <DD>General-purpose support for generating 0D (scalar), 1D (vector),
    and 2D (image) patterns, starting from mathematical functions,
    geometric shapes, random distributions, images, etc.</DD>
  </DL>

  <P>These subprojects contain code still used in Topographica (with
  imagen visible as topo.pattern for backwards compatibility), but
  can now be downloaded and installed separately.  Both projects were
  introduced at SciPy 2012 (Austin, TX); the 
  <a target="_top" href="http://www.youtube.com/watch?v=7_ELWwzFCi0">talk on
  Param</a> is available online.<BR><BR>

<p><b>18 July 2010:</b> Version 0.9.7 released, including:

<!-- Updated to r10814 -->
<center>
<table width="100%" cellpadding="5">
<tr>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>General improvements:</dt>
<dd>
  <div class="i2">- now released under less-restrictive BSD license
  instead of GPL, to facilitate commercial use of components</div>
  <div class="i2">- now supports Python 2.6</div>
  <div class="i2">- significantly reduced memory consumption (35% less for lissom.ty)</div>
  <div class="i2">- minor bugfixes</div>
  <div class="i2">- now available as .deb package for Ubuntu and .rpm for Fedora Core, in addition to .zip and .tar.gz versions, and via
  'easy_install topographica'</div>
  <div class="i2">- optional
  <A target="_top" href="http://divmod.org/trac/wiki/DivmodPyflakes">PyFlakes</A> package for detecting common Python problems</div>
  <div class="i2">- optional
  <A target="_top" href="http://mpi4py.scipy.org">mpi4py</A> package using MPI for writing parallel applications</div>
<!--  <div class="i2">- optional (experimental) integration with IDLE; try 'make topographicagui; ./topographicagui'</div> -->
  <div class="i2">- <A HREF="../Downloads/git.html">instructions</A>
  available for checking out Git version of repository</div>
</dd>
<br>
<dt>Command-line and batch:</dt>
<dd>
  <!--CEBALERT: dirname_prefix might be changed. We had email discussion but I haven't
  done anything about it yet.-->
  <div class="i2">- <?php classref('topo.command','run_batch')?> accept
  new name_time_format and dirname_prefix parameters</div>
  <div class="i2">-
  <?php fnref('topo.command','n_bytes')?>,
  <?php fnref('topo.command','n_conns')?>,
  <?php fnref('topo.command','print_sizes')?>:
  display size and memory usage of current network</div>
</dd>
<br>
<dt>GUI:</dt>
<dd>
  <div class="i2">- moved progress bars, messages, warnings, and
  errors into the status bar for each window, to make it clear where
  the error or status issue arose</div>
</dd>
</font>
</dl>
</td>
<td width="50%">
<dl COMPACT>
<font size="-1">
<br>
<dt>Plotting:</dt>
<dd>
  <div class="i2">- more joint normalization options
  (JointProjections, AllTogether, Individually), to show 
  relative differences in weight strength and activity</div>
  <div class="i2">- PhaseDisparity plot</div>
</dd>
<br>
<dt>Component library:</dt>
<dd>
  <div class="i2">- PatternGenerators:
  <?php classref('topo.pattern','ExponentialDecay')?>,
  <?php classref('topo.pattern','HalfPlane')?>,
  <?php classref('topo.pattern','Arc')?>,
  <?php classref('topo.pattern','Curve')?>, 
  <?php classref('topo.pattern','Rectangle')?> (now with smoothing),
  <?php classref('topo.pattern','RawRectangle')?> (no smoothing),
  <?php classref('topo.pattern','Sigmoid')?>,
  <?php classref('topo.pattern','SigmoidedDoG')?> (for audio STRFs),
  <?php classref('topo.pattern','PowerSpectrum')?> (for frequency decomposition),
  <?php classref('topo.pattern','Spectrogram')?> (for frequency decomposition over time),
  <?php classref('topo.pattern.audio','Audio')?> (for audio files),
  <?php classref('topo.pattern.audio','AudioFolder')?> (for directories of audio files)
  </div>
  <div class="i2">- SpiralGrating, HyperbolicGrating, RadialGrating,
  ConcentricRings, and ArcCentered pattern families can be copied from
  <A HREF="../../contrib/hegdeessen.py">contrib/hegdeessen.py</A>; to move
  to topo.pattern in next release</div>
  <div class="i2">- minor changes to PatternGenerator parameter
  passing to allow better nesting and composition</div>
  <div class="i2">- misc:
  <?php fnref('topo.misc.util','linearly_interpolate')?>,
  <?php fnref('topo.base.arrayutil','clip_upper')?></div>
</dd>
<br>
<dt>Example scripts:</dt>
<dd>
  <div class="i2">- gcal.ty: robust and simple visual map development</div>
  <div class="i2">- lissom_audio.py: example of auditory pathway</div>
</dd>
</font>
</dl>
</td>
</tr>
</table>
</center>


<p><b>12 February 2009:</b> Version 0.9.6 released, including:

<!-- Updated to r9984 -->
<center>
<table width="100%" cellpadding="5">
<tr>
<td width="50%">
<dl COMPACT>
<font size="-1">
<!--CB: surely these divs should be some kind of li?-->
<!--  <div class="i2">- optional XML snapshot
  <A HREF="../Reference_Manual/topo.command-module.html#save_snapshot">saving</A> and
  <A HREF="../Reference_Manual/topo.command-module.html#load_snapshot">loading</A></div>
-->
<!-- incomplete <A HREF="../Downloads/git.html">Instructions</A> for checking out Git version of repository<BR> -->
<!--  mouse model (examples/lissom_oo_or_species.ty)<BR> -->
<dt>General improvements:</dt>
<dd>
  <div class="i2">- significant performance improvements in
  simulations (nearly 2X overall), plotting (2X), and startup time </div>
  <div class="i2">- minor bugfixes</div>
<!--  <div class="i2">- updated Windows packages</div> -->
  <div class="i2">- more options for
  <A target="_top" href="../User_Manual/noise.html">adding noise</A>
  to ConnectionField shapes</div>
  <div class="i2">- optional
  <A target="_top" href="../Developer_Manual/optimization.html#line-by-line">line-by-line profiling</A></div>
  <div class="i2">- optional
  <A target="_top" href="http://www.cython.org">Cython</A> package for writing fast components</div>
</dd>
<br>
<dt>Command-line and batch:</dt>
<dd>
  <div class="i2">- -v and -d options to print verbose and debugging messages</div>
  <div class="i2">- new options to
  <?php classref('topo.command','run_batch')?> and better progress messages</div>
  <div class="i2">- replaced most commands with
  <?php classref('param.parameterized','ParameterizedFunction')?>s,
  which have documented, type and bound-checked arguments and allow
  inheritance of shared functionality</div>
  <div class="i2">- replaced map measurement commands in
  <A target="_top" HREF="../Reference_Manual/topo.command-module.html">topo.command</A>
  with simpler, general-purpose, easily .ty-file controllable versions (see
  lissom_oo_or.ty and lissom.ty for examples)</div>
  <div class="i2">- <?php classref('topo.command.analysis','save_plotgroup')?>:
  more useful default values; results can be cached to avoid recomputation</div>
  <div class="i2">- <?php classref('topo.command.analysis','measure_sine_pref')?>:
  general purpose measurement for any preference that can be tested
  with a sine grating</div>
  <div class="i2">- Changed locals to script-level parameters using
  <?php classref('topo.misc.commandline','GlobalParams')?>;
  see examples/lissom.ty</div>
  <div class="i2">- Made
  <?php classref('topo.command.pylabplots','gradientplot')?> and
  <?php classref('topo.command.pylabplots','fftplot')?> available in
  batch mode.</div>
</dd>
<BR>
<dt>GUI:</dt>
<dd>
  <div class="i2">- model editor supports non-Sheet EventProcessors
  and non-CFProjection EPConnections</div>
  <div class="i2">- right-click option for plotting tuning curves</div>
  <div class="i2">- plot windows can be arranged in 2D, not just a row
  (see <?php classref('topo.base.sheet','Sheet')?>.row_precedence)</div>
  </div>
</dd>
</font>
</dl>
</td>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>Example scripts:</dt>
<dd>
  <div class="i2">- example file for
  <a target="_top" href="../User_Manual/interfacing.html">interfacing to external simulators</a>
  (examples/perrinet_retina.ty)</div>
  <div class="i2">- removed outdated or in-progress examples</div>
  <div class="i2">- greatly simplified remaining example scripts</div>
  <div class="i2">- now use <?php classref('topo.misc.commandline','GlobalParams')?>
  to support consistent option setting using -p</div>
  <div class="i2">- allowed saving of local functions and instance
  method calls in snapshots</div>
</dd>
<br>
<br>
<br>
<br>
<br>
<dt>Component library:</dt>
<dd>
  <div class="i2">- PatternGenerators:
  <?php classref('topo.pattern','Translator')?>;
    mask_shape parameter also now makes it easy to specify a mask
    for any pattern, e.g. in the GUI</div>
  <div class="i2">- TransferFns (formerly called OutputFns):
  <?php classref('topo.transferfn','HalfRectifyAndPower')?>,
  <?php classref('topo.transferfn','Hysteresis')?>, and
  <?php classref('topo.transferfn','HomeostaticResponse')?></div>
  <div class="i2">- Sheets:
  <?php classref('topo.sheet','ActivityCopy')?></div>
  <div class="i2">- LearningFns:
  <?php classref('topo.learningfn.optimized','CFPLF_BCMFixed_opt')?>,
  <?php classref('topo.learningfn.optimized','CFPLF_Scaled_opt')?></div>
  <div class="i2">- Added <?php classref('param','HookList')?>
  parameters to
  <?php classref('topo.analysis.featureresponses','FeatureResponses')?> and
  <?php classref('topo.sheet.lissom','LISSOM')?> to make it easier to
  add user-defined functionality.</div>
  <div class="i2">- Changed names and definitions of various similar
  concepts (OutputFn, before_presentation, update_command,
  plot_command, etc.)  to reflect shared concept of Hooks and
  HookLists (lists of callables to run at specific spots in the
  code).</div>
  <div class="i2">- Parameters: bounds can now be exclusive, optional support for None in most
  types</div>
</dd>
</font>
</dl>
</td>
</tr>
<tr><td colspan='2'><small>We also provide a utility to simplify the
  process of <A HREF="../Downloads/update_script.html">updating scripts</A>
that were written for version 0.9.5.</small> </td></tr>
</table>
</center>


<p><b>05 September 2008:</b> Version 0.9.5
<A target="_top" href="../Downloads/index.html">released</A>, including:
<center>
<table width="100%" cellpadding="5">
<tr>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>General improvements:</dt>
<dd>
<!--CB: surely these divs should be some kind of li?-->
  <div class="i2">- numerous bugfixes and performance improvements</div>
<!-- fixed a number of pychecker warnings.<BR> -->
<!-- moved current to-do items to the sf.net trackers<BR> -->
<!-- EventProcessor.start() run only when Simulation starts, e.g. to allow joint normalization across a Sheet's projections<BR> -->

  <div class="i2">- simulation can now be locked to real time</div>

  <div class="i2">- simpler and more complete support for dynamic parameters</div>
<!-- dynamic parameters now update at most once per simulation time<BR> -->

  <div class="i2">- updated to Python 2.5 and numpy 1.1.1.</div>

  <div class="i2">- source code moved from CVS to Subversion (<A HREF="../Downloads/cvs.html">SVN</A>)</div>
<!--  replaced FixedPoint with gmpy for speed and to have rational no. for time<BR> -->
  <div class="i2">- automatic Windows and Mac <A target="_top" href="http://buildbot.topographica.org">daily builds</A></div>
  <div class="i2">- automatic running and startup <A target="_top" href="http://buildbot.topographica.org">performance measurement</A></div>
<!--CEBALERT: we're removing that for the release!-->
  <div class="i2">- contrib dir</div>
  <div class="i2">- divisive and multiplicative connections</div>
  <div class="i2">- simulation time is now a rational number for precision</div>
  <div class="i2">- PyTables HDF5 interface</div>
  <div class="i2">- more options for
  <A target="_top" href="../User_Manual/noise.html">adding noise</A></div>
<!-- topo/misc/legacy.py i.e. we can now support old snapshots if necessary<BR> -->
<!-- incomplete <A HREF="../Downloads/git.html">Instructions</A> for checking out Git version of repository<BR> -->
</dd>
<BR>
<dt>Command-line and batch:</dt>
<dd>
  <div class="i2">- simplified example file syntax
  (see examples/lissom_oo_or.ty and som_retinotopy.py)</div>
  <div class="i2">- command prompt uses <A HREF="http://ipython.scipy.org/">IPython</A> for better debugging, help</div>
  <div class="i2">- simulation name set automatically from .ty script name by default</div>
  <div class="i2">- command-line options can be called explicitly</div>
  <!-- , e.g.
  <A HREF="../Reference_Manual/topo.misc.commandline-module.html#gui">topo.misc.commandline.gui()</A> or
  ;<A HREF="../Reference_Manual/topo.misc.commandline-module.html#auto_import_commands">topo.misc.commandline.auto_import_commands()</A><BR>-->
</dd>
<BR>
<dt>GUI:</dt>
<dd>
  <div class="i2">- model editor fully supports dynamic parameters
  (described in the lissom_oo_or tutorial)</div>
  <div class="i2">- plot windows can be docked into main window</div>
  <div class="i2">- uses tk8.5 for anti-aliased fonts <!--and potential to move to platform-specific themes--></div>
<!--  cleaned up ParametersFrame and TaggedSlider behavior<BR> -->
</dd>
</font>
</dl>
</td>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>Plotting:</dt>
<dd>
  <div class="i2">- new preference map types (Hue, Direction, Speed)</div>
  <div class="i2">- combined (joint) plots using contour and arrow overlays</div>
  <div class="i2">- example of generating activity movies
  (examples/lissom_or_movie.ty)</div>
</dd>
<BR>
<dt>Example scripts:</dt>
<dd>
  <div class="i2">- example files for robotics interfacing (<A HREF="../Reference_Manual/topo.misc.playerrobot-module.html">misc/playerrobot.py</A>,
  <A HREF="../Reference_Manual/topo.misc.robotics-module.html">misc/robotics.py</A>)</div>
  <div class="i2">- simulation, plots, and analysis for modelling of any combination of position, orientation, ocular dominance, stereoscopic disparity, motion direction, speed, spatial frequency, and color (examples/lissom.ty).</div>
<!--  mouse model (examples/lissom_oo_or_species.ty)<BR> -->
</dd>
<BR>
<dt>Component library:</dt>
<dd>
  <div class="i2">- OutputFns:
  <?php classref('topo.outputfn','PoissonSample')?>,<BR>
  <?php classref('topo.outputfn','ScalingOF')?> (for homeostatic plasticity),<BR>
  <?php classref('topo.outputfn','NakaRushton')?> (for contrast gain control)<BR>
  <?php classref('topo.outputfn','AttributeTrackingOF')?> (for analyzing or plotting values over time)</div>
<!-- &nbsp;&nbsp;&nbsp;('x=HalfRectify() ; y=Square() ; z=x+y' gives 'z==PipelineOF(output_fns=x,y)')<BR> -->
<div class="i2">- PatternGenerator: <?php classref('topo.misc.robotics','CameraImage')?> (for real-time camera inputs)</div>
<!--  allowed <?php classref('topo.sheet.lissom','LISSOM')?>  normalization to be
  <A HREF="../Reference_Manual/topo.sheet.lissom.LISSOM-class.html#post_initialization_weights_output_fn">changed</A>
  after initialization<BR> -->

  <div class="i2">- CoordMapper: <?php classref('topo.coordmapper','Jitter')?></div>
  <div class="i2">- SheetMasks: <?php classref('topo.base.projection','AndMask')?>,
  <?php classref('topo.base.projection','OrMask')?>,
  <?php classref('topo.base.projection','CompositeSheetMask')?></div>
  <div class="i2">- command:
  <?php fnref('topo.command.analysis','decode_feature')?> (for estimating perceived values)
  (e.g. for calculating aftereffects)</div>
  <div class="i2">- functions for analyzing V1 complex cells</div>
  <div class="i2">- <?php classref('topo.base.functionfamily','PipelineOF')?> OutputFns can now be constructed easily using +</div>
  <div class="i2">- <?php classref('topo.numbergen','NumberGenerator')?>s
  can now be constructed using +,-,/,*,abs etc.
<!-- (e.g. abs(2*UniformRandom()-5) is now a NumberGenerator too).--></div>
<!-- provide stop_updating and restore_updating to allow functions with state to freeze their state<BR> -->
</dd>
</font>
</dl>
</td>
</tr>
<tr><td colspan='2'><small>We also provide a utility to <A
HREF="../Downloads/update_script.html">update scripts</A>
that were written for version 0.9.4.</small> </td></tr>
</table>
</center>

<p><b>26 October 2007:</b> Version 0.9.4
<A target="_top" href="../Downloads/index.html">released</A>, including:

<center>
<table width="100%" cellpadding="5">
<tr>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>General improvements:</dt>
<dd>
  numerous bugfixes<br>
  set up <A target="_top" href="http://buildbot.topographica.org">automatic daily builds</A><br>
</dd>
<dt>Example scripts:</dt>
<dd>
  new whisker barrel cortex simulation<br>
  &nbsp;&nbsp;(using transparent Matlab wrapper)<br>
  new elastic net ocular dominance simulation<br>
  new spiking example; still needs generalizing<br>
</dd>
<dt>Command-line and batch:</dt>
<dd>
  <!-- <A target="_top" href="../User_Manual/commandline.html#option-a">-a
  option to import commands automatically<br> -->
  <A target="_top" href="../User_Manual/batch.html">batch
  mode</A> for running multiple similar simulations<br>
  <A target="_top" href="../User_Manual/commandline.html#saving-bitmaps">saving
  bitmaps</A> from script/command-line (for batch runs)<br>
  script/command-line <A target="_top" href="../User_Manual/commandline.html#scripting-gui">control over GUI</A><br>
  <!-- grid_layout command to simplify model diagrams<br> -->
  <!-- options for controlling plot sizing<br> -->
  added auto-import option (-a and -g) to save typing<br>
</dd>
</font>
</dl>
</td>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>GUI:</dt>
<dd>
  greatly simplified adding GUI code <!--<A target="_top" href="../Developer_Manual/gui.html#programming-tkgui">adding GUI code</A>--><br>
  <!--  added GUI tests<br> -->
  <!--  added optional pretty-printing for parameter names in GUI<br> -->
  added progress bars, scroll bars, window icons<br>
  new Step button on console
  <!-- changed -g to launch the GUI where it is specified, to allow more control<br> -->
  <!-- added categories for plots to simplify GUI<br> -->
</dd>
<dt>Plotting:</dt>
<dd>
  <A target="_top" href="../User_Manual/plotting.html#rfplots">reverse-correlation RF mapping</A><br>
  <A target="_top" href="../User_Manual/commandline.html#3d-plotting">3D
  wireframe plotting</A> (in right-click menu)<br>
  gradient plots, histogram plots (in right-click menu)<br>
  <A target="_top" href="../User_Manual/plotting.html#measuring-preference-maps">simplified
  bitmap plotting</A> (removed template classes)<br>
  GUI plots can be saved as PNG or EPS (right-click menu)<br>
  automatic collection of plots for animations (see ./topographica examples/lissom_or_movie.ty)<br>
</dd>
<dt>Component library:</dt>
<dd>
  new
  <A HREF="../Reference_Manual/topo.coordmapper-module.html">
  coordmapper</A>s (Grid, Pipeline, Polar/Cartesian)<br>
  <!-- OutputFnDebugger for keeping track of statistics<br> -->
</dd>
</font>
</dl>
</td>
</tr>
</table>
</center>

Screenshots:
<A target="_top" href="../images/071018_plotting1_ubuntu.png">plotting 1</A>,
<A target="_top" href="../images/071018_plotting2_ubuntu.png">plotting 2</A>,
<A target="_top" href="../images/071018_modeleditor_ubuntu.png">model editor</A>.
<br><br>

<p><b>23 April 2007:</b> Version 0.9.3
<A target="_top" href="../Downloads/index.html">released</A>, including:

<center>
<table width="100%" cellpadding="5">
<tr>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>General improvements:</dt>
<dd>
  numerous bugfixes<br>
  significant optimizations (~5 times faster)<br>
  <!-- (about 5 times faster than 0.9.2 for most scripts, with more improvements to come)<br>  -->
  compressed snapshots (1/3 as large)<br>
  <!-- more comprehensive test suite checking both speed and functionality<br> -->
  much-improved reference manual<br>
  <!-- arrays based on Numpy rather than Numeric<br> -->
</dd>
<dt>Component library:</dt>
<dd>
  adding noise to any calculation<br>
  lesioning units and non-rectangular sheet shapes (see PatternCombine)<br>
  basic auditory pattern generation<br>
<!--  greatly simplified convolutions<br>--> <!-- SharedWeightCFProjection -->
  greatly simplified SOM support<br> <!-- now can be mixed and matched with any other components<br> -->
  more dynamic parameters (such as ExponentialDecay)<br>
  flexible mapping of ConnectionField centers between sheets<br>
</dd>
<dt>Example scripts:</dt>
<dd>
  examples that more closely match published simulations<br>
  new simulations for face processing and for
  self-organization from natural images<br>
</dd>
</font>
</dl>
</td>
<td width="50%">
<dl COMPACT>
<font size="-1">
<dt>GUI:</dt>
<dd>
  Better OS X and Windows support<br>
  progress reporting for map measurement<br>
  dynamic display of coordinates in plots<br>
  stop button to interrupt training safely<br>
  ability to plot and analyze during training<br>
  right-click menu for analysis of bitmap plots<br>
  saving current simulation as an editable .ty script<br>
</dd>
<dt>Command-line and batch:</dt>
<dd>
<!--  more-informative command prompt<br> -->
  site-specific commands in ~/.topographicarc<br>
  simple functions for doing optimization<br>
<!--  saving of plot data with snapshots<br> -->
</dd>
<dt>Plotting:</dt>
<dd>
  spatial frequency map plots<br>
  tuning curve plots<br>
  FFT transforms (in right-click menu)<br>
</dd>
</font>
</dl>
</td>
</tr>
</table>
</center>

Screenshots:
<A target="_top" href="../images/topographica-0.9.3_ubuntu.png">Plotting</A>,
<A target="_top" href="../images/topographica-0.9.3_modeleditor_ubuntu.png">Model editor</A>.
<br><br>


<p><b>29 November 2006:</b> There will be a short talk on Topographica
at the <A target="_top" href="http://us.pycon.org/TX2007/">PyCon 2007</A>
convention, February 23-25, 2007.
<br><br>

<p><b>22 November 2006:</b> Version 0.9.2
<A target="_top" href="../Downloads/index.html">released</A>, including
numerous bugfixes (e.g. to support GCC 4.1.x compilers),
much more complete user manual,
more useful reference manual,
more sample models,
flexible joint normalization across Projections,
arbitrary control of mapping CF centers (see CoordinateMapperFn),
Composite and Selector patterns to allow flexible combinations of input patterns,
homeostatic learning and output functions,
sigmoid and generalized logistic output functions,
and a new disparity map example (including a
random dot stereogram input pattern).
<!-- Choice class to select randomly from a list of choices -->
<br><br>

<p><b>02 November 2006:</b> Some users have reported problems when using
optimized code on systems with the most recent GCC 4.1.x C/C++
compilers.  We have added a patch to the included weave
inline-compilation package that should fix the problem, currently
available only on the most recent CVS version of Topographica.
Affected users may need to do a <A target="_top"
href="../Downloads/cvs.html">CVS</A> update, then "make -C external
weave-uninstall ; make".  These changes will be included in the next
official release.
<br><br>

<p><b>23 July 2006:</b> Version 0.9.1
<A target="_top" href="../Downloads/index.html">released</A>.
This is a bugfix release only, upgrading the included Tcl/Tk package
to correct a syntax error in its configure script, which had
been preventing compilation on platforms using bash 3.1 (such as
Ubuntu 6.06).  There is no benefit to updating if 0.9.0 already runs
on your platform.
<br><br>

<p><b>07 June 2006:</b> Version 0.9.0
<A target="_top" href="../Downloads/index.html">released</A>, including
numerous bugfixes,
context-sensitive (balloon) help for nearly every parameter and control,
full Windows support (<A target="_top" href="../images/060607_topographica_win_screenshot.png">screenshot</A>),
full Mac OS X support,
downloadable installation files,
significant performance increases (7X faster on the main example scripts, with more
speedups to come),
faster startup,
better memory management,
simpler programming interface,
improved state saving (e.g. no longer requiring the original script),
independently controllable random number streams,
plot window histories,
more library components (e.g. Oja rule, CPCA, covariance),
<!-- plotting in Sheet coordinates, -->
<!-- better plot size handling, -->
<!-- command history buffer, -->
prototype spiking neuron support, and
much-improved <A target="_top" href="../User_Manual/modeleditor.html">model editor</A>.<BR><BR>

<p><b>15 May 2006:</b> New book <A target="_top"
HREF="http://computationalmaps.org"><i>Computational Maps in the
Visual Cortex</i></A> available, including background on modeling
computational maps, a review of visual cortex models, and <A
target="_top" HREF="http://computationalmaps.org/docs/chapter5.pdf">an
extended set of examples of the types of models supported by
Topographica</a>.
<br><br>

<p><b>20 February 2006:</b> Version 0.8.2 released, including numerous
bugfixes,
circular receptive fields,
shared-weight projections,
<A TARGET="_top" href="../Tutorials/lissom_oo_or.html">tutorial with ON/OFF LGN model</A>,
<A TARGET="_top" href="../Tutorials/som_retinotopy.html">SOM retinotopy tutorial</A>,
Euclidean-distance-based response and learning functions,
density-independent SOM parameters,
<A TARGET="_top" href="../Downloads/cvs.html#osx">Mac OS X instructions</A>,
<A TARGET="_top" href="../Developer_Manual/index.html">developer manual</A>,
<A TARGET="_top" href="../User_Manual/index.html">partial user manual</A>,
much-improved
<A target="_top" href="../images/060220_model_editor_screen_shot.png">model editor</A>,
<A TARGET="_top" href="../User_Manual/commandline.html#pylab">generic Matlab-style plotting</A>,
topographic grid plotting,
RGB plots,
user-controllable plot sorting,
plot color keys,
<!-- Normally distributed random PatternGenerator, -->
and progress reports during learning.  See the
<A target="_top" href="../images/060220_topographica_screen_shot.png">Linux screenshot</A>.
<br><br>

<p><b>22 December 2005:</b> Version 0.8.1 released, including numerous
bugfixes, more flexible plotting (including weight colorization),
user-controllable optimization, properties panels, more-useful
<A TARGET="_top" href="../Reference_Manual/index.html">reference manual</A>,
image input patterns, and a prototype graphical
model editor.  <!-- Plus SOMs with selectable Projections -->
<br><br>

<p><b>8 November 2005:</b> New site launched with Topographica version
0.8.0, including a new
 <a target="_top" href="../Tutorials/lissom_or.html">LISSOM tutorial</a>.
(<a target="_top" href="../images/051107_topographica_screen_shot_white.png">Linux screenshot</a>).
