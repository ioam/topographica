## TOPOGRAPHICA

Topographica is a general-purpose neural simulator focusing on topographic maps.  The simulator is under continuous development, and scripts developed for one version are likely to need modification to run with subsequent versions.  Saved snapshot files will often continue to work with new versions, but they are not guaranteed to do so.

This program is free, open-source software available under the BSD license (see LICENSE.txt).


This document describes how to start with Topographica from the complete set of source code, which includes source code packages for all its dependencies.  Most users will instead want to start with the pre-packaged distributions available for most platforms; see ioam/topographica [Downloads](http://github.com/ioam/topographica/downloads) for links and instructions.

## CLONING TOPOGRAPHICA

Topographica on GitHub uses submodules. Please clone as follows:

```bash
git clone git://github.com/ioam/topographica.git
git submodule update --init
```

If dependencies are missing (numpy, PIL) are missing, try running ```pip install numpy PIL```.


## BUILDING DOCUMENTATION

To read more about Topographica before trying to build it, you can build the documentation separately from compiling Topographica itself. If PHP4, m4, bibtex, convert, and fig2dev are installed on your system (as in most Linux distributions), just change to the topographica directory and type "make doc reference-manual".  (This step is only necessary when building from SVN; released versions include the documentation already built.)

Once the documentation has been built, load doc/index.html into your web browser.  If there are any problems generating or reading the local copy, you can instead use the web-based documentation at [topographica.org](http://topographica.org).  (The doc/ directory is just a copy of the website, although the web site will not necessarily match this particular copy of Topographica.)

Alternatively, for each <file>.html you can simply read the corresponding source file <file>_text.php in a text editor.

## BUILDING TOPOGRAPHICA

The topographica directory includes the files necessary to build Topographica from source code on most platforms.  All non-standard external libraries are fetched automatically and for most platforms are built from source.  This approach makes the initial compilation time longer and the simulator directory larger, but it minimizes the changes necessary for specific platforms and operating system versions.

For specific instructions, see the "Build all Topographica's dependencies" and "Building Topographica" sections in doc/Developer_Manual/installation.html.


## USING TOPOGRAPHICA

See doc/Tutorials/index.html for examples of getting started with Topographica, and doc/index.html for all of the documentation.  You can also get online help from the Topographica command line using help(), or from the shell command line using "./bin/pydoc some-text".

