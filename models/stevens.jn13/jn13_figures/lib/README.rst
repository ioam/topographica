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
