from __future__ import annotations

from pcs_factory_qualification import is_factory_qualification_split

"""R23 production-promoted systemic low-visibility-diversity RGB rescue policy.

Eligibility is derived exclusively from the frozen canonical request geometry and
camera raster. No rendered RGB values or acceptance thresholds are consumed.
"""

try:
    import numpy as np
except Exception as e:  # pragma: no cover
    np = None
    _NUMPY_ERROR = repr(e)
else:
    _NUMPY_ERROR = None

from pcs_factory_micro100_gt import _hit_stack_with_faces

IMPLEMENTATION_ID = 'DF_G100_LOW_DIVERSITY_FIXED_RGB_CONTRAST_R23_PRODUCTION_V1'
DOMINANT_FACE_FRACTION_MIN = 0.80
PROFILE_TRANSFORMS = {
    'BLUEPRINT': {'pivot_u8':128,'factor_numerator':5,'factor_denominator':4},
    'TOON': {'pivot_u8':192,'factor_numerator':5,'factor_denominator':4},
    'DAY_HARD': {'pivot_u8':192,'factor_numerator':7,'factor_denominator':4},
    'CLAY': {'pivot_u8':192,'factor_numerator':7,'factor_denominator':2},
    'PAINTERLY_CONCEPT': {'pivot_u8':192,'factor_numerator':3,'factor_denominator':2},
}


def _require_numpy():
    if np is None:
        raise RuntimeError('R23_RGB_POLICY_NUMPY_UNAVAILABLE:'+str(_NUMPY_ERROR))


def r23_systemic_rgb_policy(request: dict) -> dict:
    _require_numpy()
    profile = str((request.get('appearance') or {}).get('profile_id',''))
    split = str(request.get('split',''))
    base = {
        'implementation_id': IMPLEMENTATION_ID,
        'applied': False,
        'split': split,
        'profile_id': profile,
        'eligibility_uses_rendered_rgb_statistics': False,
        'threshold_adaptive': False,
        'spatial_warp': False,
        'dominant_face_fraction_min': DOMINANT_FACE_FRACTION_MIN,
    }
    if not is_factory_qualification_split(split) or profile not in PROFILE_TRANSFORMS:
        return base
    camera = request.get('camera') or {}
    h = int(camera.get('height',0)); w = int(camera.get('width',0))
    C = np.asarray((camera.get('pose') or {}).get('camera_center_world'),dtype=np.float64)
    if C.shape != (3,) or h <= 0 or w <= 0:
        raise RuntimeError('R23_RGB_POLICY_CAMERA_SCHEMA')
    T,F = _hit_stack_with_faces(request,C,h,w)
    if T.ndim != 3 or F.shape != T.shape:
        raise RuntimeError('R23_RGB_POLICY_HIT_STACK_SHAPE')
    min_t = np.min(T,axis=2)
    arg = np.argmin(T,axis=2)
    valid = np.isfinite(min_t)
    background_pixels = int(np.count_nonzero(~valid))
    pid = np.where(valid,arg+1,0).astype(np.int32)
    visible_ids = [int(x) for x in np.unique(pid) if int(x)>0]
    face = np.full((h,w),-1,dtype=np.int16)
    for j in range(T.shape[2]):
        m = pid==(j+1)
        face[m] = F[:,:,j][m]
    labels = np.where(pid>0,(pid-1)*6+face,-1)
    fg = labels>=0
    if np.any(fg):
        _lab, counts = np.unique(labels[fg],return_counts=True)
        dominant_face_fraction = float(np.max(counts)/float(h*w))
    else:
        dominant_face_fraction = 0.0
    base.update({
        'raster_pixels': int(h*w),
        'background_pixels': background_pixels,
        'visible_object_ids': visible_ids,
        'visible_object_count': len(visible_ids),
        'dominant_face_fraction': dominant_face_fraction,
    })
    eligible = (
        background_pixels == 0 and
        len(visible_ids) == 1 and
        dominant_face_fraction >= DOMINANT_FACE_FRACTION_MIN
    )
    if eligible:
        base['applied'] = True
        base.update(PROFILE_TRANSFORMS[profile])
    return base
