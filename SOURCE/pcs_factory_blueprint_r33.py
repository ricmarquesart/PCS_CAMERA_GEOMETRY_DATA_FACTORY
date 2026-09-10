from __future__ import annotations

from pcs_factory_qualification import is_factory_qualification_split

"""R33 BLUEPRINT vertical-dominant visibility normalization policy.

Eligibility is derived exclusively from the frozen request geometry/camera and
inherited lighting-policy categories. Rendered RGB, acceptance status and RGB
thresholds are deliberately not consumed.
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

IMPLEMENTATION_ID = "DF_G100_BLUEPRINT_VERTICAL_DOMINANT_FIXED_RGB_GAIN_X2_R33_V1"
POLICY_ID = "BLUEPRINT_DOWNLIGHT_VERTICAL_DOMINANT_VISIBILITY_GAP"
R33_SPEC_DRIVE_ID = "1nFRwtgCPKxN7YjQ8eZdAsHZhlrZQGAyJ2CpdQzBu470"
DOMINANT_FACE_FRACTION_MIN = 0.45
VERTICAL_FACE_ABS_UP_MAX = 0.25
CLOSED_ROOM_FAMILIES = {"INTERIOR", "CORRIDOR", "CLUTTER", "HYBRID_CONCEPT"}


def _require_numpy():
    if np is None:
        raise RuntimeError("R33_BLUEPRINT_POLICY_NUMPY_UNAVAILABLE:" + str(_NUMPY_ERROR))


def _face_world_normal(obj: dict, face_id: int):
    axis = int(face_id) // 2
    sign = -1.0 if int(face_id) % 2 == 0 else 1.0
    nloc = np.zeros(3, dtype=np.float64)
    nloc[axis] = sign
    R = np.asarray(obj["R_local_to_world"], dtype=np.float64)
    if R.shape != (3, 3):
        raise RuntimeError("R33_BLUEPRINT_POLICY_OBJECT_ROTATION_SCHEMA")
    return R @ nloc


def r33_blueprint_vertical_dominant_policy(request: dict) -> dict:
    _require_numpy()
    split = str(request.get("split", ""))
    profile = str((request.get("appearance") or {}).get("profile_id", ""))
    family = str((request.get("scene") or {}).get("scene_family", ""))
    r15 = r15_camera_inside_fill_policy(request)
    base = {
        "implementation_id": IMPLEMENTATION_ID,
        "classification": POLICY_ID,
        "r33_spec_drive_id": R33_SPEC_DRIVE_ID,
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
        "dominant_face_fraction_min": DOMINANT_FACE_FRACTION_MIN,
        "vertical_face_abs_up_max": VERTICAL_FACE_ABS_UP_MAX,
        "closed_room_fill_active": family in CLOSED_ROOM_FAMILIES,
        "r15_fill_active": bool(r15.get("applied")),
    }
    if not is_factory_qualification_split(split) or profile != "BLUEPRINT":
        return base

    camera = request.get("camera") or {}
    h = int(camera.get("height", 0)); w = int(camera.get("width", 0))
    C = np.asarray((camera.get("pose") or {}).get("camera_center_world"), dtype=np.float64)
    objects = (request.get("scene") or {}).get("objects") or []
    if C.shape != (3,) or h <= 0 or w <= 0 or not objects:
        raise RuntimeError("R33_BLUEPRINT_POLICY_REQUEST_SCHEMA")

    T, F = _hit_stack_with_faces(request, C, h, w)
    if T.ndim != 3 or F.shape != T.shape or T.shape[2] != len(objects):
        raise RuntimeError("R33_BLUEPRINT_POLICY_HIT_STACK_SHAPE")
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
    if np.any(fg):
        labs, counts = np.unique(labels[fg], return_counts=True)
        order = np.lexsort((labs, -counts))
        dominant_label = int(labs[order[0]])
        dominant_count = int(counts[order[0]])
        dominant_object_index = dominant_label // 6
        dominant_face_id = dominant_label % 6
        dominant_fraction = float(dominant_count / float(h * w))
        n_world = _face_world_normal(objects[dominant_object_index], dominant_face_id)
        abs_up = float(abs(n_world[1]))
        dominant_object_id = str(objects[dominant_object_index].get("object_id", ""))
    else:
        dominant_label = -1; dominant_count = 0; dominant_object_index = -1
        dominant_face_id = -1; dominant_fraction = 0.0; abs_up = float("inf")
        n_world = np.array([0.0, 0.0, 0.0]); dominant_object_id = ""

    base.update({
        "raster_pixels": int(h * w),
        "foreground_pixels": int(np.count_nonzero(fg)),
        "background_pixels": int(np.count_nonzero(~valid)),
        "dominant_label": dominant_label,
        "dominant_face_pixels": dominant_count,
        "dominant_face_fraction": dominant_fraction,
        "dominant_object_index": dominant_object_index,
        "dominant_object_id": dominant_object_id,
        "dominant_face_id": dominant_face_id,
        "dominant_face_world_normal": [float(x) for x in n_world.tolist()],
        "dominant_face_abs_canonical_up_component": abs_up,
    })

    eligible = (
        dominant_fraction >= DOMINANT_FACE_FRACTION_MIN
        and abs_up <= VERTICAL_FACE_ABS_UP_MAX
        and family not in CLOSED_ROOM_FAMILIES
        and not bool(r15.get("applied"))
    )
    if eligible:
        base.update({
            "applied": True,
            "gain_numerator": 2,
            "gain_denominator": 1,
            "offset_u8": 0,
        })
    return base
