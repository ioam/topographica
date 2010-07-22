"""
A family of response functions for CFProjections.

These function objects compute a response matrix when given an input
pattern and a set of ConnectionField objects.  Response functions come
in two varieties: ResponseFunction, and CFPResponseFunction.  A
ResponseFunction (e.g. DotProduct) computes the response due to one
CF.  To compute the response due to an entire CFProjection, a
ResponseFunction can be plugged in to CFPRF_Plugin.  CFPRF_Plugin is
one example of a CFPResponseFunction, which is a function that works
with the entire Projection at once.  Some optimizations and algorithms
can only be applied at the full CFPResponseFn level, so there are
other CFPResponseFns beyond CFPRF_Plugin.

Any new response functions added to this directory will automatically
become available for any model.

$Id$
"""
__version__='$Revision$'

# Automatically discover all .py files in this directory, and import classes from basic.py. 
import os,fnmatch
from basic import *
__all__ = basic.__all__ + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch
