"""
Basic function objects.

TransferFns: accept and modify a 2d array
ResponseFns: accept two 2d arrays and return a scalar
LearningFns: accept two 2d arrays and a scalar, return one of the arrays modified
"""

# CEBALERT: Documentation is just draft.

import numpy

import param

from imagen.transferfn import TransferFn, IdentityTF # pyflakes:ignore (API import)

class LearningFn(param.Parameterized):
    """
    Abstract base class for learning functions that plug into
    CFPLF_Plugin.
    """

    __abstract = True

    # JABALERT: Shouldn't the single_connection_learning_rate be
    # omitted from the call and instead made into a class parameter?
    def __call__(self,input_activity, unit_activity, weights, single_connection_learning_rate):
        """
        Apply this learning function given the input and output
        activities and current weights.

        Must be implemented by subclasses.
        """
        raise NotImplementedError


class Hebbian(LearningFn):
    """
    Basic Hebbian rule; Dayan and Abbott, 2001, equation 8.3.

    Increases each weight in proportion to the product of this
    neuron's activity and the input activity.

    Requires some form of output_fn normalization for stability.
    """

    def __call__(self,input_activity, unit_activity, weights, single_connection_learning_rate):
        weights += single_connection_learning_rate * unit_activity * input_activity


class IdentityLF(LearningFn):
    """
    Identity function; does not modify the weights.

    For speed, calling this function object is sometimes optimized
    away entirely.  To make this feasible, it is not allowable to
    derive other classes from this object, modify it to have different
    behavior, add side effects, or anything of that nature.
    """

    def __call__(self,input_activity, unit_activity, weights, single_connection_learning_rate):
        pass



class ResponseFn(param.Parameterized):
    """Abstract base class for response functions that plug into CFPRF_Plugin."""

    __abstract = True

    def __call__(self,m1,m2):
        """
        Apply the response function; must be implemented by subclasses.
        """
        raise NotImplementedError



class DotProduct(ResponseFn):
    """
    Return the sum of the element-by-element product of two 2D
    arrays.
    """
    def __call__(self,m1,m2):
        # CBENHANCEMENT: numpy.vdot(m1,m2)?
        # Early tests indicated that
        # vdot(a,b)=dot(a.ravel(),b.ravel()) but was slower. Should
        # check that.
        return numpy.dot(m1.ravel(),m2.ravel())



class CoordinateMapperFn(param.Parameterized):
    """Abstract base class for functions mapping from a 2D coordinate into another one."""

    __abstract = True

    def __call__(self,x,y):
        """
        Apply the coordinate mapping function; must be implemented by subclasses.
        """
        raise NotImplementedError


class IdentityMF(CoordinateMapperFn):
    """Return the x coordinate of the given coordinate."""
    def __call__(self,x,y):
        return x,y


class PatternDrivenAnalysis(param.Parameterized):
    """
    Abstract base class for various stimulus-response types of analysis.

    This type of analysis consists of presenting a set of input
    patterns and collecting the responses to each one, which one will
    often want to do in a way that does not affect the current state
    of the network.

    To achieve this, the class defines several types of hooks where
    arbitrary function objects (i.e., callables) can be registered.
    These hooks are generally used to ensure that unrelated previous
    activity is eliminated, that subsequent patterns do not interact,
    and that the initial state is restored after analysis.

    Any subclasses must ensure that these hook lists are run at the
    appropriate stage in their processing, using e.g.
    "for f in some_hook_list: f()".
    """

    __abstract = True

    pre_analysis_session_hooks = param.HookList(default=[],instantiate=False,doc="""
        List of callable objects to be run before an analysis session begins.""")

    pre_presentation_hooks = param.HookList(default=[],instantiate=False,doc="""
        List of callable objects to be run before each pattern is presented.""")

    post_presentation_hooks = param.HookList(default=[],instantiate=False,doc="""
        List of callable objects to be run after each pattern is presented.""")

    post_analysis_session_hooks = param.HookList(default=[],instantiate=False,doc="""
        List of callable objects to be run after an analysis session ends.""")
