"""
A family of function objects for transforming one set of coordinates into
another.

Coordinate mapper functions are useful for defining magnifications and
other kinds of transformations on sheet coordinates, e.g. for defining
retinal magnification using a CFProjection.  A CoordinateMapperFn
(e.g. MagnifyingMapper), is applied to an (x,y) pair and returns a new
(x,y) pair.  To apply a mapping to a CF projection, set the
CFProjection's coord_mapper parameter to an instance of the desired
CoordinateMapperFn.

$Id$
"""
__version__='$Revision$'

# Automatically discover all .py files in this directory, and import classes from basic.py. 
import os,fnmatch
from basic import *
__all__ = basic.__all__ + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

