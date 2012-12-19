"""
A family of function objects for changing a set of weights over time.

Learning functions come in two varieties: LearningFunction, and
CFPLearningFunction.  A LearningFunction (e.g. Hebbian) applies to one
set of weights, typically from one ConnectionField.  To apply learning
to an entire CFProjection, a LearningFunction can be plugged in to
CFPLF_Plugin.  CFPLF_Plugin is one example of a CFPLearningFunction,
which is a function that works with the entire Projection at once.
Some optimizations and algorithms can only be applied at the full
CFPLearningFn level, so there are other CFPLearningFns beyond
CFPLF_Plugin.

Any new learning functions added to this directory will automatically
become available for any model.
"""

import param

from topo.base.functionfamily import LearningFn
# Imported here so that all learning functions will be in the same package
from topo.base.functionfamily import Hebbian,IdentityLF  # pyflakes:ignore (API import)



class Oja(LearningFn):
    """
    Oja's rule (Oja, 1982; Dayan and Abbott, 2001, equation 8.16.)

    Hebbian rule with soft multiplicative normalization, tending the
    weights toward a constant sum-squared value over time.  Thus this
    function does not normally need a separate output_fn for normalization.
    """

    alpha=param.Number(default=0.1,bounds=(0,None))
    def __call__(self,input_activity, unit_activity, weights, single_connection_learning_rate):
        weights += single_connection_learning_rate * (unit_activity * input_activity -
                                                      self.alpha * (unit_activity**2) * weights)

class Covariance(LearningFn):
    """
    Covariance learning rule supporting either input or unit thresholds.

    As presented by Dayan and Abbott (2001), covariance rules allow
    either potentiation or depression of the same synapse, depending
    on an activity level.  By default, this implementation follows
    Dayan and Abbott equation 8.8, with the unit_threshold determining
    the level of postsynaptic activity (activity of the target unit),
    below which LTD (depression) will occur.

    If you wish to use an input threshold as in Dayan and Abbott
    equation 8.9 instead, set unit_threshold to zero and change
    input_threshold to some positive value instead.  When both
    thresholds are zero this rule degenerates to the standard Hebbian
    rule.

    Requires some form of output_fn normalization for stability.
    """

    unit_threshold =param.Number(default=0.5,bounds=(0,None),
        doc="Threshold between LTD and LTP, applied to the activity of this unit.")
    input_threshold=param.Number(default=0.0,bounds=(0,None),
        doc="Threshold between LTD and LTP, applied to the input activity.")
    def __call__(self,input_activity, unit_activity, weights, single_connection_learning_rate):
        weights += single_connection_learning_rate * (unit_activity - self.unit_threshold) * (input_activity - self.input_threshold)


class CPCA(LearningFn):
    """
    CPCA (Conditional Principal Component Analysis) rule.

    (See O'Reilly and Munakata, Computational Explorations in
    Cognitive Neuroscience, 2000, equation 4.12.)

    Increases each weight in proportion to the product of this
    neuron's activity, input activity, and connection weights.

    Has built-in normalization, and so does not require output_fn
    normalization for stability.  Intended to be a more biologically
    plausible version of the Oja rule.

    Submitted by Veldri Kurniawan and Lewis Ng.
    """

    def __call__(self,input_activity, unit_activity, weights, single_connection_learning_rate):
        """
        Update the value of the given weights matrix based on the
        input_activity matrix (of the same size as the weights matrix),
        the response of this unit (the unit_activity), and the previous weights
        matrix governed by a per-connection learning rate.
        """

        weights += single_connection_learning_rate * unit_activity * (input_activity - weights);


class BCMFixed(LearningFn):
    """
    Bienenstock, Cooper, and Munro (1982) learning rule with a fixed threshold.

    (See Dayan and Abbott, 2001, equation 8.12) In the BCM rule,
    activities change only when there is both pre- and post-synaptic
    activity.  The full BCM rule requires a sliding threshold (see
    CFPBCM), but this version is simpler and easier to analyze.

    Requires some form of output_fn normalization for stability.
    """

    unit_threshold=param.Number(default=0.5,bounds=(0,None),doc="Threshold between LTD and LTP.")
    def __call__(self,input_activity, unit_activity, weights, single_connection_learning_rate):
        weights += single_connection_learning_rate * unit_activity * input_activity * (unit_activity-self.unit_threshold)



_public = list(set([_k for _k,_v in locals().items()
                    if isinstance(_v,type) and issubclass(_v,LearningFn)]))

# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = _public + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

