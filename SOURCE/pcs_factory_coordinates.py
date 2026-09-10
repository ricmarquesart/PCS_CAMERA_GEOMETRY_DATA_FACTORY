from __future__ import annotations
import math
CONVENTION_VERSION='DF-G04-COORD-V1'
C_FROM_B=((1.0,0.0,0.0),(0.0,0.0,1.0),(0.0,-1.0,0.0))
B_FROM_C=((1.0,0.0,0.0),(0.0,0.0,-1.0),(0.0,1.0,0.0))
V_FROM_G=((1.0,0.0,0.0),(0.0,-1.0,0.0),(0.0,0.0,-1.0))

def dot(a,b): return sum(float(x)*float(y) for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a): return math.sqrt(dot(a,a))
def unit(a,eps=1e-15):
    n=norm(a)
    if n<=eps: raise ValueError('zero vector')
    return tuple(float(x)/n for x in a)
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def scale(a,s): return tuple(x*s for x in a)
def mat_vec(M,v): return tuple(sum(M[i][j]*v[j] for j in range(3)) for i in range(3))
def mat_mul(A,B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def transpose(A): return tuple(tuple(A[j][i] for j in range(3)) for i in range(3))
def det3(A):
    return (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])-A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])+A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))
def blender_to_canonical(v): return mat_vec(C_FROM_B,v)
def canonical_to_blender(v): return mat_vec(B_FROM_C,v)
def graphics_to_cv(v): return mat_vec(V_FROM_G,v)
def cv_to_graphics(v): return mat_vec(V_FROM_G,v)
def frob_orthogonality_error(R):
    RtR=mat_mul(transpose(R),R)
    return math.sqrt(sum((RtR[i][j]-(1.0 if i==j else 0.0))**2 for i in range(3) for j in range(3)))
