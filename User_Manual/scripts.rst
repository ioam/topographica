*******************************************
Starting Topographica scripts interactively
*******************************************

Once you have `installed Topographica`_ you are ready to try running
it. You can choose to run Topographica interactively (with or
without a graphical display), or in 'batch mode'. This section
introduces how to run Topographica interactively; batch mode is
described `separately`_.

Starting Topographica
---------------------

To start Topographica with one of our example scripts, on most
systems just open a terminal window and type ``topographica -g``
(Windows: double click on the desktop Topographica icon). Once
Topographica has loaded, you can then click on Help, followed by
Examples, to choose an example script to run. We have tutorials for
`lissom\_oo\_or.ty`_ and `som\_retinotopy.ty`_, which make a good
starting point for using Topographica.

Alternatively, instead of selecting an example from the GUI, you can
pass the name of a script to run when you start Topographica from
the terminal, e.g.

    ::
    
      topographica /path/to/some_script.ty -g

(Windows users can use the `command prompt`_, although on Windows it
is usually easier to use the GUI menus.) This command will run a
script located at the specified path.

.. _copy-examples:

To be able to run the examples easily, you will first need to get
your own personal copy of the example scripts:

    ::
    
      topographica -c "from topo.misc.genexamples import copy_examples; copy_examples()"

During installation, the Topographica example scripts are installed
into a location that varies by operating system and installation
type; this command copies those to an examples subdirectory of your
`output path`_ (see below), typically
``~/Documents/Topographica/examples`` (or
``~/topographica/examples`` for release 0.9.7 or earlier).

Now you can run an example script using a command like the
following:

    ::
    
      topographica ~/Documents/Topographica/examples/som_retinotopy.ty -g

Topographica can also be run without the GUI by omitting the ``-g``
flag from the startup command.

Finally, note that the first time Topographica is run on a given
example, there may be a short pause while the program compiles some
of the optimized components used in that example. (Some components,
generally those with ``_opt`` in their names, use code written in
C++ internally for speed, and this code must be compiled.) The
compiled versions are stored in ``~/.python26_compiled/`` on most
systems (or in the temporary directory ``%TEMP%\%USERNAME%`` on
Windows), and they will be reused on the next run unless the source
files have changed. Thus you should only notice such pauses the
first time you use a particular component, at which time you may
also notice various inscrutable messages from the compiler. These
messages vary depending on platform (because they come from the
compiler), and may generally be ignored.

.. _outputpath:

Output path
-----------

By default, output from Topographica is stored in a particular
folder, which is typically a folder named "Topographica" inside your
home directory's documents folder. The name and location of the
documents folder depends on your platform, e.g. "My Documents" on
some versions of Windows, or "Documents" on most other platforms.
Topographica attempts to determine the platform-specific documents
folder, or falls back to ``~/Documents/Topographica``. The output
path is printed on startup when running topographica interactively.
(Windows users should see our notes about the `command prompt`_.)

For release 0.9.7 and earlier, the default output path is instead
always ``~/topographica``.

You can override the default output path by setting the value of
`param.normalize\_path`_'s ``prefix`` parameter, e.g.:

    ::

      import param param.normalize_path.prefix = "/some/other/path/"

To override the default location every time you use Topographica,
you can put these two lines in a `user configuration file`_.

User configuration file
-----------------------

On startup, Topographica will look for and run the following files
in order:

    ``~/.topographicarc`` (typically for UNIX/Linux/Mac OS X
    systems)

    ``%USERPROFILE%\topographica.ini`` (on Windows, where
    ``%USERPROFILE%`` is typically ``C:\Users\username`` on Vista/7
    or ``c:\Documents and Settings\username`` on XP).

If you want to have any code run every time you start Topographica,
you can create the appropriate user configuration file for your
platform and add your preferred startup commands to it. The user
configuration file is particularly useful for overriding various
default settings such as the `output path`_ (as described above), or
the `command prompt format`_. The file can contain any valid Python
code.

.. _ty-files:

Topographica Scripts
--------------------

Topographica scripts consist of a collection of Python commands,
usually intended to define and build a particular model. Our
convention is to give script filenames the suffix ``.ty`` to
distinguish them from ordinary Python scripts (conventionally
``.py`` files).

As illustrated above, we provide a number of sample scripts in the
examples/ directory, but you are free to write your own and run them
in just the same way. The same commands are valid in script files as
at the `commandline`_: running a script file is equivalent to
entering the commands manually at the commandline.

Our example scripts, while quite various, have some common sections,
and we anticipate that your own scripts will also contain some of
these. The first such section is the list of imports.

Imports
~~~~~~~

Python requires that each command and class be imported (i.e.,
loaded and declared) from the appropriate file before use. This
avoids confusion between similar commands defined in different files
(see the Python documentation for `more information about
imports`_). Therefore, most scripts begin with a list of imports
similar to the following:

::

    from math import exp, sqrt
    import numpy
    import param

    from topo import learningfn,numbergen,transferfn,pattern,\
                     projection,responsefn,sheet

As described in the `overview`_, Topographica provides a number of
component libraries such as `pattern`_, `numbergen`_, and so on.
Within each of these, a number of related classes and functions are
available. Topographica uses Python's idea of 'namespaces' to make
expressions written for use with Topographica more readable. For
example, Topographica provides a class called UniformRandom, used to
generate a sequence of numbers from a uniform random distribution.
Topographica also provides a class with the same name that is used
to generate two-dimensional patterns. The two are in different
files: the first is topo/numbergen/basic.py, and the second is
topo/pattern/random.py. Were you to type the following:

::

    from topo.numbergen import UniformRandom
    from topo.pattern.random import UniformRandom

you would only have access to the pattern.random version in your
script (and at the commandline), because its name would have
overwritten the numbergen version. To avoid this kind of confusion,
we recommend not importing classnames alone for library components,
but instead qualifying the names. Using the
``from topo import numbergen`` style of import allows you to refer
to ``numbergen.UniformRandom`` throughout your script, which, while
involving more typing, cuts out confusion about which class you
might be referring to (making your script easier to read and less
prone to errors).

Startup options
---------------

Topographica accepts a number of startup options. Details are
available by passing -h to Topographica (``topographica -h``), but a
few in particular are often useful. We have already seen ``-g``,
which starts an interactive session with the GUI. To run a script
interactively without the GUI, pass ``-i`` instead of ``-g``. (Note
that ``-g``, as well as starting the GUI, also imports a number of
useful commands; you can use ``-a`` as described in the
`commandline`_ section to perform the same without the GUI.)

Please note that when writing a script, you should not rely on
anything to have been automatically imported (as is done by ``-g``
and ``-a``), because other users will not necessarily start
Topographica in the same way as you: scripts should explicitly
import everything they need.

In addition to startup options for the Topographica program, scripts
themselves can also be controlled by options passed at startup. For
instance, many of our examples read parameters that can optionally
be set at startup, such as ``retina_density``, ``lgn_density``, and
``cortex_density``, e.g.:

::

    topographica -i -p retina_density=12 -p cortex_density=12 \
    ~/Documents/Topographica/examples/lissom_oo_or.ty 

In this case, we are specifying that the retina and V1 sheets in a
LISSOM simulation should have a density of 12 rather than the
default of 24 and 48, respectively. Using lower densities is useful
during initial testing or exploration of a model; higher densities
can be used to produce results for publication.

Your own scripts can read any startup parameters you require (see
`GlobalParams`_ and our example scripts for how to read any such
parameter). Note that startup parameters must be set before the
script is executed, i.e. they should be passed on the commandline
before the script.

In addition to setting startup parameters, arbitrary Python commands
can be specified at the commandline by using the ``-c`` option. For
instance:

::

    topographica -c 'from topo.command.analysis import measure_sine_pref'\
    -c 'measure_sine_pref.num_directions=12' ~/Documents/Topographica/examples/tiny.ty

would import ``measure_sine_pref`` and set its ``num_directions``
attribute to ``12``, and then execute the ``tiny.ty`` example
script. As with ordinary Python commands, you can use a semicolon
``;`` to separate statements within one command.

.. _installed Topographica: ../Downloads/index.html
.. _separately: batch.html
.. _lissom\_oo\_or.ty: ../Tutorials/lissom_oo_or.html
.. _som\_retinotopy.ty: ../Tutorials/som_retinotopy.html
.. _command prompt: ../Downloads/win32notes.html
.. _output path: #output-path
.. _param.normalize\_path: ../Reference_Manual/param.normalize_path-class.html
.. _user configuration file: #user-configuration-file
.. _command prompt format: commandline.html#promptformat
.. _commandline: commandline.html
.. _more information about imports: http://docs.python.org/2/tutorial/modules.html
.. _overview: overview.html#class-hierarchies
.. _pattern: ../Reference_Manual/topo.pattern-module.html
.. _numbergen: ../Reference_Manual/topo.numbergen-module.html
.. _GlobalParams: ../Reference_Manual/topo.misc.commandline.GlobalParams-class.html
