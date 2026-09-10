from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Dict, Iterable, Optional, Tuple, List

from pcs_factory_paths import resolve_factory_root, write_json_atomic

RUNTIME_SCHEMA = "DF-G50-BLENDER-RUNTIME-LOCK-V1"
RUNTIME_VERSION = "4.5.13"
ARCHIVE_NAME = "blender-4.5.13-windows-x64.zip"
HASH_MANIFEST_NAME = "blender-4.5.13.sha256"
EXPECTED_ARCHIVE_BYTES = 398_648_740
DIRECT_BASE_URL = "https://download.blender.org/release/Blender4.5"
MIRROR_DISCOVERY_BASE_URL = "https://mirror.blender.org/release/Blender4.5"
DIRECT_ARCHIVE_URL = f"{DIRECT_BASE_URL}/{ARCHIVE_NAME}"
DIRECT_HASH_MANIFEST_URL = f"{DIRECT_BASE_URL}/{HASH_MANIFEST_NAME}"
MIRROR_ARCHIVE_DISCOVERY_URL = f"{MIRROR_DISCOVERY_BASE_URL}/{ARCHIVE_NAME}"
MIRROR_HASH_DISCOVERY_URL = f"{MIRROR_DISCOVERY_BASE_URL}/{HASH_MANIFEST_NAME}"
# Compatibility aliases used by inherited diagnostics/tests.
OFFICIAL_BASE_URLS = (DIRECT_BASE_URL, MIRROR_DISCOVERY_BASE_URL)
ARCHIVE_URLS = (DIRECT_ARCHIVE_URL, MIRROR_ARCHIVE_DISCOVERY_URL)
HASH_MANIFEST_URLS = (DIRECT_HASH_MANIFEST_URL, MIRROR_HASH_DISCOVERY_URL)
ARCHIVE_URL = DIRECT_ARCHIVE_URL
HASH_MANIFEST_URL = DIRECT_HASH_MANIFEST_URL
ALLOWED_HOST_SUFFIX = ".blender.org"
ALLOWED_EXACT_HOSTS = {"blender.org", "download.blender.org", "mirror.blender.org"}
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_allowed_host(host: str) -> bool:
    h = (host or "").lower().rstrip(".")
    return h in ALLOWED_EXACT_HOSTS or h.endswith(ALLOWED_HOST_SUFFIX)


def _validate_allowed_url(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url))
    if parsed.scheme.lower() != "https":
        raise urllib.error.URLError(f"BLOCKED_SOURCE_SCHEME:{parsed.scheme}")
    if parsed.username or parsed.password:
        raise urllib.error.URLError("BLOCKED_SOURCE_CREDENTIALS")
    host = parsed.hostname or ""
    if not _is_allowed_host(host):
        raise urllib.error.URLError(f"BLOCKED_SOURCE_HOST:{host}")
    return str(url)


def _validate_mirror_payload_url(url: str, expected_name: str) -> str:
    """Mirror-discovery payloads may leave blender.org, but only over HTTPS and only for the frozen file."""
    parsed = urllib.parse.urlparse(str(url))
    if parsed.scheme.lower() != "https":
        raise urllib.error.URLError(f"BLOCKED_MIRROR_SCHEME:{parsed.scheme}")
    if parsed.username or parsed.password:
        raise urllib.error.URLError("BLOCKED_MIRROR_CREDENTIALS")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise urllib.error.URLError("BLOCKED_MIRROR_EMPTY_HOST")
    pp = PurePosixPath(parsed.path)
    if not pp.name == expected_name:
        raise urllib.error.URLError(f"BLOCKED_MIRROR_FILENAME:{pp.name}")
    if any(part == ".." for part in pp.parts):
        raise urllib.error.URLError("BLOCKED_MIRROR_TRAVERSAL")
    if "Blender4.5" not in pp.parts:
        raise urllib.error.URLError("BLOCKED_MIRROR_SERIES_PATH")
    return str(url)


def _mirror_host(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return (parsed.hostname or "").lower().rstrip(".")


def _mirror_dir_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = str(PurePosixPath(parsed.path).parent) + "/"
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


class BlenderRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_allowed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class MirrorDiscoveryRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, expected_name: str):
        super().__init__()
        self.expected_name = expected_name

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_mirror_payload_url(newurl, self.expected_name)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class AcceptedMirrorRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, expected_name: str, allowed_hosts: Iterable[str]):
        super().__init__()
        self.expected_name = expected_name
        self.allowed_hosts = {str(h).lower().rstrip(".") for h in allowed_hosts}

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_mirror_payload_url(newurl, self.expected_name)
        host = _mirror_host(newurl)
        if host not in self.allowed_hosts:
            raise urllib.error.URLError(f"BLOCKED_UNACCEPTED_MIRROR_HOST:{host}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _ssl_context():
    return ssl.create_default_context()


def _urlopen(req: urllib.request.Request, timeout: float = 60.0):
    opener = urllib.request.build_opener(BlenderRedirectHandler(), urllib.request.HTTPSHandler(context=_ssl_context()))
    _validate_allowed_url(req.full_url)
    return opener.open(req, timeout=timeout)


def _urlopen_mirror_discovery(req: urllib.request.Request, expected_name: str, timeout: float = 60.0):
    _validate_allowed_url(req.full_url)
    if _mirror_host(req.full_url) != "mirror.blender.org":
        raise urllib.error.URLError("MIRROR_DISCOVERY_ORIGIN_REQUIRED")
    opener = urllib.request.build_opener(MirrorDiscoveryRedirectHandler(expected_name),
                                         urllib.request.HTTPSHandler(context=_ssl_context()))
    return opener.open(req, timeout=timeout)


def _urlopen_accepted_mirror(req: urllib.request.Request, expected_name: str, allowed_hosts: Iterable[str],
                             timeout: float = 90.0):
    _validate_mirror_payload_url(req.full_url, expected_name)
    host = _mirror_host(req.full_url)
    allowed = {str(h).lower().rstrip(".") for h in allowed_hosts}
    if host not in allowed:
        raise urllib.error.URLError(f"BLOCKED_UNACCEPTED_MIRROR_HOST:{host}")
    opener = urllib.request.build_opener(AcceptedMirrorRedirectHandler(expected_name, allowed),
                                         urllib.request.HTTPSHandler(context=_ssl_context()))
    return opener.open(req, timeout=timeout)


def _request_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    out = dict(BROWSER_HEADERS)
    if extra:
        out.update(extra)
    return out


def download_small(url: str, dst: Path, max_bytes: int = 2 * 1024 * 1024) -> Dict:
    url = _validate_allowed_url(url)
    dst = Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=_request_headers())
    with _urlopen(req) as r:
        final_url = getattr(r, "geturl", lambda: url)()
        _validate_allowed_url(final_url)
        data = r.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise RuntimeError("SMALL_DOWNLOAD_EXCEEDS_BOUND")
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    tmp.write_bytes(data); os.replace(tmp, dst)
    return {"bytes": len(data), "sha256": sha256_file(dst), "url": url, "final_url": final_url, "client": "urllib"}


def download_small_mirror_probe(url: str, dst: Path, max_bytes: int = 2 * 1024 * 1024) -> Dict:
    """Retrieve checksum bytes through the official mirror discovery origin; external HTTPS final hosts are recorded."""
    url = _validate_allowed_url(url)
    if _mirror_host(url) != "mirror.blender.org":
        raise urllib.error.URLError("MIRROR_DISCOVERY_ORIGIN_REQUIRED")
    dst = Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=_request_headers({"Pragma": "no-cache"}))
    with _urlopen_mirror_discovery(req, HASH_MANIFEST_NAME) as r:
        final_url = getattr(r, "geturl", lambda: url)()
        _validate_mirror_payload_url(final_url, HASH_MANIFEST_NAME)
        data = r.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise RuntimeError("SMALL_DOWNLOAD_EXCEEDS_BOUND")
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    tmp.write_bytes(data); os.replace(tmp, dst)
    return {"bytes": len(data), "sha256": sha256_file(dst), "url": url, "final_url": final_url,
            "final_host": _mirror_host(final_url), "client": "urllib_mirror_probe"}


def download_resumable(url: str, dst: Path, expected_bytes: int, retries: int = 4) -> Dict:
    """Strict blender.org resumable urllib downloader."""
    url = _validate_allowed_url(url)
    dst = Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_suffix(dst.suffix + ".part")
    attempt = 0
    while attempt < retries:
        attempt += 1
        current = part.stat().st_size if part.exists() else 0
        if current > expected_bytes:
            part.unlink(); current = 0
        extra = {"Range": f"bytes={current}-"} if current else None
        req = urllib.request.Request(url, headers=_request_headers(extra))
        try:
            with _urlopen(req, timeout=90.0) as r:
                final_url = getattr(r, "geturl", lambda: url)()
                _validate_allowed_url(final_url)
                status = getattr(r, "status", None) or r.getcode()
                if current and status == 200:
                    current = 0; part.unlink(missing_ok=True); mode = "wb"
                elif current and status == 206:
                    mode = "ab"
                elif not current and status in (200, 206):
                    mode = "wb"
                else:
                    raise RuntimeError(f"UNEXPECTED_HTTP_STATUS:{status}")
                with part.open(mode) as f:
                    last_report = 0.0
                    while True:
                        chunk = r.read(4 * 1024 * 1024)
                        if not chunk: break
                        f.write(chunk)
                        if f.tell() > expected_bytes:
                            raise RuntimeError("DOWNLOAD_EXCEEDS_EXPECTED_SIZE")
                        now = time.monotonic()
                        if now - last_report >= 4.0:
                            pct = 100.0 * f.tell() / float(expected_bytes)
                            print(f"[DF-G50] Blender download: {f.tell():,}/{expected_bytes:,} bytes ({pct:.1f}%)", flush=True)
                            last_report = now
            size = part.stat().st_size
            if size == expected_bytes:
                os.replace(part, dst)
                return {"bytes": size, "sha256": sha256_file(dst), "url": url, "final_url": final_url,
                        "attempts": attempt, "client": "urllib"}
            if size > expected_bytes:
                raise RuntimeError("DOWNLOAD_SIZE_EXCEEDS_EXPECTED")
        except Exception:
            if attempt >= retries: raise
            time.sleep(min(8.0, 1.5 ** attempt))
    raise RuntimeError("DOWNLOAD_RETRIES_EXHAUSTED")


def download_resumable_accepted_mirror(url: str, dst: Path, expected_bytes: int,
                                       allowed_hosts: Iterable[str], retries: int = 4) -> Dict:
    """Resumable download from a mirror host admitted only by checksum-consensus discovery."""
    _validate_mirror_payload_url(url, ARCHIVE_NAME)
    host = _mirror_host(url)
    allowed = {str(h).lower().rstrip(".") for h in allowed_hosts}
    if host not in allowed:
        raise urllib.error.URLError(f"BLOCKED_UNACCEPTED_MIRROR_HOST:{host}")
    dst = Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_suffix(dst.suffix + ".part")
    attempt = 0
    while attempt < retries:
        attempt += 1
        current = part.stat().st_size if part.exists() else 0
        if current > expected_bytes:
            part.unlink(); current = 0
        extra = {"Range": f"bytes={current}-"} if current else None
        req = urllib.request.Request(url, headers=_request_headers(extra))
        try:
            with _urlopen_accepted_mirror(req, ARCHIVE_NAME, allowed, timeout=120.0) as r:
                final_url = getattr(r, "geturl", lambda: url)()
                _validate_mirror_payload_url(final_url, ARCHIVE_NAME)
                if _mirror_host(final_url) not in allowed:
                    raise urllib.error.URLError(f"BLOCKED_UNACCEPTED_MIRROR_HOST:{_mirror_host(final_url)}")
                status = getattr(r, "status", None) or r.getcode()
                if current and status == 200:
                    current = 0; part.unlink(missing_ok=True); mode = "wb"
                elif current and status == 206:
                    mode = "ab"
                elif not current and status in (200, 206):
                    mode = "wb"
                else:
                    raise RuntimeError(f"UNEXPECTED_HTTP_STATUS:{status}")
                with part.open(mode) as f:
                    last_report = 0.0
                    while True:
                        chunk = r.read(4 * 1024 * 1024)
                        if not chunk: break
                        f.write(chunk)
                        if f.tell() > expected_bytes:
                            raise RuntimeError("DOWNLOAD_EXCEEDS_EXPECTED_SIZE")
                        now = time.monotonic()
                        if now - last_report >= 4.0:
                            pct = 100.0 * f.tell() / float(expected_bytes)
                            print(f"[DF-G50] Blender mirror download: {f.tell():,}/{expected_bytes:,} bytes ({pct:.1f}%)", flush=True)
                            last_report = now
            size = part.stat().st_size
            if size == expected_bytes:
                os.replace(part, dst)
                return {"bytes": size, "sha256": sha256_file(dst), "url": url, "final_url": final_url,
                        "final_host": _mirror_host(final_url), "attempts": attempt, "client": "urllib_consensus_mirror"}
        except Exception:
            if attempt >= retries: raise
            time.sleep(min(8.0, 1.5 ** attempt))
    raise RuntimeError("MIRROR_DOWNLOAD_RETRIES_EXHAUSTED")


def _curl_exe() -> str:
    cand = shutil.which("curl.exe") or shutil.which("curl")
    if not cand:
        raise RuntimeError("CURL_FALLBACK_NOT_AVAILABLE")
    return cand


def _curl_effective_url_relaxed(stdout: str, original_url: str, expected_name: str) -> str:
    marker = "PCS_EFFECTIVE_URL="
    vals = [line.split(marker, 1)[1].strip() for line in (stdout or "").splitlines() if marker in line]
    final_url = vals[-1] if vals else original_url
    _validate_mirror_payload_url(final_url, expected_name)
    return final_url


def _validate_curl_mirror_headers(header_path: Path, original_url: str, expected_name: str,
                                  accepted_hosts: Optional[Iterable[str]] = None) -> List[str]:
    hp = Path(header_path)
    if not hp.is_file():
        raise RuntimeError("CURL_HEADER_TRACE_MISSING")
    current = original_url
    hosts = []
    allowed = None if accepted_hosts is None else {str(h).lower().rstrip(".") for h in accepted_hosts}
    text = hp.read_text(encoding="iso-8859-1", errors="replace")
    for raw in text.splitlines():
        if raw.lower().startswith("location:"):
            loc = raw.split(":", 1)[1].strip()
            nxt = urllib.parse.urljoin(current, loc)
            _validate_mirror_payload_url(nxt, expected_name)
            host = _mirror_host(nxt)
            if allowed is not None and host not in allowed:
                raise urllib.error.URLError(f"BLOCKED_UNACCEPTED_MIRROR_HOST:{host}")
            hosts.append(host)
            current = nxt
    return hosts


def download_small_mirror_probe_curl(url: str, dst: Path, max_bytes: int = 2 * 1024 * 1024) -> Dict:
    url = _validate_allowed_url(url)
    if _mirror_host(url) != "mirror.blender.org":
        raise urllib.error.URLError("MIRROR_DISCOVERY_ORIGIN_REQUIRED")
    dst = Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".curl.tmp")
    header_trace = dst.with_suffix(dst.suffix + ".curl.headers.tmp")
    tmp.unlink(missing_ok=True); header_trace.unlink(missing_ok=True)
    cmd = [_curl_exe(), "--fail", "--location", "--silent", "--show-error",
           "--retry", "2", "--retry-all-errors", "--connect-timeout", "20", "--max-time", "90",
           "--proto", "=https", "--proto-redir", "=https",
           "--user-agent", BROWSER_HEADERS["User-Agent"], "--header", "Accept: */*",
           "--dump-header", str(header_trace), "--output", str(tmp),
           "--write-out", "PCS_EFFECTIVE_URL=%{url_effective}\\n", url]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if cp.returncode != 0:
        header_trace.unlink(missing_ok=True)
        raise RuntimeError(f"CURL_MIRROR_PROBE_FAILED:rc={cp.returncode}:{cp.stderr[-1000:]}")
    try:
        _validate_curl_mirror_headers(header_trace, url, HASH_MANIFEST_NAME)
        final_url = _curl_effective_url_relaxed(cp.stdout, url, HASH_MANIFEST_NAME)
    except Exception:
        tmp.unlink(missing_ok=True); raise
    finally:
        header_trace.unlink(missing_ok=True)
    if not tmp.is_file():
        raise RuntimeError("CURL_MIRROR_PROBE_MISSING_OUTPUT")
    size = tmp.stat().st_size
    if size > max_bytes:
        tmp.unlink(missing_ok=True); raise RuntimeError("SMALL_DOWNLOAD_EXCEEDS_BOUND")
    os.replace(tmp, dst)
    return {"bytes": size, "sha256": sha256_file(dst), "url": url, "final_url": final_url,
            "final_host": _mirror_host(final_url), "client": "curl_mirror_probe"}


def _attempt_record(client: str, url: str, status: str, error: Optional[Exception] = None,
                    result: Optional[Dict] = None, digest: Optional[str] = None) -> Dict:
    rec = {"client": client, "url": url, "status": status}
    if error is not None:
        rec["error_type"] = type(error).__name__; rec["error"] = str(error)[:2000]
    if result:
        for key in ("bytes", "sha256", "final_url", "final_host", "attempts"):
            if key in result: rec[key] = result[key]
    if digest: rec["parsed_archive_sha256"] = digest
    return rec


def acquire_checksum_authority(dst: Path, direct_fn=None, mirror_probe_fns=None,
                               min_distinct_hosts: int = 2, max_rounds: int = 4) -> Dict:
    """Prefer direct official checksum. On failure require matching manifests from >=2 mirror hosts."""
    direct_fn = direct_fn or download_small
    mirror_probe_fns = mirror_probe_fns or [
        ("urllib_mirror_probe", download_small_mirror_probe),
        ("curl_mirror_probe", download_small_mirror_probe_curl),
    ]
    dst = Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    attempts = []
    try:
        direct_tmp = dst.with_suffix(dst.suffix + ".direct.tmp")
        direct_tmp.unlink(missing_ok=True)
        res = direct_fn(DIRECT_HASH_MANIFEST_URL, direct_tmp, max_bytes=64 * 1024)
        digest = parse_official_sha256_manifest(direct_tmp)
        os.replace(direct_tmp, dst)
        attempts.append(_attempt_record("direct_official", DIRECT_HASH_MANIFEST_URL, "PASS", result=res, digest=digest))
        return {"mode": "DIRECT_OFFICIAL", "archive_sha256": digest, "manifest_path": str(dst),
                "manifest_sha256": sha256_file(dst), "manifest_bytes": dst.stat().st_size,
                "accepted_mirrors": [], "attempts_log": attempts,
                "final_url": res.get("final_url") or res.get("url")}
    except Exception as e:
        attempts.append(_attempt_record("direct_official", DIRECT_HASH_MANIFEST_URL, "FAIL", error=e))

    observations = {}
    probe_index = 0
    for _round in range(max_rounds):
        for client_name, fn in mirror_probe_fns:
            probe_index += 1
            tmp = dst.with_suffix(dst.suffix + f".mirror{probe_index}.tmp")
            tmp.unlink(missing_ok=True)
            try:
                res = fn(MIRROR_HASH_DISCOVERY_URL, tmp, max_bytes=64 * 1024)
                final_url = res.get("final_url") or ""
                _validate_mirror_payload_url(final_url, HASH_MANIFEST_NAME)
                host = _mirror_host(final_url)
                if host in {"", "mirror.blender.org"}:
                    raise RuntimeError(f"MIRROR_FINAL_HOST_NOT_EXTERNAL:{host}")
                digest = parse_official_sha256_manifest(tmp)
                rec = _attempt_record(client_name, MIRROR_HASH_DISCOVERY_URL, "PASS", result=res, digest=digest)
                attempts.append(rec)
                if host not in observations:
                    observations[host] = {
                        "host": host, "final_url": final_url, "digest": digest,
                        "manifest_sha256": sha256_file(tmp), "manifest_bytes": tmp.stat().st_size,
                        "client": client_name,
                    }
                tmp.unlink(missing_ok=True)
                if len(observations) >= min_distinct_hosts:
                    digests = {v["digest"] for v in observations.values()}
                    if len(digests) != 1:
                        raise RuntimeError("MIRROR_CHECKSUM_CONSENSUS_MISMATCH:" +
                                           json.dumps(sorted((h, v["digest"]) for h,v in observations.items())))
                    digest = next(iter(digests))
                    # Persist a deterministic synthetic authority manifest containing only the agreed frozen entry.
                    dst.write_text(f"{digest}  {ARCHIVE_NAME}\\n", encoding="utf-8")
                    mirrors = [observations[h] for h in sorted(observations)]
                    return {"mode": "MIRROR_CONSENSUS_2PLUS", "archive_sha256": digest,
                            "manifest_path": str(dst), "manifest_sha256": sha256_file(dst),
                            "manifest_bytes": dst.stat().st_size, "accepted_mirrors": mirrors,
                            "attempts_log": attempts, "final_url": None}
            except Exception as e:
                attempts.append(_attempt_record(client_name, MIRROR_HASH_DISCOVERY_URL, "FAIL", error=e))
                tmp.unlink(missing_ok=True)
    raise RuntimeError("MIRROR_CHECKSUM_QUORUM_NOT_REACHED:" + json.dumps(attempts, sort_keys=True))


def _mirror_archive_urls(authority: Dict) -> List[str]:
    urls = []
    for m in authority.get("accepted_mirrors", []):
        final_manifest = m.get("final_url") or ""
        _validate_mirror_payload_url(final_manifest, HASH_MANIFEST_NAME)
        base = _mirror_dir_url(final_manifest)
        url = urllib.parse.urljoin(base, ARCHIVE_NAME)
        _validate_mirror_payload_url(url, ARCHIVE_NAME)
        if _mirror_host(url) != m.get("host"):
            raise RuntimeError("MIRROR_ARCHIVE_HOST_DERIVATION_MISMATCH")
        urls.append(url)
    return urls


def acquire_archive_with_authority(dst: Path, authority: Dict, expected_bytes: int,
                                   direct_fn=None, mirror_fn=None) -> Dict:
    direct_fn = direct_fn or download_resumable
    mirror_fn = mirror_fn or download_resumable_accepted_mirror
    attempts = []
    try:
        res = direct_fn(DIRECT_ARCHIVE_URL, dst, expected_bytes)
        attempts.append(_attempt_record("direct_official", DIRECT_ARCHIVE_URL, "PASS", result=res))
        out = dict(res); out["authority_mode"] = authority.get("mode"); out["attempts_log"] = attempts
        return out
    except Exception as e:
        attempts.append(_attempt_record("direct_official", DIRECT_ARCHIVE_URL, "FAIL", error=e))

    mirrors = authority.get("accepted_mirrors", [])
    if len({m.get("host") for m in mirrors}) < 2:
        raise RuntimeError("ARCHIVE_MIRROR_FALLBACK_REQUIRES_CHECKSUM_QUORUM:" + json.dumps(attempts, sort_keys=True))
    allowed_hosts = {m["host"] for m in mirrors}
    for url in _mirror_archive_urls(authority):
        try:
            res = mirror_fn(url, dst, expected_bytes, allowed_hosts)
            attempts.append(_attempt_record("consensus_mirror", url, "PASS", result=res))
            out = dict(res); out["authority_mode"] = authority.get("mode"); out["attempts_log"] = attempts
            return out
        except Exception as e:
            attempts.append(_attempt_record("consensus_mirror", url, "FAIL", error=e))
    raise RuntimeError("ARCHIVE_ACQUISITION_FAILED_AFTER_CONSENSUS:" + json.dumps(attempts, sort_keys=True))


def parse_official_sha256_manifest(path: Path, archive_name: str = ARCHIVE_NAME) -> str:
    text = Path(path).read_text(encoding="utf-8", errors="strict")
    matches = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if not m:
            continue
        digest, name = m.group(1).lower(), m.group(2).strip()
        if name == archive_name:
            matches.append(digest)
    if len(matches) != 1:
        raise RuntimeError(f"OFFICIAL_SHA256_ENTRY_COUNT:{len(matches)}")
    return matches[0]


def validate_archive(archive: Path, manifest: Path) -> Dict:
    archive = Path(archive)
    manifest = Path(manifest)
    if archive.name != ARCHIVE_NAME:
        raise RuntimeError(f"ARCHIVE_NAME_MISMATCH:{archive.name}")
    size = archive.stat().st_size
    if size != EXPECTED_ARCHIVE_BYTES:
        raise RuntimeError(f"ARCHIVE_SIZE_MISMATCH:{size}")
    expected_sha = parse_official_sha256_manifest(manifest)
    observed_sha = sha256_file(archive)
    if observed_sha != expected_sha:
        raise RuntimeError("ARCHIVE_SHA256_MISMATCH")
    return {
        "archive_name": archive.name,
        "archive_bytes": size,
        "archive_sha256": observed_sha,
        "official_manifest_name": manifest.name,
        "official_manifest_bytes": manifest.stat().st_size,
        "official_manifest_sha256": sha256_file(manifest),
    }


def _zip_member_is_unsafe(info: zipfile.ZipInfo) -> bool:
    name = info.filename.replace("\\", "/")
    pp = PurePosixPath(name)
    wp = PureWindowsPath(name)
    if not name or name.startswith("/") or name.startswith("\\"):
        return True
    if pp.is_absolute() or wp.is_absolute() or wp.drive:
        return True
    if any(part in ("..", "") for part in pp.parts):
        return True
    # Reject Unix symlink entries encoded in external attrs.
    mode = (info.external_attr >> 16) & 0xFFFF
    if (mode & 0o170000) == 0o120000:
        return True
    return False


def safe_extract_blender(archive: Path, destination: Path) -> Dict:
    archive = Path(archive)
    destination = Path(destination)
    staging = destination.with_name(destination.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(archive, "r") as zf:
            infos = zf.infolist()
            if not infos:
                raise RuntimeError("EMPTY_BLENDER_ARCHIVE")
            for info in infos:
                if _zip_member_is_unsafe(info):
                    raise RuntimeError(f"UNSAFE_ZIP_MEMBER:{info.filename}")
            tops = {PurePosixPath(i.filename.replace("\\", "/")).parts[0] for i in infos if i.filename}
            expected_top = "blender-4.5.13-windows-x64"
            if tops != {expected_top}:
                raise RuntimeError(f"UNEXPECTED_TOP_LEVEL:{sorted(tops)}")
            zf.extractall(staging)
        src = staging / "blender-4.5.13-windows-x64"
        blender_exe = src / "blender.exe"
        if not blender_exe.is_file():
            raise RuntimeError("BLENDER_EXE_MISSING_AFTER_EXTRACT")
        if destination.exists():
            shutil.rmtree(destination)
        os.replace(src, destination)
        shutil.rmtree(staging, ignore_errors=True)
        return {"status": "PASS", "runtime_dir": str(destination), "blender_exe": str(destination / "blender.exe")}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def query_blender_identity(blender_exe: Path, timeout: float = 90.0) -> Dict:
    blender_exe = Path(blender_exe)
    expr = (
        "import bpy,json;"
        "print('PCS_BLENDER_IDENTITY_JSON='+json.dumps({"
        "'version_string':bpy.app.version_string,"
        "'version':list(bpy.app.version),"
        "'build_hash':(bpy.app.build_hash.decode('ascii','replace') if isinstance(bpy.app.build_hash,(bytes,bytearray)) else str(bpy.app.build_hash)),"
        "'build_date':(bpy.app.build_date.decode('ascii','replace') if isinstance(bpy.app.build_date,(bytes,bytearray)) else str(bpy.app.build_date)),"
        "'build_time':(bpy.app.build_time.decode('ascii','replace') if isinstance(bpy.app.build_time,(bytes,bytearray)) else str(bpy.app.build_time))"
        "},sort_keys=True))"
    )
    cp = subprocess.run(
        [str(blender_exe), "--background", "--factory-startup", "--python-expr", expr],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )
    marker = "PCS_BLENDER_IDENTITY_JSON="
    payload = None
    for line in cp.stdout.splitlines():
        if marker in line:
            payload = line.split(marker, 1)[1].strip()
    if cp.returncode != 0 or not payload:
        raise RuntimeError(f"BLENDER_IDENTITY_QUERY_FAILED:rc={cp.returncode}")
    obj = json.loads(payload)
    version = obj.get("version")
    if version != [4, 5, 13]:
        raise RuntimeError(f"BLENDER_VERSION_MISMATCH:{version}")
    obj["returncode"] = cp.returncode
    return obj


def runtime_paths(root: Path) -> Dict[str, Path]:
    root = Path(root)
    return {
        "runtime_dir": root / "01_SOURCE" / "DCC" / "BLENDER" / RUNTIME_VERSION / "runtime",
        "lock_path": root / "00_CONTROL" / "LOCKS" / f"BLENDER_{RUNTIME_VERSION.replace('.', '_')}_RUNTIME_LOCK.json",
        "acq_dir": root / "14_RECOVERY" / "BLENDER_ACQUISITION" / RUNTIME_VERSION,
    }




def validate_archive_against_digest(archive: Path, expected_sha256: str) -> Dict:
    archive = Path(archive)
    if archive.name != ARCHIVE_NAME:
        raise RuntimeError(f"ARCHIVE_NAME_MISMATCH:{archive.name}")
    size = archive.stat().st_size
    if size != EXPECTED_ARCHIVE_BYTES:
        raise RuntimeError(f"ARCHIVE_SIZE_MISMATCH:{size}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_sha256).lower()):
        raise RuntimeError("EXPECTED_SHA256_INVALID")
    observed_sha = sha256_file(archive)
    if observed_sha != str(expected_sha256).lower():
        raise RuntimeError("ARCHIVE_SHA256_MISMATCH")
    return {"archive_name": archive.name, "archive_bytes": size, "archive_sha256": observed_sha}


def acquire_or_verify_runtime(root: Path, archive_path: Optional[Path] = None, manifest_path: Optional[Path] = None,
                              keep_archive: bool = False, allow_download: bool = True) -> Dict:
    root = Path(root)
    paths = runtime_paths(root)
    paths["acq_dir"].mkdir(parents=True, exist_ok=True)
    runtime_dir = paths["runtime_dir"]
    lock_path = paths["lock_path"]

    if lock_path.exists() and (runtime_dir / "blender.exe").is_file():
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        ident = query_blender_identity(runtime_dir / "blender.exe")
        if lock.get("schema") != RUNTIME_SCHEMA or lock.get("archive_sha256") is None:
            raise RuntimeError("INVALID_EXISTING_BLENDER_RUNTIME_LOCK")
        if ident.get("build_hash") != lock.get("blender_identity", {}).get("build_hash"):
            raise RuntimeError("BLENDER_BUILD_HASH_CHANGED")
        return {"status": "PASS_EXISTING_LOCK_VERIFIED", "lock": lock, "lock_path": str(lock_path)}

    if runtime_dir.exists() or lock_path.exists():
        raise RuntimeError("UNMANAGED_OR_PARTIAL_BLENDER_RUNTIME_STATE")

    print("[DF-G50] Runtime not present. Verifying Blender 4.5.13 acquisition authority...", flush=True)
    local_manifest = Path(manifest_path) if manifest_path else paths["acq_dir"] / HASH_MANIFEST_NAME
    if manifest_path is not None:
        official_sha = parse_official_sha256_manifest(local_manifest)
        checksum_authority = {
            "mode": "PROVIDED_LOCAL_MANIFEST",
            "archive_sha256": official_sha,
            "manifest_path": str(local_manifest),
            "manifest_sha256": sha256_file(local_manifest),
            "manifest_bytes": local_manifest.stat().st_size,
            "accepted_mirrors": [], "attempts_log": [], "final_url": None,
        }
    else:
        if not allow_download:
            raise RuntimeError("SHA256_AUTHORITY_REQUIRED_OFFLINE")
        print("[DF-G50] Acquiring checksum authority: direct official first, 2+ mirror consensus fallback...", flush=True)
        checksum_authority = acquire_checksum_authority(local_manifest)
        official_sha = checksum_authority["archive_sha256"]
        print(f"[DF-G50] Checksum authority PASS: {checksum_authority.get('mode')} sha256={official_sha}", flush=True)

    local_archive = Path(archive_path) if archive_path else paths["acq_dir"] / ARCHIVE_NAME
    archive_acq = {"client": "provided_local_file", "url": None, "attempts_log": []}
    if archive_path is None:
        if not allow_download:
            raise RuntimeError("BLENDER_ARCHIVE_REQUIRED_OFFLINE")
        archive_acq = acquire_archive_with_authority(local_archive, checksum_authority, EXPECTED_ARCHIVE_BYTES)
        print(f"[DF-G50] Blender archive acquired via {archive_acq.get('client')} from {archive_acq.get('final_url') or archive_acq.get('url')}", flush=True)

    print("[DF-G50] Verifying Blender archive size + authority SHA-256...", flush=True)
    valid = validate_archive_against_digest(local_archive, official_sha)
    print("[DF-G50] Archive verified. Extracting portable runtime...", flush=True)
    extract = safe_extract_blender(local_archive, runtime_dir)
    ident = query_blender_identity(runtime_dir / "blender.exe")
    print(f"[DF-G50] Blender identity PASS: {ident.get('version_string')} build {ident.get('build_hash')}", flush=True)

    lock = {
        "schema": RUNTIME_SCHEMA,
        "status": "PASS_PINNED_VERIFIED_RUNTIME",
        "version": RUNTIME_VERSION,
        "platform": "windows-x64",
        "archive_url": archive_acq.get("final_url") or archive_acq.get("url") or DIRECT_ARCHIVE_URL,
        "hash_manifest_url": checksum_authority.get("final_url"),
        "checksum_authority": checksum_authority,
        "archive_acquisition": archive_acq,
        "authorized_origin_candidates": [DIRECT_BASE_URL, MIRROR_DISCOVERY_BASE_URL],
        "acquisition_portability_revision": "R3",
        "archive_name": ARCHIVE_NAME,
        "archive_bytes": valid["archive_bytes"],
        "archive_sha256": valid["archive_sha256"],
        "official_manifest_name": HASH_MANIFEST_NAME,
        "official_manifest_bytes": checksum_authority.get("manifest_bytes"),
        "official_manifest_sha256": checksum_authority.get("manifest_sha256"),
        "runtime_relative_path": str(runtime_dir.relative_to(root)).replace("\\", "/"),
        "blender_identity": ident,
        "launch_contract": ["--background", "--factory-startup"],
        "required_addons": [],
        "system_install": False,
        "path_mutation": False,
    }
    write_json_atomic(lock_path, lock)
    if not keep_archive and archive_path is None:
        local_archive.unlink(missing_ok=True)
    return {"status": "PASS_NEW_RUNTIME_ACQUIRED", "lock": lock, "lock_path": str(lock_path), "extract": extract}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["acquire", "status"])
    ap.add_argument("--factory-root")
    ap.add_argument("--archive")
    ap.add_argument("--manifest")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--keep-archive", action="store_true")
    args = ap.parse_args()
    root = resolve_factory_root(args.factory_root)
    try:
        if args.command == "acquire":
            out = acquire_or_verify_runtime(
                root,
                Path(args.archive) if args.archive else None,
                Path(args.manifest) if args.manifest else None,
                keep_archive=args.keep_archive,
                allow_download=not args.offline,
            )
        else:
            p = runtime_paths(root)
            if not p["lock_path"].exists() or not (p["runtime_dir"] / "blender.exe").is_file():
                raise RuntimeError("BLENDER_RUNTIME_NOT_ACQUIRED")
            lock = json.loads(p["lock_path"].read_text(encoding="utf-8"))
            ident = query_blender_identity(p["runtime_dir"] / "blender.exe")
            out = {"status": "PASS", "lock": lock, "identity": ident}
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    except Exception as e:
        print(json.dumps({"status": "FAIL", "error_type": type(e).__name__, "error": str(e)}, indent=2), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
