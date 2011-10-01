"""
Commands that were in the Makefile for running various tests. Roughly
converted to a Python script so we can run on all platforms. Work in
progress.

Ideally, the 'unit' target (i.e. unit tests) would be all that people
need to run. Developers, for checking they haven't messed obvious
stuff up. Users, for checking a Topographica installation functions ok
on their system. The other, slower targets would only need to be run
by buildbot (on behalf of everyone).

Unfortunately, the unit tests do not currently cover enough! It's an
important project to improve them.
"""

# CEBALERT: need to fix the issue with global_params reporting name=X
# is unused.

# CEBALERT: get /usr/bin/time in here if possible.

import glob
import os
import sys
import tempfile
import commands

import param
from topo.misc.commandline import global_params as p

p.add(
    targets = param.List(default=[]),

    extra_args = param.String(default=""),

    coverage = param.Boolean(default=False),

    timing = param.Boolean(default=False)
    
    )


if p.coverage:
    coverage_cmd = "bin/coverage run --rcfile=doc/buildbot/coveragerc -a -p"
else:
    coverage_cmd = ""

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
    p.targets = ['unit','traintests','snapshots','gui','maptests']
elif p.targets == ['all']:
    # ALL
    p.targets = []

    

# ->params ?
TESTDP = 7
tests_dir = param.resolve_path("topo/tests",path_to_file=False)
scripts_dir = param.resolve_path("examples",path_to_file=False) ### XXX
topographica_script = xvfb + " " + timing_cmd + coverage_cmd + " " + sys.argv[0] + " " + p.extra_args



def _runc(cmd):
    print cmd
    return os.system(cmd)
    

import topo.misc.keyedlist
target = topo.misc.keyedlist.KeyedList()

from _setup import TRAINSCRIPTS


target['traintests'] = []
for script in TRAINSCRIPTS:
    script_path = os.path.join(scripts_dir,script)
    data_path = os.path.join(tests_dir,script+"_DATA")
    target['traintests'].append(topographica_script +  " -c 'from topo.tests.test_script import TestScript; TestScript(script=\"%(script_path)s\",data_filename=\"%(data_path)s\",decimal=6)'"%dict(script_path=script_path,data_path=data_path))

target['speedtests'] = []
for script in TRAINSCRIPTS:
    script_path = os.path.join(scripts_dir,script)
    target['speedtests'].append(topographica_script +  " -c 'from topo.tests.test_script import compare_speed_data;compare_speed_data(script=\"%(script_path)s\")'"%dict(script_path=script_path))


STARTUPSPEEDSCRIPTS = ["lissom.ty","gcal.ty"]

target['startupspeedtests'] = []
for script in STARTUPSPEEDSCRIPTS:
    script_path = os.path.join(scripts_dir,script)
    target['startupspeedtests'].append(topographica_script +  " -c 'from topo.tests.test_script import compare_startup_speed_data;compare_startup_speed_data(script=\"%(script_path)s\")'"%dict(script_path=script_path))



##### snapshot-tests
target['snapshots'] = []

# snapshot-compatibility-tests:
snapshot_path = os.path.join(tests_dir,"lissom_oo_or_od_dr_cr_dy_sf_000010.00.typ")
target['snapshots'].append(topographica_script + " -c \"from topo.command.basic import load_snapshot; load_snapshot('%(snapshot_path)s')\" -c \"topo.sim.run(1)\""%dict(snapshot_path=snapshot_path))


# Test that simulations give the same results whether run straight
# through or run part way, saved, reloaded, and run on to the same
# point.
# simulation-snapshot-tests:
target['snapshots'].append(topographica_script + " -c 'from topo.tests.test_script import compare_with_and_without_snapshot_NoSnapshot as A; A()'")

target['snapshots'].append(topographica_script + " -c 'from topo.tests.test_script import compare_with_and_without_snapshot_CreateSnapshot as B; B()'")

target['snapshots'].append(topographica_script + " -c 'from topo.tests.test_script import compare_with_and_without_snapshot_LoadSnapshot as C; C()'")

# CEBALERT: remove ~/topographica/*PICKLETEST* ?


target['pickle'] = []
# pickle-all-classes:
target['pickle'].append(topographica_script + " -c 'from topo.tests.test_script import pickle_unpickle_everything; errs = pickle_unpickle_everything(); import sys; sys.exit(errs)'")

# unpickle-compatibility-tests:
pickle_path = os.path.join(tests_dir,"instances-r11275.pickle")
target['pickle'].append(topographica_script + " -c 'from topo.tests.test_script import pickle_unpickle_everything; pickle_unpickle_everything(existing_pickles=\"%(pickle_path)s\")'"%dict(pickle_path=pickle_path))


# CB: hack that this will always be created even when test not being run
tmpd = commands.getoutput("mktemp -d")
#script-repr-tests:
target['scriptrepr']=[]
script = os.path.join(scripts_dir,"hierarchical.ty")
target['scriptrepr'].append(topographica_script + " %(script)s -a -c \"import param;param.normalize_path.prefix='%(tmpd)s'\" -c \"save_script_repr('script_repr_test.ty')\""%dict(tmpd=tmpd,script=script))

script_repr_test_path = os.path.join(tmpd,"script_repr_test.ty")    
target['scriptrepr'].append(topographica_script + " " + script_repr_test_path)
target['scriptrepr'].append(topographica_script + "-c \"import shutil;shutil.rmtree('%s')\""%tmpd)



### GUI tests
target['gui'] = []
# basic-gui-tests:
target['gui'].append(topographica_script + ' -g -c "from topo.tests.gui_tests import run_basic; nerr=run_basic();topo.guimain.quit_topographica(check=False,exit_status=nerr)"')

# detailed-gui-tests:
target['gui'].append(topographica_script + ' -g -c "from topo.tests.gui_tests import run_detailed; nerr=run_detailed(); topo.guimain.quit_topographica(check=False,exit_status=nerr)"')


target['batch'] = []
target['batch'].append(topographica_script + ' -c "from topo.tests.test_script import test_runbatch; test_runbatch()"')


target['unit'] = []
target['unit'].append(topographica_script + ' -c "import topo.tests; t=topo.tests.run(); import sys; sys.exit(len(t.failures+t.errors))"')


# CEBALERT: should use lissom.ty and test more map types
# pass a list of plotgroup names to test() instead of plotgroups_to_test to restrict the tests
target['maptests'] = []
script = os.path.join(scripts_dir,"lissom_oo_or.ty")
target['maptests'].append(topographica_script + ' -c "cortex_density=8" %s -c "topo.sim.run(100);from topo.tests.test_map_measurement import *; test(plotgroups_to_test)"'%script)


def start():
    exitstatus=0
    print "Running: %s"%p.targets
    print
    for name in (p.targets or target.keys()):
        print "*** " + name
        for cmd in target[name]:
            if _runc(cmd) > 0:
                exitstatus+=1

    print
    print "="*60
    print
    print "runtests.start(): targets with errors: %s"%exitstatus
    print
    if exitstatus>0:
        sys.exit(1)
    else:
        sys.exit(0)

    

if __name__=="__main__":
    start()

