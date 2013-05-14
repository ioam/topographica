"""
Basic SparseCFProjection with associated sparse CFs and output,
response, and learning function. If sparse component cannot be imported,
SparseCFProjection will fall back to a basic dense CFProjection.

CFSOF and CFSLF Plugin function allow any single CF output function to
be applied to the sparse CFs, but may suffer a serious performance
loss.  For real work, such functions should be implemented at the
Cython or C++ level.
"""

import numpy as np
import math
from scipy.ndimage.filters import gaussian_filter
import param

from copy import copy

import topo
from topo.base.cf import CFProjection, NullCFError, _create_mask, simple_vectorize
from topo import pattern
from imagen import patterngenerator
from imagen.patterngenerator import PatternGenerator
from topo.base.functionfamily import TransferFn, IdentityTF
from topo.base.functionfamily import LearningFn, Hebbian
from topo.base.functionfamily import ResponseFn, DotProduct
from topo.base.sheetcoords import Slice

use_sparse = True
try:
    import sparse
except:
    use_sparse = False

sparse_type = np.float32


class CFSPLF_Plugin(param.Parameterized):
    """CFSPLearningFunction applying the specified single_cf_fn to each Sparse CF."""

    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),doc="""
        Accepts a LearningFn that will be applied to each CF individually.""")


    def constant_sum_connection_rate(self,n_units,learning_rate):
        """
        Return the learning rate for a single connection assuming that
        the total rate is to be divided evenly among all the units in
        the connection field.
        """
        return float(learning_rate)/n_units


    def __call__(self, projection, **params):
        """Apply the specified single_cf_fn to every sparse CF."""
        single_connection_learning_rate = self.constant_sum_connection_rate(projection.n_units,projection.learning_rate)
        # avoid evaluating these references each time in the loop
        single_cf_fn = self.single_cf_fn

        for cf in projection.flatcfs:
            temp_weights = cf.weights
            single_cf_fn(cf.get_input_matrix(projection.src.activity),
                         projection.dest.activity.flat[cf.oned_idx], temp_weights,
                         single_connection_learning_rate)
            temp_weights *= cf.mask
            cf.weights = temp_weights



class CFSPOF_Plugin(param.Parameterized):
    """
    Applies the specified single_cf_fn to each SparseCF in the SparseCFProjection.
    """

    single_cf_fn = param.ClassSelector(TransferFn,default=IdentityTF(),
        doc="Accepts a TransferFn that will be applied to each CF individually.")


    def __call__(self, projection, **params):
        if type(self.single_cf_fn) is not IdentityTF:
            single_cf_fn = self.single_cf_fn

            for cf in projection.flatcfs:
                temp_weights = cf.weights
                single_cf_fn(cf.weights)
                cf.weights = temp_weights
                del cf.norm_total



class CFSPOF_Prune(CFSPOF_Plugin):
    """
    Prunes specified percentage of connections from CFs in SparseCFProjection
    at specified interval.
    """


    interval = param.Number(default=1000,bounds=(0,None),doc="""
        Time interval at which pruning step will be applied.""")

    percentile = param.Number(default=10.0,bounds=(0,100),doc="""
        Percentile boundary below which connections will be pruned.""")


    def __call__(self, projection, **params):
        time = math.ceil(topo.sim.time())
        if (time == 0):
            if not hasattr(self,"initial_conns"):
                self.initial_conns = {}
            self.initial_conns[projection.name] = projection.n_conns()

        elif (time % self.interval) == 0:
            for cf in projection.flatcfs:
                dim1,dim2 = cf.weights.shape
                temp_weights = cf.weights
                percentile = np.percentile(temp_weights[temp_weights.nonzero()],self.percentile)
                temp_weights[np.where(temp_weights<=percentile)] = 0.0
                cf.weights = temp_weights
            projection.weights.prune()
            self.message("%s has %f%% of initial connections" % (projection.name, (float(projection.n_conns())/self.initial_conns[projection.name])*100))


class CFSPOF_SproutRetract(CFSPOF_Plugin):
    """
    Sprouting and retraction weights output function. At a preset time
    interval, the function removes and adds connections based on a
    piecewise function, which determines the number of connections to
    alter and the sprouting and retraction ratios, eventually allowing
    connections to converge on the target_sparsity. The function
    ensures the full turnover_rate is applied at the maximal distances
    from the target sparsity, i.e. at 0% and 100% density. As the
    projection approaches the target sparsity, it will asymptote, but a
    residual turnover will ensure that a fixed amount of connections
    will continue to sprout and retract.

    Retraction deletes the x lowest weights, while sprouting applies a
    convolution with a Gaussian kernel to the existing connections,
    growing connections at locations with the highest probabilities.

    Still experimental and not scientifically validated.
    """

    interval = param.Number(default=1000,bounds=(0,None),doc="""
        Time interval between sprout/retract steps.""")

    residual_turnover = param.Number(default=0.01,bounds=(0,1.0),doc="""
        Constant turnover rate independent of current sparsity.""")

    turnover_rate = param.Number(default=0.1,bounds=(0,1.0),doc="""
        Percentage of weights to change per interval, assuming
        currently fully dense and target is fully sparse.""")

    target_sparsity = param.Number(default=0.15,bounds=(0,1.0),doc="""
        Sparsity level at which sprouting and retraction cancel out.""")

    kernel_sigma = param.Number(default=1.0,bounds=(0.0,10.0),doc="""
        Gaussian spatial variance for weights to diffuse per interval.""")

    disk_mask = param.Boolean(default=True,doc="""
        Limits connection sprouting to a disk.""")

    def __call__(self, projection, **params):
        time = math.ceil(topo.sim.time())

        if self.disk_mask:
            self.disk = pattern.Disk(size=1.0,smoothing=0.0)

        # Get CF and src sheet shapes
        cf_x,cf_y = projection.dest.activity.shape
        src_x,src_y = projection.src.activity.shape

        # Initialize sparse triplet arrays
        y_array = np.zeros((src_x*src_y*cf_y),dtype=np.int32)
        x_array = np.zeros((src_x*src_y*cf_y),dtype=np.int32)
        val_array = np.zeros((src_x*src_y*cf_y),dtype=sparse_type)

        # Create new sparse matrix to accumulate into
        sum_sparse = sparse.csarray_float(projection.src.activity.shape,projection.dest.activity.shape)

        # Counters for logging
        sprout_sum = 0; prune_sum = 0; unit_total = 0
        self.mask_total = 0

        if (time == 0):
            if not hasattr(self,"initial_conns"):
                self.initial_conns = {}
            self.initial_conns[projection.name] = projection.n_conns()
        elif (time % self.interval) == 0:
            idx=0
            for cidx,cf in enumerate(projection.flatcfs):
                temp_weights = cf.weights
                dense_unit_mask = (1.0 - (temp_weights>0.0))
                dim1,dim2 = temp_weights.shape

                sprout_count,prune_idx,nnz = self.calc_ratios(temp_weights)

                self.prune(temp_weights,prune_idx)
                nnz_pp = np.count_nonzero(temp_weights)
                prune_sum += (nnz_pp-nnz)

                self.sprout(temp_weights,dense_unit_mask,sprout_count)
                nnz_ps = np.count_nonzero(temp_weights)
                sprout_sum += nnz_ps - nnz_pp
                unit_total += nnz_ps

                # Populate sparse array chunk
                temp_sparse = sparse.csarray_float(projection.src.activity.shape,projection.dest.activity.shape)
                x1,x2,y1,y2 = cf.input_sheet_slice.tolist()
                for cnx in range(dim1):
                    val_array[idx:idx+dim2] = temp_weights[cnx,:]
                    x_val = (x1+cnx) * src_y + y1
                    x_array[idx:idx+dim2] = range(x_val,x_val+dim2)
                    y_array[idx:idx+dim2] = cidx
                    idx += dim2

                # Populate combined sparse array with sparse array chunk
                if (cidx+1)%cf_y == 0:
                    nnz_idx = val_array.nonzero()
                    temp_sparse.setTriplets(x_array[nnz_idx],y_array[nnz_idx],val_array[nnz_idx])
                    sum_sparse += temp_sparse
                    x_array *= 0; y_array *= 0; val_array *= 0.0
                    idx=0
            projection.weights = sum_sparse
            del temp_sparse, sum_sparse
            projection.weights.compress()

            self.message("%s pruned by %d and sprouted %d, connection is now %f%% dense" % (projection.name,prune_sum,sprout_sum,(float(unit_total)/self.mask_total)*100))


    def sprout(self, temp_weights, mask, sprout_count):
        """
        Applies a Gaussian blur to the existing connection field,
        selecting the n units with the highest probabilities to sprout
        new connections, where n is set by the sprout_count. New
        connections are initialized at the minimal strength of the
        current CF.
        """

        dim1,dim2 = temp_weights.shape
        init_weight = temp_weights[temp_weights.nonzero()].min()
        blurred_weights = gaussian_filter(temp_weights, sigma=self.kernel_sigma)
        blurred_weights = (blurred_weights - blurred_weights.min()) / blurred_weights.max()
        sprout_prob_map = (blurred_weights * np.random.rand(dim1,dim2)) * mask
        if self.disk_mask:
            sprout_prob_map *= self.disk(xdensity=dim2,ydensity=dim1)
        sprout_inds = np.unravel_index(np.argsort(sprout_prob_map.flatten())[-sprout_count:],(dim1,dim2))
        temp_weights[sprout_inds] = init_weight


    def prune(self, temp_weights, prune_idx):
        """
        Retracts n connections with the lowest weights, where n is
        determined by the piecewise linear function in the calc_ratios
        method.
        """

        sorted_weights = np.sort(temp_weights.flatten())
        threshold = sorted_weights[prune_idx]
        temp_weights[temp_weights < threshold] = 0.0


    def calc_ratios(self,temp_weights):
        """
        Uses a piecewise linear function to determine the unit
        proportion of sprouting and retraction and the associated
        turnover rates.

        Above the target sparsity the sprout/retract ratio scales
        linearly up to maximal density, i.e. at full density 100% of
        the turnover is put into retraction while at full sparsity
        all the turnover is put into sprouting new connections. At
        the target density sprouting and retraction are equal.

        The turnover is determined also determined by the piecewise
        linear function. At maximal distance from the target sparsity,
        i.e. at full sparsity or density, the full turnover rate will
        be used and as the target sparsity is approached from either
        side this term decays to zero. Therefore, a residual turnover
        is introduced to ensure that even at the target sparsity some
        connections continue to sprout and retract.
        """

        dim1,dim2 = temp_weights.shape
        if self.disk_mask:
            masked_units = len(self.disk(xdensity=dim2,ydensity=dim1).nonzero()[0])
        else:
            masked_units = dim1*dim2
        self.mask_total += masked_units
        max_units = dim1*dim2
        nnz = np.count_nonzero(temp_weights)
        cf_sparsity = nnz / float(masked_units)
        delta_sparsity = cf_sparsity - self.target_sparsity
        if delta_sparsity > 0:
            relative_sparsity = delta_sparsity/(1.0 - self.target_sparsity)
        else:
            relative_sparsity = delta_sparsity/self.target_sparsity

        # Total number of units to modify, broken down into units for pruning and sprouting
        delta_units = (abs(self.turnover_rate * relative_sparsity) + self.residual_turnover) * masked_units
        prune_factor = 0.5 + (0.5*relative_sparsity)
        prune_count = int(delta_units * prune_factor)
        prune_idx = (max_units-nnz)+prune_count
        sprout_count = int(delta_units * (1-prune_factor))

        return sprout_count, prune_idx, nnz



class CFSPRF_Plugin(param.Parameterized):
    """
    Generic large-scale response function based on a simple single-CF function.

    Applies the single_cf_fn to each CF in turn.  For the default single_cf_fn
    of DotProduct(), does a basic dot product of each CF with the corresponding
    slice of the input array.  This function is likely to be slow to run, but
    it is easy to extend with any arbitrary single-CF response function.

    The single_cf_fn must be a function f(X,W) that takes two identically
    shaped matrices X (the input) and W (the CF weights) and computes a scalar
    activation value based on those weights.
    """

    single_cf_fn = param.ClassSelector(ResponseFn,default=DotProduct(),doc="""
        Accepts a ResponseFn that will be applied to each CF individually.""")


    def __call__(self, projection, **params):
        single_cf_fn = self.single_cf_fn
        for i,cf in enumerate(projection.flatcfs):
            X = cf.input_sheet_slice.submatrix(projection.src.activity)
            projection.activity.flat[i] = single_cf_fn(X,cf.weights)
        projection.activity *= projection.strength


def compute_sparse_joint_norm_totals(projlist,active_units_mask=True):
    """
    Compute norm_total for each CF in each projection from a group to be
    normalized jointly.
    """

    # Assumes that all Projections in the list have the same r,c size
    assert len(projlist)>=1
    joint_sum = np.zeros(projlist[0].dest.shape,dtype=np.float64)
    for p in projlist:
        if not p.has_norm_total:
            p.norm_total *= 0.0
            p.weights.CFWeightTotals(p.norm_total)
            p.has_norm_total=True
    joint_sum = np.add.reduce([proj.norm_total for proj in projlist],dtype=np.float64)
    for p in projlist:
        p.norm_total = joint_sum.copy()



def CFPOF_DivisiveNormalizeL1_Sparse(projection):
    """
    Sparse CF Projection output function applying L1 divisive normalization
    to individual CFs.
    """

    if not projection.has_norm_total:
        projection.norm_total *= 0.0
        projection.weights.CFWeightTotals(projection.norm_total)
    projection.weights.DivisiveNormalizeL1(projection.norm_total)
    projection.has_norm_total = False



def CFPLF_Hebbian_Sparse(projection):
    """
    Sparse CF Projection learning function applying Hebbian learning
    to the weights in a projection.
    """

    single_conn_lr = projection.learning_rate/projection.n_units
    projection.norm_total *= 0.0
    projection.weights.Hebbian(projection.src.activity,projection.dest.activity,
                               projection.norm_total,single_conn_lr)
    projection.has_norm_total = True


def CFPLF_Hebbian_Sparse_opt(projection):
    """
    Sparse CF Projection learning function, which calls an optimized Hebbian
    learning function while skipping over inactive units.
    """

    single_conn_lr = projection.learning_rate/projection.n_units
    projection.norm_total *= 0.0
    projection.weights.Hebbian_opt(projection.src.activity,projection.dest.activity,
                                   projection.norm_total,single_conn_lr,projection.initialized)
    projection.has_norm_total = True



def CFPRF_DotProduct_Sparse(projection):
    """
    Sparse CF Projection response function calculating the dot-product
    between incoming activities and CF weights.
    """

    projection.weights.DotProduct(projection.strength, projection.input_buffer, projection.activity)


def CFPRF_DotProduct_Sparse_opt(projection):
    """
    Sparse CF Projection response function calculating the dot-product
    between incoming activities and CF weights. Optimization skips
    inactive units if a certain percentage of neurons is inactive.
    """

    nnz_ratio = np.count_nonzero(projection.src.activity) / len(projection.src.activity.flatten())

    if nnz_ratio < 0.1:
        projection.weights.DotProduct_opt(projection.strength, projection.src.activity, projection.activity)
    else:
        projection.weights.DotProduct(projection.strength, projection.src.activity, projection.activity)



class SparseConnectionField(param.Parameterized):
    """
    A set of weights on one input Sheet.

    Each ConnectionField contributes to the activity of one unit on
    the output sheet, and is normally used as part of a Projection
    including many other ConnectionFields.
    """

    # ALERT: need bounds, more docs
    x = param.Number(default=0.0,doc="Sheet X coordinate of CF")

    y = param.Number(default=0.0,doc="Sheet Y coordinate of CF")

    weights_generator = param.ClassSelector(PatternGenerator,
        default=patterngenerator.Constant(),constant=True,doc="""
        Generates initial weights values.""")

    min_matrix_radius=param.Integer(default=1)

    output_fns = param.HookList(default=[],class_=TransferFn,precedence=0.08,doc="""
        Optional function(s) to apply to the pattern array after it has been created.
        Can be used for normalization, thresholding, etc.""")


    def get_bounds(self,input_sheet=None):
        if not input_sheet == None:
            return self.input_sheet_slice.compute_bounds(input_sheet)
        else:
            return self.input_sheet_slice.compute_bounds(self.input_sheet)


    def __get_shape_mask(self):
        cf_shape = self.projection.cf_shape
        bounds = self.projection.bounds_template
        xdensity = self.projection.src.xdensity
        ydensity = self.projection.src.xdensity
        center_r,center_c = self.projection.src.sheet2matrixidx(0,0)
        center_x,center_y = self.projection.src.matrixidx2sheet(center_r,center_c)
        cf_mask = cf_shape(x=center_x,y=center_y,bounds=bounds,xdensity=xdensity,ydensity=ydensity)
        return cf_mask

    shape_mask = property(__get_shape_mask)


    def __get_norm_total(self):
        return self.projection.norm_total[self.matrix_idx[0],self.matrix_idx[1]]

    def __set_norm_total(self,new_norm_total):
        self.projection.norm_total[self.matrix_idx[0],self.matrix_idx[1]] = new_norm_total

    def __del_norm_total(self):
        self.projection.norm_total[self.matrix_idx[0],self.matrix_idx[1]] = 0.0

    norm_total = property(__get_norm_total,__set_norm_total,__del_norm_total)


    def __get_mask(self):
        x1,x2,y1,y2 = self.input_sheet_slice.tolist()
        mask = np.zeros((x2-x1,y2-y1),dtype=np.bool)
        inds = np.ravel_multi_index(np.mgrid[x1:x2,y1:y2],self.projection.src.shape).flatten()
        nz_flat = self.projection.weights[inds,self.oned_idx].toarray()
        nz_inds = nz_flat.reshape(x2-x1,y2-y1).nonzero()
        mask[nz_inds] = True
        return mask

    mask = property(__get_mask,
        """
        The mask property returns an array of bools representing the
        zero weights in the CF weights array.

        It is useful when applying additive functions on the weights
        array, to ensure zero values are not accidentally overwritten.

        The mask cannot be changed via the property, only by changing
        the weights directly.
        """)


    def __get_weights(self):
        """
        get_weights accesses the sparse CF matrix and returns the CF
        in dense form.
        """

        x1,x2,y1,y2 = self.src_slice
        inds = np.ravel_multi_index(np.mgrid[x1:x2,y1:y2],self.projection.src.shape).flatten()
        return self.projection.weights[inds,self.oned_idx].toarray().reshape(x2-x1,y2-y1)

    def __set_weights(self,arr):
        """
        Takes an input array, which has to match the CF shape, and
        creates an mgrid of the appropriate size, adds the proper
        offsets and passes the values and indices to the sparse matrix
        representation.
        """

        x1,x2,y1,y2 = self.src_slice
        (dim1,dim2) = arr.shape
        assert (dim1,dim2) == (x2-x1,y2-y1), "Array does not match CF shape."
        (x,y) = np.mgrid[0:dim1,0:dim2] # Create mgrid of CF size
        x_ind = np.array(x)+x1; y_ind = np.array(y) + y1; # Add slice offsets
        row_inds = np.ravel_multi_index((x_ind,y_ind),self.projection.src.shape).flatten().astype(np.int32)
        col_inds = np.array([self.oned_idx]*len(row_inds),dtype=np.int32)
        self.projection.weights.put(arr[x,y].flatten(),row_inds,col_inds)

    weights = property(__get_weights,__set_weights)


    def __init__(self,template,input_sheet,projection,**params):
        """
        Initializes the CF object and stores meta information about the CF's
        shape and position in the SparseCFProjection to allow for easier
        initialization.
        """

        super(SparseConnectionField,self).__init__(**params)

        self.input_sheet = input_sheet
        self.projection = projection

        self.matrix_idx = self.projection.dest.sheet2matrixidx(self.x,self.y)
        self.oned_idx = self.matrix_idx[0] * self.projection.dest.shape[1] + self.matrix_idx[1]

        template = copy(template)

        if not isinstance(template,Slice):
            template = Slice(template,self.input_sheet,force_odd=True,
                             min_matrix_radius=self.min_matrix_radius)
        self.weights_slice = self._create_input_sheet_slice(template)

        self.src_slice = tuple(self.input_sheet_slice.tolist())


    def _init_weights(self,mask_template):

        if not hasattr(mask_template,'view'):
            mask = _create_mask(mask_template,self.weights_slice.compute_bounds(self.input_sheet),self.input_sheet,True,0.5)

        mask = self.weights_slice.submatrix(mask_template)
        mask = np.array(mask,copy=1)

        w = self.weights_generator(x=self.x,y=self.y,bounds=self.get_bounds(self.input_sheet),
                                   xdensity=self.input_sheet.xdensity,
                                   ydensity=self.input_sheet.ydensity,
                                   mask=mask)

        w = w.astype(sparse_type)

        for of in self.output_fns:
            of(w)

        return w


    def _create_input_sheet_slice(self,template):
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
        input_sheet_slice.positionedcrop(self.x,self.y,self.input_sheet)
        input_sheet_slice.crop_to_sheet(self.input_sheet)

        # weights matrix cannot have a zero-sized dimension (could
        # happen at this stage because of cropping)
        nrows,ncols = input_sheet_slice.shape_on_sheet()
        if nrows<1 or ncols<1:
            raise NullCFError(self.x,self.y,self.input_sheet,nrows,ncols)

        self.input_sheet_slice = input_sheet_slice

        # not copied because we don't use again
        template.positionlesscrop(self.x,self.y,self.input_sheet)
        return template


    def get_input_matrix(self, activity):
        return self.input_sheet_slice.submatrix(activity)



class SparseCFProjection(CFProjection):
    """
    A projection composed of SparseConnectionFields from a Sheet into
    a ProjectionSheet.

    SparseCFProjection computes its activity using a response_fn which
    can either be an optimized function implemented as part of the
    sparse matrix class or an unoptimized function, which requests the
    weights in dense format.  The initial contents of the
    SparseConnectionFields mapping from the input Sheet into the
    target ProjectionSheet are controlled by the weights_generator,
    cf_shape, and weights_output_fn parameters, while the location of
    the ConnectionField is controlled by the coord_mapper parameter.

    Any subclass has to implement the interface activate(self) that
    computes the response from the input and stores it in the activity
    array.
    """

    cf_type = param.Parameter(default=SparseConnectionField,doc="""
        Type of ConnectionField to use when creating individual CFs.""")

    learning_fn = param.Callable(default=CFPLF_Hebbian_Sparse,doc="""
        Function for computing changes to the weights based on one activation step.""")

    response_fn = param.Callable(default=CFPRF_DotProduct_Sparse,doc="""
        Function for computing the Projection response to an input pattern.""")

    weights_output_fns = param.HookList(default=[CFPOF_DivisiveNormalizeL1_Sparse],doc="""
        Functions applied to each CF after learning.""")

    initialized = param.Boolean(default=False)


    def __init__(self,initialize_cfs=True,**params):
        """
        Initialize the Projection with a set of cf_type objects
        (typically SparseConnectionFields), each located at the
        location in the source sheet corresponding to the unit in the
        target sheet. The cf_type objects are stored in the 'cfs'
        array.

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

        self.activity = np.array(self.dest.activity)
        self.norm_total = np.array(self.dest.activity,dtype=np.float64)
        self.has_norm_total = False

        if initialize_cfs:
            self._create_cfs()

        self.input_buffer = None


    def __getstate__(self):
        """
        Method to support pickling of sparse weights object.
        """

        state_dict = self.__dict__.copy()
        state_dict['triplets'] = state_dict['weights'].getTriplets()
        state_dict['weight_shape'] = (self.src.activity.shape,self.dest.activity.shape)
        del state_dict['weights']
        return state_dict


    def __setstate__(self,state_dict):
        """
        Method to support unpickling of sparse weights object.
        """

        self.__dict__.update(state_dict)
        self.weights = sparse.csarray_float(self.weight_shape[0],self.weight_shape[1])
        rowInds, colInds, values = self.triplets
        self.weights.setTriplets(rowInds,colInds,values)
        del self.triplets
        del self.weight_shape


    def _create_cfs(self):
        """
        Creates the CF objects, initializing the weights one by one
        and adding them to the sparse weights object in chunks.
        """

        vectorized_create_cf = simple_vectorize(self._create_cf)
        self.cfs = vectorized_create_cf(*self._generate_coords())
        self.flatcfs = list(self.cfs.flat)
        self.weights = sparse.csarray_float(self.src.activity.shape,self.dest.activity.shape)

        cf_x,cf_y = self.dest.activity.shape
        src_x,src_y = self.src.activity.shape

        y_array = np.zeros((src_x*src_y*cf_y),dtype=np.int32)
        x_array = np.zeros((src_x*src_y*cf_y),dtype=np.int32)
        val_array = np.zeros((src_x*src_y*cf_y),dtype=np.float32)

        # Iterate over the CFs
        for x in range(cf_x):
            temp_sparse = sparse.csarray_float(self.src.activity.shape,self.dest.activity.shape)
            idx = 0
            for y in range(cf_y):
                x1,x2,y1,y2 = self.cfs[x][y].input_sheet_slice.tolist()
                if self.same_cf_shape_for_all_cfs:
                    mask_template = self.mask_template
                else:
                    mask_template = _create_mask(self.cf_shape,self.bounds_template,
                                                 self.src,self.autosize_mask,
                                                 self.mask_threshold)
                weights = self.cfs[x][y]._init_weights(mask_template)
                cn_x,cn_y = weights.shape
                y_val = x * cf_y + y
                for cnx in range(cn_x):
                    val_array[idx:idx+cn_y] = weights[cnx,:]
                    x_val = (x1+cnx) * src_y + y1
                    x_array[idx:idx+cn_y] = range(x_val,x_val+cn_y)
                    y_array[idx:idx+cn_y] = y_val
                    idx += cn_y
            nnz_idx = val_array.nonzero()
            temp_sparse.setTriplets(x_array[nnz_idx],y_array[nnz_idx],val_array[nnz_idx])
            self.weights += temp_sparse
            x_array *= 0; y_array *= 0; val_array *= 0.0
        del temp_sparse
        self.weights.compress()
        self.apply_learn_output_fns()
        print self.name , "loaded"


    def _create_cf(self,x,y):
        """
        Create a ConnectionField at x,y in the src sheet.
        """

        try:
            CF = self.cf_type(template=self._slice_template,projection=self,input_sheet=self.src,x=x,y=y,
                              weights_generator=self.weights_generator,
                              min_matrix_radius=self.min_matrix_radius)
        except NullCFError:
            if self.allow_null_cfs:
                CF = None
            else:
                raise

        return CF


    def activate(self,input_activity):
        """Activate using the specified response_fn and output_fn."""
        if self.input_fns:
            input_activity = input_activity.copy()
        for iaf in self.input_fns:
            iaf(input_activity)
        self.input_buffer = input_activity
        self.activity *=0.0
        self.response_fn(self)
        for of in self.output_fns:
            of(self.activity)


    def learn(self):
        """
        For a SparseCFProjection, learn consists of calling the learning_fn.
        """
        # Learning is performed if the input_buffer has already been set,
        # i.e. there is an input to the Projection.
        if self.input_buffer != None:
            self.learning_fn(self)


    def apply_learn_output_fns(self,active_units_mask=True):
        """
        Apply the weights_output_fns to each unit.
        """
        for of in self.weights_output_fns: of(self)


    def n_bytes(self):
        """
        Estimates the size on the basis of the number non-zeros in the
        sparse matrix, asssuming indices and values are stored using
        32-bit integers and floats respectively.
        """
        return self.n_conns() * (3 * 4)


    def n_conns(self):
        """
        Returns number of nonzero weights.
        """
        return self.weights.getnnz()


if not use_sparse:
    print "WARNING: Sparse component could not be imported, replacing SparseCFProjection with regular CFProjection"
    def SparseCFProjection(*args, **kwargs): # pyflakes:ignore (optimized version provided)
        return CFProjection(*args,**kwargs)
