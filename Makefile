# $Id$
PREFIX =  ${CURDIR}/
PYLINT = bin/pylint --rcfile=doc/buildbot/pylintrc
PYFLAKES = bin/pyflakes

PYCHECKER = bin/pychecker --config doc/buildbot/pycheckrc

RELEASE = 0.9.7

PYTHON = ${PREFIX}/bin/python

SVNVERSION = ${shell svnversion}

# If SVNVERSION is "exported", form a new SVNVERSION xyz:abc where xyz
# is the svn version from git svn, and abc is the git id of the HEAD
# commit.

# CEBALERT: originally had $ at end of each regular expression below,
# but not sure how to do that in makefile.  Also, could it be one grep
# command? Needs to work for this kind of thing:
# $ git svn info
# Path: .
# URL: https://topographica.svn.sourceforge.net/svnroot/topographica/trunk/topographica
# Repository Root: https://topographica.svn.sourceforge.net/svnroot/topographica
# Repository UUID: 0ce056cd-c842-0410-9ff1-d0633a95805a
# Revision: 11384
# Node Kind: directory
# Schedule: normal
# Last Changed Author: ceball
# Last Changed Rev: 11384
# Last Changed Date: 2010-10-02 11:58:56 +0100 (Sat, 02 Oct 2010)
ifeq ("${SVNVERSION}","exported")
# CEBALERT: svnversion is probably 'exported' in other situations, too. How to make the command
# below fail gracefully if "git svn" not available?
	SVNVERSION = ${shell git svn info | sed -n 's/^Revision: \([0-9]*\)/\1/p'}:${shell git rev-parse HEAD}
endif


# if 0, skips building tk and related external packages
GUI = 1

# set to empty when building 'release' debs.
DEBSTATUS = -unstable


# CEBALERT: tied to exact windows version!
ifeq ("$(shell uname -s)","MINGW32_NT-5.1")
	TIMER = 
else
	TIMER = time 
endif


# Commands needed to build a public distribution

COMPRESS_ARCHIVE           = gzip
MAKE_ARCHIVE               = tar -cf -
MAKE_ZIP                   = zip -r -q
MKDIR                      = mkdir -p
SED			   = sed
RM                         = rm -f
CD                         = cd
CP                         = cp
MV                         = mv
MAKE                       = make

# Definitions for public distributions
PROGRAM                    = topographica
DIST_TMPDIR                = ../distributions
DIST_DIRNAME               = ${PROGRAM}-${RELEASE}
DIST_DIR                   = ${DIST_TMPDIR}/${DIST_DIRNAME}
DIST_ARCHIVE               = ${DIST_DIRNAME}.tar.gz
DIST_ZIP                   = ${DIST_DIRNAME}.zip



# Default does not include doc, in case user lacks PHP
default: ext-packages topographica

all: default reference-manual doc tests examples 

# CEBALERT: should be able to remove topo/tests/testsnapshot.typ,
# topo/tests/testplotfilesaver*.png
clean: clean-doc clean-ext-packages clean-compiled clean-coverage-output
	${RM} .??*~ *~ */*~ */.??*~ */*/*~ */*/.??*~ */*/*/*~ */*/*/.??*~ *.bak
	${RM} .#??*.* */.#??*.* */*/.#??*.* */*/*/.#??*.* current_profile ./topo/tests/testsnapshot.typ ./topo/tests/testplotfilesaver*.png
	${RM} -r bin include share lib man topographica ImageSaver*.jpeg python_topo


uninstall:
	make -C external uninstall


saved-examples: 
	make -C examples saved-examples


FORCE:


examples: FORCE
	make -C examples

ext-packages:
	make -C external

clean-ext-packages: 
	make -C external clean
	make -C external uninstall


# Build the Python startup script.  Rebuilt whenever a file changes in
# topo/ or examples, to make sure that topo.version is up to date.
topographica: external Makefile topo/*/*.py examples/*.ty
# site.USER_SITE is ignored to stop Python finding packages in
# ~/.local instead of Topographica's own packages.
	${PYTHON} ${PREFIX}/create_topographica_script.py "${PYTHON}" ${RELEASE} ${SVNVERSION} 0


topographica-external-python:
ifeq ("${PYTHON}","${PREFIX}/bin/python")
	$(error "Must specify external Python (via PYTHON=/path/to/external/python)")
else
	${PYTHON} ${PREFIX}/create_topographica_script.py "${PYTHON}" ${RELEASE} ${SVNVERSION} 1
endif

# CB: experimental
topographicagui: 
	echo "import topo.tkgui;topo.tkgui.start(mainloop=False)" > _gui.py
	echo "${PREFIX}bin/idle -n -t 'Topographica shell' -r _gui.py" > topographicagui
	echo "" >> topographicagui
	chmod a+x ${PREFIX}topographicagui


## Currently useful lint checks
pyflakes: # Everything except topo/tests (where we do lots of importing but not using...)
	${PYFLAKES} topo param | grep -v topo/tests

lint-base: # topo.base and param 
	${PYLINT} --ignore=param/tk.py --ignore=param/external.py topo.base param | cat
#CEBALERT: how to get pylint's "ignore" options to work? Upgrade pylint (http://www.logilab.org/ticket/70493)?


# CEBALERT: need to update pychecker and work on its configuration if
# we're going to use it.
check:
	${PYCHECKER} param/*.py topo/*.py topo/*/*.py
# CEBALERT: way too much output to use.
lint:
	${PYLINT} topo param




clean-compiled: clean-weave clean-pyc

clean-weave:
	rm -rf ~/.python2*_compiled/ | cat

clean-pyc:
	rm -f *.pyc param/*.pyc topo/*.pyc topo/*/*.pyc topo/*/*/*.pyc examples/*.pyc contrib/*.pyc

clean-doc:
	make -C doc clean

reference-manual: 
	make -C doc reference-manual

doc: FORCE
	make -C doc/


print-info:
	@echo Running at ${shell date +%s}
	@echo svnversion ${SVNVERSION}



# CEBALERT: Move into runtests.py
generate-map-tests-data:
	./topographica -c "cortex_density=8" examples/lissom_oo_or.ty -c "topo.sim.run(100);from topo.tests.test_map_measurement import *; generate(plotgroups_to_test)" 



#############################################################################
##### tests

# CEBALERT: remove all these and document elsewhere how to run all the
# tests (might involve making them simpler to run).  When removing,
# check that buildbot uses the command below (or a new simplified
# command if one is introduced) for each target rather than just "make
# target".
tests:
	./topographica -p 'targets=["unit"]' topo/tests/runtests.py

train-tests: print-info
	./topographica -p 'targets=["traintests"]' topo/tests/runtests.py

unopt-train-tests: print-info
	./topographica -p 'testdp=5' -p 'weave=False' -p 'targets=["traintests"]' topo/tests/runtests.py

speed-tests:
	./topographica -p timing=True -p 'targets=["speedtests"]' topo/tests/runtests.py

startup-speed-tests: 
	./topographica -p timing=True -p 'targets=["startupspeedtests"]' topo/tests/runtests.py

all-speed-tests: speed-tests startup-speed-tests

snapshot-tests:
	./topographica -p 'targets=["snapshots","pickle","scriptrepr","batch"]' topo/tests/runtests.py

gui-tests:
	./topographica -p 'targets=["gui"]' topo/tests/runtests.py

map-tests:
	./topographica -p 'targets=["maptests"]' topo/tests/runtests.py

slow-tests: tests train-tests unopt-train-tests all-speed-tests snapshot-tests gui-tests map-tests

#############################################################################



#############################################################################
##### coverage: intended for buildbot only

clean-coverage-output: clean-coverage-results clean-coverage-html

clean-coverage-results:
	${RM} -r .coverage*

# CBALERT: guess at output directory.
clean-coverage-html:
	${RM} -r ~/topographica/tests/coverage_html

coverage-html:
	bin/coverage combine 
	bin/coverage html --rcfile=doc/buildbot/coveragerc -d ~/topographica/tests/coverage_html
#############################################################################



#############################################################################
##### Compare topographica and C++ lissom output
or_comparisons:
	./topographica -c "from topo.tests.test_script import run_multiple_density_comparisons;nerr=run_multiple_density_comparisons('lissom_or_reference.ty'); import sys;sys.exit(nerr)"

oo_or_comparisons:
	./topographica -c "from topo.tests.test_script import run_multiple_density_comparisons;nerr=run_multiple_density_comparisons('lissom_oo_or_reference.ty'); import sys;sys.exit(nerr)"

## speed test
v_lissom:
	make -C topo/tests/reference/	
	${TIMER}./topographica -c "profiling=True;iterations=20000" topo/tests/reference/lissom_oo_or_reference.ty
#############################################################################



#############################################################################
# For maintainer only; be careful with these commands

## Subversion-only code release, without making new binaries
## Run these from a relatively clean copy of the topographica directory 
## (without stray files, especially in doc/).

# Update any files that keep track of the version number
new-version: FORCE
	mv setup.py setup.py~
	sed -e "s/version=.*,/version='${RELEASE}',/g" setup.py~ > setup.py

TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica

tag-release: 
	svn copy ${TOPOROOT}/trunk ${TOPOROOT}/releases/${RELEASE} -m "Create release ${RELEASE}"

# Update Topographica.org web site
sf-web-site: reference-manual doc
	rsync -v -arHz --rsh=ssh doc/. web.sf.net:/home/groups/t/to/topographica/htdocs/.


SCRIPTS_TO_KEEP_IN_DIST= ^goodhill_network90.ty ^hierarchical.ty ^leaky_lissom_or.ty ^lissom_fsa.ty ^lissom_oo_or.ty ^lissom_or_movie.ty ^lissom_or.ty ^lissom.ty ^lissom_whisker_barrels.ty ^obermayer_pnas90.ty ^som_retinotopy.ty ^sullivan_neurocomputing04.ty ^tiny.ty ^gcal.ty


# Clear out everything not intended for the public distribution
#
# This is ordinarily commented out in the SVN version for safety, 
# but it is enabled when the distribution directory is created.
#
#@@distclean: FORCE clean
#@@	   ${RM} .#* */.#* */*/.#* */*~ 
#@@	   ${RM} etc/topographica.elc ImageSaver*.ppm countalerts* annotate.out emacslog
#@@	   ${RM} current_profile script timing*
#@@	   ${RM} examples/*.typ
#@@	   ${RM} -r Output
#@@	   -mv images/ellen_arthur.pgm ./TMPellen_arthur.pgm
#@@	   ${RM} -r images sounds
#@@	   ${RM} -r info
#@@	   mkdir images; mv ./TMPellen_arthur.pgm images/ellen_arthur.pgm
#@@	   ${RM} -r setup.py MANIFEST.in windows_postinstall.py topographica.ico
#@@	   ${RM} -r tmp/
#@@	   ${RM} -r contrib/
#@@	   ${RM} -r .svn */.svn */*/.svn */*/*/.svn */*/*/*/.svn
#@@	   ${CD} topo/tests/reference ; make clean
#@@	   ${RM} -r doc/buildbot/
#@@	   ${RM} -r debian/
#@@	   find examples/*.ty -maxdepth 1 ${subst ^,! -name ,${SCRIPTS_TO_KEEP_IN_DIST}} -exec rm {} \;


# Make public distribution archive
distarc: FORCE distclean 
	${CD} .. ; ${RM} -f ${DIST_ZIP} ; ${MAKE_ZIP} ${DIST_ZIP} ${DIST_DIRNAME} 

# Create public distribution subdirectory
distdir: FORCE
	${RM} -r ${DIST_DIR}
	${MKDIR} ${DIST_DIR}
	${CP} -r -d . ${DIST_DIR}
	${RM} ${DIST_DIR}/Makefile 
	${SED} \
	-e 's|^#@@||' \
	Makefile > ${DIST_DIR}/Makefile 

# Create public distribution subdirectory and archive
dist: doc distdir reference-manual FORCE
	${CD} ${DIST_DIR}; ${MAKE} distarc


# Note that the output needs to be appended to a copy of the old file,
# to keep old fixes to formatting. The HEAD:9000 can be omitted to get
# the full list, but this is faster.
ChangeLog.txt: FORCE
	make -C external svn2cl
	external/svn2cl -r HEAD:9000 --include-rev --group-by-day --separate-daylogs --break-before-msg --stdout https://topographica.svn.sourceforge.net/svnroot/topographica/ | sed -e 's|/trunk/topographica/||g' > ChangeLog.txt


######################################################################
# Create public distribution suitable for creating setup.py-based
# packages (e.g. debs)

dist-setup.py: doc distdir reference-manual
# clean dir but keep setup.py-related files
	${CD} ${DIST_DIR}; ${PYTHON} create_topographica_script.py "${PYTHON}" ${RELEASE} ${SVNVERSION} 1
	${CD} ${DIST_DIR}; ${MV} README.setup.txt README.txt
	${CD} ${DIST_DIR}; ${MV} setup.py TMPsetup.py; mv MANIFEST.in tmpMANIFEST.in; mv topographica TMPtopographica; mv topographica.ico TMPtopographica.ico; mv windows_postinstall.py TMPwindows_postinstall.py
	${CD} ${DIST_DIR}; make distclean
	${CD} ${DIST_DIR}; ${MV} TMPsetup.py setup.py; mv tmpMANIFEST.in MANIFEST.in; mv TMPtopographica topographica; mv TMPtopographica.ico topographica.ico; mv TMPwindows_postinstall.py windows_postinstall.py
# won't need to build this copy
	${RM} ${DIST_DIR}/Makefile 
	${RM} -r ${DIST_DIR}/external
# create tar.gz
	${CD} ${DIST_TMPDIR} ; ${MAKE_ARCHIVE} ${DIST_DIRNAME} | ${COMPRESS_ARCHIVE} > ${DIST_ARCHIVE}


######################################################################
# pypi
#
# These commands assume you have run "make dist-setup.py".
# (Archives don't include doc/ because of its size.)

# buildbot can set BDIST_WIN_CMD to bdist_msi when we upgrade to
# Python 2.7 (to get msi file, which can be installed from the
# commandline)
BDIST_WIN_CMD = bdist_wininst
BDIST_WININST = ${BDIST_WIN_CMD} --install-script windows_postinstall.py --plat-name=win

dist-setup.py-sdist: 
	${CD} ${DIST_DIR}; ${PYTHON} setup.py sdist

# generate windows exe (like the exe you get for numpy or matplotlib)
dist-setup.py-bdist_wininst: 
	${CD} ${DIST_DIR}; ${PYTHON} setup.py ${BDIST_WININST}

dist-pypi-upload:
	${CD} ${DIST_DIR}; ${PYTHON} setup.py register sdist ${BDIST_WININST} upload

# CEBALERT: I seem to need these for this 'if' section to be seen by
# make - is that right?
RPM_RELEASE = 
UBUNTU_RELEASE =
LOG_TEXT =

# CEBALERT: applies to DEB and RPM; rename
ifeq (${DEBSTATUS},-unstable)
	RPM_RELEASE = r${SVNVERSION}
	UBUNTU_RELEASE = ${RELEASE}~r${SVNVERSION}-0ubuntu0
	LOG_TEXT = "  * Pre-release version ${RELEASE} from SVN; see Changelog.txt for details."
else
# If you want to re-release, need to increment the last digit to
# upload to launchpad. E.g. 0.9.7-0ubuntu0~lucid is first release of
# 0.9.7 on lucid, 0.9.7-0ubuntu1~lucid is second, and so
# on. Presumably there would usually be just one release.
# (Same applies to RPM.)
	RPM_RELEASE = 0 
	UBUNTU_RELEASE = ${RELEASE}-0ubuntu0
	LOG_TEXT = "  * Version ${RELEASE}; see Changelog.txt for details."
endif


# Or, remove --spec-only to build rpm on your system (but make sure
# you have python 2.6...I don't).
rpm:
	${CD} ${DIST_DIR}; ${PYTHON} setup.py bdist_rpm --release=${RPM_RELEASE} --requires "python,python-devel,tkinter,numpy,scipy,python-imaging-tk,python-matplotlib,python-matplotlib-tk,ipython" --group="Productivity/Scientific/Other"  --spec-only

# CEBALERTs about RPM: (1) can't seem to specify python 2.6! so only
# works where python 2.6 (or 2.5) is the default on a system. (2)
# where is gmpy on FC?


######################################################################
# Ubuntu packages
#
# (1)
# To create build environment:
#
# sudo apt-get install devscripts fakeroot cdbs dput pbuilder alien
# sudo pbuilder create
#
# ln -s doc/buildbot/dot-dput.cf ~/.dput.cf
#
# Set up GPG key, sign Launchpad code of conduct.
# gpg key agent to avoid password requests:
# sudo aptitude install gnupg-agent pinentry-gtk2 pinentry-curses
# export GPGKEY=whatever
# killall -q gpg-agent
# eval $(gpg-agent --daemon)
#
# See https://wiki.ubuntu.com/PackagingGuide/Complete for more info.
#
# (2)
# These commands must be run with no diffs, and having done "svn
# update" following any commits (so svnversion doesn't end in M or
# have a colon in it).
#
# (3)
# Make the debs, upload, etc. Buildbot's master.cfg is the reference
# for this.
#
# These commands can take a while to run. There's probably some 
# redundancy in the creation of the backports.

UBUNTU_ENV = env DEBFULLNAME='C. E. Ball' DEBEMAIL='ceball@gmail.com' GPGKEY=6C92B17B
DEBUILD = ${UBUNTU_ENV} debuild
UBUNTU_TARGET = natty
UBUNTU_BACKPORTS = lucid^ hardy^ 

UBUNTU_DIR = ${DIST_TMPDIR}/topographica-${UBUNTU_RELEASE}
UBUNTU_CHANGELOG = ${UBUNTU_DIR}/debian/changelog


deb: dist-setup.py
	cd ${DIST_TMPDIR}; cp topographica-${RELEASE}.tar.gz topographica_${UBUNTU_RELEASE}.orig.tar.gz
	cd ${DIST_TMPDIR}; mv topographica-${RELEASE} topographica-${UBUNTU_RELEASE}
	cp -R debian ${UBUNTU_DIR}/debian
	rm -rf ${UBUNTU_DIR}/debian/.svn
	echo "topographica (${UBUNTU_RELEASE}~${UBUNTU_TARGET}) ${UBUNTU_TARGET}; urgency=low" > ${UBUNTU_CHANGELOG}
	echo "" >> ${UBUNTU_CHANGELOG}
	echo ${LOG_TEXT} >> ${UBUNTU_CHANGELOG}
	echo "" >> ${UBUNTU_CHANGELOG}
	echo " -- C. E. Ball <ceball@gmail.com>  ${shell date -R}" >> ${UBUNTU_CHANGELOG}
	cd ${UBUNTU_DIR}; ${DEBUILD} -S -sa -uc -us
	cd ${DIST_TMPDIR}; ${UBUNTU_ENV} debsign *.changes  # CB: could move this line to deb-ppa, since signing only required for ppa
# CB: could put this line in to test the build locally
# sudo pbuilder build topographica_${UBUNTU_RELEASE}~${UBUNTU_TARGET}.dsc 

# You must first have run 'make deb'
deb-backports: ${subst ^,_DEB_BACKPORTS,${UBUNTU_BACKPORTS}}

%_DEB_BACKPORTS:
	cd ${UBUNTU_DIR}/debian; cp changelog ../../changelog.orig
	cd ${UBUNTU_DIR}/debian; cp control ../../control.orig;

# special case for hardy, which has only tk 8.4
	if [ "$*" = hardy ]; then \
		cd ${UBUNTU_DIR}/debian; sed -e 's/python-tk/python-tk, tk-tile/' ../../control.orig > control; \
	fi;

	cd ${UBUNTU_DIR}/debian; rm changelog*; cp ../../changelog.orig changelog	
	cd ${UBUNTU_DIR}; ${UBUNTU_ENV} debchange --force-bad-version --newversion "${UBUNTU_RELEASE}~$*" --force-distribution --distribution $* "Backport to $*."
	cd ${UBUNTU_DIR}; ${DEBUILD} 
	cd ${UBUNTU_DIR}; ${DEBUILD} -S -sa
# restore changes made for backports
	cd ${UBUNTU_DIR}/debian; cp ../../control.orig control
	cd ${UBUNTU_DIR}/debian; cp ../../changelog.orig changelog

# Requires that you have first run make deb, deb-backports
deb-ppa: ${subst ^,_DPUT,${UBUNTU_BACKPORTS} ${UBUNTU_TARGET}^}

%_DPUT:
	cd ${DIST_TMPDIR}; dput topographica${DEBSTATUS}-force-$* topographica_${UBUNTU_RELEASE}~$*_source.changes


## CEBALERT: need to clean up this section, and rpm is totally untested
#rpm-svn:
## Does it need sudo?
#	cd ${DIST_TMPDIR}; alien -r topographica_${UBUNTU_RELEASE}~${UBUNTU_TARGET}_all.deb

