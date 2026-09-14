from __future__ import annotations
import ast
import hashlib
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
SOURCE=REPO/'SOURCE'/'pcs_factory_micro100_gt.py'
OPT=REPO/'qualification'/'phase3'/'candidate_b_optimized.py'
REF=REPO/'qualification'/'phase3'/'candidate_b_reference.py'

EXPECTED_DEPTH_FUNCTION_HASHES={
    '_filter_safe_interior_mask':'9806cd0be1373ab79e3c95f2bb4c32f0f46cf98a364c055e91594b7d5a9fd5ed',
    '_r29_depth_authority_adjudication':'db9fe15c28649d400a90ee9234343e25af0159d6b4d08c6f9ac0ab9b92a66d78',
}
FORBIDDEN_SELECTION_NAMES={'raw','normal','normal_error','normal_magnitude','rgb','acceptance','sample_id','seed','digest'}


def function_segment_hash(path,name):
    text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
    node=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise AssertionError('missing function '+name)
    segment=ast.get_source_segment(text,node)
    return hashlib.sha256(segment.encode('utf-8')).hexdigest()


def identifiers_in_functions(path,names):
    text=path.read_text(encoding='utf-8'); tree=ast.parse(text); out=set()
    for node in tree.body:
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name not in names: continue
        for n in ast.walk(node):
            if isinstance(n,ast.Name): out.add(n.id.lower())
            elif isinstance(n,ast.arg): out.add(n.arg.lower())
            elif isinstance(n,ast.Attribute): out.add(n.attr.lower())
    return out


def run():
    # Frozen shared Depth path must remain byte-for-byte source-identical even
    # after the Normal-only Candidate-B implementation is introduced.
    for name,expected in EXPECTED_DEPTH_FUNCTION_HASHES.items():
        got=function_segment_hash(SOURCE,name)
        if got!=expected:
            raise AssertionError(f'DEPTH_ISOLATION_SOURCE_CHANGED:{name}:{got}!={expected}')

    # Candidate-B selection functions are geometry-only. Rendered Object Index is
    # explicitly allowed for inherited-baseline/cross-check classification.
    opt_ids=identifiers_in_functions(OPT,{'analytic_centers','edge_witness_exclusions','evaluate_mask'})
    ref_ids=identifiers_in_functions(REF,{'batch_signatures','projected_edges','evaluate_pixel','evaluate_pixels'})
    bad=sorted((opt_ids|ref_ids)&FORBIDDEN_SELECTION_NAMES)
    if bad:
        raise AssertionError('CANDIDATE_B_FORBIDDEN_SELECTION_IDENTIFIER:'+','.join(bad))

    # No target/sample-specific branching literals are allowed in Candidate-B
    # reference or optimized implementation modules.
    for path in (OPT,REF):
        text=path.read_text(encoding='utf-8')
        for forbidden_literal in ('target0034','g101_0034','syn_1028','syn_1016'):
            if forbidden_literal in text:
                raise AssertionError(f'TARGET_SPECIFIC_BEHAVIOR_LITERAL:{path.name}:{forbidden_literal}')

    print('PHASE3 STATIC FIREWALL: PASS')


if __name__=='__main__': run()
