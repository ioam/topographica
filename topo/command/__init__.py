"""
A family of high-level user commands acting on the entire simulation.

Any new commands added to this directory will automatically become
available for any program.

Commands here should be 'bullet-proof' and work 'from scratch'.
That is, they should print warnings if required but should not raise
errors that would interrupt e.g. a long batch run of simulation work,
no matter what the context from which they are called.

$Id$
"""
__version__='$Revision$'

# Automatically discover all .py files in this directory, and import functions from basic.py. 
import os,fnmatch
from basic import *
__all__ = basic.__all__ + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch
