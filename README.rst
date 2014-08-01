=============  =============  ===========  ========
  Full Build       Docs        Coverage     DICE
=============  =============  ===========  ========
|FullBuild|_    |TopoDocs|_   |Coverage|_  |DICE|_
=============  =============  ===========  ========


TOPOGRAPHICA
============

Topographica is a general-purpose neural simulator focusing on topographic maps.  The simulator is under continuous development, and scripts developed for one version are likely to need modification to run with subsequent versions.  Saved snapshot files will often continue to work with new versions, but they are not guaranteed to do so.

This program is free, open-source software available under the BSD license (see LICENSE.txt).


This document describes how to get and edit the Topographica source code.  Most first-time users will instead want to use the pre-packaged distributions available for most platforms; see Topographica's `Downloads <http://ioam.github.io/topographica/Downloads/index.html>`_  page for links.

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

If dependencies are missing, you can install them using pip.  Pip is
available on most systems already, but if it is missing or if the
installed version is old, you can install it using ``easy_install
pip`` or the equivalent for your package manager, or install
virtualenv instead.  The only required dependencies are numpy and PIL,
which can be installed using::

   pip install numpy PIL

but other highly recommended packages include scipy, ipython, and
matplotlib, which can each be installed in the same way::

   pip install gmpy scipy ipython matplotlib

If you wish to use `IPython Notebook <http://ipython.org/notebook>`_
(optional) with Topographica, you can install the remaining
dependencies as follows::

   pip install ipython tornado pyzmq jinja2

The notebook server may then be launched using the following command:

::

   ../../topographica -n


MAKING DOCUMENTATION (OPTIONAL)
-------------------------------

If you want a local copy of the documentation, usually to ensure that the documentation matches the precise version of the code that you are using, you can build the documentation from your Git clone directory. If PHP4, m4, bibtex, convert, and fig2dev are installed on your system (as in most Linux distributions), just change to the doc subdirectory of the topographica directory and type ``make default reference-manual``. (This step is only necessary when building from Git; released versions include the documentation already built.)

Once the documentation has been built, load doc/index.html into your web browser.  If there are any problems generating or reading the local copy, you can instead use the web-based documentation at `topographica.org <http://topographica.org>`_.  (The doc/ directory is just a copy of the website, although the web site will not necessarily match this particular copy of Topographica.)

As a last resort, for each <file>.html you can simply read the corresponding source file <file>_text.php in a text editor.

RUNNING TOPOGRAPHICA
--------------------

As long as all the dependencies have been installed as described above, no separate build step is needed -- all core Topographica files are pure Python, and any optimized C files will be compiled on the fly as needed by Topographica.

Once installed as described above, Topographica can be launched by running the ``topographica`` script in the main directory; e.g. ``topographica -g`` for the GUI version.  See doc/Tutorials/index.html for examples of getting started with Topographica, and doc/index.html for all of the documentation.  You can also get online help from the Topographica command line using ``help()``, or from the shell command line using ``pydoc some-text``.

MODIFYING TOPOGRAPHICA OR ITS SUBMODULES
----------------------------------------

If you're a Topographica developer wanting to commit changes to Topographica or any of its submodules, 
make sure you first run the following commands to ensure everything is
up to date::

  git pull
  git submodule update

Changes to any file outside of external/ can be made in the usual git fashion::

  edit topo/dir/somefile.py
  git commit -m "Important change" topo/dir/somefile.py
  git push

If you need to make changes to one of the submodules in external/, there are several
points to remember, assuming you're starting in the topographica
directory and you're modifying the param submodule (otherwise simply exchange param
with the submodule you want to modify)::

  cd ./external/param
  git checkout master
  git pull

Now make the desired changes in the submodule and commit and push them to
the remote repository using::

  git commit -a -m "Changed xxx"
  git push

Now that you have made the desired changes to the submodule itself, you
need to update the submodule reference in topographica so it points to the
right commit::

  cd ../.. # cd back to the topographica directory
  git add ./external/param
  git commit -m "Updated param submodule reference"
  git push

That's it, you've now committed changes to the submodule and told topographica
to point to the newly updated submodule.


.. |FullBuild| image:: http://doozy.inf.ed.ac.uk:8010/png?builder=full_build
.. _FullBuild: http://doozy.inf.ed.ac.uk:8010/waterfall

.. |TopoDocs| image:: http://doozy.inf.ed.ac.uk:8010/png?builder=topographica_docs
.. _TopoDocs: http://doozy.inf.ed.ac.uk:8010/waterfall

.. |Coverage| image:: http://doozy.inf.ed.ac.uk:8010/png?builder=coverage
.. _Coverage: http://doozy.inf.ed.ac.uk:8010/waterfall

.. |DICE| image:: http://doozy.inf.ed.ac.uk:8010/png?builder=DICE_alltests
.. _DICE: http://doozy.inf.ed.ac.uk:8010/waterfall

