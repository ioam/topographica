# CEBALERT: another duplicate
RELEASE = '0.9.7'

import sys
import os
import copy
import subprocess
import re

# Python 2.7 has subprocess.check_output, which might be what I wanted.
def get_call_output(cmd):
    return subprocess.Popen(cmd.split(),stdout=subprocess.PIPE).communicate()[0].strip()
    

def _get_version():
    # CEBALERT: just copied shell commands from Makefile
    try:
        svnversion = get_call_output("svnversion")
        if svnversion=="exported":
            git_came_from = re.search("Revision: ([0-9]*)",get_call_output("git svn info")).group(1)
            git_version = get_call_output("git rev-parse HEAD")
            svnversion = git_came_from+":"+git_version
    except:
        svnversion = "None"
    return svnversion

def _get_release():
    return RELEASE

def _get_python():
    # CEBALERT: to work with pyinstaller etc, would need to check for sys.frozen
    return sys.executable


def write(python_bin,release,version,usersite):

    if usersite==0:
        python_bin+=" -s"

    script = """#!%s
# Startup script for Topographica

import topo
topo.release='%s'
topo.version='%s'

# Process the command-line arguments
from sys import argv
from topo.misc.commandline import process_argv
process_argv(argv[1:])
"""%(python_bin,release,version)
    
    # CEBALERT: assumes we're in the root topographica dir
    f = open('topographica','w')
    f.write(script)
    f.close()
    try:
        os.system('chmod +x topographica')
    except:
        pass



if __name__=='__main__':
    print "creating topographica script..."

    if len(sys.argv)==5:
        python_bin,release,version,usersite = sys.argv[1::]
    else:
        assert len(sys.argv)==1, "Either pass no arguments, or pass python_bin, release, version, usersite"
        python_bin = _get_python()
        release = _get_release()
        version = _get_version()
        usersite = 1

    print "python: %s"%python_bin
    print "release: %s"%release
    print "version: %s"%version
    print "usersite: %s"%usersite

    write(python_bin,release,version,usersite)

