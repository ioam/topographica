********************************************
Installing Topographica with version control
********************************************

Version control allows you to keep up to date with the latest
changes made by other developers, and allows you to keep track of
your own changes. Topographica's source code is held in a central
Git repository on GitHub.com; the repository contains the files
making up Topographica itself (including its documentation). Source
code versions of most of the various external libraries needed by
Topographica are kept at `SourceForge`_, but few developers will
need these.

Note that documentation may change between releases, so developers
(and others) who want to use a version-controlled copy of
Topographica should be reading the `nightly documentation build`_
rather than the previous release's documentation at
topographica.org.

Also note that the Git version is occasionally not usable due to
work in progress, but you can check to see if the code currently
builds on a specific platform, or if our suite of code tests pass,
by visiting our `automatic tests page`_.

Finally, please bear in mind that most of Topographica's development
occurs under Linux, so if you have a choice that is the
best-supported option.

Installing Topographica
~~~~~~~~~~~~~~~~~~~~~~~

First, clone the public Topographica repository as described at
`github`_. You can then either install the dependencies as described
there and then skip to the `after installation`_ instructions, or
you can build them all yourself (described below).

(Optional) Build all Topographica's dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Building Topographica's dependencies is usually straightforward on
Mac and Linux. Before beginning, you need to ensure your system has
the prerequisites described below.

Mac OS X
''''''''

Building Topographica on OS X should be straightforward. Assuming
you are using OS X 10.6 (Snow Leopard), you need to install Apple's
`Xcode3`_ if your system does not already have it. Xcode provides
the required GCC C/C++ compiler (among other development utilities).
You can then follow the instructions below for `building`_
Topographica.

*Optional*: If you want to compile a local copy of the HTML
documentation, you will also need imagemagick, transfig, and php (if
these are not already installed).

Linux
'''''

Many Linux systems will already have the required libraries
installed, so usually no action will be required here.

On some Linux distributions that start with a minimal set of
packages included, such as Ubuntu or the various "live CD" systems,
you may need to install "build tools". On Ubuntu, for instance,
these are installed via ``sudo apt-get install build-essential``.

Also on these minimal linux distributions, if you want to build and
use the GUI you may need to specify explicitly that some standard
libraries be installed: ``libx11-dev`` and ``libxft-dev``. Note that
on some systems the ``-dev`` packages are called ``-devel``, and
sometimes specific versions must be specified. Example for Ubuntu
9.10:

  ::

    sudo apt-get install libx11-dev libxft-dev

Once any necessary libraries are installed, you can proceed to the
`building`_ instructions below.

Building Topographica
'''''''''''''''''''''

The instructions below assume you have followed any necessary
platform-specific instructions described above. You will need a
writable directory with approximately 1.2 GB of space available (as
of July 2010).

Enter the directory where topographica is located and type ``make``
(which may be called ``gmake`` on some systems). It is best to do
this as a regular user in the user's own directory, not as a root
user with special privileges, because Topographica does not need any
special access to your system. The build process will take a while
to complete (e.g. about 10 minutes on a 3 GHz Core 2 Duo machine
with a local disk).

If you have problems during the build process, try adding ``-k`` to
the ``make`` command, which will allow the make process to skip any
components that do not build properly on your machine. Topographica
is highly modular, and most functionality should be accessible even
without some of those components.

*optional*: If desired, you can also make local copies of the HTML
documentation from the web site. To do so, you must have the php,
bibtex, convert, and fig2dev commands installed; type ``make all``
instead of (or after) ``make``. (If you don't have those commands,
in most distributions you can get them by installing the php5-cli,
tetex (or texlive), imagemagick, and transfig packages).
``make all`` will also run the regression tests and example files,
to ensure that everything is functioning properly on your system.

If building was successful, you can proceed to the `after
installation`_ section below.

.. _postinstall:

After installation
~~~~~~~~~~~~~~~~~~

To launch Topographica itself, you can enter ``./topographica -g``
(or just ``./topographica`` for no GUI) from within the
version-controlled topographica directory, or else enter the full
path to the script.

For actual use, you will probably want to add a symbolic link in a
directory that is in your regular path, pointing to the topographica
script. The instructions elsewhere in the documentation assume that
you have done so, so that you only need to type ``topographica``
instead of ``cd /path/to/topographica ; ./topographica``.

You can check that Topographica is working as expected by running
``make tests`` within the topographica directory. If you do the
tests on a machine without a functioning DISPLAY, such as a remote
text-only session, there will be some warnings about GUI tests being
skipped.

.. _SourceForge: http://sourceforge.net/projects/topographica
.. _nightly documentation build: http://buildbot.topographica.org/doc/Developer_Manual/installation.html
.. _automatic tests page: http://buildbot.topographica.org/
.. _github: https://github.com/ioam/topographica
.. _after installation: #postinstall
.. _Xcode3: http://developer.apple.com/tools/xcode/
.. _building: #building-topographica
