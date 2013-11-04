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


Running the Notebooks
---------------------

If all the necessary software dependencies are satisfied, including
IPython notebook, you can start exploring the model by running the
following command in this directory:

::

   ipython notebook

Now you should be able to select the '``stevens_jn13``' or '``gcal``' notebooks.

Running the live notebooks allows you to explore the model
iteratively. If you simply wish to view the static contents of these
notebooks, you may view the following two HTML versions:

- `Model definition
  <http://nbviewer.ipython.org/urls/raw.github.com/ioam/topographica/master/models/stevens.jn13/gcal.ipynb>`_:
  An interactive notebook that simultaneously defines the model and
  explores it. Running this notebook generates the Topographica model
  file '``gcal.ty``'.

- `Simulation and Figures
  <http://nbviewer.ipython.org/urls/raw.github.com/ioam/topographica/master/models/stevens.jn13/stevens_jn13.ipynb>`_:
  Defines all 842 model simulations needed to reproduce all the
  figures, allows you to launch them and automatically builds the
  corresponding SVG figures used in publication. Although running the
  full set of simulations is computationally expensive, you select a
  small subset before launching the jobs.


Topographica Installation
-------------------------

To run the model without using `IPython Notebook <http://ipython.org/>`_ you will need the Topographica simulator. To install from GitHub, you may follow `these instructions <https://github.com/ioam/topographica>`_. In brief:

::

   git clone git://github.com/ioam/topographica.git
   cd topographica
   git submodule update --init

Topographica itself depends on numpy, PIL and scipy which may be installed with pip:

::

   pip install numpy PIL scipy


With Topographica installed you can now explore the model from this
directory using the Topographica GUI:

::

   ../../topographica -g gcal.ty

The rest of the instructions show how to go further, using IPython
notebook to explore how the model is put together and how to put
results together into figures.


Installing IPython Notebook
---------------------------

To run the contents of '``stevens_jn13.ipynb``' and
'``gcal.ipynb``' and reproduce all the figures in the paper, you will
need IPython (>=1.0) and the ability to run the IPython notebook. All
the required dependencies may be installed with pip as follows:

::

   pip install ipython jinja tornado pyzmq

You can then follow the instructions above for 
`running the notebooks
<https://github.com/ioam/topographica/tree/master/models/stevens.jn13#running-the-notebooks>`.

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
