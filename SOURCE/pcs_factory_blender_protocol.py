from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pcs_factory_seed import canonical_json_bytes, identity_digest
from pcs_factory_qualification import is_factory_qualification_split
from pcs_factory_paths import write_json_atomic

REQUEST_SCHEMA = "DF-G51-BLENDER-RENDER-REQUEST-V1"
COMPLETION_SCHEMA = "DF-G51-BLENDER-COMPLETION-MANIFEST-V1"
CHUNK_SCHEMA = "DF-G54-CHUNK-MANIFEST-V1"
LEDGER_SCHEMA = "DF-G54-CHUNK-LEDGER-V1"
RESULT_SCHEMA = "DF-G56-WORKER-RESULT-MANIFEST-V1"
VALID_STATES = {"PENDING", "RUNNING", "COMPLETE", "FAILED_RETRYABLE", "FAILED_FINAL"}


def resolve_scene_family(scene: Dict[str, Any]) -> str:
    """Resolve scene-family metadata for post-render consumers without altering request identity.

    Current canonical DF-G20..G31 scene recipes use ``scene_family``. ``family`` is accepted
    only as a historical compatibility alias for older persisted artifacts.
    """
    if not isinstance(scene, dict):
        raise RuntimeError("SCENE_FAMILY_MISSING:scene_not_mapping")
    value = scene.get("scene_family")
    if value is None:
        value = scene.get("family")
    if value is None or not str(value).strip():
        raise RuntimeError("SCENE_FAMILY_MISSING")
    return str(value)





def ndc_to_pcs_pixel(ndc_x: float, ndc_y: float, width: int, height: int):
    """Map Blender camera-frame NDC (frame boundaries 0..1, y up) to PCS pixel centers.

    PCS raster authority uses the center of the top-left pixel as (0,0), hence
    frame boundaries are at -0.5 and W-0.5 / H-0.5.
    """
    w, h = int(width), int(height)
    if w <= 0 or h <= 0:
        raise ValueError("INVALID_RASTER_DIMENSIONS")
    x, y = float(ndc_x), float(ndc_y)
    return (x * float(w) - 0.5, (1.0 - y) * float(h) - 0.5)


def pixel_in_physical_raster(pixel, width: int, height: int) -> bool:
    """Return True only when a canonical pixel center lies inside the physical raster.

    PCS pixel-center coordinates put the physical frame boundaries at -0.5 and
    W-0.5 / H-0.5. R13 uses this exact domain to decide which pre-render
    reprojection landmarks carry acceptance authority.
    """
    w, h = int(width), int(height)
    if w <= 0 or h <= 0:
        raise ValueError("INVALID_RASTER_DIMENSIONS")
    try:
        u, v = float(pixel[0]), float(pixel[1])
    except Exception:
        return False
    return (math.isfinite(u) and math.isfinite(v) and
            -0.5 <= u <= float(w) - 0.5 and
            -0.5 <= v <= float(h) - 0.5)


def initial_blender_camera_from_K(K, width: int, height: int, sensor_width_mm: float = 36.0):
    """Deterministic initial Blender camera parameters from canonical pixel-center K.

    The final canonical authority remains K; the Blender worker numerically verifies/calibrates
    against Blender's own camera projection API after applying these initial values.
    """
    w, h = int(width), int(height)
    if w <= 1 or h <= 1:
        raise ValueError("INVALID_RASTER_DIMENSIONS")
    fx, fy = float(K[0][0]), float(K[1][1])
    cx, cy = float(K[0][2]), float(K[1][2])
    if fx <= 0 or fy <= 0 or sensor_width_mm <= 0:
        raise ValueError("INVALID_INTRINSICS")
    if fx >= fy:
        pax, pay = 1.0, fx / fy
    else:
        pax, pay = fy / fx, 1.0
    # world_to_camera_view spans the physical frame boundaries, therefore W (not W-1)
    # is the horizontal raster span corresponding to fx pixels.
    view_fac = float(w)
    return {
        "lens_mm": fx * float(sensor_width_mm) / view_fac,
        "shift_x": -(cx - (w - 1) / 2.0) / view_fac,
        "shift_y": +(cy - (h - 1) / 2.0) / view_fac,
        "pixel_aspect_x": pax,
        "pixel_aspect_y": pay,
        "raster_span_px": view_fac,
    }

PASS_SOCKET_BY_NAME = {
    "DEPTH": "Depth",
    "NORMAL": "Normal",
    "OBJECT_INDEX": "IndexOB",
}

def validate_engine_pass_contract(engine: str, passes) -> None:
    eng = str(engine)
    req = set(passes or [])
    if "OBJECT_INDEX" in req and eng != "CYCLES":
        raise RuntimeError(f"ENGINE_PASS_INCOMPATIBLE:{eng}:OBJECT_INDEX:REQUIRES_CYCLES")

def resolve_render_layer_socket_name(engine: str, pass_name: str, available_socket_names) -> str:
    validate_engine_pass_contract(engine, ["RGB", pass_name])
    if pass_name not in PASS_SOCKET_BY_NAME:
        raise RuntimeError(f"UNKNOWN_AUX_PASS:{pass_name}")
    expected = PASS_SOCKET_BY_NAME[pass_name]
    available = [str(x) for x in available_socket_names]
    if expected not in available:
        raise RuntimeError(
            "PASS_SOCKET_UNAVAILABLE:"
            f"engine={engine}:pass={pass_name}:expected={expected}:"
            f"available={json.dumps(available, separators=(',', ':'))}"
        )
    return expected


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def file_record(path: Path, relative_to: Optional[Path] = None) -> Dict[str, Any]:
    p = Path(path)
    rel = p.relative_to(relative_to).as_posix() if relative_to else p.name
    return {"path": rel, "bytes": p.stat().st_size, "sha256": sha256_file(p)}


def _digest_without(obj: Dict[str, Any], key: str) -> str:
    x = dict(obj)
    x.pop(key, None)
    return identity_digest(x)


def finalize_request(obj: Dict[str, Any]) -> Dict[str, Any]:
    x = dict(obj)
    x["schema"] = REQUEST_SCHEMA
    x.pop("input_digest_sha256", None)
    x["input_digest_sha256"] = identity_digest(x)
    return x


def validate_request(obj: Dict[str, Any]) -> None:
    if obj.get("schema") != REQUEST_SCHEMA:
        raise RuntimeError("BAD_REQUEST_SCHEMA")
    got = obj.get("input_digest_sha256")
    if not isinstance(got, str) or len(got) != 64:
        raise RuntimeError("MISSING_REQUEST_DIGEST")
    if _digest_without(obj, "input_digest_sha256") != got:
        raise RuntimeError("REQUEST_DIGEST_MISMATCH")
    sid = str(obj.get("sample_id", ""))
    if not sid or any(c in sid for c in "\\/:*?\"<>|") or sid in {".", ".."}:
        raise RuntimeError("UNSAFE_SAMPLE_ID")
    if obj.get("renderer", {}).get("engine") not in {"BLENDER_EEVEE_NEXT", "CYCLES"}:
        raise RuntimeError("UNSUPPORTED_RENDER_ENGINE")
    out_rel = str(obj.get("output_rel", ""))
    pp = Path(out_rel)
    if not out_rel or pp.is_absolute() or ".." in pp.parts:
        raise RuntimeError("UNSAFE_OUTPUT_REL")
    passes = obj.get("passes")
    if not isinstance(passes, list) or "RGB" not in passes:
        raise RuntimeError("RGB_PASS_REQUIRED")
    validate_engine_pass_contract(obj.get("renderer", {}).get("engine"), passes)


def write_request(path: Path, obj: Dict[str, Any]) -> Dict[str, Any]:
    x = finalize_request(obj)
    validate_request(x)
    write_json_atomic(Path(path), x)
    return x


def finalize_chunk(obj: Dict[str, Any]) -> Dict[str, Any]:
    x = dict(obj)
    x["schema"] = CHUNK_SCHEMA
    x.pop("chunk_digest_sha256", None)
    x["chunk_digest_sha256"] = identity_digest(x)
    return x


def validate_chunk(obj: Dict[str, Any]) -> None:
    if obj.get("schema") != CHUNK_SCHEMA:
        raise RuntimeError("BAD_CHUNK_SCHEMA")
    got = obj.get("chunk_digest_sha256")
    if _digest_without(obj, "chunk_digest_sha256") != got:
        raise RuntimeError("CHUNK_DIGEST_MISMATCH")
    reqs = obj.get("requests")
    if not isinstance(reqs, list) or not reqs:
        raise RuntimeError("EMPTY_CHUNK")
    ids = []
    digests = []
    for r in reqs:
        validate_request(r)
        ids.append(r["sample_id"])
        digests.append(r["input_digest_sha256"])
    if len(ids) != len(set(ids)):
        raise RuntimeError("DUPLICATE_SAMPLE_ID_IN_CHUNK")
    if len(digests) != len(set(digests)):
        raise RuntimeError("DUPLICATE_REQUEST_DIGEST_IN_CHUNK")


def new_ledger(chunk: Dict[str, Any], worker_id: Optional[str] = None) -> Dict[str, Any]:
    validate_chunk(chunk)
    return {
        "schema": LEDGER_SCHEMA,
        "chunk_digest_sha256": chunk["chunk_digest_sha256"],
        "worker_id": worker_id,
        "states": {r["sample_id"]: {"state": "PENDING", "attempts": 0, "request_digest": r["input_digest_sha256"]} for r in chunk["requests"]},
    }


def validate_ledger(ledger: Dict[str, Any], chunk: Dict[str, Any]) -> None:
    validate_chunk(chunk)
    if ledger.get("schema") != LEDGER_SCHEMA:
        raise RuntimeError("BAD_LEDGER_SCHEMA")
    if ledger.get("chunk_digest_sha256") != chunk.get("chunk_digest_sha256"):
        raise RuntimeError("LEDGER_WRONG_CHUNK")
    expected = {r["sample_id"]: r["input_digest_sha256"] for r in chunk["requests"]}
    states = ledger.get("states", {})
    if set(states) != set(expected):
        raise RuntimeError("LEDGER_SAMPLE_SET_MISMATCH")
    for sid, rec in states.items():
        if rec.get("state") not in VALID_STATES:
            raise RuntimeError(f"BAD_LEDGER_STATE:{sid}")
        if rec.get("request_digest") != expected[sid]:
            raise RuntimeError(f"LEDGER_REQUEST_DIGEST_CHANGED:{sid}")


def transition(ledger: Dict[str, Any], sample_id: str, new_state: str, error: Optional[str] = None) -> None:
    if new_state not in VALID_STATES:
        raise ValueError(new_state)
    rec = ledger["states"][sample_id]
    old = rec["state"]
    allowed = {
        "PENDING": {"RUNNING", "FAILED_FINAL"},
        "RUNNING": {"COMPLETE", "FAILED_RETRYABLE", "FAILED_FINAL"},
        "FAILED_RETRYABLE": {"RUNNING", "FAILED_FINAL"},
        "COMPLETE": set(),
        "FAILED_FINAL": set(),
    }
    if new_state not in allowed[old]:
        raise RuntimeError(f"ILLEGAL_LEDGER_TRANSITION:{old}->{new_state}")
    rec["state"] = new_state
    if new_state == "RUNNING":
        rec["attempts"] = int(rec.get("attempts", 0)) + 1
    if error is not None:
        rec["last_error"] = str(error)


def interrupted_running_to_retryable(ledger: Dict[str, Any]) -> int:
    n = 0
    for rec in ledger.get("states", {}).values():
        if rec.get("state") == "RUNNING":
            rec["state"] = "FAILED_RETRYABLE"
            rec["last_error"] = "INTERRUPTED_PREVIOUS_PROCESS"
            n += 1
    return n


def validate_completion(completion: Dict[str, Any], request: Dict[str, Any], sample_dir: Path) -> None:
    validate_request(request)
    if completion.get("schema") != COMPLETION_SCHEMA:
        raise RuntimeError("BAD_COMPLETION_SCHEMA")
    if completion.get("sample_id") != request.get("sample_id"):
        raise RuntimeError("COMPLETION_SAMPLE_ID_MISMATCH")
    if completion.get("input_digest_sha256") != request.get("input_digest_sha256"):
        raise RuntimeError("COMPLETION_REQUEST_DIGEST_MISMATCH")
    files = completion.get("files")
    if not isinstance(files, list):
        raise RuntimeError("COMPLETION_FILES_MISSING")
    by_path = {f.get("path"): f for f in files}
    if "rgb.png" not in by_path:
        raise RuntimeError("MANDATORY_RGB_MISSING_FROM_MANIFEST")
    requested = set(request.get("passes", []))
    expected_aux = {"DEPTH": "depth.exr", "NORMAL": "normal.exr", "OBJECT_INDEX": "object_index.exr"}
    for p, name in expected_aux.items():
        if p in requested and name not in by_path:
            raise RuntimeError(f"REQUESTED_PASS_MISSING:{p}")
    for rec in files:
        p = Path(sample_dir) / rec["path"]
        if not p.is_file():
            raise RuntimeError(f"COMPLETION_FILE_ABSENT:{rec['path']}")
        if p.stat().st_size != rec.get("bytes"):
            raise RuntimeError(f"COMPLETION_FILE_SIZE_MISMATCH:{rec['path']}")
        if sha256_file(p) != rec.get("sha256"):
            raise RuntimeError(f"COMPLETION_FILE_SHA_MISMATCH:{rec['path']}")
    repro = completion.get("camera_reprojection", {})
    if repro.get("status") != "PASS":
        raise RuntimeError("CAMERA_REPROJECTION_NOT_PASS")
    if float(repro.get("max_residual_px", 1e9)) > 0.50:
        raise RuntimeError("CAMERA_REPROJECTION_MAX_EXCEEDS_SPEC")
    if float(repro.get("median_residual_px", 1e9)) > 0.20:
        raise RuntimeError("CAMERA_REPROJECTION_MEDIAN_EXCEEDS_SPEC")
    if is_factory_qualification_split(request.get("split")):
        gt = completion.get("micro100_aux_gt")
        if not isinstance(gt, dict) or gt.get("status") != "PASS":
            raise RuntimeError("G100_AUX_GT_NOT_PASS_IN_COMPLETION")
        by_path = {f.get("path"): f for f in files}
        required=["normal_authority_mask.uint8.bin", "micro100_aux_gt_qa.json"]
        if gt.get("r6_addendum_drive_id") or "filter_safe_interior_authority_fraction" in (gt.get("normal") or {}):
            required.append("normal_filter_safe_interior_mask.uint8.bin")
        depth = gt.get("depth") or {}
        if depth.get("authority_semantics") == "FILTER_SAFE_INTERIOR_EXACT_DEPTH_R29_V1" or depth.get("r29_spec_drive_id"):
            required.append("depth_filter_safe_interior_mask.uint8.bin")
        for extra in required:
            if extra not in by_path:
                raise RuntimeError("G100_REQUIRED_QA_MEMBER_MISSING:" + extra)


def cache_reusable(sample_dir: Path, request: Dict[str, Any], runtime_lock: Dict[str, Any]) -> bool:
    cpath = Path(sample_dir) / "completion.json"
    if not cpath.is_file():
        return False
    try:
        c = json.loads(cpath.read_text(encoding="utf-8"))
        if c.get("runtime_archive_sha256") != runtime_lock.get("archive_sha256"):
            return False
        validate_completion(c, request, sample_dir)
        return True
    except Exception:
        return False
