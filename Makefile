# $Id$
PREFIX =  ${CURDIR}/
PYLINT = bin/pylint --rcfile=doc/buildbot/pylintrc
PYFLAKES = bin/pyflakes

PYCHECKER = bin/pychecker --config doc/buildbot/pycheckrc

RELEASE = 0.9.7

TEST_VERBOSITY = 1

# currently only applied to train-tests 
IMPORT_WEAVE = 1

# no. of decimal places to require for verifying a match in slow-tests
# (must match across platforms & for optimized vs unoptimized)
TESTDP = 7

# see topographica-other-python target
OTHER_PYTHON = /usr/bin/env python

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
	SVNVERSION = ${shell git svn info | grep -e "^Revision.*[0-9]*" | grep -o -e "[0-9]*"}:${shell git rev-parse HEAD}
endif


# if 0, skips building tk and related external packages
GUI = 1

# set to empty when building 'release' debs.
DEBSTATUS = -unstable


# COVERAGE_CMD: used by buildbot to generate various coverage data
COVERAGE = 0
COVERAGE_CMD = 

ifeq ("${COVERAGE}","1")
	COVERAGE_CMD = bin/coverage run --rcfile=doc/buildbot/coveragerc -a -p
endif

# CEBALERT: tied to exact windows version!
ifeq ("$(shell uname -s)","MINGW32_NT-5.1")
	TIMER = 
else
	TIMER = time 
endif

XVFB = ${shell which xvfb-run}
ifeq ("${XVFB}","")
	XVFBRUN = @echo "Warning: xvfb-run not found; any GUI components that are run will display windows";
else
	XVFBRUN = ${XVFB} -a
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


# Coverage targets are used by buildbot
clean-coverage-output: clean-coverage-results clean-coverage-html

clean-coverage-results:
	${RM} -r .coverage*

# CBALERT: guess at output directory. Needs to be cleaned up (see ALERT by speed-tests)
clean-coverage-html:
	${RM} -r ~/topographica/tests/coverage_html

coverage-html:
	bin/coverage combine 
	bin/coverage html --rcfile=doc/buildbot/coveragerc -d ~/topographica/tests/coverage_html


uninstall:
	make -C external uninstall


saved-examples: 
	make -C examples saved-examples


FORCE:

# To get more information about which tests are being run, do:
# make TEST_VERBOSITY=2 tests
tests: FORCE
	${XVFBRUN} ${COVERAGE_CMD} ./topographica -c "import topo.tests; t=topo.tests.run(verbosity=${TEST_VERBOSITY}); import sys; sys.exit(len(t.failures+t.errors))"

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
	${PREFIX}/bin/python ${PREFIX}/create_topographica_script.py ${PREFIX}bin/python ${RELEASE} ${SVNVERSION} 0


topographica-other-python:
	${OTHER_PYTHON} ${PREFIX}/create_topographica_script.py "${OTHER_PYTHON}" ${RELEASE} ${SVNVERSION} 1


# CB: experimental
topographicagui: 
	echo "import topo.tkgui;topo.tkgui.start(mainloop=False)" > _gui.py
	echo "${PREFIX}bin/idle -n -t 'Topographica shell' -r _gui.py" > topographicagui
	echo "" >> topographicagui
	chmod a+x ${PREFIX}topographicagui


check:
	${PYCHECKER} topo/*.py topo/*/*.py

check-base:
	${PYCHECKER} topo/base/*.py 

# CEBALERT: should add param, but apparently doesn't work. Update pylint?
lint:
	${PYLINT} topo

lint-base:
	${PYLINT} topo.base | cat

pyflakes:
	${PYFLAKES} topo param | grep -v topo/tests

pyflakes-base:
	${PYFLAKES} topo/base | cat


# Compare topographica and C++ lissom output
or_comparisons:
	./topographica -c "from topo.tests.test_script import run_multiple_density_comparisons;nerr=run_multiple_density_comparisons('lissom_or_reference.ty'); import sys;sys.exit(nerr)"

oo_or_comparisons:
	./topographica -c "from topo.tests.test_script import run_multiple_density_comparisons;nerr=run_multiple_density_comparisons('lissom_oo_or_reference.ty'); import sys;sys.exit(nerr)"


# Test that the specified scripts haven't changed in results or speed.
#SCRIPTS=^lissom_oo_or.ty ^som_retinotopy.ty
SCRIPTS= ^hierarchical.ty ^lissom_or.ty ^lissom_oo_or.ty ^som_retinotopy.ty ^sullivan_neurocomputing04.ty ^lissom.ty ^lissom_fsa.ty ^gcal.ty #^lissom_whisker_barrels.ty
# CEB: tests on these scripts temporarily suspended (SF.net #2053538)
# ^lissom_oo_or_homeostatic.ty ^lissom_oo_or_homeostatic_tracked.ty
# ^lissom_or_noshrinking.ty  - only matches to 4 dp with IMPORT_WEAVE=0 

TRAINSCRIPTS=${SCRIPTS}
TRAINDATA =${subst ^,topo/tests/,${subst .ty,.ty_DATA,${TRAINSCRIPTS}}}
TRAINTESTS=${subst ^,topo/tests/,${subst .ty,.ty_TEST,${TRAINSCRIPTS}}}

# While training data is usually checked into topo/tests and is the
# same for all machines, speed data is generated by the machine
# running this makefile. Therefore, speed data is stored in a
# machine-specific directory.

# CEBALERT: should move logic about whether or not new data needs to
# be generated into topo/tests/test_script.py; that way, won't need
# this complex scheme in the Makefile, and won't need to guess at what
# the default output directory is (~/topographica).
SPEEDSCRIPTS=${SCRIPTS}
SPEEDDATA =${subst ^,~/topographica/tests/$(shell hostname)/,${subst .ty,.ty_SPEEDDATA,${SPEEDSCRIPTS}}}
SPEEDTESTS=${subst ^,~/topographica/tests/$(shell hostname)/,${subst .ty,.ty_SPEEDTEST,${SPEEDSCRIPTS}}}

STARTUPSPEEDSCRIPTS= ^lissom_oo_or.ty ^lissom_or.ty  
STARTUPSPEEDDATA =${subst ^,~/topographica/tests/$(shell hostname)/,${subst .ty,.ty_STARTUPSPEEDDATA,${STARTUPSPEEDSCRIPTS}}}
STARTUPSPEEDTESTS=${subst ^,~/topographica/tests/$(shell hostname)/,${subst .ty,.ty_STARTUPSPEEDTEST,${STARTUPSPEEDSCRIPTS}}}


# CB: when changing the various targets, don't forget about buildbot. 

train-tests: ${TRAINTESTS}
speed-tests: ${SPEEDTESTS}
startup-speed-tests: ${STARTUPSPEEDTESTS}

all-speed-tests: speed-tests startup-speed-tests

snapshot-compatibility-tests: 
	./topographica -c "from topo.command.basic import load_snapshot; load_snapshot('topo/tests/lissom_oo_or_od_dr_cr_dy_sf_000010.00.typ')" -c "topo.sim.run(1)"


# Test that simulations give the same results whether run straight
# through or run part way, saved, reloaded, and run on to the same
# point.
simulation-snapshot-tests:
	${COVERAGE_CMD} ./topographica -c 'from topo.tests.test_script import compare_with_and_without_snapshot_NoSnapshot as A; A()'
	${COVERAGE_CMD} ./topographica -c 'from topo.tests.test_script import compare_with_and_without_snapshot_CreateSnapshot as B; B()'
	${COVERAGE_CMD} ./topographica -c 'from topo.tests.test_script import compare_with_and_without_snapshot_LoadSnapshot as C; C()'
	rm -f examples/lissom_oo_or.ty_PICKLETEST*

pickle-all-classes:
	${COVERAGE_CMD} ./topographica -c 'from topo.tests.test_script import pickle_unpickle_everything; errs = pickle_unpickle_everything(); import sys; sys.exit(errs)'

snapshot-tests: simulation-snapshot-tests snapshot-compatibility-tests script-repr-tests pickle-all-classes

print-info:
	@echo Running at ${shell date +%s}
	@echo svnversion ${SVNVERSION}

batch-tests:
	./topographica -c "from topo.tests.test_script import test_runbatch; test_runbatch()"

# CB: snapshot-tests is not part of slow-tests for the moment
# (until slow-tests split up on buildbot).
slow-tests: print-info train-tests all-speed-tests map-tests batch-tests
#snapshot-tests 

# CB: add notes somewhere about...
# - making sure weave compilation has already occurred before running speed tests
# - when to delete data files (i.e. when to generate new data)

# General rules for generating test data and running the tests
%_DATA:
	./topographica -c 'from topo.tests.test_script import generate_data; generate_data(script="examples/${notdir $*}",data_filename="tests/${notdir $*}_DATA",run_for=[1,99,150],look_at="V1",cortex_density=8,retina_density=24,lgn_density=24)'

%_TEST: %_DATA
	${TIMER}${COVERAGE_CMD} ./topographica -c 'import_weave=${IMPORT_WEAVE}' -c 'from topo.tests.test_script import TestScript; TestScript(script="examples/${notdir $*}",data_filename="tests/${notdir $*}_DATA",decimal=${TESTDP})'
# CB: Beyond 14 dp, the results of the current tests do not match on
# ppc64 and i686 (using linux).  In the future, decimal=14 might have
# to be reduced (if the tests change, or to accommodate other
# processors/platforms).

v_lissom:
	make -C topo/tests/reference/	
	${TIMER}./topographica -c "profiling=True;iterations=20000" topo/tests/reference/lissom_oo_or_reference.ty


%_SPEEDDATA:
	${TIMER}./topographica -c 'from topo.tests.test_script import generate_speed_data; generate_speed_data(script="examples/${notdir $*}",iterations=250,data_filename="tests/$(shell hostname)/${notdir $*}_SPEEDDATA")'

%_SPEEDTEST: %_SPEEDDATA
	${TIMER}./topographica -c 'from topo.tests.test_script import compare_speed_data; compare_speed_data(script="examples/${notdir $*}",data_filename="tests/$(shell hostname)/${notdir $*}_SPEEDDATA")'


%_STARTUPSPEEDDATA:
	${TIMER}./topographica -c 'from topo.tests.test_script import generate_startup_speed_data; generate_startup_speed_data(script="examples/${notdir $*}",density=48,data_filename="tests/$(shell hostname)/${notdir $*}_STARTUPSPEEDDATA")'

%_STARTUPSPEEDTEST: %_STARTUPSPEEDDATA
	${TIMER}./topographica -c 'from topo.tests.test_script import compare_startup_speed_data; compare_startup_speed_data(script="examples/${notdir $*}",data_filename="tests/$(shell hostname)/${notdir $*}_STARTUPSPEEDDATA")'

.SECONDARY: ${SPEEDDATA} ${TRAINDATA} ${STARTUPSPEEDDATA} # Make sure that *_*DATA is kept around


# Special versions for specific scripts:
topo/tests/lissom.ty_DATA:
	./topographica -c 'from topo.tests.test_script import generate_data; generate_data(script="examples/lissom.ty",data_filename="tests/lissom.ty_DATA",run_for=[1,99,150],look_at="V1",cortex_density=8,retina_density=6,lgn_density=6,dims=["or","od","dr","dy","cr","sf"])'

topo/tests/lissom.ty_SPEEDDATA:
	./topographica -c 'from topo.tests.test_script import generate_speed_data; generate_speed_data(script="examples/lissom.ty",data_filename="tests/$(shell hostname)/lissom.ty_SPEEDDATA",iterations=250,cortex_density=8,retina_density=6,lgn_density=6,dims=["or","od","dr","dy","cr","sf"])'

topo/tests/lissom_fsa.ty_DATA:
	./topographica -c 'from topo.tests.test_script import generate_data; generate_data(script="examples/lissom_fsa.ty",data_filename="tests/lissom_fsa.ty_DATA",run_for=[1,99,150],look_at="FSA",cortex_density=8,retina_density=24,lgn_density=24)'

topo/tests/lissom_whisker_barrels.ty_DATA:
	./topographica -c 'from topo.tests.test_script import generate_data; generate_data(script="examples/lissom_whisker_barrels.ty",data_filename="tests/lissom_whisker_barrels.ty_DATA",run_for=[1,99,150],look_at="S1")'


# CEBALERT: should use lissom.ty and test more map types
# pass a list of plotgroup names to test() instead of plotgroups_to_test to restrict the tests
map-tests:
	${COVERAGE_CMD} ./topographica -c "cortex_density=8" examples/lissom_oo_or.ty -c "topo.sim.run(100);from topo.tests.test_map_measurement import *; test(plotgroups_to_test)" 

generate-map-tests-data:
	./topographica -c "cortex_density=8" examples/lissom_oo_or.ty -c "topo.sim.run(100);from topo.tests.test_map_measurement import *; generate(plotgroups_to_test)" 

TESTTMPDIR := $(shell mktemp -d /tmp/topotests.XXXX)
script-repr-tests:
	${COVERAGE_CMD} ./topographica examples/hierarchical.ty -a -c "import param;param.normalize_path.prefix='${TESTTMPDIR}'" -c "save_script_repr('script_repr_test.ty')"
	${COVERAGE_CMD} ./topographica ${TESTTMPDIR}/script_repr_test.ty
	rm -rf ${TESTTMPDIR}

gui-tests: basic-gui-tests detailed-gui-tests

basic-gui-tests:
	${XVFBRUN} ${COVERAGE_CMD} ./topographica -g -c "from topo.tests.gui_tests import run_basic; nerr=run_basic();topo.guimain.quit_topographica(check=False,exit_status=nerr)"

detailed-gui-tests:
	${XVFBRUN} ${COVERAGE_CMD} ./topographica -g -c "from topo.tests.gui_tests import run_detailed; nerr=run_detailed(); topo.guimain.quit_topographica(check=False,exit_status=nerr)"


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
#@@	   ${RM} current_profile ./topo/tests/testsnapshot.typ script ./topo/tests/*.ty_*DATA timing* ./topo/tests/testplotfilesaver*.png
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
	${CD} ${DIST_DIR}; ${PREFIX}/bin/python create_topographica_script.py None ${RELEASE} ${SVNVERSION} 1
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
	${CD} ${DIST_DIR}; ${PREFIX}/bin/python setup.py sdist

# generate windows exe (like the exe you get for numpy or matplotlib)
dist-setup.py-bdist_wininst: 
	${CD} ${DIST_DIR}; ${PREFIX}/bin/python setup.py ${BDIST_WININST}

dist-pypi-upload:
	${CD} ${DIST_DIR}; ${PREFIX}/bin/python setup.py register sdist ${BDIST_WININST} upload

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
	${CD} ${DIST_DIR}; ${PREFIX}/bin/python setup.py bdist_rpm --release=${RPM_RELEASE} --requires "python,python-devel,tkinter,numpy,scipy,python-imaging-tk,python-matplotlib,python-matplotlib-tk,ipython" --group="Productivity/Scientific/Other"  --spec-only

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

UBUNTU_ENV = env DEBFULLNAME='C. E. Ball' DEBEMAIL='ceball@gmail.com' GPGKEY=4275E3C7
DEBUILD = ${UBUNTU_ENV} debuild
UBUNTU_TARGET = lucid
UBUNTU_BACKPORTS = karmic^ jaunty^ hardy^ 

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
	cd ${UBUNTU_DIR}; ${DEBUILD} 
	cd ${UBUNTU_DIR}; ${DEBUILD} -S -sa
# CEBALERT: should put this line in to test the build
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

