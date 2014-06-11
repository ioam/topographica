*********
Downloads
*********



Installing Topographica
-----------------------

Topographica is platform-independent, and all instructions below
apply to Linux, UNIX, Mac, or Windows, unless otherwise specified.
In Windows, to get a command prompt, you can use the Run command
from the Start menu and enter cmd; on other systems you can start a
Terminal or similar application.

The instructions below explain how to install Topographica `using pip`_
(for most users), `using virtualenv`_ (if you don't have pip access
or want a separate working environment, e.g. just to try out
Topographica), or `using git`_ (if you want the latest version, or need to
track our files using revision control).

First install Python
~~~~~~~~~~~~~~~~~~~~

Topographica is written in Python, which is available for nearly all
operating systems and is usually already installed (try running
``python --version`` from the command prompt). If Python version 2.6 or
later is not installed, you can download the latest version for your
system from `python.org`_. Note that we do not yet support Python3,
so if only python3 is installed you will need to install python2 as
well (e.g. Python 2.7).

If Python isn't already installed, it may be convenient to get it
from one of the integrated scientific Python distributions like
`Python(X,Y)`_, `EPD`_, or `Anaconda CE`_. These distributions are
particularly useful for Windows and Mac users, who might not
otherwise have a C compiler (necessary for good performance in
Topographica) and optimized math and matrix libraries. On any
system, the integrated distributions also provide a lot of useful
related packages, including most of Topographica's dependencies.

Quick recipe for Ubuntu Linux
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're installing on Ubuntu Linux 12.04, all you need to do is:

#. ``sudo apt-get update``
#. ``sudo apt-get install python-pip python-tk python-imaging-tk python-numpy``
#. ``sudo apt-get install ipython python-gmpy python-matplotlib python-scipy``
#. ``sudo pip install topographica``

Step 3 is optional, but highly recommended.  The remaining sections
below explain the general cross-platform procedure, but if you have
problems on any particular platform, you might consider using an
Ubuntu 12.04 virtual machine to try out Topographica so that you can
use the simple recipe above.  Similar approaches should work on other
platforms, but we don't currently have a list of the precise steps in
each case.

Install via pip
~~~~~~~~~~~~~~~

The typical way to install the most recently released version of
Topographica is via `pip`_ from the command prompt:

::

 pip install --user topographica

This will fetch Topographica and its required dependencies (i.e.,
param, paramtk, imagen, numpy, and PIL, for the 0.9.8 release) from
`PyPI`_ and install them into your home directory. The files will be
stored in a subdirectory called ``.local`` on Linux and Mac, and
into the user's ``%APPDATA%`` subdirectory on Windows (typically
named ``Application Data``).

Beyond these absolutely required packages, you will probably also
want to install others necessary for good performance (by at least a
factor of 100), to provide some optional types of plotting, and to
improve the command-line interface:

::

 pip install --user gmpy matplotlib scipy ipython

Other useful packages are described on our `dependencies`_ page, and
can usually be installed the same way.

If you have root or adminstrator access to your machine and want
these libraries to be available to all users of your system, you can
omit ``--user``, or else install the dependencies via your system's
package manager, if any.

If your system does not have pip installed or has an old version
lacking the ``--user option``, but you do have root or administrator
access, you should first install pip using:

::

 easy_install pip

or the equivalent for your package manager. If you don't have
easy\_install, you can install pip by downloading `get-pip.py`_ and
running ``python get-pip.py``.

Install via virtualenv
~~~~~~~~~~~~~~~~~~~~~~

If your machine lacks pip and you do not have root or administrator
access, then you can obtain a local copy of pip by downloading
`virtualenv.py`_. Just run it using Python to create a clean
"virtual environment" that includes pip and into which you can
install Topographica and its dependencies:

::

> python virtualenv.py VENV
> VENV/bin/pip install topographica
> VENV/bin/topographica -g

(Not tested under Windows.) You can then install any other
dependencies using `pip`_ as described above. Of course, instead of
VENV you can use any name you like for your virtual environment, and
you can have multiple different virtual environments for different
purposes.

Many people use `virtualenv`_ even if they do have root access,
because it allows you to install whatever you like without affecting
any other installations. Virtualenv is also an excellent way to try
out Topographica, because you can simply delete the generated VENV
directory if you decide not to keep the installation, with no effect
on your system.

Install via Git
~~~~~~~~~~~~~~~

If you want the most current version of Topographica, or if you want
to track Topographica development over time, you'll want the
`github`_ version of Topographica instead of installing it via pip.

Running Topographica
--------------------

Because there are many ways a user might install Topographica (or
any other Python package), the next step is to figure out where the
topographica script (used for launching Topographica) and the
example and model files (used as starting points for your modelling)
ended up.

If you follow the instructions above, the topographica script is
usually ``~/.local/bin/topographica`` or ``~/VENV/bin/topographica`` on
Linux, UNIX, and Mac. On Windows pip installations it is usually
``%APPDATA%\Python\scripts\topographica`` (where ``%APPDATA%`` is
something like ``C:\Users\jbednar\AppData\Roaming``; ``AppData`` is
often hidden in the filesystem so you may need to enable display of
hidden files).

Once you've located the topographica script, it will save typing if
you make sure that the location of that script is in your command
prompt path. Instructions for doing so differ by platform, but
should be easily obtainable. On Windows one convenient way to put
the script on the path is to create a file called ``topographica.bat``
containing a single line like:

::

@C:\Python27\python.exe %APPDATA%\Python\scripts\topographica %*

(where you use the appropriate path to both Python and your
topographica script) and put it somewhere in your path (e.g.
``C:\Windows\System32``).

The example files are usually in
``~/.local/share/topographica/examples/`` on Linux, UNIX, and Mac
systems, and in ``%APPDATA%\Python\Share\Topographica\examples`` on
Windows, or in the corresponding VENV directories.

Once you've located the script and the examples, you can start the
GUI version of Topographica from the command prompt using something
like: ``topographica -g ~/.local/share/topographica/examples/tiny.ty``
or ``python %APPDATA%\Python\scripts\topographica -g
%APPDATA%\Python\share\topographica\examples\tiny.ty`` (on
Windows).

Running Topographica interactively is described in detail in the
`User Manual`_. If you want to get straight into working with a full
network, a good way to begin is by working through the `SOM`_ or
`GCAL`_ tutorials.

Have fun with Topographica, and be sure to subscribe to the
`topographica-announce`_ mailing list to hear about future updates!

.. _using pip: #install-via-pip
.. _using virtualenv: #install-via-virtualenv
.. _using git: #install-via-git
.. _python.org: http://www.python.org/download
.. _Python(X,Y): http://www.pythonxy.com
.. _EPD: http://www.enthought.com/products/epd.php
.. _Anaconda CE: https://store.continuum.io
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
