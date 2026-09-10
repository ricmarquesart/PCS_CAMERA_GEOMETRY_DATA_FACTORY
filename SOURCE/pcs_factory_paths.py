from __future__ import annotations

import json
import os
import tempfile
import time
import errno
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_FACTORY_ROOT = Path(r"C:\PCS_LABS\CAMERA_GEOMETRY_DATA_FACTORY")
ENV_FACTORY_ROOT = "PCS_CAMERA_FACTORY_ROOT"
CONTROL_DIR = "00_CONTROL"
ROOT_SCHEMA = "PCS_CAMERA_GEOMETRY_DATA_FACTORY_ROOT_V1"
SCHEMA_VERSION_SCHEMA = "PCS_CAMERA_GEOMETRY_DATA_FACTORY_SCHEMA_VERSION_V1"
ACTIVE_COMPONENTS_SCHEMA = "PCS_CAMERA_GEOMETRY_DATA_FACTORY_ACTIVE_COMPONENTS_V1"
LATEST_ACCEPTED_SCHEMA = "PCS_CAMERA_GEOMETRY_DATA_FACTORY_LATEST_ACCEPTED_V1"


def resolve_factory_root(cli_root: Optional[str] = None) -> Path:
    """Resolve factory root by frozen precedence: CLI > env > default."""
    if cli_root:
        return Path(cli_root).expanduser()
    env = os.environ.get(ENV_FACTORY_ROOT, "").strip()
    if env:
        return Path(env).expanduser()
    return DEFAULT_FACTORY_ROOT


def control_path(root: Path, filename: str) -> Path:
    return Path(root) / CONTROL_DIR / filename


def load_json(path: Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"JSON object required: {path}")
    return obj


_WINDOWS_ATOMIC_REPLACE_RETRY_DELAYS = (0.05, 0.10, 0.20, 0.40, 0.80, 1.60, 2.00, 2.00)
_WINDOWS_ATOMIC_REPLACE_RETRY_WINERRORS = {5, 32}


def _retryable_windows_replace_error(exc: BaseException) -> bool:
    if not isinstance(exc, PermissionError):
        return False
    winerror = getattr(exc, "winerror", None)
    if winerror is not None:
        return int(winerror) in _WINDOWS_ATOMIC_REPLACE_RETRY_WINERRORS
    return os.name == "nt" and getattr(exc, "errno", None) in {errno.EACCES, errno.EPERM}


def _replace_atomic_with_bounded_retry(tmp_name: str, path: Path) -> None:
    for attempt in range(len(_WINDOWS_ATOMIC_REPLACE_RETRY_DELAYS) + 1):
        try:
            os.replace(tmp_name, path)
            return
        except PermissionError as exc:
            if not _retryable_windows_replace_error(exc) or attempt >= len(_WINDOWS_ATOMIC_REPLACE_RETRY_DELAYS):
                raise
            if not os.path.exists(tmp_name):
                raise
            time.sleep(_WINDOWS_ATOMIC_REPLACE_RETRY_DELAYS[attempt])


def write_json_atomic(path: Path, obj: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        _replace_atomic_with_bounded_retry(tmp_name, path)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        except OSError:
            pass


def relative_path(root: Path, path: Path) -> str:
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def validate_control_schema(root: Path) -> Dict[str, Dict[str, Any]]:
    expected = {
        "FACTORY_ROOT.json": ROOT_SCHEMA,
        "SCHEMA_VERSION.json": SCHEMA_VERSION_SCHEMA,
        "ACTIVE_COMPONENTS.json": ACTIVE_COMPONENTS_SCHEMA,
        "LATEST_ACCEPTED.json": LATEST_ACCEPTED_SCHEMA,
    }
    out: Dict[str, Dict[str, Any]] = {}
    for name, schema in expected.items():
        p = control_path(root, name)
        obj = load_json(p)
        if obj.get("schema") != schema:
            raise ValueError(f"schema mismatch for {name}: {obj.get('schema')} != {schema}")
        out[name] = obj
    return out
