from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pcs_factory_appearance import canonical_profiles
from pcs_factory_blender_protocol import (
    CHUNK_SCHEMA, LEDGER_SCHEMA, RESULT_SCHEMA, cache_reusable, finalize_chunk,
    interrupted_running_to_retryable, new_ledger, transition, validate_chunk,
    validate_completion, validate_ledger, write_request, file_record, sha256_file,
    resolve_scene_family,
)
from pcs_factory_blender_runtime import runtime_paths, query_blender_identity
from pcs_factory_camera import camera_profile
from pcs_factory_paths import resolve_factory_root, write_json_atomic
from pcs_factory_scene_recipe import generate_archetype, validate_scene
from pcs_factory_seed import derive_seed
from pcs_factory_run_journal import journal_event

RUN_SCHEMA = "DF-G58-BLENDER-SELFTEST-RUN-V1"
ROOT_SEED = 34620260905


def utc_now_compact():
    # Microseconds reduce collision probability; allocation below still collision-checks the filesystem.
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def _profile_by_id(pid: str) -> Dict:
    for p in canonical_profiles():
        if p["profile_id"] == pid:
            return p
    raise KeyError(pid)


def make_selftest_requests(run_id: str) -> List[Dict]:
    specs = [
        # family, camera profile, appearance, engine, width, height, passes, samples
        ("INTERIOR", "NORMAL", "PBR_REALISTIC_INTENT", "CYCLES", 640, 360, ["RGB", "DEPTH", "NORMAL", "OBJECT_INDEX"], 4),
        ("URBAN", "WIDE", "DAY_HARD", "BLENDER_EEVEE_NEXT", 640, 360, ["RGB"], 1),
        ("NON_MANHATTAN", "STRONG_ROLL", "TOON", "BLENDER_EEVEE_NEXT", 640, 360, ["RGB"], 1),
        ("SPARSE", "TELEPHOTO", "CLAY", "BLENDER_EEVEE_NEXT", 640, 360, ["RGB"], 1),
        ("REPEATED_PATTERN", "OFFCENTER", "BLUEPRINT", "BLENDER_EEVEE_NEXT", 640, 360, ["RGB"], 1),
        ("HYBRID_CONCEPT", "NORMAL", "PAINTERLY_CONCEPT", "CYCLES", 384, 216, ["RGB"], 8),
    ]
    out = []
    for i, (family, cam_name, appearance_id, engine, w, h, passes, samples) in enumerate(specs):
        scene = generate_archetype(family, index=i, root_seed=ROOT_SEED)
        sv = validate_scene(scene)
        if sv["status"] != "PASS":
            raise RuntimeError(f"SELFTEST_SCENE_INVALID:{family}:{sv['findings']}")
        cam_seed = derive_seed(ROOT_SEED, "df_g58_camera", family, i)["seed_u64"]
        cam = camera_profile(cam_name, cam_seed, width=w, height=h)
        appearance = _profile_by_id(appearance_id)
        sid = f"dfg58_{i:02d}_{family.lower()}_{cam_name.lower()}_{appearance_id.lower()}"
        req = {
            "sample_id": sid,
            "run_id": run_id,
            "scene": scene,
            "camera": {
                "profile": cam["profile"],
                "width": cam["width"],
                "height": cam["height"],
                "K": cam["K"],
                "pose": cam["pose"],
                "sampled": cam["sampled"],
            },
            "appearance": appearance,
            "renderer": {
                "engine": engine,
                "samples": samples,
                "denoise": True if engine == "CYCLES" else False,
                "device": "AUTO",
            },
            "passes": passes,
            "output_rel": f"samples/{sid}",
            "gt_class": "GT_EXACT_3D_CAMERA",
            "split": "DF_G58_SELFTEST_ONLY",
            "test77_accessed": False,
        }
        from pcs_factory_blender_protocol import finalize_request
        out.append(finalize_request(req))
    return out


def make_selftest_chunk(run_id: str, worker_id: str = "LOCAL_WINDOWS") -> Dict:
    chunk = {
        "chunk_id": f"DF_G58_SELFTEST_{run_id}",
        "worker_protocol_version": "DF-G56-V1",
        "worker_id_hint": worker_id,
        "root_seed": ROOT_SEED,
        "requests": make_selftest_requests(run_id),
        "split": "DF_G58_SELFTEST_ONLY",
        "test77_accessed": False,
        "training_started": False,
        "maya_mutated": False,
        "product_mutated": False,
    }
    return finalize_chunk(chunk)


def _nvidia_smi_sample() -> Optional[Dict]:
    # Optional telemetry is deliberately isolated from render authority. Any failure is swallowed.
    try:
        exe = shutil.which("nvidia-smi")
        if not exe:
            return None
        cp = subprocess.run(
            [exe, "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5, check=False,
        )
        if cp.returncode != 0 or not cp.stdout.strip():
            return None
        parts = [x.strip() for x in cp.stdout.splitlines()[0].split(",")]
        if len(parts) < 4:
            return None
        return {"name": parts[0], "memory_used_mib": float(parts[1]), "memory_total_mib": float(parts[2]), "utilization_percent": float(parts[3])}
    except Exception:
        return None


def run_worker(factory_root: Path, blender_exe: Path, worker_script: Path, runtime_lock: Path, run_root: Path, request_path: Path,
               log_path: Path, sample_id: str, attempt: int) -> Dict:
    cmd = [
        str(blender_exe), "--background", "--factory-startup",
        "--python", str(worker_script), "--",
        "--request", str(request_path), "--runtime-lock", str(runtime_lock), "--run-root", str(run_root),
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    gpu_samples = []
    start = time.perf_counter()
    last_report = start
    journal_event(factory_root, "G100_WORKER", "BEFORE_WORKER_SPAWN", sample_id=sample_id, attempt=int(attempt), worker_pid=None, command=cmd)
    with log_path.open("w", encoding="utf-8", errors="replace", newline="\n") as log:
        p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
        journal_event(factory_root, "G100_WORKER", "WORKER_PROCESS_STARTED", sample_id=sample_id, attempt=int(attempt), worker_pid=int(p.pid))
        while p.poll() is None:
            # R6: no in-process Win32 ctypes process telemetry. Optional GPU telemetry is exception-contained.
            g = _nvidia_smi_sample()
            if g:
                gpu_samples.append(g)
            now = time.perf_counter()
            if now - last_report >= 12.0:
                elapsed = now - start
                if g:
                    print(f"[DF-G100] render still running: {elapsed:.0f}s | GPU {g['utilization_percent']:.0f}% | VRAM {g['memory_used_mib']:.0f} MiB", flush=True)
                else:
                    print(f"[DF-G100] render still running: {elapsed:.0f}s", flush=True)
                journal_event(factory_root, "G100_WORKER", "WORKER_HEARTBEAT", sample_id=sample_id, attempt=int(attempt), worker_pid=int(p.pid), elapsed_seconds=elapsed, gpu=g)
                last_report = now
            time.sleep(0.75)
        rc = p.returncode
    elapsed = time.perf_counter() - start
    journal_event(factory_root, "G100_WORKER", "WORKER_PROCESS_EXITED", sample_id=sample_id, attempt=int(attempt), worker_pid=int(p.pid), child_exit_code=int(rc), elapsed_seconds=elapsed)
    profile = {
        "returncode": rc,
        "wall_seconds": elapsed,
        "gpu_telemetry_available": bool(gpu_samples),
        "process_metrics_available": False,
        "process_metrics_policy": "R6_DISABLED_UNSAFE_INPROCESS_WIN32_CTYPES",
    }
    if gpu_samples:
        profile["gpu_name"] = gpu_samples[0]["name"]
        profile["peak_observed_vram_mib"] = max(x["memory_used_mib"] for x in gpu_samples)
        profile["peak_observed_gpu_utilization_percent"] = max(x["utilization_percent"] for x in gpu_samples)
        profile["gpu_total_mib"] = gpu_samples[0]["memory_total_mib"]
    return profile


def execute_chunk(root: Path, chunk: Dict, run_root: Path, worker_id: str = "LOCAL_WINDOWS", max_attempts: int = 2) -> Dict:
    validate_chunk(chunk)
    rt = runtime_paths(root)
    lock_path = rt["lock_path"]
    blender_exe = rt["runtime_dir"] / "blender.exe"
    if not lock_path.is_file() or not blender_exe.is_file():
        raise RuntimeError("BLENDER_RUNTIME_NOT_READY")
    runtime_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    worker_script = Path(__file__).resolve().with_name("pcs_factory_blender_worker.py")
    if not worker_script.is_file():
        raise RuntimeError("BLENDER_WORKER_SCRIPT_MISSING")

    run_root.mkdir(parents=True, exist_ok=True)
    chunk_path = run_root / "chunk_manifest.json"
    write_json_atomic(chunk_path, chunk)
    ledger_path = run_root / "ledger.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        validate_ledger(ledger, chunk)
        interrupted_running_to_retryable(ledger)
    else:
        ledger = new_ledger(chunk, worker_id=worker_id)
    write_json_atomic(ledger_path, ledger)

    by_id = {r["sample_id"]: r for r in chunk["requests"]}
    profiles = {}
    for sid in [r["sample_id"] for r in chunk["requests"]]:
        req = by_id[sid]
        rec = ledger["states"][sid]
        sample_dir = run_root / req["output_rel"]
        if rec["state"] == "COMPLETE":
            if cache_reusable(sample_dir, req, runtime_lock):
                print(f"[DF-G100] {sid}: COMPLETE cache verified; reusing exact result.", flush=True)
                continue
            raise RuntimeError(f"COMPLETED_SAMPLE_BECAME_INVALID:{sid}")
        if cache_reusable(sample_dir, req, runtime_lock):
            # A valid immutable completion exists but ledger was interrupted before marking COMPLETE.
            if rec["state"] == "RUNNING": rec["state"] = "FAILED_RETRYABLE"
            if rec["state"] in {"PENDING", "FAILED_RETRYABLE"}:
                if rec["state"] == "PENDING":
                    transition(ledger, sid, "RUNNING")
                else:
                    transition(ledger, sid, "RUNNING")
                transition(ledger, sid, "COMPLETE")
                write_json_atomic(ledger_path, ledger)
                continue
        while rec["state"] in {"PENDING", "FAILED_RETRYABLE"} and int(rec.get("attempts", 0)) < max_attempts:
            next_attempt = int(rec.get("attempts", 0)) + 1
            print(f"[DF-G100] {sid}: starting render attempt {next_attempt}/{max_attempts} | {req['renderer']['engine']} | {req['camera']['width']}x{req['camera']['height']}", flush=True)
            transition(ledger, sid, "RUNNING")
            write_json_atomic(ledger_path, ledger)
            req_dir = run_root / "requests"
            req_dir.mkdir(parents=True, exist_ok=True)
            req_path = req_dir / f"{sid}.json"
            write_json_atomic(req_path, req)
            profile = run_worker(root, blender_exe, worker_script, lock_path, run_root, req_path,
                                 run_root / "logs" / f"{sid}.log", sid, next_attempt)
            profiles[sid] = profile
            try:
                if profile["returncode"] != 0:
                    raise RuntimeError(f"BLENDER_WORKER_RC:{profile['returncode']}")
                cpath = sample_dir / "completion.json"
                if not cpath.is_file():
                    raise RuntimeError("COMPLETION_JSON_MISSING")
                completion = json.loads(cpath.read_text(encoding="utf-8"))
                validate_completion(completion, req, sample_dir)
                transition(ledger, sid, "COMPLETE")
                print(f"[DF-G100] {sid}: PASS in {profile['wall_seconds']:.1f}s | camera max {completion['camera_reprojection']['max_residual_px']:.4f}px", flush=True)
            except Exception as e:
                print(f"[DF-G100] {sid}: attempt failed: {type(e).__name__}: {e}", flush=True)
                if int(rec.get("attempts", 0)) < max_attempts:
                    transition(ledger, sid, "FAILED_RETRYABLE", str(e))
                else:
                    transition(ledger, sid, "FAILED_FINAL", str(e))
            write_json_atomic(ledger_path, ledger)
        if rec["state"] != "COMPLETE":
            break

    validate_ledger(ledger, chunk)
    completed = [sid for sid, rec in ledger["states"].items() if rec["state"] == "COMPLETE"]
    failed = [sid for sid, rec in ledger["states"].items() if rec["state"] == "FAILED_FINAL"]
    result = {
        "schema": RESULT_SCHEMA,
        "status": "PASS" if len(completed) == len(chunk["requests"]) and not failed else "FAIL",
        "chunk_digest_sha256": chunk["chunk_digest_sha256"],
        "worker_id": worker_id,
        "completed_count": len(completed),
        "failed_final_count": len(failed),
        "completed_sample_ids": completed,
        "failed_sample_ids": failed,
        "profiles": profiles,
        "test77_accessed": False,
        "training_started": False,
        "maya_mutated": False,
        "product_mutated": False,
    }
    write_json_atomic(run_root / "worker_result_manifest.json", result)
    return result


def summarize_run(root: Path, chunk: Dict, run_root: Path, result: Dict) -> Dict:
    runtime_lock = json.loads(runtime_paths(root)["lock_path"].read_text(encoding="utf-8"))
    rows = []
    total_output = 0
    for req in chunk["requests"]:
        sid = req["sample_id"]
        sample_dir = run_root / req["output_rel"]
        c = json.loads((sample_dir / "completion.json").read_text(encoding="utf-8"))
        files_bytes = sum(int(x["bytes"]) for x in c["files"])
        total_output += files_bytes
        rows.append({
            "sample_id": sid,
            "family": resolve_scene_family(req["scene"]),
            "camera_profile": req["camera"]["profile"],
            "appearance_profile": req["appearance"]["profile_id"],
            "renderer": req["renderer"]["engine"],
            "width": req["camera"]["width"],
            "height": req["camera"]["height"],
            "render_elapsed_seconds": c["render_elapsed_seconds"],
            "output_bytes": files_bytes,
            "max_reprojection_px": c["camera_reprojection"]["max_residual_px"],
            "median_reprojection_px": c["camera_reprojection"]["median_residual_px"],
        })
    total_render_seconds = sum(r["render_elapsed_seconds"] for r in rows)
    return {
        "schema": RUN_SCHEMA,
        "status": result["status"],
        "real_blender_rendered": result["status"] == "PASS",
        "runtime_lock": runtime_lock,
        "chunk_digest_sha256": chunk["chunk_digest_sha256"],
        "sample_count": len(rows),
        "rows": rows,
        "total_render_seconds": total_render_seconds,
        "images_per_hour_render_only": (len(rows) * 3600.0 / total_render_seconds) if total_render_seconds > 0 else None,
        "total_output_bytes": total_output,
        "median_output_bytes_per_sample": statistics.median([r["output_bytes"] for r in rows]) if rows else None,
        "max_camera_reprojection_px": max([r["max_reprojection_px"] for r in rows], default=None),
        "median_of_sample_median_reprojection_px": statistics.median([r["median_reprojection_px"] for r in rows]) if rows else None,
        "test77_accessed": False,
        "training_started": False,
        "maya_mutated": False,
        "product_mutated": False,
    }


def _run_root_for_id(root: Path, run_id: str) -> Path:
    return Path(root) / "07_OUTPUT" / "RUNS" / f"DF_G58_SELFTEST_{run_id}"


def _validate_existing_run_compatibility(root: Path, run_id: str, worker_id: str = "LOCAL_WINDOWS") -> Dict:
    run_root = _run_root_for_id(root, run_id)
    if not run_root.is_dir():
        raise RuntimeError(f"RUN_ID_NOT_FOUND:{run_id}")
    cpath = run_root / "chunk_manifest.json"
    if not cpath.is_file():
        raise RuntimeError(f"RUN_CHUNK_MANIFEST_MISSING:{run_id}")
    persisted = json.loads(cpath.read_text(encoding="utf-8"))
    expected = make_selftest_chunk(run_id, worker_id=worker_id)
    # Compare immutable identity before applying the current protocol validator so historical
    # chunks superseded by stricter contracts are classified as incompatible, never mutated.
    if persisted.get("schema") != CHUNK_SCHEMA:
        raise RuntimeError(f"RUN_CHUNK_SCHEMA_INCOMPATIBLE:{run_id}:{persisted.get('schema')}")
    if persisted.get("chunk_digest_sha256") != expected.get("chunk_digest_sha256"):
        raise RuntimeError(
            f"RUN_ID_INCOMPATIBLE_CHUNK:{run_id}:persisted={persisted.get('chunk_digest_sha256')}:"
            f"expected={expected.get('chunk_digest_sha256')}"
        )
    validate_chunk(persisted)
    lpath = run_root / "ledger.json"
    if lpath.is_file():
        ledger = json.loads(lpath.read_text(encoding="utf-8"))
        validate_ledger(ledger, expected)
    return {"run_id": run_id, "run_root": str(run_root), "chunk_digest_sha256": expected["chunk_digest_sha256"]}


def _allocate_fresh_run_id(root: Path) -> str:
    base = Path(root) / "07_OUTPUT" / "RUNS"
    base.mkdir(parents=True, exist_ok=True)
    for attempt in range(1000):
        rid = utc_now_compact()
        if attempt:
            rid = f"{rid}_{attempt:03d}"
        if not _run_root_for_id(root, rid).exists():
            return rid
        time.sleep(0.001)
    raise RuntimeError("FRESH_RUN_ID_ALLOCATION_EXHAUSTED")


def _select_compatible_resume_run_id(root: Path, requested: Optional[str], worker_id: str = "LOCAL_WINDOWS") -> str:
    if requested:
        _validate_existing_run_compatibility(root, requested, worker_id=worker_id)
        return requested
    base = Path(root) / "07_OUTPUT" / "RUNS"
    existing = sorted(
        (p for p in base.glob("DF_G58_SELFTEST_*") if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    ) if base.is_dir() else []
    rejected = []
    for p in existing:
        rid = p.name[len("DF_G58_SELFTEST_"):]
        try:
            _validate_existing_run_compatibility(root, rid, worker_id=worker_id)
            return rid
        except Exception as e:
            rejected.append(f"{rid}={type(e).__name__}:{e}")
    tail = "|".join(rejected[:8])
    raise RuntimeError(f"NO_COMPATIBLE_RUN_TO_RESUME:{tail}")


def run_selftest(root: Path, run_id: Optional[str] = None, worker_id: str = "LOCAL_WINDOWS",
                 operation_mode: str = "fresh") -> Dict:
    mode = str(operation_mode).lower()
    if mode not in {"fresh", "resume"}:
        raise ValueError(f"BAD_OPERATION_MODE:{operation_mode}")
    if mode == "resume":
        rid = _select_compatible_resume_run_id(root, run_id, worker_id=worker_id)
        print(f"[DF-G54] Resume selected compatible run_id={rid}", flush=True)
    elif run_id:
        # Explicit identity is deliberate. Existing state is accepted only when exact-compatible.
        if _run_root_for_id(root, run_id).exists():
            _validate_existing_run_compatibility(root, run_id, worker_id=worker_id)
            print(f"[DF-G54] Fresh entrypoint received explicit existing compatible run_id={run_id}; reusing exact identity.", flush=True)
        rid = run_id
    else:
        rid = _allocate_fresh_run_id(root)
        print(f"[DF-G54] Fresh run allocated new run_id={rid}", flush=True)

    run_root = _run_root_for_id(root, rid)
    chunk = make_selftest_chunk(rid, worker_id=worker_id)
    journal_event(root, "G58_RUN", "RUN_ID_SELECTED", run_id=rid, run_root=str(run_root), chunk_digest_sha256=chunk["chunk_digest_sha256"], operation_mode=mode)
    result = execute_chunk(root, chunk, run_root, worker_id=worker_id)
    if result["status"] != "PASS":
        journal_event(root, "G58_RUN", "RUN_SELFTEST_FAILED", run_id=rid, run_root=str(run_root), worker_result_status=result.get("status"))
        return {"status": "FAIL", "operation_mode": mode, "selected_run_id": rid,
                "run_root": str(run_root), "worker_result": result}
    summary = summarize_run(root, chunk, run_root, result)
    summary["operation_mode"] = mode
    write_json_atomic(run_root / "DF_G50_G58_REAL_WINDOWS_SELFTEST_RESULT.json", summary)
    journal_event(root, "G58_RUN", "RUN_SELFTEST_PASSED", run_id=rid, run_root=str(run_root), sample_count=summary.get("sample_count"))
    return {"status": "PASS", "operation_mode": mode, "selected_run_id": rid,
            "run_root": str(run_root), "summary": summary}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["selftest", "resume"])
    ap.add_argument("--factory-root")
    ap.add_argument("--run-id")
    ap.add_argument("--worker-id", default="LOCAL_WINDOWS")
    args = ap.parse_args()
    root = resolve_factory_root(args.factory_root)
    try:
        out = run_selftest(root, run_id=args.run_id, worker_id=args.worker_id, operation_mode="resume" if args.command == "resume" else "fresh")
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out.get("status") == "PASS" else 2
    except Exception as e:
        print(json.dumps({"status": "FAIL", "error_type": type(e).__name__, "error": str(e)}, indent=2), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
