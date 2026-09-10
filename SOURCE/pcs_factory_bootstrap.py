from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from pcs_factory_paths import (
    ACTIVE_COMPONENTS_SCHEMA,
    ENV_FACTORY_ROOT,
    LATEST_ACCEPTED_SCHEMA,
    ROOT_SCHEMA,
    SCHEMA_VERSION_SCHEMA,
    control_path,
    load_json,
    resolve_factory_root,
    validate_control_schema,
    write_json_atomic,
)

ROOT_CONTRACT_VERSION = "DF-G00-V1"
FACTORY_BRANCH = "PCS_CAMERA_GEOMETRY_DATA_FACTORY"
DEFAULT_ROOT_TEXT = r"C:\PCS_LABS\CAMERA_GEOMETRY_DATA_FACTORY"

REQUIRED_DIRS: List[str] = [
    "00_CONTROL/LOCKS",
    "01_SOURCE/RELEASES",
    "01_SOURCE/WIP",
    "02_ASSETS/INBOX",
    "02_ASSETS/QUALIFIED",
    "02_ASSETS/LICENSES",
    "02_ASSETS/MANIFESTS",
    "03_SCENES/RECIPES",
    "03_SCENES/BASE_SCENES",
    "03_SCENES/QUALIFIED",
    "04_CAMERA_SPECS/RECIPES",
    "04_CAMERA_SPECS/CALIBRATION",
    "04_CAMERA_SPECS/ORACLES",
    "05_GENERATOR/CONFIG",
    "05_GENERATOR/PROFILES",
    "05_GENERATOR/PRESETS",
    "06_RENDER_QUEUE/PENDING",
    "06_RENDER_QUEUE/RUNNING",
    "06_RENDER_QUEUE/COMPLETE",
    "06_RENDER_QUEUE/FAILED",
    "07_OUTPUT/RUNS",
    "07_OUTPUT/CHUNKS",
    "07_OUTPUT/IMAGES",
    "07_OUTPUT/GROUND_TRUTH",
    "07_OUTPUT/MANIFESTS",
    "07_OUTPUT/REPORTS",
    "07_OUTPUT/PREVIEWS",
    "08_DATASETS/MICRO_100",
    "08_DATASETS/ENGINEERING_1K",
    "08_DATASETS/PILOT_10K",
    "08_DATASETS/SCALE_100K",
    "08_DATASETS/SCALE_200K_PLUS",
    "08_DATASETS/PROTECTED_HOLDOUTS",
    "09_QA/REPORTS",
    "09_QA/QUARANTINE",
    "09_QA/DUPLICATES",
    "09_QA/LEAKAGE",
    "10_VISUAL_CHECKPOINTS",
    "11_PACKAGES/INSTALLED",
    "11_PACKAGES/RETURNS",
    "12_CACHE",
    "13_LOGS",
    "14_RECOVERY",
    "15_EXPORT",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_default_root(root: Path) -> bool:
    s = str(root).replace("/", "\\").rstrip("\\").lower()
    prod = r"c:\pcs"
    return not (s == prod or s.startswith(prod + "\\"))


def _initialize_if_missing(path: Path, obj: Dict) -> str:
    if path.exists():
        load_json(path)  # parse check; never silently overwrite existing control authority
        return "EXISTS"
    write_json_atomic(path, obj)
    return "CREATED"


def bootstrap(root: Path) -> Dict:
    root = Path(root)
    if not _safe_default_root(root):
        raise RuntimeError(f"FACTORY_PRODUCT_ISOLATION_VIOLATION: refusing root inside C:\\PCS: {root}")

    root.mkdir(parents=True, exist_ok=True)
    created_dirs = []
    for rel in REQUIRED_DIRS:
        p = root / Path(rel)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created_dirs.append(rel)

    now = utc_now()
    controls = {}
    controls["FACTORY_ROOT.json"] = _initialize_if_missing(
        control_path(root, "FACTORY_ROOT.json"),
        {
            "schema": ROOT_SCHEMA,
            "contract_version": ROOT_CONTRACT_VERSION,
            "branch": FACTORY_BRANCH,
            "canonical_default_root": DEFAULT_ROOT_TEXT,
            "resolved_root_runtime_diagnostic": str(root),
            "resolution_precedence": ["--factory-root", ENV_FACTORY_ROOT, DEFAULT_ROOT_TEXT],
            "persistent_metadata_paths": "RELATIVE_TO_FACTORY_ROOT_WHERE_POSSIBLE",
            "product_runtime_mutated": False,
            "created_at_utc": now,
        },
    )
    controls["SCHEMA_VERSION.json"] = _initialize_if_missing(
        control_path(root, "SCHEMA_VERSION.json"),
        {
            "schema": SCHEMA_VERSION_SCHEMA,
            "factory_root_contract": ROOT_CONTRACT_VERSION,
            "sample_schema": None,
            "seed_hierarchy": None,
            "camera_oracle_schema": None,
            "generator_schema": None,
            "renderer_schema": None,
            "qa_schema": None,
            "created_at_utc": now,
        },
    )
    controls["ACTIVE_COMPONENTS.json"] = _initialize_if_missing(
        control_path(root, "ACTIVE_COMPONENTS.json"),
        {
            "schema": ACTIVE_COMPONENTS_SCHEMA,
            "components": {},
            "authority_rule": "EXPLICIT_PROMOTION_ONLY",
            "created_at_utc": now,
        },
    )
    controls["LATEST_ACCEPTED.json"] = _initialize_if_missing(
        control_path(root, "LATEST_ACCEPTED.json"),
        {
            "schema": LATEST_ACCEPTED_SCHEMA,
            "artifacts": {},
            "accepted_run_id": None,
            "accepted_dataset_id": None,
            "authority_rule": "PROMOTED_NOT_MTIME",
            "created_at_utc": now,
        },
    )

    validated = validate_control_schema(root)
    usage = shutil.disk_usage(root)
    return {
        "schema": "PCS_CAMERA_GEOMETRY_DATA_FACTORY_DF_G00_BOOTSTRAP_RESULT_V1",
        "status": "PASS",
        "resolved_root": str(root),
        "root_contract_version": ROOT_CONTRACT_VERSION,
        "required_directory_count": len(REQUIRED_DIRS),
        "created_directory_count": len(created_dirs),
        "created_directories": created_dirs,
        "control_file_actions": controls,
        "control_file_count": len(validated),
        "active_component_count": len(validated["ACTIVE_COMPONENTS.json"].get("components", {})),
        "latest_accepted_artifact_count": len(validated["LATEST_ACCEPTED.json"].get("artifacts", {})),
        "accepted_run_id": validated["LATEST_ACCEPTED.json"].get("accepted_run_id"),
        "disk_free_bytes": usage.free,
        "disk_total_bytes": usage.total,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "product_runtime_mutated": False,
        "maya_mutated": False,
        "training_started": False,
        "image_generation_started": False,
        "timestamp_utc": utc_now(),
    }


def status(root: Path) -> Dict:
    root = Path(root)
    missing = [rel for rel in REQUIRED_DIRS if not (root / rel).is_dir()]
    controls = validate_control_schema(root)
    usage = shutil.disk_usage(root)
    return {
        "schema": "PCS_CAMERA_GEOMETRY_DATA_FACTORY_DF_G00_STATUS_V1",
        "status": "PASS" if not missing else "FAIL",
        "resolved_root": str(root),
        "missing_directories": missing,
        "expected_directory_count": len(REQUIRED_DIRS),
        "active_component_count": len(controls["ACTIVE_COMPONENTS.json"].get("components", {})),
        "latest_accepted_artifact_count": len(controls["LATEST_ACCEPTED.json"].get("artifacts", {})),
        "accepted_run_id": controls["LATEST_ACCEPTED.json"].get("accepted_run_id"),
        "disk_free_bytes": usage.free,
        "product_runtime_mutated": False,
        "timestamp_utc": utc_now(),
    }


def write_report(root: Path, name: str, obj: Dict) -> Path:
    p = Path(root) / "07_OUTPUT" / "REPORTS" / name
    write_json_atomic(p, obj)
    return p


def print_tree_status(obj: Dict) -> None:
    print("=" * 68)
    print("PCS CAMERA GEOMETRY DATA FACTORY — DF-G00")
    print("=" * 68)
    print(f"Status                 : {obj.get('status')}")
    print(f"Resolved root          : {obj.get('resolved_root')}")
    print(f"Expected directories   : {obj.get('expected_directory_count', obj.get('required_directory_count'))}")
    print(f"Missing directories    : {len(obj.get('missing_directories', []))}")
    print(f"Active components      : {obj.get('active_component_count')}")
    print(f"Latest accepted items  : {obj.get('latest_accepted_artifact_count')}")
    print(f"Accepted run           : {obj.get('accepted_run_id')}")
    free = obj.get('disk_free_bytes')
    if isinstance(free, int):
        print(f"Disk free              : {free / (1024**3):.2f} GiB")
    print("C:\\PCS mutation        : NO")
    print("Image generation       : NOT STARTED")
    print("Training               : NOT STARTED")
    print("=" * 68)


def main() -> int:
    ap = argparse.ArgumentParser(description="PCS Camera Geometry Data Factory DF-G00 bootstrap/status")
    ap.add_argument("command", choices=["bootstrap", "status"])
    ap.add_argument("--factory-root", default=None)
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = ap.parse_args()
    root = resolve_factory_root(args.factory_root)
    try:
        if args.command == "bootstrap":
            obj = bootstrap(root)
            write_report(root, "DF_G00_BOOTSTRAP_RESULT.json", obj)
        else:
            obj = status(root)
            write_report(root, "DF_G00_STATUS_RESULT.json", obj)
        if args.json:
            print(json.dumps(obj, indent=2, sort_keys=True))
        else:
            print_tree_status(obj)
        return 0 if obj.get("status") == "PASS" else 2
    except Exception as e:
        print(f"DF-G00 FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
