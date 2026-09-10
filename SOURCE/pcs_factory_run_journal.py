from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from pcs_factory_paths import write_json_atomic

JOURNAL_SCHEMA = "DF-G50-G58-RUN-JOURNAL-V1"
JOURNAL_NAME = "DF_G50_G58_RUN_JOURNAL.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def journal_path(root: Path) -> Path:
    return Path(root) / "11_PACKAGES" / "RETURNS" / JOURNAL_NAME


def _read_existing(root: Path) -> Dict[str, Any]:
    path = journal_path(root)
    if not path.is_file():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        # A corrupt/partial prior journal must not prevent a new atomic journal from being written.
        return {}


def start_journal(root: Path, release_id: str, operation_mode: str) -> Dict[str, Any]:
    now = utc_now()
    obj: Dict[str, Any] = {
        "schema": JOURNAL_SCHEMA,
        "status": "RUNNING",
        "release_id": release_id,
        "operation_mode": operation_mode,
        "resolved_root": str(Path(root)),
        "started_utc": now,
        "updated_utc": now,
        "last_phase": "PROCESS_ENTRY",
        "last_event": "JOURNAL_STARTED",
        "run_id": None,
        "sample_id": None,
        "attempt": None,
        "worker_pid": None,
        "events": [],
        "product_mutated": False,
        "maya_mutated": False,
        "training_started": False,
        "test77_accessed": False,
    }
    obj["events"].append({"timestamp_utc": now, "phase": "PROCESS_ENTRY", "event": "JOURNAL_STARTED"})
    path = journal_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, obj)
    return obj


def journal_event(root: Path, phase: str, event: str, **fields: Any) -> Dict[str, Any]:
    obj = _read_existing(root)
    if obj.get("schema") != JOURNAL_SCHEMA:
        # This should normally be initialized by start_journal; fail-safe creation retains evidence.
        obj = start_journal(root, str(fields.get("release_id", "UNKNOWN")), str(fields.get("operation_mode", "UNKNOWN")))
    now = utc_now()
    obj["updated_utc"] = now
    obj["last_phase"] = phase
    obj["last_event"] = event
    for k, v in fields.items():
        if k not in {"release_id", "operation_mode"} or v is not None:
            obj[k] = v
    ev = {"timestamp_utc": now, "phase": phase, "event": event}
    ev.update({k: v for k, v in fields.items() if v is not None})
    events = list(obj.get("events") or [])
    events.append(ev)
    # The self-test pack is tiny; bound anyway so a pathological retry cannot grow forever.
    obj["events"] = events[-256:]
    write_json_atomic(journal_path(root), obj)
    return obj


def journal_finish(root: Path, status: str, phase: str = "PROCESS_EXIT", event: str = "PROCESS_FINISHED", **fields: Any) -> Dict[str, Any]:
    obj = journal_event(root, phase, event, **fields)
    obj["status"] = status
    obj["updated_utc"] = utc_now()
    write_json_atomic(journal_path(root), obj)
    return obj
