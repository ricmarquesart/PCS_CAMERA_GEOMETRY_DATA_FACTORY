from __future__ import annotations
import statistics

PROBE_FRACTIONS=((0.25,0.25),(0.75,0.25),(0.75,0.75),(0.25,0.75),(0.50,0.25),(0.75,0.50),(0.50,0.75),(0.25,0.50))
PROBE_DEPTHS_M=(4.0,4.0,4.0,4.0,8.0,8.0,8.0,8.0)

def camera_graphics_probe_specs(K,width:int,height:int):
    fx=float(K[0][0]); skew=float(K[0][1]); cx=float(K[0][2])
    fy=float(K[1][1]); cy=float(K[1][2])
    if fx<=0 or fy<=0 or int(width)<=1 or int(height)<=1:
        raise ValueError('invalid intrinsics/raster for R14 probe construction')
    out=[]
    for (fu,fv),z in zip(PROBE_FRACTIONS,PROBE_DEPTHS_M):
        u=float(fu)*(int(width)-1); v=float(fv)*(int(height)-1); z=float(z)
        y=((v-cy)/fy)*z
        x=(((u-cx)*z)-skew*y)/fx
        out.append({
            'fraction':[float(fu),float(fv)],
            'target_pixel':[u,v],
            'depth_cv_m':z,
            'camera_cv':[x,y,z],
            'camera_graphics':[x,-y,-z],
        })
    return out

def reprojection_acceptance(residuals,minimum_authoritative_landmarks:int=8,max_tolerance_px:float=0.50,median_tolerance_px:float=0.20):
    vals=[float(v) for v in residuals]
    enough=len(vals)>=int(minimum_authoritative_landmarks)
    mx=max(vals,default=1e9)
    med=statistics.median(vals) if vals else 1e9
    return {
        'status':'PASS' if enough and mx<=float(max_tolerance_px) and med<=float(median_tolerance_px) else 'FAIL',
        'authoritative_landmark_count':len(vals),
        'minimum_authoritative_landmarks':int(minimum_authoritative_landmarks),
        'max_residual_px':mx,
        'median_residual_px':med,
        'tolerance_max_px':float(max_tolerance_px),
        'tolerance_median_px':float(median_tolerance_px),
    }
