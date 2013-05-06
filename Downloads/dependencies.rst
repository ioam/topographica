************
Dependencies
************



This page gives information about the external packages that are
required or useful for Topographica; installation of these packages
is described on the main :doc:`Downloads <index>` page.

Required External Packages
--------------------------

Topographica makes extensive use of the following external packages
that must be installed to use Topographica.

`Python`_
    Topographica command and scripting language (essential!).
    Topographica is written in Python, so anything that Python can
    do is also valid for Topographica. For a good basic
    introduction, check out the `Python tutorial`_. Those already
    familiar with programming might find `Python for Programmers`_
    or `Idiomatic Python`_ useful.
`NumPy`_
    Topographica makes heavy use of NumPy arrays and math functions;
    these provide high-level operations for dealing with matrix
    data. The interface and options are `similar to Matlab`_ and
    other high-level array languages. These operations are generally
    much higher performance than explicitly manipulating each matrix
    element, as well as being simpler, and so they should be used
    whenever possible. See the `NumPy documentation list`_
    (especially the Guide to Numpy, NumPy Example List, and NumPy
    Functions by Category) to learn about the full range of
    available functions.
`PIL`_
    Topographica uses the Python Imaging Library for reading and
    writing bitmap images of various types. PIL also provides a
    variety of `image processing and graphics routines`_, which are
    available for use in Topographica components and scripts.

Required IOAM Packages
----------------------

Some of the modules developed for Topographica are maintained and
released separately, so that they can be used in other projects, but
are also required for Topographica:

`Param`_ and `ParamTk`_
    General-purpose support for full-featured Parameters, extending
    Python attributes to have documentation, bounds, types, etc. The
    Tk interface ParamTk is optional, and only used for
    Topographica's optional tkgui interface.
`ImaGen`_
    General-purpose support for generating 0D (scalar), 1D (vector),
    and 2D (image) patterns, starting from mathematical functions,
    geometric shapes, random distributions, images, etc. Useful for
    any program that uses such patterns, e.g. any sensory modelling
    software, not just Topographica.

Again, installation of these packages is described on the main
`Downloads`_ page.

Typical External Packages
-------------------------

Most Topographica users will also want these additional packages:

`MatPlotLib`_
    Matplotlib is used for generating 1D (line) and 2D (plane)
    plots, such as topographic grid plots. It provides `PyLab`_, a
    very general Matlab-like interface for creating plots of any
    quantities one might wish to visualize, including any array or
    vector in the program.
`IPython`_
    IPython provides Topographica with an enhanced Python shell,
    allowing efficient interactive work. The `IPython tutorial`_
    explains the most immediately useful features; see `IPython's
    documentation`_ for more detailed information.
`Weave`_
    Topographica uses weave (shipped with SciPy) to allow snippets
    of C or C++ code to be included within Python functions, usually
    for a specific speed optimization. This functionality is
    available for any user-defined library function, for cases when
    speed is crucial.
`gmpy`_
    A C-coded Python extension module that wraps the GMP library to
    provide Python with fast multiprecision arithmetic. Topographica
    uses gmpy's rational type as its default simulation time, to
    avoid precision issues inherent in floating-point arithmetic.
    Since gmpy requires GMP to be built, Topographica will fall back
    to a slower, purely Python implementation of fixed-point numbers
    (`fixedpoint`_) if gmpy is not available.
`Lancet`_
    Support for running large numbers of simulation jobs and
    collating the results to produce figures and analyses,
    especially for publication.

Optional External Packages
--------------------------

A number of other packages are also useful with Topographica, but
are not necessarily required. Packages listed below are therefore
not part of the default Topographica installation, but many are in
use by Topographica users and/or developers.

In most cases, these packages are included in Python distributions
such as `EPD`_/`Python(x,y)`_, or are available via package managers
such as apt-get/MacPorts. Alternatively, the packages are available
for easy\_install/pip install/standard Python installation via
`PyPI`_. Many of these packages can also be installed using the
external directory of Topographica; see the `github installation
instructions`_. Note that, however you choose to install any of
these packages, if your system has more than one copy of Python *you
must install the package using the same copy of Python that you are
using for Topographica*.

If you encounter problems using these packages, feel free to `ask
the Topographica community for help`_.

`SciPy`_
    SciPy includes many, many functions useful in scientific
    research, such as statistics, linear algebra, integration and
    differential equation solvers, etc.
`mlabwrap`_
    mlabwrap is a high-level Python-to-Matlab bridge, allowing
    Matlab to look like a normal Python library:

    ::

        from mlabwrap import mlab  # start a Matlab session
        mlab.plot([1,2,3],'-o')

    mlabwrap is transitioning to SciKits (see below), but
    installation can be tricky so we describe it further here.
    First, check you can run ``matlab -nodesktop -nosplash``
    successfully, then build from source (e.g. from Topographica's
    fat distribution with ``make -C external mlabwrap``, or download
    and build the source yourself). If the matlab libraries are not
    in your ``LD_LIBRARY_PATH``, there will be a note during the
    build telling you to add the libraries to your path. For
    example:

    ::

        export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/matlab-7.5/bin/glnx86

    You can either add that permanently to your path, or add it each
    time before using mlabwrap.

`pyaudiolab`_
    pyaudiolab provides an easy way to read from and write to sound
    files (it wraps `libsndfile`_). In the fat distribtion, building
    should be simple: ``make -C external pyaudiolab``.
`scikits-image`_
    A collection of algorithms for image processing.
`Player/Stage/Gazebo`_
    The Player/Stage/Gazebo project provides interfaces for a large
    variety of external hardware and simulation software, such as
    cameras, digitizers, and robots. The Gazebo and Stage simulators
    that support the Player interface can also be used, as described
    on the Player site. Note that a connection to Player is provided
    in topo/misc/robotics.py (last tested with player-2.0.4.tar.bz2
    from playerstage.sf.net).
`Processing`_
    Because of the "global interpreter lock" it is not possible to
    do true multiprocessing in Python using the language's built-in
    threads. The *processing* module provides support for
    multiprocessing using an API similar to that of Python's
    *threading* module. (Although, unlike threads, processes don't
    share memory.) The module also provides a number of other useful
    features including process-safe queues, worker pools, and
    factories ("managers") that allow the creation of python objects
    in other processes that communicate through proxies.
`Cython`_
    Cython is a language that is very similar to Python, but
    supports calling C functions and declaring C types, and will
    produce and compile C code. Therefore, the performance benefit
    of C is available from a much simpler language. Because Cython
    can compile almost any Python code to C, one can start with a
    component written entirely in Python and then optimize it step
    by step (by adding types, for example). See the Cython
    documentation for more information.
`Quantities`_
    Quantities allows you to use real-world units in your .ty
    scripts, such as mm or degrees of visual field, converting them
    to Topographica's units.
`SciKits`_
    SciKits provide many useful extensions to SciPy, e.g. for
    machine learning and numerical optimization.
`RPy`_
    The language R (a free implementation of the S statistical
    language) has a nice interface to Python that allows any R
    function to be called from Python. Nearly any statistical
    function you might ever need is in R.

Topographica runs on an unmodified version of the Python language,
and so it can be used with any other Python package that you install
yourself. A good list of potentially useful software is located at
`SciPy.org`_.

As above, note that if your system has more than one copy of Python,
you must install the package using the same copy of Python that you
are using for Topographica.

.. _Python: http://python.org/doc/
.. _Python tutorial: http://docs.python.org/tut/tut.html
.. _Python for Programmers: http://wiki.python.org/moin/BeginnersGuide/Programmers
.. _Idiomatic Python: http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html
.. _NumPy: http://numpy.scipy.org/
.. _similar to Matlab: http://www.scipy.org/NumPy_for_Matlab_Users
.. _NumPy documentation list: http://www.scipy.org/Documentation
.. _PIL: http://www.pythonware.com/products/pil/
.. _image processing and graphics routines: http://www.pythonware.com/library/pil/handbook/index.htm
.. _Param: http://ioam.github.com/param/
.. _ParamTk: http://ioam.github.com/paramtk/
.. _ImaGen: http://ioam.github.com/imagen/
.. _Downloads: ../Downloads/index.html
.. _MatPlotLib: http://matplotlib.sourceforge.net/
.. _PyLab: http://matplotlib.sourceforge.net/matplotlib.pylab.html
.. _IPython: http://ipython.scipy.org/
.. _IPython tutorial: http://ipython.scipy.org/doc/manual/html/interactive/tutorial.html
.. _IPython's documentation: http://ipython.scipy.org/moin/Documentation
.. _Weave: http://www.scipy.org/Weave
.. _gmpy: http://code.google.com/p/gmpy/
.. _fixedpoint: http://fixedpoint.sourceforge.net/
.. _Lancet: http://ioam.github.com/lancet/
.. _EPD: http://enthought.com/products/epd.php
.. _Python(x,y): http://pythonxy.com
.. _PyPI: http://pypi.python.org/pypi
.. _github installation instructions: http://pypi.python.org/pypi
.. _ask the Topographica community for help: http://sourceforge.net/projects/topographica/forums/forum/178312
.. _SciPy: http://www.scipy.org/
.. _mlabwrap: http://mlabwrap.sourceforge.net/
.. _pyaudiolab: http://www.ar.media.kyoto-u.ac.jp/members/david/softwares/pyaudiolab/index.html
.. _libsndfile: http://www.mega-nerd.com/libsndfile/
.. _scikits-image: http://scikits-image.org/
.. _Player/Stage/Gazebo: http://playerstage.sf.net
.. _Processing: http://pypi.python.org/pypi/processing
.. _Cython: http://cython.org
.. _Quantities: http://packages.python.org/quantities
.. _SciKits: http://scikits.appspot.com/scikits
.. _RPy: http://rpy.sourceforge.net/
.. _SciPy.org: http://www.scipy.org/Topical_Software
