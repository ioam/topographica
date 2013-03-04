# distutils: language = c++

"""
Cython wrapper of Eigen3 subclass (used to extend standard sparse
functionality) for sparse implementation. Implements Topographica
specific functionality (e.g. DivisiveNormalizationL1, DotProduct and
Hebbian learning). Also supplies interface for initializing, reading
and writing sparse matrices. Further, methods to prune and compress
the sparse matrix are available.
"""

from cython.operator cimport dereference as deref
from cpython cimport bool
import numpy
cimport numpy
import cython

cdef extern from "SparseMatrixExt.cpp":
    cdef cppclass SparseMatrixExt[T]:
        SparseMatrixExt()
        SparseMatrixExt(SparseMatrixExt[T])
        SparseMatrixExt(int, int)
        int cols()
        int nonZeros()
        int rows()
        int size()
        T coeff(int, int)
        SparseMatrixExt[T] add(SparseMatrixExt[T]&)
        void nonZeroInds(long*, long*)
        void insertVal(int, int, T)
        void makeCompressed()
        void iterNonZero(int*, int*, float*)
        void DotProduct(int,double,double*,double*)
        void DotProduct_opt(int,double,double*,double*)
        void Hebbian(double*,double*,double*,double)
        void Hebbian_opt(double*,double*,double*,double)
        void DivisiveNormalizeL1(double*)
        void DivisiveNormalizeL1_opt(double*,double*)
        void CFWeightTotals(double*)
        void setTriplets(int*,int*,float*,int)
        void reserve(int)
        void slice(int*, int, int*, int, SparseMatrixExt[T]*)
        void prune(float,float)

cdef class csarray_float:
    cdef SparseMatrixExt[float] *thisPtr
    cdef tuple src_dim, dest_dim
    cdef int x,y


    def __cinit__(self, src_dim, dest_dim):
        """
        Create a new column major dynamic array.
        """
        if isinstance(src_dim,tuple):
            self.src_dim = src_dim
            self.dest_dim = dest_dim
            self.thisPtr = new SparseMatrixExt[float](src_dim[0]*src_dim[1],dest_dim[0]*dest_dim[1])
        else:
            self.x = src_dim
            self.y = dest_dim
            self.thisPtr = new SparseMatrixExt[float](self.x,self.y)


    def __dealloc__(self):
        """
        Deallocate the SparseMatrixExt object.
        """
        del self.thisPtr


    def __getNDim(self):
        """
        Return the number of dimensions of this array.
        """
        return 2


    def __getShape(self):
        """
        Return the shape of this array (rows, cols)
        """
        return (self.thisPtr.rows(), self.thisPtr.cols())


    def __getSize(self):
        """
        Return the size of this array, that is rows*cols
        """
        return self.thisPtr.size()


    def getnnz(self):
        """
        Return the number of non-zero elements in the array
        """
        return self.thisPtr.nonZeros()


    def __setitem__(self, inds, val):
        """
        Set elements of the array. If i,j = inds are integers then the corresponding
        value in the array is set.
        """
        i, j = inds

        if type(i) == numpy.ndarray and type(j) == numpy.ndarray:
            self.put(val, i, j)
        else:
            i = int(i)
            j = int(j)
            if i < 0 or i>=self.thisPtr.rows():
                raise ValueError("Invalid row index " + str(i))
            if j < 0 or j>=self.thisPtr.cols():
                raise ValueError("Invalid col index " + str(j))

            self.thisPtr.insertVal(i, j, val)

    def __add__(csarray_float self, csarray_float A):
        """
        Add two matrices together
        """
        if self.shape != A.shape:
            raise ValueError("Cannot add matrices of shapes" + str(self.shape) + " and " + str(A.shape))

        cdef csarray_float result = csarray_float(self.src_dim,self.dest_dim)
        del result.thisPtr
        result.thisPtr = new SparseMatrixExt[float](self.thisPtr.add(deref(A.thisPtr)))
        return result


    def prune(self):
        """
        Calls prune function on the sparse matrix, sparsifying all
        nonzero entries below a specified value.
        """
        self.thisPtr.prune(0.0001,0.000001)


    def nonzero(self):
        """
        Return a tuple of arrays corresponding to nonzero elements.
        """
        cdef numpy.ndarray[long, ndim=1, mode="c"] rowInds = numpy.zeros(self.getnnz(), dtype=numpy.int64)
        cdef numpy.ndarray[long, ndim=1, mode="c"] colInds = numpy.zeros(self.getnnz(), dtype=numpy.int64)

        if self.getnnz() != 0:
            self.thisPtr.nonZeroInds(&rowInds[0], &colInds[0])

        return (rowInds, colInds)


    def __getitem__(self, inds):
        """
        Get a value or set of values from the array (denoted A). Currently 3 types of parameters
        are supported. If i,j = inds are integers then the corresponding elements of the array
        are returned. If i,j are both arrays of ints then we return the corresponding
        values of A[i[k], j[k]] (note: i,j must be sorted in ascending order). If one of
        i or j is a slice e.g. A[[1,2], :] then we return the submatrix corresponding to
        the slice.
        """

        i, j = inds

        if type(i) == numpy.ndarray and type(j) == numpy.ndarray:
            return self.__adArraySlice(numpy.ascontiguousarray(i, dtype=numpy.int) , numpy.ascontiguousarray(j, dtype=numpy.int) )
        elif (type(i) == numpy.ndarray or type(i) == slice or isinstance(i,int)) and (type(j) == slice or type(j) == numpy.ndarray or isinstance(j,int)):
            indList = []
            for k, index in enumerate(inds):
                if type(index) == numpy.ndarray:
                    indList.append(index)
                elif type(index) == slice:
                    if index.start == None:
                        start = 0
                    else:
                        start = index.start
                    if index.stop == None:
                        stop = self.shape[k]
                    else:
                        stop = index.stop
                    indArr = numpy.arange(start, stop)
                    indList.append(indArr)
                elif isinstance(index,int):
                    indList.append([index])

            return self.subArray(numpy.array(indList[0]), numpy.array(indList[1]))
        else:
            i = int(i)
            j = int(j)

            #Deal with negative indices
            if i<0:
                i += self.thisPtr.rows()
            if j<0:
                j += self.thisPtr.cols()

            if i < 0 or i>=self.thisPtr.rows():
                raise ValueError("Invalid row index " + str(i))
            if j < 0 or j>=self.thisPtr.cols():
                raise ValueError("Invalid col index " + str(j))
            return self.thisPtr.coeff(i, j)


    def subArray(self, numpy.ndarray[numpy.int_t, ndim=1, mode="c"] rowInds, numpy.ndarray[numpy.int_t, ndim=1, mode="c"] colInds):
        """
        Explicitly perform an array slice to return a submatrix with the given
        indices. Only works with ascending ordered indices. This is similar
        to using numpy.ix_.
        """
        cdef numpy.ndarray[int, ndim=1, mode="c"] rowIndsC
        cdef numpy.ndarray[int, ndim=1, mode="c"] colIndsC

        cdef csarray_float result = csarray_float(rowInds.shape[0], colInds.shape[0])

        rowIndsC = numpy.ascontiguousarray(rowInds, dtype=numpy.int32)
        colIndsC = numpy.ascontiguousarray(colInds, dtype=numpy.int32)

        if rowInds.shape[0] != 0 and colInds.shape[0] != 0:
            self.thisPtr.slice(&rowIndsC[0], rowIndsC.shape[0], &colIndsC[0], colIndsC.shape[0], result.thisPtr)
        return result


    def put(self, val, numpy.ndarray[int, ndim=1] rowInds not None, numpy.ndarray[int, ndim=1] colInds not None):
        """
        Select rowInds and colInds
        """
        cdef unsigned int ix
        self.reserve(len(rowInds))
        if isinstance(val,numpy.ndarray):
            for ix in range(len(rowInds)):
                self.thisPtr.insertVal(rowInds[ix], colInds[ix], val[ix])
        else:
            for ix in range(len(rowInds)):
                self.thisPtr.insertVal(rowInds[ix], colInds[ix], val)


    def copy(self):
        """
        Return a copied version of this array.
        """
        cdef csarray_float result = csarray_float(self.src_dim,self.dest_dim)
        del result.thisPtr
        result.thisPtr = new SparseMatrixExt[float](deref(self.thisPtr))
        return result


    def toarray(self):
        """
        Convert this sparse matrix into a numpy array.
        """
        cdef numpy.ndarray[float, ndim=2, mode="c"] result = numpy.zeros(self.shape, numpy.float32)
        cdef numpy.ndarray[long, ndim=1, mode="c"] rowInds
        cdef numpy.ndarray[long, ndim=1, mode="c"] colInds
        cdef unsigned int i

        (rowInds, colInds) = self.nonzero()

        for i in range(rowInds.shape[0]):
            result[rowInds[i], colInds[i]] += self.thisPtr.coeff(rowInds[i], colInds[i])

        return result


    def compress(self):
        """
        Turn this matrix into compressed sparse format by freeing extra memory
        space in the buffer.
        """
        self.thisPtr.makeCompressed()


    def reserve(self, int n):
        """
        Reserve n nonzero entries and turns the matrix into uncompressed mode.
        """
        self.thisPtr.reserve(n)


    def getTriplets(self):
        """
        Returns coordinate and value triplets from sparse matrix.
        """
        cdef numpy.ndarray[int, ndim=1, mode="c"] rowInds = numpy.zeros(self.getnnz(), dtype=numpy.int32)
        cdef numpy.ndarray[int, ndim=1, mode="c"] colInds = numpy.zeros(self.getnnz(), dtype=numpy.int32)
        cdef numpy.ndarray[float, ndim=1, mode="c"] values = numpy.zeros(self.getnnz(), dtype=numpy.float32)
        self.thisPtr.iterNonZero(&rowInds[0], &colInds[0], &values[0])
        return rowInds, colInds, values


    def setTriplets(self, numpy.ndarray[int, ndim=1, mode="c"] rows, numpy.ndarray[int, ndim=1, mode="c"] cols, numpy.ndarray[float, ndim=1, mode="c"] vals):
        """
        Calls C method, which sets nonzero value in the sparse matrix based on coordinate and value triplets.
        """
        self.thisPtr.setTriplets(&rows[0],&cols[0],&vals[0],int(vals.shape[0]))


    def Hebbian(self,numpy.ndarray[double, ndim=2, mode="c"] src_act, numpy.ndarray[double, ndim=2, mode="c"] dest_act, numpy.ndarray[double, ndim=2, mode="c"] norm_total, double lr):
        """
        Call C method to update weights based on Hebbian learning and
        the learning rate, also calculates the CF weight totals for
        divisive normalization.
        """
        self.thisPtr.Hebbian(&src_act[0,0],&dest_act[0,0],&norm_total[0,0],lr)


    def Hebbian_opt(self,numpy.ndarray[double, ndim=2, mode="c"] src_act, numpy.ndarray[double, ndim=2, mode="c"] dest_act, numpy.ndarray[double, ndim=2, mode="c"] norm_total, double lr, bool init):
        """
        Call optimized C method to update weights based on Hebbian
        learning and the learning rate, also calculates the CF weight
        totals for divisive normalization. Optimization skips inactive
        units (only provides speedup in very specific circumstances).
        """
        if init:
            self.thisPtr.Hebbian_opt(&src_act[0,0],&dest_act[0,0],&norm_total[0,0],lr)
        else:
            self.thisPtr.Hebbian(&src_act[0,0],&dest_act[0,0],&norm_total[0,0],lr)


    def DotProduct(self, double strength, numpy.ndarray[double, ndim=2, mode="c"] dense, numpy.ndarray[double, ndim=2, mode="c"] out):
        """
        Call C method to calculate the dot product sums between the input activities and CF weights.
        """
        self.thisPtr.DotProduct(self.dest_dim[0]*self.dest_dim[1],strength,&dense[0,0],&out[0,0])


    def DotProduct_opt(self, double strength, numpy.ndarray[double, ndim=2, mode="c"] dense, numpy.ndarray[double, ndim=2, mode="c"] out):
        """
        Call optimized C method to calculate the dot product sums between the input activities and CF weights.
        """
        self.thisPtr.DotProduct_opt(self.dest_dim[0]*self.dest_dim[1],strength,&dense[0,0],&out[0,0])


    def DivisiveNormalizeL1(self,numpy.ndarray[double, ndim=2, mode="c"] norm_total):
        """
        Calls C method to apply divisive normalization on each CF in
        the sparse projection.
        """
        self.thisPtr.DivisiveNormalizeL1(&norm_total[0,0])


    def DivisiveNormalizeL1_opt(self,numpy.ndarray[double, ndim=2, mode="c"] norm_total, numpy.ndarray[double, ndim=2, mode="c"] dest_act, bool init):
        """
        Calls optimized C method to apply divisive normalization on
        each CF in the sparse projection.  Optimization skips inactive
        units (only provides speedup in very specific circumstances).
        """
        if init:
            self.thisPtr.DivisiveNormalizeL1(&norm_total[0,0])
        else:
            self.thisPtr.DivisiveNormalizeL1_opt(&norm_total[0,0],&dest_act[0,0])


    def CFWeightTotals(self,numpy.ndarray[double, ndim=2, mode="c"] norm_total):
        """
        Method to calculate the current weight totals for each CF.
        """
        self.thisPtr.CFWeightTotals(&norm_total[0,0])


    shape = property(__getShape)
    size = property(__getSize)
    ndim = property(__getNDim)
