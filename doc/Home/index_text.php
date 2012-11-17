<IMG src="../images/Topo-arch-white.jpg" 
     width="300" height="326" border="2" alt="Sample architecture" align="right"></A>

<P><!--img src="../images/T-bg.png" width="43" height="50" align="left" alt="T" border="2"-->Topographica 

is a software package for computational modeling of neural maps, developed by the 
<a target="_top" href="http://www.anc.ed.ac.uk">Institute for Adaptive and Neural Computation</a>
at the 
<a target="_top" href="http://www.ed.ac.uk">University of Edinburgh</a> and the 
<a target="_top" href="http://www.cs.utexas.edu/users/nn">Neural Networks Research
Group</a> at the 
<a target="_top" href="http://www.utexas.edu">University of Texas at Austin</a>.  
Development of Topographica has been funded by the 
<a target="_top" href="http://grants.nih.gov/grants/guide/pa-files/PAR-03-035.html">NIMH Human Brain Project</a> 
under grant 1R01-MH66991.  The goal is to help researchers understand
brain function at the level of the topographic maps that make up
sensory and motor systems.

<P>Topographica is intended to complement the many good low-level
neuron simulators that are available, such as
<A target="_top" HREF="http://www.genesis-sim.org/GENESIS/">Genesis</A> and
<A target="_top" HREF="http://kacy.neuro.duke.edu/">Neuron</A>.  
Those simulators focus on modeling the detailed internal behavior of
neurons and small networks of them.  Topographica instead focuses on
the large-scale structure and function that is visible only when many
thousands of such neurons are connected into topographic maps
containing millions of connections.  Many important phenomena cannot
be studied without such large networks, including the two-dimensional
organization of visual orientation and motion direction maps, and
object segmentation and grouping processes.

<P>To make such models practical, in Topographica the fundamental unit
is a sheet of neurons, rather than a neuron or a part of a neuron.  For most
simulations, the sheets can be implemented at a high level, consisting
of abstract firing-rate or integrate-and-fire neurons.  When required
for validation or for specific phenomena, Topographica can easily be
extended using a Sheet that interfaces to more detailed neuron models
in other simulators.  Less-detailed sheets can also be used temporarily,
e.g. when interacting with the model in real time.  Throughout,
Topographica makes it simple to use an appropriate level of detail and
complexity, as determined by the available computing power, phenomena
of interest, and amount of biological data available for validation.

<P>Compared to writing code for such models from scratch, Topographica
makes it simple to define multiple interconnected sheets, to use
localized patches of connections, to control the inputs to each sheet
and analyze the outputs, and to manage results from models
and simulations as they are developed and improved over time.

<P>The figure at top right shows an example Topographica model of the
early stages in the visual system, modeling how retinal input is
transformed by the thalamus, primary visual cortex, and higher
cortical areas.  Because Topographica is a general-purpose map
simulator, it also supports any other sensory modality that is
organized into topographic maps, such as touch and hearing, as well as
motor areas.

<P>Topographica is freely available for downloading, and is an open
source project
(<A HREF="http://www.opensource.org/licenses/bsd-license.php">BSD
license</A>) whose capabilities can be extended and modified by any
user.  We welcome contributions from users, and invite interested
people to join our globally distributed development team.

<P>Also see our <A target="_top"
HREF="http://homepages.inf.ed.ac.uk/jbednar/research.html">
research pages</a> for results from simulations run with Topographica
and related tools, and our <A target="_top"
HREF="http://computationalmaps.org">2005 book</A> for more details.

