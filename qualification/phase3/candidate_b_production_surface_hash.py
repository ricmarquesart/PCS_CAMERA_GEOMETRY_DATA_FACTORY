from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'SOURCE' / 'pcs_factory_micro100_gt.py'

CONSTANTS = {
    'PHASE3_CANDIDATE_B_METHOD_ID',
    'PHASE3_CANDIDATE_B_RETENTION_FLOOR',
    'PHASE3_CANDIDATE_B_LATTICE_STEP_PX',
    'PHASE3_CANDIDATE_B_DYADIC_JS',
    'PHASE3_CANDIDATE_B_SPEC_DRIVE_ID',
    'PHASE3_CANDIDATE_B_FULL_DOMAIN_SPEC_DRIVE_ID',
    'PHASE3_CANDIDATE_B_REASON_PRIORITY',
    '_PHASE3_CANDIDATE_B_SIGNS',
    '_PHASE3_CANDIDATE_B_EDGE_PAIRS',
}
FUNCTIONS = {
    '_phase3_b_batch_signatures',
    '_phase3_b_analytic_centers',
    '_phase3_b_clip_segment',
    '_phase3_b_projected_edges',
    '_phase3_b_reason_for_transition',
    '_phase3_b_choose_reason',
    '_phase3_b_edge_pairs',
    '_phase3_b_edge_witness_exclusions',
    '_phase3_candidate_b_require_retention',
    '_phase3_candidate_b_normal_safe_mask',
}


def canonical_surface(path: Path):
    raw = path.read_bytes()
    tree = ast.parse(raw.decode('utf-8'))
    found_constants = {}
    found_functions = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node.target, ast.Name):
                targets = [node.target.id]
            for name in targets:
                if name in CONSTANTS:
                    if name in found_constants:
                        raise AssertionError(f'DUPLICATE_CONSTANT:{name}')
                    found_constants[name] = ast.dump(node, annotate_fields=True, include_attributes=False)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FUNCTIONS:
            if node.name in found_functions:
                raise AssertionError(f'DUPLICATE_FUNCTION:{node.name}')
            found_functions[node.name] = ast.dump(node, annotate_fields=True, include_attributes=False)

    if set(found_constants) != CONSTANTS:
        raise AssertionError('CONSTANT_SET_MISMATCH:' + json.dumps({
            'missing': sorted(CONSTANTS - set(found_constants)),
            'extra': sorted(set(found_constants) - CONSTANTS),
        }, sort_keys=True))
    if set(found_functions) != FUNCTIONS:
        raise AssertionError('FUNCTION_SET_MISMATCH:' + json.dumps({
            'missing': sorted(FUNCTIONS - set(found_functions)),
            'extra': sorted(set(found_functions) - FUNCTIONS),
        }, sort_keys=True))

    payload = {
        'constants': {k: found_constants[k] for k in sorted(found_constants)},
        'functions': {k: found_functions[k] for k in sorted(found_functions)},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    source_sha256 = hashlib.sha256(raw).hexdigest()
    git_blob_sha1 = hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
    return {
        'schema': 'DF-G101-PHASE3-CANDIDATE-B-PRODUCTION-SURFACE-HASH-V1',
        'source_bytes': len(raw),
        'source_sha256': source_sha256,
        'source_git_blob_sha1': git_blob_sha1,
        'constant_count': len(found_constants),
        'function_count': len(found_functions),
        'canonical_surface_bytes': len(canonical),
        'canonical_surface_sha256': hashlib.sha256(canonical).hexdigest(),
    }


if __name__ == '__main__':
    result = canonical_surface(SOURCE)
    print(json.dumps(result, sort_keys=True))
