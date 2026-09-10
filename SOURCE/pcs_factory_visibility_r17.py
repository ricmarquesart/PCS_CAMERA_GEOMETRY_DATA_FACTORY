from pcs_factory_qualification import is_factory_qualification_split
from pcs_factory_visibility_r15 import r15_camera_inside_fill_policy

IMPLEMENTATION_ID = "DF_G100_CAMERA_INSIDE_FIXED_RGB_CONTRAST_V1_R17"
PIVOT_U8 = 128
FACTOR_NUMERATOR = 17
FACTOR_DENOMINATOR = 16

def r17_camera_inside_contrast_policy(request):
    r15 = r15_camera_inside_fill_policy(request)
    applied = bool(
        is_factory_qualification_split(request.get("split"))
        and r15.get("applied") is True
    )
    return {
        "implementation_id": IMPLEMENTATION_ID,
        "applied": applied,
        "eligibility_semantics": "R15_CAMERA_INSIDE_VISIBILITY_AID_CATEGORY_R17",
        "pivot_u8": PIVOT_U8,
        "factor_numerator": FACTOR_NUMERATOR,
        "factor_denominator": FACTOR_DENOMINATOR,
        "adaptive": False,
        "threshold_adaptive": False,
        "sample_statistics_used": False,
        "spatial_warp": False,
        "resize": False,
        "resample": False,
        "geometry_preserving": True,
        "r15_policy": r15,
    }
