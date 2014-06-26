**************************************
Using multiple cores with Topographica
**************************************

Topographica supports multiple-core processors using the OpenMP
library (`openmp.org`_). This functionality can result in significant
speedup when running simulations on multicore machines.

OpenMP support is enabled by default for any system with OpenMP
installed and working.  Most modern compilers come with OpenMP
support; see the `list at openmp.org`_.  Topographica will still run
correctly if OpenMP is not installed or if you only have a single
core.

In general, adding more cores to a process makes it faster.  However,
because cores typically share the same memory subsystem on a
processor, and because most Topographica simulations rely heavily on
memory accesses, you are unlikely to find that performance scales
linearly with the number of cores.  Often, some of these cores will
end up waiting while other cores access memory, giving you diminishing
returns from the additional cores.  Thus there's usually not much harm
from leaving one core free for other processes, such as your windowing
system, at least for machines with more than a couple of cores.  You
are only likely to find linear scaling for simulations involving high
levels of computation per memory access, whereas most Topographica
simulations involve simple computations performed on a very large
number of memory elements.  Even so, there is no reason not to use the
extra cores if they would otherwise go unused!


Controlling OpenMP
^^^^^^^^^^^^^^^^^^

By default, OpenMP will use all the cores available on your machine.
To change this behavior, you can set the ``OMP_NUM_THREADS``
environment variable, either in your shell's startup files or by
specifying the number of cores in your call to Topographica::

   OMP_NUM_THREADS=3 ./topographica /examples/gcal.ty -c "topo.sim.run(10000)"

For instance, you might want to leave one core free to keep your
system responding quickly during interactive use, specifying
OMP_NUM_THREADS=3 (for a four-core machine).  Or you can disable
OpenMP altogether by specifying OMP_NUM_THREADS=1, to get
single-threaded performance.

Once Topographica is running, you can check that the correct number of
cores is being used by monitoring your system's processor usage
externally, e.g. using the ``top`` command in Unix in a separate
window.

.. _openmp.org: http://openmp.org/wp/
.. _list at openmp.org: http://openmp.org/wp/openmp-compilers/
