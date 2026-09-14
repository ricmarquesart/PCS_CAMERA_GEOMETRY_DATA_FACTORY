from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'SOURCE'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pcs_factory_micro100_gt as gt
import candidate_b_reference as cb


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


def make_case(width_px=0.015625, occluded=False, u0=31.1, v0=31.5):
    W = 64
    H = 64
    fx = 60.0
    K = np.array([[fx, 0, 31.5], [0, fx, 31.5], [0, 0, 1]], float)
    Rwc = np.eye(3)
    C = np.zeros(3)
    twc = np.zeros(3)
    z = 6.0
    thin_z = 12.0 if occluded else z
    xcam = (u0 - 31.5) / fx * thin_z
    ycam = (v0 - 31.5) / fx * thin_z
    width_m = width_px * thin_z / fx

    def obj(oid, c, d, R=np.eye(3)):
        return {
            'object_id': oid,
            'center_world': list(map(float, c)),
            'dimensions_m': list(map(float, d)),
            'R_local_to_world': np.asarray(R, float).tolist(),
        }

    bg = obj('synthetic.background', [0, 0, 10], [18, 18, 0.08])
    thin = obj('synthetic.thin', [xcam, ycam, thin_z], [width_m, 3.8, 0.002])
    return {
        'sample_id': f'candidate_b_{width_px}_{occluded}',
        'camera': {
            'width': W,
            'height': H,
            'K': K.tolist(),
            'pose': {
                'camera_center_world': C.tolist(),
                'R_world_to_camera_cv': Rwc.tolist(),
                't_world_to_camera_cv': twc.tolist(),
            },
        },
        'scene': {'objects': [bg, thin]},
    }


def center_oid_and_old_safe(req):
    H = int(req['camera']['height'])
    W = int(req['camera']['width'])
    yy, xx = np.indices((H, W), dtype=float)
    oo, ff, aa = cb.batch_signatures(req, np.column_stack([xx.ravel(), yy.ravel()]))
    assert_true(not np.any(aa), 'unexpected center ambiguity in synthetic fixture')
    oid = oo.reshape(H, W).astype(np.int32)
    face = ff.reshape(H, W)
    labels = np.where(oid > 0, (oid - 1) * 6 + face, -1).astype(np.int32)
    return oid, gt._filter_safe_interior_mask(oid, labels, 2)


def local_results(req, oid, old_safe):
    rows = {}
    for y in range(26, 38):
        for x in range(26, 38):
            if old_safe[y, x]:
                rows[(x, y)] = cb.evaluate_pixel(req, x, y, oid)
    return rows


def canonical(rows):
    return json.dumps(
        {f'{x},{y}': v for (x, y), v in sorted(rows.items())},
        sort_keys=True,
        separators=(',', ':'),
    )


def run():
    vis = make_case(0.015625, False)
    oid, old = center_oid_and_old_safe(vis)
    assert_true(int(np.count_nonzero(oid == 2)) == 0, 'fixture must be center-invisible')
    vr = local_results(vis, oid, old)
    unsafe = [v for v in vr.values() if not v['safe']]
    assert_true(len(unsafe) > 0, 'visible center-invisible thin occluder was missed')
    assert_true(
        any(v['reason'] == 'SUBPIXEL_THIN_OCCLUDER_SUPPORT' for v in unsafe),
        'thin occluder reason missing',
    )

    occ = make_case(0.015625, True)
    oo, os = center_oid_and_old_safe(occ)
    assert_true(int(np.count_nonzero(oo == 2)) == 0, 'occluded thin object unexpectedly center-visible')
    orows = local_results(occ, oo, os)
    assert_true(all(v['safe'] for v in orows.values()), 'fully occluded projected geometry created false erosion')

    ultra = make_case(0.000030517578125, False)
    uo, us = center_oid_and_old_safe(ultra)
    ur = local_results(ultra, uo, us)
    uunsafe = [v for v in ur.values() if not v['safe']]
    assert_true(len(uunsafe) > 0, 'ultra-thin geometry escaped Candidate B')
    assert_true(
        any(v.get('edge_witness') is not None for v in uunsafe),
        'ultra-thin exclusion lacks geometry-seeded edge witness',
    )

    p = next(p for p, v in vr.items() if not v['safe'] and v['reason'] == 'SUBPIXEL_THIN_OCCLUDER_SUPPORT')
    altered = oid.copy()
    x, y = p
    altered[y, x + 1] = 2
    a = cb.evaluate_pixel(vis, x, y, altered)
    assert_true(not a['safe'], 'rendered Object Index overrode analytic unsafe witness')
    assert_true(
        a['reason'] in {'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT', 'SUBPIXEL_THIN_OCCLUDER_SUPPORT'},
        'unexpected classification after OID cross-check change',
    )

    border = cb.evaluate_pixel(vis, 0, 0, oid)
    assert_true(
        border['safe'] is False and border['reason'] == 'IMAGE_BOUND_SUPPORT_INCOMPLETE',
        'image-bound fail-closed rule failed',
    )

    vr2 = local_results(vis, oid, old)
    assert_true(canonical(vr) == canonical(vr2), 'Candidate B focused results are not deterministic')

    interior = cb.evaluate_pixel(vis, 10, 10, oid)
    assert_true(interior['safe'] is True, 'deep interior was incorrectly excluded')

    print(json.dumps({
        'status': 'PASS',
        'method_id': cb.METHOD_ID,
        'visible_center_invisible_unsafe_count': len(unsafe),
        'ultrathin_unsafe_count': len(uunsafe),
        'occluded_unsafe_count': sum(not v['safe'] for v in orows.values()),
        'deterministic': True,
    }, sort_keys=True))


if __name__ == '__main__':
    run()
