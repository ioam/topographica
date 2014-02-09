==================================================
Replicating Stevens et al. (J. Neuroscience, 2013)
==================================================

This directory includes all the code necessary to re-run all the
simulations and regenerate all the figures detailed in `Stevens et
al. (2013) <http://www.jneurosci.org/content/33/40/15747.full>`_.

| @article{Stevens2013,
|   author = {Stevens, Jean-Luc R. and Law, Judith S. and
|   Antol\\'{i}k, J\\'{a}n and Bednar, James A.},
|   title = {Mechanisms for Stable, Robust, and Adaptive
|   Development of Orientation Maps in the Primary Visual Cortex},
|   journal = {The Journal of Neuroscience},
|   volume = {33},
|   number = {40},
|   pages = {15747-15766},
|   year = {2013},
|   doi = {10.1523/JNEUROSCI.1037-13.2013},
|   url = {http://www.jneurosci.org/content/33/40/15747.full}
| }


Getting Started
---------------

To run the model, you will need the Topographica simulator. To install
from GitHub, you may follow `these instructions
<https://github.com/ioam/topographica>`_ which includes the
instructions for installing `IPython Notebook
<http://ipython.org/notebook>`_.

With Topographica installed you can now explore the model from this
directory using the Topographica GUI without requiring IPython
Notebook:

::

   ../../topographica -g gcal.ty

To go further, using IPython notebook to explore how the model is put
together and how to put results together into figures, you can run the
following command in this directory:

::

   ../../topographica -n

Now if you visit localhost:8888 in your browser you should be able to
select the '``stevens_jn13``' or '``gcal``' notebooks. Note that if a
port number other than 8888 be required, the appropriate port number
will be shown in the terminal. IPython >=1.0 is required.

Running the live notebooks allows you to explore the model
iteratively. If you simply wish to view the static contents of these
notebooks, you may view the following two HTML versions:

- `Model definition <http://ioam.github.io/media/gcal.html>`_: A
  notebook that simultaneously defines the model and explores
  it. Running the live version of this notebook generates the
  Topographica model file '``gcal.ty``' and will regenerate the
  contents shown in the HTML version.

- `Simulation and Figures
  <http://ioam.github.io/media/stevens_jn13.html>`_:
  Defines all 842 model simulations needed to reproduce all the
  figures, allows you to launch them and automatically builds the
  corresponding SVG figures used in publication. Although running the
  full set of simulations is computationally expensive, the live
  notebook allows you to select a small subset before launching the
  jobs.


Directory organization
----------------------

There is a README file in every subdirectory of
'``jn13_figures``'. The overall organization is as follows:

- ``jn13_figures/__init__.py``: Python code to dynamically generate
  the SVG figures.
- ``jn13_figures/figures``: Static SVG figures (experimental data) and
  symbolic links to dynamically generated figures.
- ``jn13_figures/lib``: Utilities used by ``__init__.py``,
  ``gcal.ipynb`` and ``stevens_jn13.ipynb``. See the README file for
  more details about the files in this directory.
- ``jn13_figures/output``: Simulation output and the figure build
  directory ``build_dir``.
- ``jn13_figures/templates``: SVG templates for all the dynamically
  generated figures. Raster placeholders snapshots are stored in the
  ``snapshots`` subdirectory.
