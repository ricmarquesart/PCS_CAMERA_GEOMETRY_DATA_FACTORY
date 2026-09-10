from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter

try:
    import numpy as np
except Exception:
    np = None

from pcs_factory_camera import camera_profile, clip_segment, look_at, structural_line
from pcs_factory_coordinates import add, dot, mat_vec, scale, sub, transpose, unit
from pcs_factory_seed import derive_seed, identity_digest

SCHEMA = 'DF-G100-R26-CAMERA-OBSERVABILITY-V2'
CANDIDATE_BUDGET = 64
DEFAULT_EVALUATED_CANDIDATES = 4
GRID_W = 32
GRID_H = 18
BOUNDARY_EPS_M = 1e-9
MIN_SEGMENT_PX = 12.0
RICH_STRUCTURAL = {
    'INTERIOR','CORRIDOR','URBAN','INTERSECTION','INDUSTRIAL','STAIRS_RAMPS',
    'NON_MANHATTAN','CLUTTER','REPEATED_PATTERN','HYBRID_CONCEPT'
}
THRESHOLDS = {
    'RICH_STRUCTURAL': {
        'scene_hit_fraction_min': 0.10,
        'distinct_visible_object_ids_min': 3,
        'dominant_visible_object_fraction_max': 0.85,
        'clipped_structural_segments_min': 8,
        'distinct_projected_direction_set_ids_min': 2,
    },
    'SPARSE': {
        'scene_hit_fraction_min': 0.05,
        'distinct_visible_object_ids_min': 1,
        'clipped_structural_segments_min': 2,
    },
    'ORGANIC_NEGATIVE': {
        'scene_hit_fraction_min': 0.05,
        'distinct_visible_object_ids_min': 2,
        'dominant_visible_object_fraction_max': 0.90,
    },
}
THRESHOLD_HASH = identity_digest(THRESHOLDS)


def _mat_t_vec(R, v):
    return mat_vec(transpose(R), v)


def _obb_local(point, obj):
    return _mat_t_vec(obj['R_local_to_world'], sub(tuple(point), tuple(obj['center_world'])))


def point_inside_obb(point, obj, eps=BOUNDARY_EPS_M):
    q = _obb_local(point, obj)
    h = tuple(float(d) * 0.5 for d in obj['dimensions_m'])
    # Boundary is authority-bearing and fails closed.
    return all(abs(float(q[i])) <= h[i] + float(eps) for i in range(3))


def ray_obb_t(origin, direction, obj, eps=BOUNDARY_EPS_M):
    o = _obb_local(origin, obj)
    d = _mat_t_vec(obj['R_local_to_world'], tuple(direction))
    h = tuple(float(x) * 0.5 for x in obj['dimensions_m'])
    tmin = -float('inf')
    tmax = float('inf')
    for i in range(3):
        oi = float(o[i]); di = float(d[i]); hi = h[i]
        if abs(di) <= 1e-15:
            if oi < -hi - eps or oi > hi + eps:
                return None
            continue
        a = (-hi - oi) / di
        b = ( hi - oi) / di
        if a > b: a, b = b, a
        tmin = max(tmin, a)
        tmax = min(tmax, b)
        if tmin > tmax:
            return None
    if tmax <= eps:
        return None
    return tmin if tmin > eps else tmax


def _obb_world_aabb(obj):
    c = tuple(float(x) for x in obj['center_world'])
    d = tuple(float(x) * 0.5 for x in obj['dimensions_m'])
    R = obj['R_local_to_world']
    pts=[]
    for sx in (-1,1):
        for sy in (-1,1):
            for sz in (-1,1):
                local=(sx*d[0],sy*d[1],sz*d[2])
                pts.append(add(c, mat_vec(R, local)))
    mn=tuple(min(p[i] for p in pts) for i in range(3))
    mx=tuple(max(p[i] for p in pts) for i in range(3))
    return mn,mx


def scene_bounds(scene):
    boxes=[_obb_world_aabb(o) for o in scene.get('objects',[])]
    if not boxes:
        return {'min':(-1.0,0.0,-1.0),'max':(1.0,2.0,1.0),'center':(0.0,1.0,0.0),'extent':(2.0,2.0,2.0)}
    mn=tuple(min(b[0][i] for b in boxes) for i in range(3))
    mx=tuple(max(b[1][i] for b in boxes) for i in range(3))
    cen=tuple((mn[i]+mx[i])*0.5 for i in range(3))
    ext=tuple(mx[i]-mn[i] for i in range(3))
    return {'min':mn,'max':mx,'center':cen,'extent':ext}


def _room_free_volume(scene):
    floor=next((o for o in scene.get('objects',[]) if o.get('role')=='GROUND' and o.get('primitive')=='FLOOR_PLANE'),None)
    ceil=next((o for o in scene.get('objects',[]) if o.get('role')=='CEILING'),None)
    if floor is None or ceil is None:
        raise RuntimeError('R26_ROOM_ENVELOPE_MISSING')
    fc=tuple(map(float,floor['center_world'])); fd=tuple(map(float,floor['dimensions_m']))
    cc=tuple(map(float,ceil['center_world'])); cd=tuple(map(float,ceil['dimensions_m']))
    floor_top=fc[1]+fd[1]*0.5
    ceil_bottom=cc[1]-cd[1]*0.5
    margin=min(0.65, max(0.35, min(fd[0],fd[2])*0.055))
    return {
        'min':(fc[0]-fd[0]*0.5+margin, floor_top+0.12, fc[2]-fd[2]*0.5+margin),
        'max':(fc[0]+fd[0]*0.5-margin, ceil_bottom-0.18, fc[2]+fd[2]*0.5-margin),
        'center':(fc[0], (floor_top+ceil_bottom)*0.5, fc[2]),
        'margin_m':margin,
        'floor_top_y':floor_top,
        'ceiling_bottom_y':ceil_bottom,
    }


def _candidate_seed(root_seed, sample_index, candidate_index):
    return int(derive_seed(int(root_seed),'micro100-v2-camera-candidate',int(sample_index),int(candidate_index))['seed_u64'])


def _profile_intrinsics(profile, seed, width, height):
    # Reuse the accepted V1 profile sampler solely for deterministic intrinsics and profile parameters.
    return camera_profile(profile, seed, width=width, height=height)


def _clamp(x,a,b): return min(max(float(x),float(a)),float(b))


def _candidate_pose(scene, profile, seed, width, height):
    b=_profile_intrinsics(profile,seed,width,height)
    s=b['sampled']; r=random.Random(int(seed) ^ 0xDFA10026)
    family=str(scene['scene_family'])
    bounds=scene_bounds(scene)
    roll=float(s['roll_deg'])
    pitch_mag=abs(float(s['pitch_bias_deg']))
    pitch_sign=1.0 if float(s['pitch_bias_deg'])>=0 else -1.0
    if family in {'INTERIOR','CORRIDOR','CLUTTER','HYBRID_CONCEPT'}:
        fv=_room_free_volume(scene); mn=fv['min']; mx=fv['max']; cen=fv['center']
        # Deterministic free-space candidates. Keep away from shell; solid-occupancy gate handles props.
        x=r.uniform(mn[0],mx[0]); z=r.uniform(mn[2],mx[2])
        free_h=max(0.2,mx[1]-mn[1])
        if profile=='LOW_CAMERA': y=mn[1]+r.uniform(0.03,0.16)*free_h
        elif profile=='HIGH_CAMERA': y=mn[1]+r.uniform(0.72,0.94)*free_h
        else: y=mn[1]+r.uniform(0.28,0.68)*free_h
        C=(x,y,z)
        # Mostly look across the room toward a deterministic attention point; candidate jitter prevents collapse.
        tx=cen[0]+r.uniform(-0.22,0.22)*(mx[0]-mn[0])
        tz=cen[2]+r.uniform(-0.22,0.22)*(mx[2]-mn[2])
        ty=cen[1]+r.uniform(-0.12,0.12)*free_h
        horiz=max(1.0,math.hypot(tx-x,tz-z))
        if profile=='STRONG_PITCH':
            ang=math.radians(_clamp(pitch_mag,22.0,42.0)); ty=y+pitch_sign*math.tan(ang)*min(horiz,2.5)
            ty=_clamp(ty,mn[1],mx[1])
        elif profile=='NEAR_INFINITY':
            # Prefer a long view through the room/corridor by biasing target toward the opposite free-volume side.
            dx=tx-x; dz=tz-z
            if abs(dx)>=abs(dz): tx=mx[0] if dx>=0 else mn[0]
            else: tz=mx[2] if dz>=0 else mn[2]
        target=(tx,ty,tz)
        deriv={'mode':'ENCLOSED_FREE_VOLUME','scene_bounds':bounds,'free_volume':fv,'target_world':target}
    else:
        cen=bounds['center']; ext=bounds['extent']; horizontal=max(2.0,0.5*math.hypot(ext[0],ext[2]));
        # Target y is biased toward useful scene mass, not the global origin.
        target_y=bounds['min'][1] + (0.28 if family!='ORGANIC_NEGATIVE' else 0.38)*max(1.0,ext[1])
        target=(cen[0]+r.uniform(-0.10,0.10)*ext[0], target_y, cen[2]+r.uniform(-0.10,0.10)*ext[2])
        if profile=='WIDE': rmul=r.uniform(0.55,0.90)
        elif profile=='TELEPHOTO': rmul=r.uniform(1.15,1.70)
        elif profile=='NEAR_INFINITY': rmul=r.uniform(1.65,2.35)
        else: rmul=r.uniform(0.75,1.25)
        dist=max(3.0,horizontal*rmul)
        az=math.radians(r.uniform(-180.0,180.0))
        ground=bounds['min'][1]
        if profile=='LOW_CAMERA': y=ground+max(0.18,0.035*max(ext[1],4.0))
        elif profile=='HIGH_CAMERA': y=ground+max(4.0,0.72*max(ext[1],6.0))
        else: y=ground+max(1.0,min(3.2,0.20*max(ext[1],6.0)))
        C=(target[0]+dist*math.sin(az), y, target[2]+dist*math.cos(az))
        if profile=='STRONG_PITCH':
            horiz=max(1.0,math.hypot(target[0]-C[0],target[2]-C[2])); ang=math.radians(_clamp(pitch_mag,22.0,45.0))
            ty=C[1]+pitch_sign*math.tan(ang)*min(horiz,8.0)
            target=(target[0],_clamp(ty,bounds['min'][1],bounds['max'][1]+0.25*max(ext[1],1.0)),target[2])
        deriv={'mode':'SCENE_EXTENT_ORBIT','scene_bounds':bounds,'horizontal_radius_m':horizontal,'distance_m':dist,'target_world':target}
    pose=look_at(C,target,roll_deg=roll)
    return {'profile':profile,'width':int(width),'height':int(height),'K':b['K'],'fx':b['fx'],'fy':b['fy'],'cx':b['cx'],'cy':b['cy'],'pose':pose,'sampled':dict(s,scene_aware_target_world=target,scene_aware_camera_center_world=C),'derivation':deriv}


def _camera_ray_world(camera,u,v):
    K=camera['K']; fx=float(K[0][0]); fy=float(K[1][1]); cx=float(K[0][2]); cy=float(K[1][2])
    dcv=unit(((float(u)-cx)/fx,(float(v)-cy)/fy,1.0))
    Rcw=transpose(camera['pose']['R_world_to_camera_cv'])
    return unit(mat_vec(Rcw,dcv))


def _coarse_nearest_hit_counts(scene,camera):
    """Vectorized equivalent of the frozen 32x18 nearest-OBB ray probe.

    Uses the exact same pixel-center rays, slab epsilon and strict nearest-t
    tie behavior as the scalar authority, but evaluates all 576 rays at once.
    """
    C=tuple(camera['pose']['camera_center_world']); objs=list(scene.get('objects',[]))
    width=int(camera['width']); height=int(camera['height'])
    if np is None:
        counts=Counter()
        for gy in range(GRID_H):
            v=(gy+0.5)*height/GRID_H-0.5
            for gx in range(GRID_W):
                u=(gx+0.5)*width/GRID_W-0.5
                d=_camera_ray_world(camera,u,v); best=None
                for oi,o in enumerate(objs):
                    t=ray_obb_t(C,d,o)
                    if t is not None and (best is None or t<best[0]): best=(t,oi)
                if best is not None: counts[objs[best[1]]['object_id']]+=1
        return counts
    gx=np.arange(GRID_W,dtype=np.float64)
    gy=np.arange(GRID_H,dtype=np.float64)
    uu=(gx+0.5)*float(width)/GRID_W-0.5
    vv=(gy+0.5)*float(height)/GRID_H-0.5
    U,V=np.meshgrid(uu,vv)
    K=camera['K'];fx=float(K[0][0]);fy=float(K[1][1]);cx=float(K[0][2]);cy=float(K[1][2])
    dcv=np.stack(((U-cx)/fx,(V-cy)/fy,np.ones_like(U)),axis=-1).reshape(-1,3)
    dcv/=np.linalg.norm(dcv,axis=1,keepdims=True)
    Rcw=np.asarray(transpose(camera['pose']['R_world_to_camera_cv']),dtype=np.float64)
    rays=dcv @ Rcw.T
    rays/=np.linalg.norm(rays,axis=1,keepdims=True)
    Cn=np.asarray(C,dtype=np.float64)
    n=rays.shape[0]; best_t=np.full(n,np.inf,dtype=np.float64); best_i=np.full(n,-1,dtype=np.int32)
    eps=float(BOUNDARY_EPS_M)
    for oi,obj in enumerate(objs):
        R=np.asarray(obj['R_local_to_world'],dtype=np.float64)
        center=np.asarray(obj['center_world'],dtype=np.float64)
        h=np.asarray(obj['dimensions_m'],dtype=np.float64)*0.5
        o=(Cn-center) @ R
        d=rays @ R
        tmin=np.full(n,-np.inf,dtype=np.float64); tmax=np.full(n,np.inf,dtype=np.float64); valid=np.ones(n,dtype=bool)
        for ax in range(3):
            di=d[:,ax]; oi0=float(o[ax]); hi=float(h[ax]); par=np.abs(di)<=1e-15
            valid &= ~(par & ((oi0 < -hi-eps) | (oi0 > hi+eps)))
            non=~par
            if np.any(non):
                a=(-hi-oi0)/di[non]; b=(hi-oi0)/di[non]
                lo=np.minimum(a,b); hi_t=np.maximum(a,b)
                tmin[non]=np.maximum(tmin[non],lo); tmax[non]=np.minimum(tmax[non],hi_t)
            valid &= tmin<=tmax
        valid &= tmax>eps
        t=np.where(tmin>eps,tmin,tmax)
        valid &= np.isfinite(t)
        better=valid & (t<best_t)
        best_t[better]=t[better];best_i[better]=oi
    counts=Counter()
    for oi in range(len(objs)):
        c=int(np.count_nonzero(best_i==oi))
        if c: counts[objs[oi]['object_id']]=c
    return counts


def observability_metrics(scene,camera):
    C=tuple(camera['pose']['camera_center_world']); objs=list(scene.get('objects',[]))
    inside=[o['object_id'] for o in objs if point_inside_obb(C,o)]
    counts=_coarse_nearest_hit_counts(scene,camera); structural_ids={o['object_id'] for o in objs if o.get('structural')}
    width=int(camera['width']); height=int(camera['height'])
    total=GRID_W*GRID_H; hit=sum(counts.values()); hitfrac=hit/total
    dominant=(max(counts.values())/hit) if hit else 1.0
    visible_structural=[oid for oid in counts if oid in structural_ids]
    seg_count=0; dirsets=set(); total_len=0.0
    for o in objs:
        if o.get('object_id') not in counts:
            continue
        for e in o.get('edges',[]):
            if not e.get('structural'): continue
            try:
                sl=structural_line(e['line_id'],tuple(e['p0_world']),tuple(e['p1_world']),e['direction_set_id'],camera['pose'],camera['K'],width,height,object_id=o['object_id'])
            except Exception:
                continue
            seg=sl.get('clipped_segment')
            if seg:
                dx=float(seg[1][0])-float(seg[0][0]);dy=float(seg[1][1])-float(seg[0][1]);ln=math.hypot(dx,dy)
                if ln>=MIN_SEGMENT_PX:
                    seg_count+=1;dirsets.add(e['direction_set_id']);total_len+=ln
    diag=max(1.0,math.hypot(width,height))
    return {
        'camera_inside_any_solid':bool(inside),'camera_inside_object_ids':sorted(inside),
        'scene_hit_fraction':hitfrac,'background_fraction':1.0-hitfrac,
        'distinct_visible_object_ids':len(counts),'visible_object_ids':sorted(counts),
        'distinct_visible_structural_object_ids':len(visible_structural),'visible_structural_object_ids':sorted(visible_structural),
        'dominant_visible_object_fraction':dominant,
        'per_object_hit_fractions':{k:counts[k]/hit for k in sorted(counts)} if hit else {},
        'clipped_structural_segments':seg_count,'distinct_projected_direction_set_ids':len(dirsets),
        'projected_direction_set_ids':sorted(dirsets),'normalized_clipped_structural_length':total_len/diag,
        'grid':{'width':GRID_W,'height':GRID_H,'ray_count':total},
    }

def admissibility(scene_family, metrics):
    fam=str(scene_family)
    checks={'camera_outside_all_solids':not bool(metrics['camera_inside_any_solid'])}
    if fam in RICH_STRUCTURAL:
        t=THRESHOLDS['RICH_STRUCTURAL']
        checks.update({
            'scene_hit_fraction':metrics['scene_hit_fraction']>=t['scene_hit_fraction_min'],
            'visible_object_count':metrics['distinct_visible_object_ids']>=t['distinct_visible_object_ids_min'],
            'dominance':metrics['dominant_visible_object_fraction']<=t['dominant_visible_object_fraction_max'],
            'structural_segments':metrics['clipped_structural_segments']>=t['clipped_structural_segments_min'],
            'direction_sets':metrics['distinct_projected_direction_set_ids']>=t['distinct_projected_direction_set_ids_min'],
        }); cls='RICH_STRUCTURAL'
    elif fam=='SPARSE':
        t=THRESHOLDS['SPARSE']
        checks.update({
            'scene_hit_fraction':metrics['scene_hit_fraction']>=t['scene_hit_fraction_min'],
            'visible_object_count':metrics['distinct_visible_object_ids']>=t['distinct_visible_object_ids_min'],
            'structural_segments':metrics['clipped_structural_segments']>=t['clipped_structural_segments_min'],
        }); cls='SPARSE'
    elif fam=='ORGANIC_NEGATIVE':
        t=THRESHOLDS['ORGANIC_NEGATIVE']
        checks.update({
            'scene_hit_fraction':metrics['scene_hit_fraction']>=t['scene_hit_fraction_min'],
            'visible_object_count':metrics['distinct_visible_object_ids']>=t['distinct_visible_object_ids_min'],
            'dominance':metrics['dominant_visible_object_fraction']<=t['dominant_visible_object_fraction_max'],
        }); cls='ORGANIC_NEGATIVE'
    else:
        raise KeyError(fam)
    return {'class':cls,'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}


def _rank_key(metrics,candidate_index,rich):
    return (
        -int(metrics['distinct_visible_object_ids']),
        float(metrics['dominant_visible_object_fraction']),
        -int(metrics['clipped_structural_segments']) if rich else 0,
        -float(metrics['normalized_clipped_structural_length']) if rich else 0.0,
        int(candidate_index),
    )


def select_scene_aware_camera(scene, profile, root_seed, sample_index, width, height, candidate_budget=CANDIDATE_BUDGET, evaluated_candidates=None):
    if int(candidate_budget)!=CANDIDATE_BUDGET:
        raise RuntimeError('R26_CANDIDATE_BUDGET_MUTATION')
    if evaluated_candidates is not None:
        stages=[int(evaluated_candidates)]
        if stages[0]<1 or stages[0]>CANDIDATE_BUDGET:
            raise RuntimeError('R26_EVALUATED_CANDIDATE_COUNT_INVALID')
    else:
        # Deterministic bounded geometric search: cheap first stage, then expand only
        # when no camera satisfies the frozen hard gates. No RGB/acceptance feedback.
        stages=[4,8,16,32,64]
    rows=[]; passes=[]; evaluated=0
    cams={}
    for stage_end in stages:
        if stage_end<=evaluated:
            continue
        for ci in range(evaluated,stage_end):
            seed=_candidate_seed(root_seed,sample_index,ci)
            cam=_candidate_pose(scene,profile,seed,width,height)
            met=observability_metrics(scene,cam); adm=admissibility(scene['scene_family'],met)
            row={'candidate_index':ci,'candidate_seed_u64':seed,'metrics':met,'admissibility':adm,'camera_digest_sha256':identity_digest(cam)}
            rows.append(row); cams[ci]=cam
            if adm['status']=='PASS': passes.append(row)
        evaluated=stage_end
        if passes:
            break
    if not passes:
        summary=[{'candidate_index':r['candidate_index'],'checks':r['admissibility']['checks'],'metrics':{k:r['metrics'][k] for k in ('camera_inside_any_solid','scene_hit_fraction','distinct_visible_object_ids','dominant_visible_object_fraction','clipped_structural_segments','distinct_projected_direction_set_ids')}} for r in rows]
        raise RuntimeError('R26_NO_ADMISSIBLE_CAMERA:'+json.dumps(summary,separators=(',',':')))
    rich=scene['scene_family'] in RICH_STRUCTURAL
    selected_row=min(passes,key=lambda r:_rank_key(r['metrics'],r['candidate_index'],rich))
    selected_cam=cams[selected_row['candidate_index']]
    provenance={
        'schema':SCHEMA,'implementation_id':'DF_G100_SCENE_AWARE_CAMERA_OBSERVABILITY_V2_R26',
        'candidate_budget':CANDIDATE_BUDGET,'evaluated_candidates':evaluated,
        'search_stage_schedule':[4,8,16,32,64],
        'passing_candidate_count':len(passes),'selected_candidate_index':selected_row['candidate_index'],
        'selected_candidate_seed_u64':selected_row['candidate_seed_u64'],'selected_camera_digest_sha256':selected_row['camera_digest_sha256'],
        'selected_metrics':selected_row['metrics'],'selected_admissibility':selected_row['admissibility'],
        'thresholds':THRESHOLDS,'threshold_hash_sha256':THRESHOLD_HASH,
        'selection_objective':['MAX_VISIBLE_OBJECT_IDS','MIN_DOMINANT_VISIBLE_OBJECT_FRACTION','MAX_CLIPPED_STRUCTURAL_SEGMENTS','MAX_NORMALIZED_CLIPPED_STRUCTURAL_LENGTH','MIN_CANDIDATE_INDEX'],
        'scene_derivation':selected_cam.pop('derivation'),
        'non_adaptive':True,'rgb_statistics_used':False,'prior_v1_failure_used_for_selection':False,
        'camera_inside_any_solid_assertion':False,
        'candidate_summary_digest_sha256':identity_digest(rows),
    }
    provenance['candidate_summaries']=[{
        'candidate_index':r['candidate_index'],'candidate_seed_u64':r['candidate_seed_u64'],'status':r['admissibility']['status'],
        'checks':r['admissibility']['checks'],'camera_inside_any_solid':r['metrics']['camera_inside_any_solid'],
        'scene_hit_fraction':r['metrics']['scene_hit_fraction'],'distinct_visible_object_ids':r['metrics']['distinct_visible_object_ids'],
        'dominant_visible_object_fraction':r['metrics']['dominant_visible_object_fraction'],
        'clipped_structural_segments':r['metrics']['clipped_structural_segments'],
        'distinct_projected_direction_set_ids':r['metrics']['distinct_projected_direction_set_ids'],
        'camera_digest_sha256':r['camera_digest_sha256'],
    } for r in rows]
    return selected_cam,provenance

def validate_selected(scene,camera,provenance):
    if provenance.get('schema')!=SCHEMA or provenance.get('threshold_hash_sha256')!=THRESHOLD_HASH:
        raise RuntimeError('R26_OBSERVABILITY_PROVENANCE_IDENTITY_MISMATCH')
    if provenance.get('candidate_budget')!=CANDIDATE_BUDGET or not (1 <= int(provenance.get('evaluated_candidates',0)) <= CANDIDATE_BUDGET):
        raise RuntimeError('R26_OBSERVABILITY_CANDIDATE_COUNT_MISMATCH')
    if provenance.get('non_adaptive') is not True or provenance.get('rgb_statistics_used') is not False or provenance.get('prior_v1_failure_used_for_selection') is not False:
        raise RuntimeError('R26_OBSERVABILITY_ADAPTIVITY_FIREWALL')
    met=observability_metrics(scene,camera); adm=admissibility(scene['scene_family'],met)
    if adm['status']!='PASS' or met['camera_inside_any_solid']:
        raise RuntimeError('R26_SELECTED_CAMERA_NOT_ADMISSIBLE')
    frozen=provenance.get('selected_metrics') or {}
    keys=('camera_inside_any_solid','scene_hit_fraction','distinct_visible_object_ids','dominant_visible_object_fraction','clipped_structural_segments','distinct_projected_direction_set_ids')
    for k in keys:
        a=met[k]; b=frozen.get(k)
        if isinstance(a,float):
            if b is None or abs(float(a)-float(b))>1e-12: raise RuntimeError('R26_SELECTED_METRIC_MISMATCH:'+k)
        elif a!=b: raise RuntimeError('R26_SELECTED_METRIC_MISMATCH:'+k)
    return {'schema':'DF-G100-R26-SELECTED-CAMERA-VALIDATION-V1','status':'PASS','metrics':met,'admissibility':adm}
