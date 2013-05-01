"""
Projection classes.

A Projection is a connection between two Sheets, generally implemented
as a large set of ConnectionFields.

Any new Projection classes added to this directory will automatically
become available for any model.
"""

from copy import copy

import numpy as np

import param

# So all Projections are present in this package
from topo.base.projection import Projection
from topo.base.boundingregion import BoundingBox
from topo.base.sheet import activity_type
from topo.base.sheetcoords import Slice
from topo.base.cf import CFProjection,ConnectionField,\
     CFPLearningFn,CFPLF_Identity,CFPOutputFn,CFIter,ResizableCFProjection
from topo.base.patterngenerator import PatternGenerator,Constant
from topo.base.functionfamily import CoordinateMapperFn,IdentityMF
from topo.misc.util import rowcol2idx
from topo.transferfn import TransferFn,IdentityTF
from topo.learningfn import LearningFn,IdentityLF
from topo.base import patterngenerator

class CFPOF_SharedWeight(CFPOutputFn):
    """
    CFPOutputFn for use with SharedWeightCFProjections.

    Applies the single_cf_fn to the single shared CF's weights.
    """
    single_cf_fn = param.ClassSelector(TransferFn,default=IdentityTF())

    # CEBALERT: remove norm_values?
    def __call__(self, cfs, norm_values=None, **params):
        """Apply the specified single_cf_fn to every CF."""
        if type(self.single_cf_fn) is not IdentityTF:
            cf = cfs[0,0]
            self.single_cf_fn(cf.weights)

from topo.base.cf import _create_mask

class SharedWeightCF(ConnectionField):

    __slots__ = []

    def __init__(self,cf,input_sheet,x=0.0,y=0.0,template=BoundingBox(radius=0.1),
                 mask=patterngenerator.Constant(),
                 min_matrix_radius=1):
        """
        From an existing copy of ConnectionField (CF) that acts as a
        template, create a new CF that shares weights with the
        template CF.  Copies all the properties of CF to stay
        identical except the weights variable that actually contains
        the data.

        The only difference from a normal CF is that the weights of
        the CF are implemented as a numpy view into the single master
        copy of the weights stored in the CF template.
        """
        # CEBALERT: There's no call to super's __init__; see JAHACKALERT
        # below.
        template = copy(template)

        if not isinstance(template,Slice):
            template = Slice(template,input_sheet,force_odd=True,
                             min_matrix_radius=min_matrix_radius)

        # Note: if passed in, mask is shared between CFs (but not if created here)
        if not hasattr(mask,'view'):
            mask = _create_mask(patterngenerator.Constant(),
                               template.compute_bounds(input_sheet),
                               input_sheet,True,0.5)



        self._has_norm_total=np.array([0],dtype=np.int32)
        self._norm_total=np.array([0.0],dtype=np.float64)

        self.mask=mask
        weights_slice = self._create_input_sheet_slice(input_sheet,x,y,template,min_matrix_radius=min_matrix_radius)
        self.weights = weights_slice.submatrix(cf.weights)

        # JAHACKALERT the TransferFn cannot be applied in SharedWeightCF
        # - another inconsistency in the class tree design - there
        # should be nothing in the parent class that is ignored in its
        # children.  Probably need to extract some functionality of
        # ConnectionField into a shared abstract parent class.
        # We have agreed to make this right by adding a constant property that
        # will be set true if the learning should be active
        # The SharedWeightCFProjection class and its anccestors will
        # have this property set to false which means that the
        # learning will be deactivated



class SharedWeightCFProjection(CFProjection):
    """
    A Projection with a single set of weights, shared by all units.

    Otherwise similar to CFProjection, except that learning is
    currently disabled.
    """
    ### JABHACKALERT: Set to be constant as a clue that learning won't
    ### actually work yet, but we could certainly extend it to support
    ### learning if desired, e.g. to learn position-independent responses.
    learning_fn = param.ClassSelector(CFPLearningFn,CFPLF_Identity(),constant=True)
    weights_output_fns = param.HookList(default=[CFPOF_SharedWeight()])
    precedence = param.Number(default=0.5)

    def __init__(self,**params):
        """
        Initialize the Projection with a single cf_type object
        (typically a ConnectionField),
        """
        # We don't want the whole set of cfs initialized, but we
        # do want anything that CFProjection defines.
        super(SharedWeightCFProjection,self).__init__(initialize_cfs=False,**params)

        # We want the sharedcf to be located on the grid, so use the
        # center of a unit
        sheet_rows,sheet_cols=self.src.shape
        # arbitrary (e.g. could use 0,0)
        center_row,center_col = sheet_rows/2,sheet_cols/2
        center_unitxcenter,center_unitycenter=self.src.matrixidx2sheet(center_row,
                                                                       center_col)


        self.__sharedcf=self.cf_type(self.src,
                                     x=center_unitxcenter,
                                     y=center_unitycenter,
                                     template=self._slice_template,
                                     weights_generator=self.weights_generator,
                                     mask=self.mask_template,
                                     output_fns=[wof.single_cf_fn for wof in self.weights_output_fns],
                                     min_matrix_radius=self.min_matrix_radius)

        self._create_cfs()



    def _create_cf(self,x,y):
        # Does not pass the mask, as it would have to be sliced
        # for each cf, and is only used for learning.
        CF = SharedWeightCF(self.__sharedcf,self.src,x=x,y=y,
                            template=self._slice_template,
                            min_matrix_radius=self.min_matrix_radius,
                            mask=self.mask_template)

        return CF


    def learn(self):
        """
        Because of how output functions are applied, it is not currently
        possible to use learning functions and learning output functions for
        SharedWeightCFProjections, so we disable them here.
        """
        pass


    def apply_learn_output_fns(self,active_units_mask=True):
        """
        Because of how output functions are applied, it is not currently
        possible to use learning functions and learning output functions for
        SharedWeightCFProjections, so we disable them here.
        """
        pass


    def n_bytes(self):
        return self.activity.nbytes + self.__sharedcf.weights.nbytes + \
               sum([cf.input_sheet_slice.nbytes
                    for cf,i in CFIter(self)()])





# JABALERT: Can this be replaced with a CFProjection with a Hysteresis output_fn?
# If not it should probably be replaced with a new output_fn type instead.
class LeakyCFProjection(ResizableCFProjection):
    """
    A projection that has a decay_rate parameter so that incoming
    input is decayed over time as x(t) = input + x(t-1)*exp(-decay_rate),
    and then the weighted sum of x(t) is calculated.
    """

    decay_rate = param.Number(default=1.0,bounds=(0,None),
                        doc="Input decay rate for each leaky synapse")

    precedence = param.Number(default=0.4)

    def __init__(self,**params):
        super(LeakyCFProjection,self).__init__(**params)
        self.leaky_input_buffer = np.zeros(self.src.activity.shape)

    def activate(self,input_activity):
        """
        Retain input_activity from the previous step in leaky_input_buffer
        and add a leaked version of it to the current input_activity. This
        function needs to deal with a finer time-scale.
        """
        self.leaky_input_buffer = input_activity + self.leaky_input_buffer*np.exp(-self.decay_rate)
        super(LeakyCFProjection,self).activate(self.leaky_input_buffer)

    def n_bytes(self):
        return super(LeakyCFProjection,self).n_bytes() + \
               self.activity.nbytes*1 # for leaky_input_buffer


class ScaledCFProjection(CFProjection):
    """
    Allows scaling of activity based on a specified target average activity.

    An exponentially weighted average is used to calculate the average
    activity.  This average is then used to calculate scaling factors
    for the current activity and for the learning rate.

    The plastic parameter can be used to turn off updating of the average
    activity, e.g. during map measurement.
    """

    target = param.Number(default=0.045, doc="""Target average activity for the projection.""")

    target_lr = param.Number(default=0.045, doc="""
        Target average activity for scaling the learning rate.""")

    smoothing = param.Number(default=0.999, doc="""
        Influence of previous activity, relative to current, for computing the average.""")
    precedence = param.Number(default=0.4)

    def __init__(self,**params):
        # JABALERT: Private variables should be prefixed __ (truly private) or _ (nominally private)
        # Are all of these really something you expect people to be using outside this class?
        super(ScaledCFProjection,self).__init__(**params)
        self.x_avg=None
        self.sf=None
        self.lr_sf=None
        self.scaled_x_avg=None


    def calculate_sf(self):
        """
        Calculate current scaling factors based on the target and previous average activities.

        Keeps track of the scaled average for debugging. Could be
        overridden by a subclass to calculate the factors differently.
        """

        if self.plastic:
            self.sf *=0.0
            self.lr_sf *=0.0
            self.sf += self.target/self.x_avg
            self.lr_sf += self.target_lr/self.x_avg
            self.x_avg = (1.0-self.smoothing)*self.activity + self.smoothing*self.x_avg
            self.scaled_x_avg = (1.0-self.smoothing)*self.activity*self.sf + self.smoothing*self.scaled_x_avg


    def do_scaling(self):
        """
        Scale the projection activity and learning rate for the projection.
        """
        self.activity *= self.sf
        if hasattr(self.learning_fn,'learning_rate_scaling_factor'):
            self.learning_fn.update_scaling_factor(self.lr_sf)
        else:
            raise ValueError("Projections to be called must have learning function which supports scaling (e.g. CFPLF_PluginScaled).")


    def activate(self,input_activity):
        """Activate using the specified response_fn and output_fn."""
        self.input_buffer = input_activity
        self.activity *=0.0

        if self.x_avg is None:
            self.x_avg=self.target*np.ones(self.dest.shape, activity_type)
        if self.scaled_x_avg is None:
            self.scaled_x_avg=self.target*np.ones(self.dest.shape, activity_type)
        if self.sf is None:
            self.sf=np.ones(self.dest.shape, activity_type)
        if self.lr_sf is None:
            self.lr_sf=np.ones(self.dest.shape, activity_type)

        self.response_fn(CFIter(self), input_activity, self.activity, self.strength)
        for of in self.output_fns:
            of(self.activity)
        self.calculate_sf()
        self.do_scaling()


    def n_bytes(self):
        return super(ScaledCFProjection,self).n_bytes() + \
               self.activity.nbytes*4 # for x_avg,sf,lr_sf,scaled_x_avg



class OneToOneProjection(Projection):
    """
    A projection that has at most one input connection for each unit.

    This projection has exactly one weight for each destination unit.
    The input locations on the input sheet are determined by a
    coordinate mapper.  Inputs that map outside the bounds of the
    input sheet are treated as having zero weight.
    """
    coord_mapper = param.ClassSelector(CoordinateMapperFn,
        default=IdentityMF(),
        doc='Function to map a destination unit coordinate into the src sheet.')

    weights_generator = param.ClassSelector(PatternGenerator,
        default=Constant(),constant=True,
        doc="""Generate initial weight values for each unit of the destination sheet.""")

    learning_fn = param.ClassSelector(LearningFn,default=IdentityLF(),
        doc="""Learning function applied to weights.""")

    learning_rate = param.Number(default=0)


    def __init__(self,**kw):
        super(OneToOneProjection,self).__init__(**kw)

        self.input_buffer = None

        dx,dy = self.dest.bounds.centroid()

        # JPALERT: Not sure if this is the right way to generate weights.
        # For full specificity, each initial weight should be dependent on the
        # coordinates of both the src unit and the dest unit.
        self.weights = self.weights_generator(bounds=self.dest.bounds,
                                              xdensity=self.dest.xdensity,
                                              ydensity=self.dest.ydensity)


        # JPALERT: CoordMapperFns should really be made to take
        # matrices of x/y points and apply their mapping to all.  This
        # could give great speedups, esp for AffineTransform mappings,
        # which can be applied to many points with a single matrix
        # multiplication.
        srccoords = [self.coord_mapper(x,y)
                     for y in reversed(self.dest.sheet_rows())
                     for x in self.dest.sheet_cols()]

        self.src_idxs = np.array([rowcol2idx(r,c,self.src.activity.shape)
                               for r,c in (self.src.sheet2matrixidx(u,v)
                                           for u,v in srccoords)])

        # dest_idxs contains the indices of the dest units whose weights project
        # in bounds on the src sheet.
        src_rows,src_cols = self.src.activity.shape
        def in_bounds(x,y):
            r,c = self.src.sheet2matrixidx(x,y)
            return (0 <= r < src_rows) and (0 <= c < src_cols)
        destmask = [in_bounds(x,y) for x,y in srccoords]

        # The [0] is required because numpy.nonzero returns the
        # nonzero indices wrapped in a one-tuple.
        self.dest_idxs = np.nonzero(destmask)[0]
        self.src_idxs = self.src_idxs.take(self.dest_idxs)
        assert len(self.dest_idxs) == len(self.src_idxs)

        self.activity = np.zeros(self.dest.shape,dtype=float)

    def activate(self,input):
        self.input_buffer = input
        result = self.weights.take(self.dest_idxs) * input.take(self.src_idxs) * self.strength
        self.activity.put(self.dest_idxs,result)
        for of in self.output_fns:
            of(self.activity)

    def learn(self):
        if self.input_buffer is not None:
            self.learning_fn(self.input_buffer,
                             self.dest.activity,
                             self.weights,
                             self.learning_rate)

    def n_conns(self):
        rows,cols=self.activity.shape
        return rows*cols

    def n_bytes(self):
        return super(OneToOneProjection,self).n_bytes() + \
               self.activity.nbytes


_public = list(set([_k for _k,_v in locals().items()
                    if isinstance(_v,type) and issubclass(_v,Projection)]))
_public += [
    "CFPOF_SharedWeight",
    "SharedWeightCF",
]

# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = _public + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch
