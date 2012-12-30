"""
Analysis tools for Topographica, other than plotting tools.
"""


# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

