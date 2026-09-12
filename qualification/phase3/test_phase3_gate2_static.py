from __future__ import annotations

import ast
import subprocess
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
SOURCE=REPO/'SOURCE'/'pcs_factory_micro100_gt.py'

UNCHANGED_FUNCTIONS=(
    '_filter_safe_interior_mask',
    '_r29_depth_authority_adjudication',
    '_fit_renderer_effective_principal_point',
    '_r21_generalized_renderer_effective_pp_refine',
    '_r23_eval_pp_candidate',
    '_r23_pp_stage',
    '_r23_global_bounded_pp_search',
)
CANDIDATE_FUNCTIONS={
    '_phase3_b_batch_signatures','_phase3_b_analytic_centers','_phase3_b_clip_segment',
    '_phase3_b_projected_edges','_phase3_b_reason_for_transition','_phase3_b_choose_reason',
    '_phase3_b_edge_pairs','_phase3_b_edge_witness_exclusions','_phase3_candidate_b_require_retention',
    '_phase3_candidate_b_normal_safe_mask',
}
FORBIDDEN_NAMES={'raw','normal','normal_error','normal_magnitude','rgb','acceptance','sample_id','seed','digest'}
FORBIDDEN_REQUEST_KEYS={'sample_id','seed','digest','rgb','acceptance','normal','normal_error','normal_magnitude'}
FORBIDDEN_CALLS={'_r29_depth_authority_adjudication','_fit_renderer_effective_principal_point','_r21_generalized_renderer_effective_pp_refine','_r23_eval_pp_candidate','_r23_pp_stage','_r23_global_bounded_pp_search'}


def parse(text):
    return ast.parse(text)


def fn_map(tree):
    return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}


def ast_semantic(node):
    return ast.dump(node,annotate_fields=True,include_attributes=False)


def string_subscript_keys(node):
    out=set()
    for n in ast.walk(node):
        if isinstance(n,ast.Subscript):
            s=n.slice
            if isinstance(s,ast.Constant) and isinstance(s.value,str):out.add(s.value.lower())
    return out


def call_names(node):
    out=[]
    for n in ast.walk(node):
        if isinstance(n,ast.Call):
            f=n.func
            if isinstance(f,ast.Name):out.append(f.id)
            elif isinstance(f,ast.Attribute):out.append(f.attr)
    return out


def run():
    current=SOURCE.read_text(encoding='utf-8')
    try:
        baseline=subprocess.check_output(['git','show','origin/main:SOURCE/pcs_factory_micro100_gt.py'],cwd=REPO,text=True)
    except subprocess.CalledProcessError as exc:
        raise AssertionError('GATE2_BASELINE_MAIN_UNAVAILABLE') from exc
    cur_tree=parse(current); base_tree=parse(baseline); cur=fn_map(cur_tree); base=fn_map(base_tree)

    # Shared Depth and camera-binding science must remain AST-identical to main.
    for name in UNCHANGED_FUNCTIONS:
        if name not in cur or name not in base:raise AssertionError('GATE2_MISSING_IMMUTABLE_FUNCTION:'+name)
        if ast_semantic(cur[name])!=ast_semantic(base[name]):raise AssertionError('GATE2_IMMUTABLE_FUNCTION_CHANGED:'+name)

    missing=sorted(CANDIDATE_FUNCTIONS-set(cur))
    if missing:raise AssertionError('GATE2_MISSING_CANDIDATE_FUNCTION:'+','.join(missing))

    # Candidate construction functions may see analytic request geometry/camera
    # and rendered Object Index classification only, never rendered Normal/RGB or
    # sample/outcome identity. Exact forbidden request keys and selector names are
    # rejected structurally, not by convention.
    for name in sorted(CANDIDATE_FUNCTIONS):
        node=cur[name]
        identifiers={n.id.lower() for n in ast.walk(node) if isinstance(n,ast.Name)}
        identifiers|={a.arg.lower() for a in node.args.args}
        bad_names=sorted(identifiers & FORBIDDEN_NAMES)
        if bad_names:raise AssertionError(f'GATE2_FORBIDDEN_SELECTOR_NAME:{name}:'+','.join(bad_names))
        bad_keys=sorted(string_subscript_keys(node)&FORBIDDEN_REQUEST_KEYS)
        if bad_keys:raise AssertionError(f'GATE2_FORBIDDEN_REQUEST_KEY:{name}:'+','.join(bad_keys))
        bad_calls=sorted(set(call_names(node))&FORBIDDEN_CALLS)
        if bad_calls:raise AssertionError(f'GATE2_CANDIDATE_STEERS_PROTECTED_PATH:{name}:'+','.join(bad_calls))
        seg=ast.get_source_segment(current,node) or ''
        for literal in ('target0034','g101_0034','syn_1028','syn_1016'):
            if literal in seg:raise AssertionError(f'GATE2_TARGET_SPECIFIC_LITERAL:{name}:{literal}')

    # Only Normal evaluation may call Candidate B: once in reusable K evaluation
    # and twice in validate_aux_gt (canonical and already-selected effective K).
    r21_calls=[c for c in call_names(cur['_r21_normal_eval_for_K']) if c=='_phase3_candidate_b_normal_safe_mask']
    val_calls=[c for c in call_names(cur['validate_aux_gt']) if c=='_phase3_candidate_b_normal_safe_mask']
    if len(r21_calls)!=1 or len(val_calls)!=2:
        raise AssertionError(f'GATE2_NORMAL_CALLSITE_COUNT:r21={len(r21_calls)} validate={len(val_calls)}')
    depth_calls=[c for c in call_names(cur['_r29_depth_authority_adjudication']) if 'phase3_candidate_b' in c]
    if depth_calls:raise AssertionError('GATE2_DEPTH_CALLS_CANDIDATE_B')

    # Frozen constants and explicit non-steering provenance are mandatory.
    required=(
        "PHASE3_CANDIDATE_B_RETENTION_FLOOR = 0.9783428720083247",
        "PHASE3_CANDIDATE_B_METHOD_ID = 'DF_G101_POST_R2_GEOMETRY_SEEDED_SUBPIXEL_VISIBILITY_REFERENCE_B_V1'",
        "'phase3_candidate_b_depth_authority_mutated':False",
        "'phase3_candidate_b_camera_binding_steered':False",
        "'phase3_candidate_b_rendered_normal_used_in_selection':False",
    )
    for needle in required:
        if needle not in current:raise AssertionError('GATE2_REQUIRED_PROVENANCE_MISSING:'+needle)

    print('PHASE3 GATE2 STATIC/DEPTH/K FIREWALL: PASS')


if __name__=='__main__':run()
