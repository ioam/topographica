PREFIX = ${dir ${CURDIR}}
CC = gcc

default: gui-skip platform-skip python jpeg pil numpy matplotlib weave pychecker common pylint epydoc docutils ipython gmpy pyflakes

# avoid building some things on some platforms
# uses touch -a to avoid changing modification dates
platform-skip:
ifeq ("$(shell uname -s)","Darwin")
	touch -a tcl
	touch -a tk
# CEBALERT: doesn't stop readline building on mac!
	touch -a readline
endif

gui-skip:
ifeq (${GUI},0)
	touch -a tcl
	touch -a tk
endif


all: default pyaudiolab mlabwrap scipy ipython pyrex pytables psyco gnuplotpy

dist: bluesphere

clean: python-clean jpeg-clean pil-clean numpy-clean tk-clean tcl-clean matplotlib-clean weave-clean pychecker-clean common-clean pylint-clean epydoc-clean docutils-clean scipy-clean mlabwrap-clean ipython-clean libsndfile-clean pyaudiolab-clean psyco-clean pyrex-clean hdf5-clean pytables-clean gnuplotpy-clean bluesphere-clean player-clean progressbar-clean stage-clean gmp-clean mxnumber-clean gmpy-clean svn2cl-clean readline-clean termcap-clean guppy-clean pyopenssl-clean foolscap-clean zope_interface-clean twisted-clean mpi4py-clean openmpi-clean pyflakes-clean setuptools-clean freetype-clean libpng-clean zlib-clean m4-clean

uninstall: python-uninstall jpeg-uninstall pil-uninstall numpy-uninstall tk-uninstall tcl-uninstall matplotlib-uninstall weave-uninstall pychecker-uninstall common-uninstall pylint-uninstall epydoc-uninstall docutils-uninstall scipy-uninstall mlabwrap-uninstall ipython-uninstall libsndfile-uninstall pyaudiolab-uninstall psyco-uninstall pyrex-uninstall hdf5-uninstall pytables-uninstall gnuplotpy-uninstall player-uninstall progressbar-uninstall stage-uninstall gmp-uninstall mxnumber-uninstall gmpy-uninstall svn2cl-uninstall readline-uninstall termcap-uninstall guppy-uninstall pyopenssl-uninstall foolscap-uninstall zope_interface-uninstall twisted-uninstall mpi4py-uninstall openmpi-uninstall pyflakes-clean setuptools-clean freetype-uninstall libpng-uninstall zlib-uninstall m4-uninstall


#####
# CEB: hack apparently necessary to avoid occasional and mysterious
# "broken pipes" on buildbot
%.tar.gz_extract: %.tar.gz
	cp $< $<_tmp.tar.gz
	gunzip $<_tmp.tar.gz
	tar -xf $<_tmp.tar
	rm -f $<_tmp.tar

%.tgz_extract: %.tgz
	cp $< $<_tmp.tgz
	gunzip -f $<_tmp.tgz
	tar -xf $<_tmp.tar
	rm -f $<_tmp.tar
#####


##############################################################
# Python (interpreted language)
#
PYTHON2 = Python-2.7.3

PYTHON2_LIB  = lib/python2.7
PYTHON2_INC  = include/python2.7
PYTHON2_CONF = lib/python2.7/config

PYTHON2_UNINSTALL += bin/idle bin/python bin/pydoc bin/python2.7
PYTHON2_UNINSTALL += ${PYTHON2_LIB} man/man1/python.1 include/python2.7


# LDFLAGS sets ${PREFIX}/lib as the LD_LIBRARY in the binary
# CB: rpath is ignored on OS X (so where are the library files taken from?). 
python: ${PYTHON2}.tgz tk readline zlib
	echo ${PREFIX}
	tar -xzf ${PYTHON2}.tgz

# Configure for specific operating system versions
ifeq ("$(shell uname -s)","Darwin")
ifeq ("$(shell uname -r | cut -d . -f 1)","9") # Darwin 9.x == Mac OS X 10.5 (Leopard)
	patch -p0 < Python_OSX_tk.diff # build python with tcl/tk from /Library/Frameworks
	cd ${PYTHON2}; ./configure --prefix=${PREFIX} MACOSX_DEPLOYMENT_TARGET=10.5
else
ifeq ("$(shell uname -r | cut -d . -f 1)","10") # Darwin 10.x == Mac OS X 10.6 (Snow Leopard)
	cd ${PYTHON2}; ./configure --prefix=${PREFIX} MACOSX_DEPLOYMENT_TARGET=10.6 
else # Darwin pre 9
	patch -p0 < Python_OSX_tk.diff # build python with tcl/tk from /Library/Frameworks
	cd ${PYTHON2}; ./configure --prefix=${PREFIX}
endif
endif
else # linux
	cd ${PYTHON2}; ./configure --prefix=${PREFIX} LDFLAGS=-Wl,-rpath,${PREFIX}/lib
endif
	cd ${PYTHON2}; env PREFIX=${PREFIX} make EXTRA_CFLAGS=-I${PREFIX}/include
	cd ${PYTHON2}; env PREFIX=${PREFIX} make install
	touch python

python-clean:
	rm -rf ${PYTHON2} Python-2.4*/ Python-2.5*/ Python-2.6*/

python-uninstall:
	rm -rf python ${foreach f,${PYTHON2_UNINSTALL}, ${PREFIX}/${f}} Python-2.4*/ Python-2.5*/ Python-2.6*/

##############################################################
# Tcl (required by Tk GUI toolkit)
#
TCL = tcl8.5.10
TCL_UNINSTALL += bin/tclsh8.5 bin/wish8.5 lib/tclConfig.sh
TCL_UNINSTALL += lib/tcl8.5 lib.tclConfig.sh lib/libtcl8.5.so lib/libtclstub8.5.a
TCL_UNINSTALL += include/tcl*.h man/man*

tcl: ${TCL}-src.tar.gz
	tar -xzf ${TCL}-src.tar.gz
	cd ${TCL}/unix; ./configure --prefix=${PREFIX}
	make -C ${TCL}/unix install
	touch tcl

tcl-clean:
	rm -rf ${TCL} tcl8*/
tcl-uninstall:
	rm -rf tcl ${foreach f,${TCL_UNINSTALL}, ${PREFIX}/${f}} tcl8*/



##############################################################
# Tk (GUI toolkit)
#
TK = tk8.5.5

TK_UNINSTALL += lib/tk8.5 lib/libtk8.5.so lib/libtkstub8.5.a
TK_UNINSTALL += include/tk*.h lib/tkConfig.sh

tk: ${TK}-src.tar.gz tcl
	tar -xzf ${TK}-src.tar.gz
	cd ${TK}/unix; ./configure --prefix=${PREFIX} --enable-xft
	make -C ${TK}/unix install
	touch tk

tk-clean:
	rm -rf ${TK} tk8*/
tk-uninstall:
	rm -rf tk ${foreach f,${TK_UNINSTALL}, ${PREFIX}/${f}} tk8*/



##############################################################
# ipython (improved interactive prompt)
#
IPYTHON = ipython-0.12
IPYTHON_UNINSTALL =  ${PYTHON_LIB}/site-packages/IPython

ipython: ${IPYTHON}.tar.gz python 
	tar -xzf ${IPYTHON}.tar.gz
	cd ${IPYTHON}; ${PREFIX}/bin/python setup.py install
	touch ipython

ipython-clean:
	rm -rf ${IPYTHON} 
ipython-uninstall:
	rm -rf ipython ${IPYTHON} $(foreach f, ${IPYTHON_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# freetype 

FREETYPE = freetype-2.3.9
# CEBALERT: stuff missing, probably
FREETYPE_UNINSTALL += lib/libfreetype.* 

freetype: ${FREETYPE}.tar.gz
	tar -xzf ${FREETYPE}.tar.gz
	cd ${FREETYPE}; ./configure --prefix=${PREFIX} 
	make -C ${FREETYPE}
	make -C ${FREETYPE} install
	touch freetype

freetype-clean: 
	rm -rf ${FREETYPE} 
freetype-uninstall:
	rm -rf freetype $(foreach f, ${FREETYPE_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# zlib (dependency of libpng)

ZLIB = zlib-1.2.5

ZLIB_UNINSTALL += lib/libz*
ZLIB_UNINSTALL += share/man/man3/zlib*
ZLIB_UNINSTALL += lib/pkgconfig/zlib*
ZLIB_UNINSTALL += include/zlib*

zlib: ${ZLIB}.tar.gz
	tar -xzf ${ZLIB}.tar.gz
	cd ${ZLIB}; ./configure --prefix=${PREFIX} 
	make -C ${ZLIB} install
	touch zlib

zlib-clean: 
	rm -rf ${ZLIB} 
zlib-uninstall:
	rm -rf zlib $(foreach f, ${ZLIB_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# libpng

LIBPNG = libpng-1.2.40

LIBPNG_UNINSTALL += lib/libpng* 
LIBPNG_UNINSTALL += include/libpng*
LIBPNG_UNINSTALL += include/png* 
LIBPNG_UNINSTALL += share/man/man5/png* 
LIBPNG_UNINSTALL += lib/pkgconfig/libpng*


libpng: ${LIBPNG}.tar.gz zlib
	tar -xzf ${LIBPNG}.tar.gz
	cd ${LIBPNG}; env CFLAGS="-I${PREFIX}/include" LDFLAGS="-L${PREFIX}/lib" ./configure --prefix=${PREFIX} --includedir=${PREFIX}/include --libdir=${PREFIX}/lib
	make -C ${LIBPNG}
	make -C ${LIBPNG} install
	touch libpng

libpng-clean: 
	rm -rf ${LIBPNG} 
libpng-uninstall:
	rm -rf libpng $(foreach f, ${LIBPNG_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# jpeg (JPEG image library)

JPEG = jpeg-6b

JPEG_UNINSTALL += bin/cjpeg bin/djpeg bin/jpegtran bin/rdjpgcom bin/wrjpgcom
JPEG_UNINSTALL += lib/libjpeg.* 
JPEG_UNINSTALL += man/man1/cjpeg.1 man/man1/djpeg.1 man/man1/jpegtran.1
JPEG_UNINSTALL += man/man1/rdjpgcom.1 man/man1/wrjpgcom.1
JPEG_UNINSTALL += include/jconfig.h include/jerror.h include/jmorecfg.h include/jpeglib.h


jpeg: ${JPEG}.tgz
	tar -xzf ${JPEG}.tgz
# CEBALERT: for mac!
	mkdir -p ${PREFIX}/man
	mkdir -p ${PREFIX}/man/man1
	cd ${JPEG}; ./configure --prefix=${PREFIX} --enable-shared --enable-static
	make -C ${JPEG}
	make -C ${JPEG} test
	make -C ${JPEG} install
	touch jpeg

jpeg-clean: 
	rm -rf ${JPEG} 
jpeg-uninstall:
	rm -rf jpeg $(foreach f, ${JPEG_UNINSTALL}, ${PREFIX}/${f})


##############################################################
# PIL (bitmap image library)
#
PIL = Imaging-1.1.6
PIL_UNINSTALL = ${PYTHON_LIB}/site-packages/PIL

pil: ${PIL}.tgz jpeg python
	tar -xzf ${PIL}.tgz
#	cd ${PIL}/libImaging; ./configure --prefix=${PREFIX} --with-jpeg=${PREFIX}/lib
#	make -C ${PIL}/libImaging
#
# Apply OS-specific patches:
ifeq ("$(shell uname -m)","x86_64")
# CEBALERT: patch below might no longer be necessary, now we include zlib
#       # Tell 64-bit Linux machines where to find zlib, to prevent "encoder zip not available" problems
	cd ${PIL}; patch < ../Imaging.diff
endif

# On Mac, PIL inserts mac-specific locations before user-specified
# ones (surely a bug) no matter what you try to do ...except hack the
# setup.py script.
ifeq ("$(shell uname -s)","Darwin")
	cd ${PIL}; cp setup.py setup.py~; sed s^'join(prefix, "lib"))'^'join(prefix, "lib"),where=0)'^ setup.py~ > setup.py
	cd ${PIL}; cp setup.py setup.py~; sed s^'join(prefix, "include"))'^'join(prefix, "include"),where=0)'^ setup.py~ > setup.py
endif
	cd ${PIL}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py build_ext -i
	cd ${PIL}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python selftest.py
	cd ${PIL}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch pil

pil-clean:
	rm -rf ${PIL} 
pil-uninstall:
	rm -rf pil $(foreach f, ${PIL_UNINSTALL}, ${PREFIX}/${f})


##############################################################
# numpy (matrix library)
#
NUMPY = numpy-1.6.1
NUMPY_UNINSTALL =  ${PYTHON_LIB}/site-packages/numpy

numpy: ${NUMPY}.tar.gz python
	tar -xzf ${NUMPY}.tar.gz
	cd ${NUMPY}; ${PREFIX}/bin/python setup.py install
	touch numpy

numpy-clean:
	rm -rf ${NUMPY} 
numpy-uninstall:
	rm -rf numpy $(foreach f, ${NUMPY_UNINSTALL}, ${PREFIX}/${f})


##############################################################
# MatPlotLib (plotting library)
#
MATPLOTLIB = matplotlib-1.1.0
MATPLOTLIB_UNINSTALL =  ${PYTHON_LIB}/site-packages/matplotlib

# Workaround to allow MATPLOTLIB to compile on a remote session.
#
# Forces the DISPLAY variable to be set, if only to a guess at the
# correct value.  If DISPLAY is set incorrectly, matplotlib may not be
# able to find the right Tcl/Tk libraries.
ifeq ($(strip $(DISPLAY)),)
  MATPLOTLIB_DISPLAY="DISPLAY=:0"
else
  MATPLOTLIB_DISPLAY=
endif

matplotlib: ${MATPLOTLIB}.tar.gz python freetype libpng
	make ${MATPLOTLIB}.tar.gz_extract
#	tar -xzf ${MATPLOTLIB}.tar.gz
# use env vars because mpl somehow doesn't pass through I and L properly
	cd ${MATPLOTLIB}; env LDFLAGS="-L${PREFIX}/lib" CFLAGS="-I${PREFIX}/include -I${PREFIX}/include/freetype2 -I${PREFIX}/include/libpng12" ${PREFIX}/bin/python setup.py build_ext -L${PREFIX}/lib/
	cd ${MATPLOTLIB}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${MATPLOTLIB_DISPLAY} ${PREFIX}/bin/python setup.py build
	cd ${MATPLOTLIB}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${MATPLOTLIB_DISPLAY} ${PREFIX}/bin/python setup.py install
	touch matplotlib

matplotlib-clean:
	rm -rf ${MATPLOTLIB} matplotlib-0.90*/
matplotlib-uninstall:
	rm -rf matplotlib ${MATPLOTLIB} $(foreach f, ${MATPLOTLIB_UNINSTALL}, ${PREFIX}/${f}) matplotlib-0.90*/



##############################################################
# Weave (on its own apart from Scipy)
#
WEAVE = scipy-0.7.1
WEAVE_UNINSTALL = ${PYTHON_LIB}/site-packages/weave external/weave

# Forces removal of weave version used with Numeric
weave: ${WEAVE}.tar.gz python
	rm -rf Scipy_core-0.3.0_108.1820
	rm -f ${PYTHON_LIB}/site-packages/weave external/weave
	tar -xzf ${WEAVE}.tar.gz
# we make weave not depend on scipy
	patch -p0 < weave.diff
# CEBALERT: Remove next time scipy is updated
# http://projects.scipy.org/scipy/ticket/855
	patch -p0 < weave_keyerror.patch
	cp ${WEAVE}/scipy/io/dumb_shelve.py ${WEAVE}/scipy/weave/
	cp ${WEAVE}/scipy/io/dumbdbm_patched.py ${WEAVE}/scipy/weave
	cd ${WEAVE}/scipy/weave/; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch weave

weave-clean:
	rm -rf ${WEAVE} weave-3852
weave-uninstall:
	rm -rf weave ${WEAVE} $(foreach f, ${WEAVE_UNINSTALL}, ${PREFIX}/${f}) weave-3852



##############################################################
# Scipy
#
SCIPY = scipy-0.7.1
SCIPY_UNINSTALL = ${PYTHON_LIB}/site-packages/scipy external/scipy

# Forces removal of scipy version used with Numeric
scipy: ${SCIPY}.tar.gz python
	rm -f ${PYTHON_LIB}/site-packages/scipy external/scipy
	tar -xzf ${SCIPY}.tar.gz
	cp scipy-site.cfg ${SCIPY}/site.cfg
	cd ${SCIPY}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch scipy

scipy-clean:
	rm -rf ${SCIPY} 
scipy-uninstall:
	rm -rf scipy ${SCIPY} $(foreach f, ${SCIPY_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# Fixed-Point package
#
# We no longer build fixedpoint because it's included in topo as
# topo/misc/fixedpoint.py. This section shows how we generate
# fixedpoint.py by patching the original fixedpoint.py to support
# pickling.
#
#
FIXEDPT = fixedpoint-0.1.2
FIXEDPT_UNINSTALL = ${PYTHON_LIB}/site-packages

fixedpoint: ${FIXEDPT}.tgz python fixedpoint.diff fixedpoint_setup.py
	rm -rf ${FIXEDPT}
	tar -xzf ${FIXEDPT}.tgz
	mv fixedpoint ${FIXEDPT}
	cp fixedpoint.diff ${FIXEDPT}
	cp fixedpoint_setup.py ${FIXEDPT}/setup.py
	cd ${FIXEDPT}; patch < fixedpoint.diff; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch fixedpoint

fixedpoint-clean:
	rm -rf ${FIXEDPT}
fixedpoint-uninstall:
	rm -rf fixedpoint ${FIXEDPT} ${FIXEDPT_UNINSTALL}/fixedpoint*


##############################################################
# pyflakes (optional source code checker)
#
PYFLAKES = pyflakes-0.5.0
PYFLAKES_UNINSTALL = ${PYTHON_LIB}/site-packages/pyflakes*
PYFLAKES_UNINSTALL = ${PREFIX}/bin/pyflakes

pyflakes: ${PYFLAKES}.tar.gz python
	tar -xzf ${PYFLAKES}.tar.gz
	cd ${PYFLAKES}; ${PREFIX}/bin/python setup.py install
	touch pyflakes

pyflakes-clean:
	rm -rf ${PYFLAKES} 
pyflakes-uninstall:
	rm -rf pyflakes ${PYFLAKES} $(foreach f, ${PYFLAKES_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# pychecker (optional source code checker)
#
PYCHECKER = pychecker-0.8.18-CVS-200712061936
PYCHECKER_UNINSTALL = ${PYTHON_LIB}/site-packages/pychecker

pychecker: ${PYCHECKER}.tar.gz python
	tar -xzf ${PYCHECKER}.tar.gz
	cd ${PYCHECKER}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch pychecker

pychecker-clean:
	rm -rf ${PYCHECKER} 
pychecker-uninstall:
	rm -rf pychecker ${PYCHECKER} $(foreach f, ${PYCHECKER_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# logilab common files, required for pylint (but should be 
# removed if pylint is removed)
#
COMMON = logilab-common-0.41.0
COMMON_UNINSTALL = ${PYTHON_LIB}/site-packages/logilab/common

common: ${COMMON}.tar.gz python
	tar -xzf ${COMMON}.tar.gz
	cd ${COMMON}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch common

common-clean:
	rm -rf ${COMMON} 
common-uninstall:
	rm -rf common ${COMMON} $(foreach f, ${COMMON_UNINSTALL}, ${PREFIX}/${f})



################################################################
# logilab astng, required for pylint (but should be 
# removed if pylint is removed)
ASTNG = logilab-astng-0.19.0
ASTNG_UNINSTALL = ${PYTHON_LIB}/site-packages/logilab/astng

astng: ${ASTNG}.tar.gz python
	tar -xzf ${ASTNG}.tar.gz
	cd ${ASTNG}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch astng

astng-clean:
	rm -rf ${ASTNG} logilab-astng-0.*/
astng-uninstall:
	rm -rf astng ${ASTNG} $(foreach f, ${ASTNG_UNINSTALL}, ${PREFIX}/${f}) logilab-astng-0.*/



##############################################################
# pylint (optional source-code checker)
#
PYLINT = pylint-0.18.0
PYLINT_UNINSTALL = ${PYTHON_LIB}/site-packages/pylint

pylint: ${PYLINT}.tar.gz python common astng
	tar -xzf ${PYLINT}.tar.gz
	cd ${PYLINT}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch pylint

pylint-clean: astng-clean common-clean
	rm -rf ${PYLINT} pylint-0.*/
pylint-uninstall: astng-uninstall common-uninstall
	rm -rf pylint ${PYLINT} $(foreach f, ${PYLINT_UNINSTALL}, ${PREFIX}/${f}) pylint-0.*/



##############################################################
# epydoc (Automatic Reference_Manual generator)
#
EPYDOC3 = epydoc-3.0.1
EPYDOC3_UNINSTALL = ${PYTHON_LIB}/site-packages/epydoc

epydoc: ${EPYDOC3}.tar.gz python
	tar -xzf ${EPYDOC3}.tar.gz
	cd ${EPYDOC3}; cd epydoc ; patch -p0 < ../../epydoc.diff; cd .. ; ${PREFIX}/bin/python setup.py install
	touch epydoc

epydoc-clean:
	rm -rf ${EPYDOC3} 
epydoc-uninstall:
	rm -rf epydoc ${EPYDOC3} $(foreach f, ${EPYDOC3_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# docutils (used by epydoc)
#
DOCUTILS = docutils-0.4
DOCUTILS_UNINSTALL = ${PYTHON_LIB}/site-packages/docutils

docutils: ${DOCUTILS}.tar.gz python
	tar -xzf ${DOCUTILS}.tar.gz
	cd ${DOCUTILS}; ${PREFIX}/bin/python setup.py install
	touch docutils

docutils-clean:
	rm -rf ${DOCUTILS} 
docutils-uninstall:
	rm -rf docutils ${DOCUTILS} $(foreach f, ${DOCUTILS_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# libsndfile (used by pyaudiolab)
#
LIBSNDFILE = libsndfile-1.0.24

LIBSNDFILE_UNINSTALL += bin/sndfile-* 
LIBSNDFILE_UNINSTALL += lib/libsndfile.*

libsndfile: ${LIBSNDFILE}.tar.gz
	tar -xzf ${LIBSNDFILE}.tar.gz
	cd ${LIBSNDFILE}; ./configure --prefix=${PREFIX}
	cd ${LIBSNDFILE}; make 
	cd ${LIBSNDFILE}; make install
	touch libsndfile

libsndfile-clean:
	rm -rf ${LIBSNDFILE} 
libsndfile-uninstall:
	rm -rf libsndfile ${foreach f,${LIBSNDFILE_UNINSTALL}, ${PREFIX}/${f}}


##############################################################
# setuptools (required by audiolab)
#
SETUPTOOLS = setuptools-0.6c11
SETUPTOOLS_UNINSTALL = ${PYTHON_LIB}/site-packages/setuptools*

setuptools: ${SETUPTOOLS}.tar.gz python
	tar -xzf ${SETUPTOOLS}.tar.gz
	cd ${SETUPTOOLS}; ${PREFIX}/bin/python setup.py install
	touch setuptools

setuptools-clean:
	rm -rf ${SETUPTOOLS} 
setuptools-uninstall:
	rm -rf setuptools ${SETUPTOOLS} $(foreach f, ${SETUPTOOLS_UNINSTALL}, ${PREFIX}/${f})


##############################################################
# pyaudiolab (sound file reading)
#
# optionally sudo apt-get install libasound2-dev
# (or for Mac, get the CoreAudio framework from Apple)
PYAUDIOLAB = scikits.audiolab-0.11.0
PYAUDIOLAB_UNINSTALL = ${PYTHON_LIB}/site-packages/scikits.audiolab*egg

pyaudiolab: ${PYAUDIOLAB}.tar.gz python libsndfile setuptools 
	tar -xzf ${PYAUDIOLAB}.tar.gz
	cd ${PYAUDIOLAB}; env PREFIX=${PREFIX} LD_LIBRARY_PATH=${PREFIX}/lib ${PREFIX}/bin/python setup.py install
	touch pyaudiolab

pyaudiolab-clean:
	rm -rf ${PYAUDIOLAB} 
pyaudiolab-uninstall:
	rm -rf pyaudiolab ${PYAUDIOLAB} $(foreach f, ${PYAUDIOLAB_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# mlabwrap (high level python to matlab bridge)
#
MLABWRAP = mlabwrap-1.0
MLABWRAP_UNINSTALL =  ${PYTHON_LIB}/site-packages/mlabwrap.py*
MLABWRAP_UNINSTALL += ${PYTHON_LIB}/site-packages/mlabrawmodule.so

mlabwrap: ${MLABWRAP}.tar.gz python 
	tar -xzf ${MLABWRAP}.tar.gz
	cd ${MLABWRAP}; ${PREFIX}/bin/python setup.py install
	touch mlabwrap

mlabwrap-clean:
	rm -rf ${MLABWRAP} 
mlabwrap-uninstall:
	rm -rf mlabwrap ${MLABWRAP} $(foreach f, ${MLABWRAP_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# PSYCO
#
PSYCO = psyco-dist

PSYCO_UNINSTALL += ${PYTHON_LIB}/site-packages/psyco

psyco: ${PSYCO}-svn56930.tar.gz python
	tar -xzf ${PSYCO}-svn56930.tar.gz
	cd ${PSYCO}; ${PREFIX}/bin/python setup.py install
	touch psyco

psyco-clean:
	rm -rf ${PSYCO} 
psyco-uninstall:
	rm -rf psyco ${foreach f,${PSYCO_UNINSTALL}, ${PREFIX}/${f}}



##############################################################
# Pyrex (required by PyTables)
#
PYREX = Pyrex-0.9.5.1a

PYREX_UNINSTALL += ${PYTHON_LIB}/site-packages/Pyrex

pyrex: ${PYREX}.tar.gz python
	tar -xzf ${PYREX}.tar.gz
	cd ${PYREX}; ${PREFIX}/bin/python setup.py install
	touch pyrex

pyrex-clean:
	rm -rf ${PYREX}
pyrex-uninstall:
	rm -rf pyrex ${foreach f,${PYREX_UNINSTALL}, ${PREFIX}/${f}}



##############################################################
# HDF5 library (required by PyTables)
#
HDF5 = hdf5-1.8.9

HDF5_UNINSTALL += 

hdf5: ${HDF5}.tar.gz
	tar -xzf ${HDF5}.tar.gz
	cd ${HDF5}; ./configure --enable-cxx --prefix=${PREFIX}
	make -C ${HDF5} install
	touch hdf5

hdf5-clean:
	rm -rf ${HDF5} 
hdf5-uninstall:
	rm -rf hdf5 ${foreach f,${HDF5_UNINSTALL}, ${PREFIX}/${f}}


##############################################################
# Numexpr
#
NUMEXPR = numexpr-2.0.1

NUMEXPR_UNINSTALL += ${PYTHON_LIB}/site-packages/numexpr

numexpr: ${NUMEXPR}.tar.gz python
	tar -xzf ${NUMEXPR}.tar.gz
	cd ${NUMEXPR}; ${PREFIX}/bin/python setup.py install
	touch numexpr

numexpr-clean:
	rm -rf ${NUMEXPR}

numexpr-uninstall:
	rm -rf numexpr ${foreach f,${NUMEXPR_UNINSTALL}, ${PREFIX}/${f}}

##############################################################
# PyTables
#
PYTABLES = tables-2.4.0

PYTABLES_UNINSTALL += ${PYTHON_LIB}/site-packages/tables

pytables: ${PYTABLES}.tar.gz hdf5 numexpr cython
	tar -xzf ${PYTABLES}.tar.gz
	cd ${PYTABLES}; ${PREFIX}/bin/python setup.py install --hdf5=${PREFIX}
	touch pytables

pytables-clean:
	rm -rf ${PYTABLES}
pytables-uninstall:
	rm -rf pytables ${foreach f,${PYTABLES_UNINSTALL}, ${PREFIX}/${f}}

##############################################################
# BlueSphere
# Only needs to be updated when the choice of icons changes, as the results 
# are ordinarily checked in under topo/tkgui/icons/.
# 
BLUESPHERE = BlueSphere-SVG-snapshot-Nov-29-2002

BLUESPHERE_UNINSTALL += topo/tkgui/icons/*.png

bluesphere: ${BLUESPHERE}.tar.gz
	rm -rf ${BLUESPHERE}
	mkdir ${BLUESPHERE}
	cd ${BLUESPHERE}; tar -xzf ../${BLUESPHERE}.tar.gz
	cp ${BLUESPHERE}_Makefile ${BLUESPHERE}/Makefile
	cd ${BLUESPHERE}; make
	cp ${BLUESPHERE}/*.png ../topo/tkgui/icons/
	touch bluesphere

bluesphere-clean:
	rm -rf ${BLUESPHERE}
bluesphere-uninstall:
	rm -rf bluesphere ${foreach f,${BLUESPHERE_UNINSTALL}, ${PREFIX}/${f}}

##############################################################
# Gnuplotpy
#
GNUPLOTPY = gnuplot-py-1.7

GNUPLOTPY_UNINSTALL += ${PYTHON_LIB}/site-packages/Gnuplot

gnuplotpy: ${GNUPLOTPY}.tar.gz
	tar -xzf ${GNUPLOTPY}.tar.gz
	cd ${GNUPLOTPY}; ${PREFIX}/bin/python setup.py install
	touch gnuplotpy

gnuplotpy-clean:
	rm -rf ${GNUPLOTPY}
gnuplotpy-uninstall:
	rm -rf gnuplotpy ${foreach f,${GNUPLOTPY_UNINSTALL}, ${PREFIX}/${f}}

##############################################################
# Player
#
# ALERT: Not fully tested yet; may need more attention
PLAYER = player-2.1.0rc1

PLAYER_UNINSTALL += ${PYTHON_LIB}/site-packages/playerc* ${PYTHON_LIB}/site-packages/_playerc.so ${PYTHON_LIB}/../libplayer*

player: ${PLAYER}.tar.bz2
	tar -xjf ${PLAYER}.tar.bz2
	cd ${PLAYER}; ./configure --prefix=${PREFIX} ${PLAYER_FLAGS}
	make -C ${PLAYER} install
	make -C ${PLAYER}/client_libs/libplayerc/bindings/python
	cd ${PLAYER}/client_libs/libplayerc/bindings/python ; ${PREFIX}/bin/python ./setup.py install 
	touch player

player-clean:
	rm -rf ${PLAYER}
player-uninstall:
	rm -rf player ${foreach f,${PLAYER_UNINSTALL}, ${PREFIX}/${f}}



##############################################################
# Stage
#
# ALERT: Not fully tested yet; may need more attention
STAGE = stage-2.1.0rc1

STAGE_UNINSTALL += ${PYTHON_LIB}/../libstage*

stage: ${STAGE}.tar.bz2
	tar -xjf ${STAGE}.tar.bz2
	cd ${STAGE}; ./configure --prefix=${PREFIX}
	make -C ${STAGE} install
	touch stage

stage-clean:
	rm -rf ${STAGE}
stage-uninstall:
	rm -rf stage ${foreach f,${STAGE_UNINSTALL}, ${PREFIX}/${f}}



##############################################################
# progressbar
#
PROGRESSBAR = progressbar-2.2

PROGRESSBAR_UNINSTALL += ${PYTHON_LIB}/site-packages/progressbar.py

progressbar: ${PROGRESSBAR}.tar.gz python
	tar -xzf ${PROGRESSBAR}.tar.gz
	cd ${PROGRESSBAR}; ${PREFIX}/bin/python setup.py install
	touch progressbar

progressbar-clean:
	rm -rf ${PROGRESSBAR}
progressbar-uninstall:
	rm -rf progressbar ${foreach f,${PROGRESSBAR_UNINSTALL}, ${PREFIX}/${f}}


#############################################################
# GNU M4
M4 = m4-1.4.9

M4_UNINSTALL += share/info/m4*
M4_UNINSTALL += share/man/man1/m4*

m4: ${M4}.tar.gz 
	tar -xzf ${M4}.tar.gz
	cd ${M4}; ./configure --prefix=${PREFIX} 
	make -C ${M4}
	make -C ${M4} install
	touch m4

m4-clean: 
	rm -rf ${M4} 
m4-uninstall:
	rm -rf m4 $(foreach f, ${M4_UNINSTALL}, ${PREFIX}/${f})



#############################################################
# GNU MP
GMP = gmp-4.3.1

GMP_UNINSTALL += lib/libgmp.* 
GMP_UNINSTALL += include/gmp.h


gmp: ${GMP}.tar.gz m4
	tar -xzf ${GMP}.tar.gz
	cd ${GMP}; env PATH=${PREFIX}/bin:${PATH} ./configure --prefix=${PREFIX} 
	env PATH=${PREFIX}/bin:${PATH} make -C ${GMP}
	env PATH=${PREFIX}/bin:${PATH} make -C ${GMP} check
	env PATH=${PREFIX}/bin:${PATH} make -C ${GMP} install
	touch gmp

gmp-clean: 
	rm -rf ${GMP} 
gmp-uninstall:
	rm -rf gmp $(foreach f, ${GMP_UNINSTALL}, ${PREFIX}/${f})


# CBALERT: there are probably other packages for which we should remove .egg-info?

# CB: mxnumber will be removed

##############################################################
# eGenix mx Experimental (for mxNumber)
#
MXNUMBER = egenix-mx-experimental-3.0.0

MXNUMBER_UNINSTALL += ${PYTHON_LIB}/site-packages/mx/
MXNUMBER_UNINSTALL += ${PYTHON_LIB}/site-packages/egenix_mx_experimental-3.0.0-py2.5.egg-info

mxnumber: ${MXNUMBER}.tar.gz python gmp
	tar -xzf ${MXNUMBER}.tar.gz
	cd ${MXNUMBER}; ${PREFIX}/bin/python setup.py install
	touch mxnumber

mxnumber-clean:
	rm -rf ${MXNUMBER}
mxnumber-uninstall:
	rm -rf mxnumber ${foreach f,${MXNUMBER_UNINSTALL}, ${PREFIX}/${f}}


##############################################################
# wraps GMP
#
GMPY = gmpy

GMPY_UNINSTALL += ${PYTHON_LIB}/site-packages/gmpy-1.01-py2.5.egg-info
GMPY_UNINSTALL += ${PYTHON_LIB}/site-packages/gmpy.so

gmpy: ${GMPY}-sources-101.tar.gz python gmp
	tar -xzf ${GMPY}-sources-101.tar.gz
	cd ${GMPY}; ${PREFIX}/bin/python setup.py build_ext --include-dirs='${PREFIX}/include' --library-dirs='${PREFIX}/lib'; ${PREFIX}/bin/python setup.py install
	touch gmpy

gmpy-clean:
	rm -rf ${GMPY}
gmpy-uninstall:
	rm -rf gmpy ${foreach f,${GMPY_UNINSTALL}, ${PREFIX}/${f}}



##############################################################
# processing (improved interactive prompt)
#
PROCESSING = processing-0.51
PROCESSING_UNINSTALL =  ${PYTHON_LIB}/site-packages/processing
PROCESSING_UNINSTALL += ${PYTHON_LIB}/site-packages/processing-0.51-py2.5.egg-info

processing: ${PROCESSING}.tar.gz python 
	tar -xzf ${PROCESSING}.tar.gz
	cd ${PROCESSING}; ${PREFIX}/bin/python setup.py install
	touch processing

processing-clean:
	rm -rf ${PROCESSING} 
processing-uninstall:
	rm -rf processing ${PROCESSING} $(foreach f, ${PROCESSING_UNINSTALL}, ${PREFIX}/${f})



##############################################################
# svn2cl (Only used for generating the ChangeLog)
#
SVN2CL = svn2cl-0.10

svn2cl: ${SVN2CL}.tar.gz
	tar -xzf ${SVN2CL}.tar.gz
	ln -sf ${SVN2CL}/svn2cl.sh svn2cl

svn2cl-clean:

svn2cl-uninstall:
	rm -rf svn2cl ${SVN2CL}


##############################################################
# pyttk (CB: currently unused - will replace Tile.py)
#
PYTTK = pyttk-0.2.6

PYTTK_UNINSTALL += ${PYTHON_LIB}/site-packages/pyttk.py

pyttk: ${PYTTK}.tar.gz python
	tar -xzf ${PYTTK}.tar.gz
	cd ${PYTTK}; ${PREFIX}/bin/python setup.py install
	touch pyttk

pyttk-clean:
	rm -rf ${PYTTK}
pyttk-uninstall:
	rm -rf pyttk ${foreach f,${PYTTK_UNINSTALL}, ${PREFIX}/${f}}


#############################################################
# GNU READLINE
READLINE = readline-5.2

READLINE_UNINSTALL += lib/libreadline.* 
READLINE_UNINSTALL += include/readline.h

readline: ${READLINE}.tar.gz termcap
	tar -xzf ${READLINE}.tar.gz
	cd ${READLINE}; ./configure --prefix=${PREFIX} 
	make -C ${READLINE}
	make -C ${READLINE} install
	touch readline

readline-clean: 
	rm -rf ${READLINE} 
readline-uninstall:
	rm -rf readline $(foreach f, ${READLINE_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# GNU TERMCAP
TERMCAP = termcap-1.3.1

TERMCAP_UNINSTALL += lib/libtermcap.* 
TERMCAP_UNINSTALL += include/termcap.h

termcap: ${TERMCAP}.tar.gz
	tar -xzf ${TERMCAP}.tar.gz
	cd ${TERMCAP}; ./configure --prefix=${PREFIX} 
	make -C ${TERMCAP}
	make -C ${TERMCAP} install
	touch termcap

termcap-clean: 
	rm -rf ${TERMCAP} 
termcap-uninstall:
	rm -rf termcap $(foreach f, ${TERMCAP_UNINSTALL}, ${PREFIX}/${f})




#############################################################
# CYTHON
CYTHON = Cython-0.16

CYTHON_UNINSTALL += ${PYTHON_LIB}/site-packages/Cython*
CYTHON_UNINSTALL += ${PYTHON_LIB}/site-packages/pyximport
CYTHON_UNINSTALL += bin/cython

cython: ${CYTHON}.tar.gz
	tar -xzf ${CYTHON}.tar.gz
	cd ${CYTHON}; ${PREFIX}/bin/python setup.py install
	touch cython

cython-clean: 
	rm -rf ${CYTHON} 
cython-uninstall:
	rm -rf cython $(foreach f, ${CYTHON_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# LINE_PROFILER
LINE_PROFILER = line_profiler-582df342463a

LINE_PROFILER_UNINSTALL += ${PYTHON_LIB}/site-packages/line_profiler*
LINE_PROFILER_UNINSTALL += bin/kernprof.py

line_profiler: ${LINE_PROFILER}.tar.gz cython
	tar -xzf ${LINE_PROFILER}.tar.gz
	cd ${LINE_PROFILER}; ${PREFIX}/bin/python setup.py install
	touch line_profiler

line_profiler-clean: 
	rm -rf ${LINE_PROFILER} 
line_profiler-uninstall:
	rm -rf line_profiler $(foreach f, ${LINE_PROFILER_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# guppy: provides heapy, a memory profiler
GUPPY = guppy-r70

GUPPY_UNINSTALL += ${PYTHON_LIB}/site-packages/guppy
GUPPY_UNINSTALL += ${PYTHON_LIB}/site-packages/guppy*.egg*

guppy: ${GUPPY}.tar.gz python
	tar -xzf ${GUPPY}.tar.gz
	cd ${GUPPY}; ${PREFIX}/bin/python setup.py install
	touch guppy

guppy-clean: 
	rm -rf ${GUPPY} 
guppy-uninstall:
	rm -rf guppy $(foreach f, ${GUPPY_UNINSTALL}, ${PREFIX}/${f})



#############################################################
# OpenMPI
OPENMPI = openmpi-1.3.3

# CEBALERT: uninstall info not complete!
OPENMPI_UNINSTALL += lib/libmpi*
OPENMPI_UNINSTALL += lib/openmpi
OPENMPI_UNINSTALL += lib/mpi.mod
OPENMPI_UNINSTALL += bin/mpi*

openmpi: ${OPENMPI}.tar.gz
	tar -xzf ${OPENMPI}.tar.gz
	cd ${OPENMPI}; ./configure --prefix=${PREFIX} 
	cd ${OPENMPI}; make all install
	touch openmpi

openmpi-clean: 
	rm -rf ${OPENMPI} 
openmpi-uninstall:
	rm -rf openmpi $(foreach f, ${OPENMPI_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# mpi4py using Topographica's openmpi
#
# 2009/11/03: Works on DICE ("make mpi4py-test" shows most tests passing)
# 2009/11/03: Works on my Ubuntu 9.10 machine (tests pass similarly to above)
MPI4PY = mpi4py-1.1.0

MPI4PY_UNINSTALL += ${PYTHON_LIB}/site-packages/mpi4py
MPI4PY_UNINSTALL += ${PYTHON_LIB}/site-packages/mpi4py*.egg*

mpi4py: ${MPI4PY}.tar.gz python openmpi
	tar -xzf ${MPI4PY}.tar.gz
# specify topographica's copy of OpenMPI
	echo "[topo-openmpi]" >> ${MPI4PY}/mpi.cfg
	echo "mpi_dir              = ${PREFIX}" >> ${MPI4PY}/mpi.cfg
	echo "mpicc                = %(mpi_dir)s/bin/mpicc" >> ${MPI4PY}/mpi.cfg
	echo "mpicxx               = %(mpi_dir)s/bin/mpicxx" >> ${MPI4PY}/mpi.cfg
	echo "library_dirs         = %(mpi_dir)s/lib:%(mpi_dir)s/lib/openmpi" >> ${MPI4PY}/mpi.cfg
	echo "runtime_library_dirs = %(library_dirs)s" >> ${MPI4PY}/mpi.cfg
# without MPILD, finds system linker first
	cd ${MPI4PY}; env MPILD=${PREFIX}/bin/mpicc ${PREFIX}/bin/python setup.py build --mpi=topo-openmpi
# without MPILD, MPICC, and MPICXX, finds system versions first
	cd ${MPI4PY}; env MPILD=${PREFIX}/bin/mpicc MPICC=${PREFIX}/bin/mpicc MPICXX=${PREFIX}/bin/mpicxx ${PREFIX}/bin/python setup.py install
	touch mpi4py

mpi4py-clean: 
	rm -rf ${MPI4PY} 
mpi4py-uninstall:
	rm -rf mpi4py $(foreach f, ${MPI4PY_UNINSTALL}, ${PREFIX}/${f})

mpi4py-test: mpi4py
	${PREFIX}/bin/mpiexec -n 2 ${PREFIX}/bin/python ${PREFIX}/external/mpi4py-1.1.0/test/runalltest.py


#############################################################
# mpi4py using system mpi: optionally set SYSTEM_MPI
# (e.g. SYSTEM_MPI=lam); you might also need to edit mpi.cfg. 
#
# 2009/11/03: On eddie.ecdf, works fine as it is (just 'make -C
# external mpi4py_systemmpi'; 'make mpi4py_systemmpi-test' shows most
# tests passing).
# Note that on eddie, it's necessary to do the following before building
# or using mpi4py:
# $ module load openmpi/ethernet/gcc/latest
#
# 2009/11/03: On my Ubuntu 9.10 machine (with OpenMPI installed from
# Synaptic), builds ok but segfaults when running.
# 2009/11/04: Works on DICE ("make -C external mpi4py_systemmpi") as
# long as /usr/lib/openmpi/1.2.7-gcc/bin (or
# /usr/lib64/openmpi/1.2.7-gcc/bin) is in PATH before /usr/bin
# (e.g. type "export PATH=/usr/lib/openmpi/1.2.7-gcc/bin:$PATH").

MPI4PY_SYSTEMMPI = mpi4py-1.1.0

MPI4PY_SYSTEMMPI_UNINSTALL += ${PYTHON_LIB}/site-packages/mpi4py
MPI4PY_SYSTEMMPI_UNINSTALL += ${PYTHON_LIB}/site-packages/mpi4py*.egg*

mpi4py_systemmpi: ${MPI4PY_SYSTEMMPI}.tar.gz python 
	tar -xzf ${MPI4PY_SYSTEMMPI}.tar.gz
	cd ${MPI4PY_SYSTEMMPI}; ${PREFIX}/bin/python setup.py build --mpi=${SYSTEMMPI_MPI}
	cd ${MPI4PY_SYSTEMMPI}; ${PREFIX}/bin/python setup.py install
	touch mpi4py_systemmpi

mpi4py_systemmpi-clean: mpi4py-clean

mpi4py_systemmpi-uninstall: mpi4py-uninstall

mpi4py_systemmpi-test: mpi4py_systemmpi
	mpiexec -n 2 ${PREFIX}/bin/python ${PREFIX}/external/mpi4py-1.1.0/test/runalltest.py



#############################################################
# twisted: for parallel computing features in IPython
TWISTED = Twisted-8.2.0

# CEBALERT: probably not complete
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/ckeygen
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/trial
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/tap2deb
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/twistd
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/tkconch
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/cftp
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/mailmail
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/lore
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/conch
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/pyhtmlizer
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/mktap
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/manhole
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/tap2rpm
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/im
TWISTED_UNINSTALL += ${PYTHON_LIB}/bin/tapconvert

TWISTED_UNINSTALL += ${PYTHON_LIB}/site-packages/twisted
TWISTED_UNINSTALL += ${PYTHON_LIB}/site-packages/twisted*.egg*

twisted: ${TWISTED}.tar.gz python
	tar -xzf ${TWISTED}.tar.gz
	cd ${TWISTED}; ${PREFIX}/bin/python setup.py install
	touch twisted

twisted-clean: 
	rm -rf ${TWISTED} 
twisted-uninstall:
	rm -rf twisted $(foreach f, ${TWISTED_UNINSTALL}, ${PREFIX}/${f})


#############################################################
# zope_interface: for parallel computing features in IPython
ZOPE_INTERFACE = zope.interface-3.3.0

ZOPE_INTERFACE_UNINSTALL += ${PYTHON_LIB}/site-packages/zope*

zope_interface: ${ZOPE_INTERFACE}.tar.gz python
	tar -xzf ${ZOPE_INTERFACE}.tar.gz
	cd ${ZOPE_INTERFACE}; ${PREFIX}/bin/python setup.py install
	touch zope_interface

zope_interface-clean: 
	rm -rf ${ZOPE_INTERFACE} 
zope_interface-uninstall:
	rm -rf zope_interface $(foreach f, ${ZOPE_INTERFACE_UNINSTALL}, ${PREFIX}/${f})



#############################################################
# foolscap: for parallel computing features in IPython
FOOLSCAP = foolscap-0.4.2

FOOLSCAP_UNINSTALL += ${PYTHON_LIB}/site-packages/foolscap*

foolscap: ${FOOLSCAP}.tar.gz python pyopenssl
	tar -xzf ${FOOLSCAP}.tar.gz
	cd ${FOOLSCAP}; ${PREFIX}/bin/python setup.py install
	touch foolscap

foolscap-clean: 
	rm -rf ${FOOLSCAP} 
foolscap-uninstall:
	rm -rf foolscap $(foreach f, ${FOOLSCAP_UNINSTALL}, ${PREFIX}/${f})



#############################################################
# pyopenssl: required by foolscap
# (requires e.g. ssl-dev package)

PYOPENSSL = pyOpenSSL-0.9

PYOPENSSL_UNINSTALL += ${PYTHON_LIB}/site-packages/pyopenssl*

pyopenssl: ${PYOPENSSL}.tar.gz python 
	tar -xzf ${PYOPENSSL}.tar.gz
	cd ${PYOPENSSL}; ${PREFIX}/bin/python setup.py build
	cd ${PYOPENSSL}; ${PREFIX}/bin/python setup.py install
	touch pyopenssl

pyopenssl-clean: 
	rm -rf ${PYOPENSSL} 
pyopenssl-uninstall:
	rm -rf pyopenssl $(foreach f, ${PYOPENSSL_UNINSTALL}, ${PREFIX}/${f})




#############################################################
# IPython with parallel computing features

parallel_ipython: zope_interface twisted foolscap ipython



##############################################################
# coverage (code coverage analysis)
#
COVERAGE = coverage-3.4
COVERAGE_UNINSTALL += ${PYTHON_LIB}/site-packages/coverage*egg 
COVERAGE_UNINSTALL += ${PREFIX}/bin/coverage

coverage: ${COVERAGE}.tar.gz python setuptools
	tar -xzf ${COVERAGE}.tar.gz
	cd ${COVERAGE}; ${PREFIX}bin/python setup.py install
	touch coverage

coverage-clean:
	rm -rf ${COVERAGE} 
coverage-uninstall:
	rm -rf coverage ${COVERAGE} $(foreach f, ${COVERAGE_UNINSTALL}, ${PREFIX}/${f})

##############################################################
# Quantities (for Unit Support)
#
QUANTITIES = quantities-0.10.1

QUANTITIES_UNINSTALL += ${PYTHON_LIB}/site-packages/quantities

quantities: ${QUANTITIES}.tar.gz
	tar -xzf ${QUANTITIES}.tar.gz
	cd ${QUANTITIES}; ${PREFIX}/bin/python setup.py install
	touch quantities

quantities-clean:
	rm -rf ${QUANTITIES}
quantities-uninstall:
	rm -rf quantities ${foreach f,${QUANTITIES_UNINSTALL}, ${PREFIX}/${f}}


#############################################################################
# ADDED SEPTEMBER 2012 [ Migration to GitHub ]                              #
#                                                                           #
# If you are viewing this for a checkout before September 2012, please      #
# note that the following section was NOT part in the original Makefile.    #
#                                                                           #
# These generic targets  have been added for migration from Sourceforge     #
# to GitHub, introduced to dramatically reduce the size of the repository,  #
# removing the old binary files from SVN. These targets download the        #
# necessary files from Sourceforge. If you encounter errors due to missing  #
# archives files, please ensure the original make target is correct.        #
#                                                                           #
# Custom diffs and patches have also been removed from external by bundling #
# them with the tarballs they modify. For this reason, Imaging 1.1.6,       #
# Epydoc 3.0.1 and Scipy 0.7.1 are extracted upon download to decompress    #
# the necessary diffs.                                                      #
#                                                                           #
# These targets has been appended in September 2012 and should work for     #
# all correctly written targets: targets that list the required source      #
# archive(s) as necessary dependencies.                                     #
#############################################################################

%.tgz:
	wget --no-check-certificate https://sourceforge.net/projects/topographica/files/external-full-history/$@
	@ if [ $@ = Imaging-1.1.6.tgz ] ; then tar -xzf $@  ; fi

%.tar.gz:
	wget --no-check-certificate https://sourceforge.net/projects/topographica/files/external-full-history/$@
	@ if [ $@ = scipy-0.7.1.tar.gz -o  $@ = epydoc-3.0.1.tar.gz ] ; then tar -xzf $@  ; fi

%.py.gz:
	wget --no-check-certificate https://sourceforge.net/projects/topographica/files/external-full-history/$@

%.tar.bz2:
	wget --no-check-certificate https://sourceforge.net/projects/topographica/files/external-full-history/$@
