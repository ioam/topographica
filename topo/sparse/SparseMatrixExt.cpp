/*
Subclass of Eigen3 SparseMatrix extended with useful utilities for use
by Topographica. Speed-critical components are implemented here and
higher-level (Topographica specific) components should be implemented
in Cython.
*/

#ifndef SparseMatrixEXT_H
#define SparseMatrixEXT_H
#include <iostream>
#include <omp.h>
#include <eigen3/Eigen/Sparse>
#include <vector>
#define EIGEN_DONT_PARALLELIZE

using Eigen::SparseMatrix;

template <class T, int S=Eigen::ColMajor>
  class SparseMatrixExt:public SparseMatrix<T, S> {
  public:
  SparseMatrixExt<T, S>():
		SparseMatrix<T, S>(){
		}

	SparseMatrixExt<T, S>(int rows, int cols):
		SparseMatrix<T, S>(rows, cols){
		}


  SparseMatrixExt<T, S>(const SparseMatrix<T, S> other):
  SparseMatrix<T, S>(other){
		}

  SparseMatrixExt& operator=(const SparseMatrixExt& other)  {
	SparseMatrix<T, S>::operator=(other);
	return *this;
  }

  SparseMatrixExt<T, S> add(const SparseMatrixExt& other) {
    return (SparseMatrixExt<T,S>)((*this) + other);
  }

  void slice(int* array1, int size1, int* array2, int size2, SparseMatrixExt<T, S> *mat) {
	//Array indices must be sorted
	//SparseMatrixExt *mat = new SparseMatrixExt<T, S>(size1, size2);
	int size1Ind = 0;

	//Assume column major class - j is col index
	for (int j=0; j<size2; ++j) {
	  size1Ind = 0;
	  for (typename SparseMatrixExt<T, S>::InnerIterator it(*this, array2[j]); it; ++it) {
		while (array1[size1Ind] < it.row() && size1Ind < size1) {
		  size1Ind++;
		}
		if(it.row() == array1[size1Ind]) {
		  mat->insert(size1Ind, j) = it.value();
		}
	  }
	}
  }

  void insertVal(int row, int col, T val) {
	if (this->coeff(row, col) != val)
	  this->coeffRef(row, col) = val;
  }

  void iterNonZero(int* array1, int* array2, float* array3) {
	unsigned int i = 0;
	for (int k=0; k<this->outerSize(); ++k) {
	  for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		array1[i] = it.row();
		array2[i] = it.col();
		array3[i] = it.value();
		i++;
	  }
	}
  }

  void DotProduct(unsigned int num_cfs, double strength, double* input, double* activity) {
    #pragma omp parallel
	{
	  unsigned int k, j;
      #pragma omp for schedule(guided, 8)
      for (k=0; k<this->outerSize(); ++k) {
		for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		  activity[it.col()] += input[it.row()] * it.value();
		}
	  }
      #pragma omp for schedule(guided, 8)
	  for (j=0; j<num_cfs; ++j) {
		activity[j] *= strength;
	  }
	}
  }

  void DotProduct_opt(unsigned int num_cfs, double strength, double* input, double* activity) {
    double epsilon = 0.000001;
    #pragma omp parallel
	{
	  unsigned int k, j;
	  double src;
      #pragma omp for schedule(guided, 8)
      for (k=0; k<this->outerSize(); ++k) {
		for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		  src = input[it.row()];
		  if (src >= epsilon) {
			activity[it.col()] += src * it.value();
		  }
		}
	  }
      #pragma omp for schedule(guided, 8)
	  for (j=0; j<num_cfs; ++j) {
		activity[j] *= strength;
	  }
	}
  }

  void Hebbian(double* src_act,double* dest_act, double* norm_total, const double lr) {
	#pragma omp parallel
	{
	  unsigned int k, y;
      #pragma omp for schedule(guided, 8)
	  for (int k=0; k<this->outerSize(); ++k) {
		for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		  y = it.col();
		  it.valueRef() += dest_act[y] * lr * src_act[it.row()];
		  norm_total[y] += it.value();
		}
	  }
	}
  }

  void Hebbian_opt(double* src_act,double* dest_act, double* norm_total, const double lr) {
	double epsilon = 0.000001;
	#pragma omp parallel
	{
	  unsigned int k, y;
	  double src, dest;
      #pragma omp for schedule(guided, 8)
	  for (int k=0; k<this->outerSize(); ++k) {
		for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		  y = it.col();
		  src = src_act[it.row()];
		  dest = dest_act[y];
		  if (src >= epsilon and dest >= epsilon) {
			it.valueRef() += dest * lr * src;
		  }
		  norm_total[y] += it.value();
		}
	  }
	}
  }

  void CFWeightTotals(double* norm_total) {
	#pragma omp parallel
	{
	  unsigned int k;
	  #pragma omp for schedule(guided, 8)
	  for (k=0; k<this->outerSize(); ++k) {
		for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		  norm_total[it.col()] += it.value();
		}
	  }
	}
  }

  void DivisiveNormalizeL1(double* norm_total) {
	#pragma omp parallel
	{
	  unsigned int k;
	  double factor;
	  #pragma omp for schedule(guided, 8)
	  for (k=0; k<this->outerSize(); ++k) {
		for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		  factor = 1.0/norm_total[it.col()];
		  it.valueRef() *= factor;
		}
	  }
	}
  }

  void DivisiveNormalizeL1_opt(double* norm_total, double* dest_act) {
	double epsilon = 0.000001;
    #pragma omp parallel
	{
	  unsigned int k, y;
	  double factor;
	  #pragma omp for schedule(guided, 8)
	  for (k=0; k<this->outerSize(); ++k) {
		for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		  y = it.col();
		  if (dest_act[y] >= epsilon) {
			factor = 1.0/norm_total[y];
			it.valueRef() *= factor;
		  }
		}
	  }
	}
  }

  void nonZeroInds(long* array1, long* array2) {
	int i = 0;
	for (int k=0; k<this->outerSize(); ++k) {
	  for (typename SparseMatrixExt<T>::InnerIterator it(*this,k); it; ++it) {
		array1[i] = it.row();
		array2[i] = it.col();
		i++;
	  }
	}
  }

  void setTriplets(const int* is, const int* js, const float* vs, const int n) {
	  typedef Eigen::Triplet<float> Tr;
	  std::vector<Tr> tripletList;
	  tripletList.reserve(n);
	  for (int i = 0; i < n; i++) {
		tripletList.push_back(Tr(is[i],js[i],vs[i]));
	  }
	  this->setFromTriplets(tripletList.begin(),tripletList.end());
  }};

#endif
