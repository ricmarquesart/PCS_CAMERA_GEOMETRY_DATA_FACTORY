from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(REPO/'SOURCE'))

import candidate_b_optimized as opt
import synthetic_cases as syn
import pcs_factory_micro100_gt as gt


def assert_true(v,msg):
    if not v:raise AssertionError(msg)


def old_for(req):
    co,cf,ca=opt.analytic_centers(req)
    if np.any(ca):raise RuntimeError('unexpected center ambiguity in fixture')
    oid=co.astype(np.int32); labels=np.where(oid>0,(oid-1)*6+cf,-1).astype(np.int32)
    return gt._filter_safe_interior_mask(oid,labels,2),oid


def find_case(target):
    for req,meta,kind in syn.iter_ultrathin():
        if req['sample_id']==target:return req,meta,kind
    raise KeyError(target)


def run():
    # Deep corrected interior: good analytic unit normals pass; a non-unit value
    # stays invalid/unexplained and a wrong unit direction still fails 1e-5.
    req,_meta=syn.special_case('DEEP_INTERIOR'); old,oid=old_for(req); objmask=oid>0
    C=np.asarray(req['camera']['pose']['camera_center_world'],dtype=np.float64); K=np.asarray(req['camera']['K'],dtype=np.float64)
    zeros=np.zeros((int(req['camera']['height']),int(req['camera']['width']),3),dtype=np.float64)
    probe=gt._r21_normal_eval_for_K(req,C,zeros,oid,objmask,2,K)
    raw_good=np.einsum('ij,hwj->hwi',np.asarray(gt.B_FROM_C,dtype=np.float64),probe['pred_ncan'])
    good=gt._r21_normal_eval_for_K(req,C,raw_good,oid,objmask,2,K)
    assert_true(good['normal_ok'],'analytic good Normal did not pass')
    safe_coords=np.argwhere(good['filter_safe']&objmask)
    assert_true(len(safe_coords)>0,'no deep Candidate-B-safe pixel')
    y,x=map(int,safe_coords[len(safe_coords)//2])

    nonunit=raw_good.copy(); nonunit[y,x]*=0.5
    bad_nonunit=gt._r21_normal_eval_for_K(req,C,nonunit,oid,objmask,2,K)
    assert_true(not bad_nonunit['normal_ok'] and bad_nonunit['unexplained_count']>=1,'non-unit deep interior was incorrectly excused')

    wrong=raw_good.copy(); wrong[y,x]*=-1.0
    bad_dir=gt._r21_normal_eval_for_K(req,C,wrong,oid,objmask,2,K)
    assert_true(not bad_dir['normal_ok'],'wrong unit direction passed Normal direction gate')
    assert_true(float(np.max(bad_dir['safe_raw_err']))>gt.NORMAL_GEOM_TOL,'wrong direction did not exceed frozen tolerance')

    # Sample identity is a forbidden selector: identical geometry with arbitrary
    # IDs must produce byte-identical masks and reasons.
    req,_m,_k=find_case('syn_1028_HORIZONTAL_VISIBLE_3.0517578125e-05'); old,oid=old_for(req)
    m1,r1=gt._phase3_candidate_b_normal_safe_mask(req,old,oid)
    renamed=copy.deepcopy(req); renamed['sample_id']='completely_unrelated_identity'
    m2,r2=gt._phase3_candidate_b_normal_safe_mask(renamed,old,oid)
    assert_true(np.array_equal(m1,m2),'sample identity changed Candidate-B mask')
    assert_true(r1['reason_digest_sha256']==r2['reason_digest_sha256'],'sample identity changed Candidate-B reasons')

    # Geometry perturbation must change only through analytic geometry and still
    # remain exactly equivalent to the independently qualified implementation.
    pert=copy.deepcopy(req)
    pert['scene']['objects'][1]['center_world'][0]=float(pert['scene']['objects'][1]['center_world'][0])+0.01
    pold,poid=old_for(pert); pm,pr=gt._phase3_candidate_b_normal_safe_mask(pert,pold,poid); om,orr=opt.evaluate_mask(pert,pold,poid)
    assert_true(np.array_equal(pm,om),'perturbed geometry production/reference mask mismatch')
    assert_true(pr['reason_by_pixel']==orr['reason_by_pixel'],'perturbed geometry production/reference reason mismatch')

    # Force the analytic ambiguity signal at one inherited-safe center to prove
    # the production path fails closed rather than silently eroding authority.
    amb_req,_am=syn.special_case('DEEP_INTERIOR'); amb_old,amb_oid=old_for(amb_req)
    original=gt._phase3_b_analytic_centers
    def forced(request,K_override=None):
        o,f,a=original(request,K_override); a=a.copy(); yy,xx=np.argwhere(amb_old)[0]; a[int(yy),int(xx)]=True; return o,f,a
    gt._phase3_b_analytic_centers=forced
    try:
        try:
            gt._phase3_candidate_b_normal_safe_mask(amb_req,amb_old,amb_oid)
        except RuntimeError as exc:
            assert_true('UNCLASSIFIED_ANALYTIC_AMBIGUITY' in str(exc),'wrong ambiguity failure')
        else:
            raise AssertionError('unclassified analytic ambiguity did not fail closed')
    finally:
        gt._phase3_b_analytic_centers=original

    print('PHASE3 GATE2 NEGATIVE/FAIL-CLOSED TESTS: PASS')


if __name__=='__main__':run()
