# DF-G101 Phase 3 Gate 2 — Production Materialized

Status: `PRODUCTION_SOURCE_MATERIALIZED_PENDING_QUALIFICATION`

The governed Gate-2 materializer committed the Normal-only Candidate-B production integration in commit `47ca7bd79ebbb68c8e95f8bb00f621eaf1d766f2`.

This marker intentionally creates a normal branch push after the GitHub-Actions-authored materialization commit so the full Gate-2 qualification workflow can execute on the already-materialized production source. The materializer is idempotent and must report that no further production patch is required.

Frozen Candidate-B method:
`DF_G101_POST_R2_GEOMETRY_SEEDED_SUBPIXEL_VISIBILITY_REFERENCE_B_V1`

Frozen retention floor:
`0.9783428720083247`

Production mutation authority remains Normal FILTER_SAFE_INTERIOR only. Shared `_filter_safe_interior_mask`, R29 Depth authority, Object/Depth principal-point selection, tolerances, raw Normal authority, and renderer outputs remain protected.

No real G101 rerun/resume is authorized by this marker.
