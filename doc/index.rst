****
Home
****

Recent News
-----------
.. include:: news.rst

Topographica
------------

.. figure:: images/Topo-arch-white.jpg
   :align: right
   :alt: Sample architecture

Topographica is a software package for computational modeling of neural
maps, developed by the `Institute for Adaptive and Neural Computation`_
at the `University of Edinburgh`_ and the `Neural Networks Research
Group`_ at the `University of Texas at Austin`_. Development of
Topographica has been funded by the `NIMH Human Brain Project`_ under
grant 1R01-MH66991. The goal is to help researchers understand brain
function at the level of the topographic maps that make up sensory and
motor systems.

Topographica is intended to complement the many good low-level neuron
simulators that are available, such as `Genesis`_ and `Neuron`_. Those
simulators focus on modeling the detailed internal behavior of neurons
and small networks of them. Topographica instead focuses on the
large-scale structure and function that is visible only when many
thousands of such neurons are connected into topographic maps containing
millions of connections. Many important phenomena cannot be studied
without such large networks, including the two-dimensional organization
of visual orientation and motion direction maps, and object segmentation
and grouping processes.

To make such models practical, in Topographica the fundamental unit is a
sheet of neurons, rather than a neuron or a part of a neuron. For most
simulations, the sheets can be implemented at a high level, consisting
of abstract firing-rate or integrate-and-fire neurons. When required for
validation or for specific phenomena, Topographica can easily be
extended using a Sheet that interfaces to more detailed neuron models in
other simulators. Less-detailed sheets can also be used temporarily,
e.g. when interacting with the model in real time. Throughout,
Topographica makes it simple to use an appropriate level of detail and
complexity, as determined by the available computing power, phenomena of
interest, and amount of biological data available for validation.

Compared to writing code for such models from scratch, Topographica
makes it simple to define multiple interconnected sheets, to use
localized patches of connections, to control the inputs to each sheet
and analyze the outputs, and to manage results from models and
simulations as they are developed and improved over time.

The figure at top right shows an example Topographica model of the early
stages in the visual system, modeling how retinal input is transformed
by the thalamus, primary visual cortex, and higher cortical areas.
Because Topographica is a general-purpose map simulator, it also
supports any other sensory modality that is organized into topographic
maps, such as touch and hearing, as well as motor areas.

Topographica is freely available for downloading, and is an open source
project (`BSD license`_) whose capabilities can be extended and modified
by any user. We welcome contributions from users, and invite interested
people to join our globally distributed development team.

Also see our `Publications list`_ for results from simulations run with
Topographica, such as this `2012 review paper`_.

.. _Institute for Adaptive and Neural Computation: http://www.anc.ed.ac.uk
.. _University of Edinburgh: http://www.ed.ac.uk
.. _Neural Networks Research Group: http://www.cs.utexas.edu/users/nn/
.. _University of Texas at Austin: http://www.utexas.edu
.. _NIMH Human Brain Project: http://grants.nih.gov/grants/guide/pa-files/PAR-03-035.html
.. _Genesis: http://www.genesis-sim.org/GENESIS/
.. _Neuron: http://kacy.neuro.duke.edu/
.. _BSD license: http://opensource.org/licenses/bsd-license.php
.. _Publications list: Home/pubs.html
.. _2012 review paper: http://dx.doi.org/10.1016/j.jphysparis.2011.12.001

.. toctree::
    News/index
    Downloads/index
    Tutorials/index
    User_Manual/index
    Developer_Manual/index
    Forums/index
    Team_Members/index
    FAQ/index
    Links/index
    Home/pubs
