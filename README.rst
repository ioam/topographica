TOPOGRAPHICA
============

Topographica is a general-purpose neural simulator focusing on topographic maps.  The simulator is under continuous development, and scripts developed for one version are likely to need modification to run with subsequent versions.  Saved snapshot files will often continue to work with new versions, but they are not guaranteed to do so.

This program is free, open-source software available under the BSD license (see LICENSE.txt).


This document describes how to get and edit the Topographica source code.  Most first-time users will instead want to use the pre-packaged distributions available for most platforms; see ioam/topographica `Downloads <http://github.com/ioam/topographica/downloads>`_  for links.

CLONING TOPOGRAPHICA
--------------------

Topographica on GitHub uses submodules, e.g. for the Param and ImaGen libraries. Please clone as follows::

   git clone git://github.com/ioam/topographica.git
   cd topographica
   git submodule update --init

The clone command above is read-only.  To push changes set up your `SSH key <https://help.github.com/articles/generating-ssh-keys>`_ and clone with::

   git clone git@github.com:ioam/topographica.git
   cd topographica
   git submodule update --init

If dependencies are missing, you can install them using pip.  Pip is available on most systems already, but if it is missing or if the installed version is old, you
can install it using ``easy_install pip`` or the equivalent for your package manager, or install virtualenv instead.  The only required dependencies are numpy and PIL, which can be installed using
``pip install numpy PIL``, but other highly recommended packages include scipy, ipython, and matplotlib, which can each be installed in the same way.

MAKING DOCUMENTATION (OPTIONAL)
-------------------------------

If you want a local copy of the documentation, usually to ensure that the documentation matches the precise version of the code that you are using, you can build the documentation from your Git clone directory. If PHP4, m4, bibtex, convert, and fig2dev are installed on your system (as in most Linux distributions), just change to the doc subdirectory of the topographica directory and type ``make default reference-manual``. (This step is only necessary when building from Git; released versions include the documentation already built.)

Once the documentation has been built, load doc/index.html into your web browser.  If there are any problems generating or reading the local copy, you can instead use the web-based documentation at `topographica.org <http://topographica.org>`_.  (The doc/ directory is just a copy of the website, although the web site will not necessarily match this particular copy of Topographica.)

As a last resort, for each <file>.html you can simply read the corresponding source file <file>_text.php in a text editor.

BUILDING FROM SOURCE (OPTIONAL)
-------------------------------

As long as all the dependencies have been installed as described above, no separate build step is needed -- all core Topographica files are pure Python, and any optimized C files will be compiled on the fly as needed by Topographica.

Alternatively, the dependencies can all be built from source, by changing to the "external" directory and typing ``make default``.  All non-standard external libraries will be fetched automatically and for most platforms will be built from source.  This approach makes the initial compilation time vastly longer and the simulator directory vastly larger, but it provides a full set of dependencies with known versions, including packages needed by Topographica's maintainers.  For specific instructions, see the "Build all Topographica's dependencies" and "Building Topographica" sections in the `Developer Manual installation instructions <http://topographica.org/Developer_Manual/installation.html>`_.

If you use this Makefile, you will need to append the absolute path of ``./topographica/bin/python`` to your ``PATH`` environment variable in order to make use of the packages you have built::

   export PATH=<PATH TO ./topographica/bin/>:$PATH

RUNNING TOPOGRAPHICA
--------------------

Once installed as described above, Topographica can be launched by running the ``topographica`` script in the main directory; e.g. ``topographica -g`` for the GUI version.  See doc/Tutorials/index.html for examples of getting started with Topographica, and doc/index.html for all of the documentation.  You can also get online help from the Topographica command line using ``help()``, or from the shell command line using ``pydoc some-text``.

MODIFYING SUBMODULES
--------------------

Before committing changes to Topographica or any of its submodules
make sure you first run the following commands to ensure everything is
up-to-date::

  git pull
  git submodule update

If you need to make changes to one of the submodules there are a
number of points to remember, assuming you're starting in the topographica
directory and you're modifying the param submodule (simply exchange param
with the submodule you want to modify)::

  cd ./external/param
  git checkout master
  git pull

Now make the desired changes in the submodule and commit and push them to
the remote repository using::

  git commit -a -m "Changed xxx"
  git push

Now that you have made the desired changes to the submodule itsself you
need to update the submodule reference in topographica so it points to the
right commit::

  cd ../.. # cd back to the topographica directory
  git add ./external/param
  git commit -m "Updated param submodule reference"
  git push

That's it, you've now committed changes to the submodule and told topographica
to point to your new commit.
