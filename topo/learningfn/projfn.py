"""
Learning functions for Projections.


For example, CFProjectionLearningFunctions compute a new set of
ConnectionFields when given an input and output pattern and a set of
ConnectionField objects.
"""
import numpy as np

import param

from topo.base.cf import CFPLearningFn
from topo.base.sheet import activity_type
from topo.base.functionfamily import Hebbian,LearningFn
# Imported here so that all ProjectionLearningFns will be in the same package
from topo.base.cf import CFPLF_Identity,CFPLF_Plugin  # pyflakes:ignore (API import)


class CFPLF_EuclideanHebbian(CFPLearningFn):
    """
    Hebbian CFProjection learning rule based on Euclidean distance.

    Learning is driven by the distance from the input pattern to the
    weights, scaled by the current activity.  To implement a Kohonen
    SOM algorithm, the activity should be the neighborhood kernel
    centered around the winning unit, as implemented by KernelMax.
    """
    # CEBERRORALERT: ignoring the sheet mask
    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        # This learning function does not need to scale the learning
        # rate like some do, so it does not use constant_sum_connection_rate()

        cfs = iterator.flatcfs
        rows,cols = output_activity.shape
        for r in xrange(rows):
            for c in xrange(cols):
                flati = r*cols+c
                out = output_activity.flat[flati]
                if out !=0:
                    rate = learning_rate * out
                    cf = cfs[flati]
                    X = cf.get_input_matrix(input_activity)
                    cf.weights += rate * (X - cf.weights)

                    # CEBHACKALERT: see ConnectionField.__init__()
                    cf.weights *= cf.mask



#### JABHACKALERT: Untested
##class CFPLF_BCM(CFPLearningFn):
##    """
##    Bienenstock, Cooper, and Munro (1982) learning rule with sliding threshold.
##
##    (See Dayan and Abbott, 2001, equation 8.12, 8.13).
##
##    Activities change only when there is both pre- and post-synaptic activity.
##    Threshold is adjusted based on recent firing rates.
##    """
##    single_cf_fn = param.ClassSelector(LearningFn,default=BCMFixed())
##
##    unit_threshold_0=param.Number(default=0.5,bounds=(0,None),
##        doc="Initial value of threshold between LTD and LTP; actual value computed based on recent history.")
##    unit_threshold_learning_rate=param.Number(default=0.1,bounds=(0,None),
##        doc="Amount by which the unit_threshold is adjusted for each activity calculation.")
##
##    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
##        cfs = iterator.proj._cfs
##        # Initialize thresholds the first time we learn the size of the output_activity.
##        if not hasattr(self,'unit_thresholds'):
##            self.unit_thresholds=np.ones(output_activity.shape, dtype=np.float32)*self.unit_threshold_0
##
##        rows,cols = output_activity.shape
##
##        # JABALERT: Is this correct?
##      single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
##
##        # avoid evaluating these references each time in the loop
##        single_cf_fn = self.single_cf_fn
##      for r in xrange(rows):
##            for c in xrange(cols):
##                cf = cfs[r][c]
##                input_act = cf.get_input_matrix(input_activity)
##                unit_activity = output_activity[r,c]
##                threshold=self.unit_thresholds[r,c]
##                #print cf.weights, type(cf.weights)
##                #print input_act, type(input_act)
##                #print single_connection_learning_rate,unit_activity,threshold, (unit_activity-threshold)
##                cf.weights += (single_connection_learning_rate * unit_activity * (unit_activity-threshold)) * input_act
##                self.unit_thresholds[r,c] += self.unit_threshold_learning_rate*(unit_activity*unit_activity-threshold)
##
##                # CEBHACKALERT: see ConnectionField.__init__()
##                cf.weights *= cf.mask



class CFPLF_Trace(CFPLearningFn):
    """
    LearningFn that incorporates a trace of recent activity,
    not just the current activity.

    Based on P. Foldiak (1991), "Learning Invariance from
    Transformation Sequences", Neural Computation 3:194-200.  Also see
    Sutton and Barto (1981) and Wallis and Rolls (1997).

    Incorporates a decay term to keep the weight vector bounded, and
    so it does not normally require any output_fn normalization for
    stability.

    NOT YET TESTED.
    """

    trace_strength=param.Number(default=0.5,bounds=(0.0,1.0),
       doc="How much the learning is dominated by the activity trace, relative to the current value.")

    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),
        doc="LearningFn that will be applied to each CF individually.")

    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        ##Initialise traces to zero if they don't already exist
        if not hasattr(self,'traces'):
            self.traces=np.zeros(output_activity.shape,activity_type)
        for cf,i in iterator():
            unit_activity = output_activity.flat[i]
            #   print "unit activity is",unit_activity
        #    print "self trace is",self.traces[r,c]
            new_trace = (self.trace_strength*unit_activity)+((1-self.trace_strength)*self.traces.flat[i])
        #     print "and is now",new_trace
            self.traces.flat[i] = new_trace
            cf.weights += single_connection_learning_rate * new_trace * \
                              (cf.get_input_matrix(input_activity) - cf.weights)

            #CEBHACKALERT: see ConnectionField.__init__()
            cf.weights *= cf.mask



class CFPLF_OutstarHebbian(CFPLearningFn):
    """
    CFPLearningFunction applying the specified (default is Hebbian)
    single_cf_fn to each CF, where normalization is done in an outstar-manner.

    Presumably does not need a separate output_fn for normalization.

    NOT YET TESTED.
    """
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),
        doc="LearningFn that will be applied to each CF individually.")

    outstar_wsum = None

    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        # avoid evaluating these references each time in the loop
        single_cf_fn = self.single_cf_fn
        outstar_wsum = np.zeros(input_activity.shape)
        for cf,i in iterator():
            single_cf_fn(cf.get_input_matrix(input_activity),
                         output_activity.flat[i], cf.weights, single_connection_learning_rate)
            # Outstar normalization
            wrows,wcols = cf.weights.shape
            for wr in xrange(wrows):
                for wc in xrange(wcols):
                    outstar_wsum[wr][wc] += cf.weights[wr][wc]

            # CEBHACKALERT: see ConnectionField.__init__()
            cf.weights *= cf.mask




class HomeoSynaptic(CFPLearningFn):
    """
    Learning function using homeostatic synaptic scaling from
    Sullivan & de Sa, "Homeostatic Synaptic Scaling in Self-Organizing Maps",
    Neural Networks (2006), 19(6-7):734-43.

    Does not necessarily require output_fn normalization for stability.
    """
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),
       doc="LearningFn that will be applied to each CF individually")

    beta_n = param.Number(default=0.01,bounds=(0,None),
       doc="homeostatic learning rate")

    beta_c = param.Number(default=0.005,bounds=(0,None),
       doc="time window over which the neuron's firing rate is averaged")

    activity_target = param.Number(default=0.1,bounds=(0,None),
         doc="Target average activity")

    #debug = param.Boolean(default=False,doc="Print average activity values")
    #beta_n = param.Number(default=0.00033,bounds=(0,None),doc="Homeostatic learning rate") #Too small?
    #beta_c = param.Number(default=0.000033,bounds=(0,None),doc="Time window over which the neuron's firing rate is averaged")

    def __init__(self,**params):
        super(HomeoSynaptic,self).__init__(**params)
        self.temp_hist = []
        self.ave_hist = []

    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        """
        Update the value of the given weights matrix based on the
        input_activity matrix (of the same size as the weights matrix)
        and the response of this unit (the unit_activity), governed by
        a per-connection learning rate.
        """
        if not hasattr(self,'averages'):
            self.averages = np.ones(output_activity.shape, dtype=np.float) * 0.1


            # normalize initial weights to 1.0
            for cf,i in iterator():
                current_norm_value = 1.0*np.sum(abs(cf.weights.ravel()))
                if current_norm_value != 0:
                    factor = (1.0/current_norm_value)
                    cf.weights *= factor

        # compute recent average of output activity
        self.averages = self.beta_c * output_activity + (1.0-self.beta_c) * self.averages
        activity_norm = 1.0 + self.beta_n * \
           ((self.averages - self.activity_target)/self.activity_target)

        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)

        # avoid evaluating these references each time in the loop
        single_cf_fn = self.single_cf_fn
        for cf,i in iterator():
            single_cf_fn(cf.get_input_matrix(input_activity),
                         output_activity.flat[i], cf.weights, single_connection_learning_rate)

            # homeostatic normalization
            cf.weights /= activity_norm.flat[i]

            # CEBHACKALERT: see ConnectionField.__init__()
            cf.weights *= cf.mask

        # For analysis only; can be removed (in which case also remove the initializations above)
# CEBALERT: I changed [0][7] to [0]!
        self.ave_hist.append(self.averages.flat[0])
        self.temp_hist.append (np.sum(abs(iterator.flatcfs[0].weights.ravel())))




class CFPLF_PluginScaled(CFPLearningFn):
    """
    CFPLearningFunction applying the specified single_cf_fn to each CF.
    Scales the single-connection learning rate by a scaling factor
    that is different for each individual unit. Thus each individual
    connection field uses a different learning rate.
    """

    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),
        doc="Accepts a LearningFn that will be applied to each CF individually.")

    learning_rate_scaling_factor = param.Parameter(default=None,
        doc="Matrix of scaling factors for scaling the learning rate of each CF individually.")


    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        """Apply the specified single_cf_fn to every CF."""

        if self.learning_rate_scaling_factor is None:
            self.learning_rate_scaling_factor = np.ones(output_activity.shape)

        single_cf_fn = self.single_cf_fn
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)

        for cf,i in iterator():
            sc_learning_rate = self.learning_rate_scaling_factor.flat[i] * single_connection_learning_rate
            single_cf_fn(cf.get_input_matrix(input_activity),
                         output_activity.flat[i], cf.weights, sc_learning_rate)
            # CEBHACKALERT: see ConnectionField.__init__() re. mask & output fn
            cf.weights *= cf.mask


    def update_scaling_factor(self, new_scaling_factor):
        """Update the single-connection learning rate scaling factor."""
        self.learning_rate_scaling_factor = new_scaling_factor


__all__ = [
    "CFPLF_Identity",
    "CFPLF_Plugin",
    "CFPLF_EuclideanHebbian",
    "CFPLF_Trace",
    "CFPLF_OutstarHebbian",
    "HomeoSynaptic",
    "CFPLF_PluginScaled",
]
