from __future__ import annotations

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
FIX = Path(__file__).resolve().parent / 'fixtures' / 'gateb_v1c'
MANIFEST_PATH = FIX / 'gateb_v1c_manifest.json'
PARTS = [FIX / f'gateb_v1c_part{i:02d}.txt' for i in range(1, 11)]
sys.path.insert(0, str(REPO / 'SOURCE'))
import pcs_factory_micro100_gt as gt

EXPECTED = {
    'manifest_bytes': 3102,
    'manifest_sha256': '9cff09bd0b995ae024b01e5270713101195c9bc559eafe17ffb1ac665cef24db',
    'json_bytes': 368092,
    'json_sha256': '0a6b8f08b5d6e8d46bcf0fcbc391e4029d6c691e70dc77c67b4b0c8977a4d966',
    'xz_bytes': 52080,
    'xz_sha256': 'ead2b9b0af314f6460934115aed1aa3aaa4c67e4f7bc832a1bfbe8fefce8ea3a',
    'base64_chars': 69440,
    'sample_count': 34,
    'aggregate_safe': 2438043,
    'sample_id_digest': '4475d6ddc122011e30af6ca422912adcf9c897d295a7357e902ae1b5cb359034',
    'baseline_digest': '20e91ceeb3d6966cb96420abe380eebb7577ebd49ccbe2f22e6f735eca6fee15',
    'source_subset_digest': 'f42fd9783af6cdba9bfd24515f7bf3b44da73a8508b1577f9342d1e763362d0a',
    'production_blob_sha1': '9e67ad85499d779239d5004dc11e81c1e0c1baea',
    'capsule_schema': 'DF-G101-PHASE3-GATE-B-HASHBOUND-COMPACT-TRANSPORT-V1C',
    'manifest_schema': 'DF-G101-PHASE3-GATE-B-HASHBOUND-COMPACT-TRANSPORT-MANIFEST-V1C',
}
EXPECTED_PARTS = [
    (6944, '3ff9577bfd2e7c3dd89933331c247825074017a17ef30226da5a67587b8b66c2'),
    (6944, '84fc9689f44d4589163ed1e47f7e554957f171e00ed934ab9e977aa7e5e316db'),
    (6944, '65b7c0e507a2ac9f20ee2e67ff0517a2a8e55e0fdb84d156e1c275c5dd7817b9'),
    (6944, '2dc66630c6b7373e40f5ec4ff17d2d1a95c51ec7d1d9d7e8da68fe6180a1cae4'),
    (6944, 'e779e569738830a8f7ab987daaebf596fcbd8c638cc283f49e9d2038539377e7'),
    (6944, 'eb8cd3cf4e37093915d9e08349f7a283af3177f6b3db5a0202db7db8cf94dc95'),
    (6944, '4deafe79be3550e521f8fbfe20eb11a3b424c76f0e9fe25baeb73a03d3b523f1'),
    (6944, '132c006f7c9190b390a9f671c24a64f8136440eb083489635e2ca70211dd9146'),
    (6944, '61092545555bc874ab1e59132a1cb6d1b26d1d7167ff0afd71ce4c6bf13eaa54'),
    (6944, '37debd6fb630e2fd8dfff7a5908f7893a0c44c98e9c05704a6c2b4033d8498cc'),
]
REQUIRED_SOURCE_FILES = {
    'request.json',
    'sample/micro100_aux_gt_qa.json',
    'sample/normal_authority_mask.uint8.bin',
    'sample/normal_filter_safe_interior_mask.uint8.bin',
    'sample/object_index.exr',
    'sample/r21_binding_lab.json',
}


def fail(msg):
    raise AssertionError(msg)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob_sha1(b: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(b)).encode('ascii') + b'\0' + b).hexdigest()


def decode_rle(flat, n):
    if len(flat) % 2:
        fail('GATEB_RLE_ODD_LENGTH')
    out = np.empty(int(n), dtype=np.int32)
    p = 0
    for i in range(0, len(flat), 2):
        value = int(flat[i]); count = int(flat[i + 1])
        if count <= 0 or p + count > n:
            fail('GATEB_RLE_INVALID_COUNT')
        out[p:p + count] = value
        p += count
    if p != n:
        fail(f'GATEB_RLE_LENGTH_MISMATCH:{p}!={n}')
    return out


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


def main(out_path=None):
    # Transport/manifest identity first: no scientific assertion before this block passes.
    manifest_bytes = MANIFEST_PATH.read_bytes()
    if len(manifest_bytes) != EXPECTED['manifest_bytes'] or sha256(manifest_bytes) != EXPECTED['manifest_sha256']:
        fail('GATEB_MANIFEST_IDENTITY_MISMATCH')
    manifest = json.loads(manifest_bytes)
    if manifest.get('schema') != EXPECTED['manifest_schema']:
        fail('GATEB_MANIFEST_SCHEMA_MISMATCH')

    part_bytes = []
    for i, (path, (n, digest)) in enumerate(zip(PARTS, EXPECTED_PARTS), 1):
        b = path.read_bytes()
        if len(b) != n or sha256(b) != digest:
            fail(f'GATEB_PART_IDENTITY_MISMATCH:{i:02d}')
        mrow = manifest['shards'][i - 1]
        if mrow['name'] != path.name or int(mrow['bytes']) != n or mrow['sha256'] != digest:
            fail(f'GATEB_MANIFEST_PART_BINDING_MISMATCH:{i:02d}')
        if mrow['git_blob_sha1'] != git_blob_sha1(b):
            fail(f'GATEB_PART_GIT_BLOB_MISMATCH:{i:02d}')
        part_bytes.append(b)
    b64 = b''.join(part_bytes)
    if len(b64) != EXPECTED['base64_chars']:
        fail('GATEB_BASE64_LENGTH_MISMATCH')
    try:
        xz = base64.b64decode(b64, validate=True)
    except Exception as exc:
        raise AssertionError('GATEB_BASE64_DECODE_FAILED') from exc
    if len(xz) != EXPECTED['xz_bytes'] or sha256(xz) != EXPECTED['xz_sha256']:
        fail('GATEB_XZ_IDENTITY_MISMATCH')
    try:
        raw = lzma.decompress(xz, format=lzma.FORMAT_XZ)
    except Exception as exc:
        raise AssertionError('GATEB_XZ_DECODE_FAILED') from exc
    if len(raw) != EXPECTED['json_bytes'] or sha256(raw) != EXPECTED['json_sha256']:
        fail('GATEB_JSON_IDENTITY_MISMATCH')
    cap = json.loads(raw)
    if cap.get('schema') != EXPECTED['capsule_schema']:
        fail('GATEB_CAPSULE_SCHEMA_MISMATCH')

    # Production source binding is byte/object identity, not a source-code string check.
    source_bytes = SOURCE.read_bytes()
    actual_blob = git_blob_sha1(source_bytes)
    if actual_blob != EXPECTED['production_blob_sha1']:
        fail(f'GATEB_PRODUCTION_BLOB_MISMATCH:{actual_blob}')
    if cap.get('production_source_git_blob_sha1') != EXPECTED['production_blob_sha1']:
        fail('GATEB_CAPSULE_PRODUCTION_BINDING_MISMATCH')
    if manifest.get('production_source_git_blob_sha1') != EXPECTED['production_blob_sha1']:
        fail('GATEB_MANIFEST_PRODUCTION_BINDING_MISMATCH')

    agg = cap['aggregate']
    if int(agg['sample_count']) != EXPECTED['sample_count']:
        fail('GATEB_SAMPLE_COUNT_MISMATCH')
    if int(agg['ordinal_first']) != 0 or int(agg['ordinal_last']) != 33:
        fail('GATEB_ORDINAL_RANGE_MISMATCH')
    if int(agg['inherited_safe_pixels']) != EXPECTED['aggregate_safe']:
        fail('GATEB_AGGREGATE_OLD_SAFE_AUTHORITY_MISMATCH')
    if int(agg['expected_corrected_safe_pixels']) != EXPECTED['aggregate_safe'] or int(agg['expected_exclusions']) != 0:
        fail('GATEB_EXPECTED_CORRECTED_AUTHORITY_MISMATCH')
    if agg['sample_id_digest_sha256'] != EXPECTED['sample_id_digest']:
        fail('GATEB_SAMPLE_ID_AUTHORITY_VALUE_MISMATCH')
    if agg['baseline_mask_digest_sha256'] != EXPECTED['baseline_digest']:
        fail('GATEB_BASELINE_DIGEST_AUTHORITY_VALUE_MISMATCH')
    if agg['source_subset_authority_digest_sha256'] != EXPECTED['source_subset_digest']:
        fail('GATEB_SOURCE_SUBSET_AUTHORITY_VALUE_MISMATCH')

    samples = sorted(cap['samples'], key=lambda r: int(r['ordinal']))
    if [int(r['ordinal']) for r in samples] != list(range(34)):
        fail('GATEB_ORDINAL_SET_MISMATCH')
    ids = [str(r['sample_id']) for r in samples]
    id_digest = sha256(('\n'.join(ids) + '\n').encode('utf-8'))
    if id_digest != EXPECTED['sample_id_digest']:
        fail('GATEB_SAMPLE_ID_DIGEST_MISMATCH')
    archived_mask_hashes = [str(r['r6']['archived_mask_sha256']) for r in samples]
    archived_digest = sha256(('\n'.join(archived_mask_hashes) + '\n').encode('ascii'))
    if archived_digest != EXPECTED['baseline_digest']:
        fail('GATEB_ARCHIVED_BASELINE_DIGEST_MISMATCH')

    source_return = cap['source_return']
    if source_return != manifest['source_return']:
        fail('GATEB_SOURCE_RETURN_MANIFEST_CAPSULE_MISMATCH')
    if source_return != {
        'filename': 'DF_G101_POST_R2_PHASE2_LOCAL_COMPLETED_FIXTURES_RETURN_V4.zip',
        'bytes': 16889773,
        'sha256': 'aa8ad77e253e6d515f789f86b3b403d2b58ef7e6721927666bec930a07e3eb26',
        'return_manifest_sha256': 'a21558366459801dbe0cb7c41ab0e660adcb8e8fe5202caf748aaba857e43bb6',
    }:
        fail('GATEB_SOURCE_RETURN_AUTHORITY_MISMATCH')

    total_old = total_new = 0
    corrected_hashes = []
    rows = []
    t_all = time.perf_counter()
    for row in samples:
        sid = str(row['sample_id'])
        t0 = time.perf_counter()
        if set(row['source_files']) != REQUIRED_SOURCE_FILES:
            fail('GATEB_SOURCE_FILE_SET_MISMATCH:' + sid)
        for rel, meta in row['source_files'].items():
            if int(meta['bytes']) <= 0 or len(str(meta['sha256'])) != 64:
                fail('GATEB_SOURCE_FILE_IDENTITY_INVALID:' + sid + ':' + rel)

        final = row['final_binding']
        if final['status'] != {'depth': 'PASS', 'normal': 'PASS', 'object': 'PASS'}:
            fail('GATEB_ARCHIVED_FINAL_BINDING_STATUS_MISMATCH:' + sid)
        na = row['normal_authority']
        if float(na['archived_filter_safe_authority_fraction']) != 1.0 or int(na['archived_unexplained_invalid_interior_pixels']) != 0:
            fail('GATEB_ARCHIVED_NORMAL_AUTHORITY_MISMATCH:' + sid)

        request = row['request_minimal']
        if 'sample_id' in request or 'seed' in request or 'digest' in request:
            fail('GATEB_SELECTION_REQUEST_METADATA_LEAK:' + sid)
        h, w = [int(v) for v in row['object_index']['shape']]
        if (w, h) != (int(request['camera']['width']), int(request['camera']['height'])):
            fail('GATEB_RASTER_SHAPE_MISMATCH:' + sid)
        oid = decode_rle(row['object_index']['rle_value_count_flat'], h * w).reshape(h, w)
        oid_bytes = oid.astype('<i4', copy=False).tobytes(order='C')
        if sha256(oid_bytes) != row['object_index']['reconstructed_i32_le_sha256']:
            fail('GATEB_OBJECT_INDEX_HASH_MISMATCH:' + sid)

        k_eff = np.asarray(final['K_effective'], dtype=np.float64)
        base_k = np.asarray(request['camera']['K'], dtype=np.float64)
        delta = np.asarray(final['delta_px'], dtype=np.float64)
        expected_k = base_k.copy(); expected_k[0, 2] += delta[0]; expected_k[1, 2] += delta[1]
        if not np.array_equal(k_eff, expected_k):
            fail('GATEB_EFFECTIVE_K_BINDING_MISMATCH:' + sid)

        old = build_old_mask(request, oid, k_eff, int(row['r6']['filter_support_radius_px']))
        old_u8 = old.astype(np.uint8)
        old_bytes = old_u8.tobytes(order='C')
        old_count = int(np.count_nonzero(old))
        if len(old_bytes) != int(row['r6']['archived_mask_bytes']):
            fail('GATEB_REBUILT_OLD_BYTES_MISMATCH:' + sid)
        if old_count != int(row['r6']['archived_safe_count']):
            fail('GATEB_REBUILT_OLD_COUNT_MISMATCH:' + sid)
        if sha256(old_bytes) != row['r6']['archived_mask_sha256']:
            fail('GATEB_REBUILT_OLD_HASH_MISMATCH:' + sid)

        new, result = gt._phase3_candidate_b_normal_safe_mask(
            request,
            old,
            oid,
            K_override=k_eff,
            renderer_filter_width_px=gt.G100_CYCLES_FILTER_WIDTH_PX,
        )
        if not np.array_equal(new, old):
            fail('GATEB_CANDIDATE_B_CHANGED_ARCHIVED_CONTROL:' + sid)
        if int(result['excluded_count']) != 0 or float(result['retained_fraction']) != 1.0 or result['reason_counts'] != {}:
            fail('GATEB_CANDIDATE_B_CONTROL_RESULT_MISMATCH:' + sid)
        if int(result.get('reason_counts', {}).get('UNCLASSIFIED_ANALYTIC_AMBIGUITY', 0)) != 0:
            fail('GATEB_UNCLASSIFIED_AMBIGUITY:' + sid)
        for key in (
            'rendered_normal_used_in_selection', 'rgb_used_in_selection',
            'acceptance_used_in_selection', 'sample_identity_used_in_selection',
            'depth_authority_mutated', 'camera_binding_steered',
        ):
            if bool(result[key]):
                fail('GATEB_NON_STEERING_FLAG_VIOLATION:' + sid + ':' + key)
        if result['method_id'] != gt.PHASE3_CANDIDATE_B_METHOD_ID:
            fail('GATEB_METHOD_ID_MISMATCH:' + sid)
        if float(result['retention_floor']) != float(gt.PHASE3_CANDIDATE_B_RETENTION_FLOOR):
            fail('GATEB_RETENTION_FLOOR_MISMATCH:' + sid)

        total_old += old_count
        total_new += int(np.count_nonzero(new))
        corrected_hashes.append(sha256(new.astype(np.uint8).tobytes(order='C')))
        rows.append({
            'ordinal': int(row['ordinal']), 'sample_id': sid,
            'old_safe_count': old_count, 'new_safe_count': int(np.count_nonzero(new)),
            'excluded_count': int(result['excluded_count']),
            'retained_fraction': float(result['retained_fraction']),
            'reason_counts': result['reason_counts'],
            'edge_touched_old_safe_count': int(result['edge_touched_old_safe_count']),
            'edge_pixel_pairs': int(result['edge_pixel_pairs']),
            'runtime_seconds': time.perf_counter() - t0,
        })
        print(f"GATEB SAMPLE PASS {int(row['ordinal']):04d} {sid} old={old_count} edge_pairs={result['edge_pixel_pairs']}")

    corrected_digest = sha256(('\n'.join(corrected_hashes) + '\n').encode('ascii'))
    if total_old != EXPECTED['aggregate_safe'] or total_new != EXPECTED['aggregate_safe']:
        fail(f'GATEB_AGGREGATE_SAFE_COUNT_MISMATCH:{total_old}:{total_new}')
    if corrected_digest != EXPECTED['baseline_digest']:
        fail('GATEB_AGGREGATE_CORRECTED_DIGEST_MISMATCH')

    report = {
        'schema': 'DF-G101-PHASE3-GATE-B-GITHUB-QUALIFICATION-RESULT-V1C',
        'status': 'PASS',
        'sample_count': len(rows),
        'aggregate_old_safe_pixels': total_old,
        'aggregate_new_safe_pixels': total_new,
        'aggregate_exclusions': total_old - total_new,
        'sample_id_digest_sha256': id_digest,
        'archived_baseline_digest_sha256': archived_digest,
        'corrected_mask_digest_sha256': corrected_digest,
        'production_source_git_blob_sha1': actual_blob,
        'capsule_json_sha256': EXPECTED['json_sha256'],
        'capsule_xz_sha256': EXPECTED['xz_sha256'],
        'manifest_sha256': EXPECTED['manifest_sha256'],
        'source_subset_authority_digest_sha256': EXPECTED['source_subset_digest'],
        'all_retention_exact_1': all(r['retained_fraction'] == 1.0 for r in rows),
        'all_exclusions_zero': all(r['excluded_count'] == 0 for r in rows),
        'all_reason_counts_empty': all(r['reason_counts'] == {} for r in rows),
        'runtime_seconds': time.perf_counter() - t_all,
        'samples': rows,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if out_path:
        Path(out_path).write_text(text, encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'samples'}, sort_keys=True))
    return report


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else None
    main(out)
