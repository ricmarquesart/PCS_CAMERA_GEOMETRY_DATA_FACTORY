# DF-G101 Phase 3 Gate C — MICRO100 Production Equivalence Spec Freeze

Date: 2026-09-14 UTC

Status: `SPEC_FROZEN / EVIDENCE_MATERIALIZATION_IN_PROGRESS / REAL_G101_NOT_AUTHORIZED`

Canonical governance document: Google Drive `1F-9Y0zP1raEFeEh3T85T_FG2wBNw5ycmfxnXbtLmJOo`.

## Canonical authority

- G100 closure: `CLOSED_PASS_REAL_MICRO100`, Drive `1a63qacKbvG_OKUwGzPCoBXIk5WxmZiauKBXQiBstNJs`.
- Canonical RETURN: `PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_RETURN_20260909_R36.zip`.
- Drive ID: `12VDhJRmvu105VHRplr2I2LtGeGwVcQdV`.
- Bytes: `64151371`.
- SHA-256: `f94476c926bb7ba6e13e5122031dc25649e1f8277d4440bb0471ce946e57dee6`.
- ZIP entries: `235`; CRC: PASS.
- `RETURN_MANIFEST.json`: `48338` bytes; SHA-256 `c9a32fc848b7083bb3224d52554dae0554dcefc899505e40fdde07f99b5d4a3f`.

## Frozen Gate-C pass condition

Current production Candidate B must be executed read-only against all 100 canonical MICRO100 samples. Every sample must authenticate, remain PASS, produce a corrected Normal safe mask byte-identical to the inherited mask, retain exactly `1.0`, produce zero exclusions and empty reason counts, introduce zero unexplained invalid interior, and preserve effective camera K plus Depth/Object authority. The Gate2 static Depth/K firewall must remain PASS. No rendered Normal, RGB, acceptance, sample identity, seed, or digest may enter Candidate-B mask selection.

Aggregate inherited Normal-safe pixels frozen by the canonical evidence materialization: `7066304`.

## Compact evidence materialization

A minimal hybrid-OID capsule was generated only from byte-authenticated canonical R36 evidence:

- schema: `DF-G101-PHASE3-GATE-C-MICRO100-MINIMAL-HYBRID-OID-CAPSULE-V1`
- JSON: `493271` bytes / SHA-256 `4838e81a1876cca9042a9b5e44e2cc2e4dd8dc39d111c5aaf1055cf25745d5d3`
- XZ: `77292` bytes / SHA-256 `64a8b870c6b76af710cab904e7558370a7225d405762707d936cc236ddeead4f`
- Base64: `103056` bytes / SHA-256 `28a15d6df6534e5e8c56ebdd686b5ad0c8620da8fbcb14542f3106db54bbd7e9`
- sample-ID digest: `6d3b047de7ce2cdbdf50e99c0a315eb737be3b7942c6fb0e558d1535fb7b46d3`
- inherited Normal-safe digest: `4a31f4df0b059d22c29bb61f93f24059aec4c7f90dcc43b09f4591916e733383`

Inherited-mask reconstruction is analytic-PID hash-gated for 92 samples. Eight samples require hash-bound archived rendered Object Index transport because exact geometric coincident visibility can choose an alternate object identity on the same surface: ordinals `003, 027, 039, 051, 063, 075, 087, 099`. Rendered Object Index remains inherited baseline/cross-check evidence only and cannot override Candidate-B analytic witness semantics.

A canonical-source local precheck reproduced the inherited Normal-safe masks for 100/100 under this hybrid transport. This is only a transport precheck; final Gate-C scientific authority requires the committed CURRENT production Candidate B in GitHub CI.

## Execution plan

1. Materialize the capsule/manifest without production-science changes.
2. Authenticate transport before any scientific assertion.
3. Reconstruct each inherited mask and invoke current production `_phase3_candidate_b_normal_safe_mask`.
4. Shard 100 samples to stay under CI timeout and run Ubuntu/Windows qualification where practical.
5. Emit per-shard JSON artifacts and aggregate exactly 100 unique ordinals, `7066304` inherited/corrected safe pixels, zero exclusions, empty reasons, and one qualified committed head.
6. Close Gate C only after those committed CI artifacts pass.

Gate C does **not** authorize real G101. PRE_REAL_PASS remains a separate closure after Gate C and the required synthetic/negative/determinism/performance/package/Drive-round-trip aggregation.
