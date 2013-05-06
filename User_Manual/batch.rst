**********************************************
Running Topographica simulations in batch mode
**********************************************

Topographica is designed so that full functionality is available
from the command line and batch mode, without any GUI required. This
support is essential for running large numbers of similar
simulations, e.g. to compare parameter settings or other options,
usually using clusters or networks of workstations.

To make this process simpler, Topographica provides a command
topo.command.run\_batch, which puts all results into a uniquely
identifiable directory that records the options used for the run.
Example:

::

      topographica -a -c "run_batch('~/Documents/Topographica/examples/tiny.ty')"

(see `how to get a copy of the example files`_ if you do not have
them already).

Here the `"-a" option`_ is used so that run\_batch can be called
without importing it explicitly, and also so that all commands will
be available to the various plotting and analysis routines called by
run\_batch (as described below). The result will be a directory with
a name like ``200710112056_tiny`` in the ``Output`` subdirectory of
your ``Topographica`` folder in your ``Documents`` directory (this
can be customized, and is ``~/topographica`` in release 0.9.7 and
earlier; see the note about the `default output path`_ for more
information). The name encodes the date of the run (in
year/month/day/hour/minute format) plus the name of the script file.

If you want to override any of the options accepted by tiny.ty, you
can do that when you call run\_batch:

::

      topographica -a -c "run_batch('~/Documents/Topographica/examples/tiny.ty',cortex_density=3)"

To help you keep the options straight, they will be encoded into the
directory name (as ``200710112056_tiny,cortex_density=3`` in this
case).

run\_batch also accepts a parameter ``analysis_fn``, which can be
any callable Python object (e.g. the name of a function). The
analysis\_fn will be called periodically during the run, at times
specified by a parameter ``times`` (e.g.
``[0.5,2.8,100,500,1000,5000]``). The simulation will complete after
the last analysis time.

The default analysis\_fn creates a few plots each time and saves the
current script\_repr() of the simulation to record the parameter
settings from that time. In practice you will want to supply your
own function, defined either in your .ty file or in a separate
script or module executed before you call run\_batch. In this case
you can start from the default\_analysis\_function in
topo/command/basic.py as an example. Your analysis\_fn should avoid
using any GUI functions (i.e., should not import anything from
topo.tkgui), and it should save all of its results into files. For
more information about commands that can go into the analysis\_fn,
see the `command line/script language`_ section.

As you might expect, you can provide any other options before or
after the run\_batch call, as usual. These will be processed before
or after the batch run, respectively:

::

      topographica -a -c "save_script_repr()" -p cortex_density=3\
      -c "run_batch('~/Documents/Topographica/examples/tiny.ty')" \
      -c "save_snapshot()"

Note that the output directory is not created or changed until the
run\_batch command is executed, so the output from the
save\_script\_repr() command will go into the default output
directory. Also note that when a parameter is set before run\_batch
(as cortex\_density is in this example), it will not be encoded into
the directory filename, because run\_batch will not be aware that it
has changed. Similarly, any errors in the commands provided before
or after run\_batch will not show up in the .out file stored in the
simulation directory, because that is closed when run\_batch
completes. Thus it's usually best to use run\_batch's options rather
than the separate commands shown in this example.

Lancet
~~~~~~

Once you get used to run\_batch, you'll often want to run a large
number of coordinated run\_batch runs, e.g. to do a parameter
search. Topographica works well with `Lancet`_, which provides these
features and many more. Lancet allows you to specify parameter
spaces to cover, launch multiple jobs (on single machines or
computing clusters), collate the results, generate figures and
analyses from the results, and archive these for posterity. See the
Lancet site for more details.

.. _how to get a copy of the example files: ../User_Manual/scripts.html#copy-examples
.. _"-a" option: commandline.html#option-a
.. _default output path: scripts.html#output-path
.. _command line/script language: commandline.html
.. _Lancet: https://github.com/ioam/lancet/
