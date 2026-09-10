from __future__ import annotations

"""G101 R2 BLUEPRINT foreground-dominant near-total vertical visibility policy.

Eligibility is derived exclusively from the frozen request geometry/camera and
inherited visibility/lighting categories. It composes after R36 and intentionally
consumes no rendered-image measurements or acceptance outcomes.
"""

from pcs_factory_qualification import is_factory_qualification_split
from pcs_factory_visibility_r15 import r15_camera_inside_fill_policy
from pcs_factory_blueprint_r33 import CLOSED_ROOM_FAMILIES
from pcs_factory_blueprint_r36 import r36_blueprint_extreme_vertical_policy

IMPLEMENTATION_ID = "DF_G101_BLUEPRINT_FOREGROUND_VERTICAL_FIXED_RGB_GAIN_X2_R2_V1"
POLICY_ID = "BLUEPRINT_DOWNLIGHT_FOREGROUND_DOMINANT_NEAR_TOTAL_VERTICAL_VISIBILITY_GAP"
G101_R2_SPEC_DRIVE_ID = "1tidiKAl6NspDeIq0yQyf5l2hc-DQjEcHVq-tO0aUSJk"
FOREGROUND_RASTER_NUMERATOR = 2
FOREGROUND_RASTER_DENOMINATOR = 3
VERTICAL_FOREGROUND_NUMERATOR = 19
VERTICAL_FOREGROUND_DENOMINATOR = 20
VERTICAL_FACE_ABS_UP_MAX = 0.25


def g101_r2_blueprint_foreground_vertical_policy(request: dict) -> dict:
    split = str(request.get("split", ""))
    profile = str((request.get("appearance") or {}).get("profile_id", ""))
    family = str((request.get("scene") or {}).get("scene_family", ""))
    r15 = r15_camera_inside_fill_policy(request)
    base = {
        "implementation_id": IMPLEMENTATION_ID,
        "classification": POLICY_ID,
        "g101_r2_spec_drive_id": G101_R2_SPEC_DRIVE_ID,
        "applied": False,
        "split": split,
        "profile_id": profile,
        "scene_family": family,
        "eligibility_uses_rendered_rgb_statistics": False,
        "acceptance_status_used": False,
        "threshold_adaptive": False,
        "adaptive": False,
        "spatial_warp": False,
        "resize": False,
        "resample": False,
        "foreground_raster_fraction_min": 2.0 / 3.0,
        "vertical_foreground_fraction_min": 0.95,
        "vertical_face_abs_up_max": VERTICAL_FACE_ABS_UP_MAX,
        "closed_room_fill_active": family in CLOSED_ROOM_FAMILIES,
        "r15_fill_active": bool(r15.get("applied")),
    }
    if not is_factory_qualification_split(split) or profile != "BLUEPRINT":
        return base

    r36 = r36_blueprint_extreme_vertical_policy(request)
    raster_pixels = int(r36.get("raster_pixels", 0) or 0)
    foreground_pixels = int(r36.get("foreground_pixels", 0) or 0)
    vertical_pixels = int(r36.get("aggregate_vertical_face_pixels", 0) or 0)
    if raster_pixels <= 0:
        raise RuntimeError("G101_R2_BLUEPRINT_POLICY_RASTER_SCHEMA")

    foreground_fraction = float(foreground_pixels / float(raster_pixels))
    vertical_foreground_fraction = (
        float(vertical_pixels / float(foreground_pixels)) if foreground_pixels else 0.0
    )
    existing_r33_applied = bool(r36.get("existing_r33_applied"))
    existing_r36_applied = bool(r36.get("applied"))
    base.update({
        "raster_pixels": raster_pixels,
        "foreground_pixels": foreground_pixels,
        "background_pixels": int(raster_pixels - foreground_pixels),
        "aggregate_vertical_face_pixels": vertical_pixels,
        "foreground_raster_fraction": foreground_fraction,
        "aggregate_vertical_foreground_fraction": vertical_foreground_fraction,
        "aggregate_vertical_raster_fraction": float(r36.get("aggregate_vertical_raster_fraction", 0.0)),
        "existing_r33_applied": existing_r33_applied,
        "existing_r36_applied": existing_r36_applied,
        "vertical_faces": r36.get("vertical_faces", []),
    })

    foreground_dominant = foreground_pixels * FOREGROUND_RASTER_DENOMINATOR >= raster_pixels * FOREGROUND_RASTER_NUMERATOR
    foreground_nearly_all_vertical = (
        foreground_pixels > 0
        and vertical_pixels * VERTICAL_FOREGROUND_DENOMINATOR >= foreground_pixels * VERTICAL_FOREGROUND_NUMERATOR
    )
    eligible = (
        not existing_r33_applied
        and not existing_r36_applied
        and family not in CLOSED_ROOM_FAMILIES
        and not bool(r15.get("applied"))
        and foreground_dominant
        and foreground_nearly_all_vertical
    )
    if eligible:
        base.update({
            "applied": True,
            "gain_numerator": 2,
            "gain_denominator": 1,
            "offset_u8": 0,
        })
    return base
