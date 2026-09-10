from __future__ import annotations
import math, json
from pcs_factory_coordinates import *
from pcs_factory_camera import *

def _max_abs_matrix(A,B): return max(abs(A[i][j]-B[i][j]) for i in range(3) for j in range(3))
def angle_dirs(a,b):
    a=unit(a); b=unit(b); c=min(1.0,max(-1.0,abs(dot(a,b))))
    return math.acos(c)
def compare_sample(sample):
    cam=sample['camera']; K=tuple(tuple(float(x) for x in row) for row in cam['K']); pose={k:tuple(tuple(x for x in row) for row in cam[k]) if k.startswith('R_') else tuple(cam[k]) for k in ['camera_center_world','R_camera_to_world_graphics','R_world_to_camera_graphics','R_world_to_camera_cv','t_world_to_camera_cv']}
    findings=[]; max_point=0.0; max_vp=0.0; max_line=0.0
    # rotation checks
    ortho=frob_orthogonality_error(pose['R_camera_to_world_graphics']); deterr=abs(det3(pose['R_camera_to_world_graphics'])-1.0)
    if ortho>1e-9: findings.append('ROTATION_NOT_ORTHONORMAL')
    if deterr>1e-9: findings.append('ROTATION_DET_NOT_PLUS_ONE')
    # inverse consistency
    if _max_abs_matrix(transpose(pose['R_camera_to_world_graphics']),pose['R_world_to_camera_graphics'])>1e-9: findings.append('GRAPHICS_ROTATION_INVERSE_MISMATCH')
    expected_w2cv=mat_mul(V_FROM_G,pose['R_world_to_camera_graphics'])
    if _max_abs_matrix(expected_w2cv,pose['R_world_to_camera_cv'])>1e-9: findings.append('CV_GRAPHICS_MAPPING_MISMATCH')
    expected_t=scale(mat_vec(pose['R_world_to_camera_cv'],pose['camera_center_world']),-1.0)
    if max(abs(expected_t[i]-pose['t_world_to_camera_cv'][i]) for i in range(3))>1e-9: findings.append('TRANSLATION_MISMATCH')
    # K scalar consistency
    for got,exp,name in [(K[0][0],cam['fx_px'],'FX'),(K[1][1],cam['fy_px'],'FY'),(K[0][2],cam['cx_px'],'CX'),(K[1][2],cam['cy_px'],'CY')]:
        if abs(got-float(exp))>1e-9: findings.append('K_'+name+'_MISMATCH')
    # point checks
    for row in sample['geometry_truth'].get('points',[]):
        try: uv=project_world(tuple(row['world']),pose,K)[:2]
        except ValueError:
            if row.get('visible_expected',True): findings.append('POINT_VISIBILITY_MISMATCH:'+row['id'])
            continue
        if row.get('pixel') is not None:
            e=math.hypot(uv[0]-row['pixel'][0],uv[1]-row['pixel'][1]); max_point=max(max_point,e)
            if e>1e-7: findings.append('POINT_REPROJECTION:'+row['id'])
    # VP checks
    for row in sample['geometry_truth'].get('vanishing_points',[]):
        vp=vanishing_point(tuple(row['direction_world']),pose,K,cam['width_px'],cam['height_px'])
        if bool(vp['finite']) != bool(row['finite']): findings.append('VP_FINITE_CLASS:'+row['id']); continue
        if vp['finite'] and row.get('pixel') is not None:
            e=math.hypot(vp['pixel'][0]-row['pixel'][0],vp['pixel'][1]-row['pixel'][1]); max_vp=max(max_vp,e)
            if e>1e-7: findings.append('VP_REPROJECTION:'+row['id'])
    # horizon
    if sample['geometry_truth'].get('horizon'):
        h=horizon_from_plane_normal(tuple(sample['geometry_truth']['horizon']['plane_normal_world']),pose,K)['line_normalized']; ref=tuple(sample['geometry_truth']['horizon']['line_normalized'])
        # lines are oriented deterministically by normalize_line
        e=max(abs(h[i]-ref[i]) for i in range(3)); max_line=max(max_line,e)
        if e>1e-9: findings.append('HORIZON_MISMATCH')
    return {'schema':'DF-G14-ORACLE-RESULT-V1','status':'PASS' if not findings else 'FAIL','findings':findings,'max_point_reprojection_px':max_point,'max_vp_reprojection_px':max_vp,'max_line_residual':max_line,'rotation_orthogonality_error':ortho,'rotation_det_error':deterr}
