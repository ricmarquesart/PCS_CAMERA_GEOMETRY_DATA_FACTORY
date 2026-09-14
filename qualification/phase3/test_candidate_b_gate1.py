from __future__ import annotations
import hashlib
import json
import sys
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

FLOOR=0.9783428720083247
SYN1028_SHA='6b5882d76ddca5d0b8d3168a8afcb1f1837b3ff1e03bc1c5081d03d8edfb0948'
SYN1016_SHA='0db44c07f67c42aec099584271ba9ef2454f567685b42f8299264f450217011a'
PHASE2_26={(x,y) for y in (62,65) for x in range(64,77)}


def assert_true(v,msg):
    if not v: raise AssertionError(msg)


def old_for(req):
    co,cf,ca=opt.analytic_centers(req)
    assert_true(not np.any(ca),'unexpected integer-center ambiguity')
    oid=co.astype(np.int32)
    old=opt.inherited_r6_mask(oid,cf,2)
    # Cross-check the inherited production primitive itself. This is only a
    # regression check; Candidate B never replaces the shared Depth mask.
    labels=np.where(oid>0,(oid-1)*6+cf,-1).astype(np.int32)
    prod=gt._filter_safe_interior_mask(oid,labels,2)
    assert_true(np.array_equal(old,prod),'independent R6 baseline != production inherited mask')
    return old,oid


def case_by_id(target):
    for it in (syn.iter_standard(),syn.iter_ultrathin()):
        for req,meta,kind in it:
            if req['sample_id']==target: return req,meta,kind
    raise KeyError(target)


def mask_sha(mask):
    return hashlib.sha256(np.asarray(mask,dtype=np.uint8).tobytes(order='C')).hexdigest()


def run():
    results={}

    # Frozen standard visible anchor: full Candidate B remains the Phase-2 mask.
    req,meta,kind=case_by_id('syn_000_VERTICAL_VISIBLE_0.015625')
    old,oid=old_for(req); mask,r=opt.evaluate_mask(req,old,oid)
    assert_true(int(old.sum())==10816,'syn000 old count')
    assert_true(r['new_safe_count']==10657 and r['excluded_count']==159,'syn000 counts')
    assert_true(r['mask_sha256']=='7e230f4ee63e35294baabfe328fea471820f5216a3bd2fa3dccb8478ac556667','syn000 mask')
    opt.require_retention(r); results['syn000']=r

    # Fully occluded negative control must not erode authority.
    req,meta,kind=case_by_id('syn_001_VERTICAL_OCCLUDED_0.015625')
    old,oid=old_for(req); mask,r=opt.evaluate_mask(req,old,oid)
    assert_true(r['old_safe_count']==15376 and r['new_safe_count']==15376 and r['excluded_count']==0,'occluded false erosion')
    assert_true(r['mask_sha256']=='e08573974d525e30068d971e95b9f7b0b1b4b2d3c89570f28f09cf0776da2755','occluded mask')
    results['syn001']=r

    # Full-domain clarification anchor. The old Phase-2 bounded B field reported
    # 26 extra controls; complete Candidate B has 146 lattice-only extras.
    req,meta,kind=case_by_id('syn_1028_HORIZONTAL_VISIBLE_3.0517578125e-05')
    old,oid=old_for(req); mask,r=opt.evaluate_mask(req,old,oid)
    dmask,dr=direct.full_lattice_mask(req,old)
    assert_true(r['old_safe_count']==15376,'syn1028 old count')
    assert_true(r['new_safe_count']==15060 and r['excluded_count']==316,'syn1028 full-domain counts')
    assert_true(r['witness_exclusion_count']==170 and r['lattice_only_exclusion_count']==146,'syn1028 witness/lattice split')
    assert_true(r['mask_sha256']==SYN1028_SHA,'syn1028 optimized hash')
    assert_true(dr['lattice_excluded_count']==316 and dr['mask_sha256']==SYN1028_SHA,'syn1028 direct lattice')
    assert_true(np.array_equal(mask,dmask),'syn1028 optimized != direct full lattice')
    assert_true(PHASE2_26 <= set(r['reason_by_pixel']),'the frozen Phase-2 26 are not preserved unsafe')
    assert_true(abs(r['retained_fraction']-0.9794484911550468)<1e-15,'syn1028 retention')
    opt.require_retention(r); results['syn1028']={k:v for k,v in r.items() if k not in ('reason_by_pixel','evidence_by_pixel')}

    # Frozen global retention-floor anchor. Direct and optimized masks must be exact.
    req,meta,kind=case_by_id('syn_1016_DIAGONAL_VISIBLE_0.0001220703125')
    old,oid=old_for(req); mask,r=opt.evaluate_mask(req,old,oid)
    dmask,dr=direct.full_lattice_mask(req,old)
    assert_true(r['old_safe_count']==15376 and r['new_safe_count']==15043 and r['excluded_count']==333,'syn1016 counts')
    assert_true(r['mask_sha256']==SYN1016_SHA and dr['mask_sha256']==SYN1016_SHA,'syn1016 hash')
    assert_true(np.array_equal(mask,dmask),'syn1016 optimized != direct full lattice')
    assert_true(r['retained_fraction']==FLOOR,'frozen retention floor changed')
    opt.require_retention(r); results['syn1016']={k:v for k,v in r.items() if k not in ('reason_by_pixel','evidence_by_pixel')}

    # Determinism on the divergence anchor.
    req,meta,kind=case_by_id('syn_1028_HORIZONTAL_VISIBLE_3.0517578125e-05')
    old,oid=old_for(req); m1,r1=opt.evaluate_mask(req,old,oid); m2,r2=opt.evaluate_mask(req,old,oid)
    assert_true(np.array_equal(m1,m2),'optimized mask non-deterministic')
    digest1=hashlib.sha256(json.dumps(sorted((f'{x},{y}',v) for (x,y),v in r1['reason_by_pixel'].items()),separators=(',',':')).encode()).hexdigest()
    digest2=hashlib.sha256(json.dumps(sorted((f'{x},{y}',v) for (x,y),v in r2['reason_by_pixel'].items()),separators=(',',':')).encode()).hexdigest()
    assert_true(digest1==digest2,'reason classification non-deterministic')

    # Retention guard itself is fail-closed.
    try:
        opt.require_retention({'retained_fraction':FLOOR-1e-6})
    except RuntimeError as exc:
        assert_true('RETENTION_BELOW_FROZEN_FLOOR' in str(exc),'wrong retention failure')
    else:
        raise AssertionError('retention below floor did not fail closed')

    print(json.dumps({'status':'PASS','floor':FLOOR,'syn1028_complete_mask_sha256':SYN1028_SHA,'syn1016_floor_mask_sha256':SYN1016_SHA,'deterministic_reason_digest':digest1,'anchors':{k:{kk:vv for kk,vv in v.items() if kk not in ('reason_by_pixel','evidence_by_pixel')} for k,v in results.items()}},sort_keys=True,default=str))


if __name__=='__main__': run()
