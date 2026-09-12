from __future__ import annotations
import math
import numpy as np

WIDTHS = (0.015625,0.03125,0.0625,0.125,0.25,0.5,0.75,1.0,1.5,2.0,2.1346979,3.0,5.0)
ULTRATHIN_WIDTHS = (0.0078125,0.001953125,0.00048828125,0.0001220703125,0.000030517578125)
ORIENTS = {'VERTICAL':0.0,'DIAGONAL':math.pi/4.0,'HORIZONTAL':math.pi/2.0}
PHASES = ((0.011,0.019),(0.023,0.037),(0.041,0.013),(0.053,0.047))


def rxyz(rx,ry,rz):
    cx,sx=math.cos(rx),math.sin(rx); cy,sy=math.cos(ry),math.sin(ry); cz,sz=math.cos(rz),math.sin(rz)
    rxm=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]],dtype=float)
    rym=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]],dtype=float)
    rzm=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]],dtype=float)
    return rzm@rym@rxm


def _project(K,pc):
    return np.array([K[0,0]*pc[0]/pc[2]+K[0,2],K[1,1]*pc[1]/pc[2]+K[1,2]],dtype=float)


def make_case(width_px, orient_name, occluded, idx):
    W=128; H=128; fx=(60.0,80.0,120.0)[idx%3]; fy=fx; cx=63.5; cy=63.5
    K=np.array([[fx,0,cx],[0,fy,cy],[0,0,1]],dtype=float)
    pitch=(-0.11,0.0,0.09)[idx%3]; yaw=(-0.13,0.04,0.12)[(idx//3)%3]; roll=(-0.08,0.03,0.10)[(idx//9)%3]
    Rwc=rxyz(pitch,yaw,roll); Rcw=Rwc.T; C=np.array([0.2,-0.15,0.35],dtype=float); twc=-Rwc@C
    z=(4.5,6.0,8.0)[(idx//2)%3]
    uoff=(-7.25,0.0,6.5)[(idx//4)%3]; voff=(-5.5,0.0,5.75)[(idx//5)%3]
    u0=cx+uoff; v0=cy+voff; thin_z=12.0 if occluded else z
    xcam=(u0-cx)/fx*thin_z; ycam=(v0-cy)/fy*thin_z
    theta=ORIENTS[orient_name]; Robj_cam=rxyz(0,0,theta)
    width_m=float(width_px)*thin_z/fx; length_m=3.8; depth_m=0.002
    def world_obj(oid,center_cam,dims,Rcam):
        center_world=Rcw@np.asarray(center_cam,dtype=float)+C; Rworld=Rcw@Rcam
        return {'object_id':oid,'center_world':center_world.tolist(),'dimensions_m':list(map(float,dims)),'R_local_to_world':Rworld.tolist()}
    bg=world_obj('synthetic.background',[0,0,10.0],[18,18,0.08],np.eye(3))
    thin=world_obj('synthetic.thin',[xcam,ycam,thin_z],[width_m,length_m,depth_m],Robj_cam)
    req={'sample_id':f'syn_{idx:03d}_{orient_name}_{"OCCLUDED" if occluded else "VISIBLE"}_{width_px}',
         'camera':{'width':W,'height':H,'K':K.tolist(),'pose':{'camera_center_world':C.tolist(),'R_world_to_camera_cv':Rwc.tolist(),'t_world_to_camera_cv':twc.tolist()}},
         'scene':{'objects':[bg,thin]}}
    a=Robj_cam@np.array([-width_m/2,0,0])+np.array([xcam,ycam,thin_z]); b=Robj_cam@np.array([width_m/2,0,0])+np.array([xcam,ycam,thin_z])
    ach=_project(K,a); bch=_project(K,b)
    meta={'target_width_px':float(width_px),'measured_cross_section_px':float(np.linalg.norm(ach-bch)),'center_uv':[u0,v0],'fx':fx,'thin_z':thin_z,'camera_euler_rad':[pitch,yaw,roll]}
    return req,meta


def special_case(name):
    W=128; H=128; fx=80.0; K=np.array([[fx,0,63.5],[0,fx,63.5],[0,0,1]],dtype=float); Rwc=np.eye(3); C=np.zeros(3); twc=np.zeros(3)
    def obj(oid,c,d,R=np.eye(3)):
        return {'object_id':oid,'center_world':list(map(float,c)),'dimensions_m':list(map(float,d)),'R_local_to_world':np.asarray(R,dtype=float).tolist()}
    bg=obj('background',[0,0,10],[18,18,.08]); objs=[bg]; meta={'center_uv':[63.5,63.5]}
    if name=='CREASE': objs=[obj('creasebox',[0,0,7],[4,4,2],rxyz(0,0.45,0.2)),bg]
    elif name=='OUTSIDE_SUPPORT':
        z=6.0; u=68.5; x=(u-63.5)/fx*z; objs=[bg,obj('thin.outside',[x,0,z],[0.02,3,.002],np.eye(3))]
    elif name=='COPLANAR_SPLIT': objs=[obj('left',[-2,0,10],[4,18,.08]),obj('right',[2,0,10],[4,18,.08])]
    elif name=='NONCOPLANAR_STEP': objs=[obj('near',[-2,0,9.5],[4,18,.08]),obj('far',[2,0,10.5],[4,18,.08])]
    req={'sample_id':'syn_special_'+name,'camera':{'width':W,'height':H,'K':K.tolist(),'pose':{'camera_center_world':C.tolist(),'R_world_to_camera_cv':Rwc.tolist(),'t_world_to_camera_cv':twc.tolist()}},'scene':{'objects':objs}}
    return req,meta


def iter_standard(orientation=None, occluded=None):
    idx=0
    for orient in ORIENTS:
        for width in WIDTHS:
            for occ in (False,True):
                req,meta=make_case(width,orient,occ,idx)
                if (orientation is None or orient==orientation) and (occluded is None or occ==occluded):
                    yield req,meta,('OCCLUDED' if occ else 'VISIBLE')
                idx+=1


def iter_ultrathin(orientation=None, occluded=None):
    idx=1000
    for orient in ORIENTS:
        for width in ULTRATHIN_WIDTHS:
            for occ in (False,True):
                req,meta=make_case(width,orient,occ,idx)
                if (orientation is None or orient==orientation) and (occluded is None or occ==occluded):
                    yield req,meta,('OCCLUDED' if occ else 'VISIBLE')
                idx+=1


def iter_phase_shift(orientation=None, occluded=None):
    idx=2000
    for orient in ORIENTS:
        for width in (0.000030517578125,0.0001220703125):
            for du,dv in PHASES:
                for occ in (False,True):
                    req,meta=make_case(width,orient,occ,idx)
                    Rwc=np.asarray(req['camera']['pose']['R_world_to_camera_cv'],dtype=float); Rcw=Rwc.T
                    fx=float(req['camera']['K'][0][0]); fy=float(req['camera']['K'][1][1]); z=float(meta['thin_z'])
                    shift=Rcw@np.array([du/fx*z,dv/fy*z,0.0],dtype=float)
                    req['scene']['objects'][1]['center_world']=(np.asarray(req['scene']['objects'][1]['center_world'],dtype=float)+shift).tolist()
                    meta=dict(meta); meta['center_uv']=[meta['center_uv'][0]+du,meta['center_uv'][1]+dv]
                    req['sample_id']=f'phase_{idx}_{orient}_{width}_{du}_{dv}_{occ}'
                    if (orientation is None or orient==orientation) and (occluded is None or occ==occluded):
                        yield req,meta,('OCCLUDED' if occ else 'VISIBLE')
                    idx+=1
