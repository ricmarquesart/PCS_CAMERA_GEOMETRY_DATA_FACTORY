from __future__ import annotations
import math
from pcs_factory_coordinates import *
CAMERA_SCHEMA_VERSION='DF-G10-G14-CAMERA-V1'
EPS_INF=1e-12

def K_matrix(fx,fy,cx,cy,skew=0.0):
    vals=[fx,fy,cx,cy,skew]
    if not all(math.isfinite(float(v)) for v in vals): raise ValueError('non-finite intrinsics')
    if fx<=0 or fy<=0: raise ValueError('focal pixels must be positive')
    return ((float(fx),float(skew),float(cx)),(0.0,float(fy),float(cy)),(0.0,0.0,1.0))

def intrinsics_from_focal_sensor(focal_mm,sensor_mm,width_px,height_px,fit='HORIZONTAL',cx=None,cy=None,pixel_aspect=1.0):
    if focal_mm<=0 or sensor_mm<=0 or width_px<=1 or height_px<=1 or pixel_aspect<=0: raise ValueError('invalid physical camera')
    fit=fit.upper()
    if fit=='HORIZONTAL':
        fx=focal_mm/sensor_mm*width_px; fy=fx/pixel_aspect
    elif fit=='VERTICAL':
        fy=focal_mm/sensor_mm*height_px; fx=fy*pixel_aspect
    else: raise ValueError('fit must be HORIZONTAL or VERTICAL; AUTO must resolve before authority')
    if cx is None: cx=(width_px-1)/2.0
    if cy is None: cy=(height_px-1)/2.0
    return {'fx_px':fx,'fy_px':fy,'cx_px':float(cx),'cy_px':float(cy),'K':K_matrix(fx,fy,cx,cy),'resolved_fit':fit,'focal_mm':float(focal_mm),'sensor_fit_dimension_mm':float(sensor_mm),'pixel_aspect':float(pixel_aspect)}

def look_at(camera_center,target,up_hint=(0.0,1.0,0.0),roll_deg=0.0):
    C=tuple(map(float,camera_center)); T=tuple(map(float,target)); up=unit(up_hint)
    forward=unit(sub(T,C))
    right=unit(cross(forward,up))
    cam_up=unit(cross(right,forward))
    if roll_deg:
        a=math.radians(float(roll_deg)); ca,sa=math.cos(a),math.sin(a)
        right2=add(scale(right,ca),scale(cam_up,sa))
        up2=add(scale(cam_up,ca),scale(right,-sa))
        right,cam_up=unit(right2),unit(up2)
    back=scale(forward,-1.0)
    R_c2w=tuple(tuple(col[i] for col in (right,cam_up,back)) for i in range(3))
    if frob_orthogonality_error(R_c2w)>1e-12 or abs(det3(R_c2w)-1.0)>1e-12: raise RuntimeError('look_at rotation invalid')
    R_w2g=transpose(R_c2w); R_w2cv=mat_mul(V_FROM_G,R_w2g)
    t=scale(mat_vec(R_w2cv,C),-1.0)
    return {'camera_center_world':C,'R_camera_to_world_graphics':R_c2w,'R_world_to_camera_graphics':R_w2g,'R_world_to_camera_cv':R_w2cv,'t_world_to_camera_cv':t,'forward_world':forward,'right_world':right,'up_world':cam_up}

def world_to_cv(point,pose): return add(mat_vec(pose['R_world_to_camera_cv'],point),pose['t_world_to_camera_cv'])
def direction_to_cv(direction,pose): return mat_vec(pose['R_world_to_camera_cv'],direction)

def project_cv(p,K):
    x,y,z=p
    if z<=0: raise ValueError('point not in front of camera')
    q=mat_vec(K,p); return (q[0]/q[2],q[1]/q[2],z)
def project_world(point,pose,K): return project_cv(world_to_cv(point,pose),K)

def normalize_hpoint(h):
    n=math.sqrt(sum(x*x for x in h))
    if n<=1e-15: raise ValueError('zero homogeneous point')
    h=tuple(x/n for x in h)
    # deterministic unoriented sign: largest-magnitude component positive
    k=max(range(3),key=lambda i:abs(h[i]))
    if h[k]<0: h=tuple(-x for x in h)
    return h

def vanishing_point(direction_world,pose,K,width=None,height=None):
    d=unit(direction_to_cv(unit(direction_world),pose)); h=mat_vec(K,d); hn=normalize_hpoint(h)
    finite=abs(h[2])>EPS_INF
    out={'direction_camera_cv':d,'homogeneous_raw':h,'homogeneous_normalized':hn,'finite':finite}
    if finite:
        u,v=h[0]/h[2],h[1]/h[2]; out['pixel']=(u,v)
        if width is not None and height is not None: out['location_class']='ON_SCREEN' if 0<=u<=width-1 and 0<=v<=height-1 else 'OFF_SCREEN'
    else: out['pixel']=None; out['location_class']='INFINITE'
    return out

def inv3(A):
    d=det3(A)
    if abs(d)<1e-15: raise ValueError('singular')
    a=A
    adj=((a[1][1]*a[2][2]-a[1][2]*a[2][1], a[0][2]*a[2][1]-a[0][1]*a[2][2], a[0][1]*a[1][2]-a[0][2]*a[1][1]),
         (a[1][2]*a[2][0]-a[1][0]*a[2][2], a[0][0]*a[2][2]-a[0][2]*a[2][0], a[0][2]*a[1][0]-a[0][0]*a[1][2]),
         (a[1][0]*a[2][1]-a[1][1]*a[2][0], a[0][1]*a[2][0]-a[0][0]*a[2][1], a[0][0]*a[1][1]-a[0][1]*a[1][0]))
    return tuple(tuple(adj[i][j]/d for j in range(3)) for i in range(3))
def normalize_line(l):
    n=math.hypot(l[0],l[1])
    if n<=1e-15: raise ValueError('invalid image line')
    l=tuple(x/n for x in l)
    if l[0]<-1e-15 or (abs(l[0])<=1e-15 and l[1]<0): l=tuple(-x for x in l)
    return l

def horizon_from_plane_normal(normal_world,pose,K):
    ncv=direction_to_cv(unit(normal_world),pose)
    lin=mat_vec(transpose(inv3(K)),ncv)
    return {'normal_camera_cv':ncv,'line_raw':lin,'line_normalized':normalize_line(lin)}

def line_through_pixels(p1,p2):
    x1,y1=p1; x2,y2=p2
    return normalize_line((y1-y2,x2-x1,x1*y2-x2*y1))
def line_point_distance(line,p): return abs(line[0]*p[0]+line[1]*p[1]+line[2])

def clip_segment(p1,p2,width,height):
    # Liang-Barsky on pixel-center rectangle
    x0,y0=p1; x1,y1=p2; dx=x1-x0; dy=y1-y0
    p=(-dx,dx,-dy,dy); q=(x0,width-1-x0,y0,height-1-y0); u0,u1=0.0,1.0
    for pi,qi in zip(p,q):
        if abs(pi)<1e-15:
            if qi<0:return None
        else:
            r=qi/pi
            if pi<0: u0=max(u0,r)
            else: u1=min(u1,r)
            if u0>u1:return None
    return ((x0+u0*dx,y0+u0*dy),(x0+u1*dx,y0+u1*dy))

def structural_line(line_id,p0_world,p1_world,family_id,pose,K,width,height,object_id='analytic',plane_id=None):
    a=world_to_cv(p0_world,pose); b=world_to_cv(p1_world,pose)
    if a[2]<=0 or b[2]<=0:
        return {'line_id':line_id,'direction_family_id':family_id,'visibility_class':'BEHIND_OR_CROSSES_CAMERA','object_id':object_id,'plane_id':plane_id}
    pa=project_cv(a,K)[:2]; pb=project_cv(b,K)[:2]; line=line_through_pixels(pa,pb); clipped=clip_segment(pa,pb,width,height)
    return {'line_id':line_id,'direction_family_id':family_id,'object_id':object_id,'plane_id':plane_id,'world_endpoints':[p0_world,p1_world],'projected_endpoints':[pa,pb],'image_line':line,'clipped_segment':clipped,'visibility_class':'GEOMETRIC_IN_FRAME' if clipped else 'OUTSIDE'}

def camera_profile(profile,seed_u64,width=960,height=540):
    # deterministic stdlib RNG, profile ranges are stable V1 diagnostics only
    import random
    r=random.Random(int(seed_u64))
    bins={
      'NORMAL':(45,70,0,10,0,4,1.2,2.2), 'WIDE':(80,110,0,18,0,6,0.5,1.8), 'TELEPHOTO':(20,35,0,8,0,3,1.2,3.0),
      'STRONG_ROLL':(45,75,0,12,15,35,0.8,2.2), 'STRONG_PITCH':(45,80,20,50,0,8,0.4,3.2), 'LOW_CAMERA':(50,90,0,18,0,8,0.15,0.6),
      'HIGH_CAMERA':(45,80,10,40,0,8,3.5,8.0), 'PORTRAIT':(45,85,0,25,0,12,0.5,2.5), 'OFFCENTER':(45,80,0,20,0,10,0.5,2.5),
      'NEAR_INFINITY':(35,60,0,2,0,1,1.0,2.0)}
    if profile not in bins: raise KeyError(profile)
    fov0,fov1,p0,p1,r0,r1,h0,h1=bins[profile]
    hfov=math.radians(r.uniform(fov0,fov1)); fx=(width-1)/(2*math.tan(hfov/2)); fy=fx
    cx=(width-1)/2; cy=(height-1)/2
    if profile=='OFFCENTER': cx += r.uniform(-0.18,0.18)*width; cy += r.uniform(-0.12,0.12)*height
    height_m=r.uniform(h0,h1); dist=r.uniform(4,14); yaw=r.uniform(-55,55); pitch=r.uniform(p0,p1)*(1 if r.random()>.5 else -1); roll=r.uniform(r0,r1)*(1 if r.random()>.5 else -1)
    ya=math.radians(yaw); pa=math.radians(pitch)
    target=(0.0,1.0,0.0); C=(dist*math.sin(ya),height_m+dist*math.sin(pa)*0.15,dist*math.cos(ya))
    pose=look_at(C,target,roll_deg=roll)
    return {'profile':profile,'width':width,'height':height,'K':K_matrix(fx,fy,cx,cy),'fx':fx,'fy':fy,'cx':cx,'cy':cy,'pose':pose,'sampled':{'hfov_deg':math.degrees(hfov),'yaw_deg':yaw,'pitch_bias_deg':pitch,'roll_deg':roll,'height_m':height_m,'distance_m':dist}}
