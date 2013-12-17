===============
Utility library
===============

The directory contains all the support code for
``jn13_figures/__init__.py`` and the ``gcal.ipynb`` and
``stevens_jn13.ipynb`` notebooks.

- ``analysis.py``: Code for analysing map stability, locating
  pinwheels and estimating the hypercolumn distance. Used of the
  course of each simulation as defined in
  ``measurement.py``. Stability analysis is also used directly in
  ``jn13_figures/__init__.py``.
- ``measurement.py``: Defines analysis functions that are run over the
  course of each simulation. Measurements of orientation selectivity
  and preference are returned together with the corresponding analysis
  data.
- ``vectorplots.py``: Vector plotting using matplotlib. Generates
  various types of histograms, "stream" plots, pinwheel and contours
  overlays and scalebars.
- ``rasterplots.py``: Raster image processing using PIL. Used to
  generate preference/selectivity maps, connection field (CF) images
  and polar FFT power spectra.
- ``compose.py``: Utilities to generate publication quality SVG
  figures using the templates defined in ``jn13_figures/templates``
- ``misc.py``: A small collection of minor helper utilities.

Normalization patch
~~~~~~~~~~~~~~~~~~~

The normalization factor in `Equation 9
<http://www.jneurosci.org/content/33/40/15747.full#disp-formula-9>`_
and the divisive post-synaptic weight normalization term in `Equation
10
<http://www.jneurosci.org/content/33/40/15747.full#disp-formula-9>`_
were originally stored in 32-bit accumulators at the time of
publication. These accumulators have since been updated to 64-bit
floats which has neglible effect on stable, robust models such as
GCAL. In contrast, the simpler L and AL models are unstable when
trained with high contrast stimuli (`Figure 7F
<http://www.jneurosci.org/content/33/40/15747.full#F7>`_, `Figure 8F
<http://www.jneurosci.org/content/33/40/15747.full#F7>`_). This
instability makes these two models highly sensitive to changes in
numerical accuracy such as this change in accumulator precision.

Although the published scientific conclusions are unaffected, a git
patch is offered to allow exact replication of the maps shown in
`Figure 7F <http://www.jneurosci.org/content/33/40/15747.full#F7>`_
and `Figure 8F
<http://www.jneurosci.org/content/33/40/15747.full#F7>`_:

- ``normalization.diff``: Apply this diff to revert from 64-bit
  accumulators to 32-bit accumulators for weight normalization. This
  allows the published example maps for the unstable L and AL models
  to be replicated exactly at high contrast. This patch may be applied
  as follows::

   # In Topographica git repository
   git checkout 6f4adb7df09e4c93fb383d04d0f04711896cce2c
   git apply normalization.diff
