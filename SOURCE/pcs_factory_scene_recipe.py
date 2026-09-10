from __future__ import annotations
import math, random, json
from pcs_factory_seed import derive_seed, identity_digest
from pcs_factory_coordinates import unit, dot, cross, mat_vec, det3, frob_orthogonality_error
from pcs_factory_scene_truth import solvability_record, plane_from_point_normal, metric_anchor, SOLVABILITY_CLASSES
SCENE_SCHEMA='DF-G20-G31-SCENE-RECIPE-V1'

def I3(): return ((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))
def rot_y(deg):
    a=math.radians(float(deg)); c,s=math.cos(a),math.sin(a)
    return ((c,0.0,s),(0.0,1.0,0.0),(-s,0.0,c))
def rot_x(deg):
    a=math.radians(float(deg)); c,s=math.cos(a),math.sin(a)
    return ((1,0,0),(0,c,-s),(0,s,c))
def matmul(A,B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def transform_point(R,t,p):
    q=mat_vec(R,p); return tuple(q[i]+t[i] for i in range(3))

def box_edges(dim,R,t,object_id,frame_id='WORLD',structural=True):
    sx,sy,sz=[float(x)/2 for x in dim]
    corners=[(-sx,-sy,-sz),(sx,-sy,-sz),(sx,-sy,sz),(-sx,-sy,sz),(-sx,sy,-sz),(sx,sy,-sz),(sx,sy,sz),(-sx,sy,sz)]
    wc=[transform_point(R,t,p) for p in corners]
    pairs=[(0,1,'LX'),(1,2,'LZ'),(2,3,'LX'),(3,0,'LZ'),(4,5,'LX'),(5,6,'LZ'),(6,7,'LX'),(7,4,'LZ'),(0,4,'LY'),(1,5,'LY'),(2,6,'LY'),(3,7,'LY')]
    axis={'LX':mat_vec(R,(1,0,0)),'LY':mat_vec(R,(0,1,0)),'LZ':mat_vec(R,(0,0,1))}
    out=[]
    for k,(a,b,la) in enumerate(pairs):
        out.append({'line_id':f'{object_id}.e{k:02d}','object_id':object_id,'p0_world':wc[a],'p1_world':wc[b],'direction_world':unit(axis[la]),'direction_set_id':f'{frame_id}:{la}','structural':bool(structural)})
    return out

def make_box(object_id,primitive,center,dimensions,rotation_y_deg=0.0,rotation_x_deg=0.0,frame_id='WORLD',structural=True,role=None):
    dims=tuple(map(float,dimensions))
    if any(d<=0 for d in dims): raise ValueError('positive dimensions required')
    R=matmul(rot_y(rotation_y_deg),rot_x(rotation_x_deg))
    t=tuple(map(float,center))
    return {'object_id':object_id,'primitive':primitive,'center_world':t,'dimensions_m':dims,'R_local_to_world':R,'local_frame_id':frame_id,'structural':bool(structural),'role':role,'edges':box_edges(dims,R,t,object_id,frame_id,structural)}

def make_scene(base_scene_id,family,seed,objects,planes=None,anchors=None,solvability_class='SOLVABLE_3VP',modifiers=None,notes=None):
    direction_ids=sorted({e['direction_set_id'] for o in objects for e in o.get('edges',[]) if e.get('structural')})
    dirs=[]
    for did in direction_ids:
        for o in objects:
            hit=next((e for e in o.get('edges',[]) if e.get('structural') and e['direction_set_id']==did),None)
            if hit: dirs.append(hit['direction_world']); break
    sol=solvability_record(solvability_class,dirs,[sum(1 for o in objects for e in o.get('edges',[]) if e.get('structural') and e['direction_set_id']==did) for did in direction_ids])
    core={'schema':SCENE_SCHEMA,'base_scene_id':base_scene_id,'scene_family':family,'root_seed_u64':int(seed),'units':'meter','objects':objects,'planes':planes or [],'metric_anchors':anchors or [],'direction_set_ids':direction_ids,'solvability':sol,'modifiers':modifiers or [],'notes':notes,'split_family_key':base_scene_id}
    core['recipe_digest_sha256']=identity_digest(core)
    return core

def _room(base,seed,corridor=False):
    r=random.Random(seed); w=r.uniform(6,11); d=r.uniform(6,12); h=r.uniform(2.7,4.2); objs=[]
    objs += [make_box(f'{base}.floor','FLOOR_PLANE',(0,-0.1,0),(w,0.2,d),role='GROUND'),make_box(f'{base}.ceil','CEILING_PANEL',(0,h+0.1,0),(w,0.2,d),role='CEILING')]
    th=0.18
    objs += [make_box(f'{base}.wallN','WALL_PANEL',(0,h/2,-d/2),(w,h,th)),make_box(f'{base}.wallS','WALL_PANEL',(0,h/2,d/2),(w,h,th)),make_box(f'{base}.wallE','WALL_PANEL',(w/2,h/2,0),(th,h,d)),make_box(f'{base}.wallW','WALL_PANEL',(-w/2,h/2,0),(th,h,d))]
    if corridor:
        for i in range(4): objs.append(make_box(f'{base}.door{i}','DOOR_OPENING_PROXY',(-w/2+0.12,1.1,-d/3+i*d/5),(0.25,2.2,1.0),structural=False))
    for i in range(3):
        x=r.uniform(-w*.3,w*.3); z=r.uniform(-d*.3,d*.3); objs.append(make_box(f'{base}.prop{i}','BOX',(x,r.uniform(.35,.7),z),(r.uniform(.6,1.6),r.uniform(.7,1.4),r.uniform(.6,1.6)),structural=False,role='CLUTTER_PROXY'))
    pl=[{'plane_id':f'{base}.ground',**plane_from_point_normal((0,0,0),(0,1,0)),'role':'GROUND'}]
    return objs,pl

def _urban(base,seed,intersection=False):
    r=random.Random(seed); objs=[make_box(f'{base}.road','ROAD_PLANE',(0,-.08,0),(16,.16,30),role='GROUND')]
    for side,x in [('L',-7.0),('R',7.0)]:
        for i in range(5):
            z=-12+i*6+r.uniform(-.5,.5); hh=r.uniform(5,14); ww=r.uniform(4,6); dd=r.uniform(3.5,6)
            objs.append(make_box(f'{base}.b{side}{i}','BOX',(x,hh/2,z),(ww,hh,dd),rotation_y_deg=r.uniform(-4,4),frame_id='URBAN_MAIN'))
    if intersection: objs.append(make_box(f'{base}.crossroad','ROAD_PLANE',(0,-.06,0),(30,.12,8),rotation_y_deg=90,role='GROUND'))
    for i in range(6): objs.append(make_box(f'{base}.pole{i}','POLE',((-5 if i%2==0 else 5),1.6,-12+i*4),(0.16,3.2,0.16),structural=False))
    pl=[{'plane_id':f'{base}.ground',**plane_from_point_normal((0,0,0),(0,1,0)),'role':'GROUND'}]
    return objs,pl

def _industrial(base,seed):
    r=random.Random(seed); objs=[make_box(f'{base}.floor','FLOOR_PLANE',(0,-.1,0),(18,.2,24),role='GROUND')]
    for i in range(5):
        z=-10+i*5
        for x in (-7,7): objs.append(make_box(f'{base}.col{i}_{x}','COLUMN',(x,3,z),(.45,6,.45)))
        objs.append(make_box(f'{base}.beam{i}','BEAM',(0,5.5,z),(14,.35,.35)))
    for j in range(4): objs.append(make_box(f'{base}.rack{j}','SHELF',(-3+j*2,1.7,2),(1.3,3.4,5),structural=True))
    return objs,[{'plane_id':f'{base}.ground',**plane_from_point_normal((0,0,0),(0,1,0)),'role':'GROUND'}]

def _stairs(base,seed):
    objs=[make_box(f'{base}.ground','FLOOR_PLANE',(0,-.08,0),(12,.16,12),role='GROUND')]
    n=10; rise=.18; run=.32
    for i in range(n): objs.append(make_box(f'{base}.step{i}','STAIR_FLIGHT_PROXY',(0,(i+.5)*rise,-2+i*run),(3,rise,run)))
    objs.append(make_box(f'{base}.landing','LANDING',(0,n*rise+.1,1.5),(4,.2,3)))
    objs.append(make_box(f'{base}.ramp','RAMP',(4,1.0,0),(2,.25,7),rotation_x_deg=-15,frame_id='RAMP_FRAME'))
    return objs,[{'plane_id':f'{base}.groundP',**plane_from_point_normal((0,0,0),(0,1,0)),'role':'GROUND'}]

def _nonmanhattan(base,seed):
    r=random.Random(seed); objs=[]
    for k,a in enumerate([0,27,-38,62]):
        x=-6+k*4; hh=r.uniform(3,6); objs.append(make_box(f'{base}.cluster{k}','BOX',(x,hh/2,0),(3,hh,6),rotation_y_deg=a,frame_id=f'LOCAL{k}'))
    objs.append(make_box(f'{base}.ground','FLOOR_PLANE',(0,-.1,0),(20,.2,16),role='GROUND'))
    return objs,[{'plane_id':f'{base}.groundP',**plane_from_point_normal((0,0,0),(0,1,0)),'role':'GROUND'}]

def _sparse(base,seed):
    objs=[make_box(f'{base}.ground','FLOOR_PLANE',(0,-.1,0),(18,.2,18),role='GROUND'),make_box(f'{base}.wall','WALL_PANEL',(0,2,-5),(12,4,.2))]
    return objs,[{'plane_id':f'{base}.groundP',**plane_from_point_normal((0,0,0),(0,1,0)),'role':'GROUND'}]

def _repeated(base,seed):
    objs=[make_box(f'{base}.ground','FLOOR_PLANE',(0,-.1,0),(16,.2,16),role='GROUND'),make_box(f'{base}.facade','WALL_PANEL',(0,4,-5),(14,8,.3))]
    for iy in range(3):
        for ix in range(5): objs.append(make_box(f'{base}.window{iy}_{ix}','WINDOW_OPENING_PROXY',(-5+ix*2.5,2+iy*2,-4.8),(1.4,1.1,.15),structural=False,role='REPEATED_CONFUSER'))
    return objs,[{'plane_id':f'{base}.groundP',**plane_from_point_normal((0,0,0),(0,1,0)),'role':'GROUND'}]

def _organic(base,seed):
    r=random.Random(seed); objs=[]
    for i in range(12): objs.append(make_box(f'{base}.blob{i}','ORGANIC_BLOB_PROXY',(r.uniform(-6,6),r.uniform(.2,1.5),r.uniform(-6,6)),(r.uniform(.4,2),r.uniform(.4,2.5),r.uniform(.4,2)),rotation_y_deg=r.uniform(0,180),structural=False,role='ORGANIC_PROXY'))
    return objs,[]

def _hybrid(base,seed):
    objs,pl=_room(base,seed)
    objs.append(make_box(f'{base}.hero','BOX',(2.5,2.2,0),(3.5,4.4,2.2),rotation_y_deg=32,frame_id='HERO_FRAME',structural=True,role='HERO_PROXY'))
    objs.append(make_box(f'{base}.foreground','BOX',(-4,1.8,4),(4,3.6,1),rotation_y_deg=-18,frame_id='FG_FRAME',structural=False,role='FOREGROUND_SILHOUETTE'))
    return objs,pl

def generate_archetype(family,index=0,root_seed=34620260905):
    s=derive_seed(root_seed,'scene-family',family,index)['seed_u64']; base=f'{family.lower()}_{index:04d}'
    if family=='INTERIOR': objs,pl=_room(base,s,False); sol='SOLVABLE_3VP'; mods=[]
    elif family=='CORRIDOR': objs,pl=_room(base,s,True); sol='SOLVABLE_2VP_LIKE'; mods=['NARROW_CORRIDOR']
    elif family=='URBAN': objs,pl=_urban(base,s,False); sol='SOLVABLE_3VP'; mods=[]
    elif family=='INTERSECTION': objs,pl=_urban(base,s,True); sol='MULTIPLE_LOCAL_FRAMES'; mods=['CROSS_STREET']
    elif family=='INDUSTRIAL': objs,pl=_industrial(base,s); sol='REPEATED_PATTERN_AMBIGUITY'; mods=['REPEATED_BAYS']
    elif family=='STAIRS_RAMPS': objs,pl=_stairs(base,s); sol='MULTIPLE_LOCAL_FRAMES'; mods=['SLOPED_STRUCTURE']
    elif family=='NON_MANHATTAN': objs,pl=_nonmanhattan(base,s); sol='NON_MANHATTAN'; mods=['MULTI_ORIENTATION']
    elif family=='SPARSE': objs,pl=_sparse(base,s); sol='INSUFFICIENT_VISIBLE_STRUCTURE'; mods=['WEAK_STRUCTURE']
    elif family=='CLUTTER': objs,pl=_room(base,s); sol='WEAK_THIRD_AXIS'; mods=['HEAVY_CLUTTER'];
    elif family=='REPEATED_PATTERN': objs,pl=_repeated(base,s); sol='REPEATED_PATTERN_AMBIGUITY'; mods=[]
    elif family=='ORGANIC_NEGATIVE': objs,pl=_organic(base,s); sol='ORGANIC_NEGATIVE'; mods=[]
    elif family=='HYBRID_CONCEPT': objs,pl=_hybrid(base,s); sol='MULTIPLE_LOCAL_FRAMES'; mods=['HERO_COMPOSITION']
    else: raise KeyError(family)
    anchors=[]
    if pl: anchors=[metric_anchor(f'{base}.height_anchor',(0,0,0),(0,2.5,0),plane_id=pl[0]['plane_id'])]
    return make_scene(base,family,s,objs,pl,anchors,sol,mods)

CANONICAL_FAMILIES=['INTERIOR','CORRIDOR','URBAN','INTERSECTION','INDUSTRIAL','STAIRS_RAMPS','NON_MANHATTAN','SPARSE','CLUTTER','REPEATED_PATTERN','ORGANIC_NEGATIVE','HYBRID_CONCEPT']

def validate_scene(scene):
    findings=[]; ids=[]; plane_ids={p['plane_id'] for p in scene.get('planes',[])}
    for o in scene.get('objects',[]):
        oid=o.get('object_id'); ids.append(oid)
        if not oid: findings.append('MISSING_OBJECT_ID')
        if any((not math.isfinite(float(d)) or float(d)<=0) for d in o.get('dimensions_m',[])): findings.append('BAD_DIMENSIONS:'+str(oid))
        R=o.get('R_local_to_world')
        if R is None or frob_orthogonality_error(R)>1e-9 or abs(det3(R)-1)>1e-9: findings.append('BAD_ROTATION:'+str(oid))
        for e in o.get('edges',[]):
            ids.append(e.get('line_id')); p0=e['p0_world'];p1=e['p1_world']; d=unit(tuple(p1[i]-p0[i] for i in range(3)))
            if abs(abs(dot(d,e['direction_world']))-1)>1e-9: findings.append('EDGE_DIRECTION_MISMATCH:'+e['line_id'])
    if len(ids)!=len(set(ids)): findings.append('DUPLICATE_ID')
    for a in scene.get('metric_anchors',[]):
        if a.get('plane_id') and a['plane_id'] not in plane_ids: findings.append('DANGLING_ANCHOR_PLANE:'+a['anchor_id'])
    if scene.get('solvability',{}).get('class') not in SOLVABILITY_CLASSES: findings.append('BAD_SOLVABILITY')
    digest=scene.get('recipe_digest_sha256'); clone=dict(scene); clone.pop('recipe_digest_sha256',None)
    if digest!=identity_digest(clone): findings.append('RECIPE_DIGEST_MISMATCH')
    return {'schema':'DF-G20-G31-SCENE-VALIDATION-V1','status':'PASS' if not findings else 'FAIL','findings':findings,'object_count':len(scene.get('objects',[])),'structural_edge_count':sum(1 for o in scene.get('objects',[]) for e in o.get('edges',[]) if e.get('structural')),'plane_count':len(scene.get('planes',[])),'direction_set_count':len(scene.get('direction_set_ids',[]))}
