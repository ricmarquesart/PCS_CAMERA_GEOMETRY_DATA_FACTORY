from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(REPO/'SOURCE'))

import candidate_b_optimized as opt
import candidate_b_direct_oracle as direct
import synthetic_cases as syn
import pcs_factory_micro100_gt as gt

FLOOR=0.9783428720083247
SYN1028_SHA='6b5882d76ddca5d0b8d3168a8afcb1f1837b3ff1e03bc1c5081d03d8edfb0948'
SYN1016_SHA='0db44c07f67c42aec099584271ba9ef2454f567685b42f8299264f450217011a'


def assert_true(v,msg):
    if not v: raise AssertionError(msg)


def case_by_id(target):
    for it in (syn.iter_standard(),syn.iter_ultrathin()):
        for req,meta,kind in it:
            if req['sample_id']==target:return req,meta,kind
    raise KeyError(target)


def old_for(req):
    co,cf,ca=opt.analytic_centers(req)
    assert_true(not np.any(ca),'unexpected integer-center ambiguity')
    oid=co.astype(np.int32)
    labels=np.where(oid>0,(oid-1)*6+cf,-1).astype(np.int32)
    old=gt._filter_safe_interior_mask(oid,labels,2)
    ref=opt.inherited_r6_mask(oid,cf,2)
    assert_true(np.array_equal(old,ref),'production inherited R6 mismatch')
    return old,oid


def reason_digest(reasons):
    rows=sorted((f'{x},{y}',v) for (x,y),v in reasons.items())
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()


def compare_case(case_id,expected_sha=None):
    req,_meta,_kind=case_by_id(case_id); old,oid=old_for(req)
    t0=time.perf_counter(); pmask,pres=gt._phase3_candidate_b_normal_safe_mask(req,old,oid); prod_s=time.perf_counter()-t0
    t1=time.perf_counter(); omask,ores=opt.evaluate_mask(req,old,oid); opt_s=time.perf_counter()-t1
    assert_true(np.array_equal(pmask,omask),case_id+': production mask != qualified optimized reference')
    assert_true(pres['reason_by_pixel']==ores['reason_by_pixel'],case_id+': production reasons != qualified reference')
    assert_true(pres['old_safe_count']==ores['old_safe_count'],case_id+': old count')
    assert_true(pres['new_safe_count']==ores['new_safe_count'],case_id+': new count')
    assert_true(pres['excluded_count']==ores['excluded_count'],case_id+': exclusion count')
    assert_true(pres['retained_fraction']==ores['retained_fraction'],case_id+': retention')
    assert_true(pres['mask_sha256']==ores['mask_sha256'],case_id+': mask digest')
    assert_true(pres['reason_digest_sha256']==reason_digest(ores['reason_by_pixel']),case_id+': reason digest')
    assert_true(pres['method_id']==gt.PHASE3_CANDIDATE_B_METHOD_ID,case_id+': method id')
    if expected_sha is not None:assert_true(pres['mask_sha256']==expected_sha,case_id+': frozen mask digest')
    return {'case_id':case_id,'production_seconds':prod_s,'qualified_reference_seconds':opt_s,
            'old_safe_count':pres['old_safe_count'],'new_safe_count':pres['new_safe_count'],
            'excluded_count':pres['excluded_count'],'retained_fraction':pres['retained_fraction'],
            'mask_sha256':pres['mask_sha256'],'reason_digest_sha256':pres['reason_digest_sha256'],
            'witness_exclusion_count':pres['witness_exclusion_count'],'lattice_only_exclusion_count':pres['lattice_only_exclusion_count']}


def run():
    assert_true(gt.PHASE3_CANDIDATE_B_RETENTION_FLOOR==FLOOR,'production floor changed')
    rows=[]
    rows.append(compare_case('syn_000_VERTICAL_VISIBLE_0.015625'))
    rows.append(compare_case('syn_001_VERTICAL_OCCLUDED_0.015625'))
    r1028=compare_case('syn_1028_HORIZONTAL_VISIBLE_3.0517578125e-05',SYN1028_SHA); rows.append(r1028)
    r1016=compare_case('syn_1016_DIAGONAL_VISIBLE_0.0001220703125',SYN1016_SHA); rows.append(r1016)
    assert_true(r1028['new_safe_count']==15060 and r1028['excluded_count']==316,'syn1028 frozen full-domain counts')
    assert_true(r1028['witness_exclusion_count']==170 and r1028['lattice_only_exclusion_count']==146,'syn1028 witness/lattice split')
    assert_true(r1016['new_safe_count']==15043 and r1016['excluded_count']==333,'syn1016 frozen counts')
    assert_true(r1016['retained_fraction']==FLOOR,'syn1016 must define retention floor')

    # Independent literal direct lattice oracle on the two hardest frozen anchors.
    for case_id,expected in (
        ('syn_1028_HORIZONTAL_VISIBLE_3.0517578125e-05',SYN1028_SHA),
        ('syn_1016_DIAGONAL_VISIBLE_0.0001220703125',SYN1016_SHA),
    ):
        req,_m,_k=case_by_id(case_id); old,oid=old_for(req)
        pmask,pres=gt._phase3_candidate_b_normal_safe_mask(req,old,oid)
        dmask,dres=direct.full_lattice_mask(req,old)
        assert_true(np.array_equal(pmask,dmask),case_id+': production != direct full-domain oracle')
        assert_true(dres['mask_sha256']==expected,case_id+': direct frozen digest')

    # Determinism, including exact primary reason classification.
    req,_m,_k=case_by_id('syn_1028_HORIZONTAL_VISIBLE_3.0517578125e-05'); old,oid=old_for(req)
    m1,p1=gt._phase3_candidate_b_normal_safe_mask(req,old,oid); m2,p2=gt._phase3_candidate_b_normal_safe_mask(req,old,oid)
    assert_true(np.array_equal(m1,m2),'production mask non-deterministic')
    assert_true(p1['reason_digest_sha256']==p2['reason_digest_sha256'],'production reasons non-deterministic')

    # Frozen filter-width provenance must fail closed.
    try:
        gt._phase3_candidate_b_normal_safe_mask(req,old,oid,renderer_filter_width_px=1.500001)
    except RuntimeError as exc:
        assert_true('RENDER_FILTER_WIDTH_MISMATCH' in str(exc),'wrong filter-width failure')
    else:
        raise AssertionError('altered filter width did not fail closed')

    # The retention guard itself must fail closed below the frozen floor.
    try:
        gt._phase3_candidate_b_require_retention(1000,978)
    except RuntimeError as exc:
        assert_true('RETENTION_BELOW_FROZEN_FLOOR' in str(exc),'wrong retention failure')
    else:
        raise AssertionError('retention below floor did not fail closed')

    rep={'schema':'DF-G101-PHASE3-GATE2-PRODUCTION-ANCHORS-V1','status':'PASS','floor':FLOOR,'rows':rows}
    print(json.dumps(rep,sort_keys=True))


if __name__=='__main__':run()
