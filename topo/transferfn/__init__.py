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
"""

import copy

import param

import numpy as np
from numpy import exp,zeros,ones,power

from topo.base.sheet import activity_type
from topo.base.arrayutil import clip_lower

from numbergen import TimeAwareRandomState

# Imported here so that all TransferFns will be in the same package
from imagen.transferfn import TransferFn, TransferFnWithState   # pyflakes:ignore (API import)
from imagen.transferfn import IdentityTF, Threshold             # pyflakes:ignore (API import)
from imagen.transferfn import BinaryThreshold, Hysteresis                # pyflakes:ignore (API import)
from imagen.transferfn import DivisiveNormalizeL1, DivisiveNormalizeL2   # pyflakes:ignore (API import)
from imagen.transferfn import DivisiveNormalizeLinf, DivisiveNormalizeLp # pyflakes:ignore (API import)

# CEBHACKALERT: these need to respect the mask - which will be passed in.


class PiecewiseLinear(TransferFn):
    """
    Piecewise-linear TransferFn with lower and upper thresholds.

    Values below the lower_threshold are set to zero, those above
    the upper threshold are set to 1.0, and those in between are
    scaled linearly.
    """
    lower_bound = param.Number(default=0.0,softbounds=(0.0,1.0))
    upper_bound = param.Number(default=1.0,softbounds=(0.0,1.0))

    def __call__(self,x):
        fact = 1.0/(self.upper_bound-self.lower_bound)
        x -= self.lower_bound
        x *= fact
        x.clip(0.0,1.0,out=x)



class Sigmoid(TransferFn):
    """
    Sigmoidal (logistic) transfer function: 1/(1+exp-(r*x+k)).

    As defined in Jochen Triesch, ICANN 2005, LNCS 3696 pp. 65-70.
    The parameters control the growth rate (r) and the x position (k)
    of the exponential.

    This function is a special case of the GeneralizedLogistic
    function, with parameters r=r, l=0, u=1, m=-k/2r, and b=1.  See
    Richards, F.J. (1959), A flexible growth function for empirical
    use. J. Experimental Botany 10: 290--300, 1959.
    http://en.wikipedia.org/wiki/Generalised_logistic_curve
    """

    r = param.Number(default=1,doc="Parameter controlling the growth rate")
    k = param.Number(default=0,doc="Parameter controlling the x-postion")

    def __call__(self,x):
        x_orig = copy.copy(x)
        x *= 0.0
        x += 1.0 / (1.0 + exp(-(self.r*x_orig+self.k)))



class NakaRushton(TransferFn):
    #JABALERT: Please write the equation into words in the docstring, as in Sigmoid.
    """
    Naka-Rushton curve.

    From Naka, K. and Rushton, W. (1996), S-potentials from luminosity
    units in the retina of fish (Cyprinidae). J. Physiology 185:587-599.

    The Naka-Rushton curve has been shown to be a good approximation
    of constrast gain control in cortical neurons.  The input of the
    curve is usually contrast, but under the assumption that the
    firing rate of a model neuron is directly proportional to the
    contrast, it can be used as a TransferFn for a Sheet.

    The parameter c50 corresponds to the contrast at which the half of
    the maximal output is reached.  For a Sheet TransferFn this translates
    to the input for which a neuron will respond with activity 0.5.
    """

    c50 = param.Number(default=0.1, doc="""
        The input of the neuron at which it responds at half of its
        maximal firing rate (1.0).""")

    e = param.Number(default=1.0,doc="""
        The exponent of the input x.""")

    #JABALERT: (pow(x_orig,self.e) should presumably be done only once, using a temporary
    def __call__(self,x):
        #print 'A:', x
        #print 'B:', pow(x,self.e) / (pow(x,self.e) + pow(self.c50,self.e))
        x_orig = copy.copy(x)
        x *= 0
        x += pow(x_orig,self.e) / (pow(x_orig,self.e) + pow(self.c50,self.e))



class GeneralizedLogistic(TransferFn):
    """
    The generalized logistic curve (Richards' curve): y = l + (u /(1 + b * exp(-r*(x-2*m))^(1/b))).

    The logistic curve is a flexible function for specifying a
    nonlinear growth curve using five parameters:

    * l: the lower asymptote
    * u: the upper asymptote minus l
    * m: the time of maximum growth
    * r: the growth rate
    * b: affects near which asymptote maximum growth occurs

    From Richards, F.J. (1959), A flexible growth function for empirical
    use. J. Experimental Botany 10: 290--300.
    http://en.wikipedia.org/wiki/Generalised_logistic_curve
    """

    # JABALERT: Reword these to say what they are, not what they
    # control, if they are anything that can be expressed naturally.
    # E.g. is l a parameter controlling the lower asymptote, or is it
    # simply the lower asymptote?  If it's the lower asymptote, say
    # doc="Lower asymptote.".  Only if the parameter's relationship to
    # what it controls is very indirect should it be worded as below.
    l = param.Number(default=1,doc="Parameter controlling the lower asymptote.")
    u = param.Number(default=1,doc="Parameter controlling the upper asymptote (upper asymptote minus lower asymptote.")
    m = param.Number(default=1,doc="Parameter controlling the time of maximum growth.")
    r = param.Number(default=1,doc="Parameter controlling the growth rate.")
    b = param.Number(default=1,doc="Parameter which affects near which asymptote maximum growth occurs.")

    def __call__(self,x):
        x_orig = copy.copy(x)
        x *= 0.0
        x += self.l + ( self.u /(1 + self.b*exp(-self.r *(x_orig - 2*self.m))**(1 / self.b)) )



class HalfRectifyAndSquare(TransferFn):
    """
    Transfer function that applies a half-wave rectification (clips at zero)
    and then squares the values.
    """
    t = param.Number(default=0.0,doc="""
        The threshold at which output becomes non-zero.""")

    def __call__(self,x):
        x -= self.t
        clip_lower(x,0)
        x *= x



class HalfRectifyAndPower(TransferFn):
    """
    Transfer function that applies a half-wave rectification (i.e.,
    clips at zero), and then raises the result to the e-th power
    (where the exponent e can be selected arbitrarily).
    """
    e = param.Number(default=2.0,doc="""
        The exponent to which the thresholded value is raised.""")

    t = param.Number(default=0.0,doc="""
        The threshold level subtracted from x.""")

    def __call__(self,x):
        x -= self.t
        clip_lower(x,0)
        a = power(x,self.e)
        x*=0
        x+=a



class ExpLinear(TransferFn):
    """
    Transfer function that is exponential until t from which point it is linear.
    """

    e = param.Number(default=1.0,doc="""
        The exponent of the exponetial part of the curve""")
    t1 = param.Number(default=0.5,doc="""
        The threshold level where function becomes non-zero""")
    t2 = param.Number(default=1.0,doc="""
        The threshold level at which curve becomes linear""")

    a = param.Number(default=1.0,doc="""
        The overall scaling of the function""")

    def __call__(self,x):
        x-=self.t1
        clip_lower(x,0)
        z = (x>=self.t2)*(1.0*exp(self.e*(-self.t2))+(x-self.t2)) + \
            (x<self.t2)*(exp(self.e*(x-self.t2))-exp(self.e*(-self.t2)))
        x*=0
        x+=self.a*z



class Square(TransferFn):
    """Transfer function that applies a squaring nonlinearity."""

    def __call__(self,x):
        x *= x


# CB: it's not ideal that all TransferFnWithRandomState fns have
# the plastic stuff (from TransferFnWithState).
class TransferFnWithRandomState(TransferFnWithState, TimeAwareRandomState):
    """
    Abstract base class for TransferFns that use a random
    state. Inherits time-dependent control of the random state from
    numbergen.TimeAwareRandomState. Consult the help of
    TimeAwareRandomState for more information.
    """

    random_generator = param.Parameter(
        default=np.random.RandomState(seed=(10,10)),precedence=-1,doc=
        """
        Using Numpy's RandomState instead of random.Random as the
        former can generate random arrays and more random
        distributions. See RandomState's help for more information.
        """)

    __abstract = True

    def __init__(self,**params):
        super(TransferFnWithRandomState,self).__init__(**params)
        self.__random_generators_stack = []
        self._initialize_random_state(seed=(10,10), shared=True)

    def state_push(self):
        """
        Save the current random number generator (onto the stack),
        replacing it with a copy.
        """
        self.__random_generators_stack.append(self.random_generator)
        self.random_generator=copy.copy(self.random_generator)
        super(TransferFnWithRandomState,self).state_push()

    def state_pop(self):
        """
        Retrieve the previous random number generator from the stack.
        """
        self.random_generator = self.__random_generators_stack.pop()
        super(TransferFnWithRandomState,self).state_push()


class PoissonSample(TransferFnWithRandomState):
    """
    Simulate Poisson-distributed activity with specified mean values.

    This transfer function interprets each matrix value as the
    (potentially scaled) rate of a Poisson process and replaces it
    with a sample from the appropriate Poisson distribution.

    To allow the matrix to contain values in a suitable range (such as
    [0.0,1.0]), the input matrix is scaled by the parameter in_scale,
    and the baseline_rate is added before sampling.  After sampling,
    the output value is then scaled by out_scale.  The function thus
    performs this transformation::

      x <- P(in_scale * x + baseline_rate) * out_scale

    where x is a matrix value and P(r) samples from a Poisson
    distribution with rate r.
    """

    in_scale = param.Number(default=1.0,doc="""
       Amount by which to scale the input.""")

    baseline_rate = param.Number(default=0.0,doc="""
       Constant to add to the input after scaling, resulting in a baseline
       Poisson process rate.""")

    out_scale = param.Number(default=1.0,doc="""
       Amount by which to scale the output (e.g. 1.0/in_scale).""")

    def __call__(self,x):
        if self.time_dependent: self._hash_and_seed()

        x *= self.in_scale
        x += self.baseline_rate
        sample = self.random_generator.poisson(x,x.shape)
        x *= 0.0
        x += sample
        x *= self.out_scale



# CEBALERT: I think this TF is a bit misleading because it does not
# alter the input array. Is a TransferFn the right thing to use to
# record an average activity? Could consider replacing this with my
# "attribute tracking" code (some of which is not yet in SVN).
class ActivityAveragingTF(TransferFnWithState):
    """
    Calculates the average of the input activity.

    The average is calculated as an exponential moving average, where
    the weighting for each older data point decreases exponentially.
    The degree of weighing for the previous values is expressed as a
    constant smoothing factor.

    The plastic parameter allows the updating of the average values
    to be disabled temporarily, e.g. while presenting test patterns.
    """

    step = param.Number(default=1, doc="""
        How often to update the average.
        For instance, step=1 means to update it every time this TF is
        called; step=2 means to update it every other time.""")

    smoothing = param.Number(default=0.9997, doc="""
        The degree of weighting for the previous average, when
        calculating the new average.""")

    initial_average=param.Number(default=0, doc="""
        Starting value for the average activity.""")


    def __init__(self,**params):
        super(ActivityAveragingTF,self).__init__(**params)
        self.n_step = 0
        self.x_avg=None


    def __call__(self,x):
        if self.x_avg is None:
            self.x_avg=self.initial_average*ones(x.shape, activity_type)

        # Collect values on each appropriate step

        self.n_step += 1
        if self.n_step == self.step:
            self.n_step = 0
            if self.plastic:
                self.x_avg = (1.0-self.smoothing)*x + self.smoothing*self.x_avg



class HomeostaticMaxEnt(TransferFnWithRandomState):
    """
    Implementation of homeostatic intrinsic plasticity from Jochen Triesch,
    ICANN 2005, LNCS 3696 pp.65-70.

    A sigmoid activation function is adapted automatically to achieve
    desired average firing rate and approximately exponential
    distribution of firing rates (for the maximum possible entropy).

    Note that this TransferFn has state, so the history of calls to it
    will affect future behavior.  The plastic parameter can be used
    to disable changes to the state.

    Also calculates average activity as useful debugging information,
    for use with AttributeTrackingTF.  Average activity is calculated as
    an exponential moving average with a smoothing factor (smoothing).
    For more information see:
    NIST/SEMATECH e-Handbook of Statistical Methods, Single Exponential Smoothing
    http://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm
    """

    eta = param.Number(default=0.0002,doc="""
        Learning rate for homeostatic plasticity.""")

    mu = param.Number(default=0.01,doc="""
        Target average firing rate.""")

    smoothing = param.Number(default=0.9997, doc="""
        Weighting of previous activity vs. current activity when
        calculating the average.""")

    a_init = param.Parameter(default=None,doc="""
        Multiplicative parameter controlling the exponential.""")

    b_init = param.Parameter(default=None,doc="""
        Additive parameter controlling the exponential.""")

    step = param.Number(default=1, doc="""
        How often to update the a and b parameters.
        For instance, step=1 means to update it every time this TF is
        called; step=2 means to update it every other time.""")

    def __init__(self,**params):
        super(HomeostaticMaxEnt,self).__init__(**params)
        self.first_call = True
        self.n_step=0
        self.__current_state_stack=[]
        self.a=None
        self.b=None
        self.y_avg=None

    def __call__(self,x):
        if self.time_dependent: self._hash_and_seed()

        if self.first_call:
            self.first_call = False
            if self.a_init==None:
                self.a = self.random_generator.uniform(low=10, high=20,size=x.shape)
            else:
                self.a = ones(x.shape, x.dtype.char) * self.a_init
            if self.b_init==None:
                self.b = self.random_generator.uniform(low=-8.0, high=-4.0,size=x.shape)
            else:
                self.b = ones(x.shape, x.dtype.char) * self.b_init
            self.y_avg = zeros(x.shape, x.dtype.char)

        # Apply sigmoid function to x, resulting in what Triesch calls y
        x_orig = copy.copy(x)

        x *= 0.0
        x += 1.0 / (1.0 + exp(-(self.a*x_orig + self.b)))


        self.n_step += 1
        if self.n_step == self.step:
            self.n_step = 0
            if self.plastic:
                self.y_avg = (1.0-self.smoothing)*x + self.smoothing*self.y_avg #Calculate average for use in debugging only

                # Update a and b
                self.a += self.eta * (1.0/self.a + x_orig - (2.0 + 1.0/self.mu)*x_orig*x + x_orig*x*x/self.mu)
                self.b += self.eta * (1.0 - (2.0 + 1.0/self.mu)*x + x*x/self.mu)


    def state_push(self):
        self.__current_state_stack.append((copy.copy(self.a), copy.copy(self.b), copy.copy(self.y_avg), copy.copy(self.first_call)))
        super(HomeostaticMaxEnt,self).state_push()


    def state_pop(self):
        self.a, self.b, self.y_avg, self.first_call =  self.__current_state_stack.pop()
        super(HomeostaticMaxEnt,self).state_pop()



class ScalingTF(TransferFnWithState):
    """
    Scales input activity based on the current average activity (x_avg).

    The scaling is calculated to bring x_avg for each unit closer to a
    specified target average.  Calculates a scaling factor that is
    greater than 1 if x_avg is less than the target and less than 1 if
    x_avg is greater than the target, and multiplies the input
    activity by this scaling factor.

    The plastic parameter allows the updating of the average values
    to be disabled temporarily, e.g. while presenting test patterns.
    """

    target = param.Number(default=0.01, doc="""
        Target average activity for each unit.""")

    step=param.Number(default=1, doc="""
        How often to calculate the average activity and scaling factor.""")

    smoothing = param.Number(default=0.9997, doc="""
        Determines the degree of weighting of previous activity vs.
        current activity when calculating the average.""")


    def __init__(self,**params):
        super(ScalingTF,self).__init__(**params)
        self.n_step = 0
        self.x_avg=None
        self.sf=None

    def __call__(self,x):

        if self.x_avg is None:
            self.x_avg=self.target*ones(x.shape, activity_type)
        if self.sf is None:
            self.sf=ones(x.shape, activity_type)

        # Collect values on each appropriate step

        self.n_step += 1
        if self.n_step == self.step:
            self.n_step = 0
            if self.plastic:
                self.sf *= 0.0
                self.sf += self.target/self.x_avg
                self.x_avg = (1.0-self.smoothing)*x + self.smoothing*self.x_avg

        x *= self.sf

_public = list(set([_k for _k,_v in locals().items() if isinstance(_v,type) and issubclass(_v,TransferFn)]))


# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = _public + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch
