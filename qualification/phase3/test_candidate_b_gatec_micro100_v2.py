from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'SOURCE' / 'pcs_factory_micro100_gt.py'
FIX = Path(__file__).resolve().parent / 'fixtures' / 'micro100_gatec_v2'
MANIFEST_PATH = FIX / 'manifest.json'
PARTS = [FIX / f'part{i:02d}.b64' for i in range(1, 17)]
sys.path.insert(0, str(REPO / 'SOURCE'))
import pcs_factory_micro100_gt as gt

EXPECTED = {
    'manifest_bytes': 1376,
    'manifest_sha256': '20c52048a83236bdc056b1bf61ed28ea7136882a6266c8a7a9c0f03b11f86840',
    'json_bytes': 588689,
    'json_sha256': '0ab266c1a0bc585934be2b172be531832841e9abbdcb0c51ae90f65c21079088',
    'xz_bytes': 94416,
    'xz_sha256': '8c5c7a773ecfdc338db4683a9beb210f72bd7e02d377fb2abb465f65f7fb0c7f',
    'base64_bytes': 125888,
    'base64_sha256': 'b007be866d433670bbc6ad0c20fd0aa9f2d4df2d7cb7e336478469b6e02ceaa4',
    'sample_count': 100,
    'aggregate_safe': 7066304,
    'sample_id_digest': '6d3b047de7ce2cdbdf50e99c0a315eb737be3b7942c6fb0e558d1535fb7b46d3',
    'mask_digest': '4a31f4df0b059d22c29bb61f93f24059aec4c7f90dcc43b09f4591916e733383',
    'production_blob_sha1': '9e67ad85499d779239d5004dc11e81c1e0c1baea',
    'capsule_schema': 'DF-G101-PHASE3-GATE-C-MICRO100-MINIMAL-HYBRID-OID-CAPSULE-V2',
    'manifest_schema': 'DF-G101-PHASE3-GATE-C-MICRO100-MINIMAL-HYBRID-OID-MANIFEST-V2',
    'rendered_ordinals': [3, 27, 39, 51, 63, 75, 87, 99],
}
EXPECTED_PART_HASHES = [
    'f24f5658669ada9ac77adc5acfdfed32bed673ccb1819fa5db17cf32295bf643',
    '212aec31fca735d287deebf190e357aab50be8abc53754c955d120ea192e078d',
    'e3a72cb74c1f7a68c6a57a35cb37cf5bfc32199fe1c58da9c740b1ac386d1f66',
    'cdc6e2aa4975c21dfad0a5e3b5890d9b52e330f5bf8b788b2728597d51139a65',
    'a27016260ede8622e02e453321e4019f6041a7bc1beb8b8328eb1181ca6b67d7',
    '513888468ffabfc8dbe1276c095d5c928eccc10494d0b0b7dc21795e00d64025',
    '01a0ac97c92a10ba594127540fbbaf9e906838801ace2860cce989993ae8d04c',
    '02aeaf6834acab74f70eaec91e35c2b35986e85061828de75d1cc40d9f5518e7',
    '6addf1a2fd821e3976ad150e71e6fc0a21663c4dca4f98907b159b49e7ef19cd',
    'af3da19ca00239b2dbcd8d53fd58a36d4f5c3cd24ba16e98a8b21768235b5e57',
    'a93b7457c75ebb290d058db234613f22dfe84abc07b7fc2da7b9f1aafebc49b9',
    'd72e30377203d8d0b8a6206c50b2d1ad80c218bd62970b2f3b0861b7db744a22',
    '2dc4f325af3b35e49fd172b3170f0a374ddf21586b2d9abe1b6a88cf0331e814',
    'bc34d680d67667b1aa473f924bb021779a24c0e15cb2cbac1306f4f2cb9af307',
    '66bd850f080c1718c64378224c4982a427e6fe587e222ee8deeb7b14ad45f133',
    '7a123ec18a348636540fde291b9c98c9fb799d8a6720912e1e37a396ac134dc9',
]
SOURCE_AUTHORITY = {
    'filename': 'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_RETURN_20260909_R36.zip',
    'bytes': 64151371,
    'sha256': 'f94476c926bb7ba6e13e5122031dc25649e1f8277d4440bb0471ce946e57dee6',
    'return_manifest_bytes': 48338,
    'return_manifest_sha256': 'c9a32fc848b7083bb3224d52554dae0554dcefc899505e40fdde07f99b5d4a3f',
    'zip_entries': 235,
    'drive_id': '12VDhJRmvu105VHRplr2I2LtGeGwVcQdV',
    'closure_drive_id': '1a63qacKbvG_OKUwGzPCoBXIk5WxmZiauKBXQiBstNJs',
}


def fail(msg: str):
    raise AssertionError(msg)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob_sha1(b: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(b)).encode('ascii') + b'\0' + b).hexdigest()


def decode_rle(flat, n: int):
    if len(flat) % 2:
        fail('GATEC_RLE_ODD_LENGTH')
    out = np.empty(int(n), dtype=np.int32)
    p = 0
    for i in range(0, len(flat), 2):
        value, count = int(flat[i]), int(flat[i + 1])
        if count <= 0 or p + count > n:
            fail('GATEC_RLE_INVALID_COUNT')
        out[p:p + count] = value
        p += count
    if p != n:
        fail(f'GATEC_RLE_LENGTH_MISMATCH:{p}!={n}')
    return out


def analytic_oid(request, k_eff):
    h, w = int(request['camera']['height']), int(request['camera']['width'])
    C = np.asarray(request['camera']['pose']['camera_center_world'], dtype=np.float64)
    _pred_depth, pid = gt._predict_depth_and_id(request, C, h, w, k_eff)
    return np.asarray(pid, dtype=np.int32)


def build_old_mask(request, oid, k_eff, radius):
    h, w = oid.shape
    C = np.asarray(request['camera']['pose']['camera_center_world'], dtype=np.float64)
    _dcv, dw = gt._ray_grid(request, h, w, K_override=k_eff)
    labels = np.full((h, w), -1, dtype=np.int32)
    for j, obj in enumerate(request['scene']['objects'], 1):
        _t, _n, face = gt._object_hit_surface(C, dw, obj)
        m = oid == j
        labels[m] = (j - 1) * 6 + face[m].astype(np.int32)
    return gt._filter_safe_interior_mask(oid, labels, int(radius))


def load_authenticated_capsule():
    manifest_bytes = MANIFEST_PATH.read_bytes()
    if len(manifest_bytes) != EXPECTED['manifest_bytes'] or sha256(manifest_bytes) != EXPECTED['manifest_sha256']:
        fail('GATEC_MANIFEST_IDENTITY_MISMATCH')
    manifest = json.loads(manifest_bytes)
    if manifest.get('schema') != EXPECTED['manifest_schema']:
        fail('GATEC_MANIFEST_SCHEMA_MISMATCH')
    if manifest.get('source_authority') != SOURCE_AUTHORITY:
        fail('GATEC_MANIFEST_SOURCE_AUTHORITY_MISMATCH')

    chunks = []
    for i, (path, digest) in enumerate(zip(PARTS, EXPECTED_PART_HASHES), 1):
        b = path.read_bytes()
        if len(b) != 7868 or sha256(b) != digest:
            fail(f'GATEC_PART_IDENTITY_MISMATCH:{i:02d}')
        chunks.append(b)
    b64 = b''.join(chunks)
    if len(b64) != EXPECTED['base64_bytes'] or sha256(b64) != EXPECTED['base64_sha256']:
        fail('GATEC_BASE64_IDENTITY_MISMATCH')
    try:
        xz = base64.b64decode(b64, validate=True)
    except Exception as exc:
        raise AssertionError('GATEC_BASE64_DECODE_FAILED') from exc
    if len(xz) != EXPECTED['xz_bytes'] or sha256(xz) != EXPECTED['xz_sha256']:
        fail('GATEC_XZ_IDENTITY_MISMATCH')
    try:
        raw = lzma.decompress(xz, format=lzma.FORMAT_XZ)
    except Exception as exc:
        raise AssertionError('GATEC_XZ_DECODE_FAILED') from exc
    if len(raw) != EXPECTED['json_bytes'] or sha256(raw) != EXPECTED['json_sha256']:
        fail('GATEC_JSON_IDENTITY_MISMATCH')
    cap = json.loads(raw)
    if cap.get('schema') != EXPECTED['capsule_schema']:
        fail('GATEC_CAPSULE_SCHEMA_MISMATCH')
    if cap.get('source_authority') != SOURCE_AUTHORITY:
        fail('GATEC_CAPSULE_SOURCE_AUTHORITY_MISMATCH')
    return manifest, cap


def validate_global(cap):
    agg = cap['aggregate']
    if int(agg['sample_count']) != EXPECTED['sample_count']:
        fail('GATEC_SAMPLE_COUNT_MISMATCH')
    if int(agg['old_safe_pixels']) != EXPECTED['aggregate_safe']:
        fail('GATEC_AGGREGATE_OLD_SAFE_AUTHORITY_MISMATCH')
    if int(agg['expected_new_safe_pixels']) != EXPECTED['aggregate_safe'] or int(agg['expected_exclusions']) != 0:
        fail('GATEC_EXPECTED_CORRECTED_AUTHORITY_MISMATCH')
    if agg['sample_id_digest_sha256'] != EXPECTED['sample_id_digest']:
        fail('GATEC_SAMPLE_ID_AUTHORITY_MISMATCH')
    if agg['old_mask_digest_sha256'] != EXPECTED['mask_digest']:
        fail('GATEC_MASK_DIGEST_AUTHORITY_MISMATCH')
    if [int(v) for v in agg['rendered_oid_samples']] != EXPECTED['rendered_ordinals']:
        fail('GATEC_RENDERED_OID_SET_AUTHORITY_MISMATCH')

    samples = sorted(cap['samples'], key=lambda r: int(r['ordinal']))
    if [int(r['ordinal']) for r in samples] != list(range(100)):
        fail('GATEC_ORDINAL_SET_MISMATCH')
    ids = [str(r['sample_id']) for r in samples]
    if sha256(('\n'.join(ids) + '\n').encode('utf-8')) != EXPECTED['sample_id_digest']:
        fail('GATEC_SAMPLE_ID_DIGEST_MISMATCH')
    old_hashes = [str(r['old']['sha256']) for r in samples]
    if sha256(('\n'.join(old_hashes) + '\n').encode('ascii')) != EXPECTED['mask_digest']:
        fail('GATEC_ARCHIVED_MASK_DIGEST_MISMATCH')
    rendered = [int(r['ordinal']) for r in samples if r['oid_mode'] == 'RENDERED_RLE_HASH_GATED']
    if rendered != EXPECTED['rendered_ordinals']:
        fail('GATEC_RENDERED_OID_SET_MISMATCH')
    return samples


def qualify_rows(samples, ordinals):
    source_bytes = SOURCE.read_bytes()
    actual_blob = git_blob_sha1(source_bytes)
    if actual_blob != EXPECTED['production_blob_sha1']:
        fail(f'GATEC_PRODUCTION_BLOB_MISMATCH:{actual_blob}')

    selected = [r for r in samples if int(r['ordinal']) in ordinals]
    if len(selected) != len(ordinals):
        fail('GATEC_SELECTED_ORDINAL_MISMATCH')
    rows = []
    t_all = time.perf_counter()
    for row in selected:
        ordinal, sid = int(row['ordinal']), str(row['sample_id'])
        t0 = time.perf_counter()
        status = row['archived_status']
        if {k: status[k] for k in ('sample', 'depth', 'normal', 'object')} != {
            'sample': 'PASS', 'depth': 'PASS', 'normal': 'PASS', 'object': 'PASS'
        }:
            fail('GATEC_ARCHIVED_STATUS_MISMATCH:' + sid)
        if float(status['filter_width']) != 1.5:
            fail('GATEC_FILTER_WIDTH_AUTHORITY_MISMATCH:' + sid)
        na = row['archived_normal_authority']
        if float(na['filter_safe_authority_fraction']) != 1.0 or int(na['unexplained_invalid']) != 0:
            fail('GATEC_ARCHIVED_NORMAL_AUTHORITY_MISMATCH:' + sid)
        if len(str(na['mask_sha256'])) != 64 or int(na['authority_pixels']) <= 0:
            fail('GATEC_ARCHIVED_AUTHORITY_IDENTITY_INVALID:' + sid)
        if set(row['raw_identity']) != {'depth_exr_sha256', 'normal_exr_sha256', 'object_index_exr_sha256', 'depth_safe_sha256'}:
            fail('GATEC_RAW_IDENTITY_SCHEMA_MISMATCH:' + sid)
        for k in ('depth_exr_sha256', 'normal_exr_sha256', 'object_index_exr_sha256'):
            if len(str(row['raw_identity'][k])) != 64:
                fail('GATEC_RAW_IDENTITY_INVALID:' + sid + ':' + k)

        request = row['request_minimal']
        forbidden = {'sample_id', 'seed', 'digest', 'rgb', 'acceptance'}
        if forbidden.intersection(request):
            fail('GATEC_SELECTION_REQUEST_METADATA_LEAK:' + sid)
        if forbidden.intersection(request.get('camera', {})) or forbidden.intersection(request.get('scene', {})):
            fail('GATEC_SELECTION_REQUEST_METADATA_LEAK_NESTED:' + sid)

        h, w = int(request['camera']['height']), int(request['camera']['width'])
        if int(row['old']['bytes']) != h * w:
            fail('GATEC_OLD_MASK_BYTE_COUNT_MISMATCH:' + sid)
        final = row['final_binding']
        if final['statuses'] != {'depth_status': 'PASS', 'normal_status': 'PASS', 'object_status': 'PASS'}:
            fail('GATEC_FINAL_BINDING_STATUS_MISMATCH:' + sid)
        k_eff = np.asarray(final['K_effective'], dtype=np.float64)
        base_k = np.asarray(request['camera']['K'], dtype=np.float64)
        delta = np.asarray(final['delta_px'], dtype=np.float64)
        expected_k = base_k.copy(); expected_k[0, 2] += delta[0]; expected_k[1, 2] += delta[1]
        if not np.array_equal(k_eff, expected_k):
            fail('GATEC_EFFECTIVE_K_BINDING_MISMATCH:' + sid)

        mode = str(row['oid_mode'])
        if mode == 'ANALYTIC_PID_HASH_GATED':
            if row['rendered_oid'] is not None:
                fail('GATEC_ANALYTIC_OID_HAS_RENDERED_PAYLOAD:' + sid)
            oid = analytic_oid(request, k_eff)
        elif mode == 'RENDERED_RLE_HASH_GATED':
            if ordinal not in EXPECTED['rendered_ordinals']:
                fail('GATEC_RENDERED_OID_UNAUTHORIZED_ORDINAL:' + sid)
            meta = row['rendered_oid']
            if not isinstance(meta, dict) or len(str(meta['exr_sha256'])) != 64:
                fail('GATEC_RENDERED_OID_META_INVALID:' + sid)
            if meta['exr_sha256'] != row['raw_identity']['object_index_exr_sha256']:
                fail('GATEC_RENDERED_OID_EXR_BINDING_MISMATCH:' + sid)
            oid = decode_rle(meta['rle'], h * w).reshape(h, w)
            if sha256(oid.astype('<i4', copy=False).tobytes(order='C')) != meta['i32_le_sha256']:
                fail('GATEC_RENDERED_OID_RECONSTRUCTION_HASH_MISMATCH:' + sid)
        else:
            fail('GATEC_OID_MODE_INVALID:' + sid)

        old = build_old_mask(request, oid, k_eff, int(row['old']['radius']))
        old_bytes = old.astype(np.uint8).tobytes(order='C')
        old_count = int(np.count_nonzero(old))
        if len(old_bytes) != int(row['old']['bytes']):
            fail('GATEC_REBUILT_OLD_BYTES_MISMATCH:' + sid)
        if old_count != int(row['old']['safe_pixels']):
            fail('GATEC_REBUILT_OLD_COUNT_MISMATCH:' + sid)
        if sha256(old_bytes) != row['old']['sha256']:
            fail('GATEC_REBUILT_OLD_HASH_MISMATCH:' + sid)

        old_before = old.copy(); oid_before = oid.copy(); k_before = k_eff.copy()
        new, result = gt._phase3_candidate_b_normal_safe_mask(
            request, old, oid, K_override=k_eff,
            renderer_filter_width_px=gt.G100_CYCLES_FILTER_WIDTH_PX,
        )
        if not np.array_equal(old, old_before) or not np.array_equal(oid, oid_before) or not np.array_equal(k_eff, k_before):
            fail('GATEC_RUNTIME_INPUT_MUTATION:' + sid)
        if not np.array_equal(new, old):
            fail('GATEC_CANDIDATE_B_CHANGED_ARCHIVED_CONTROL:' + sid)
        if int(result['excluded_count']) != 0 or float(result['retained_fraction']) != 1.0 or result['reason_counts'] != {}:
            fail('GATEC_CANDIDATE_B_CONTROL_RESULT_MISMATCH:' + sid)
        if int(result.get('reason_counts', {}).get('UNCLASSIFIED_ANALYTIC_AMBIGUITY', 0)) != 0:
            fail('GATEC_UNCLASSIFIED_AMBIGUITY:' + sid)
        for key in (
            'rendered_normal_used_in_selection', 'rgb_used_in_selection',
            'acceptance_used_in_selection', 'sample_identity_used_in_selection',
            'depth_authority_mutated', 'camera_binding_steered',
        ):
            if bool(result[key]):
                fail('GATEC_NON_STEERING_FLAG_VIOLATION:' + sid + ':' + key)
        if result['method_id'] != gt.PHASE3_CANDIDATE_B_METHOD_ID:
            fail('GATEC_METHOD_ID_MISMATCH:' + sid)
        if float(result['retention_floor']) != float(gt.PHASE3_CANDIDATE_B_RETENTION_FLOOR):
            fail('GATEC_RETENTION_FLOOR_MISMATCH:' + sid)
        if float(gt.PHASE3_CANDIDATE_B_RETENTION_FLOOR) != 0.9783428720083247:
            fail('GATEC_FROZEN_RETENTION_FLOOR_DRIFT:' + sid)

        new_hash = sha256(new.astype(np.uint8).tobytes(order='C'))
        rows.append({
            'ordinal': ordinal, 'sample_id': sid, 'oid_mode': mode,
            'old_safe_count': old_count, 'new_safe_count': int(np.count_nonzero(new)),
            'old_mask_sha256': row['old']['sha256'], 'new_mask_sha256': new_hash,
            'excluded_count': int(result['excluded_count']),
            'retained_fraction': float(result['retained_fraction']),
            'reason_counts': result['reason_counts'],
            'runtime_seconds': time.perf_counter() - t0,
        })
        print(f'GATEC SAMPLE PASS {ordinal:04d} {sid} mode={mode} old={old_count}')
    return rows, actual_blob, time.perf_counter() - t_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int)
    ap.add_argument('--end', type=int)
    ap.add_argument('--ordinals', type=str)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    _manifest, cap = load_authenticated_capsule()
    samples = validate_global(cap)
    if args.ordinals:
        ordinals = sorted({int(x) for x in args.ordinals.split(',') if x.strip()})
    else:
        if args.start is None or args.end is None or args.start < 0 or args.end > 99 or args.end < args.start:
            fail('GATEC_INVALID_ORDINAL_SELECTION')
        ordinals = list(range(args.start, args.end + 1))
    rows, actual_blob, elapsed = qualify_rows(samples, ordinals)
    report = {
        'schema': 'DF-G101-PHASE3-GATE-C-MICRO100-SHARD-RESULT-V2',
        'status': 'PASS',
        'ordinals': ordinals,
        'sample_count': len(rows),
        'aggregate_old_safe_pixels': sum(r['old_safe_count'] for r in rows),
        'aggregate_new_safe_pixels': sum(r['new_safe_count'] for r in rows),
        'aggregate_exclusions': sum(r['excluded_count'] for r in rows),
        'all_retention_exact_1': all(r['retained_fraction'] == 1.0 for r in rows),
        'all_exclusions_zero': all(r['excluded_count'] == 0 for r in rows),
        'all_reason_counts_empty': all(r['reason_counts'] == {} for r in rows),
        'production_source_git_blob_sha1': actual_blob,
        'capsule_json_sha256': EXPECTED['json_sha256'],
        'capsule_xz_sha256': EXPECTED['xz_sha256'],
        'manifest_sha256': EXPECTED['manifest_sha256'],
        'runtime_seconds': elapsed,
        'samples': rows,
    }
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'samples'}, sort_keys=True))


if __name__ == '__main__':
    main()
