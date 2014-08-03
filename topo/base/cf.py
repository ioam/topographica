"""
ConnectionField and associated classes.

This module defines some basic classes of objects used to create
simulations of cortical sheets that take input through connection
fields that project from other cortical sheets (or laterally from
themselves).

ConnectionField: Holds a single connection field within a
CFProjection.

CFProjection: A set of ConnectionFields mapping from a Sheet into a
ProjectionSheet.

CFSheet: A subclass of ProjectionSheet that provides an interface to
the underlying ConnectionFields in any projection of type
CFProjection.
"""


from copy import copy
import numpy as np

import param
from dataviews import CoordinateGrid, Dimension
from dataviews.collector import AttrTree
from dataviews.ndmapping import AttrDict
from dataviews.sheetviews import BoundingBox, BoundingRegionParameter, Slice

import patterngenerator
from patterngenerator import PatternGenerator
from functionfamily import TransferFn,IdentityTF
from functionfamily import LearningFn,Hebbian,IdentityLF
from functionfamily import ResponseFn,DotProduct
from functionfamily import CoordinateMapperFn,IdentityMF
from projection import Projection,ProjectionSheet
from sheetview import CFView, CFStack


def simple_vectorize(fn,num_outputs=1,output_type=object,doc=''):
    """
    Wrapper for Numpy.vectorize to make it work properly with different Numpy versions.
    """

    # Numpy.vectorize returns a callable object that applies the given
    # fn to a list or array.  By default, Numpy.vectorize will call
    # the supplied fn an extra time to determine the output types,
    # which is a big problem for any function with side effects.
    # Supplying arguments is supposed to avoid the problem, but as of
    # Numpy 1.6.1 (and apparently since at least 1.1.1) this feature
    # was broken:
    #
    # $ ./topographica -c "def f(x): print x" -c "import numpy" -c "numpy.vectorize(f,otypes=numpy.sctype2char(object)*1)([3,4])"
    # 3
    # 3
    # 4
    #
    # Numpy 1.7.0 seems to fix the problem:
    # $ ./topographica -c "def f(x): print x" -c "import numpy" -c "numpy.vectorize(f,otypes=numpy.sctype2char(object)*1)([3,4])"
    # 3
    # 4
    #
    # To make it work with all versions of Numpy, we use
    # numpy.vectorize as-is for versions > 1.7.0, and a nasty hack for
    # previous versions.

    # Simple Numpy 1.7.0 version:
    if int(np.version.version[0]) >= 1 and int(np.version.version[2]) >= 7:
        return np.vectorize(fn,otypes=np.sctype2char(output_type)*num_outputs, doc=doc)

    # Otherwise, we have to mess with Numpy's internal data structures to make it work.
    vfn = np.vectorize(fn,doc=doc)
    vfn.nout=num_outputs # number of outputs of fn
    output_typecode = np.sctype2char(output_type)
    vfn.otypes=output_typecode*num_outputs # typecodes of outputs of fn
    import inspect

    try:
        fn_code = fn.func_code if hasattr(fn,'func_code') else fn.__call__.func_code
    except:
        raise TypeError("Couldn't find code of %s"%fn)

    fn_args = inspect.getargs(fn_code)[0]
    extra = 1 if fn_args[0]=='self' else 0
    vfn.lastcallargs=len(fn_args)-extra # num args of fn
    return vfn



#: Specified explicitly when creating weights matrix - required
#: for optimized C functions.
weight_type = np.float32


class NullCFError(ValueError):
    """
    Error thrown when trying to create an empty CF.
    """
    def __init__(self,x,y,input,rows,cols):
        ValueError.__init__(self,"ConnectionField at (%s,%s) (input_sheet=%s) has a zero-sized weights matrix (%s,%s); you may need to supply a larger bounds_template or increase the density of the sheet."%(x,y,input,rows,cols))


class ConnectionField(object):
    """
    A set of weights on one input Sheet.

    Each ConnectionField contributes to the activity of one unit on
    the output sheet, and is normally used as part of a Projection
    including many other ConnectionFields.
    """
    __slots__ = ['weights','input_sheet_slice','mask',
                 '_has_norm_total','_norm_total']

    def __get_norm_total(self):
        """
        Return the stored norm_value, if any, or else the current sum of the weights.
        See the norm_total property for more details.
        """
        # The actual value is cached in _norm_total.
        if self._has_norm_total[0]>0:
            return self._norm_total[0]
        else:
            # CEBALERT: what was I playing with for this before?
            return np.sum(np.abs(self.weights),dtype=np.float64)

    def __set_norm_total(self,new_norm_total):
        """
        Set an explicit value to be returned by norm_total.
        See the norm_total property for more details.
        """
        self._has_norm_total[0] = 1
        self._norm_total[0] = new_norm_total

    def __del_norm_total(self):
        """
        Delete any cached norm_total that may have been set.
        See the norm_total property for more details.
        """
        self._has_norm_total[0] = 0


    # CB: Accessing norm_total as a property from the C code takes
    # about 2% of run time for 90 iterations of lissom_oo_or. (As of
    # r8139, using floating-point simulation time.)
    norm_total = property(__get_norm_total,__set_norm_total,__del_norm_total,
        """
        The norm_total property returns a value useful in computing
        a sum-based weight normalization.

        By default, the value returned is simply the current sum of
        the connection weights.  However, another value can be
        substituted by setting norm_total explicitly, and this cached
        value will then be returned instead.

        This mechanism has two main purposes.  First, it allows a
        learning function to cache the sum value for an output
        function to use later without computation, which can result in
        significant time savings.  Second, the extra level of
        indirection allows the sum value to be manipulated before it
        is used, to implement operations like joint normalization
        across corresponding CFs in multiple Projections.

        Apart from such cases, norm_total can be ignored.

        Note that every person who uses a class that sets or gets
        norm_total must be very careful to ensure that stale values
        will never be accessed.  A good way to do this is to make sure
        that the value is only set just before it will be used, and
        deleted as soon as it has been accessed.

        WARNING: Any c-optimized code can bypass this property and
        access directly _has_norm_total, _norm_total

        """)


    def get_bounds(self,input_sheet):
        return self.input_sheet_slice.compute_bounds(input_sheet)

    # Class attribute to switch to legacy weight generation if False
    independent_weight_generation = True

    # CEBALERT:
    # template and mask: usually created ONCE by CFProjection and
    # specified as a Slice and array (respectively). Otherwise,
    # can be specified as BoundingBox and patterngenerator.

    # Note that BoundingBox() is ok for a default even though it's
    # mutable because we copy it inside init.  Constant() is ok too
    # because mask and weights_generator are not modified.
    def __init__(self,input_sheet,x=0.0,y=0.0,template=BoundingBox(radius=0.1),
                 weights_generator=patterngenerator.Constant(),
                 mask=patterngenerator.Constant(),
                 output_fns=None,min_matrix_radius=1, label=None):
        """
        Create weights at the specified (x,y) location on the
        specified input_sheet.

        The supplied template (if a BoundingRegion) is converted to a
        Slice, moved to the specified (x,y) location, and then the
        weights pattern is drawn inside by the weights_generator.

        Note that if the appropriate template Slice is already known,
        then it can be passed in instead of a BoundingRegion template.
        This slice will then be used directly, instead of converting
        the template into a Slice.

        The supplied template object itself will not be modified (it
        is copied before use).

        The mask allows the weights to be limited to being non-zero in
        a subset of the rectangular weights area.  The actual mask
        used is a view of the given mask created by cropping to the
        boundaries of the input_sheet, so that the weights all
        correspond to actual locations in the input sheet.  For
        instance, if a circular pattern of weights is desired, the
        mask should have a disk-shaped pattern of elements with value
        1, surrounded by elements with the value 0.  If the CF extends
        over the edge of the input sheet then the weights will
        actually be half-moon (or similar) rather than circular.
        """
        #print "Create CF",input_sheet.name,x,y,"template=",template,"wg=",weights_generator,"m=",mask,"ofs=",output_fns,"min r=",min_matrix_radius

        template = copy(template)

        if not isinstance(template,Slice):
            template = Slice(template,input_sheet,force_odd=True,
                             min_matrix_radius=min_matrix_radius)

        # Note: if passed in, mask is shared between CFs (but not if created here)
        if not hasattr(mask,'view'):
            mask = _create_mask(mask,template.compute_bounds(input_sheet),
        # CEBALERT: it's not really worth adding more ALERTs on this
        # topic, but...there's no way for the CF to control autosize
        # and threshold.
                               input_sheet,True,0.5)


        # CB: has to be set for C code. Can't be initialized at the
        # class level, or it would become a read-only class attribute
        # (because it's a slot:
        # http://docs.python.org/reference/datamodel.html). Can we
        # somehow avoid having to think about _has_norm_total in the
        # python code? Could the C code initialize this value?
        self._has_norm_total=np.array([0],dtype=np.int32)
        self._norm_total=np.array([0.0],dtype=np.float64)

        if output_fns is None:
            output_fns = []

        # CEBALERT: now even more confusing; weights_slice is
        # different from input_sheet_slice. At least need to rename.
        weights_slice = self._create_input_sheet_slice(input_sheet,x,y,template,min_matrix_radius)

        # CBNOTE: this would be clearer (but not perfect, and probably slower)
        # m = mask_template[self.weights_slice()]
        self.mask = weights_slice.submatrix(mask)  # view of original mask
        self.mask = np.array(self.mask,copy=1) # CEBALERT: why is this necessary?

        # (without it, optimized learning function creates artifacts in CFs at
        # left and right edges of sheet, at some densities)

        # CBENHANCEMENT: might want to do something about a size
        # that's specified (right now the size is assumed to be that
        # of the bounds)
        # shouldn't be extra computation of boundingbox because it's gone from Slice.__init__; could avoid extra lookups by getting straight from slice

        pattern_params = dict(x=x,y=y,bounds=self.get_bounds(input_sheet),
                              xdensity=input_sheet.xdensity,
                              ydensity=input_sheet.ydensity,
                              mask=self.mask)

        controlled_weights = (param.Dynamic.time_dependent
                              and isinstance(param.Dynamic.time_fn, param.Time)
                              and self.independent_weight_generation)

        if controlled_weights:
            with param.Dynamic.time_fn as t:
                t(0)                        # Initialize weights at time zero.
                # Controls random streams
                name = "%s_CF (%.5f, %.5f)" % ('' if label is None else label, x,y)
                w = weights_generator(**dict(pattern_params, name=name))
        else:
            w = weights_generator(**pattern_params)


        # CEBALERT: unnecessary copy! Pass type to PG & have it draw
        # in that.  (Should be simple, except making it work for all
        # the PG subclasses that override array creation in various
        # ways (producing or using inconsistent types) turned out to
        # be too painful.)
        self.weights = w.astype(weight_type)

        # CEBHACKALERT: the system of masking through multiplication
        # by 0 works for now, while the output_fns are all
        # multiplicative.  But in the long run we need a better way to
        # apply the mask.  The same applies anywhere the mask is used,
        # including in learningfn/. We should investigate masked
        # arrays (from numpy).
        for of in output_fns:
            of(self.weights)


    # CB: can this be renamed to something better?
    def _create_input_sheet_slice(self,input_sheet,x,y,template,min_matrix_radius):
        """
        Create the input_sheet_slice, which provides the appropriate
        Slice for this CF on the input_sheet (as well as providing
        this CF's exact bounds).

        Also creates the weights_slice, which provides the Slice for
        this weights matrix (in case it must be cropped at an edge).
        """
        # copy required because the template gets modified here but
        # needs to be used again
        input_sheet_slice = copy(template)
        input_sheet_slice.positionedcrop(x,y,input_sheet)
        input_sheet_slice.crop_to_sheet(input_sheet)

        # weights matrix cannot have a zero-sized dimension (could
        # happen at this stage because of cropping)
        nrows,ncols = input_sheet_slice.shape_on_sheet()
        if nrows<1 or ncols<1:
            raise NullCFError(x,y,input_sheet,nrows,ncols)

        self.input_sheet_slice = input_sheet_slice

        # not copied because we don't use again
        template.positionlesscrop(x,y,input_sheet)
        return template


    # CEBALERT: unnecessary method; can use something like
    # activity[cf.input_sheet_slice()]
    def get_input_matrix(self, activity):
        # CBNOTE: again, this might be clearer (but probably slower):
        # activity[self.input_sheet_slice()]
        return self.input_sheet_slice.submatrix(activity)



class CFPResponseFn(param.Parameterized):
    """
    Map an input activity matrix into an output matrix using the CFs
    in a CFProjection.

    Objects in this hierarchy of callable function objects compute a
    response matrix when given an input pattern and a set of
    ConnectionField objects.  Typically used as part of the activation
    function for a neuron, computing activation for one Projection.

    Objects in this class must support being called as a function with
    the arguments specified below, and are assumed to modify the
    activity matrix in place.
    """
    __abstract=True

    def __call__(self, iterator, input_activity, activity, strength, **params):
        raise NotImplementedError


class CFPRF_Plugin(CFPResponseFn):
    """
    Generic large-scale response function based on a simple single-CF function.

    Applies the single_cf_fn to each CF in turn.  For the default
    single_cf_fn of DotProduct(), does a basic dot product of each CF with the
    corresponding slice of the input array.  This function is likely
    to be slow to run, but it is easy to extend with any arbitrary
    single-CF response function.

    The single_cf_fn must be a function f(X,W) that takes two
    identically shaped matrices X (the input) and W (the
    ConnectionField weights) and computes a scalar activation value
    based on those weights.
    """
    single_cf_fn = param.ClassSelector(ResponseFn,default=DotProduct(),
        doc="Accepts a ResponseFn that will be applied to each CF individually.")

    def __call__(self, iterator, input_activity, activity, strength):
        single_cf_fn = self.single_cf_fn
        for cf,i in iterator():
            X = cf.input_sheet_slice.submatrix(input_activity)
            activity.flat[i] = single_cf_fn(X,cf.weights)
        activity *= strength


class CFPLearningFn(param.Parameterized):
    """
    Compute new CFs for a CFProjection based on input and output activity values.

    Objects in this hierarchy of callable function objects compute a
    new set of CFs when given input and output patterns and a set of
    ConnectionField objects.  Used for updating the weights of one
    CFProjection.

    Objects in this class must support being called as a function with
    the arguments specified below.
    """
    __abstract = True


    def constant_sum_connection_rate(self,n_units,learning_rate):
        """
        Return the learning rate for a single connection assuming that
        the total rate is to be divided evenly among all the units in
        the connection field.
        """
        return float(learning_rate)/n_units


    # JABALERT: Should the learning_rate be a parameter of this object instead of an argument?
    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        """
        Apply this learning function to the given set of ConnectionFields,
        and input and output activities, using the given learning_rate.
        """
        raise NotImplementedError


class CFPLF_Identity(CFPLearningFn):
    """CFLearningFunction performing no learning."""
    single_cf_fn = param.ClassSelector(LearningFn,default=IdentityLF(),constant=True)

    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        pass


class CFPLF_Plugin(CFPLearningFn):
    """CFPLearningFunction applying the specified single_cf_fn to each CF."""
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),
        doc="Accepts a LearningFn that will be applied to each CF individually.")
    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        """Apply the specified single_cf_fn to every CF."""
        single_connection_learning_rate = self.constant_sum_connection_rate(iterator.proj_n_units,learning_rate)
        # avoid evaluating these references each time in the loop
        single_cf_fn = self.single_cf_fn

        for cf,i in iterator():
            single_cf_fn(cf.get_input_matrix(input_activity),
                         output_activity.flat[i], cf.weights,
                         single_connection_learning_rate)
            cf.weights *= cf.mask


class CFPOutputFn(param.Parameterized):
    """
    Type for an object that applies some operation (typically something
    like normalization) to all CFs in a CFProjection for which the specified
    mask (typically the activity at the destination of this projection)
    is nonzero.
    """
    __abstract = True

    def __call__(self, iterator, **params):
        """Operate on each CF for which the mask is nonzero."""
        raise NotImplementedError


class CFPOF_Plugin(CFPOutputFn):
    """
    Applies the specified single_cf_fn to each CF in the CFProjection
    for which the mask is nonzero.
    """
    single_cf_fn = param.ClassSelector(TransferFn,default=IdentityTF(),
        doc="Accepts a TransferFn that will be applied to each CF individually.")

    def __call__(self, iterator, **params):
        if type(self.single_cf_fn) is not IdentityTF:
            single_cf_fn = self.single_cf_fn

            for cf,i in iterator():
                single_cf_fn(cf.weights)
                del cf.norm_total


class CFPOF_Identity(CFPOutputFn):
    """
    CFPOutputFn that leaves the CFs unchanged.

    Must never be changed or subclassed, because it might never
    be called. (I.e., it could simply be tested for and skipped.)
    """
    single_cf_fn = param.ClassSelector(TransferFn,default=IdentityTF(),constant=True)

    def __call__(self, iterator, **params):
        pass


# CB: need to make usage of 'src' and 'input_sheet' consistent between
# ConnectionField and CFProjection (i.e. pick one of them).
class CFProjection(Projection):
    """
    A projection composed of ConnectionFields from a Sheet into a ProjectionSheet.

    CFProjection computes its activity using a response_fn of type
    CFPResponseFn (typically a CF-aware version of mdot) and output_fns
    (typically none).  The initial contents of the
    ConnectionFields mapping from the input Sheet into the target
    ProjectionSheet are controlled by the weights_generator, cf_shape,
    and weights_output_fn parameters, while the location of the
    ConnectionField is controlled by the coord_mapper parameter.

    Any subclass has to implement the interface
    activate(self,input_activity) that computes the response from the
    input and stores it in the activity array.
    """

    response_fn = param.ClassSelector(CFPResponseFn,
        default=CFPRF_Plugin(),
        doc='Function for computing the Projection response to an input pattern.')

    input_fns = param.HookList(default=[],class_=TransferFn,doc="""
        Function(s) applied to the input before the projection activity is computed.""")

    cf_type = param.Parameter(default=ConnectionField,constant=True,
        doc="Type of ConnectionField to use when creating individual CFs.")

    # JPHACKALERT: Not all support for null CFs has been implemented.
    # CF plotting and C-optimized CFPxF_ functions need
    # to be fixed to support null CFs without crashing.
    allow_null_cfs = param.Boolean(default=False,
        doc="Whether or not the projection can have entirely empty CFs")

    nominal_bounds_template = BoundingRegionParameter(
        default=BoundingBox(radius=0.1),doc="""
        Bounds defining the Sheet area covered by a prototypical ConnectionField.
        The true bounds will differ depending on the density (see create_slice_template()).""")

    weights_generator = param.ClassSelector(PatternGenerator,
        default=patterngenerator.Constant(),constant=True,
        doc="Generate initial weights values.")

    cf_shape = param.ClassSelector(PatternGenerator,
        default=patterngenerator.Constant(),constant=True,
        doc="Mask pattern to define the shape of the connection fields.")

    same_cf_shape_for_all_cfs = param.Boolean(default=True,doc="""
        Whether or not to share a single cf_shape mask for all CFs.
        If True, the cf_shape is evaluated only once and shared for
        all CFs, which saves computation time and memory.  If False,
        the cf_shape is evaluated once for each CF, allowing each to
        have its own shape.""")

    learning_fn = param.ClassSelector(CFPLearningFn,
        default=CFPLF_Plugin(),
        doc='Function for computing changes to the weights based on one activation step.')

    # JABALERT: Shouldn't learning_rate be owned by the learning_fn?
    learning_rate = param.Number(default=0.0,softbounds=(0,100),doc="""
        Amount of learning at each step for this projection, specified
        in units that are independent of the density of each Sheet.""")

    weights_output_fns = param.HookList(default=[CFPOF_Plugin()],
        class_=CFPOutputFn,
        doc='Functions applied to each CF after learning.')

    strength = param.Number(default=1.0,doc="""
        Global multiplicative scaling applied to the Activity of this Sheet.""")

    coord_mapper = param.ClassSelector(CoordinateMapperFn,
        default=IdentityMF(),
        doc='Function to map a projected coordinate into the target sheet.')

    # CEBALERT: this is temporary (allows c++ matching in certain
    # cases).  We will allow the user to override the mask size, but
    # by offering a scaling parameter.
    autosize_mask = param.Boolean(
        default=True,constant=True,precedence=-1,doc="""
        Topographica sets the mask size so that it is the same as the connection field's
        size, unless this parameter is False - in which case the user-specified size of
        the cf_shape is used. In normal usage of Topographica, this parameter should
        remain True.""")

    mask_threshold = param.Number(default=0.5,constant=True,doc="""
        If a unit is above this value in the cf_shape mask, it is
        included; otherwise it is excluded from the mask.""")

    apply_output_fns_init=param.Boolean(default=True,doc="""
        Whether to apply the output function to connection fields (e.g. for
        normalization) when the CFs are first created.""")

    min_matrix_radius = param.Integer(default=1,bounds=(0,None),doc="""
        Enforced minimum for radius of weights matrix.
        The default of 1 gives a minimum matrix of 3x3. 0 would
        allow a 1x1 matrix.""")

    hash_format = param.String(default="{name}-{src}-{dest}", doc="""
       Format string to determine the hash value used to initialize
       random weight generation. Format keys available include {name}
       {src} and {dest}.""")

    precedence = param.Number(default=0.8)


    def __init__(self,initialize_cfs=True,**params):
        """
        Initialize the Projection with a set of cf_type objects
        (typically ConnectionFields), each located at the location
        in the source sheet corresponding to the unit in the target
        sheet. The cf_type objects are stored in the 'cfs' array.

        The nominal_bounds_template specified may be altered: the
        bounds must be fitted to the Sheet's matrix, and the weights
        matrix must have odd dimensions. These altered bounds are
        passed to the individual connection fields.

        A mask for the weights matrix is constructed. The shape is
        specified by cf_shape; the size defaults to the size
        of the nominal_bounds_template.
        """
        super(CFProjection,self).__init__(**params)

        self.weights_generator.set_dynamic_time_fn(None,sublistattr='generators')
        # get the actual bounds_template by adjusting a copy of the
        # nominal_bounds_template to ensure an odd slice, and to be
        # cropped to sheet if necessary
        self._slice_template = Slice(copy(self.nominal_bounds_template),
                                     self.src,force_odd=True,
                                     min_matrix_radius=self.min_matrix_radius)

        self.bounds_template = self._slice_template.compute_bounds(self.src)

        self.mask_template = _create_mask(self.cf_shape,self.bounds_template,
                                         self.src,self.autosize_mask,
                                         self.mask_threshold)

        self.n_units = self._calc_n_units()

        if initialize_cfs:
            self._create_cfs()

        if self.apply_output_fns_init:
            self.apply_learn_output_fns(active_units_mask=False)

        ### JCALERT! We might want to change the default value of the
        ### input value to self.src.activity; but it fails, raising a
        ### type error. It probably has to be clarified why this is
        ### happening
        self.input_buffer = None
        self.activity = np.array(self.dest.activity)
        if 'cfs' not in self.dest.views:
            self.dest.views.CFs = AttrTree()
        self.dest.views.CFs[self.name] = self._cf_grid()


    def _cf_grid(self, shape=None, **kwargs):
        "Create ProjectionGrid with the correct metadata."
        grid = CoordinateGrid(self.dest.bounds, None,
                              xdensity=self.dest.xdensity,
                              ydensity=self.dest.ydensity)
        grid.metadata = AttrDict(timestamp=self.src.simulation.time(),
                                 info=self.name,
                                 proj_src_name=self.src.name,
                                 proj_dest_name=self.dest.name,
                                 **kwargs)
        return grid


    def _generate_coords(self):
        X,Y = self.dest.sheetcoords_of_idx_grid()
        vectorized_coord_mapper = simple_vectorize(self.coord_mapper,
                                                   num_outputs=2,
                                                   # CB: could switch to float32?
                                                   output_type=float)
        return vectorized_coord_mapper(X,Y)


    # CB: should be _initialize_cfs() since we already have 'initialize_cfs' flag?
    def _create_cfs(self):
        vectorized_create_cf = simple_vectorize(self._create_cf)
        self.cfs = vectorized_create_cf(*self._generate_coords())
        self.flatcfs = list(self.cfs.flat)


    def _create_cf(self,x,y):
        """
        Create a ConnectionField at x,y in the src sheet.
        """
        # (to restore would need to have an r,c counter)
        # self.debug("Creating CF(%d,%d) from src (%.3f,%.3f) to  dest (%.3f,%.3f)"%(r,c,x_cf,y_cf,x,y))

        try:
            if self.same_cf_shape_for_all_cfs:
                mask_template = self.mask_template
            else:
                mask_template = _create_mask(self.cf_shape,self.bounds_template,
                                             self.src,self.autosize_mask,
                                             self.mask_threshold)
            label = self.hash_format.format(name=self.name,
                                            src=self.src.name,
                                            dest=self.dest.name)

            CF = self.cf_type(self.src, x=x, y=y,
                              template=self._slice_template,
                              weights_generator=self.weights_generator,
                              mask=mask_template,
                              min_matrix_radius=self.min_matrix_radius,
                              label = label)
        except NullCFError:
            if self.allow_null_cfs:
                CF = None
            else:
                raise

        return CF


    def _calc_n_units(self):
        """Return the number of unmasked units in a typical ConnectionField."""

        return min(len(self.mask_template.ravel().nonzero()[0]),
                   # CEBALERT: if the mask_template is bigger than the
                   # src sheet (e.g.  conn radius bigger than src
                   # radius), return the size of the source sheet
                   self.src.shape[0]*self.src.shape[1])


    def cf(self,r,c):
        """Return the specified ConnectionField"""
        # CB: should we offer convenience cf(x,y) (i.e. sheetcoords) method instead?
        self.warning("CFProjection.cf(r,c) is deprecated: use cfs[r,c] instead")
        return self.cfs[r,c]


    def cf_bounds(self,r,c):
        """Return the bounds of the specified ConnectionField."""
        return self.cfs[r,c].get_bounds(self.src)


    def grid(self, rows=11, cols=11, lbrt=None, situated=False, **kwargs):
        xdensity, ydensity = self.dest.xdensity, self.dest.ydensity
        l, b, r, t = self.dest.bounds.lbrt()
        half_x_unit = ((r-l) / xdensity) / 2.
        half_y_unit = ((t-b) / ydensity) / 2.
        if lbrt is None:
            bounds = self.dest.bounds
            l, b, r, t = (l+half_x_unit, b+half_y_unit, r-half_x_unit, t-half_y_unit)
        else:
            l, b = self.dest.closest_cell_center(lbrt[0], lbrt[1])
            r, t = self.dest.closest_cell_center(lbrt[2], lbrt[3])
            bounds = BoundingBox(points=[(l-half_x_unit, b-half_y_unit),
                                         (r+half_x_unit, t+half_y_unit)])
        x, y = np.meshgrid(np.linspace(l, r, cols),
                           np.linspace(b, t, rows))
        coords = zip(x.flat, y.flat)

        grid_items = {}
        for x, y in coords:
            grid_items[x, y] = self.view(x, y, situated=situated, **kwargs)

        grid = CoordinateGrid(bounds, (cols, rows), initial_items=grid_items,
                              title=' '.join([self.dest.name, self.name, '{label}']),
                              label='CFs')
        grid.metadata = AttrDict(info=self.name,
                                 proj_src_name=self.src.name,
                                 proj_dest_name=self.dest.name,
                                 timestamp=self.src.simulation.time(),
                                 **kwargs)
        return grid


    def view(self, sheet_x, sheet_y, timestamp=None, situated=False, **kwargs):
        """
        Return a single connection field SheetView, for the unit
        located nearest to sheet coordinate (sheet_x,sheet_y).
        """
        if timestamp is None:
            timestamp = self.src.simulation.time()
        time_dim = Dimension("Time", type=param.Dynamic.time_fn.time_type)
        (r, c) = self.dest.sheet2matrixidx(sheet_x, sheet_y)
        cf = self.cfs[r, c]
        r1, r2, c1, c2 = cf.input_sheet_slice
        situated_shape = self.src.activity.shape
        situated_bounds = self.src.bounds
        roi_bounds = cf.get_bounds(self.src)
        if situated:
            matrix_data = np.zeros(situated_shape, dtype=np.float64)
            matrix_data[r1:r2, c1:c2] = cf.weights.copy()
            bounds = situated_bounds
        else:
            matrix_data = cf.weights.copy()
            bounds = roi_bounds

        sv = CFView(matrix_data, bounds, situated_bounds=situated_bounds,
                    input_sheet_slice=(r1, r2, c1, c2), roi_bounds=roi_bounds,
                    label=self.name+ " CF Weights", value='CF Weight')
        sv.metadata=AttrDict(timestamp=timestamp)

        cfstack = CFStack((timestamp, sv), dimensions=[time_dim])
        cfstack.metadata = AttrDict(coords=(sheet_x, sheet_y),
                                    dest_name=self.dest.name,
                                    precedence=self.src.precedence, proj_name=self.name,
                                    src_name=self.src.name,
                                    row_precedence=self.src.row_precedence,
                                    timestamp=timestamp, **kwargs)
        return cfstack


    def get_view(self, sheet_x, sheet_y, timestamp=None):
        self.warning("Deprecated, call 'view' method instead.")
        return self.view(sheet_x, sheet_y, timestamp)


    def activate(self,input_activity):
        """Activate using the specified response_fn and output_fn."""
        if self.input_fns:
            input_activity = input_activity.copy()
        for iaf in self.input_fns:
            iaf(input_activity)
        self.input_buffer = input_activity
        self.activity *=0.0
        self.response_fn(CFIter(self), input_activity, self.activity, self.strength)
        for of in self.output_fns:
            of(self.activity)


    # CEBALERT: should add active_units_mask to match
    # apply_learn_output_fns.
    def learn(self):
        """
        For a CFProjection, learn consists of calling the learning_fn.
        """
        # Learning is performed if the input_buffer has already been set,
        # i.e. there is an input to the Projection.
        if self.input_buffer != None:
            self.learning_fn(CFIter(self),self.input_buffer,self.dest.activity,self.learning_rate)


    # CEBALERT: called 'learn' output fns here, but called 'weights' output fns
    # elsewhere (mostly). Change all to 'learn'?
    def apply_learn_output_fns(self,active_units_mask=True):
        """
        Apply the weights_output_fns to each unit.

        If active_units_mask is True, inactive units will be skipped.
        """
        for of in self.weights_output_fns:
            of(CFIter(self,active_units_mask=active_units_mask))


    # CEBALERT: see gc alert in simulation.__new__
    def _cleanup(self):
        for cf in self.cfs.flat:
            # cf could be None or maybe something else
            if hasattr(cf,'input_sheet'):
                cf.input_sheet=None
            if hasattr(cf,'input_sheet_slice'):
                cf.input_sheet_slice=None
            if hasattr(cf,'weights_slice'):
                cf.weights_slice=None


    def n_bytes(self):
        # Could also count the input_sheet_slice
        rows,cols=self.cfs.shape
        return super(CFProjection,self).n_bytes() + \
               sum([cf.weights.nbytes +
                    cf.mask.nbytes
                    for cf,i in CFIter(self,ignore_sheet_mask=True)()])


    def n_conns(self):
        # Counts non-masked values, if mask is available; otherwise counts
        # weights as connections if nonzero
        rows,cols=self.cfs.shape
        return np.sum([len((cf.mask if cf.mask is not None else cf.weights).ravel().nonzero()[0])
                    for cf,i in CFIter(self)()])


# CEB: have not yet decided proper location for this method
# JAB: should it be in PatternGenerator?
def _create_mask(shape,bounds_template,sheet,autosize=True,threshold=0.5):
    """
    Create the mask (see ConnectionField.__init__()).
    """
    # Calculate the size & aspect_ratio of the mask if appropriate;
    # mask size set to be that of the weights matrix
    if hasattr(shape, 'size') and autosize:
        l,b,r,t = bounds_template.lbrt()
        shape.size = t-b
        shape.aspect_ratio = (r-l)/shape.size

    # Center mask to matrixidx center
    center_r,center_c = sheet.sheet2matrixidx(0,0)
    center_x,center_y = sheet.matrixidx2sheet(center_r,center_c)

    mask = shape(x=center_x,y=center_y,
                 bounds=bounds_template,
                 xdensity=sheet.xdensity,
                 ydensity=sheet.ydensity)

    mask = np.where(mask>=threshold,mask,0.0)

    # CB: unnecessary copy (same as for weights)
    return mask.astype(weight_type)



class CFIter(object):
    """
    Iterator to walk through all ConnectionFields of all neurons in
    the destination Sheet of the given CFProjection.  Each iteration
    yields the tuple (cf,i) where cf is the ConnectionField at
    position i in the projection's flatcfs list.

    If active_units_mask is True, inactive units will be skipped. If
    ignore_sheet_mask is True, even units excluded by the sheet mask
    will be included.
    """

    # CB: as noted elsewhere, rename active_units_mask (to e.g.
    # ignore_inactive_units).
    def __init__(self,cfprojection,active_units_mask=False,ignore_sheet_mask=False):

        self.flatcfs = cfprojection.flatcfs
        self.activity = cfprojection.dest.activity
        self.mask = cfprojection.dest.mask
        self.cf_type = cfprojection.cf_type
        self.proj_n_units = cfprojection.n_units
        self.allow_skip_non_responding_units = cfprojection.dest.allow_skip_non_responding_units

        self.active_units_mask = active_units_mask
        self.ignore_sheet_mask = ignore_sheet_mask

    def __nomask(self):
        # return an array indicating all units should be processed

        # dtype for C functions.
        # could just be flat.
        return np.ones(self.activity.shape,dtype=self.activity.dtype)

    # CEBALERT: make _
    def get_sheet_mask(self):
        if not self.ignore_sheet_mask:
            return self.mask.data
        else:
            return self.__nomask()

    # CEBALERT: make _ (and probably drop '_mask').
    def get_active_units_mask(self):
        if self.allow_skip_non_responding_units and self.active_units_mask:
            return self.activity
        else:
            return self.__nomask()

    # CEBALERT: rename?
    def get_overall_mask(self):
        """
        Return an array indicating whether or not each unit should be
        processed.
        """
        # JPHACKALERT: Should really check for the existence of the
        # mask, rather than checking its type. This is a hack to
        # support higher-order projections whose dest is a CF, instead
        # of a sheet.  The right thing to do is refactor so that CF
        # masks and  SheetMasks are subclasses of an abstract Mask
        # type so that they support the same interfaces.
        #
        # CEBALERT: put back when supporting neighborhood masking
        # (though preferably do what Jeff suggests instead)
#        if isinstance(self.proj.dest.mask,SheetMask):
#            return get_active_units_mask()
#        else:

        # CB: note that it's faster for our optimized C functions to
        # combine the masks themselves, rather than using this method.
        sheet_mask = self.get_sheet_mask()
        active_units_mask = self.get_active_units_mask()
        return np.logical_and(sheet_mask,active_units_mask)


    def __call__(self):
        mask = self.get_overall_mask()
        for i,cf in enumerate(self.flatcfs):
            if cf is not None:
                if mask.flat[i]:
                    yield cf,i


# PRALERT: CFIter Alias for backwards compatability with user code
# Should be removed before release v1.0
MaskedCFIter = CFIter

### We don't really need this class; its methods could probably be
### moved up to ProjectionSheet, because they may in fact be valid for
### all ProjectionSheets. But we're leaving it here, because it is
### likely to be useful in the future.
class CFSheet(ProjectionSheet):
    """
    A ProjectionSheet providing access to the ConnectionFields in its CFProjections.

    CFSheet is a Sheet built from units indexed by Sheet coordinates
    (x,y).  Each unit can have one or more ConnectionFields on another
    Sheet (via this sheet's CFProjections).  Thus CFSheet is a more
    concrete version of a ProjectionSheet; a ProjectionSheet does not
    require that there be units or weights of any kind.  Unless you
    need access to the underlying ConnectionFields for visualization
    or analysis, CFSheet and ProjectionSheet are interchangeable.
    """

    measure_maps = param.Boolean(True,doc="""
        Whether to include this Sheet when measuring various maps to create SheetViews.""")

    precedence = param.Number(0.5)


    def update_unit_view(self,x,y,proj_name=''):
        """
        Creates the list of UnitView objects for a particular unit in this CFSheet.
        (There is one UnitView for each Projection to this CFSheet).

        Each UnitView is then added to the sheet_views of its source sheet.
        It returns the list of all UnitViews for the given unit.
        """
        for p in self.in_connections:
            if not isinstance(p,CFProjection):
                self.debug("Skipping non-CFProjection "+p.name)
            elif proj_name == '' or p.name==proj_name:
                v = p.view(x, y, self.simulation.time())
                cfs = self.views.CFs
                if p.name not in cfs:
                    cfs[p.name] = p._cf_grid()
                cfs[p.name][x, y] = v




class ResizableCFProjection(CFProjection):
    """
    A CFProjection with resizable weights.
    """
    # Less efficient memory usage than CFProjection because it stores
    # the (x,y) position of each ConnectionField.


    def _generate_coords(self):
        # same as super's, but also stores the coords.

        # CB: this is storing redundant info because generate_coords()
        # returns output from mgrid. Might be better to store the 1d x
        # and y coords, and generate the grids when needed?
        self.X_cf,self.Y_cf = super(ResizableCFProjection,self)._generate_coords()
        return self.X_cf,self.Y_cf


    ### This could be changed into a special __set__ method for
    ### bounds_template, instead of being a separate function, but
    ### having it be explicit like this might be clearer.
    ###
    ### This implementation is fairly slow, and for some algorithms
    ### that rely on changing the bounds frequently, it may be worth
    ### re-implementing it in C.
    def change_bounds(self, nominal_bounds_template):
        """
        Change the bounding box for all of the ConnectionFields in this Projection.

        Calls change_bounds() on each ConnectionField.

        Currently only allows reducing the size, but should be
        extended to allow increasing as well.
        """
        slice_template = Slice(copy(nominal_bounds_template),
                               self.src,force_odd=True,
                               min_matrix_radius=self.min_matrix_radius)

        bounds_template = slice_template.compute_bounds(self.src)

        if not self.bounds_template.containsbb_exclusive(bounds_template):
            if self.bounds_template.containsbb_inclusive(bounds_template):
                self.debug('Initial and final bounds are the same.')
            else:
                self.warning('Unable to change_bounds; currently allows reducing only.')
            return

        # it's ok so we can store the bounds and resize the weights
        mask_template = _create_mask(self.cf_shape,bounds_template,self.src,
                                     self.autosize_mask,self.mask_threshold)

        self.mask_template = mask_template
        self.n_units = self._calc_n_units()
        self.nominal_bounds_template = nominal_bounds_template

        self.bounds_template = bounds_template
        self._slice_template = slice_template

        cfs = self.cfs
        rows,cols = cfs.shape
        output_fns = [wof.single_cf_fn for wof in self.weights_output_fns]

        for r in xrange(rows):
            for c in xrange(cols):
                xcf,ycf = self.X_cf[0,c],self.Y_cf[r,0]
                # CB: listhack - loop is candidate for replacement by numpy fn
                self._change_cf_bounds(cfs[r,c],input_sheet=self.src,
                                       x=xcf,y=ycf,
                                       template=slice_template,
                                       mask=mask_template,
                                       output_fns=output_fns,
                                       min_matrix_radius=self.min_matrix_radius)


    def change_density(self, new_wt_density):
        """
        Rescales the weight matrix in place, interpolating or resampling as needed.

        Not yet implemented.
        """
        raise NotImplementedError


    def _change_cf_bounds(self,cf,input_sheet,x,y,template,mask,output_fns=None,min_matrix_radius=1):
        """
        Change the bounding box for this ConnectionField.

        Discards weights or adds new (zero) weights as necessary,
        preserving existing values where possible.

        Currently only supports reducing the size, not increasing, but
        should be extended to support increasing as well.

        Note that the supplied template will be modified, so if you're
        also using them elsewhere you should pass copies.
        """
        if output_fns is None:
            output_fns = []

        # CEBALERT: re-write to allow arbitrary resizing
        or1,or2,oc1,oc2 = cf.input_sheet_slice

        weights_slice = cf._create_input_sheet_slice(input_sheet,x,y,copy(template),min_matrix_radius)

        r1,r2,c1,c2 = cf.input_sheet_slice


        if not (r1 == or1 and r2 == or2 and c1 == oc1 and c2 == oc2):
            # CB: note that it's faster to copy (i.e. replacing copy=1 with copy=0
            # below slows down change_bounds().
            cf.weights = np.array(cf.weights[r1-or1:r2-or1,c1-oc1:c2-oc1],copy=1)
            # (so the obvious choice,
            # cf.weights=cf.weights[r1-or1:r2-or1,c1-oc1:c2-oc1],
            # is also slower).

            cf.mask = weights_slice.submatrix(mask)
            cf.mask = np.array(cf.mask,copy=1) # CB: why's this necessary?
                                                # (see ALERT in __init__)
            cf.weights *= cf.mask
            for of in output_fns:
                of(cf.weights)
            del cf.norm_total
