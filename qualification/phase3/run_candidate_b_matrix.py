from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(REPO/'SOURCE'))
import candidate_b_optimized as opt
import synthetic_cases as syn


def old_for(req):
    co,cf,ca=opt.analytic_centers(req)
    if np.any(ca): raise RuntimeError('INTEGER_CENTER_ANALYTIC_AMBIGUITY')
    oid=co.astype(np.int32); old=opt.inherited_r6_mask(oid,cf,2)
    return old,oid


def row(req,meta,kind):
    old,oid=old_for(req); mask,res=opt.evaluate_mask(req,old,oid); opt.require_retention(res)
    center_samples=int(np.count_nonzero(oid==2)) if len(req['scene']['objects'])>=2 else 0
    if kind=='OCCLUDED' and res['excluded_count']!=0:
        raise RuntimeError('OCCLUDED_FALSE_EROSION:'+req['sample_id'])
    if kind=='VISIBLE' and center_samples==0 and res['excluded_count']<=0:
        raise RuntimeError('CENTER_INVISIBLE_VISIBLE_OCCLUDER_MISSED:'+req['sample_id'])
    return {
        'case_id':req['sample_id'],'kind':kind,'old_safe':res['old_safe_count'],'new_safe':res['new_safe_count'],
        'excluded':res['excluded_count'],'retained_fraction':res['retained_fraction'],'mask_sha256':res['mask_sha256'],
        'witness_exclusions':res['witness_exclusion_count'],'lattice_only_exclusions':res['lattice_only_exclusion_count'],
        'edge_touched_old_safe_count':res['edge_touched_old_safe_count'],'thin_center_samples':center_samples,
        'reason_counts':res['reason_counts'],'target_width_px':meta.get('target_width_px')
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--suite',choices=['standard','ultrathin','phase','special'],required=True)
    ap.add_argument('--orientation',choices=list(syn.ORIENTS),default=None); ap.add_argument('--mode',choices=['visible','occluded'],default=None)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    occ=None if args.mode is None else args.mode=='occluded'; rows=[]
    if args.suite=='standard': iterator=syn.iter_standard(args.orientation,occ)
    elif args.suite=='ultrathin': iterator=syn.iter_ultrathin(args.orientation,occ)
    elif args.suite=='phase': iterator=syn.iter_phase_shift(args.orientation,occ)
    else:
        iterator=[]
        for name in ('DEEP_INTERIOR','CREASE','OUTSIDE_SUPPORT','COPLANAR_SPLIT','NONCOPLANAR_STEP'):
            req,meta=syn.special_case(name); iterator.append((req,meta,'SPECIAL'))
    for req,meta,kind in iterator:
        r=row(req,meta,kind); rows.append(r)
        if req['sample_id']=='syn_special_DEEP_INTERIOR' and r['excluded']!=0:
            raise RuntimeError('DEEP_INTERIOR_FALSE_EROSION')
    if not rows: raise RuntimeError('EMPTY_MATRIX_SHARD')
    semantic=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    minimum=min(rows,key=lambda r:r['retained_fraction'])
    rep={'schema':'DF-G101-PHASE3-CANDIDATE-B-MATRIX-SHARD-V1','status':'PASS','suite':args.suite,'orientation':args.orientation,'mode':args.mode,
         'case_count':len(rows),'semantic_digest':semantic,'minimum_retention':minimum['retained_fraction'],'minimum_case_id':minimum['case_id'],
         'total_excluded':sum(r['excluded'] for r in rows),'total_lattice_only_exclusions':sum(r['lattice_only_exclusions'] for r in rows),'rows':rows}
    Path(args.out).write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:rep[k] for k in ('status','suite','orientation','mode','case_count','semantic_digest','minimum_retention','minimum_case_id','total_excluded','total_lattice_only_exclusions')},sort_keys=True))


if __name__=='__main__': main()
