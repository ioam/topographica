****
News
****

**2 Oct 2013:** New paper using Topographica
============================================

`Stevens et al. (J. Neuroscience 2013) <http://dx.doi.org/10.1523/JNEUROSCI.1037-13.2013>`_
shows results from the GCAL model included with Topographica 
(`examples/gcal.ty <https://github.com/ioam/topographica/blob/master/examples/gcal.ty>`_).  
A complete example of replicating all results from the paper will be posted here soon, showing how to use 
`Lancet <https://github.com/ioam/lancet>`_ to launch the simulations, collate the results, and 
generate the final figures.  Meanwhile, the 
`GCAL tutorial <../Tutorials/gcal.html>`_ shows how to explore a running GCAL model.

**2 May 2013:** New web site
============================

Topographica has moved to a Sphinx_ and reStructuredText_ website with
online editing in Git, and integrated User and Reference Manuals,
thanks to contributions from Wiktor Brodlo.  Please let us know if
there are any problems, and meanwhile if you add code to Topographica,
please also contribute documentation in .rst format, which is very
easy to write and maintain.


**23 Nov 2012:** Version 0.9.8 released
=======================================

General improvements:
    - now uses native Python by default, making it much easier to integrate Topographica into your scientific workflow
    - `shared-memory multiple-core support (via OpenMP)`_
    - support for Python 2.7, NumPy 1.6, IPython 0.11-0.12, and Matplotlib 1.1.0
    - Mac OS X: right click supported on more platforms, automatic .ty file syntax colouring in Xcode 3
    - snapshots created by version 0.9.7 and above will be supported
    - default output path now in a Topographica subfolder of your system's Documents directory (often ~ on Linux; typically Documents elsewhere)
    - simpler installation using pip on all platforms
    - no longer need to build topographica script on installation
    - minor bugfixes
Command-line and batch:
    - --pdb calls debugger after every unhandled exception
Example scripts:
    - ptztracker.ty: example of controlling a pan/tilt/zoom camera to track objects in real time
    - new "models" subdirectory for published work; "examples" is now meant only for simpler starting points

GUI:
    - Model Editor allows text labels to be suppressed so that .eps output can be labeled in an illustration program (e.g. Inkscape) for use in publications
    - New plot options for right-clicking: plot in sheet coords, plot in matrix coords, autocorrelation (requires SciPy)
Component library:
    - PatternGenerators: `Sigmoid`_ (half plane with sigmoidal border), `LogGaussian`_ (Gaussian with skew), `SigmoidedDoG`_ (auditory RF with a DoG multiplied by a sigmoid), `SigmoidedDoLG`_ (auditory RF with two DoLGs multiplied by a sigmoid), `new CameraImage`_ (OpenCV live camera import) pattern families
    - `DistributionStatisticFn`_ classes for controlling map and tuning curve measurement: `DSF\_MaxValue`_ (preference is peak value) `DSF\_WeightedAverage`_ (pref is weighted average) `DSF\_VonMisesFit`_, (from von Mises circular normal fit), `DSF\_BimodalVonMisesFit`_ (bimodal distribution fit; also see `DSF\_TopTwoValues`_ and `DSF\_BimodalPeaks`_).
    - `Array`_ parameter
    - Simulation and EventProcessors now support tab completion and "." access to their Sheets and EPConnections (e.g. "topo.sim.V1.Afferent")
    - greatly expanded support for auditory input; see `imagen.audio`_

**3 Oct 2012:** Topographica development moved from `SourceForge SVN`_ to `GitHub git`_.
========================================================================================

SVN write access has now been disabled. See the `Git Crash Course`_
to translate your SVN commands to Git. All features since 0.9.7 are
now available from `github`_, and all sf.net bugs and feature
requests have been converted to GitHub issues. The Param and ImaGen
subprojects now accompany Topographica as git submodules, allowing
easy editing while leaving them as separate projects. Installation
is now via either `git (for developers)`_ or `pip (for users)`_.

**18 Jul 2012:** New subprojects at GitHub
==========================================
New subprojects at GitHub have been created for elements of Topographica that are widely reusable in other projects:

`Param`_ and `ParamTk`_
    General-purpose support for full-featured Parameters, extending
    Python attributes to have documentation, bounds, types, etc.,
    with optional Tk support.
`ImaGen`_
    General-purpose support for generating 0D (scalar), 1D (vector),
    and 2D (image) patterns, starting from mathematical functions,
    geometric shapes, random distributions, images, etc.

These subprojects contain code still used in Topographica (with
imagen visible as topo.pattern for backwards compatibility), but can
now be downloaded and installed separately. Both projects were
introduced at SciPy 2012 (Austin, TX); the `talk on Param`_ is
available online.

**18 July 2010:** Version 0.9.7 released
========================================

General improvements:
    - now released under less-restrictive BSD license instead of GPL, to facilitate commercial use of components
    - now supports Python 2.6
    - significantly reduced memory consumption (35% less for lissom.ty)
    - minor bugfixes
    - now available as .deb package for Ubuntu and .rpm for Fedora Core, in addition to .zip and .tar.gz versions, and via 'easy\_install topographica'
    - optional `PyFlakes`_ package for detecting common Python problems
    - optional `mpi4py`_ package using MPI for writing parallel applications
    - `instructions`_ available for checking out Git version of repository
Command-line and batch:
    - `run\_batch`_ accept new name\_time\_format and dirname\_prefix parameters
    - `n\_bytes`_, `n\_conns`_, `print\_sizes`_: display size and memory usage of current network
GUI:
    - moved progress bars, messages, warnings, and errors into the status bar for each window, to make it clear where the error or status issue arose
Plotting:
    - more joint normalization options (JointProjections, AllTogether, Individually), to show relative differences in weight strength and activity
    - PhaseDisparity plot
Component library:
    - PatternGenerators: `ExponentialDecay`_, `HalfPlane`_, `Arc`_, `Curve`_, `Rectangle`_ (now with smoothing), `RawRectangle`_ (no smoothing), `Sigmoid`_, `SigmoidedDoG`_ (for audio STRFs), `PowerSpectrum`_ (for frequency decomposition), `Spectrogram`_ (for frequency decomposition over time), `Audio`_ (for audio files), `AudioFolder`_ (for directories of audio files)
    - SpiralGrating, HyperbolicGrating, RadialGrating, ConcentricRings, and ArcCentered pattern families can be copied from `contrib/hegdeessen.py`_; to move to topo.pattern in next release
    - minor changes to PatternGenerator parameter passing to allow better nesting and composition
    - misc: `linearly\_interpolate`_, `clip\_upper`_
Example scripts:
    - gcal.ty: robust and simple visual map development
    - lissom\_audio.py: example of auditory pathway

**12 February 2009:** Version 0.9.6 released
============================================

General improvements:
    - significant performance improvements in simulations (nearly 2X overall), plotting (2X), and startup time
    - minor bugfixes
    - more options for `adding noise`_ to ConnectionField shapes
    - optional `line-by-line profiling`_
    - optional `Cython`_ package for writing fast components
Command-line and batch:
    - -v and -d options to print verbose and debugging messages
    - new options to `run\_batch`_ and better progress messages
    - replaced most commands with `ParameterizedFunction`_\ s, which have documented, type and bound-checked arguments and allow inheritance of shared functionality
    - replaced map measurement commands in `topo.command`_ with simpler, general-purpose, easily .ty-file controllable versions (see lissom\_oo\_or.ty and lissom.ty for examples)
    - `save\_plotgroup`_: more useful default values; results can be cached to avoid recomputation
    - `measure\_sine\_pref`_: general purpose measurement for any preference that can be tested with a sine grating
    - Changed locals to script-level parameters using `GlobalParams`_; see examples/lissom.ty
    - Made `gradientplot`_ and `fftplot`_ available in batch mode.
GUI:
    - model editor supports non-Sheet EventProcessors and non-CFProjection EPConnections
    - right-click option for plotting  tuning curves
    - plot windows can be arranged in 2D, not just a row (see `Sheet`_.row\_precedence)

Example scripts:
    - example file for `interfacing to external simulators`_ (examples/perrinet\_retina.ty)
    - removed outdated or in-progress examples
    - greatly simplified remaining example scripts
    - now use `GlobalParams`_ to support consistent option setting using -p
    - allowed saving of local functions and instance method calls in snapshots
Component library:
    - PatternGenerators: `Translator`_; mask\_shape parameter also now makes it easy to specify a mask for any pattern, e.g. in the GUI
    - TransferFns (formerly called OutputFns): `HalfRectifyAndPower`_, `Hysteresis`_, and `HomeostaticResponse`_
    - Sheets: `ActivityCopy`_
    - LearningFns: `CFPLF\_BCMFixed\_opt`_, `CFPLF\_Scaled\_opt`_
    - Added `HookList`_ parameters to `FeatureResponses`_ and `LISSOM`_ to make it easier to add user-defined functionality.
    - Changed names and definitions of various similar concepts (OutputFn, before\_presentation, update\_command, plot\_command, etc.) to reflect shared concept of Hooks and HookLists (lists of callables to run at specific spots in the code).
    - Parameters: bounds can now be exclusive, optional support for None in most types

We also provide a utility to simplify the process of `updating
scripts`_ that were written for version 0.9.5.

**05 September 2008:** Version 0.9.5 `released`_
================================================

General improvements:
    - numerous bugfixes and performance improvements
    - simulation can now be locked to real time
    - simpler and more complete support for dynamic parameters
    - updated to Python 2.5 and numpy 1.1.1.
    - source code moved from CVS to Subversion (`SVN`_)
    - automatic Windows and Mac `daily builds`_
    - automatic running and startup `performance measurement`_
    - contrib dir
    - divisive and multiplicative connections
    - simulation time is now a rational number for precision
    - PyTables HDF5 interface
    - more options for `adding noise`_
Command-line and batch:
    - simplified example file syntax (see examples/lissom\_oo\_or.ty and som\_retinotopy.py)
    - command prompt uses `IPython`_ for better debugging, help
    - simulation name set automatically from .ty script name by default
    - command-line options can be called explicitly
GUI:
    - model editor fully supports dynamic parameters (described in the lissom\_oo\_or tutorial)
    - plot windows can be docked into main window
    - uses tk8.5 for anti-aliased fonts

Plotting:
    - new preference map types (Hue, Direction, Speed)
    - combined (joint) plots using contour and arrow overlays
    - example of generating activity movies (examples/lissom\_or\_movie.ty)
Example scripts:
    - example files for robotics interfacing (`misc/playerrobot.py`_, `misc/robotics.py`_)
    - simulation, plots, and analysis for modelling of any combination of position, orientation, ocular dominance, stereoscopic disparity, motion direction, speed, spatial frequency, and color (examples/lissom.ty).
Component library:
    - OutputFns: `PoissonSample`_, `ScalingOF`_ (for homeostatic plasticity), `NakaRushton`_ (for contrast gain control) `AttributeTrackingOF`_ (for analyzing or plotting values over time)
    - PatternGenerator: `CameraImage`_ (for real-time camera inputs)
    - CoordMapper: `Jitter`_
    - SheetMasks: `AndMask`_, `OrMask`_, `CompositeSheetMask`_
    - command: `decode\_feature`_ (for estimating perceived values) (e.g. for calculating aftereffects)
    - functions for analyzing V1 complex cells
    - `PipelineOF`_ OutputFns can now be constructed easily using +
    - `NumberGenerator`_\ s can now be constructed using +,-,/,\*,abs etc.

We also provide a utility to `update scripts`_ that were written for
version 0.9.4.

**26 October 2007:** Version 0.9.4 `released`_
==============================================

General improvements:
    - numerous bugfixes
    - set up `automatic daily builds`_
Example scripts:
    - new whisker barrel cortex simulation (using transparent Matlab wrapper)
    - new elastic net ocular dominance simulation
    - new spiking example; still needs generalizing
Command-line and batch:
    - `batch mode`_ for running multiple similar simulations
    - `saving bitmaps`_ from script/command-line (for batch runs)
    - script/command-line `control over GUI`_
    - added auto-import option (-a and -g) to save typing
GUI:
    - greatly simplified adding GUI code
    - added progress bars, scroll bars, window icons
    - new Step button on console
Plotting:
    - `reverse-correlation RF mapping`_
    - `3D wireframe plotting`_ (in right-click menu)
    - gradient plots, histogram plots (in right-click menu)
    - `simplified bitmap plotting`_ (removed template classes)
    - GUI plots can be saved as PNG or EPS (right-click menu)
    - automatic collection of plots for animations (see ./topographica examples/lissom\_or\_movie.ty)
Component library:
    - new `coordmapper`_\ s (Grid, Pipeline, Polar/Cartesian)

Screenshots: `plotting 1`_, `plotting 2`_, `updated model editor screenshot`_.

**23 April 2007:** Version 0.9.3 `released`_
============================================

General improvements:
    - numerous bugfixes
    - significant optimizations (~5 times faster)
    - compressed snapshots (1/3 as large)
    - much-improved reference manual
Component library:
    - adding noise to any calculation
    - lesioning units and non-rectangular sheet shapes (see PatternCombine)
    - basic auditory pattern generation
    - greatly simplified SOM support
    - more dynamic parameters (such as ExponentialDecay)
    - flexible mapping of ConnectionField centers between sheets
Example scripts:
    - examples that more closely match published simulations
    - new simulations for face processing and for self-organization from natural images
GUI:
    - Better OS X and Windows support
    - progress reporting for map measurement
    - dynamic display of coordinates in plots
    - stop button to interrupt training safely
    - ability to plot and analyze during training
    - right-click menu for analysis of bitmap plots
    - saving current simulation as an editable .ty script
Command-line and batch:
    - site-specific commands in ~/.topographicarc
    - simple functions for doing optimization
Plotting:
    - spatial frequency map plots
    - tuning curve plots
    - FFT transforms (in right-click menu)

Screenshots: `Plotting`_, `Model editor screenshot`_.

**29 November 2006:** Topographica talk at PyCon
================================================
There will be a short talk on Topographica at
the `PyCon 2007`_ convention, February 23-25, 2007.

**22 November 2006:** Version 0.9.2 `released`_
===============================================
Includes numerous
bugfixes (e.g. to support GCC 4.1.x compilers), much more complete
user manual, more useful reference manual, more sample models,
flexible joint normalization across Projections, arbitrary control
of mapping CF centers (see CoordinateMapperFn), Composite and
Selector patterns to allow flexible combinations of input patterns,
homeostatic learning and output functions, sigmoid and generalized
logistic output functions, and a new disparity map example
(including a random dot stereogram input pattern).

**02 November 2006:** GCC 4.1.x problems reported
=================================================
Some users have reported problems when using
optimized code on systems with the most recent GCC 4.1.x C/C++
compilers. We have added a patch to the included weave
inline-compilation package that should fix the problem, currently
available only on the most recent CVS version of Topographica.
Affected users may need to do a `CVS`_ update, then "make -C
external weave-uninstall ; make". These changes will be included in
the next official release.

**23 July 2006:** Version 0.9.1 `released`_
===========================================
This is a bugfix
release only, upgrading the included Tcl/Tk package to correct a
syntax error in its configure script, which had been preventing
compilation on platforms using bash 3.1 (such as Ubuntu 6.06). There
is no benefit to updating if 0.9.0 already runs on your platform.

**07 June 2006:** Version 0.9.0 `released`_
===========================================
Includes numerous
bugfixes, context-sensitive (balloon) help for nearly every
parameter and control, full Windows support (`screenshot`_), full
Mac OS X support, downloadable installation files, significant
performance increases (7X faster on the main example scripts, with
more speedups to come), faster startup, better memory management,
simpler programming interface, improved state saving (e.g. no longer
requiring the original script), independently controllable random
number streams, plot window histories, more library components (e.g.
Oja rule, CPCA, covariance), prototype spiking neuron support, and
much-improved `model editor`_.

**15 May 2006:** New book `Computational Maps in the Visual Cortex`_ available
================================================================================
Includes background on modeling computational
maps, a review of visual cortex models, and `an extended set of
examples of the types of models supported by Topographica`_.

**20 February 2006:** Version 0.8.2 released
============================================
Includes numerous
bugfixes, circular receptive fields, shared-weight projections,
`tutorial with ON/OFF LGN model`_, `SOM retinotopy tutorial`_,
Euclidean-distance-based response and learning functions,
density-independent SOM parameters, `Mac OS X instructions`_,
`developer manual`_, `partial user manual`_, much-improved `model
editor (screenshot)`_, `generic Matlab-style plotting`_, topographic grid
plotting, RGB plots, user-controllable plot sorting, plot color
keys, and progress reports during learning. `See the Linux
screenshot`_.

**22 December 2005:** Version 0.8.1 released
============================================
Includes numerous
bugfixes, more flexible plotting (including weight colorization),
user-controllable optimization, properties panels, more-useful
`reference manual`_, image input patterns, and a prototype graphical
model editor.

**8 November 2005:** New site launched with Topographica version 0.8.0
======================================================================
Includes a new `LISSOM tutorial`_. (`Linux screenshot`_).

.. _shared-memory multiple-core support (via OpenMP): ../User_Manual/multicore.html
.. _Sigmoid: ../Reference_Manual/imagen.Sigmoid-class.html
.. _LogGaussian: ../Reference_Manual/imagen.LogGaussian-class.html
.. _SigmoidedDoG: ../Reference_Manual/imagen.SigmoidedDoG-class.html
.. _SigmoidedDoLG: ../Reference_Manual/imagen.SigmoidedDoLG-class.html
.. _new CameraImage: ../Reference_Manual/imagen.opencvcamera.CameraImage-class.html
.. _DistributionStatisticFn: ../Reference_Manual/topo.misc.distribution.DistributionStatisticFn-class.html
.. _DSF\_MaxValue: ../Reference_Manual/topo.misc.distribution.DSF_MaxValue-class.html
.. _DSF\_WeightedAverage: ../Reference_Manual/topo.misc.distribution.DSF_WeightedAverage-class.html
.. _DSF\_VonMisesFit: ../Reference_Manual/topo.misc.distribution.DSF_VonMisesFit-class.html
.. _DSF\_BimodalVonMisesFit: ../Reference_Manual/topo.misc.distribution.DSF_BimodalVonMisesFit-class.html
.. _DSF\_TopTwoValues: ../Reference_Manual/topo.misc.distribution.DSF_TopTwoValues-class.html
.. _DSF\_BimodalPeaks: ../Reference_Manual/topo.misc.distribution.DSF_BimodalPeaks-class.html
.. _Array: ../Reference_Manual/param.Array-class.html
.. _imagen.audio: ../Reference_Manual/imagen.audio-module.html
.. _SourceForge SVN: http://sourceforge.net/projects/topographica
.. _GitHub git: http://github.com/ioam/topographica
.. _Git Crash Course: https://git.wiki.kernel.org/index.php/GitSvnCrashCourse
.. _github: https://github.com/ioam/topographica
.. _git (for developers): https://github.com/ioam/topographica
.. _pip (for users): ../Downloads/index.html
.. _Param: http://ioam.github.com/param/
.. _ParamTk: http://ioam.github.com/paramtk/
.. _ImaGen: http://ioam.github.com/imagen/
.. _talk on Param: http://www.youtube.com/watch?v=7_ELWwzFCi0
.. _PyFlakes: http://divmod.org/trac/wiki/DivmodPyflakes
.. _mpi4py: http://mpi4py.scipy.org
.. _instructions: ../Downloads/git.html
.. _run\_batch: ../Reference_Manual/topo.command.run_batch-class.html
.. _n\_bytes: ../Reference_Manual/topo.command-module.html#n_bytes
.. _n\_conns: ../Reference_Manual/topo.command-module.html#n_conns
.. _print\_sizes: ../Reference_Manual/topo.command-module.html#print_sizes
.. _ExponentialDecay: ../Reference_Manual/topo.pattern.ExponentialDecay-class.html
.. _HalfPlane: ../Reference_Manual/topo.pattern.HalfPlane-class.html
.. _Arc: ../Reference_Manual/topo.pattern.Arc-class.html
.. _Curve: ../Reference_Manual/topo.pattern.Curve-class.html
.. _Rectangle: ../Reference_Manual/topo.pattern.Rectangle-class.html
.. _RawRectangle: ../Reference_Manual/topo.pattern.RawRectangle-class.html
.. _PowerSpectrum: ../Reference_Manual/topo.pattern.PowerSpectrum-class.html
.. _Spectrogram: ../Reference_Manual/topo.pattern.Spectrogram-class.html
.. _Audio: ../Reference_Manual/topo.pattern.audio.Audio-class.html
.. _AudioFolder: ../Reference_Manual/topo.pattern.audio.AudioFolder-class.html
.. _contrib/hegdeessen.py: ../../contrib/hegdeessen.py
.. _linearly\_interpolate: ../Reference_Manual/topo.misc.util-module.html#linearly_interpolate
.. _clip\_upper: ../Reference_Manual/topo.base.arrayutil-module.html#clip_upper
.. _adding noise: ../User_Manual/noise.html
.. _line-by-line profiling: ../Developer_Manual/optimization.html#line-by-line
.. _Cython: http://www.cython.org
.. _ParameterizedFunction: ../Reference_Manual/param.parameterized.ParameterizedFunction-class.html
.. _topo.command: ../Reference_Manual/topo.command-module.html
.. _save\_plotgroup: ../Reference_Manual/topo.command.analysis.save_plotgroup-class.html
.. _measure\_sine\_pref: ../Reference_Manual/topo.command.analysis.measure_sine_pref-class.html
.. _GlobalParams: ../Reference_Manual/topo.misc.commandline.GlobalParams-class.html
.. _gradientplot: ../Reference_Manual/topo.command.pylabplots.gradientplot-class.html
.. _fftplot: ../Reference_Manual/topo.command.pylabplots.fftplot-class.html
.. _Sheet: ../Reference_Manual/topo.base.sheet.Sheet-class.html
.. _interfacing to external simulators: ../User_Manual/interfacing.html
.. _Translator: ../Reference_Manual/topo.pattern.Translator-class.html
.. _HalfRectifyAndPower: ../Reference_Manual/topo.transferfn.HalfRectifyAndPower-class.html
.. _Hysteresis: ../Reference_Manual/topo.transferfn.Hysteresis-class.html
.. _HomeostaticResponse: ../Reference_Manual/topo.transferfn.HomeostaticResponse-class.html
.. _ActivityCopy: ../Reference_Manual/topo.sheet.ActivityCopy-class.html
.. _CFPLF\_BCMFixed\_opt: ../Reference_Manual/topo.learningfn.optimized.CFPLF_BCMFixed_opt-class.html
.. _CFPLF\_Scaled\_opt: ../Reference_Manual/topo.learningfn.optimized.CFPLF_Scaled_opt-class.html
.. _HookList: ../Reference_Manual/param.HookList-class.html
.. _FeatureResponses: ../Reference_Manual/topo.analysis.featureresponses.FeatureResponses-class.html
.. _LISSOM: ../Reference_Manual/topo.sheet.lissom.LISSOM-class.html
.. _updating scripts: ../Downloads/update_script.html
.. _released: ../Downloads/index.html
.. _SVN: ../Downloads/cvs.html
.. _daily builds: http://buildbot.topographica.org
.. _performance measurement: http://buildbot.topographica.org
.. _IPython: http://ipython.scipy.org/
.. _misc/playerrobot.py: ../Reference_Manual/topo.misc.playerrobot-module.html
.. _misc/robotics.py: ../Reference_Manual/topo.misc.robotics-module.html
.. _PoissonSample: ../Reference_Manual/topo.outputfn.PoissonSample-class.html
.. _ScalingOF: ../Reference_Manual/topo.outputfn.ScalingOF-class.html
.. _NakaRushton: ../Reference_Manual/topo.outputfn.NakaRushton-class.html
.. _AttributeTrackingOF: ../Reference_Manual/topo.outputfn.AttributeTrackingOF-class.html
.. _CameraImage: ../Reference_Manual/topo.misc.robotics.CameraImage-class.html
.. _Jitter: ../Reference_Manual/topo.coordmapper.Jitter-class.html
.. _AndMask: ../Reference_Manual/topo.base.projection.AndMask-class.html
.. _OrMask: ../Reference_Manual/topo.base.projection.OrMask-class.html
.. _CompositeSheetMask: ../Reference_Manual/topo.base.projection.CompositeSheetMask-class.html
.. _decode\_feature: ../Reference_Manual/topo.command.analysis-module.html#decode_feature
.. _PipelineOF: ../Reference_Manual/topo.base.functionfamily.PipelineOF-class.html
.. _NumberGenerator: ../Reference_Manual/topo.numbergen.NumberGenerator-class.html
.. _update scripts: ../Downloads/update_script.html
.. _automatic daily builds: http://buildbot.topographica.org
.. _batch mode: ../User_Manual/batch.html
.. _saving bitmaps: ../User_Manual/commandline.html#saving-bitmaps
.. _control over GUI: ../User_Manual/commandline.html#scripting-gui
.. _reverse-correlation RF mapping: ../User_Manual/plotting.html#rfplots
.. _3D wireframe plotting: ../User_Manual/commandline.html#3d-plotting
.. _simplified bitmap plotting: ../User_Manual/plotting.html#measuring-preference-maps
.. _coordmapper: ../Reference_Manual/topo.coordmapper-module.html
.. _plotting 1: ../_static/071018_plotting1_ubuntu.png
.. _plotting 2: ../_static/071018_plotting2_ubuntu.png
.. _updated model editor screenshot: ../_static/071018_modeleditor_ubuntu.png
.. _Plotting: ../_static/topographica-0.9.3_ubuntu.png
.. _Model editor screenshot: ../_static/topographica-0.9.3_modeleditor_ubuntu.png
.. _PyCon 2007: http://us.pycon.org/TX2007/
.. _CVS: ../Downloads/cvs.html
.. _screenshot: ../_static/060607_topographica_win_screenshot.png
.. _model editor: ../User_Manual/modeleditor.html
.. _Computational Maps in the Visual Cortex: http://computationalmaps.org
.. _an extended set of examples of the types of models supported by Topographica: http://computationalmaps.org/docs/chapter5.pdf
.. _tutorial with ON/OFF LGN model: ../Tutorials/lissom_oo_or.html
.. _SOM retinotopy tutorial: ../Tutorials/som_retinotopy.html
.. _Mac OS X instructions: ../Downloads/cvs.html#osx
.. _developer manual: ../Developer_Manual/index.html
.. _partial user manual: ../User_Manual/index.html
.. _model editor (screenshot): ../_static/060220_model_editor_screen_shot.png
.. _generic Matlab-style plotting: ../User_Manual/commandline.html#pylab
.. _See the Linux screenshot: ../_static/060220_topographica_screen_shot.png
.. _reference manual: ../Reference_Manual/index.html
.. _LISSOM tutorial: ../Tutorials/lissom_oo_or.html
.. _Linux screenshot: ../_static/051107_topographica_screen_shot_white.png
.. _reStructuredText: http://docutils.sourceforge.net/docs/user/rst/quickref.html
.. _Sphinx: http://sphinx.pocoo.org
