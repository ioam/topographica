 
*****
Links
*****



The development of Topographica was supported in part by the U.S.
`National Institutes of Mental Health`_ under `Human Brain Project`_
grant 1R01-MH66991, and by the U.S. `National Science Foundation`_
under grant IIS-9811478.

Educational applications of Topographica are supported in part by
the University of Edinburgh `Doctoral Training Centre in
Neuroinformatics`_, with funding from the `Engineering and Physical
Sciences Research Council`_ and the `Medical Research council`_
through the `Life Sciences Interface`_. For sample assignments see
the `web page`_ for the course `Computational Neuroscience of Vision
(CNV)`_ offered by the `School of Informatics`_ of the `University
of Edinburgh`_.

If you use this software in work leading to an academic publication,
please cite this reference:

    James A. Bednar.
    `Topographica: Building and Analyzing Map-Level Simulations from
    Python, C/C++, MATLAB, NEST, or NEURON Components. 
    <http://dx.doi.org/10.3389/neuro.11.008.2009>`_
    Frontiers in Neuroinformatics, 3:8, 2009.

or in BibTeX format:

::

    @Article{bednar:fin09,
      author  = "James A. Bednar",
      title   = "{Topographica}: {B}uilding and Analyzing Map-Level
                 Simulations from {Python}, {C/C++}, {MATLAB}, {NEST},
                 or {NEURON} Components",
      journal = "Frontiers in Neuroinformatics",
      year    = 2009,
      volume  = 3,
      pages   = 8,
      url     = "http://dx.doi.org/10.3389/neuro.11.008.2009",
    }

.. figure:: ../images/cmvc-cover-icon.jpg
   :align: right
   :alt: Computational Maps in the Visual Cortex (2005) Miikkulainen, Bednar, Choe, and Sirosh

Many of the ideas in Topographica were first
developed in conjunction with our book:

    Risto Miikkulainen, James A. Bednar, Yoonsuck Choe, and Joseph
    Sirosh. `Computational Maps in the Visual Cortex`_. Springer,
    Berlin, 2005.

The book has background on cortical maps in general, descriptions of
the various levels of modeling, and a detailed presentation of the
scaling equations that underlie Sheet coordinates (which are also
described in `Bednar et al. Neuroinformatics, 2:275-302, 2004`_).

Other useful simulators:

`Neuron`_, `GENESIS`_, and `MOOSE`_

Detailed low-level modeling of neurons and small networks. It is
possible to use these simulators for topographic maps, but the
computational requirements are usually extremely high, and typical
users simulate much smaller networks. Note that there are now
(3/2007) Python bindings for Neuron, so it should be practical to
wrap a Neuron simulation into a Topographica Sheet for analysis.

`Brian`_

Brian is a pure Python simulator (like Topographica) that supports
spiking models using a very clear differential-equation-based
specification style.  It's targeted more at networks of neurons than
at organized maps, but can also be useful for maps.

`NEST`_

NEST (formerly called BLISS) is a general-purpose simulator for
large networks of neurons, but without an explicit focus on
topography. Much of NEST is based on a custom stack-based scripting
language (like RPN calculators or PostScript) that is not nearly as
friendly as Python, and requires much more of the simulation code to
be written in C. On the other hand, NEST does provide many useful,
high-performance primitives, has good parallel computer support, and
can be particularly useful for models that do not fit Topographica's
abstractions closely. NEST now offers a Python interface, which can
be used to wrap a spiking NEST simulation as a Topographica sheet.
See `Bednar, Frontiers in Neuroinformatics 2009`_ for an example of
such an interface.

`NCS`_

The NCS simulator focuses on large-scale simulation of networks of
spiking neurons, using C/C++ with a custom specification language
rather than an extensible scripting language. Thus it is likely to
be useful primarily for running simulations very similar to those
built by the developers, rather than being fully extensible as
Topographica is.

`iNVT`_

iLab Neuromorphic Vision Toolkit is a high-performance
computer-vision oriented C++ toolkit from Koch and Itti with support
for saliency maps for modeling attention. It has a strong focus on
topographically organized regions, but at a high level of
abstraction, and without specific support for learning and
development. As for NCS, it also requires more time-consuming and
less flexible development in C++.

`Emergent`_

Formerly called PDP++, Emergent focuses on simulating neural
networks of various types, for either engineering or cognitive
science applications. Although there is support for networks
arranged as maps (e.g. Kohonen SOMs), the interface is designed to
make the influence of individual units clear, which is not typically
useful for analyzing maps. In any case, Emergent has less emphasis
on simulating biological experiments and brain tissue than does
Topographica, instead concentrating on more abstract systems that
perform specific tasks.

`LENS`_

Simple, basic artificial neural-network simulator (primarily
abstract backpropagation networks, but also has support for Kohonen
SOM models of topographic maps).

`Catacomb`_

Highly graphical Java-based simulator covering numerous levels, from
ion channels to behavioral experiments. Can be used for some of the
same types of models supported by Topographica, but does not have an
explicit focus on topographically organized areas. May not currently
be maintained.

Other potentially useful simulators are listed at the `Emergent`_
site.

.. _National Institutes of Mental Health: http://www.nimh.nih.gov
.. _Human Brain Project: http://www.nimh.nih.gov/neuroinformatics
.. _National Science Foundation: http://www.nsf.gov
.. _Doctoral Training Centre in Neuroinformatics: http://anc.ed.ac.uk/neuroinformatics
.. _Engineering and Physical Sciences Research Council: http://www.epsrc.ac.uk/
.. _Medical Research council: http://www.mrc.ac.uk/
.. _Life Sciences Interface: http://www.epsrc.ac.uk/ResearchFunding/Programmes/LifeSciencesInterface/
.. _web page: http://www.inf.ed.ac.uk/teaching/courses/cnv/
.. _Computational Neuroscience of Vision (CNV): http://www.inf.ed.ac.uk/teaching/courses/cnv/
.. _School of Informatics: http://www.inf.ed.ac.uk
.. _University of Edinburgh: http://www.ed.ac.uk
.. _Understanding Neural Maps with Topographica: http://www.brains-minds-media.org/archive/1402
.. _Computational Maps in the Visual Cortex: http://computationalmaps.org
.. _`Bednar et al. Neuroinformatics, 2:275-302, 2004`: http://nn.cs.utexas.edu/keyword?bednar:neuroinformatics04
.. _Neuron: http://kacy.neuro.duke.edu/
.. _GENESIS: http://www.genesis-sim.org/GENESIS/
.. _MOOSE: http://moose.ncbs.res.in
.. _Brian: http://briansimulator.org
.. _Catacomb: http://askja.bu.edu/catacomb
.. _NEST: http://www.nest-initiative.org
.. _Bednar, Frontiers in Neuroinformatics 2009: http://dx.doi.org/10.3389/neuro.11.008.2009
.. _NCS: http://brain.unr.edu/ncsDocs/
.. _iNVT: http://ilab.usc.edu/toolkit/documentation.shtml
.. _Emergent: http://grey.colorado.edu/emergent/index.php/Main_Page
.. _LENS: http://www.cs.cmu.edu/~dr/Lens

