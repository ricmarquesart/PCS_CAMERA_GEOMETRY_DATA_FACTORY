from __future__ import annotations

QUALIFICATION_SPLITS = frozenset({
    "MICRO100_QUALIFICATION_ONLY",
    "SCALE1K_QUALIFICATION_ONLY",
})

def is_factory_qualification_split(value) -> bool:
    return str(value) in QUALIFICATION_SPLITS
