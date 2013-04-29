**************************************
Using multiple cores with Topographica
**************************************

Starting from March 2012, Topographica supports multiple-core
processors using the OpenMP library (`openmp.org`_). This
functionality can result in significant speedup when running
simulations on multicore machines. OpenMP support is enabled by
default, and will not prevent Topographica from working as normal on
single-core machines or on multicore machines that lack the
necessary OpenMP libraries and compiler support.

OpenMP in Topographica
----------------------

Using OpenMP in Topographica is straightforward, requiring at most a
single (optional) variable to control the number of threads used. To
get the most out of your multicore system, it is important to
understand that enabling OpenMP does not guarantee the best possible
performance: in some situations you may find using multiple
concurrent but single-threaded instances of Topographica will
complete the desired set of simulations quicker.

Installing OpenMP
~~~~~~~~~~~~~~~~~

The OpenMP library is supported and shipped with recent versions of
most modern compilers. To check if your compiler can support OpenMP,
please consult the `list of compatible compilers at openmp.org`_. If
you find OpenMP cannot be enabled with Topographica, you may be
running an older compiler version. In this case, you should consider
updating your compiler and making sure the necessary library files
are installed for your particular distribution or operating system.

Enabling OpenMP
~~~~~~~~~~~~~~~

OpenMP is enabled by default, and can be disabled via the global
"openmp" variable in the Topographica environment using '-c
openmp=False' at the commandline. To illustrate this with the
example model (tiny.ty), monitor your processor usage (eg. using top
or htop on Linux) after running the following command:

::

     ./topographica -p 'openmp=False' -g ./examples/tiny.ty -c 'topo.sim.run(10000)' 

If you omit 'openmp=False', you should see that all available cores
are in use for the duration of the simulation and you may notice
some loss of responsiveness on your system while the simulation is
running. The default OpenMP behaviour to use all available cores for
one or two-processor machines, and all but one of the cores for
larger machines; the actual number being used will be reported when
Topographica starts up.

Setting the number of threads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best way to set the number of threads used by OpenMP in
Topographica is to supply the global 'openmp\_threads' variable with
the appropriate positive integer value. This can be done at the
commandline per simulation or globally across simulations using the
topographicarc file. In general, it may be useful to leave at least
one core free in order to maintain a responsive system when running
simulations, which is the default for most systems.

Via .topographicarc
^^^^^^^^^^^^^^^^^^^

If you wish to use OpenMP with Topographica regularly, you may wish
to enable OpenMP globally and define the number of threads in one
place. Therefore, the recommended global way of configuring OpenMP
is to add the following two lines to ~/.topographicarc (setting the
number of threads to your desired value):

::

    openmp=True
    openmp_threads=2

You can freely override this value as you wish for individual
simulations using the commandline. You may find yourself doing this
regularly if you are working on a hetrogeneous collection of
machines with varying numbers of cores and need anything other than
the default behavior.

Via the commandline
^^^^^^^^^^^^^^^^^^^

Here is an example of how the number of threads used can be set to
two on the commandline:

::

     ./topographica -p openmp_threads=2 -g ./examples/tiny.ty -c 'topo.sim.run(10000)' 

It is advised that you only change the number of OpenMP threads when
you want to override the value in the topographicarc file. As OpenMP
does not change the results of the simulation, omitting OpenMP
options at the commandline does not result in any loss of useful
scientific information about the simulation being run.

Via environment variable
^^^^^^^^^^^^^^^^^^^^^^^^

If the number of OpenMP threads is not set explicitly using the
methods above, the 'OMP\_NUM\_THREADS' environment variable is
consulted (if it exists). To illustrate, the following simulation
will only use two cores:

::

     OMP_NUM_THREADS=2 ./topographica -p seed_val=42 -g ./examples/gcal.ty 

The OMP\_NUM\_THREADS environment variable is designed to be a
system-wide setting for all OpenMP enabled programs. For this
reason, explicit use of "openmp\_threads" is preferred unless there
is good reason to use the system-wide default.

When to use OpenMP
~~~~~~~~~~~~~~~~~~

OpenMP is very useful when you have to run a single, long-running
simulation and do not wish to leave multiple cores on your system
idle. When you have a batch of simulations to run, it is important
to understand that using N threads per simulation does not mean each
simulation will complete N times quicker. In some circumstances,
running N single-threaded Topographica instances concurrently may
help you complete your batch of simulations quicker. Furthermore,
you are likely to find ever-diminishing returns as you increase the
number of OpenMP threads per Topographica instance. This is one of
the reasons you may wish to leave at least one core free in order to
keep the rest of the system responsive.

The scalability of OpenMP will vary depending on the computing
environment used, the model definition and the particular parameters
of the simulation (eg. cortex\_density) as there are many possible
trade-offs between memory usage, number of threads and number of
cores. One simplistic rule of thumb is to try and launch many
independent simulations as long as you launch fewer simulations than
available cores and you do not run out of memory - swapping will
always result in major slowdown. Each core will work most
efficiently if it is running an independent simulation with an
independent block of memory, provided that memory consumption is not
the bottleneck. Unfortunately, in Topographica, this is rarely the
case.

If multiple cores are assigned to a single simulation, the cores are
likely to have some memory contention as they are operating on the
same block of memory. This explains why each extra core results in a
smaller boost in performance. The fundamental problem, however, is
that Topographica simulations are often memory-bound, making memory
access the major bottleneck regardless of the number of cores
available or how they are used. In summary, it is worth keeping
these issues in mind when using OpenMP and you may find it
worthwhile to benchmark your system for your own simulations.

.. _openmp.org: http://openmp.org/wp/
.. _list of compatible compilers at openmp.org: http://openmp.org/wp/openmp-compilers/
