from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pcs_factory_paths import write_json_atomic
from pcs_factory_blender_protocol import resolve_scene_family

GALLERY_SCHEMA = "DF-G58-BLENDER-VISUAL-CHECKPOINT-V1"


def _esc(x: Any) -> str:
    return html.escape(str(x), quote=True)


def _svg_overlay(completion: Dict[str, Any], width: int, height: int) -> str:
    truth = completion.get("truth_overlay", {}) if isinstance(completion, dict) else {}
    elems: List[str] = []
    horizon = truth.get("horizon_line_abc")
    if isinstance(horizon, list) and len(horizon) == 3:
        a, b, c = map(float, horizon)
        pts = []
        if abs(b) > 1e-12:
            for x in (0.0, float(width - 1)):
                y = -(a * x + c) / b
                if -2 * height <= y <= 3 * height:
                    pts.append((x, y))
        if len(pts) < 2 and abs(a) > 1e-12:
            pts = []
            for y in (0.0, float(height - 1)):
                x = -(b * y + c) / a
                if -2 * width <= x <= 3 * width:
                    pts.append((x, y))
        if len(pts) >= 2:
            (x1, y1), (x2, y2) = pts[:2]
            elems.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="cyan" stroke-width="2"/>')
    vp_colors = {"X": "#ff4b4b", "Y": "#4bd96a", "Z": "#4b86ff"}
    for axis, rec in sorted((truth.get("vps") or {}).items()):
        pix = rec.get("pixel") if isinstance(rec, dict) else None
        if not (isinstance(pix, list) and len(pix) == 2):
            continue
        x, y = map(float, pix)
        color = vp_colors.get(axis, "yellow")
        if -50 <= x <= width + 50 and -50 <= y <= height + 50:
            elems.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="6" fill="none" stroke="{color}" stroke-width="3"/>')
            elems.append(f'<text x="{x+8:.3f}" y="{y-8:.3f}" fill="{color}" font-size="16" font-weight="bold">{_esc(axis)}</text>')
    for rec in truth.get("landmarks", [])[:16]:
        pix = rec.get("pixel") if isinstance(rec, dict) else None
        if isinstance(pix, list) and len(pix) == 2:
            x, y = map(float, pix)
            elems.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="2.8" fill="yellow" stroke="black" stroke-width="0.8"/>')
    return f'<svg class="overlay" viewBox="0 0 {width} {height}" preserveAspectRatio="none">{"".join(elems)}</svg>'


def write_template(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = """<!doctype html><meta charset='utf-8'><title>DF-G50..G58 Blender Self-Test</title>
<style>body{font-family:system-ui;margin:2rem;background:#111;color:#eee}.warn{padding:1rem;border:2px solid #f5b942;background:#251d08}code{color:#b9dcff}</style>
<h1>DF-G50..G58 Blender Headless Render Factory</h1>
<div class='warn'><b>NOT_RENDERED_YET / PRE-REAL TEMPLATE</b><br>This file is a pre-real visual checkpoint shell only. It is not evidence that Blender, Eevee, Cycles, materials, assets or auxiliary passes have executed.</div>
<p>Real qualification must replace this shell with the run-specific gallery produced from verified completion manifests and real RGB outputs.</p>
"""
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def generate_real_gallery(run_root: Path, chunk: Dict[str, Any], out_path: Path) -> Path:
    run_root = Path(run_root)
    if not chunk.get("requests"):
        raise RuntimeError("EMPTY_GALLERY_CHUNK")
    cards = []
    for req in chunk["requests"]:
        sdir = run_root / req["output_rel"]
        cpath = sdir / "completion.json"
        rgb = sdir / "rgb.png"
        if not cpath.is_file() or not rgb.is_file():
            raise RuntimeError(f"REAL_GALLERY_MISSING_COMPLETION:{req['sample_id']}")
        c = json.loads(cpath.read_text(encoding="utf-8"))
        if c.get("status") != "PASS_REAL_BLENDER_RENDERED" or c.get("real_blender_rendered") is not True:
            raise RuntimeError(f"FALSE_REAL_GALLERY_GUARD:{req['sample_id']}")
        width = int(req["camera"]["width"]); height = int(req["camera"]["height"])
        img_rel = rgb.relative_to(out_path.parent).as_posix()
        overlay = _svg_overlay(c, width, height)
        repro = c.get("camera_reprojection", {})
        cards.append(f"""
<section class='card'><h2>{_esc(req['sample_id'])}</h2>
<div class='imagewrap' style='aspect-ratio:{width}/{height}'><img src='{_esc(img_rel)}' alt='{_esc(req['sample_id'])}'>{overlay}</div>
<table>
<tr><th>Scene</th><td>{_esc(resolve_scene_family(req['scene']))}</td><th>Camera</th><td>{_esc(req['camera']['profile'])}</td></tr>
<tr><th>Appearance</th><td>{_esc(req['appearance']['profile_id'])}</td><th>Renderer</th><td>{_esc(req['renderer']['engine'])}</td></tr>
<tr><th>Render time</th><td>{float(c.get('render_elapsed_seconds',0)):.3f} s</td><th>Passes</th><td>{_esc(', '.join(req['passes']))}</td></tr>
<tr><th>Reprojection max</th><td>{float(repro.get('max_residual_px',999)):.5f} px</td><th>median</th><td>{float(repro.get('median_residual_px',999)):.5f} px</td></tr>
</table></section>""")
    html_text = """<!doctype html><meta charset='utf-8'><title>PCS DF-G58 Real Blender Self-Test</title>
<style>body{font-family:system-ui;margin:1.5rem;background:#101114;color:#eee}.ok{padding:1rem;background:#0c2a18;border:2px solid #3bc76b}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:1rem}.card{background:#1b1d22;padding:1rem;border-radius:10px}.imagewrap{position:relative;width:100%;background:#000}.imagewrap img,.overlay{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.overlay{pointer-events:none}table{border-collapse:collapse;width:100%;margin-top:.7rem}th,td{border-bottom:1px solid #444;padding:.3rem;text-align:left}th{color:#9cc7ff}</style>
<h1>PCS Camera Geometry Data Factory — DF-G50..G58</h1><div class='ok'><b>REAL_BLENDER_RENDERED</b> — this gallery was generated only from verified real Blender completion manifests.</div><div class='grid'>""" + "\n".join(cards) + "</div>"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text, encoding="utf-8", newline="\n")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["template", "real"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-root")
    ap.add_argument("--chunk")
    a = ap.parse_args()
    if a.command == "template":
        write_template(Path(a.out)); print(a.out); return 0
    if not a.run_root or not a.chunk:
        raise SystemExit("--run-root and --chunk are required for real")
    chunk = json.loads(Path(a.chunk).read_text(encoding="utf-8"))
    generate_real_gallery(Path(a.run_root), chunk, Path(a.out)); print(a.out); return 0


if __name__ == "__main__":
    raise SystemExit(main())
