# PCS Camera Geometry Data Factory

Private engineering/source repository for the **Precision Camera Solver Camera Geometry Data Factory**.

This repository is intentionally **Data Factory only**. C-Hub, C-RADIO, specialist projects, Maya product runtime, datasets, production run-roots, RETURN/FAILURE_RETURN packages and large evidence artifacts do not belong here.

## Authority model

At this bootstrap stage, **Google Drive remains the canonical project/scientific authority** for frozen specs, accepted release packages, real-run evidence, datasets and Project Control. GitHub is the dedicated source-control mirror and future CI surface for Data Factory engineering.

See [`AUTHORITY.md`](AUTHORITY.md) for the exact source seed and Drive authorities.

## Source layout

- `SOURCE/` — current Data Factory Python source baseline.
- `df_g101_scale1k.py` — current G101 SCALE1K runner source baseline.
- `df_g101_focused_selftest.py` — focused regression/selftest source shipped with the baseline.
- `RUN_DF_G101_SCALE1K.bat` / `RUN_DF_G101_SCALE1K_GUARDIAN.ps1` — Windows launcher/guardian source from the baseline release.
- `SPECS/` — pointers to frozen Google Drive specs; not copies of mutable project history.
- `AUTHORITY/` and `PLAN_G101/` — small identity/pointer artifacts only.
- `SOURCE_SEED_MANIFEST.json` — SHA-256 inventory of the initial source seed.

## Important

This Git repository is **not** a production run-root and should never be used to store generated 1K/10K data. The currently authorized G101 R2 real run remains isolated on the Windows machine and is not changed by this bootstrap.

CI will be added as a separate, explicit step after the source mirror is verified. The first bootstrap is intentionally minimal.
