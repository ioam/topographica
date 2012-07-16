<H2>Detailed changes</A></H2>

Significant changes for each new release are listed on the <A
HREF="index.html">News</A> page. This page lists lower-level changes
that might affect existing users who are upgrading from one release to
the next.

<H3>Upcoming release</H3>

Changes since 0.9.7. Fully updated 2011/10/09; some updates as of 2012/03/27. 

<H4>Changes that might require attention in your code or workflow</H4>
<ul>
  <li>r12105: Moved base.boundingregion, base.sheetcoords,
  base.patterngenerator, misc.patternfn, and topo.pattern/* into
  imagen package, though all will continue to be usable in their
  original locations.
  <li>r12103: Moved TransferFn and IdentityTF out of
  functionfamily.py, and *Threshold and DivisiveNormalize* out of
  topo.transferfn, into new file imagen.transferfn for use in ImaGen,
  though all will continue to be usable in their original locations.
  <li>r12102: Moved RandomDotStereogram from topo.pattern.rds to
  topo.pattern.random, and deleted rds.py.
  <li>r12095: Moved topo.numbergen to a separate numbergen directory
  for use in ImaGen, though it will continue to be usable as
  topo.numbergen for the time being.  
  <li>r11906: OpenMP changes to the optimized learningfns and 
  transferfns mean that 'private' attributes _has_norm_total and 
  _norm_total are now implemented differently (with arrays). Any 
  code directly accessing these attributes may break; as always
  the right way to use norm_total from Python is through the
  norm_total property, and to use 'del norm_total' to indicate that
  the norm_total is stale.
  <li>r11904, r11916: Changed map measurement code to use an
  extensible hierarchy of objects for extracting the preference and
  selectivity values from a histogram.  Any custom map measurement
  code derived from those used in topo.command.analysis, or custom
  parameter values mentioning weighted_average, will 
  need updating.  Any .ty files that set featuremap selectivity scales and/or
  cyclic ranges should be updated to set 
  topo.misc.distribution.DSF_WeightedAverage.selectivity_scale instead
  of topo.analysis.featureresponses.FeatureMaps.selectivity_multiplier,
  and SheetView.cylic_range instead of SheetView.norm_factor.
<li>r11896: Changed interface of topo.command.activityplot (rarely
  used so far) and changed "Plot with axis labels" right-click option
  in plots to "Plot in matrix coords", to acknowledge new option
  "Plot in sheet coords".
<li>r11862: 'make OTHER_PYTHON=/path/to/python topographica-other-python' is now '/path/to/python create_topographica_script.py'. Additionally, Windows users can then run '/path/to/python windows_postinstall.py create_batchfile' to get an executable topographica.bat.
<li>r11817: BCMFixed removed from learningfn.projfn
<li>r11803: Output path now ~/Documents/Topographica [CB: not yet finalized]
<li>r11715: 'make OTHER_PYTHON=... topographica-other-python' is now 'make PYTHON=... topographica-external-python'. But this option will likely be removed from the Makefile (see r11862).

<!-- CEBALERT: check backwards compatibility; is there a new feature here?
r11611 | bilal-khan | 2011-05-24 15:06:57 +0100 (Tue, 24 May 2011) | 1 line
Changed paths:
   M /trunk/topographica/param/__init__.py

Changed resolve_path so it now uses a boolean param to determine if the path is to a file or a folder. Changed Filename and Foldername to use the new param.

r11608 | bilal-khan | 2011-05-08 02:34:05 +0100 (Sun, 08 May 2011) | 1 line
Changed paths:
   M /trunk/topographica/param/__init__.py

Added a path_type param to resolve_path, changed it from an arg.

r11563 | bilal-khan | 2011-05-02 19:16:26 +0100 (Mon, 02 May 2011) | 1 line
Changed paths:
   M /trunk/topographica/param/__init__.py

Copied the resolve_path class to resolve_path2, a generalised version that checks for the existance of a path and does not discriminate between files and folders. Created 2 new classes resolve_file_path and resolve_folder_path that take the output of resolve_path and simply check if it is a file or a folder respectively. Created a new Path class that is a generalised version of the old Filename class, changed the Filename class to inherit from this new Path class, created a new Foldername class that also inherits from the Path class. All changes are backwards compatible.

-->

<!-- CEBALERT: check Bilal's topoconsole error printing. 

e.g.
------------------------------------------------------------------------
r11614 | bilal-khan | 2011-05-24 15:07:28 +0100 (Tue, 24 May 2011) | 1 line
Changed paths:
   M /trunk/topographica/topo/misc/commandline.py

Removed cli option -t to display full traceback (full tracebacks are now on by default).
------------------------------------------------------------------------
r11613 | bilal-khan | 2011-05-24 15:07:18 +0100 (Tue, 24 May 2011) | 1 line
Changed paths:
   M /trunk/topographica/topo/tkgui/topoconsole.py

Made output of the full trace on error the default.

(there are more)

--> 

<li>r11532: Removed apparently unmaintained Gnosis Utils. Removed experimental xml snapshot saving.
<li>r11500: Simplified user startup files: ~/.topographica for linux/OS X, and ~/topographica.ini for Windows.
<li>r11482: Changed default connection delay to be nonzero, and made negative values illegal.  
<li>r11440: Removed unused BLT.
<li>r11336: No longer using LATEST_STABLE svn branch. 


<!-- CEBALERT: check for changes that have a reasonable chance of affecting a user.
------------------------------------------------------------------------
r11316 | ceball | 2010-07-27 18:52:53 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/analysis/featureresponses.py
   M /trunk/topographica/topo/analysis/vision.py
   M /trunk/topographica/topo/command/analysis.py
   M /trunk/topographica/topo/learningfn/basic.py
   M /trunk/topographica/topo/learningfn/projfn.py
   M /trunk/topographica/topo/learningfn/som.py
   M /trunk/topographica/topo/sheet/lissom.py
   M /trunk/topographica/topo/sheet/saccade.py

Removed unused imports.

------------------------------------------------------------------------
r11315 | ceball | 2010-07-27 18:43:01 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/plotting/plotgroup.py
   M /trunk/topographica/topo/sheet/basic.py
   M /trunk/topographica/topo/sheet/optimized.py

Removed unused imports.
------------------------------------------------------------------------
r11314 | ceball | 2010-07-27 18:18:52 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/plotting/bitmap.py
   M /trunk/topographica/topo/plotting/plot.py
   M /trunk/topographica/topo/plotting/plotfilesaver.py
   M /trunk/topographica/topo/transferfn/optimized.py

Removed unused imports.
------------------------------------------------------------------------
r11310 | ceball | 2010-07-27 17:56:14 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/tkgui/editor.py
   M /trunk/topographica/topo/tkgui/featurecurvepanel.py
   M /trunk/topographica/topo/tkgui/plotgrouppanel.py
   M /trunk/topographica/topo/tkgui/projectionpanel.py
   M /trunk/topographica/topo/tkgui/templateplotgrouppanel.py
   M /trunk/topographica/topo/tkgui/testpattern.py
   M /trunk/topographica/topo/tkgui/topoconsole.py

Removed unused imports.
------------------------------------------------------------------------
r11304 | ceball | 2010-07-27 17:35:22 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/misc/memuse.py
   M /trunk/topographica/topo/misc/trace.py
   M /trunk/topographica/topo/misc/util.py
   M /trunk/topographica/topo/transferfn/misc.py

Removed unused imports.
------------------------------------------------------------------------
r11296 | ceball | 2010-07-27 15:39:42 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/command/analysis.py
   M /trunk/topographica/topo/command/basic.py
   M /trunk/topographica/topo/command/pylabplot.py
   M /trunk/topographica/topo/coordmapper/basic.py

Removed unused imports.
------------------------------------------------------------------------
r11293 | ceball | 2010-07-27 15:19:32 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/misc/patternfn.py
   M /trunk/topographica/topo/pattern/image.py
   M /trunk/topographica/topo/pattern/random.py
   M /trunk/topographica/topo/pattern/rds.py

Removed unused imports.
------------------------------------------------------------------------
r11290 | ceball | 2010-07-27 14:42:46 +0100 (Tue, 27 Jul 2010) | 1 line
Changed paths:
   M /trunk/topographica/topo/base/arrayutil.py

Removed unused import and fixed spacing.
------------------------------------------------------------------------
-->
</ul>

<P>Heavy development of audio-related files continued, so there were multiple changes.

<!--Stable now?-->

<H4>New features</H4>

Most features implemented for this release are recorded in our <A
HREF="https://sourceforge.net/tracker/?func=&group_id=53602&atid=470932&assignee=&status=&category=&artgroup=&keyword=&submitter=&artifact_id=&assignee=&status=&category=&artgroup=2306092&submitter=&keyword=&artifact_id=&submit=Filter&mass_category=&mass_priority=&mass_resolution=&mass_assignee=&mass_artgroup=&mass_status=&mass_cannedresponse=">feature
request tracker</A>.

<P>Smaller additions:

<ul>
<!-- commented out because there might have been other additions since
the 'last updated' date that should be added before this one
<li>r11853: Fixed quoting of command used to launch a batch run (allowing it to be copied and pasted to re-run).
--> 
<li>r11756: all tests can be run from Python (runtests.py) without needing the Makefile.
<li>r11491: Added skip parameter for topographic grid plots.
<li>r11487: Made Model Editor diagrams work well for large numbers of dimensions; still not perfect for small numbers of dimensions and/or some combinations of dimensions.
<li>r11485: added a method to subtract distributions, useful in manipulating multiple feature responses.
<li>r11403: added Cython CFPDotProduct function.
<li>r11379: Added the measure of a secondary orientation preference, and plotting facilities
for the secondary orientation by pseudo-colors, and the combination of primary
and secondary orientation as segments in each unit.
<li>r11360: Added vector versions of disp_key_white_vert_small.png for publications

</ul>



<H4>Bug fixes</H4>

Most bugs fixed for this release are recorded in our <A HREF="https://sourceforge.net/tracker/?func=&group_id=53602&atid=470929&assignee=&status=&category=&artgroup=&keyword=&submitter=&artifact_id=&assignee=&status=&category=&artgroup=2283791&submitter=&keyword=&artifact_id=&submit=Filter&mass_category=&mass_priority=&mass_resolution=&mass_assignee=&mass_artgroup=&mass_status=&mass_cannedresponse=">bug tracker</A>.

<P>Smaller fixes:

<ul>
<li>r11772: Fix pickling of h_to_*() functions in examples/lissom.ty.
<li>r11770: Include test data in packages (e.g. debs), allowing tests to be run.
<li>r11706: Ensure times are converted to simulation time's type rather than relying on the type of the outcome of operations such as add(number,simulation time) to be simulation time's type. Allows newer versions of gmpy 1 to work for simulation's time (see http://code.google.com/p/gmpy/issues/detail?id=44).
<!-- CEBALERT: not part of interface?
<li>r11701: Changed param.concrete_descendents to work on classes of any type, not just Parameterized classes.
-->
<li>r11623: Corrected bug with Integer param where default=None was not being allowed even when allow_None was set.
<li>r11552: Replaced the get_all_slots(class) function with get_occupied_slots(instance), fixing pickling error for instances of certain classes.
<li>r11551: Fixed default value bug in param.Composite (if not set to a new list on initialization, attribs list could otherwise be shared between instances).
<li>r11543: Fixed bug detecting a value that is different from the default (when value or default is a numpy array).
<!--
<li>r11452: Data from speed-tests is now stored in different folder for each hostname, to prevent overwriting of one machine's data by another when ~ is shared (e.g. on DICE).
<li>r11441: Changed GCAL example to use sheet.lissom.LISSOM rather than sheet.lissom.JointScaling(apply_scaling=False). There should be no change, since JointScaling with apply_scaling=False appears to be equivalent to LISSOM.
<li>r11421: Rather than requiring an existing Tk instance to be passed to initialize(), look for one in the standard location (Tkinter._default_root).
<li>r11417: Fixed long-standing bug in PickleMain that was preventing Topographica simulations from being pickled using pickle (rather than cPickle, the default).
<li>r11401: Fixed bug in 'AllTogether' plot normalization; previously, normalization was incorrect when there was a mixture of positive-value and negative-value plots.

<li>r11359: Fixed color bar spacing in topo/command/disp_key_white_vert_small.png
<li>r11324: Use resolve_path() in load_snapshot().
<li>r11322: Do not pickle resolve_path's search_paths and normalize_path's prefix.
<li>r11321: Added option to prevent pickling of a Parameter's default value.
<!--
<li>r11312: In topo/plotting/plotgroup.py: Fixed error calling a method; not sure why we've never seen a failure.
-->
<li>r11302: In topo/misc/genexamples.py, fixed undefined name error if examples not found.
<li>r11295: Fixed error in line() function causing it to fail when smoothing was set to 0.
</ul>


<!--
<H3>Release 0.9.7</H3>
...
-->

