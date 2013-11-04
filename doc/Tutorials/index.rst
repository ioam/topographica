*********
Tutorials
*********



Topographica comes with the following step-by-step guides to running
simulations:

:doc:`gcal`

How to run and test a simple orientation map simulation in the
Topographica Tk GUI using the GCAL cortical model from `Stevens et
al. (J. Neuroscience 2013)
<http://dx.doi.org/10.1523/JNEUROSCI.1037-13.2013>`_.  The tutorial
allows you to present various objects to a saved orientation map
network, and to visualize and analyze the responses. It also shows how
to develop a new simulation using different input patterns.

This tutorial supersedes an `older tutorial`_ using the LISSOM model
from  `Miikkulainen et al. (2005) <http://computationalmaps.org>`_.

:doc:`som_retinotopy`

How to run a model in the Topographica Tk GUI that develops
selectivity for position, mapping the input space to the cortical
space. The model uses the abstract SOM algorithm, focusing on the
basic principles of self-organization rather than modeling any
particular biological system.

|gcal_ipynb|_

This is an `IPython Notebook <http://ipython.org/notebook.html>`_ that
steps through the definition of the GCAL model used in the tutorial
above. This demonstrates how a Topographica model can be interactively
explored in the Notebook environment. Installation instructions, the
notebooks themselves and all the supporting code `may be found here
<https://github.com/ioam/topographica/tree/master/models/stevens.jn13>`_.

|stevens_jn13|_

This second `IPython Notebook <http://ipython.org/notebook.html>`_
uses the GCAL model definition notebook described above to reproduce
the figures shown in `Stevens et al. (J. Neuroscience 2013)
<http://dx.doi.org/10.1523/JNEUROSCI.1037-13.2013>`_. This notebook
demonstrates an agile, reproducible workflow using IPython Notebook
and Lancet as described in `this newly submitted paper
<http://homepages.inf.ed.ac.uk/jbednar/papers/stevens.fin13_submitted.pdf>`_
with installation instructions and supporting material `available here
<https://github.com/ioam/topographica/tree/master/models/stevens.jn13>`_.


These should be good starting points for seeing how Topographica
works and how to use a Topographica model. If you develop any other
tutorials for your own models, we would love to add them here!

.. Trick to get matching italic style for the links
.. _gcal_ipynb: ../_static/gcal_notebook.html
.. |gcal_ipynb| replace:: *GCAL Model definition*

.. _stevens_jn13: ../_static/stevens_jn13_notebook.html
.. |stevens_jn13| replace:: *Reproducing the GCAL paper*

.. _older tutorial: ./lissom_oo_or.html
