*********
Tutorials
*********

Topographica comes with the following step-by-step guides to running
simulations.

Tutorials using the Tk GUI
--------------------------

The Tk GUI is a good way to explore a model without needing to
write any additional code.

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


How to run and explore the SOM algorithm in the notebook environment.
This tutorial covers the same material as the first SOM tutorial,
illustrating how a model may be explored without requiring the GUI. In
addition, this notebook includes several videos showing how the SOM
develops over time, showcasing a feature only available in the
notebook environment.


|gcal_ipynb|_

A static HTML snapshot of a notebook that illustrates how to
define, explore, and analyze the GCAL model (see above) from
within IPython Notebook.  In practice, you'll want to try out the
actual notebook for yourself, which you can do by downloading the
latest git version of Topographica using `these instructions
<https://github.com/ioam/topographica/tree/master/models/stevens.jn13#topographica-installation>`_.

|stevens_jn13|_

Building on the GCAL IPython Notebook described above, this second
notebook shows how to reproduce
every figure from `Stevens et al. (J. Neuroscience 2013)
<http://dx.doi.org/10.1523/JNEUROSCI.1037-13.2013>`_. This notebook
is the final result of an agile workflow for doing reproducible
research based on IPython Notebook and
`Lancet <https://github.com/ioam/lancet>`_, as described in
`this newly submitted paper
<http://homepages.inf.ed.ac.uk/jbednar/papers/stevens.fin13_submitted.pdf>`_.
The link above takes you to a static copy of the notebook output; to
replicate it for yourself just follow
`these instructions
<https://github.com/ioam/topographica/tree/master/models/stevens.jn13#topographica-installation>`_.

Each of these tutorials should be a good starting point for seeing how
Topographica works and how to use a Topographica model in practice. If
you develop any other tutorials for your own models, we would love to
add them here!

.. _gcal_gui_tutorial: ./gcal.html
.. |gcal_gui_tutorial| replace:: GCAL GUI Tutorial

.. _som_retinotopy_gui: ./som_retinotopy.html
.. |som_retinotopy_gui| replace:: SOM Retinotopy GUI Tutorial

.. Trick to get matching italic style for the links
.. _gcal_ipynb: ../_static/gcal.html
.. |gcal_ipynb| replace:: *GCAL Model definition*

.. _stevens_jn13: ../_static/stevens_jn13.html
.. |stevens_jn13| replace:: *Replicating Stevens et al. (J. Neuroscience 2013)*

.. _older tutorial: ./lissom_oo_or.html

.. _som_ipynb: http://ioam.github.io/media/som_retinotopy.html
.. |som_ipynb| replace:: *SOM Retinotopic Map*
