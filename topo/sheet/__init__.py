"""
Sheet classes.

A Sheet is a two-dimensional arrangement of processing units,
typically modeling a neural region or a subset of cells in a neural
region.  Any new Sheet classes added to this directory will
automatically become available for any model.

$Id$
"""
__version__='$Revision$'

# Automatically discover all .py files in this directory, and import classes from basic.py. 
import os,fnmatch
from basic import *
__all__ = basic.__all__ + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

# Not a sheet, but needed for using Sheets
from topo.base.sheet import BoundingBox  # pyflakes:ignore (API import)

# By default, avoid loading modules that rely on external libraries
# that might not be present on this system.
__all__.remove('ptztracker')
