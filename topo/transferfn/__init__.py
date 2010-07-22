"""
A family of function objects for transforming a matrix generated from some other function.

Output functions are useful for neuron activation functions,
normalization of matrices, etc.  They come in two varieties:
OutputFunction, and CFPOutputFunction.  An OutputFunction
(e.g. PiecewiseLinear) applies to one matrix of any type, such as an
activity matrix or a set of weights.  To apply an OutputFunction to
all of the weight matrices in an entire CFProjection, an
OutputFunction can be plugged in to CFPOF_Plugin.  CFPOF_Plugin is one
example of a CFPOutputFunction, which is a function that works with
the entire Projection at once.

Any new output functions added to this directory will automatically
become available for any model.

$Id$
"""
__version__='$Revision$'

# Automatically discover all .py files in this directory, and import classes from basic.py. 
import os,fnmatch
from basic import *
__all__ = basic.__all__ + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch
