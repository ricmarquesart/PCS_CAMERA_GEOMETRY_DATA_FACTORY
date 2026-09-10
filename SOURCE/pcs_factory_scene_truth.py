from __future__ import annotations
import math
from pcs_factory_coordinates import unit, dot, add, scale
from pcs_factory_camera import project_world
TRUTH_SCHEMA_VERSION='DF-G15-G16-TRUTH-V1'
SOLVABILITY_CLASSES={
 'SOLVABLE_3VP','SOLVABLE_2VP_LIKE','SOLVABLE_1VP_LIKE','WEAK_THIRD_AXIS','NEAR_INFINITE_DIRECTION','MULTIPLE_LOCAL_FRAMES','NON_MANHATTAN','INSUFFICIENT_VISIBLE_STRUCTURE','ORGANIC_NEGATIVE','REPEATED_PATTERN_AMBIGUITY'}
EXPECTED_BEHAVIOR={'SOLVE','SOLVE_WITH_ABSTENTION_OPTION','ABSTAIN'}

def unoriented_angle_deg(a,b):
    a=unit(a); b=unit(b); c=min(1.0,max(-1.0,abs(dot(a,b))))
    return math.degrees(math.acos(c))

def solvability_record(declared_class,directions_world,visible_support_counts=None,vp_status=None,expected_behavior=None,notes=None):
    if declared_class not in SOLVABILITY_CLASSES: raise ValueError('invalid solvability class')
    dirs=[unit(d) for d in directions_world]
    pairs=[]
    for i in range(len(dirs)):
        for j in range(i+1,len(dirs)):
            pairs.append({'i':i,'j':j,'angle_deg':unoriented_angle_deg(dirs[i],dirs[j])})
    supports=list(visible_support_counts or [None]*len(dirs))
    if len(supports)!=len(dirs): raise ValueError('support length mismatch')
    if expected_behavior is None:
        expected_behavior='ABSTAIN' if declared_class in {'INSUFFICIENT_VISIBLE_STRUCTURE','ORGANIC_NEGATIVE'} else ('SOLVE_WITH_ABSTENTION_OPTION' if declared_class in {'WEAK_THIRD_AXIS','NEAR_INFINITE_DIRECTION','MULTIPLE_LOCAL_FRAMES','NON_MANHATTAN','REPEATED_PATTERN_AMBIGUITY'} else 'SOLVE')
    if expected_behavior not in EXPECTED_BEHAVIOR: raise ValueError('invalid expected behavior')
    return {'schema':'DF-G15-SOLVABILITY-V1','class':declared_class,'expected_behavior':expected_behavior,'direction_count':len(dirs),'directions_world':dirs,'pairwise_unoriented_angles_deg':pairs,'visible_support_counts':supports,'vp_status':vp_status or [],'notes':notes}

def normalize_plane(normal_world,d_m):
    n=unit(normal_world); raw_norm=math.sqrt(sum(float(x)*float(x) for x in normal_world))
    if raw_norm<=1e-15: raise ValueError('zero plane normal')
    return {'schema':'DF-G16-PLANE-V1','normal_world':n,'d_m':float(d_m)/raw_norm}

def plane_from_point_normal(point_world,normal_world):
    n=unit(normal_world); return {'schema':'DF-G16-PLANE-V1','normal_world':n,'d_m':-dot(n,point_world)}

def signed_point_plane_distance(point_world,plane): return dot(plane['normal_world'],point_world)+float(plane['d_m'])
def camera_plane_distance(camera_center_world,plane): return signed_point_plane_distance(camera_center_world,plane)
def ray_plane_intersection(ray_origin_world,ray_direction_world,plane,eps=1e-12):
    d=unit(ray_direction_world); n=plane['normal_world']; denom=dot(n,d)
    if abs(denom)<=eps: return {'parallel':True,'point_world':None,'ray_t_m':None}
    t=-(dot(n,ray_origin_world)+float(plane['d_m']))/denom
    return {'parallel':False,'point_world':add(ray_origin_world,scale(d,t)),'ray_t_m':t}
def metric_anchor(anchor_id,p0_world,p1_world,object_id=None,plane_id=None):
    delta=[float(p1_world[i])-float(p0_world[i]) for i in range(3)]; length=math.sqrt(sum(x*x for x in delta))
    return {'schema':'DF-G16-METRIC-ANCHOR-V1','anchor_id':anchor_id,'p0_world':tuple(p0_world),'p1_world':tuple(p1_world),'length_m':length,'object_id':object_id,'plane_id':plane_id}
def project_metric_anchor(anchor,pose,K):
    a=project_world(anchor['p0_world'],pose,K); b=project_world(anchor['p1_world'],pose,K)
    return {'anchor_id':anchor['anchor_id'],'pixel_endpoints':(a[:2],b[:2]),'depths_m':(a[2],b[2]),'length_m':anchor['length_m']}
