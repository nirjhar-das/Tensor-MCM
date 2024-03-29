# -*- coding: utf-8 -*-
"""Tensor-MCM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1OdapZJYm7eCD-gUOeHf2RBu8UmHk38b1
"""

!pip install tensorly

import tensorly as tl
from tensorly.decomposition import parafac
import cvxpy as cp
import numpy as np

def rank_R_decomp(X, R=3):
  X_t = tl.tensor(X)
  _, factors = parafac(X_t, rank=R)
  fact_np = [tl.to_numpy(f) for f in factors]
  return fact_np

def inner_prod_decomp(Ai, Aj):
  #Ai = rank_R_decomp(Xi, rank)
  #Aj = rank_R_decomp(Xj, rank)
  s = 0.0
  R = len(Ai[0].shape[1])
  for p in range(R):
    for q in range(R):
      prod = 1.0
      for ai, aj in zip(Ai, Aj):
        prod *= np.dot(ai[:, p], aj[:, q])
      s += prod
  return s

def make_kernel(data_decomp):
  K = np.zeros((len(data_decomp), len(data_decomp)))
  for i in range(len(data_decomp)):
    for j in range(i+1):
      K[i, j] = inner_prod_decomp(data_decomp[i], data_decomp[j])
      K[j, i] = K[i, j]
  
  return K

def tensor_MCM(data_X, data_Y, rank=3.0, C=1.0):
  M = len(data_X)
  data_fact = [rank_R_decomp(X, rank) for X in data_X]
  data_decomp = [f[1] for ]
  K = make_kernel(data_decomp)

  h = cp.variable()
  b = cp.variable()
  q = cp.variable(M)
  l = cp.variable(M)

  obj = h + C*cp.atoms.affine.sum.sum(q)

  constraints = []
  for i in range(M):
    contraints.append(h >= (data_Y[i]*(cp.atoms.affine.sum.sum(l, K[:, i])+b) + q[i]))
    contraints.append(data_Y[i]*(cp.atoms.affine.sum.sum(l, K[:, i]) + b) + q[i]) >= 1)
  
  prob = cp.Problem(cp.minimize(obj), constraints)
  prob.solve()

  print('The optimal value is:', prob.value)

  return data_decomp, l.value

def construct_W(data_decomp, l, eps=1e-9):
  keep_l = l[l>eps]
  R = data_decomp[0][1].shape[1]
  W = tl.zeros([data_decomp[0][i].shape[0] for i in range(len(data_decomp[0]))])
  for i, flag in enumerate((l > eps)):
    if flag:
      W += l[i]*tl.cp_to_tensor((np.ones(R), data_decomp[i]))
  
  return W

def select_features(mask, x_decomp):
  x_reduced = []
  for m, x in zip(mask, x_decomp):
    x_reduced.append(x[mask])
  
  return x_reduced

def tensor_mcm_reduction(data_X, data_Y, thres, rank=3, C=1.0, eps=1e-9):
  '''
  data_X    :   List containing tensors of images
  data_Y    :   List containing labels (+1 or -1)
  rank      :   Rank-R decomposition of data (hyperparameter, typically between 3 to 10)
  C         :   Hyperparameter for MCM
  eps       :   Hyperparameter for filtering support tensors
  thres     :   Threshold for dropping features along dimensions (array/list of size data tensor's dimension)
  '''
  X_decomp, l = tensor_MCM(data_X, data_Y, rank, C)
  W = construct_W(X_decomp, l, eps)
  W_decomp = rank_R_decomp(W, rank=1)
  mask = [(w.squeeze() > thr) for w in zip(W_decomp, thres)]
  X_reduced = []
  for x in X_decomp :
    x_red = select_features(mask, x, thres)
    X_reduced.append(x_red)
  
  return X_reduced