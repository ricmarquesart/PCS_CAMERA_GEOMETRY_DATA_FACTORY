from __future__ import annotations

import html
import json
import math
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pcs_factory_camera import project_world
from pcs_factory_seed import identity_digest

PARITY_EXPECTATION_SCHEMA = "DF-G60-PARITY-EXPECTATION-V1"
MAYA_RESULT_SCHEMA = "DF-G60-MAYA-RESULT-V1"
ROUNDTRIP_REPORT_SCHEMA = "DF-G62-ROUNDTRIP-REPORT-V1"
MICROSET_SCHEMA = "DF-G61-MAYA-NATIVE-MICROSET-V1"
REAL_AGGREGATE_SCHEMA = "DF-G60-G62-REAL-MAYA-PARITY-AGGREGATE-V1"

CASES = (
    "CENTERED_NORMAL", "WIDE", "TELEPHOTO", "PORTRAIT",
    "OFFCENTER_PP", "ROLL", "PITCH", "NONDEFAULT_ASPECT",
)

HARD_MAX_PX = 0.50
HARD_MEDIAN_PX = 0.20
FOCAL_REL_MAX = 1e-6
PRECISION_MAX_EQ_1920_1080_PX = 0.05


def _mat3_list(m):
    return [[float(x) for x in row] for row in m]


def _vec3(v):
    return [float(x) for x in v]


def build_expectation(case_id: str, camera: Dict[str, Any], landmarks_world: Dict[str, Iterable[float]], width: int, height: int, sensor_width_mm: float = 36.0) -> Dict[str, Any]:
    if case_id not in CASES:
        raise ValueError("UNKNOWN_PARITY_CASE")
    K = camera["K"]
    pose = camera["pose"]
    fx, fy, cx, cy = float(K[0][0]), float(K[1][1]), float(K[0][2]), float(K[1][2])
    expected = {}
    for name, p in sorted(landmarks_world.items()):
        u, v, z = project_world(tuple(map(float, p)), pose, K)
        expected[name] = {"world": _vec3(p), "pixel": [u, v], "depth_cv_m": z}
    focal_mm = fx * float(sensor_width_mm) / float(width)
    # Legacy PRE_REAL metadata is retained for microset identity only. Real Maya mapping is
    # always recomputed from canonical K by maya_camera_parameters() below.
    xoff_px = cx - (width - 1) / 2.0
    yoff_px = cy - (height - 1) / 2.0
    xoff_mm = xoff_px / fx * focal_mm
    yoff_mm = yoff_px / fy * focal_mm
    out = {
        "schema": PARITY_EXPECTATION_SCHEMA,
        "case_id": case_id,
        "width": int(width), "height": int(height),
        "sensor_width_mm": float(sensor_width_mm),
        "focal_mm": focal_mm,
        "K": _mat3_list(K),
        "principal_point_px": [cx, cy],
        "film_offset_mm": [xoff_mm, -yoff_mm],
        "camera_center_world": _vec3(pose["camera_center_world"]),
        "R_camera_to_world_graphics": _mat3_list(pose["R_camera_to_world_graphics"]),
        "expected_landmarks": expected,
    }
    out["expectation_sha256"] = identity_digest(out)
    return out


def validate_expectation(exp: Dict[str, Any]) -> None:
    if exp.get("schema") != PARITY_EXPECTATION_SCHEMA:
        raise RuntimeError("BAD_PARITY_EXPECTATION_SCHEMA")
    x = dict(exp)
    got = x.pop("expectation_sha256", None)
    if identity_digest(x) != got:
        raise RuntimeError("PARITY_EXPECTATION_DIGEST_MISMATCH")
    if exp.get("case_id") not in CASES:
        raise RuntimeError("UNKNOWN_PARITY_CASE")
    if not exp.get("expected_landmarks"):
        raise RuntimeError("NO_PARITY_LANDMARKS")
    if int(exp.get("width", 0)) <= 1 or int(exp.get("height", 0)) <= 1:
        raise RuntimeError("BAD_PARITY_RASTER")


def validate_microset(obj: Dict[str, Any]) -> None:
    if obj.get("schema") != MICROSET_SCHEMA:
        raise RuntimeError("BAD_MAYA_MICROSET_SCHEMA")
    x = dict(obj)
    got = x.pop("microset_sha256", None)
    if identity_digest(x) != got:
        raise RuntimeError("MAYA_MICROSET_DIGEST_MISMATCH")
    cases = obj.get("cases", [])
    if [c.get("case_id") for c in cases] != list(CASES):
        raise RuntimeError("MICROSET_CASE_ORDER_OR_SET_INVALID")
    for c in cases:
        validate_expectation(c)


def maya_camera_parameters(exp: Dict[str, Any]) -> Dict[str, float]:
    """Derive Maya film-back parameters from canonical K.

    Maya/OpenGL frustum convention means a positive horizontal film offset moves the
    image principal point left, while a positive vertical film offset moves it down
    in top-left raster coordinates. Canonical K remains the authority.
    """
    validate_expectation(exp)
    w, h = int(exp["width"]), int(exp["height"])
    K = exp["K"]
    fx, fy = float(K[0][0]), float(K[1][1])
    cx, cy = float(K[0][2]), float(K[1][2])
    focal = float(exp["focal_mm"])
    sensor_w = float(exp["sensor_width_mm"])
    sensor_h = sensor_w * float(h) / float(w)
    center_x, center_y = (w - 1) / 2.0, (h - 1) / 2.0
    hoff_mm = (center_x - cx) / fx * focal
    voff_mm = (cy - center_y) / fy * focal
    return {
        "focal_mm": focal,
        "horizontal_film_aperture_in": sensor_w / 25.4,
        "vertical_film_aperture_in": sensor_h / 25.4,
        "horizontal_film_offset_in": hoff_mm / 25.4,
        "vertical_film_offset_in": voff_mm / 25.4,
        "device_aspect_ratio": float(w) / float(h),
        "pixel_aspect": 1.0,
        "film_fit": 1.0,
    }


def reconstructed_principal_point_from_maya_params(exp: Dict[str, Any]) -> List[float]:
    p = maya_camera_parameters(exp)
    w, h = int(exp["width"]), int(exp["height"])
    K = exp["K"]
    fx, fy = float(K[0][0]), float(K[1][1])
    focal = float(p["focal_mm"])
    hoff_mm = float(p["horizontal_film_offset_in"]) * 25.4
    voff_mm = float(p["vertical_film_offset_in"]) * 25.4
    return [
        (w - 1) / 2.0 - fx * hoff_mm / focal,
        (h - 1) / 2.0 + fy * voff_mm / focal,
    ]


def generate_maya_python(exp: Dict[str, Any], result_json_path: str) -> str:
    """Generate an immutable mayapy payload using Maya's real projection matrix.

    The canonical PCS camera is the authority. The worker is intentionally standalone,
    creates a fresh empty scene and writes only a JSON result under the factory run.
    """
    validate_expectation(exp)
    payload = json.dumps(exp, sort_keys=True)
    result_path = str(result_json_path).replace("\\", "/")
    params = maya_camera_parameters(exp)
    camera_params = json.dumps(params, sort_keys=True)
    return textwrap.dedent(f'''\
    import json, math, os, platform, sys, traceback
    import maya.standalone

    EXP = json.loads({payload!r})
    CAM = json.loads({camera_params!r})
    OUT = {result_path!r}
    initialized = False
    try:
        maya.standalone.initialize(name='python')
        initialized = True
        import maya.cmds as cmds
        import maya.api.OpenMaya as om

        cmds.file(new=True, force=True)
        cam_t, cam_s = cmds.camera(name='PCS_DF_PARITY_CAMERA')
        cmds.setAttr(cam_s + '.focalLength', float(CAM['focal_mm']))
        cmds.setAttr(cam_s + '.horizontalFilmAperture', float(CAM['horizontal_film_aperture_in']))
        cmds.setAttr(cam_s + '.verticalFilmAperture', float(CAM['vertical_film_aperture_in']))
        cmds.setAttr(cam_s + '.horizontalFilmOffset', float(CAM['horizontal_film_offset_in']))
        cmds.setAttr(cam_s + '.verticalFilmOffset', float(CAM['vertical_film_offset_in']))
        cmds.setAttr(cam_s + '.filmFit', 1)  # horizontal fit
        for attr, value in [('lensSqueezeRatio',1.0),('overscan',1.0),('cameraScale',1.0),('filmFitOffset',0.0),('horizontalPan',0.0),('verticalPan',0.0),('horizontalShake',0.0),('verticalShake',0.0)]:
            if cmds.attributeQuery(attr, node=cam_s, exists=True):
                cmds.setAttr(cam_s + '.' + attr, value)
        for attr in ['panZoomEnabled','shakeEnabled','shakeOverscanEnabled']:
            if cmds.attributeQuery(attr, node=cam_s, exists=True):
                cmds.setAttr(cam_s + '.' + attr, False)

        w = int(EXP['width']); h = int(EXP['height'])
        cmds.setAttr('defaultResolution.width', w)
        cmds.setAttr('defaultResolution.height', h)
        cmds.setAttr('defaultResolution.pixelAspect', 1.0)
        cmds.setAttr('defaultResolution.deviceAspectRatio', float(w)/float(h))

        R = EXP['R_camera_to_world_graphics']
        C = EXP['camera_center_world']
        # Maya xform accepts row-vector transform layout. Canonical R stores camera basis
        # in columns, so rows below are the transposed basis vectors.
        M = [R[0][0],R[1][0],R[2][0],0.0,
             R[0][1],R[1][1],R[2][1],0.0,
             R[0][2],R[1][2],R[2][2],0.0,
             C[0],C[1],C[2],1.0]
        cmds.xform(cam_t, matrix=M, worldSpace=True)

        sel = om.MSelectionList(); sel.add(cam_s)
        dag = sel.getDagPath(0)
        fn = om.MFnCamera(dag)
        world_inv = dag.inclusiveMatrixInverse()
        proj_raw = fn.projectionMatrix()
        # Maya 2026 Python API 2.0 may return MFloatMatrix here.
        # MPoint multiplication does not accept MFloatMatrix, so materialize
        # the exact 16 numeric values as a double-precision MMatrix first.
        proj = om.MMatrix([float(proj_raw[i]) for i in range(16)])
        view_params = fn.getViewParameters(float(w)/float(h), False, False, False)
        render_frustum = fn.getRenderingFrustum(float(w)/float(h))
        result = {{
            'schema':'{MAYA_RESULT_SCHEMA}', 'status':'PASS_WORKER',
            'case_id':EXP['case_id'], 'width':w, 'height':h,
            'landmarks':{{}},
            'focal_mm':float(cmds.getAttr(cam_s+'.focalLength')),
            'horizontal_film_aperture_in':float(cmds.getAttr(cam_s+'.horizontalFilmAperture')),
            'vertical_film_aperture_in':float(cmds.getAttr(cam_s+'.verticalFilmAperture')),
            'horizontal_film_offset_in':float(cmds.getAttr(cam_s+'.horizontalFilmOffset')),
            'vertical_film_offset_in':float(cmds.getAttr(cam_s+'.verticalFilmOffset')),
            'film_fit':int(cmds.getAttr(cam_s+'.filmFit')),
            'runtime':{{'maya_version':str(cmds.about(version=True)), 'maya_api_version':str(cmds.about(apiVersion=True)), 'platform':platform.platform(), 'python':sys.version.split()[0]}},
            'camera_world_matrix':[float(x) for x in cmds.xform(cam_t, q=True, matrix=True, worldSpace=True)],
            'projection_matrix':[float(proj[i]) for i in range(16)],
            'view_parameters':[float(x) for x in view_params],
            'rendering_frustum':[float(x) for x in render_frustum],
        }}
        for name, rec in EXP['expected_landmarks'].items():
            p = om.MPoint(*rec['world'], 1.0)
            cp = p * world_inv
            clip = cp * proj
            if abs(clip.w) < 1e-12:
                result['landmarks'][name] = {{'valid':False, 'reason':'CLIP_W_ZERO'}}
                continue
            ndcx = clip.x / clip.w; ndcy = clip.y / clip.w
            # Frozen full-raster / pixel-center convention. Do not use (W-1)/(H-1).
            u = (ndcx*0.5 + 0.5) * w - 0.5
            v = (1.0 - (ndcy*0.5 + 0.5)) * h - 0.5
            result['landmarks'][name] = {{
                'valid':True,
                'pixel':[float(u),float(v)],
                'camera_point':[float(cp.x),float(cp.y),float(cp.z),float(cp.w)],
                'clip':[float(clip.x),float(clip.y),float(clip.z),float(clip.w)],
                'ndc':[float(ndcx),float(ndcy)]
            }}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        tmp = OUT + '.tmp'
        with open(tmp,'w',encoding='utf-8') as f:
            json.dump(result,f,indent=2,sort_keys=True)
        os.replace(tmp,OUT)
        print('PCS_DF_MAYA_PARITY_RESULT', OUT, flush=True)
    except Exception as exc:
        fail = {{'schema':'{MAYA_RESULT_SCHEMA}','status':'FAIL_WORKER','case_id':EXP.get('case_id'),'error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()}}
        try:
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT+'.failure.json','w',encoding='utf-8') as f: json.dump(fail,f,indent=2,sort_keys=True)
        except Exception:
            pass
        print(json.dumps(fail,sort_keys=True), file=sys.stderr, flush=True)
        raise
    finally:
        if initialized:
            try: maya.standalone.uninitialize()
            except Exception: pass
    ''')


def _residual(a, b):
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def precision_scale_1920_1080(width: int, height: int) -> float:
    return math.hypot(1920.0, 1080.0) / math.hypot(float(width), float(height))


def compare_roundtrip(expectation: Dict[str, Any], maya_result: Dict[str, Any], blender_result: Dict[str, Any] | None = None,
                      max_px: float = HARD_MAX_PX, median_px: float = HARD_MEDIAN_PX,
                      focal_rel_max: float = FOCAL_REL_MAX, precision_max_eq: float = PRECISION_MAX_EQ_1920_1080_PX) -> Dict[str, Any]:
    validate_expectation(expectation)
    if maya_result.get("schema") != MAYA_RESULT_SCHEMA:
        raise RuntimeError("BAD_MAYA_RESULT_SCHEMA")
    if maya_result.get("case_id") != expectation.get("case_id"):
        raise RuntimeError("PARITY_CASE_MISMATCH")
    residuals = []
    per = {}
    for name, erec in expectation["expected_landmarks"].items():
        mrec = maya_result.get("landmarks", {}).get(name)
        if not mrec or not mrec.get("valid"):
            per[name] = {"status": "MISSING_OR_INVALID"}
            continue
        r = _residual(erec["pixel"], mrec["pixel"])
        residuals.append(r)
        per[name] = {"status":"PASS", "expected_pixel":erec["pixel"], "maya_pixel":mrec["pixel"], "residual_px":r}
    if not residuals:
        maxr = med = rms = float("inf")
    else:
        s = sorted(residuals)
        maxr = max(s)
        med = s[len(s)//2] if len(s)%2 else 0.5*(s[len(s)//2-1]+s[len(s)//2])
        rms = math.sqrt(sum(x*x for x in s)/len(s))
    try:
        mf = float(maya_result.get("focal_mm"))
        focal_rel = abs(mf - float(expectation["focal_mm"])) / max(abs(float(expectation["focal_mm"])), 1e-12)
    except Exception:
        focal_rel = float("inf")

    hard_reasons = []
    if len(residuals) != len(expectation["expected_landmarks"]): hard_reasons.append("LANDMARK_COUNT_INCOMPLETE")
    if not math.isfinite(maxr) or maxr > max_px: hard_reasons.append("MAX_LANDMARK_RESIDUAL")
    if not math.isfinite(med) or med > median_px: hard_reasons.append("MEDIAN_LANDMARK_RESIDUAL")
    if not math.isfinite(focal_rel) or focal_rel > focal_rel_max: hard_reasons.append("FOCAL_REL_ERROR")

    scale = precision_scale_1920_1080(int(expectation["width"]), int(expectation["height"]))
    max_eq = maxr * scale if math.isfinite(maxr) else float("inf")
    precision_pass = math.isfinite(max_eq) and max_eq <= precision_max_eq
    if hard_reasons:
        status = "FAIL"
    elif precision_pass:
        status = "PASS_PRECISION_QUALIFIED"
    else:
        status = "PASS_HARD_NOT_PRECISION_QUALIFIED"

    bsummary = None
    if blender_result is not None:
        bsummary = dict(blender_result)

    return {
        "schema": ROUNDTRIP_REPORT_SCHEMA,
        "case_id": expectation["case_id"],
        "status": status,
        "hard_gate_pass": not hard_reasons,
        "precision_gate_pass": precision_pass,
        "reasons": hard_reasons + ([] if precision_pass else ["G18_PRECISION_TARGET_1920X1080_EQ"]),
        "thresholds": {
            "max_residual_px": float(max_px), "median_residual_px": float(median_px),
            "relative_focal_error": float(focal_rel_max), "max_residual_px_1920x1080_equivalent": float(precision_max_eq),
        },
        "maya": {
            "landmark_count": len(residuals), "expected_landmark_count": len(expectation["expected_landmarks"]),
            "max_residual_px": maxr, "median_residual_px": med, "rms_residual_px": rms,
            "relative_focal_error": focal_rel, "precision_scale_1920x1080_equivalent": scale,
            "max_residual_px_1920x1080_equivalent": max_eq, "per_landmark": per,
        },
        "blender_prerequisite_context": bsummary,
    }


def make_microset(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    if [x.get("case_id") for x in cases] != list(CASES):
        raise ValueError("MICROSET_CASE_ORDER_OR_SET_INVALID")
    out = {"schema": MICROSET_SCHEMA, "cases": cases}
    out["microset_sha256"] = identity_digest(out)
    return out


def svg_for_case(expectation: Dict[str, Any], maya_result: Dict[str, Any], report: Dict[str, Any], exaggeration: float = 80.0) -> str:
    w, h = int(expectation["width"]), int(expectation["height"])
    view_w = 900
    view_h = max(360, int(round(view_w * h / w)))
    sx, sy = view_w / w, view_h / h
    marks = []
    palette = ["#ff4d4f", "#52c41a", "#1677ff", "#722ed1", "#fa8c16", "#13c2c2"]
    for i, (name, erec) in enumerate(expectation["expected_landmarks"].items()):
        mrec = maya_result.get("landmarks", {}).get(name, {})
        ex, ey = float(erec["pixel"][0]), float(erec["pixel"][1])
        x1, y1 = ex*sx, ey*sy
        c = palette[i % len(palette)]
        marks.append(f'<circle cx="{x1:.3f}" cy="{y1:.3f}" r="5" fill="none" stroke="{c}" stroke-width="2"/><text x="{x1+7:.3f}" y="{y1-7:.3f}" font-size="14" fill="{c}">E:{html.escape(name)}</text>')
        if mrec.get("valid"):
            mx, my = map(float, mrec["pixel"])
            # Exaggerate only the vector, keep its origin at exact expected location.
            dx, dy = (mx-ex)*sx*exaggeration, (my-ey)*sy*exaggeration
            x2, y2 = x1+dx, y1+dy
            marks.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{c}" stroke-width="2"/><circle cx="{x2:.3f}" cy="{y2:.3f}" r="3" fill="{c}"/><text x="{x2+5:.3f}" y="{y2+15:.3f}" font-size="11" fill="{c}">M×{exaggeration:g}</text>')
    maxr = report["maya"]["max_residual_px"]
    med = report["maya"]["median_residual_px"]
    eq = report["maya"]["max_residual_px_1920x1080_equivalent"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {view_h+70}" width="100%" height="auto"><rect x="0" y="0" width="{view_w}" height="{view_h}" fill="#20242a" stroke="#ddd"/><text x="12" y="{view_h+24}" fill="#fff" font-size="16">{html.escape(expectation['case_id'])} | {w}×{h} | focal {expectation['focal_mm']:.6f} mm | max {maxr:.6g}px | median {med:.6g}px | eq-max {eq:.6g}px | {html.escape(report['status'])}</text>{''.join(marks)}</svg>'''


def gallery_html(rows: List[Dict[str, Any]], runtime: Dict[str, Any], prerequisite: Dict[str, Any], real: bool) -> str:
    banner = "REAL MAYA PARITY" if real else "PRE_REAL / MOCK"
    cards = []
    for row in rows:
        rep = row["report"]
        cards.append(f'''<section class="card"><h2>{html.escape(row['case_id'])} — {html.escape(rep['status'])}</h2><p>max={rep['maya']['max_residual_px']:.9g}px · median={rep['maya']['median_residual_px']:.9g}px · 1920×1080eq max={rep['maya']['max_residual_px_1920x1080_equivalent']:.9g}px · focal rel={rep['maya']['relative_focal_error']:.3g}</p><iframe src="{html.escape(row['svg_name'])}" loading="lazy"></iframe></section>''')
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>DF-G60..G62 Maya Parity</title><style>body{{font-family:Segoe UI,Arial;background:#0f1115;color:#e9edf2;margin:24px}}header{{padding:18px;background:#18202b;border:1px solid #3b4a5d}}.card{{margin:18px 0;padding:15px;background:#171b21;border:1px solid #343b46}}iframe{{width:100%;height:520px;border:0;background:#111}}code{{color:#aee}}</style></head><body><header><h1>{banner}</h1><p>Maya: {html.escape(str(runtime.get('maya_version')))} · API {html.escape(str(runtime.get('maya_api_version')))} · mayapy SHA {html.escape(str(runtime.get('mayapy_sha256')))}</p><p>Accepted Blender R9 prerequisite: {html.escape(str(prerequisite.get('sha256')))} · worst Blender camera residual {prerequisite.get('worst_max_reprojection_px')}</p></header>{''.join(cards)}</body></html>'''
