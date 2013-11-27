# ALERT: Most of this file is outdated, and should be removed, 
# mainly leaving targets useful for making releases.  Most of 
# them should be called from the parent directory to this one,
# using "make -f platform/Makefile <target>".

PREFIX =  ${CURDIR}/
PYLINT = bin/pylint --rcfile=topo/tests/buildbot/pylintrc

PYCHECKER = bin/pychecker --config doc/buildbot/pycheckrc

GIT_DESCRIBE = $(shell git describe)
RELEASE = $(shell echo ${GIT_DESCRIBE} | cut -d- -f1 | cut -c2-)
GITVERSION = $(shell echo ${GIT_DESCRIBE} |  cut -d- -f2)

PYTHON = ${PREFIX}/bin/python

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



# By default, do nothing
default: 
	echo "The Makefile is primarily for package maintainers; see the Developers Manual for more info. It is not needed for building or using Topogrpahica."

all: default reference-manual doc

# CEBALERT: should be able to remove topo/tests/testsnapshot.typ,
# topo/tests/testplotfilesaver*.png
clean: clean-doc clean-ext-packages clean-compiled clean-coverage-output
	${RM} .??*~ *~ */*~ */.??*~ */*/*~ */*/.??*~ */*/*/*~ */*/*/.??*~ *.bak
	${RM} .#??*.* */.#??*.* */*/.#??*.* */*/*/.#??*.* current_profile ./topo/tests/testsnapshot.typ ./topo/tests/testplotfilesaver*.png
	${RM} -r bin include share lib man ImageSaver*.jpeg python_topo


uninstall:
	make -C external uninstall


FORCE:


ext-packages:
	make -C external

clean-ext-packages: 
	make -C external clean
	make -C external uninstall


# CB: experimental
topographicagui: 
	echo "import topo.tkgui;topo.tkgui.start(mainloop=False)" > _gui.py
	echo "${PREFIX}bin/idle -n -t 'Topographica shell' -r _gui.py" > topographicagui
	echo "" >> topographicagui
	chmod a+x ${PREFIX}topographicagui


# CEBALERT: need to update pychecker and work on its configuration if
# we're going to use it.
check:
	${PYCHECKER} external/param/*.py topo/*.py topo/*/*.py
# CEBALERT: way too much output to use.
lint:
	${PYLINT} topo external/param




clean-compiled: clean-weave clean-pyc

clean-weave:
	rm -rf ~/.python2*_compiled/ | cat

clean-pyc:
	rm -f *.pyc external/param/*.pyc external/paramtk/*.pyc topo/*.pyc topo/*/*.pyc topo/*/*/*.pyc examples/*.pyc models/*.pyc contrib/*.pyc

clean-doc:
	make -C doc clean

reference-manual: 
	make -C doc reference-manual

doc: FORCE
	make -C doc html 


# CEBALERT: Move into runtests.py
generate-map-tests-data:
	./topographica -c "cortex_density=8" models/lissom_oo_or.ty -c "topo.sim.run(100);from topo.tests.test_map_measurement import *; generate(plotgroups_to_test)" 

release-file:
	echo ${GIT_DESCRIBE} > topo/.release



#############################################################################



#############################################################################
##### coverage: intended for buildbot only

clean-coverage-output: clean-coverage-results clean-coverage-html

clean-coverage-results:
	${RM} -r .coverage*

# CBALERT: guess at output directory.
clean-coverage-html:
	${RM} -r ~/Documents/Topographica/tests/coverage_html

coverage-html:
	coverage combine 
	coverage html --rcfile=doc/buildbot/coveragerc -d ~/Documents/Topographica/tests/coverage_html
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

## Git-only code release, without making new binaries
## Run these from a relatively clean copy of the topographica directory 
## (without stray files, especially in doc/).

# Update any files that keep track of the version number
new-version: FORCE
	mv setup.py setup.py~
	sed -e "s/version=.*,/version='${RELEASE}',/g" setup.py~ > setup.py

TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica

# Update Topographica.org web site
sf-web-site: reference-manual doc
	rsync -v -arHz --rsh=ssh doc/. web.sf.net:/home/groups/t/to/topographica/htdocs/.


EXAMPLES_TO_KEEP_IN_DIST= ^gcal.ty ^hierarchical.ty ^lissom_audio.ty ^perrinet_retina.ty ^ptztracker.ty ^saccade_demo.ty ^som_retinotopy.ty ^tiny.ty 
MODELS_TO_KEEP_IN_DIST= ^goodhill_network90.ty ^leaky_lissom_or.ty ^lissom.ty ^lissom_fsa.ty ^lissom_oo_or.ty ^lissom_oo_or_cr.ty ^lissom_or.ty ^lissom_or_movie.ty ^lissom_whisker_barrels.ty ^obermayer_pnas90.ty ^sullivan_neurocomputing04.ty 


# Clear out everything not intended for the public distribution
#
# This is ordinarily commented out in the SVN version for safety, 
# but it is enabled when the distribution directory is created.
#
#@@distclean: FORCE clean
#@@	   ${RM} .#* */.#* */*/.#* */*~ 
#@@	   ${RM} README.rst ; ${CP} platform/distutils/README.setup.txt README.txt
#@@	   ${RM} etc/topographica.elc ImageSaver*.ppm countalerts* annotate.out emacslog
#@@	   ${RM} current_profile script timing*
#@@	   ${RM} examples/*.typ models/*.typ
#@@	   ${RM} -r Output
#@@	   -mv images/ellen_arthur.pgm ./TMPellen_arthur.pgm
#@@	   ${RM} -r images sounds
#@@	   ${RM} -r info
#@@	   mkdir images; mv ./TMPellen_arthur.pgm images/ellen_arthur.pgm
#@@	   ${RM} -r tmp/
#@@	   ${RM} -r contrib/
#@@	   ${RM} -r .svn */.svn */*/.svn */*/*/.svn */*/*/*/.svn
#@@	   ${RM} -r .git* */.git* */*/.git* */*/*/.git* */*/*/*/.git*
#@@	   ${CD} topo/tests/reference ; make clean
#@@	   ${RM} -r doc/buildbot/
#@@	   ${RM} -r platform/debian/
#@@	   ${RM} -r external/
#@@	   ${RM} -r doc/bib*.blg doc/bib*.bbl doc/bib*.aux
#@@	   find examples/*.ty -maxdepth 1 ${subst ^,! -name ,${EXAMPLES_TO_KEEP_IN_DIST}} -exec rm {} \;
#@@	   find models/*.ty -maxdepth 1 ${subst ^,! -name ,${MODELS_TO_KEEP_IN_DIST}} -exec rm {} \;


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
dist: doc distdir FORCE
	${CD} ${DIST_DIR}; ${MAKE} distarc


# Note that the output needs to be appended to a copy of the old file,
# to keep old fixes to formatting. The HEAD:XXXXX can be omitted to get
# the full list, but this is faster.
ChangeLog.txt: FORCE
	make -C external svn2cl
	external/svn2cl -r HEAD:12000 --include-rev --group-by-day --separate-daylogs --break-before-msg --stdout https://topographica.svn.sourceforge.net/svnroot/topographica/ | sed -e 's|/trunk/topographica/||g' > ChangeLog.txt


######################################################################
# Create "pysource", the basis for "python setup.py" distributions

dist-pysource: doc distdir reference-manual
	${CD} ${DIST_DIR}; make distclean
	${CD} ${DIST_DIR}; ${CP} platform/distutils/README.setup.txt README.txt
	${CD} ${DIST_DIR}; ${CP} platform/distutils/setup.py setup.py
	${CD} ${DIST_DIR}; ${CP} platform/distutils/MANIFEST.in MANIFEST.in
# won't need to build this copy
	${RM} ${DIST_DIR}/Makefile 
	${RM} -r ${DIST_DIR}/external
# create tar.gz  # CEBALERT: can I delete this?
	${CD} ${DIST_TMPDIR} ; ${MAKE_ARCHIVE} ${DIST_DIRNAME} | ${COMPRESS_ARCHIVE} > ${DIST_ARCHIVE}


######################################################################
# Public "setup.py"-type distributions
#
# These commands assume you have run "make dist-pysource".
# (Archives don't include doc/ because of its size.)

# CEB: bdist_msi supports silent install, but seems to be missing other options!
BDIST_WIN_CMD = bdist_wininst
# Note: no path to install-script, just name
BDIST_WININST = ${BDIST_WIN_CMD} --user-access-control auto --install-script windows_postinstall.py --plat-name=win

dist-pysource-sdist: 
	${CD} ${DIST_DIR}; ${PYTHON} setup.py sdist

# generate windows exe (like the exe you get for numpy or matplotlib)
dist-pysource-bdist_wininst: 
	${CD} ${DIST_DIR}; ${PYTHON} setup.py ${BDIST_WININST}

# CEB: should probably upload to pypi manually, if we're going to do it at all
## put dist onto pypi
#dist-pypi-upload:
#	${CD} ${DIST_DIR}; ${PYTHON} setup.py register sdist ${BDIST_WININST} upload

# CEBALERT: I seem to need these for this 'if' section to be seen by
# make - is that right?
RPM_RELEASE = 
UBUNTU_RELEASE =
LOG_TEXT =

# CEBALERT: applies to DEB and RPM; rename
ifeq (${DEBSTATUS},-unstable)
	RPM_RELEASE = r${GITVERSION}
	UBUNTU_RELEASE = ${RELEASE}~r${GITVERSION}-0ubuntu0
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


# remove --source-only to try building rpm on your system
rpm:
	${CD} ${DIST_DIR}; ${PYTHON} setup.py bdist_rpm --release=${RPM_RELEASE} --requires "python,python-devel,tkinter,numpy,scipy,python-imaging-tk,python-matplotlib,python-matplotlib-tk,ipython" --group="Productivity/Scientific/Other" --source-only

# CEBALERTs about RPM: (1) can't seem to specify python 2.5+! So only
# works where python 2.5+ is the default on a system. (2) where is
# gmpy on FC?


######################################################################
# Ubuntu packages
#
# (1)
# To create build environment:
#
# sudo apt-get install devscripts fakeroot cdbs dput pbuilder alien
# sudo pbuilder create
#
# --- optional, currently unused steps for launchpad
# ln -s doc/buildbot/dot-dput.cf ~/.dput.cf
#
# Set up GPG key, sign Launchpad code of conduct.
# gpg key agent to avoid password requests:
# sudo aptitude install gnupg-agent pinentry-gtk2 pinentry-curses
# export GPGKEY=whatever
# killall -q gpg-agent
# eval $(gpg-agent --daemon)
# ---
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
DEBUILD = ${UBUNTU_ENV} debuild -S -sa -uc -us 
UBUNTU_TARGET = oneiric
UBUNTU_BACKPORTS = lucid^ maverick^ natty^ 

UBUNTU_DIR = ${DIST_TMPDIR}/topographica-${UBUNTU_RELEASE}
UBUNTU_CHANGELOG = ${UBUNTU_DIR}/debian/changelog

# You must first have run make dist-pysource. (Not a dependency
# because buildbot runs these targets separately.)
deb:
	cd ${DIST_TMPDIR}; cp topographica-${RELEASE}.tar.gz topographica_${UBUNTU_RELEASE}.orig.tar.gz
	cd ${DIST_TMPDIR}; mv topographica-${RELEASE} topographica-${UBUNTU_RELEASE}
	cp -R platform/debian ${UBUNTU_DIR}/debian
	rm -rf ${UBUNTU_DIR}/debian/.svn
	echo "topographica (${UBUNTU_RELEASE}~${UBUNTU_TARGET}) ${UBUNTU_TARGET}; urgency=low" > ${UBUNTU_CHANGELOG}
	echo "" >> ${UBUNTU_CHANGELOG}
	echo ${LOG_TEXT} >> ${UBUNTU_CHANGELOG}
	echo "" >> ${UBUNTU_CHANGELOG}
	echo " -- C. E. Ball <ceball@gmail.com>  ${shell date -R}" >> ${UBUNTU_CHANGELOG}
	cd ${UBUNTU_DIR}; ${DEBUILD}
# CEBALERT: I never got signing to work without interaction in buildbot
#	cd ${DIST_TMPDIR}; ${UBUNTU_ENV} debsign *.changes  # CB: could move this line to deb-ppa, since signing only required for ppa
# CB: could put something like this line in to test the build locally
# sudo pbuilder build topographica_${UBUNTU_RELEASE}~${UBUNTU_TARGET}.dsc 

# You must first have run 'make deb'.
deb-backports: ${subst ^,_DEB_BACKPORTS,${UBUNTU_BACKPORTS}}

%_DEB_BACKPORTS:
	cd ${UBUNTU_DIR}/debian; cp changelog ../../changelog.orig
	cd ${UBUNTU_DIR}/debian; cp control ../../control.orig;
	cd ${UBUNTU_DIR}/debian; rm changelog*; cp ../../changelog.orig changelog	
	cd ${UBUNTU_DIR}; ${UBUNTU_ENV} debchange --force-bad-version --newversion "${UBUNTU_RELEASE}~$*" --force-distribution --distribution $* "Backport to $*."
	cd ${UBUNTU_DIR}; ${DEBUILD}
# revert changes made for backports
	cd ${UBUNTU_DIR}/debian; cp ../../changelog.orig changelog

# Requires that you have first run make deb, deb-backports
deb-ppa: ${subst ^,_DPUT,${UBUNTU_BACKPORTS} ${UBUNTU_TARGET}^}

%_DPUT:
	cd ${DIST_TMPDIR}; dput topographica${DEBSTATUS}-force-$* topographica_${UBUNTU_RELEASE}~$*_source.changes


## CEBALERT: need to clean up this section, and rpm is totally untested
#rpm-svn:
## Does it need sudo?
#	cd ${DIST_TMPDIR}; alien -r topographica_${UBUNTU_RELEASE}~${UBUNTU_TARGET}_all.deb

