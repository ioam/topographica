import numpy as np
import param

from topo.sparse.sparsecf import SparseCFProjection, SparseConnectionField

import pycuda.gpuarray as gpuarray
from pycuda.elementwise import ElementwiseKernel
import pycuda.driver as cuda
import pycuda.autoinit
import scikits.cuda.cusparse as cusparse

cusparse.init()


def CFPOF_DivisiveNormalizeL1_Sparse_GPU(projection):
    """
    Divisive normalisation computed on the GPU
    """
    if not projection.has_norm_total:
        projection.weights_gpu.mv(projection.norm_ones_gpu, y=projection.norm_total_gpu, autosync=False)
    
    projection.norm_total_gpu = 1.0/projection.norm_total_gpu

    projection.normalize_kernel(projection.nzrows_gpu, projection.norm_total_gpu, projection.weights_gpu.Val, range=slice(0, projection.nzcount, 1))
    projection.has_norm_total = False


def CFPLF_Hebbian_Sparse_GPU(projection):
    """
    Sparse CF Projection learning function applying Hebbian learning
    to the weights in a projection.
    """
    single_conn_lr = projection.learning_rate/projection.n_units
    # Transfering source and destination activities:
    src_activity_gpu = gpuarray.to_gpu_async(np.ravel(projection.src.activity).astype(np.float32), )
    dest_activity_gpu = gpuarray.to_gpu_async(np.ravel(projection.dest.activity).astype(np.float32), )

    # Computing Hebbian learning weights:
    projection.hebbian_kernel(single_conn_lr, projection.nzrows_gpu, projection.nzcols_gpu, src_activity_gpu, dest_activity_gpu, projection.weights_gpu.Val, range=slice(0, projection.nzcount, 1))

    # Normalisation values:
    projection.weights_gpu.mv(projection.norm_ones_gpu, y=projection.norm_total_gpu, autosync=False)
    projection.has_norm_total = True


def CFPRF_DotProduct_Sparse_GPU(projection):
    """
    Sparse CF Projection response function calculating the dot-product
    between incoming activities and CF weights. Uses GPU.
    """
    projection.input_buffer_pagelocked[:] = np.ravel(projection.input_buffer).astype(np.float32)  
    projection.input_buffer_gpu = gpuarray.to_gpu_async(projection.input_buffer_pagelocked, stream=projection.pycuda_stream)
    projection.weights_gpu.mv(projection.input_buffer_gpu, alpha=projection.strength, y=projection.activity_gpu_buffer, autosync=False, stream=projection.pycuda_stream)
    projection.activity_gpu_buffer.get_async(ary=projection.activity, stream=projection.pycuda_stream)



class GPUSparseCFProjection(SparseCFProjection):
    """
    A projection composed of SparseConnectionFields from a Sheet into
    a ProjectionSheet, calculated using a GPU.

    Any subclass has to implement the interface activate(self) that
    computes the response from the input and stores it in the activity
    array.
    """

    cf_type = param.Parameter(default=SparseConnectionField,doc="""
        Type of ConnectionField to use when creating individual CFs.""")

    learning_fn = param.Callable(default=CFPLF_Hebbian_Sparse_GPU,doc="""
        Function for computing changes to the weights based on one activation step.""")

    response_fn = param.Callable(default=CFPRF_DotProduct_Sparse_GPU,doc="""
        Function for computing the Projection response to an input pattern.""")

    weights_output_fns = param.HookList(default=[CFPOF_DivisiveNormalizeL1_Sparse_GPU],doc="""
        Functions applied to each CF after learning.""")

    initialized = param.Boolean(default=False)


    def __init__(self,**params):

        '''
        Hack-ish way to avoid initialisation until the weights are transfered:
        '''
        should_apply = self.apply_output_fns_init
        params['apply_output_fns_init'] = False

        super(GPUSparseCFProjection,self).__init__(**params)
        # Transfering the weights:
        self.pycuda_stream = cuda.Stream()
        self.weights_gpu = cusparse.CSR.to_CSR(self.weights.toSparseArray().transpose())
        # Getting the row and columns indices for the *transposed* matrix. Used for Hebbian learning and normalisation:
        nzcols, nzrows = self.weights.nonzero()
        tups = sorted(zip(nzrows, nzcols))
        nzrows = [x[0] for x in tups]
        nzcols = [x[1] for x in tups]

        '''
        Allocating a page-locked piece of memory for the activity so that GPU could transfer data to the
        main memory without the involvment of the CPU:
        '''
        self.activity = cuda.pagelocked_empty(self.activity.shape, np.float32)
        self.activity_gpu_buffer = gpuarray.zeros(shape=(self.weights_gpu.shape[0],), dtype=np.float32)

        self.input_buffer_pagelocked = cuda.pagelocked_empty(shape=(self.weights_gpu.shape[1],), dtype=np.float32, mem_flags=cuda.host_alloc_flags.WRITECOMBINED)
        self.input_buffer = gpuarray.zeros(shape=(self.weights_gpu.shape[1], ), dtype=np.float32)

        self.norm_total_gpu = gpuarray.zeros(shape=(self.weights_gpu.shape[0],), dtype=np.float32)

        # Getting them on the GPU:
        self.nzcount = self.weights.getnnz()
        self.nzrows_gpu = gpuarray.to_gpu(np.array(nzrows, np.int32))
        self.nzcols_gpu = gpuarray.to_gpu(np.array(nzcols, np.int32))
        # Helper array for normalization:
        self.norm_ones_gpu = gpuarray.to_gpu(np.array([1.0] * self.weights_gpu.shape[1], np.float32))
        # Kernel that applies the normalisation:
        self.normalize_kernel = ElementwiseKernel(
                        "int *nzrows, float *norm_total, float *weights",
                        "weights[i] *= norm_total[nzrows[i]]",
                        "divisive_normalize")
        # Kernel that calculates the learning:
        self.hebbian_kernel = ElementwiseKernel(
                        "float single_conn_lr, int *row, int *col, float *src_activity, float *dest_activity, float *result",
                        "result[i] += single_conn_lr * src_activity[row[i]] * dest_activity[col[i]]",
                        "hebbian_learning")

        params['apply_output_fns_init'] = should_apply
        self.apply_output_fns_init = should_apply
        if self.apply_output_fns_init:
            self.apply_learn_output_fns()
