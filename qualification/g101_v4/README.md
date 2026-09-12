# DF-G101 V4 — GitHub Windows runtime preflight

Purpose: close the qualification gap explicitly declared by the canonical V4 pre-real record: the original qualification container had no PowerShell runtime, so no Windows PowerShell runtime PASS was claimed.

This GitHub qualification is **synthetic and non-production**. It does not execute the collector against Ricardo's preserved local G101 run-root, does not consume the exactly-one real V4 collector execution authorization, and does not alter Data Factory science, sample admission, production source, Blender, Maya, training, TEST77/A5, or product state.

Canonical authorities:
- V3 failure adjudication: Drive `1_K60VuSItxbci9JSZbWbEKWAK15Gu3fx`
- V4 correction spec: Drive `10CYQRkVLO5b8d4YRvlYW7k4uEIIB0VVB`
- V4 authority-binding addendum: Drive `1SA0O0c9Hhj7EQiHkzykc2BoNotWzN5Ez`
- V4 one-execution authorization: Drive `11r2gwTKIbEelonNhOISUD3SzvUOmHpOH`
- canonical V4 package: Drive `1PREM-mAWFkGBC4iYToSrXG7VoPRvLwlb`
- canonical package SHA-256: `8a81413b620cb7125d87564f8f1ffc7cf5c3294572461d364904dec727ee1e38`

The workflow tests the V4 collector source as a read-only source mirror. It performs:
- PowerShell parser validation of the collector;
- frozen static checks for removal of the V3 binder pattern;
- Windows runtime execution of the replacement `::new()` + `.ToArray()` generic-list path;
- explicit ordered-dictionary key sorting, duplicate-ID map, byte accumulation, and JSON materialization;
- launcher static binding to the bundled PowerShell collector only;
- an informational, non-gating attempt to reproduce the retired V3 `New-Object List[object]` + `@($list)` behavior on the runner's runtime.

The full real collector is deliberately **not executed** in GitHub Actions. The real collector remains governed by the separate exactly-one local execution authorization.
