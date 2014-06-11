"""
Transfer functions with more complex dependencies.

$Id: basic.py 10790 2009-11-21 17:51:33Z antolikjan $
"""

import copy

import numpy, numpy.random
from numpy import ones

import param

import topo
import topo.base.functionfamily

from topo.base.arrayutil import clip_lower,array_argmax
from topo.base.patterngenerator import PatternGenerator,Constant
from topo.base.boundingregion import BoundingBox
from topo.base.sheetcoords import SheetCoordinateSystem

from topo.transferfn import TransferFn, TransferFnWithState
from topo.pattern import Gaussian

# Not suitable for basic.py due to its dependence on patterns.
class PatternCombine(TransferFn):
    """
    Combine the supplied pattern with one generated using a
    PatternGenerator.

    Useful for operations like adding noise or masking out lesioned
    items or around the edges of non-rectangular shapes.
    """

    generator = param.ClassSelector(PatternGenerator,
        default=Constant(), doc="""
        Pattern to combine with the supplied matrix.""")

    operator = param.Parameter(numpy.multiply,precedence=0.98,doc="""
        Binary Numeric function used to combine the two patterns.

        Any binary Numeric array "ufunc" returning the same type of
        array as the operands and supporting the reduce operator is
        allowed here.  See topo.pattern.Composite.operator for more
        details.
        """)

    def __call__(self,x):
        ###JABHACKALERT: Need to set it up to be independent of
        #density; right now only things like random numbers work
        #reasonably
        rows,cols = x.shape
        bb = BoundingBox(points=((0,0), (rows,cols)))
        generated_pattern = self.generator(bounds=bb,xdensity=1,ydensity=1).transpose()
        new_pattern = self.operator(x, generated_pattern)
        x *= 0.0
        x += new_pattern



# Not suitable for basic.py due to its dependence on patterns.
class KernelMax(TransferFn):
    """
    Replaces the given matrix with a kernel function centered around the maximum value.

    This operation is usually part of the Kohonen SOM algorithm, and
    approximates a series of lateral interactions resulting in a
    single activity bubble.

    The radius of the kernel (i.e. the surround) is specified by the
    parameter 'radius', which should be set before using __call__.
    The shape of the surround is determined by the
    neighborhood_kernel_generator, and can be any PatternGenerator
    instance, or any function accepting bounds, density, radius, and
    height to return a kernel matrix.
    """

    kernel_radius = param.Number(default=0.0,bounds=(0,None),doc="""
        Kernel radius in Sheet coordinates.""")

    neighborhood_kernel_generator = param.ClassSelector(PatternGenerator,
        default=Gaussian(x=0.0,y=0.0,aspect_ratio=1.0),
        doc="Neighborhood function")

    crop_radius_multiplier = param.Number(default=3.0,doc="""
        Factor by which the radius should be multiplied, when deciding
        how far from the winner to keep evaluating the kernel.""")

    density=param.Number(1.0,bounds=(0,None),doc="""
        Density of the Sheet whose matrix we act on, for use
        in converting from matrix to Sheet coordinates.""")


    def __call__(self,x):
        rows,cols = x.shape
        radius = self.density*self.kernel_radius
        crop_radius = int(max(1.25,radius*self.crop_radius_multiplier))

        # find out the matrix coordinates of the winner
        wr,wc = array_argmax(x)

        # convert to sheet coordinates
        wy = rows-wr-1

        # Optimization: Calculate the bounding box around the winner
        # in which weights will be changed
        cmin = max(wc-crop_radius,  0)
        cmax = min(wc+crop_radius+1,cols)
        rmin = max(wr-crop_radius,  0)
        rmax = min(wr+crop_radius+1,rows)
        ymin = max(wy-crop_radius,  0)
        ymax = min(wy+crop_radius+1,rows)
        bb = BoundingBox(points=((cmin,ymin), (cmax,ymax)))

        # generate the kernel matrix and insert it into the correct
        # part of the output array
        kernel = self.neighborhood_kernel_generator(bounds=bb,xdensity=1,ydensity=1,
                                                    size=2*radius,x=wc+0.5,y=wy+0.5)
        x *= 0.0
        x[rmin:rmax,cmin:cmax] = kernel


class HalfRectify(TransferFn):
    """
    Transfer function that applies a half-wave rectification (clips at zero)
    """

    t_init = param.Number(default=0.0,doc="""
        The initial value of threshold at which output becomes non-zero..""")


    gain = param.Number(default=1.0,doc="""
        The neuronal gain""")

    randomized_init = param.Boolean(False,doc="""
        Whether to randomize the initial t parameter.""")

    noise_magnitude =  param.Number(default=0.1,doc="""
        The magnitude of the additive noise to apply to the t_init
        parameter at initialization.""")


    def __init__(self,**params):
        super(TransferFn,self).__init__(**params)
        self.first_call = True


    def __call__(self,x):
        if self.first_call:
            self.first_call = False
            if self.randomized_init:
                self.t = ones(x.shape, x.dtype.char) * self.t_init + \
		(topo.pattern.random.UniformRandom() \
                 (xdensity=x.shape[0],ydensity=x.shape[1])-0.5) * \
                 self.noise_magnitude*2
            else:
                self.t = ones(x.shape, x.dtype.char) * self.t_init

        x -= self.t
        clip_lower(x,0)
        x *= self.gain



class HomeostaticResponse(TransferFnWithState):
    """
    Adapts the parameters of a linear threshold function to maintain a
    constant desired average activity. Defined in:

    Jean-Luc R. Stevens, Judith S. Law, Jan Antolik, and James A. Bednar.
    Mechanisms for stable, robust, and adaptive development of orientation
    maps in the primary visual cortex.
    Journal of Neuroscience 33:15747-15766, 2013.
    http://dx.doi.org/10.1523/JNEUROSCI.1037-13.2013
    """

    t_init = param.Number(default=0.15,doc="""
        Initial value of the threshold value t.""")

    randomized_init = param.Boolean(False,doc="""
        Whether to randomize the initial t parameter.""")

    seed = param.Integer(default=42, doc="""
       Random seed used to control the initial randomized t values.""")

    target_activity = param.Number(default=0.024,doc="""
        The target average activity.""")

    linear_slope = param.Number(default=1.0,doc="""
        Slope of the linear portion above threshold.""")

    learning_rate = param.Number(default=0.01,doc="""
        Learning rate for homeostatic plasticity.""")

    smoothing = param.Number(default=0.991,doc="""
        Weighting of previous activity vs. current activity when
        calculating the average activity.""")

    noise_magnitude =  param.Number(default=0.1,doc="""
        The magnitude of the additive noise to apply to the t_init
        parameter at initialization.""")

    period = param.Number(default=1.0, constant=True, doc="""
        How often the threshold should be adjusted.

        If the period is 0, the threshold is adjusted continuously, each
        time this TransferFn is called.

        For nonzero periods, adjustments occur only the first time
        this TransferFn is called after topo.sim.time() reaches an
        integer multiple of the period.

        For example, if period is 2.5 and the TransferFn is evaluated
        every 0.05 simulation time units, the threshold will be
        adjusted at times 2.55, 5.05, 7.55, etc.""")


    def __init__(self,**params):
        super(HomeostaticResponse,self).__init__(**params)
        self.first_call = True
        self.__current_state_stack=[]
        self.t=None     # To allow state_push at init
        self.y_avg=None # To allow state_push at init

        next_timestamp = topo.sim.time() + self.period
        self._next_update_timestamp = topo.sim.convert_to_time_type(next_timestamp)
        self._y_avg_prev = None
        self._x_prev = None


    def _initialize(self,x):
        self._x_prev = numpy.copy(x)
        self._y_avg_prev = ones(x.shape, x.dtype.char) * self.target_activity

        if self.randomized_init:
            self.t = ones(x.shape, x.dtype.char) * self.t_init + \
                (topo.pattern.random.UniformRandom( \
                    random_generator=numpy.random.RandomState(seed=self.seed)) \
                     (xdensity=x.shape[0],ydensity=x.shape[1]) \
                     -0.5)*self.noise_magnitude*2
        else:
            self.t = ones(x.shape, x.dtype.char) * self.t_init
        self.y_avg = ones(x.shape, x.dtype.char) * self.target_activity


    def _apply_threshold(self,x):
        """Applies the piecewise-linear thresholding operation to the activity."""
        x -= self.t
        clip_lower(x,0)
        if self.linear_slope != 1.0:
            x *= self.linear_slope 


    def _update_threshold(self, prev_t, x, prev_avg, smoothing, learning_rate, target_activity):
        """
        Applies exponential smoothing to the given current activity and previous
        smoothed value following the equations given in the report cited above.

        If plastic is set to False, the running exponential average
        values and thresholds are not updated.
        """
        y_avg = (1.0-smoothing)*x + smoothing*prev_avg
        t = prev_t + learning_rate * (y_avg - target_activity)
        return (y_avg, t) if self.plastic else (prev_avg, prev_t)


    def __call__(self,x):
        """Initialises on the first call and then applies homeostasis."""
        if self.first_call: self._initialize(x); self.first_call = False

        if (topo.sim.time() > self._next_update_timestamp):
            self._next_update_timestamp += self.period
            # Using activity matrix and and smoothed activity from *previous* call.
            (self.y_avg, self.t) = self._update_threshold(self.t, self._x_prev, self._y_avg_prev,
                                                          self.smoothing, self.learning_rate,
                                                          self.target_activity)
            self._y_avg_prev = self.y_avg   # Copy only if not in continuous mode

        self._apply_threshold(x)            # Apply the threshold only after it is updated
        self._x_prev[...,...] = x[...,...]  # Recording activity for the next periodic update


    def state_push(self):
        self.__current_state_stack.append((copy.copy(self.t),
                                           copy.copy(self.y_avg),
                                           copy.copy(self.first_call),
                                           copy.copy(self._next_update_timestamp),
                                           copy.copy(self._y_avg_prev),
                                           copy.copy(self._x_prev)))
        super(HomeostaticResponse, self).state_push()

    def state_pop(self):
        (self.t, self.y_avg, self.first_call, self._next_update_timestamp,
        self._y_avg_prev, self._x_prev) = self.__current_state_stack.pop()
        super(HomeostaticResponse, self).state_pop()



class AttributeTrackingTF(TransferFnWithState):
    """
    Keeps track of attributes of a specified Parameterized over time, for analysis or plotting.

    Useful objects to track include sheets (e.g. "topo.sim['V1']"),
    projections ("topo.sim['V1'].projections['LateralInhibitory']"),
    or an output_function.

    Any attribute whose value is a matrix the same size as the
    activity matrix can be tracked.  Only specified units within this
    matrix will be tracked.

    If no object is specified, this function will keep track of the
    incoming activity over time.

    The results are stored in a dictionary named 'values', as (time,
    value) pairs indexed by the parameter name and unit.  For
    instance, if the value of attribute 'x' is v for unit (0.0,0.0)
    at time t, values['x'][(0.0,0.0)]=(t,v).

    Updating of the tracked values can be disabled temporarily using
    the plastic parameter.
    """

    # ALERT: Need to make this read-only, because it can't be changed
    # after instantiation unless _object is also changed.  Or else
    # need to make _object update whenever object is changed and
    # _object has already been set.
    object = param.Parameter(default=None, doc="""
        Parameterized instance whose parameters will be tracked.

        If this parameter's value is a string, it will be evaluated first
        (by calling Python's eval() function).  This feature is designed to
        allow circular references, so that the TF can track the object that
        owns it, without causing problems for recursive traversal (as for
        script_repr()).""")
    # There may be some way to achieve the above without using eval(), which would be better.
    #JLALERT When using this function snapshots cannot be saved because of problem with eval()

    attrib_names = param.List(default=[], doc="""
        List of names of the function object's parameters that should be stored.""")

    units = param.List(default=[(0.0,0.0)], doc="""
        Sheet coordinates of the unit(s) for which parameter values will be stored.""")

    step = param.Number(default=1, doc="""
        How often to update the tracked values.

        For instance, step=1 means to update them every time this TF is
        called; step=2 means to update them every other time.""")

    coordframe = param.Parameter(default=None,doc="""
        SheetCoordinateSystem to use to convert the position into matrix coordinates.

        If this parameter's value is a string, it will be evaluated
        first(by calling Python's eval() function).  This feature is
        designed to allow circular references, so that the TF can
        track the object that owns it, without causing problems for
        recursive traversal (as for script_repr()).""")

    def __init__(self,**params):
        super(AttributeTrackingTF,self).__init__(**params)
        self.values={}
        self.n_step = 0
        self._object=None
        self._coordframe=None
        for p in self.attrib_names:
            self.values[p]={}
            for u in self.units:
                self.values[p][u]=[]


    def __call__(self,x):

        if self._object==None:
            if isinstance(self.object,str):
                self._object=eval(self.object)
            else:
                self._object=self.object

        if self._coordframe == None:
            if isinstance(self.coordframe,str) and isinstance(self._object,SheetCoordinateSystem):
                raise ValueError(str(self._object)+"is already a coordframe, no need to specify coordframe")
            elif isinstance(self._object,SheetCoordinateSystem):
                self._coordframe=self._object
            elif isinstance(self.coordframe,str):
                self._coordframe=eval(self.coordframe)
            else:
                raise ValueError("A coordinate frame (e.g. coordframe=topo.sim['V1']) must be specified in order to track"+str(self._object))

        #collect values on each appropriate step
        self.n_step += 1

        if self.n_step == self.step:
            self.n_step = 0
            if self.plastic:
                for p in self.attrib_names:
                    if p=="x":
                        value_matrix=x
                    else:
                        value_matrix= getattr(self._object, p)

                    for u in self.units:
                        mat_u=self._coordframe.sheet2matrixidx(u[0],u[1])
                        self.values[p][u].append((topo.sim.time(),value_matrix[mat_u]))



__all__ = list(set([k for k,v in locals().items() if isinstance(v,type) and issubclass(v,TransferFn)]))
__all__.remove("TransferFn")
__all__.remove("TransferFnWithState")

