#!/usr/bin/env python

import sys
from distutils.core import setup
import glob

examples = glob.glob('examples/*.ty')
scripts = ['topographica']

### TOPOGRAPHICA DEPENDENCIES ########################################
required = {'PIL':">=1.1.6",
            'numpy':">=1.0"} 

optional = {'gmpy':'>=1.0', 
            'matplotlib':'>=0.8',
            'scipy':'>=0.5',
            'ipython':">=0.7"}
            
# for pip/easy_install (just go for the basics until easy_install works better!)
packages_to_install = [required]

packages_to_state = [required]
######################################################################

setup_args = {}


if 'setuptools' in sys.modules:
    # support easy_install without depending on setuptools
    install_requires = []
    for package_list in packages_to_install:
        install_requires+=["%s%s"%(package,version) for package,version in package_list.items()]
    setup_args['install_requires']=install_requires
    setup_args['dependency_links']=["http://pypi.python.org/simple/"]
    setup_args['zip_safe']=False

for package_list in packages_to_state:
    requires = []
    requires+=["%s (%s)"%(package,version) for package,version in package_list.items()]
    setup_args['requires']=requires


if 'bdist_wininst' in sys.argv:
    scripts.append('windows_postinstall.py')
    # CEBALERT: how else to get the ico into a place the postinstall script can find?!
    scripts.append("topographica.ico")


_topographica_devs='Topographica Developers'
_topographica_devs_email='developers[at]topographica[dot]org' 


setup_args.update(dict(
    name='topographica',

    # CEBALERT: we need one single place with the version number!  
    #
    # This release number is usually 1 higher than the Makefile's,
    # except when the Makefile is updated just prior to release.  This
    # is because DEBs etc being built between releases have a release
    # number of the next release combined with the svn revision
    # number, to match DEB convention. (Whereas for svn copy we are
    # using the opposite convention...)
    version='0.9.8',

    description='A general-purpose neural simulator focusing on topographic maps.',

    long_description="""
`Topographica`_ is a software package for computational modeling of
neural maps. The goal is to help researchers understand brain function
at the level of the topographic maps that make up sensory and motor
systems.

Please see http://topographica.org/ for more information.

Installation
============

Topographica is already packaged for a number of platforms, including
Linux, Mac, and Windows. Please see http://topographica.org/Downloads
for links to packages. Below is a brief summary for installation into
an existing Python environment.

If you have `easy_install`_ or `pip`_ (or similar), you can use one of
those to install Topographica and its dependencies automatically
(e.g. ``easy_install topographica`` or ``pip install topographica``).

Alternatively, you can download and unpack the archive below, and then
install Topographica with a command like ``python setup.py install``
(e.g. ``sudo python setup.py install`` for a site-wide installation,
or ``python setup.py install --user`` to install into
``~/.local``). You will need to install at least `NumPy`_ and `PIL`_
before running Topographica. We also recommend that you install
`MatPlotLib`_ so you can access all Topographica's plots, as well as
`Gmpy`_ and Weave (available as part of `SciPy`_) for optimum
performance.

.. _Topographica:
   http://topographica.org/Home/index.html
.. _NumPy: 
   http://pypi.python.org/pypi/numpy
.. _Gmpy: 
   http://pypi.python.org/pypi/gmpy
.. _SciPy: 
   http://pypi.python.org/pypi/scipy
.. _MatPlotLib: 
   http://pypi.python.org/pypi/matplotlib
.. _PIL: 
   http://pypi.python.org/pypi/PIL
.. _easy_install:
   http://peak.telecommunity.com/DevCenter/EasyInstall
.. _pip:
   http://pip.openplans.org/

""",

    author= _topographica_devs,
    author_email= _topographica_devs_email,
    maintainer= _topographica_devs,
    maintainer_email= _topographica_devs_email,
    platforms=['Windows', 'Mac OS X', 'Linux'],
    license='BSD',
#    download_url='http://sourceforge.net/projects/topographica/files/',
    url='http://topographica.org/',

    classifiers = [
        "License :: OSI Approved :: BSD License",
# (until packaging tested)
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Education",
        "Topic :: Scientific/Engineering"],

    # CEBALERT: do I have to list these? if I do, can I generate the list automatically?
    packages=['topo',
              'param',
              'topo.analysis',
              'topo.base',
              'topo.command',
              'topo.coordmapper',
              'topo.ep',
              'topo.learningfn',
              'topo.misc',
              'topo.numbergen',
              'topo.transferfn',
              'topo.pattern',
              'topo.plotting',
              'topo.projection',
              'topo.responsefn',
              'topo.sheet',
              'topo.tests',
              'topo.tkgui'],

    package_data={
        # CEBALERT: These things are not data, but I don't see how
        # else to make sure they are included
        'param': ['externaltk/snit-2.2.1/*.tcl',
                  'externaltk/scrodget-2.1/*.tcl',
                  'externaltk/tooltip-1.4/*.tcl'],

        'topo.tkgui': ['icons/*.*'],
        'topo.command':['*.png','*.pdf'],
        'topo.tests':['*.txt','*.jpg','*.pgm']},

    data_files=[('share/topographica/examples',examples)],

    scripts = scripts))



setup(**setup_args)
