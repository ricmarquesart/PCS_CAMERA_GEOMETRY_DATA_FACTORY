from __future__ import annotations

from pcs_factory_qualification import is_factory_qualification_split

"""R36 BLUEPRINT extreme distributed vertical-coverage normalization.

This policy generalizes the physical R33 downlight visibility diagnosis from a
single dominant vertical face to near-total aggregate vertical coverage spread
across multiple visible faces. Eligibility is derived exclusively from frozen
request geometry/camera plus inherited fill categories. Rendered RGB,
acceptance status, and RGB thresholds are deliberately not consumed.
"""

try:
    import numpy as np
except Exception as e:  # pragma: no cover
    np = None
    _NUMPY_ERROR = repr(e)
else:
    _NUMPY_ERROR = None

from pcs_factory_micro100_gt import _hit_stack_with_faces
from pcs_factory_visibility_r15 import r15_camera_inside_fill_policy
from pcs_factory_blueprint_r33 import (
    r33_blueprint_vertical_dominant_policy,
    _face_world_normal,
    CLOSED_ROOM_FAMILIES,
)

IMPLEMENTATION_ID = "DF_G100_BLUEPRINT_EXTREME_VERTICAL_FIXED_RGB_GAIN_X3_R36_V1"
POLICY_ID = "BLUEPRINT_DOWNLIGHT_DISTRIBUTED_EXTREME_VERTICAL_COVERAGE_VISIBILITY_GAP"
R36_SPEC_DRIVE_ID = "1JCmjhF9iccw8ARBoKLSF3ZI_PUjuGVyC_MrJdlMtfPg"
EXTREME_VERTICAL_RASTER_FRACTION_MIN = 0.95
VERTICAL_FACE_ABS_UP_MAX = 0.25


def _require_numpy():
    if np is None:
        raise RuntimeError("R36_BLUEPRINT_POLICY_NUMPY_UNAVAILABLE:" + str(_NUMPY_ERROR))


def r36_blueprint_extreme_vertical_policy(request: dict) -> dict:
    _require_numpy()
    split = str(request.get("split", ""))
    profile = str((request.get("appearance") or {}).get("profile_id", ""))
    family = str((request.get("scene") or {}).get("scene_family", ""))
    r15 = r15_camera_inside_fill_policy(request)
    r33 = r33_blueprint_vertical_dominant_policy(request)
    base = {
        "implementation_id": IMPLEMENTATION_ID,
        "classification": POLICY_ID,
        "r36_spec_drive_id": R36_SPEC_DRIVE_ID,
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
        "vertical_face_abs_up_max": VERTICAL_FACE_ABS_UP_MAX,
        "extreme_vertical_raster_fraction_min": EXTREME_VERTICAL_RASTER_FRACTION_MIN,
        "closed_room_fill_active": family in CLOSED_ROOM_FAMILIES,
        "r15_fill_active": bool(r15.get("applied")),
        "existing_r33_applied": bool(r33.get("applied")),
    }
    if not is_factory_qualification_split(split) or profile != "BLUEPRINT":
        return base

    camera = request.get("camera") or {}
    h = int(camera.get("height", 0)); w = int(camera.get("width", 0))
    C = np.asarray((camera.get("pose") or {}).get("camera_center_world"), dtype=np.float64)
    objects = (request.get("scene") or {}).get("objects") or []
    if C.shape != (3,) or h <= 0 or w <= 0 or not objects:
        raise RuntimeError("R36_BLUEPRINT_POLICY_REQUEST_SCHEMA")

    T, F = _hit_stack_with_faces(request, C, h, w)
    if T.ndim != 3 or F.shape != T.shape or T.shape[2] != len(objects):
        raise RuntimeError("R36_BLUEPRINT_POLICY_HIT_STACK_SHAPE")
    min_t = np.min(T, axis=2)
    arg = np.argmin(T, axis=2)
    valid = np.isfinite(min_t)
    object_idx = np.where(valid, arg, -1).astype(np.int32)
    face = np.full((h, w), -1, dtype=np.int16)
    for j in range(T.shape[2]):
        m = object_idx == j
        face[m] = F[:, :, j][m]
    labels = np.where(valid, object_idx * 6 + face, -1)
    fg = labels >= 0

    vertical_pixels = 0
    vertical_faces = []
    if np.any(fg):
        labs, counts = np.unique(labels[fg], return_counts=True)
        for lab, count in zip(labs.tolist(), counts.tolist()):
            lab = int(lab); count = int(count)
            obj_idx = lab // 6; face_id = lab % 6
            n_world = _face_world_normal(objects[obj_idx], face_id)
            abs_up = float(abs(n_world[1]))
            if abs_up <= VERTICAL_FACE_ABS_UP_MAX:
                vertical_pixels += count
                vertical_faces.append({
                    "label": lab,
                    "object_index": obj_idx,
                    "object_id": str(objects[obj_idx].get("object_id", "")),
                    "face_id": face_id,
                    "pixels": count,
                    "fraction_of_raster": float(count / float(h * w)),
                    "abs_canonical_up_component": abs_up,
                })

    raster_pixels = int(h * w)
    foreground_pixels = int(np.count_nonzero(fg))
    vertical_fraction = float(vertical_pixels / float(raster_pixels)) if raster_pixels else 0.0
    vertical_foreground_fraction = float(vertical_pixels / float(foreground_pixels)) if foreground_pixels else 0.0
    vertical_faces.sort(key=lambda x: (-x["pixels"], x["label"]))
    base.update({
        "raster_pixels": raster_pixels,
        "foreground_pixels": foreground_pixels,
        "background_pixels": int(raster_pixels - foreground_pixels),
        "aggregate_vertical_face_pixels": int(vertical_pixels),
        "aggregate_vertical_raster_fraction": vertical_fraction,
        "aggregate_vertical_foreground_fraction": vertical_foreground_fraction,
        "aggregate_vertical_face_count": len(vertical_faces),
        "vertical_faces": vertical_faces,
    })

    eligible = (
        not bool(r33.get("applied"))
        and vertical_fraction >= EXTREME_VERTICAL_RASTER_FRACTION_MIN
        and family not in CLOSED_ROOM_FAMILIES
        and not bool(r15.get("applied"))
    )
    if eligible:
        base.update({
            "applied": True,
            "gain_numerator": 3,
            "gain_denominator": 1,
            "offset_u8": 0,
        })
    return base
