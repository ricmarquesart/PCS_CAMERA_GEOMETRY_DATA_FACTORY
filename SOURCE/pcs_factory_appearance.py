from __future__ import annotations
import math
from typing import Any, Dict, List
from pcs_factory_seed import derive_seed, identity_digest

APPEARANCE_SCHEMA='DF-G40-G48-APPEARANCE-PROFILE-V1'
EFFECT_CLASSES={'GEOMETRY_PRESERVING_BY_CONSTRUCTION','GEOMETRY_PRESERVING_REQUIRES_VALIDATION','SPATIAL_WARP_KNOWN_HOMOGRAPHY','SPATIAL_WARP_KNOWN_NONLINEAR','SPATIAL_WARP_UNKNOWN'}
EXACT_ELIGIBLE_EFFECTS={'GEOMETRY_PRESERVING_BY_CONSTRUCTION','GEOMETRY_PRESERVING_REQUIRES_VALIDATION'}
CATEGORIES={'PBR','LIGHTING','ENVIRONMENT','ATMOSPHERE','IMAGING','NPR','CONCEPT','EDGE_DISPLAY'}

def profile(profile_id:str, category:str, effect:str, exact_eligible:bool, params:Dict[str,Any], requires_assets=None, backend='PINNED_DCC_REQUIRED')->Dict[str,Any]:
    x={'schema':APPEARANCE_SCHEMA,'profile_id':profile_id,'profile_version':'1','category':category,'geometry_effect_class':effect,'exact_GT_eligibility':bool(exact_eligible),'parameters':params,'required_asset_classes':list(requires_assets or []),'backend_requirement':backend,'validation_status':'REQUIRES_REAL_RENDER_VALIDATION' if backend!='NONE' else 'PRE_DCC_MATH_VALIDATED'}
    x['profile_digest_sha256']=identity_digest({k:v for k,v in x.items() if k!='profile_digest_sha256'})
    return x

def canonical_profiles()->List[Dict[str,Any]]:
    P=[]
    add=lambda *a,**k:P.append(profile(*a,**k))
    g='GEOMETRY_PRESERVING_BY_CONSTRUCTION'; v='GEOMETRY_PRESERVING_REQUIRES_VALIDATION'
    add('PBR_REALISTIC_INTENT','PBR',v,True,{'roughness':[0.18,0.85],'metallic':[0.0,1.0],'texture_complexity':'mixed'})
    add('SIMPLE_CLEAN','PBR',v,True,{'roughness':[0.45,0.8],'metallic':[0.0,0.1],'texture_complexity':'low'})
    add('LOW_TEXTURE','PBR',v,True,{'texture_complexity':'very_low','value_variation':'low'})
    add('HIGH_TEXTURE','PBR',v,True,{'texture_complexity':'high','uv_scale_variation':[0.5,4.0]})
    add('REFLECTIVE_CONFUSER','PBR',v,True,{'roughness':[0.02,0.25],'metallic':[0.1,1.0],'glass_like_candidates':True})
    add('DAY_HARD','LIGHTING',g,True,{'key':'sun','shadow_softness':'hard','contrast':'high'})
    add('OVERCAST_SOFT','LIGHTING',g,True,{'key':'sky','shadow_softness':'soft','contrast':'low'})
    add('INTERIOR_MIXED','LIGHTING',g,True,{'temperature_mix':True,'contrast':'medium'})
    add('DARK_LOW_CONTRAST','LIGHTING',g,True,{'exposure_intent':'low','contrast':'low'})
    add('BRIGHT_HIGH_KEY','LIGHTING',g,True,{'exposure_intent':'high','contrast':'medium_low'})
    add('PROCEDURAL_SKY','ENVIRONMENT',g,True,{'background_visible':True,'rotation_deg':[0,360]},backend='PINNED_DCC_REQUIRED')
    add('FOG_HAZE','ATMOSPHERE',v,True,{'visibility':'variable','fog_density':[0.0,0.08]})
    add('IMAGE_DEGRADED','IMAGING',v,True,{'compression':'variable','downsample':'variable','noise':'variable','spatial_warp':False})
    add('CLAY','NPR',v,True,{'materials':'single_clay','edge_warp':False})
    add('TOON','NPR',v,True,{'bands':[2,6],'silhouette':'optional','edge_warp':False})
    add('LINE_ART','NPR',v,True,{'line_mode':'structural_plus_silhouette','edge_warp':False})
    add('TECH_SKETCH','EDGE_DISPLAY',v,True,{'line_mode':'technical','paper_overlay':True,'edge_warp':False})
    add('PAINTERLY_CONCEPT','CONCEPT',v,True,{'value_grouping':'simplified','brush_overlay':True,'spatial_warp':False})
    add('GRAYSCALE','EDGE_DISPLAY',g,True,{'saturation':0.0},backend='NONE')
    add('BLUEPRINT','EDGE_DISPLAY',g,True,{'palette':'blueprint','spatial_warp':False},backend='NONE')
    return P

def validate_profile(x:Dict[str,Any])->Dict[str,Any]:
    errs=[]
    if x.get('schema')!=APPEARANCE_SCHEMA: errs.append('BAD_SCHEMA')
    if x.get('category') not in CATEGORIES: errs.append('BAD_CATEGORY')
    e=x.get('geometry_effect_class')
    if e not in EFFECT_CLASSES: errs.append('BAD_EFFECT_CLASS')
    if x.get('exact_GT_eligibility') and e not in EXACT_ELIGIBLE_EFFECTS: errs.append('EXACT_GT_INELIGIBLE_EFFECT')
    p=x.get('parameters')
    if not isinstance(p,dict): errs.append('PARAMS_NOT_OBJECT')
    if isinstance(p,dict):
        def scan(v,path=''):
            if isinstance(v,(int,float)) and not isinstance(v,bool) and not math.isfinite(float(v)): errs.append('NONFINITE:'+path)
            elif isinstance(v,list):
                for i,q in enumerate(v): scan(q,f'{path}[{i}]')
            elif isinstance(v,dict):
                for k,q in v.items(): scan(q,f'{path}.{k}')
        scan(p,'parameters')
    req=x.get('required_asset_classes',[])
    if not isinstance(req,list): errs.append('BAD_REQUIRED_ASSETS')
    return {'status':'PASS' if not errs else 'FAIL','errors':errs}

def choose_profile(root_seed:int, category:str, ordinal:int=0)->Dict[str,Any]:
    options=[p for p in canonical_profiles() if p['category']==category]
    if not options: raise ValueError('NO_PROFILE_FOR_CATEGORY')
    sd=derive_seed(root_seed,'appearance_profile',category,ordinal)
    return options[sd['seed_u64']%len(options)]

def mm(A,B):
    return [[sum(float(A[i][k])*float(B[k][j]) for k in range(3)) for j in range(3)] for i in range(3)]
def apply_h(H,p):
    u,v=float(p[0]),float(p[1]); q=[H[0][0]*u+H[0][1]*v+H[0][2],H[1][0]*u+H[1][1]*v+H[1][2],H[2][0]*u+H[2][1]*v+H[2][2]]
    if abs(q[2])<1e-15: return None
    return [q[0]/q[2],q[1]/q[2]]
def H_identity(): return [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
def H_crop(x0,y0): return [[1.,0.,-float(x0)],[0.,1.,-float(y0)],[0.,0.,1.]]
def H_mirror_x(width:int): return [[-1.,0.,float(width-1)],[0.,1.,0.],[0.,0.,1.]]
def H_resize(w0:int,h0:int,w1:int,h1:int):
    sx=float(w1)/float(w0); sy=float(h1)/float(h0)
    return [[sx,0.,0.5*sx-0.5],[0.,sy,0.5*sy-0.5],[0.,0.,1.]]
def H_roll(width:int,height:int,deg:float):
    th=math.radians(float(deg)); c=math.cos(th);s=math.sin(th);cx=(width-1)/2.;cy=(height-1)/2.
    # image coordinates y-down; positive deg is visually clockwise
    return [[c,-s,cx-c*cx+s*cy],[s,c,cy-s*cx-c*cy],[0.,0.,1.]]
def transform_points(H,pts): return [apply_h(H,p) for p in pts]

def validate_known_homography(before,after,H,tol_px=1e-9):
    if len(before)!=len(after): return {'status':'FAIL','reason':'COUNT_MISMATCH'}
    errs=[]
    for a,b in zip(before,after):
        q=apply_h(H,a)
        if q is None: return {'status':'FAIL','reason':'POINT_AT_INFINITY'}
        errs.append(math.hypot(q[0]-b[0],q[1]-b[1]))
    mx=max(errs,default=0.); med=sorted(errs)[len(errs)//2] if errs else 0.
    return {'status':'PASS' if mx<=tol_px else 'FAIL','max_displacement_residual_px':mx,'median_displacement_residual_px':med,'tolerance_px':tol_px}
