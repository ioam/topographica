"""
Commands that were in the Makefile for running various tests. Roughly
converted to a Python script so we can run on all platforms. Work in
progress.

Check README and buildbot to see how to run the tests, but here are some examples:

default set:
./topographica topo/tests/runtests.py

all:
./topographica -p 'targets=["all"]' topo/tests/runtests.py
"""

# CEBALERT: need to fix the issue with global_params reporting name=X
# is unused.


# Comments from the Makefile that I haven't processed yet:
#
# (1)
# CB: Beyond 14 dp, the results of the current tests do not match on
# ppc64 and i686 (using linux).  In the future, decimal=14 might have
# to be reduced (if the tests change, or to accommodate other
# processors/platforms).
#


import glob
import os
import sys
import tempfile
import commands

import param
from topo.misc.commandline import global_params as p

p.add(
    targets = param.List(default=[],doc="Leave empty for default set, ['all'] for all tests except speedtests, ['speed'] for speed tests, or else list the targets required."),

    timing = param.Boolean(default=False),

    testdp = param.Number(default=6),

    testdp_unopt = param.Number(default=5)

    )

if p.timing:
    timing_cmd = "/usr/bin/time"
else:
    timing_cmd = ""


# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return ""

xvfb = which('xvfb-run')
if not xvfb:
    print "xvfb-run not found; any GUI components that are run will display windows"
else:
    xvfb = xvfb + " -a"

if len(p.targets)==0:
    # DEFAULT
    p.targets = ['traintests','snapshots','gui','maptests'] # maptests wouldn't be default except it's caught platform different problems before (there aren't enough unit tests!)

# Allow allsnapshottests as shortcut for snapshots and pickle.
# CEBALERT: should just combine these tests anyway.
if "allsnapshottests" in p.targets:
    index = p.targets.index("allsnapshottests")
    p.targets[index] = "snapshots"
    p.targets.insert(index,"pickle")

# ->params ?
tests_dir = param.resolve_path("topo/tests",path_to_file=False)
scripts_dir = param.resolve_path(".",path_to_file=False) ### XXX
topographica_script = xvfb + " " + timing_cmd + " " + sys.argv[0] + " " +  " "

def _runc(cmd):
    print cmd
    return os.system(cmd)


import topo.misc.keyedlist
target = topo.misc.keyedlist.KeyedList()
speedtarget = topo.misc.keyedlist.KeyedList()


# CEBALERT: need to pick which scripts to include for traintests and
# speedtests and startupspeedtests (see test_script.py).
#
# From the Makefile:
# SCRIPTS= ^hierarchical.ty ^lissom_or.ty ^lissom_oo_or.ty ^som_retinotopy.ty ^sullivan_neurocomputing04.ty ^lissom.ty ^lissom_fsa.ty ^gcal.ty ^lissom_whisker_barrels.ty
# CEB: tests on these scripts temporarily suspended (SF.net #2053538)
# ^lissom_oo_or_homeostatic.ty ^lissom_oo_or_homeostatic_tracked.ty
# ^lissom_or_noshrinking.ty  - only matches to 4 dp with IMPORT_WEAVE=0
# Now I'm using this list for train-tests:

# CEBALERT: this list should be defined in one place.
#from setup import TRAINSCRIPTS
TRAINSCRIPTS = [
    "examples/hierarchical.ty",
    "models/lissom_or.ty",
    "models/lissom_oo_or.ty",
    "examples/som_retinotopy.ty",
    "models/sullivan_neurocomputing04.ty",
    "models/lissom.ty",
#    "models/lissom_fsa.ty",  # CEBALERT: disabled for now (needs special case - look_at=fsa not v1, see below)
    "examples/gcal.ty"
    ]


# (and a different list for speedtests - see test_script.py).
#
# Also: special cases from the Makefile to consider restoring:
#
##topo/tests/lissom.ty_DATA:
##	./topographica -c 'from topo.tests.test_script import generate_data; generate_data(script="examples/lissom.ty",data_filename="tests/lissom.ty_DATA",run_for=[1,99,150],look_at="V1",cortex_density=8,retina_density=6,lgn_density=6,dims=["or","od","dr","dy","cr","sf"])'
##
##topo/tests/lissom_fsa.ty_DATA:
##	./topographica -c 'from topo.tests.test_script import generate_data; generate_data(script="examples/lissom_fsa.ty",data_filename="tests/lissom_fsa.ty_DATA",run_for=[1,99,150],look_at="FSA",cortex_density=8,retina_density=24,lgn_density=24)'
##
##topo/tests/lissom_whisker_barrels.ty_DATA:
##	./topographica -c 'from topo.tests.test_script import generate_data; generate_data(script="examples/lissom_whisker_barrels.ty",data_filename="tests/lissom_whisker_barrels.ty_DATA",run_for=[1,99,150],look_at="S1")'



target['traintests'] = []
for script in TRAINSCRIPTS:
    script_path = os.path.join(scripts_dir,script)
    target['traintests'].append(topographica_script +  ''' -c "from topo.tests.test_script import test_script; test_script(script=%(script_path)s,decimal=%(dp)s)"'''%dict(script_path=repr(script_path),dp=p.testdp))

# CEBALERT: should use the code above but just with the changes for running without weave.
target['unopttraintests'] = []
for script in TRAINSCRIPTS:
    script_path = os.path.join(scripts_dir,script)
    target['unopttraintests'].append(topographica_script + " -c \"import_weave=False\"" +  " -c \"from topo.tests.test_script import test_script; test_script(script=%(script_path)s,decimal=%(dp)s)\""%dict(script_path=repr(script_path),dp=p.testdp_unopt))


speedtarget['speedtests'] = []
SPEEDSCRIPTS = TRAINSCRIPTS
SPEEDSCRIPTS.remove("examples/hierarchical.ty") # CEBALERT: remove problematic example (doesn't work for some densities)
for script in SPEEDSCRIPTS:
    script_path = os.path.join(scripts_dir,script)
    speedtarget['speedtests'].append(topographica_script +  ''' -c "from topo.tests.test_script import compare_speed_data;compare_speed_data(script=%(script_path)s)"'''%dict(script_path=repr(script_path)))


STARTUPSPEEDSCRIPTS = ["models/lissom.ty","examples/gcal.ty"]

speedtarget['startupspeedtests'] = []
for script in STARTUPSPEEDSCRIPTS:
    script_path = os.path.join(scripts_dir,script)
    speedtarget['startupspeedtests'].append(topographica_script +  ''' -c "from topo.tests.test_script import compare_startup_speed_data;compare_startup_speed_data(script=%(script_path)s)"'''%dict(script_path=repr(script_path)))



##### snapshot-tests
target['snapshots'] = []

# snapshot-compatibility-tests:
#snapshot_path = os.path.join(tests_dir,"lissom_oo_or_od_dr_cr_dy_sf_000010.00.typ")
#target['snapshots'].append(topographica_script + ''' -c "from topo.command import load_snapshot; load_snapshot(%(snapshot_path)s)" -c #"topo.sim.run(1)"'''%dict(snapshot_path=repr(snapshot_path)))


# Test that simulations give the same results whether run straight
# through or run part way, saved, reloaded, and run on to the same
# point.
# simulation-snapshot-tests:
target['snapshots'].append(topographica_script + ''' -c "from topo.tests.test_script import compare_with_and_without_snapshot_NoSnapshot as A; A()"''')

target['snapshots'].append(topographica_script + ''' -c "from topo.tests.test_script import compare_with_and_without_snapshot_CreateSnapshot as B; B()"''')

target['snapshots'].append(topographica_script + ''' -c "from topo.tests.test_script import compare_with_and_without_snapshot_LoadSnapshot as C; C()"''')

# CEBALERT: remove ~/topographica/*PICKLETEST* ?


target['pickle'] = []
# pickle-all-classes:
target['pickle'].append(topographica_script + ''' -c "from topo.tests.test_script import pickle_unpickle_everything; errs = pickle_unpickle_everything(); import sys; sys.exit(errs)"''')

# unpickle-compatibility-tests:
pickle_path = os.path.join(tests_dir,"instances-r11275.pickle")
target['pickle'].append(topographica_script + '''-l -c "from topo.tests.test_script import pickle_unpickle_everything; errs = pickle_unpickle_everything(existing_pickles=%(pickle_path)s); import sys; sys.exit(errs)"'''%dict(pickle_path=repr(pickle_path)))


# CEBALERT: hack that this will always be created even when test not being run
# DSALERT: also it's not portable; python has a tempfile module that should
# easily be able to replace this

temp_dir = ""
if "scriptrepr" in p.targets or "all" in p.targets:
    from tempfile import mkdtemp
    temp_dir = mkdtemp()
    temp_dir = temp_dir.replace("\\", "\\\\")

#script-repr-tests:
target['scriptrepr']=[]
script = os.path.join(scripts_dir,"examples/hierarchical.ty")
target['scriptrepr'].append(topographica_script + " %(script)s -a -c \"import param;param.normalize_path.prefix='%(temp_dir)s'\" -c \"save_script_repr('script_repr_test.ty')\""%dict(temp_dir=temp_dir,script=script))

script_repr_test_path = os.path.join(temp_dir,"script_repr_test.ty")
target['scriptrepr'].append(topographica_script + " " + script_repr_test_path)
target['scriptrepr'].append(topographica_script + "-c \"import shutil;shutil.rmtree('%s')\""%temp_dir)


### GUI tests
target['gui'] = []
# basic-gui-tests:
target['gui'].append(topographica_script + ' -g -c "from topo.tests.gui_tests import run_basic; nerr=run_basic();topo.guimain.quit_topographica(check=False,exit_status=nerr)"')

# detailed-gui-tests:
target['gui'].append(topographica_script + ' -g -c "from topo.tests.gui_tests import run_detailed; nerr=run_detailed(); topo.guimain.quit_topographica(check=False,exit_status=nerr)"')


target['batch'] = []
target['batch'].append(topographica_script + ' -c "from topo.tests.test_script import test_runbatch; test_runbatch()"')


# CEBALERT: should use lissom.ty and test more map types
# pass a list of plotgroup names to test() instead of plotgroups_to_test to restrict the tests
target['maptests'] = []
script = os.path.join(scripts_dir,"models/lissom_oo_or.ty")
target['maptests'].append(topographica_script + ' -c "cortex_density=8" %s -c "topo.sim.run(100);from topo.tests.test_map_measurement import *; test(plotgroups_to_test)"'%script)


def start():
    errors = []

    print "Running: %s"%p.targets
    print

    # CEBALERT: rename one of target or targets!

    if p.targets==['all']:
        targets = target.keys()
    elif p.targets==['speed']:
        targets = speedtarget.keys()
    else:
        targets = p.targets

    target.update(speedtarget)

    for name in targets:
        print "*** " + name
        for cmd in target[name]:
            if _runc(cmd) > 0:
                if name not in errors:
                    errors.append(name)

    print
    print "="*60
    print
    print "runtests.start(): targets with errors: %s"%len(errors)
    if len(errors)>0:
        print errors
        sys.exit(1)
    else:
        sys.exit(0)



if __name__=="__main__":
    start()

