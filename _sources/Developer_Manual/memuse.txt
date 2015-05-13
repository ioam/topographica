************
Memory usage
************

In many cases, the factor that determines whether a Topographica
simulation will be practical is its memory usage. Once a simulation
is larger than the system memory, it will be entirely impractical,
if not impossible, to run on a given machine. Moreover, runtime can
often be improved by reducing memory requirements, because much of
the simulation time is taken performing simple, fast operations on a
large number of items, which is dominated by the memory bandwidth.

Topographica provides several utilities for measuring memory usage
`topo.misc.memuse`_, and these can be used to optimize specific
parts of the code to reduce memory requirements. Some of these
currently (6/2009) only work on UNIX-like systems, but it should be
straightforward to provide similar functionality for other operating
systems. This page first discusses utilities that can help you
determine your total memory requirements and whether optimizing
these is possible, and then briefly discusses how to optimize them.

Topsize
-------

On a UNIX-like system, you can measure the total real memory of any
process using the ``top`` command. For instance, if you have started
Topographica's copy of Python using ``./bin/python``, top returns:

::

     PID USER      PR  NI  VIRT  RES  SHR S %CPU %MEM    TIME+  COMMAND           
    4060 jbednar   17   0  7684 2780 1676 S    0  0.1   0:00.00 python             

Here RES indicates that a minimal Python process takes 2,780 bytes
on this machine, i.e. much less than one megabyte of system memory.

Topographica provides a command `topsize`_ to extract this number
automatically for the python process from which it is run:

::

    $ bin/python -c 'execfile("topo/misc/memuse.py") ; print topsize()'
    2908

Here the number is slightly higher than before because Python has
now executed ``memuse.py``, which requires importing some libraries.
The ./topographica script imports many additional libraries by
default, and so the process size for running ./topographica is much
higher than for python alone:

::

    $ ./topographica -c 'from topo.misc import memuse' -c 'print memuse.topsize_mb()'
    topsize:10m

Here the ``m`` indicates that the size is 10 megabytes, i.e. about
10.5 million bytes. The requirements rise further if most of the
commands are imported at the start:

::

    $ ./topographica -a -c 'from topo.misc import memuse, asizeof' -c 'print memuse.topsize_mb()'
    topsize:25m

For this particular version of Topographica, 25MB should be
considered the minimal process size for any real network run without
a GUI, and sizes below that number are likely to be possible only by
selecting components that avoid importing system libraries. In any
case, most modern computers have at least 1024MB of memory, and so
this overhead should rarely be significant.

Simsize and asizeof
-------------------

The total process size from `topsize`_ has the biggest effect on
whether a simulation is practical, but it's crucial to know what
Python/Topographica components make up the total. The `asizeof`_
function can be used to estimate the size of any Python object in
Python 2.5 or earlier, e.g.:

::

    >>> from topo.misc.asizeof import asizeof
    >>> asizeof([])
    40
    >>> asizeof([1,2,3,4,5,6])
    176

Python 2.6 provides a method ``sys.getsizeof`` that appears to work
similarly but has not been tested.

``asizeof`` has many limitations, and it will systematically
underestimate the requirements when there are parts of objects for
which the memory use is not known. In particular, asizeof does not
currently account for any memory taken by Numpy array values:

::

    >>> from topo.misc.asizeof import asizeof
    >>> from numpy import array
    >>> asizeof(array([]))
    40
    >>> asizeof(array([1,2,3,4,5,6]))
    40
    topo_t000000.00_c10>>> asizeof(array([0]*10000))
    40

All Topographica weights and activity values are stored in numpy
arrays, and so this omission can be significant.

In any case, Topographica provides a function `simsize`_ for
measuring ``asizeof(topo.sim)``:

::

    $ ./topographica -a -c 'from topo.misc import memuse, asizeof' examples/tiny.ty \
    -c 'print memuse.simsize()'
    48800

Again, this value does not include any arrays, which are counted by
`n\_bytes`_ (below).

n\_bytes, n\_conns, and print\_sizes
------------------------------------

The above routines are meant to be very general, albeit flawed.
Topographica also provides Topographica-specific functions for
counting the number of bytes taken by the main Numpy arrays, which
constitute the major necessary data structures required for
simulating networks.

The estimated number of bytes taken for the weights and activity
arrays can be found from the `n\_bytes`_ command:

::

    $ ./topographica -a examples/lissom_oo_or.ty -c 'print n_bytes()'
    15908552

As an aside, you can determine how many neural connections have been
defined using the `n\_conns`_ command:

::

    $ ./topographica -a examples/lissom_oo_or.ty -c 'print n_conns()'
    2197512

The results from `n\_conns`_ and `n\_bytes`_ are reported by default
for batch simulations using the `print\_sizes`_ command:

::

    $ ./topographica -a examples/lissom_oo_or.ty -c 'print_sizes()'
    Defined 2197512-connection network; 15MB required for weight storage.

Note that `n\_conns`_ reports the total number of connections
defined, unique or not; for simulations like ``lissom_oo_or.ty``
that include a `SharedWeightCFProjection`_ the memory taken can be
far less than the number of weights would suggest because most of
the connections share the same physical memory.

allsizes\_mb and memuse\_batch: total memory usage
--------------------------------------------------

As should be clear from the above, a complete picture of the memory
usage is possible only by combining information from different
sources. Topographica provides a convenient way to do so via the
`allsizes\_mb`_ command:

::

          
    $ ./topographica -a -c 'from topo.misc import memuse, asizeof' \
    examples/lissom_oo_or.ty -c 'print memuse.allsizes_mb()'
    topsize:52m =? code + simsize:10MB + wtsize:15MB (25MB tot)

Here the total process size (reported by top) is 52MB. This total
includes memory taken by the code and libraries (estimated at 25MB
above for this Python version and machine), the Python data
structures in ``topo.sim`` (reported as 10MB by ``asizeof``), and
the weight and activity Numpy matrices (reported as 15MB by
``n_bytes``). As the formatting of the output suggests, these
numbers should approximately add up, i.e. 52MB should be
approximately the sum of (25MB + 10MB + 15MB), which at 50MB is true
in this case. Thus in this simulation, there is relatively little
that can be optimized, as 80% (40MB) is taken by system libraries
and essential objects such as the network weights and activities.
Other simulations *do* offer potential optimization, e.g.:

::

    $ ./topographica -a -c "from topo.misc import memuse" \
    -c "memuse.memuse_batch('examples/lissom.ty',retina_density=24,\
    lgn_density=24,cortex_density=48,dims=['or','od','dr','dy','cr','sf'])"
    ...
    topsize:1.4g =? code + simsize:869MB + wtsize:389MB (1259MB tot)

Here `memuse\_batch`_ has been used to evaluate memory usage in a
large number of simulations with different parameters, and in this
particular simulation the code, libraries, activities, and weights
account for only 30% of the memory requirements ((389+25)/1400).
Thus this example has a large potential for memory usage
optimization.

Heapy
-----

The above routines can be used to determine when memory usage
optimization might be worthwhile, by making it clear when memory is
taken by Python's internal data structures. Actually doing the
optimization requires careful consideration of the details of how
Python and Topographica allocate memory in specific cases.
`asizeof`_ can be useful in this respect, but much more detailed
information is available from an external program `Heapy`_, which
can be installed using e.g. ``apt-get install python-guppy``.

Heapy will give you output similar to a performance profiler, but
for memory usage. For example:

::

    $ ./topographica -i \
    -p 'cortex_density=retina_density=24' -p lgn_density=10 \
    -p 'dims=["or","od","dr","cr","sf"]' \
    -c "from guppy import hpy; h=hpy(); h.setrelheap()" \
    ...
    >>> execfile('examples/lissom.ty')
    >>> heap=h.heap()
    >>> heap
    Partition of a set of 2703203 objects. Total size = 117259620 bytes.
     Index  Count   %     Size   % Cumulative  % Kind (class / dict of class)
         0  47536   2 24718720  21  24718720  21 dict of 0x9226e94
         1 1204254 45 19268064  16  43986784  38 numpy.float64
         2 265472  10 15928320  14  59915104  51 topo.base.sheetcoords.Slice
         3  85200   3 11587200  10  71502304  61 dict of 0x921e3dc
         4 267183  10  9618588   8  81120892  69 topo.base.boundingregion.AARectangle
         5 182936   7  7317440   6  88438332  75 numpy.ndarray
         6 101539   4  6921776   6  95360108  81 str
         7 267183  10  6412392   5 101772500  87 topo.base.boundingregion.BoundingBox
         8  85200   3  3408000   3 105180500  90 0x921e3dc
         9  63929   2  2842656   2 108023156  92 list
    <399 more rows. Type e.g. '_.more' to view.>

This output indicates that the single largest component of the
memory usage is for a set of objects of type ``dict``, while in most
properly optimized Topographica simulations the memory requirements
should be dominated by objects of type numpy.floatXX (the activity
and weight matrices).

We can find out more by examining the details for each group of
items above. For instance, heap partition index 0 (which is a group
of dict objects that together take 21% of the memory) can be
examined by looking at ``heap[0]``. First, the identity of the
objects can be seen using ``shpaths``:

::

    >>> heap[0].shpaths
     0: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff0'].__dict__['in_connections'][0].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     1: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff0'].__dict__['in_connections'][1].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     2: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff0'].__dict__['in_connections'][2].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     3: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff1'].__dict__['in_connections'][0].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     4: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff1'].__dict__['in_connections'][1].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     5: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff1'].__dict__['in_connections'][2].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     6: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff2'].__dict__['in_connections'][0].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     7: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff2'].__dict__['in_connections'][1].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     8: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff2'].__dict__['in_connections'][2].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
     9: h.Root.i0_modules['topo'].__dict__['sim'].__dict__['_event_processors']['LeftBlue-RedGreen
    LGNOff3'].__dict__['in_connections'][0].__dict__['_SharedWeigh...ion__sharedcf'].__dict__
    <... 1206 more paths ...>

Thus these appear to be the attribute dictionaries of SharedWeightCF
objects, which makes sense for this network because it contains
dozens of LGN sheets connected using SharedWeightCFProjections.
Further breakdown of what exactly is stored in these dicts can be
seen using ``referents``:

::

    >>> heap[0].referents
    Partition of a set of 192529 objects. Total size = 7325148 bytes.
     Index  Count   %     Size   % Cumulative  % Kind (class / dict of class)
         0  47536  25  2852160  39   2852160  39 topo.base.sheetcoords.Slice
         1  47543  25  2151956  29   5004116  68 str
         2  47536  25  1521152  21   6525268  89 list
         3  49808  26   796928  11   7322196 100 numpy.float64
         4     80   0     2240   0   7324436 100 0x922ad8c
         5     24   0      672   0   7325108 100 0x9255fc4
         6      1   0       28   0   7325136 100 0x9469fd4
         7      1   0       12   0   7325148 100 bool

Here it is clear that most of the memory in these dictionaries is
taken by Slice objects, and thus the obvious place to begin
optimization is on the Slice class. Using this information, we can
start examining Slice to determine how its memory usage can be
reduced. This process is similar to that for `performance
optimization`_, but focusing on memory rather than speed.

If you are debugging memory usage during the running of a simulation,
you may want to use ``setrelheap()`` after loading the simulation but
before running. Similarly, you can subtract one ``heap()`` from
another.

Note that `documentation for Heapy`_ is sparse and difficult to
follow; it may be easier to start with some `notes from another
developer`_.


Beyond Python
-------------

If the memory usage reported by heapy is vastly different from the
memory usage reported by the operating system (e.g. via top), you may
have encountered a bug outside Python code. Various tools exist to
investigate such a situation (e.g. `gdb-heap`_, valgrind) but are
beyond the scope of this guide. You might be able to narrow down the
problem to a particular extension or operation by cutting out parts of
your simulation bit by bit until you find the culprit (at which point
you could search the web for known bugs in that extension).

Another possible cause of discrepancy in memory usage is that Python
does not always `return memory to the operating system`_, even after
you free that memory in Python. If you do use a lot of memory in
Python at any point, this could be your problem.


.. _topo.misc.memuse: ../Reference_Manual/topo.misc.memuse-module.html
.. _topsize: ../Reference_Manual/topo.misc.memuse-module.html#topsize
.. _asizeof: ../Reference_Manual/topo.misc.asizeof-module.html#asizeof
.. _simsize: ../Reference_Manual/topo.misc.memuse-module.html#simsize
.. _n\_bytes: ../Reference_Manual/topo.command-module.html#n_bytes
.. _n\_conns: ../Reference_Manual/topo.command-module.html#n_conns
.. _print\_sizes: ../Reference_Manual/topo.command-module.html#print_sizes
.. _SharedWeightCFProjection: ../Reference_Manual/topo.projection.SharedWeightCFProjection-class.html
.. _allsizes\_mb: ../Reference_Manual/topo.misc.memuse-module.html#allsizes_mb
.. _memuse\_batch: ../Reference_Manual/topo.misc.memuse-module.html#memuse_batch
.. _Heapy: http://guppy-pe.sourceforge.net/#Heapy
.. _performance optimization: optimization.html
.. _documentation for Heapy: http://guppy-pe.sourceforge.net/heapy_Use.html
.. _notes from another developer: http://smira.ru/wp-content/uploads/2011/08/heapy.html
.. _gdb-heap: https://github.com/rogerhu/gdb-heap
.. _return memory to the operating system: http://effbot.org/pyfaq/why-doesnt-python-release-the-memory-when-i-delete-a-large-object.htm
