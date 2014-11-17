*********
Downloads
*********

Installing Topographica
-----------------------

Topographica is platform-independent, and all instructions below apply
to Linux, UNIX, Mac, or Windows, unless otherwise specified.  In
Windows, to get a command prompt, you can use the Run command from the
Start menu and enter cmd; on other systems you can start a Terminal or
similar application.

The instructions below explain how to install Topographica `using
pip`_ (for most users), or `using git`_ (if you want the latest
version, or need to track our files using revision control). However,
we first provide a `quick start`_ recipe, which you can follow step by
step to get the most recent official release in a short time.

Quick start
~~~~~~~~~~~

To get started quickly on 64-bit Linux (even if your user account has
no system privileges), you can follow the steps below:

::

 wget http://repo.continuum.io/archive/Anaconda-2.1.0-Linux-x86_64.sh
 chmod +x ./Anaconda-2.1.0-Linux-x86_64.sh
 ./Anaconda-2.1.0-Linux-x86_64.sh -b -p ~/topo-env
 export PATH=~/topo-env:~/topo-env/bin:${PATH}
 conda install --yes numpy=1.8 matplotlib scipy
 conda install --yes --channel https://conda.binstar.org/oarodriguez gmpy
 pip install topographica==0.9.8-1
 
This will install Topographica into a completely self-contained
`Anaconda`_ Python environment, so will not interfere with any
existing software, nor will it be affected by any subsequent changes
to the system. Note that if you decide not to keep Topographica, you
can uninstall by deleting the ~/topo-env directory.

Having followed the quick start guide, you can skip ahead to `Running
Topographica`_. The remaining sections below explain the general
cross-platform installation procedure, but if you have problems on any
particular platform, you might consider using e.g. a 64-bit Ubuntu
14.04 virtual machine (via `VirtualBox`_, for instance) to try out
Topographica so that you can use the simple recipe above.  Similar
approaches should work on other platforms, but we don't currently have
a list of the precise steps in each case. User-contributed recipes are
welcome: please submit a `github issue`_.


Install a Python environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Topographica is written in Python, which is available for nearly all
operating systems. If you do not already have a Python environment in
which you wish to install Topographica, you can get one via your
system's package manager, or by installing one of the free integrated
scientific Python distributions like `Anaconda`_, `Python(X,Y)`_, or
`Canopy`_. These integrated distributions provide many useful related
packages (including many of Topographica's required and optional
dependencies), can be installed without requiring special privileges,
and provide a C compiler on platforms that may otherwise not have one
(e.g. Windows or Mac), allowing Topographica's optional optimized
components to be used.

However you obtain a Python environment, note the following minimum
requirements:

* Python 2 (2.6 or 2.7; we do not yet support Python 3)
* NumPy
* PIL (from pillow)


Install via pip
~~~~~~~~~~~~~~~

The typical way to install the most recently released version of
Topographica is via `pip`_ from the command prompt:

::

 pip install topographica

This will install Topographica and any required dependencies your
Python environment does not have (from `PyPI`_). Apart from the
dependencies listed above, Topographica also requires three other IOAM
packages: param, paramtk, and imagen.

Note that pip can instead install packages into your home directory
(via the ``--user`` option), or you may use `virtualenv`_ to keep
Topographica's Python environment separate from any others you may
have.

Beyond these absolutely required packages, you will probably also want
to install packages that provide some optional types of plotting, and
to improve the command-line interface:

::

 pip install matplotlib scipy ipython

For better performance (by at least a factor of 100), you should also
install gmpy and weave:

::
 
 pip install gmpy weave

If your system has a C compiler, weave allows Topographica's optional
optimized components to be used. On linux, a C compiler is usually
included, but on minimal distributions you may need to install the
equivalent of a "build-essential" package (e.g. `sudo apt-get install
build-essential` on Ubuntu). On other platforms, an integrated
scientific Python environment such as `Anaconda`_ or `Python(X,Y)` may
be the easiest way to obtain a compiler.

Other useful packages are described on our `dependencies`_ page, and
can usually also be installed via pip.


Install via Git
~~~~~~~~~~~~~~~

If you want the most current version of Topographica, or if you want
to track Topographica development over time, you'll want the `github`_
version of Topographica instead of installing it via pip.


Running Topographica
--------------------

Because there are many ways a user might install Topographica (or any
other Python package), the next step is to figure out where the
topographica script (used for launching Topographica) and the example
and model files (used as starting points for your modelling) ended up.

If you followed the quick start above, the topographica script will be
in ``~/topo-env/bin/topographica``, and the examples and models will
be in ``~/topo-env/share/topographica/``.

If you installed via pip into an existing Python environment (or
virtual environment), the topographica script will be in that
environment's ``bin`` directory (Linux, UNIX, and Mac) or ``scripts``
folder (Windows). The examples and models will be in the environment's
``share`` directory (``share/topographica/``).

If you used pip's `--user` option, the topographica script is usually
``~/.local/bin/topographica`` on Linux, UNIX, and Mac. On Windows pip
installations it is usually ``%APPDATA%\Python\scripts\topographica``
(where ``%APPDATA%`` is something like
``C:\Users\jbednar\AppData\Roaming``; ``AppData`` is often hidden in
the filesystem so you may need to enable display of hidden files). The
examples and models will usually be in
``~/.local/share/topographica/`` on Linux, UNIX, and Mac systems, and
in ``%APPDATA%\Python\Share\Topographica\`` on Windows.

Once you've located the topographica script, it will save typing if
you add the location of that script to your command prompt
path. Instructions for doing so differ by platform, but should be
easily obtainable. Windows users should additionally create an
executable topographica.bat script by pasting the following into a
cmd.exe window:

::

 (echo set PYFILE=%~f0 && echo set PYFILE=%PYFILE:~0,-4% && echo "%~f0\..\..\python.exe" "%PYFILE%" %*) > path\to\scripts\topographica.bat

where ``path\to\scripts\`` is the location containing your
``topographica`` script, as described above.

You can start the GUI version of Topographica from the command prompt
using ``topographica -g``, or specify an example to load, e.g. on
Linux:

::

 topographica -g ~/topo-env/share/topographica/examples/tiny.ty

Or on Windows:

::

 topographica -g %HOMEPATH%\topo-env\share\topographica\examples\tiny.ty


Running Topographica interactively is described in detail in the `User
Manual`_. If you want to get straight into working with a full
network, a good way to begin is by working through the `SOM`_ or
`GCAL`_ tutorials.

Have fun with Topographica, and be sure to subscribe to the
`topographica-announce`_ mailing list to hear about future updates!

.. _using pip: #install-via-pip
.. _using git: #install-via-git
.. _python.org: http://www.python.org/download
.. _Python(X,Y): http://www.pythonxy.com
.. _Anaconda: http://continuum.io/downloads
.. _Canopy: https://store.enthought.com/downloads/
.. _pip: http://www.pip-installer.org
.. _PyPI: http://pypi.python.org/pypi/topographica
.. _dependencies: dependencies.html
.. _get-pip.py: https://raw.github.com/pypa/pip/master/contrib/get-pip.py
.. _virtualenv.py: https://raw.github.com/pypa/virtualenv/master/virtualenv.py
.. _virtualenv: http://www.virtualenv.org
.. _github: https://github.com/ioam/topographica
.. _User Manual: ../User_Manual/scripts.html
.. _SOM: ../Tutorials/som_retinotopy.html
.. _GCAL: ../Tutorials/gcal.html
.. _topographica-announce: https://lists.sourceforge.net/lists/listinfo/topographica-announce
.. _VirtualBox: http://www.virtualbox.org/
.. _github issue: https://github.com/ioam/topographica/issues/new
