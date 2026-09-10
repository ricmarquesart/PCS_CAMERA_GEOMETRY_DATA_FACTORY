# PCS CAMERA GEOMETRY DATA FACTORY — DF-G101 SCALE1K V1 — R2 RECOVERY

Status at package creation: **PRE-REAL QUALIFIED; REAL EXECUTION REQUIRES THE SEPARATE DRIVE RELEASE AUTHORIZATION RECORD.**

This is **not** a fresh SCALE1K runner. It is a one-time recovery/continuation package for the exact existing fail-closed `DF_G101_SCALE1K_V1_R1` run-root produced by the single authorized R1 execution.

## What R2 does

1. Authenticates the exact R1 10-COMPLETE prestate before any run-root mutation.
2. Preserves the complete sample0005 pre-remediation evidence and the R1 failure authority.
3. Applies the frozen geometry/light-only G101-R2 BLUEPRINT terminal RGB8 x2 transform to `g101v1_0005_urban_low_camera_blueprint` using existing bytes; **no rerender**.
4. Requires sample0005 to pass the unchanged acceptance gates and proves GT/camera/masks remain byte-identical.
5. Revalidates existing PASS 0000-0004 without rewriting their acceptance records; materializes acceptance 0006-0009 from their existing COMPLETE bytes without worker invocation.
6. Keeps the chunk000 ledger byte-identical and rebuilds its archive.
7. Continues real rendering only at chunk001/sample0010.
8. Applies the same frozen R2 geometry-only rule to future eligible BLUEPRINT samples after R36.
9. Emits collision-safe compact FAILURE_RETURN evidence if anything fails.

## Frozen R2 science

R2 applies only when BLUEPRINT, R33=false, R36=false, not a closed-room family, no R15 camera-inside fill, foreground occupies at least 2/3 of the raster, and at least 95% of foreground pixels are substantially vertical. Eligibility does not read rendered RGB, acceptance, sample ID, seed or digest. Transform: `y=min(255,2*x)` per RGB8 channel. RGB thresholds are unchanged.

Spec authority: Google Drive `1tidiKAl6NspDeIq0yQyf5l2hc-DQjEcHVq-tO0aUSJk`.
Canonical R1 failure authority embedded under `AUTHORITY/` SHA-256 `653a3ebe21c4fdb5f9be3d30a76e2332ea996858acf80ac6d81dd72cfa413f7e`.

## Operator procedure

- Preserve `C:\PCS_LABS\CAMERA_GEOMETRY_DATA_FACTORY\09_RUNS\DF_G101_SCALE1K_V1_R1` exactly.
- Do **not** run R1 again and do not delete/reset/rename/recreate/manual-edit that run-root.
- Close Maya and Blender.
- Extract this entire ZIP to a new folder **outside** the factory root.
- Run only `RUN_DF_G101_SCALE1K.bat`, exactly once.
- If the Guardian blocks or anything fails, return the FAILURE_RETURN plus Guardian result and **do not rerun**.
- On measurement success, return the INDEX ZIP and all ten RETURN_SHARD ZIPs.

1000/1000 is measurement completion only. SCALE1K still requires independent Drive round-trip, statistical/operational/corpus QA and frozen visual adjudication before closure. 10K, training/C-RADIO/TEST77/A5 and Maya/product mutation remain blocked/separate.
