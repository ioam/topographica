*********
Tutorials
*********

Topographica comes with the following step-by-step guides to running
simulations.

Tutorials using the Tk GUI
--------------------------

The Tk GUI is a good way to explore a model without needing to
write any additional code.  However, the GUI only supports a limited
set of operations, and so after doing an initial exploration using the
GUI, we recommend using the more-powerful IPython notebook interface
illustrated in the following section.


|gcal_gui_tutorial|_

How to run and test a simple orientation map simulation using the
GCAL cortical model from
`Stevens et al. (J. Neuroscience 2013) <http://dx.doi.org/10.1523/JNEUROSCI.1037-13.2013>`_.
The tutorial allows you to present various objects to a saved
orientation map network, and to visualize and analyze the
responses. It also shows how to develop a new simulation using
different input patterns.

This tutorial supersedes an `older tutorial`_ using the LISSOM model
from  `Miikkulainen et al. (2005) <http://computationalmaps.org>`_.

|som_retinotopy_gui|_

How to run a model that develops selectivity for position,
mapping the input space to the cortical space. The model uses the
abstract SOM algorithm, focusing on the basic principles of
self-organization rather than modeling any particular biological
system.


IPython Notebooks
-----------------

In addition to the GUI-based way of interacting with Topographica
illustrated in the tutorials above, you can also use `IPython Notebook
<http://ipython.org/notebook.html>`_, which provides a command-line
prompt that allows you to weave together Python code, textual output,
and graphical output.  This approach makes it easier to modify a
model, look at parts of it not currently exposed in the GUI, and to
develop new types of analyses not yet offered in the GUI.


|som_ipynb|_


How to run and explore the SOM algorithm in the notebook environment
(same topics as the above GUI tutorial, but now showing how the
commands are invoked and can be modified).  In addition, this notebook
includes several videos showing how the SOM develops over time,
showcasing a feature only available in the notebook environment.


|gcal_tutorial|_

An exploration of GCAL or LISSOM model in the notebook environment.
This tutorial covers the same material as the first GCAL tutorial, but
adds animations showing how GCAL develops over time.


|gcal_collector|_

A demonstration of how the Collector class can be defined and used to
collect measurements from a given model over development. Here the
GCAL model is explored using more involved analysis than presented in
the basic GCAL tutorial. Analysis over development includes
orientation preference histograms, hypercolumn distance estimation,
pinwheel finding and the pinwheel density estimation.

|gcal_all|_

The above tutorials all focus on orientation maps.  This tutorial
shows how to use GCAL for developing maps for other visual feature
dimensions, in any combination.  Making all maps develop well together
is an ongoing project (and requires much greater computational
resources than individual maps), but the individual maps and most
combinations should be usable already.

Other GCAL notebooks replicating `Stevens et al. (J. Neuroscience 2013)
<http://dx.doi.org/10.1523/JNEUROSCI.1037-13.2013>`_ may be found
`here
<https://github.com/ioam/topographica/tree/master/models/stevens.jn13>`_. These
notebooks only aim to replicate the published results and are *not*
up-to-date demonstrations of the recommended workflow for using
Topographica in the IPython Notebook environment.

Each of these tutorials should be a good starting point for seeing how
Topographica works and how to use a Topographica model in practice. If
you develop any other tutorials for your own models, we would love to
add them here!


.. Notebook tutorials
.. _som_ipynb: http://ioam.github.io/media/topo/som_retinotopy.html
.. |som_ipynb| replace:: SOM Retinotopic Map

.. _gcal_tutorial: http://ioam.github.io/media/topo/GCAL_Tutorial.html
.. |gcal_tutorial| replace:: GCAL Tutorial

.. _gcal_collector: http://ioam.github.io/media/topo/GCAL_Collector.html
.. |gcal_collector| replace:: GCAL Collector Tutorial

.. _gcal_all: http://ioam.github.io/media/topo/gcal_all.html
.. |gcal_all| replace:: GCAL All-Maps Tutorial

.. GUI tutorials
.. _gcal_gui_tutorial: ./gcal.html
.. |gcal_gui_tutorial| replace:: GCAL GUI Tutorial

.. _som_retinotopy_gui: ./som_retinotopy.html
.. |som_retinotopy_gui| replace:: SOM Retinotopy GUI Tutorial

.. _older tutorial: ./lissom_oo_or.html

.. Unused links (though still live)
.. _gcal_ipynb: ../_static/gcal.html
.. |gcal_ipynb| replace:: GCAL Model definition

.. Trick to get matching italic style for the links
.. _stevens_jn13: ../_static/stevens_jn13.html
.. |stevens_jn13| replace:: *Replicating Stevens et al. (J. Neuroscience 2013)*
