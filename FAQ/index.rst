 
*****
FAQ
*****



Frequently Asked Questions about Topographica
=============================================

Here we collect together some answers to general questions about
Topographica. If you have a problem that isn't answered below,
please feel free to ask us (either in one of our `forums`_, or by
email).

#. **Q:** *How can I get access to the actual data shown in the
   various plots, etc.?*

   **A:** The main objects in the simulation can be accessed through
   the ``topo.sim`` attribute. For instance, if you have a sheet
   named ``'V1'``, it can be accessed as ``topo.sim.V1``. From there
   the projections, weights, etc. for that unit can be obtained. See
   the `Command line`_ section of the user manual for more
   information, including how to plot such data manually.
#. **Q:** *After upgrading Topographica or editing some of its
   files, I get errors when loading a saved snapshot.*

   **A:** As of 0.9.5, Topographica saves the state by using
   Python's pickling procedure, which saves *everything* in the
   current simulation. The disadvantage of this approach is that
   changes in the definition of any of the classes used (apart from
   changing parameter values or strictly adding code) can cause the
   reloading to fail. Whenever possible, we provide legacy snapshot
   support that maps from the old definition into the new one, and
   so snapshots *should* continue to be loadable. However, if you
   have trouble with a particular file, please file a bug report so
   that we can extend the legacy support to be able to load it. We
   may eventually set up an XML or HDF5-based archival storage
   format, but this is difficult to achieve with the fast pace of
   Topographica development.
#. **Q:** *What models or algorithms does Topographica support?*

   **A:** Topographica is built in a highly modular fashion, and
   thus it can support an effectively infinite number of algorithms
   with little or no change to the underlying code. For instance,
   there is no particular Topographica component that implements the
   SOM algorithm -- instead, a SOM network like
   examples/som\_retinotopy.ty is simply built from:

   #. An input pattern specified from a large library of possible
      `PatternGenerator`_\ s
   #. A general-purpose `GeneratorSheet`_ for presenting input
      patterns
   #. A general-purpose weight projection class `CFProjection`_
   #. A general-purpose array of units `CFSheet`_
   #. A specialized transfer function (`KernelMax`_) that picks a
      winning unit and activates the rest according to a
      user-specified kernel function (also implemented as a
      `PatternGenerator`_).

   This approach makes it simple to change specific aspects of a
   model (e.g. to choose a different `PatternGenerator`_ for the
   kernel function) without necessarily requiring any new code, as
   long as the new function has already been written for any
   previous model. For this example, only the KernelMax function
   (about 50 lines of Python code) was added specifically for
   supporting SOM; the other components were all already used in a
   wide variety of other models.

#. **Q:** *I think I've found a problem with Topographica. What
   should I do now?*

   **A:** Topographica is continuously changing to support active
   research, so problems can occur. To be sure you have found a
   problem with Topographica itself, and to help us fix it quickly,
   please follow our guidelines for `Reporting specific problems
   with Topographica`_.
#. **Q:** *pip failed while processing dependencies. What can I do
   now?*

   **A:** pip can sometimes encounter problems while processing
   dependencies. In such cases, installation will stop at the failed
   dependency, so it is usually straightforward to identify and fix
   the problem. Below we list some possibilities for solving pip
   problems:

   -  pip dependency-processing problems can sometimes be solved by
      installing the individual dependencies before running
      ``pip install topographica``:
      ``pip install numpy; pip install PIL`` (then, optionally,
      other recommended dependencies). Once these are installed,
      repeat the ``pip install topographica`` command.
   -  Binaries of Topographica's required dependencies (NumPy and
      PIL) as well as optional dependencies (MatPlotLib, gmpy,
      SciPy) are available for many platforms, using the native
      package manager for your platform (if available) or
      self-installing .exe files (for Windows). Once installed,
      repeat the ``pip install topographica`` command. Note that
      it's not always obvious how to make sure that separate
      installations like this all use the same copy of Python as
      Topographica is using, but doing so is necessary for this
      approach to work.
   -  If a binary is not available for your platform, you should
      check the dependency's installation instructions for your
      platform. Usually, you will need to make sure that you have
      typical code-building tools (e.g. a C/C++ compiler). Your
      distribution will usually have such tools available, e.g. the
      "build-essential" package on Ubuntu or `Xcode`_ on Mac. You
      will also need the Python headers, for which it might be
      necessary to install your distribution's "python-dev" or
      "python-devel" package.

#. **Q:** *On my Mac, the GUI windows take a long time to refresh,
   seeming to bounce around for a while. Why is this?*

   **A:** There is a bug in some versions of Tcl/Tk on OS X that
   causes Tkinter to perform very slowly. You could try installing a
   newer version of Tcl/Tk (e.g. ActiveTcl), but you would need to
   make sure your copy of Python is built against it. Please feel
   free to contact Topographica's developers if you would like more
   help with this problem.

.. _forums: ../Forums/index.html
.. _Command line: ../User_Manual/commandline.html
.. _PatternGenerator: ../Reference_Manual/topo.base.patterngenerator.PatternGenerator-class.html
.. _GeneratorSheet: ../Reference_Manual/topo.sheet.GeneratorSheet-class.html
.. _CFProjection: ../Reference_Manual/topo.base.cf.CFProjection-class.html
.. _CFSheet: ../Reference_Manual/topo.base.cf.CFSheet-class.html
.. _KernelMax: ../Reference_Manual/topo.transferfn.misc.KernelMax-class.html
.. _Reporting specific problems with Topographica: ../Forums/problems.html
.. _Xcode: http://developer.apple.com/technologies/tools/xcode.html
