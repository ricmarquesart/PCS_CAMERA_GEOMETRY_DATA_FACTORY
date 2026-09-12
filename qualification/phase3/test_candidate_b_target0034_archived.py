from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'SOURCE'))

import pcs_factory_micro100_gt as gt

CAPSULE = HERE / 'fixtures' / 'g101_target0034_capsule_v1.b64'
EXPECTED_CAPSULE_SCHEMA = 'DF-G101-PHASE3-ARCHIVED-TARGET0034-MINIMAL-CAPSULE-V1'
EXPECTED_SAMPLE_ID = 'g101v1_0034_intersection_near_infinity_blueprint'
EXPECTED_SHAPE = (216, 512)
EXPECTED_SOURCE_IDENTITY = {
    'request_json_sha256': 'a018ce9ef12ed94ef41fc132e8649a081671b697f7921d08aa21989d43423bdc',
    'object_index_exr_sha256': '7983879e85bf4f7e7cec7db4021dbdc7cab14a2d19576ae7c33686dfb6a0cb97',
    'old_normal_safe_mask_sha256': '32a540224e8c14ae4d7bc779cc5b7494d25a58104b34f412239c6aff0140e11a',
    'normal_authority_mask_sha256': '0603c2f57c4715495d521b7046d7bd067ce6924eaa1d290c91bfcaff9f54f2a1',
    'depth_filter_safe_mask_sha256': '32a540224e8c14ae4d7bc779cc5b7494d25a58104b34f412239c6aff0140e11a',
    'normal_exr_sha256': 'ec519e51e870257555a6c3731a9611294c77c28754ae2b1179d9b51ba0db9274',
    'depth_exr_sha256': '0715e67f48796fe626fac0dc665d362936365aaa9c42a8ae138026fb8d1b0f29',
}
EXPECTED_K = np.asarray([
    [615.1186858678312, 0.0, 255.49947278199747],
    [0.0, 615.1186858678312, 107.500554976683],
    [0.0, 0.0, 1.0],
], dtype=np.float64)
EXPECTED_DELTA = np.asarray([-0.0005272180025183681, 0.0005549766830098888], dtype=np.float64)
EXPECTED_OLD_COUNT = 53872
EXPECTED_NEW_COUNT = 53797
EXPECTED_EXCLUDED = 75
EXPECTED_RETENTION = 0.9986078111078112
EXPECTED_OLD_SHA = '32a540224e8c14ae4d7bc779cc5b7494d25a58104b34f412239c6aff0140e11a'
EXPECTED_NEW_SHA = 'e386310d6f09bc87bc76e4e1d5d87d06247d99d26c8cb29d6957f7678ea2d735'
EXPECTED_REASONS = {'SUBPIXEL_THIN_OCCLUDER_SUPPORT': 75}
EXPECTED_AUTHORITY_PIXELS = 53797
EXPECTED_AUTHORITY_FRACTION = 1.0
EXPECTED_UNEXPLAINED_INVALID = 0


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def digest_u8(a):
    return hashlib.sha256(np.asarray(a, dtype=np.uint8).tobytes(order='C')).hexdigest()


def load_capsule():
    text = CAPSULE.read_text(encoding='ascii')
    try:
        raw = zlib.decompress(base64.b64decode(text))
        cap = json.loads(raw.decode('utf-8'))
    except Exception as exc:
        raise AssertionError('TARGET0034_CAPSULE_DECODE_FAILED') from exc
    assert_true(cap.get('schema') == EXPECTED_CAPSULE_SCHEMA, 'target0034 capsule schema drift')
    assert_true(cap.get('sample_id') == EXPECTED_SAMPLE_ID, 'target0034 sample identity drift')
    assert_true(tuple(cap.get('shape', ())) == EXPECTED_SHAPE, 'target0034 raster shape drift')
    assert_true(cap.get('source_identity') == EXPECTED_SOURCE_IDENTITY, 'target0034 archived source identity drift')
    assert_true('sample_id' not in cap['request_minimal'], 'selection request must not contain sample identity')
    return cap


def decode_arrays(cap):
    shape = tuple(cap['shape'])
    oid = np.frombuffer(base64.b64decode(cap['oid_i16_b64']), dtype='<i2').reshape(shape).astype(np.int32)
    old = np.frombuffer(base64.b64decode(cap['old_normal_safe_u8_b64']), dtype=np.uint8).reshape(shape).astype(bool)
    auth = np.frombuffer(base64.b64decode(cap['normal_authority_u8_b64']), dtype=np.uint8).reshape(shape).astype(bool)
    depth_safe = np.frombuffer(base64.b64decode(cap['depth_filter_safe_u8_b64']), dtype=np.uint8).reshape(shape).astype(bool)
    return oid, old, auth, depth_safe


def run(out_path=None):
    cap = load_capsule()
    oid, old, authority, depth_safe = decode_arrays(cap)
    expected = cap['archived_expected']

    assert_true(int(np.count_nonzero(old)) == EXPECTED_OLD_COUNT, 'archived old-safe count drift')
    assert_true(digest_u8(old) == EXPECTED_OLD_SHA, 'archived old-safe digest drift')
    assert_true(int(expected['old_safe_count']) == EXPECTED_OLD_COUNT, 'capsule expected old-safe count drift')
    assert_true(expected['old_safe_sha256'] == EXPECTED_OLD_SHA, 'capsule expected old-safe digest drift')
    assert_true(int(expected['new_safe_count']) == EXPECTED_NEW_COUNT, 'capsule expected new-safe count drift')
    assert_true(int(expected['excluded_count']) == EXPECTED_EXCLUDED, 'capsule expected exclusion count drift')
    assert_true(float(expected['retained_fraction']) == EXPECTED_RETENTION, 'capsule expected retention drift')
    assert_true(expected['new_safe_sha256'] == EXPECTED_NEW_SHA, 'capsule expected new-safe digest drift')
    assert_true(expected['reason_counts'] == EXPECTED_REASONS, 'capsule expected reason counts drift')
    assert_true(int(expected['filter_safe_authority_pixels']) == EXPECTED_AUTHORITY_PIXELS, 'capsule expected authority pixels drift')
    assert_true(float(expected['filter_safe_authority_fraction']) == EXPECTED_AUTHORITY_FRACTION, 'capsule expected authority fraction drift')
    assert_true(int(expected['unexplained_invalid_count']) == EXPECTED_UNEXPLAINED_INVALID, 'capsule expected unexplained-invalid drift')

    # Frozen renderer-effective K is consumed by Normal only. Candidate B is not
    # permitted to steer K, Depth authority, acceptance, rendered Normal, RGB, or
    # sample/outcome identity.
    K = np.asarray(cap['final_renderer_effective_K'], dtype=np.float64)
    delta = np.asarray(cap['binding_delta_px'], dtype=np.float64)
    assert_true(np.array_equal(K, EXPECTED_K), 'target0034 renderer-effective K drift')
    assert_true(np.array_equal(delta, EXPECTED_DELTA), 'target0034 renderer-effective delta drift')
    old_before = old.copy()
    oid_before = oid.copy()
    K_before = K.copy()
    depth_before = depth_safe.copy()
    depth_digest_before = digest_u8(depth_before)

    t0 = time.perf_counter()
    new_safe, result = gt._phase3_candidate_b_normal_safe_mask(
        cap['request_minimal'],
        old,
        oid,
        K_override=K,
        renderer_filter_width_px=gt.G100_CYCLES_FILTER_WIDTH_PX,
    )
    runtime_seconds = time.perf_counter() - t0

    # Exact real-fixture equivalence to the independently archived Phase-2
    # Candidate-B adjudication. No tolerance or approximate mask comparison is
    # permitted here.
    assert_true(result['old_safe_count'] == EXPECTED_OLD_COUNT, 'production target0034 old count mismatch')
    assert_true(result['new_safe_count'] == EXPECTED_NEW_COUNT, 'production target0034 new count mismatch')
    assert_true(result['excluded_count'] == EXPECTED_EXCLUDED, 'production target0034 exclusion count mismatch')
    assert_true(result['retained_fraction'] == EXPECTED_RETENTION, 'production target0034 retention mismatch')
    assert_true(result['mask_sha256'] == EXPECTED_NEW_SHA, 'production target0034 mask digest mismatch')
    assert_true(result['reason_counts'] == EXPECTED_REASONS, 'production target0034 reason classification mismatch')
    assert_true(digest_u8(new_safe) == EXPECTED_NEW_SHA, 'production target0034 materialized mask digest mismatch')

    # Corrected Normal authority gate on the archived authority bitmap.
    filter_safe_pixels = int(np.count_nonzero(new_safe))
    filter_safe_authority_pixels = int(np.count_nonzero(new_safe & authority))
    filter_safe_authority_fraction = float(filter_safe_authority_pixels / filter_safe_pixels) if filter_safe_pixels else 0.0
    unexplained_invalid = int(np.count_nonzero(new_safe & ~authority))
    assert_true(filter_safe_authority_pixels == EXPECTED_AUTHORITY_PIXELS, 'target0034 corrected Normal authority pixel mismatch')
    assert_true(filter_safe_authority_fraction == EXPECTED_AUTHORITY_FRACTION, 'target0034 corrected Normal authority fraction mismatch')
    assert_true(unexplained_invalid == EXPECTED_UNEXPLAINED_INVALID, 'target0034 unexplained invalid Normal pixels remain')

    # Runtime non-mutation checks. Depth is deliberately not an input to the
    # Candidate-B function; its archived mask must remain byte-identical.
    assert_true(np.array_equal(old, old_before), 'Candidate B mutated inherited Normal-safe input')
    assert_true(np.array_equal(oid, oid_before), 'Candidate B mutated rendered Object Index input')
    assert_true(np.array_equal(K, K_before), 'Candidate B steered renderer-effective K')
    assert_true(np.array_equal(depth_safe, depth_before), 'Candidate B mutated archived Depth-safe mask')
    assert_true(digest_u8(depth_safe) == depth_digest_before == EXPECTED_OLD_SHA, 'Depth-safe digest changed')
    assert_true(result['depth_authority_mutated'] is False, 'production provenance reports Depth mutation')
    assert_true(result['camera_binding_steered'] is False, 'production provenance reports K steering')
    assert_true(result['rendered_normal_used_in_selection'] is False, 'rendered Normal used in selection')
    assert_true(result['rgb_used_in_selection'] is False, 'RGB used in selection')
    assert_true(result['acceptance_used_in_selection'] is False, 'acceptance used in selection')
    assert_true(result['sample_identity_used_in_selection'] is False, 'sample identity used in selection')
    assert_true(result['method_id'] == gt.PHASE3_CANDIDATE_B_METHOD_ID, 'Candidate-B method id drift')
    assert_true(result['retention_floor'] == gt.PHASE3_CANDIDATE_B_RETENTION_FLOOR, 'retention floor provenance drift')

    report = {
        'schema': 'DF-G101-PHASE3-TARGET0034-ARCHIVED-PRODUCTION-EQUIVALENCE-V1',
        'status': 'PASS',
        'sample_id': EXPECTED_SAMPLE_ID,
        'runtime_seconds': runtime_seconds,
        'shape': list(EXPECTED_SHAPE),
        'old_safe_count': result['old_safe_count'],
        'new_safe_count': result['new_safe_count'],
        'excluded_count': result['excluded_count'],
        'retained_fraction': result['retained_fraction'],
        'mask_sha256': result['mask_sha256'],
        'reason_counts': result['reason_counts'],
        'reason_digest_sha256': result['reason_digest_sha256'],
        'edge_touched_old_safe_count': result['edge_touched_old_safe_count'],
        'edge_pixel_pairs': result['edge_pixel_pairs'],
        'witness_exclusion_count': result['witness_exclusion_count'],
        'lattice_only_exclusion_count': result['lattice_only_exclusion_count'],
        'filter_safe_authority_pixels': filter_safe_authority_pixels,
        'filter_safe_authority_fraction': filter_safe_authority_fraction,
        'unexplained_invalid_count': unexplained_invalid,
        'depth_safe_sha256_before_after': depth_digest_before,
        'depth_authority_mutated': result['depth_authority_mutated'],
        'camera_binding_steered': result['camera_binding_steered'],
        'rendered_normal_used_in_selection': result['rendered_normal_used_in_selection'],
        'rgb_used_in_selection': result['rgb_used_in_selection'],
        'acceptance_used_in_selection': result['acceptance_used_in_selection'],
        'sample_identity_used_in_selection': result['sample_identity_used_in_selection'],
        'phase2_closure_drive_id': cap['provenance']['phase2_closure_drive_id'],
        'phase3_gate2_closure_drive_id': cap['provenance']['phase3_gate2_closure_drive_id'],
    }
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if out_path:
        Path(out_path).write_text(text, encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    args = ap.parse_args()
    run(args.out)


if __name__ == '__main__':
    main()
