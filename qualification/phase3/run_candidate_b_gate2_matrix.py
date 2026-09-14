from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(REPO/'SOURCE'))

import candidate_b_reference as cb
import candidate_b_optimized as opt
import candidate_b_direct_oracle as direct
import synthetic_cases as syn
import pcs_factory_micro100_gt as gt


def old_for(req):
    co,cf,ca=opt.analytic_centers(req)
    if np.any(ca):raise RuntimeError('INTEGER_CENTER_ANALYTIC_AMBIGUITY')
    oid=co.astype(np.int32)
    labels=np.where(oid>0,(oid-1)*6+cf,-1).astype(np.int32)
    old=gt._filter_safe_interior_mask(oid,labels,2)
    if not np.array_equal(old,opt.inherited_r6_mask(oid,cf,2)):raise RuntimeError('INHERITED_R6_BASELINE_MISMATCH')
    return old,oid


def edge_touched_pixels(req,old,K_override=None):
    H,W=old.shape; fw=cb.FILTER_WIDTH_PX; touched=set()
    for _oi,_ei,p0,p1 in cb.projected_edges(req,K_override):
        xmin=max(0,int(math.ceil(min(p0[0],p1[0])-fw-1e-12))); xmax=min(W-1,int(math.floor(max(p0[0],p1[0])+fw+1e-12)))
        ymin=max(0,int(math.ceil(min(p0[1],p1[1])-fw-1e-12))); ymax=min(H-1,int(math.floor(max(p0[1],p1[1])+fw+1e-12)))
        if xmin>xmax or ymin>ymax:continue
        for y in range(ymin,ymax+1):
            for x in range(xmin,xmax+1):
                if old[y,x] and cb._clip_segment(p0,p1,x-fw,x+fw,y-fw,y+fw) is not None:touched.add((x,y))
    return touched


def literal_direct_candidate_b(req,old,oid,K_override=None):
    """Complete direct reference: full lattice everywhere + literal B on edge supports."""
    lattice,lmeta=direct.full_lattice_mask(req,old,K_override)
    final=lattice.copy(); touched=edge_touched_pixels(req,old,K_override)
    need=set(touched)
    for y,x in np.argwhere(old & ~lattice):need.add((int(x),int(y)))
    reasons={}
    for x,y in sorted(need,key=lambda p:(p[1],p[0])):
        ev=cb.evaluate_pixel(req,x,y,oid,K_override)
        if not ev['safe']:
            final[y,x]=False; reasons[(x,y)]=ev['reason']
    excluded={(int(x),int(y)) for y,x in np.argwhere(old & ~final)}
    missing=excluded-set(reasons)
    if missing:
        for x,y in sorted(missing,key=lambda p:(p[1],p[0])):
            ev=cb.evaluate_pixel(req,x,y,oid,K_override)
            if ev['safe']:raise RuntimeError('DIRECT_ORACLE_REASON_MISSING_SAFE:'+str((x,y)))
            reasons[(x,y)]=ev['reason']
    reason_rows=sorted((f'{x},{y}',r) for (x,y),r in reasons.items())
    return final,{
        'old_safe_count':int(np.count_nonzero(old)),'new_safe_count':int(np.count_nonzero(final)),
        'excluded_count':int(np.count_nonzero(old&~final)),'reason_by_pixel':reasons,
        'mask_sha256':hashlib.sha256(final.astype(np.uint8).tobytes(order='C')).hexdigest(),
        'reason_digest_sha256':hashlib.sha256(json.dumps(reason_rows,separators=(',',':')).encode()).hexdigest(),
        'edge_touched_old_safe_count':len(touched),'direct_lattice_excluded_count':lmeta['lattice_excluded_count'],
    }


def row(req,meta,kind):
    old,oid=old_for(req)
    t0=time.perf_counter(); pmask,pres=gt._phase3_candidate_b_normal_safe_mask(req,old,oid); prod_s=time.perf_counter()-t0
    t1=time.perf_counter(); dmask,dres=literal_direct_candidate_b(req,old,oid); direct_s=time.perf_counter()-t1
    if not np.array_equal(pmask,dmask):raise RuntimeError('PRODUCTION_DIRECT_MASK_XOR:'+req['sample_id']+':'+str(int(np.count_nonzero(pmask^dmask))))
    if pres['reason_by_pixel']!=dres['reason_by_pixel']:
        keys=set(pres['reason_by_pixel'])|set(dres['reason_by_pixel']); dif=[p for p in keys if pres['reason_by_pixel'].get(p)!=dres['reason_by_pixel'].get(p)]
        raise RuntimeError('PRODUCTION_DIRECT_REASON_XOR:'+req['sample_id']+':'+str(len(dif))+':'+str(sorted(dif)[:8]))
    if pres['mask_sha256']!=dres['mask_sha256'] or pres['reason_digest_sha256']!=dres['reason_digest_sha256']:
        raise RuntimeError('PRODUCTION_DIRECT_DIGEST_MISMATCH:'+req['sample_id'])
    center_samples=int(np.count_nonzero(oid==2)) if len(req['scene']['objects'])>=2 else 0
    if kind=='OCCLUDED' and pres['excluded_count']!=0:raise RuntimeError('OCCLUDED_FALSE_EROSION:'+req['sample_id'])
    if kind=='VISIBLE' and center_samples==0 and pres['excluded_count']<=0:raise RuntimeError('CENTER_INVISIBLE_VISIBLE_OCCLUDER_MISSED:'+req['sample_id'])
    return {'case_id':req['sample_id'],'kind':kind,'old_safe':pres['old_safe_count'],'new_safe':pres['new_safe_count'],'excluded':pres['excluded_count'],
            'retained_fraction':pres['retained_fraction'],'mask_sha256':pres['mask_sha256'],'reason_digest_sha256':pres['reason_digest_sha256'],
            'witness_exclusions':pres['witness_exclusion_count'],'lattice_only_exclusions':pres['lattice_only_exclusion_count'],
            'edge_touched_old_safe_count':pres['edge_touched_old_safe_count'],'thin_center_samples':center_samples,
            'reason_counts':pres['reason_counts'],'target_width_px':meta.get('target_width_px'),
            'production_seconds':prod_s,'direct_reference_seconds':direct_s,'direct_lattice_excluded':dres['direct_lattice_excluded_count']}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--suite',choices=['standard','ultrathin','phase','special'],required=True)
    ap.add_argument('--orientation',choices=list(syn.ORIENTS),default=None); ap.add_argument('--mode',choices=['visible','occluded'],default=None)
    ap.add_argument('--out',required=True); args=ap.parse_args(); occ=None if args.mode is None else args.mode=='occluded'; rows=[]
    if args.suite=='standard':iterator=syn.iter_standard(args.orientation,occ)
    elif args.suite=='ultrathin':iterator=syn.iter_ultrathin(args.orientation,occ)
    elif args.suite=='phase':iterator=syn.iter_phase_shift(args.orientation,occ)
    else:
        iterator=[]
        for name in ('DEEP_INTERIOR','CREASE','OUTSIDE_SUPPORT','COPLANAR_SPLIT','NONCOPLANAR_STEP'):
            req,meta=syn.special_case(name); iterator.append((req,meta,'SPECIAL'))
    for req,meta,kind in iterator:
        r=row(req,meta,kind); rows.append(r)
        if req['sample_id']=='syn_special_DEEP_INTERIOR' and r['excluded']!=0:raise RuntimeError('DEEP_INTERIOR_FALSE_EROSION')
    if not rows:raise RuntimeError('EMPTY_GATE2_MATRIX_SHARD')
    semantic=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(); minimum=min(rows,key=lambda r:r['retained_fraction'])
    rep={'schema':'DF-G101-PHASE3-GATE2-PRODUCTION-DIRECT-MATRIX-SHARD-V1','status':'PASS','suite':args.suite,'orientation':args.orientation,'mode':args.mode,
         'case_count':len(rows),'semantic_digest':semantic,'minimum_retention':minimum['retained_fraction'],'minimum_case_id':minimum['case_id'],
         'total_excluded':sum(r['excluded'] for r in rows),'total_lattice_only_exclusions':sum(r['lattice_only_exclusions'] for r in rows),
         'production_seconds_total':sum(r['production_seconds'] for r in rows),'direct_reference_seconds_total':sum(r['direct_reference_seconds'] for r in rows),'rows':rows}
    Path(args.out).write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:rep[k] for k in ('status','suite','orientation','mode','case_count','semantic_digest','minimum_retention','minimum_case_id','total_excluded','total_lattice_only_exclusions','production_seconds_total','direct_reference_seconds_total')},sort_keys=True))


if __name__=='__main__':main()
