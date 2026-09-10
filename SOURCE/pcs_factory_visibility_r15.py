from __future__ import annotations

from pcs_factory_qualification import is_factory_qualification_split

IMPLEMENTATION_ID = "DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15"
CLOSED_ROOM_FAMILIES = {"INTERIOR", "CORRIDOR", "CLUTTER", "HYBRID_CONCEPT"}

def camera_inside_closed_solid_ids(scene_recipe, camera_center_world):
    C=[float(x) for x in camera_center_world]
    out=[]
    for obj in (scene_recipe or {}).get("objects", []):
        R=obj.get("R_local_to_world")
        ctr=obj.get("center_world")
        dims=obj.get("dimensions_m")
        if not (R and ctr and dims and len(R)==3 and len(ctr)==3 and len(dims)==3):
            continue
        delta=[C[i]-float(ctr[i]) for i in range(3)]
        # local = R^T * (C-center)
        local=[sum(float(R[j][a])*delta[j] for j in range(3)) for a in range(3)]
        half=[float(d)/2.0 for d in dims]
        if all(abs(local[a]) < half[a] for a in range(3)):
            out.append(str(obj.get("object_id")))
    return out

def r15_camera_inside_fill_policy(request):
    scene=(request or {}).get("scene") or {}
    app=(request or {}).get("appearance") or {}
    profile=str(app.get("profile_id", ""))
    family=str(scene.get("scene_family", ""))
    split=str((request or {}).get("split", ""))
    pose=((request or {}).get("camera") or {}).get("pose") or {}
    ids=camera_inside_closed_solid_ids(scene, pose.get("camera_center_world", ())) if pose.get("camera_center_world") else []
    existing_closed_room = is_factory_qualification_split(split) and family in CLOSED_ROOM_FAMILIES and profile!="PAINTERLY_CONCEPT"
    painterly = profile=="PAINTERLY_CONCEPT"
    applied = is_factory_qualification_split(split) and bool(ids) and (not painterly) and (not existing_closed_room)
    reason=("APPLY" if applied else ("NOT_QUALIFICATION_SPLIT" if not is_factory_qualification_split(split) else ("CAMERA_OUTSIDE_ALL_SOLIDS" if not ids else ("PAINTERLY_FILL_ALREADY_ACTIVE" if painterly else "CLOSED_ROOM_FILL_ALREADY_ACTIVE"))))
    return {
        "implementation_id": IMPLEMENTATION_ID,
        "camera_inside_solid_object_ids": ids,
        "camera_inside_any_solid": bool(ids),
        "applied": bool(applied),
        "suppression_reason": None if applied else reason,
        "energy_w": 350.0 if applied else None,
        "soft_shadow_radius_m": 2.0 if applied else None,
        "location": "BLENDER_CAMERA_LOCATION" if applied else None,
        "geometry_preserving": True,
        "spatial_warp": False,
        "adaptive": False,
        "threshold_adaptive": False,
    }
