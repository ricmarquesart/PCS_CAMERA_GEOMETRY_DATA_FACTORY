from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'SOURCE' / 'pcs_factory_micro100_gt.py'
MARKER = "PHASE3_CANDIDATE_B_METHOD_ID = 'DF_G101_POST_R2_GEOMETRY_SEEDED_SUBPIXEL_VISIBILITY_REFERENCE_B_V1'"

CONSTANT_ANCHOR = "R18_GRID_INDICES = tuple(range(-4,5))\n"
CONSTANTS = r'''
PHASE3_CANDIDATE_B_METHOD_ID = 'DF_G101_POST_R2_GEOMETRY_SEEDED_SUBPIXEL_VISIBILITY_REFERENCE_B_V1'
PHASE3_CANDIDATE_B_RETENTION_FLOOR = 0.9783428720083247
PHASE3_CANDIDATE_B_LATTICE_STEP_PX = 1.0 / 16.0
PHASE3_CANDIDATE_B_DYADIC_JS = tuple(range(5,17))
PHASE3_CANDIDATE_B_SPEC_DRIVE_ID = '1ZYv-PuMeUJgUI74RcSixK8npdPdtFfYWQZo2EYw1wwY'
PHASE3_CANDIDATE_B_FULL_DOMAIN_SPEC_DRIVE_ID = '1kAlIHgWv6-vxkUsTV18H9zcytIYdzB55zA7KusFFmWw'
PHASE3_CANDIDATE_B_REASON_PRIORITY = {
    'IMAGE_BOUND_SUPPORT_INCOMPLETE':1,
    'SUBPIXEL_THIN_OCCLUDER_SUPPORT':2,
    'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT':3,
    'CONTINUOUS_FACE_NORMAL_DISCONTINUITY_SUPPORT':4,
    'CONTINUOUS_OBJECT_SILHOUETTE_SUPPORT':5,
    'UNCLASSIFIED_ANALYTIC_AMBIGUITY':6,
}
_PHASE3_CANDIDATE_B_SIGNS = tuple(
    (sx,sy,sz) for sx in (-1.0,1.0) for sy in (-1.0,1.0) for sz in (-1.0,1.0)
)
_PHASE3_CANDIDATE_B_EDGE_PAIRS = tuple(
    (i,j) for i,a in enumerate(_PHASE3_CANDIDATE_B_SIGNS)
    for j,b in enumerate(_PHASE3_CANDIDATE_B_SIGNS)
    if j>i and sum(1 for aa,bb in zip(a,b) if aa!=bb)==1
)
'''

HELPER_ANCHOR = "def _r21_normal_eval_for_K(request, C, raw, oid, objmask, filter_radius, K_override):\n"
HELPERS = r'''
def _phase3_b_batch_signatures(request, uv, K_override=None, chunk=80000):
    """Candidate-B arbitrary-ray analytic visibility signatures.

    This Normal-only helper consumes scene/camera geometry only. It deliberately
    does not accept rendered Normal/RGB/outcome/sample identity inputs.
    """
    _require_numpy()
    uv=np.asarray(uv,dtype=np.float64)
    if uv.ndim!=2 or uv.shape[1]!=2:
        raise RuntimeError('G100_PHASE3_B_UV_SHAPE')
    K=np.asarray(request['camera']['K'] if K_override is None else K_override,dtype=np.float64)
    C=np.asarray(request['camera']['pose']['camera_center_world'],dtype=np.float64)
    Rcw=np.asarray(request['camera']['pose']['R_world_to_camera_cv'],dtype=np.float64).T
    plane=_r19_face_plane_signatures(request)
    nall=len(uv); OO=np.empty(nall,dtype=np.int32); FF=np.empty(nall,dtype=np.int16); AA=np.zeros(nall,dtype=bool)
    for s0 in range(0,nall,int(chunk)):
        u=uv[s0:s0+int(chunk)]; n=len(u)
        dcv=np.column_stack([(u[:,0]-K[0,2])/K[0,0],(u[:,1]-K[1,2])/K[1,1],np.ones(n,dtype=np.float64)])
        dwb=dcv@Rcw.T
        Ts=[]; Fs=[]
        for obj in request['scene']['objects']:
            t,_nc,face=_object_hit_surface(C,dwb[:,None,:],obj)
            Ts.append(t[:,0]); Fs.append(face[:,0])
        if not Ts:
            OO[s0:s0+n]=0; FF[s0:s0+n]=-1
            continue
        T=np.stack(Ts,axis=1); F=np.stack(Fs,axis=1)
        mt=np.min(T,axis=1); idx=np.argmin(T,axis=1)
        oo=np.where(np.isfinite(mt),idx+1,0).astype(np.int32)
        ff=np.where(np.isfinite(mt),F[np.arange(n),idx],-1).astype(np.int16)
        eq=(T==mt[:,None]) & np.isfinite(T)
        for ii in np.where(eq.sum(axis=1)>1)[0]:
            js=np.where(eq[ii])[0]
            sigs={(int(j+1),int(F[ii,j])) for j in js}
            planes={plane[j][int(F[ii,j])] for j in js if int(F[ii,j])>=0}
            if len(planes)>1:
                AA[s0+ii]=True
            elif sigs:
                oo[ii],ff[ii]=min(sigs)
        OO[s0:s0+n]=oo; FF[s0:s0+n]=ff
    return OO,FF,AA


def _phase3_b_analytic_centers(request,K_override=None):
    h=int(request['camera']['height']); w=int(request['camera']['width'])
    yy,xx=np.indices((h,w),dtype=np.float64)
    o,f,a=_phase3_b_batch_signatures(request,np.column_stack([xx.ravel(),yy.ravel()]),K_override)
    return o.reshape(h,w),f.reshape(h,w),a.reshape(h,w)


def _phase3_b_clip_segment(p0,p1,x0,x1,y0,y1):
    d=p1-p0; t0=0.0; t1=1.0
    for p,q in ((-d[0],p0[0]-x0),(d[0],x1-p0[0]),(-d[1],p0[1]-y0),(d[1],y1-p0[1])):
        if p==0.0:
            if q<0.0:return None
        else:
            r=q/p
            if p<0.0:t0=max(t0,r)
            else:t1=min(t1,r)
            if t0>t1:return None
    return p0+t0*d,p0+t1*d


def _phase3_b_projected_edges(request,K_override=None):
    _require_numpy()
    K=np.asarray(request['camera']['K'] if K_override is None else K_override,dtype=np.float64)
    Rwc=np.asarray(request['camera']['pose']['R_world_to_camera_cv'],dtype=np.float64)
    twc=np.asarray(request['camera']['pose']['t_world_to_camera_cv'],dtype=np.float64)
    signs=np.asarray(_PHASE3_CANDIDATE_B_SIGNS,dtype=np.float64); out=[]
    for oi,obj in enumerate(request['scene']['objects'],1):
        R=np.asarray(obj['R_local_to_world'],dtype=np.float64); ctr=np.asarray(obj['center_world'],dtype=np.float64)
        half=np.asarray(obj['dimensions_m'],dtype=np.float64)/2.0
        vertices=(signs*half)@R.T+ctr; cam=vertices@Rwc.T+twc; validz=cam[:,2]>1e-12
        with np.errstate(divide='ignore',invalid='ignore'):
            uv=np.column_stack([K[0,0]*cam[:,0]/cam[:,2]+K[0,2],K[1,1]*cam[:,1]/cam[:,2]+K[1,2]])
        for edge_index,(a,b) in enumerate(_PHASE3_CANDIDATE_B_EDGE_PAIRS):
            if not validz[a] and not validz[b]:continue
            out.append((oi,edge_index,uv[a].copy(),uv[b].copy()))
    return tuple(out)


def _phase3_b_reason_for_transition(center,other,rendered_oid,x,y,h,w,ambiguous=False):
    if ambiguous:return 'UNCLASSIFIED_ANALYTIC_AMBIGUITY'
    if other==center:return None
    if other[0]!=center[0]:
        if other[0]==0 or center[0]==0:return 'CONTINUOUS_OBJECT_SILHOUETTE_SUPPORT'
        nh=rendered_oid[max(0,y-2):min(h,y+3),max(0,x-2):min(w,x+3)]
        if not np.any(nh==other[0]):return 'SUBPIXEL_THIN_OCCLUDER_SUPPORT'
        return 'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT'
    if other[1]!=center[1]:return 'CONTINUOUS_FACE_NORMAL_DISCONTINUITY_SUPPORT'
    return None


def _phase3_b_choose_reason(reasons):
    vals=[r for r in reasons if r]
    return min(vals,key=lambda r:PHASE3_CANDIDATE_B_REASON_PRIORITY[r]) if vals else None


def _phase3_b_edge_pairs(request,old_safe,K_override=None):
    h,w=old_safe.shape; out=[]; touched=set(); fw=G100_CYCLES_FILTER_WIDTH_PX
    for oi,edge_index,p0,p1 in _phase3_b_projected_edges(request,K_override):
        xmin=max(0,int(math.ceil(min(p0[0],p1[0])-fw-1e-12))); xmax=min(w-1,int(math.floor(max(p0[0],p1[0])+fw+1e-12)))
        ymin=max(0,int(math.ceil(min(p0[1],p1[1])-fw-1e-12))); ymax=min(h-1,int(math.floor(max(p0[1],p1[1])+fw+1e-12)))
        if xmin>xmax or ymin>ymax:continue
        pairs=[]
        for y in range(ymin,ymax+1):
            for x in range(xmin,xmax+1):
                if not old_safe[y,x]:continue
                clipped=_phase3_b_clip_segment(p0,p1,x-fw,x+fw,y-fw,y+fw)
                if clipped is not None:
                    pairs.append((x,y,clipped)); touched.add((x,y))
        if pairs:out.append((oi,edge_index,p0,p1,pairs))
    return out,touched


def _phase3_b_edge_witness_exclusions(request,old_safe,rendered_oid,center_o,center_f,K_override=None):
    old=np.asarray(old_safe,dtype=bool); oid=np.asarray(rendered_oid,dtype=np.int32); h,w=old.shape; fw=G100_CYCLES_FILTER_WIDTH_PX
    edge_groups,touched=_phase3_b_edge_pairs(request,old,K_override); evidence={}; pair_count=0
    for oi,edge_index,p0,p1,pairs in edge_groups:
        pair_count+=len(pairs); edge=p1-p0; n=np.asarray([-edge[1],edge[0]],dtype=np.float64); nl=float(np.linalg.norm(n))
        if nl==0.0:continue
        n/=nl
        if not (n[0]>0.0 or (n[0]==0.0 and n[1]>=0.0)):n=-n
        probes=[]; meta=[]
        for pi,(x,y,(a,b)) in enumerate(pairs):
            d=b-a; L=float(np.linalg.norm(d)); qs=[a.copy()] if L==0.0 else [a+t*d for t in (0.25,0.5,0.75)]
            for q_index,q in enumerate(qs):
                for j in PHASE3_CANDIDATE_B_DYADIC_JS:
                    dist=fw/(2**j); qp=q+dist*n; qm=q-dist*n
                    ok=(x-fw-1e-12<=qp[0]<=x+fw+1e-12 and y-fw-1e-12<=qp[1]<=y+fw+1e-12 and 0.0<=qp[0]<=w-1 and 0.0<=qp[1]<=h-1 and x-fw-1e-12<=qm[0]<=x+fw+1e-12 and y-fw-1e-12<=qm[1]<=y+fw+1e-12 and 0.0<=qm[0]<=w-1 and 0.0<=qm[1]<=h-1)
                    if ok:
                        k=len(probes); probes.extend([qp,qm]); meta.append((pi,q_index,j,dist,k))
        if not probes:continue
        po,pf,pa=_phase3_b_batch_signatures(request,np.asarray(probes,dtype=np.float64),K_override)
        best=[None]*len(pairs)
        for pi,q_index,j,dist,k in meta:
            x,y,_=pairs[pi]; center=(int(center_o[y,x]),int(center_f[y,x])); sp=(int(po[k]),int(pf[k])); sm=(int(po[k+1]),int(pf[k+1])); ambiguous=bool(pa[k] or pa[k+1])
            if not ambiguous and not (sp!=sm and (sp!=center or sm!=center)):continue
            if ambiguous:reason='UNCLASSIFIED_ANALYTIC_AMBIGUITY'
            else:
                reason=_phase3_b_choose_reason([
                    _phase3_b_reason_for_transition(center,sp,oid,x,y,h,w) if sp!=center else None,
                    _phase3_b_reason_for_transition(center,sm,oid,x,y,h,w) if sm!=center else None,
                ]) or 'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT'
            witness={'reason':reason,'edge_object_id':int(oi),'edge_index':int(edge_index),'q_index':int(q_index),'dyadic_j':int(j),'distance_px':float(dist),'plus_signature':sp,'minus_signature':sm}
            if best[pi] is None or PHASE3_CANDIDATE_B_REASON_PRIORITY[reason]<PHASE3_CANDIDATE_B_REASON_PRIORITY[best[pi]['reason']]:best[pi]=witness
        for pi,witness in enumerate(best):
            if witness is None:continue
            x,y,_=pairs[pi]; p=(x,y)
            if p not in evidence or PHASE3_CANDIDATE_B_REASON_PRIORITY[witness['reason']]<PHASE3_CANDIDATE_B_REASON_PRIORITY[evidence[p]['reason']]:evidence[p]=witness
    return evidence,touched,pair_count


def _phase3_candidate_b_require_retention(old_count,new_count,floor=PHASE3_CANDIDATE_B_RETENTION_FLOOR):
    old_count=int(old_count); new_count=int(new_count)
    if old_count<0 or new_count<0 or new_count>old_count:raise RuntimeError('G100_PHASE3_B_RETENTION_COUNT_INVALID')
    value=float(new_count/old_count) if old_count else 1.0
    if old_count and value<float(floor):
        raise RuntimeError('G100_PHASE3_CANDIDATE_B_RETENTION_BELOW_FROZEN_FLOOR:'+str(value))
    return value


def _phase3_candidate_b_normal_safe_mask(request,inherited_old_safe,rendered_oid,K_override=None,renderer_filter_width_px=G100_CYCLES_FILTER_WIDTH_PX,lattice_batch_pixels=32):
    """Production Candidate-B correction for Normal FILTER_SAFE_INTERIOR only.

    The caller supplies the inherited discrete R6 Normal-safe mask. This function
    can only remove authority from that mask. It never mutates or replaces the
    shared R29 Depth mask path and never participates in K selection.
    """
    _require_numpy()
    fw=float(renderer_filter_width_px)
    if not np.isfinite(fw) or abs(fw-G100_CYCLES_FILTER_WIDTH_PX)>1e-12:
        raise RuntimeError('G100_PHASE3_B_RENDER_FILTER_WIDTH_MISMATCH:'+json.dumps({'expected':G100_CYCLES_FILTER_WIDTH_PX,'actual':fw},sort_keys=True))
    old=np.asarray(inherited_old_safe,dtype=bool); oid=np.asarray(rendered_oid,dtype=np.int32)
    if old.shape!=oid.shape:raise RuntimeError('G100_PHASE3_B_MASK_SHAPE_MISMATCH')
    h,w=old.shape
    if (w,h)!=(int(request['camera']['width']),int(request['camera']['height'])):raise RuntimeError('G100_PHASE3_B_RASTER_MISMATCH')
    center_o,center_f,center_a=_phase3_b_analytic_centers(request,K_override)
    safe=old.copy(); reasons={}; evidence={}
    for y,x in np.argwhere(old):
        x=int(x); y=int(y)
        if x-fw<0.0 or x+fw>w-1 or y-fw<0.0 or y+fw>h-1:
            safe[y,x]=False; reasons[(x,y)]='IMAGE_BOUND_SUPPORT_INCOMPLETE'
        elif center_a[y,x]:
            safe[y,x]=False; reasons[(x,y)]='UNCLASSIFIED_ANALYTIC_AMBIGUITY'
    witness,touched,pair_count=_phase3_b_edge_witness_exclusions(request,old,oid,center_o,center_f,K_override)
    for p,ev in witness.items():
        x,y=p; safe[y,x]=False; reasons[p]=ev['reason']; evidence[p]=ev
    evalpix=sorted((p for p in touched if safe[p[1],p[0]]),key=lambda p:(p[1],p[0]))
    offs=np.asarray([-fw+k*PHASE3_CANDIDATE_B_LATTICE_STEP_PX for k in range(49)],dtype=np.float64)
    du,dv=np.meshgrid(offs,offs,indexing='xy'); delta=np.column_stack([du.ravel(),dv.ravel()]); lattice_only=0
    batch=max(1,int(lattice_batch_pixels))
    for s0 in range(0,len(evalpix),batch):
        pp=evalpix[s0:s0+batch]; base=np.asarray(pp,dtype=np.float64); pts=(base[:,None,:]+delta[None,:,:]).reshape(-1,2)
        bo,bf,ba=_phase3_b_batch_signatures(request,pts,K_override)
        bo=bo.reshape(len(pp),-1); bf=bf.reshape(len(pp),-1); ba=ba.reshape(len(pp),-1)
        for i,(x,y) in enumerate(pp):
            center=(int(center_o[y,x]),int(center_f[y,x]))
            if bool(np.any(ba[i])):
                reason='UNCLASSIFIED_ANALYTIC_AMBIGUITY'; detail={'lattice_ambiguity':True}
            else:
                diff=(bo[i]!=center[0]) | (bf[i]!=center[1])
                if not np.any(diff):continue
                k=int(np.flatnonzero(diff)[0]); other=(int(bo[i,k]),int(bf[i,k]))
                reason=_phase3_b_reason_for_transition(center,other,oid,x,y,h,w) or 'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT'
                detail={'lattice_signature':other,'lattice_index':k}
            safe[y,x]=False; reasons[(x,y)]=reason; evidence[(x,y)]={'reason':reason,**detail}; lattice_only+=1
    old_count=int(np.count_nonzero(old)); new_count=int(np.count_nonzero(safe)); retention=_phase3_candidate_b_require_retention(old_count,new_count)
    counts={}
    for r in reasons.values():counts[r]=counts.get(r,0)+1
    reason_rows=sorted((f'{x},{y}',r) for (x,y),r in reasons.items())
    reason_digest=hashlib.sha256(json.dumps(reason_rows,separators=(',',':')).encode('utf-8')).hexdigest()
    mask_digest=hashlib.sha256(safe.astype(np.uint8).tobytes(order='C')).hexdigest()
    result={
        'schema':'DF-G101-PHASE3-CANDIDATE-B-PRODUCTION-V1','method_id':PHASE3_CANDIDATE_B_METHOD_ID,
        'spec_drive_id':PHASE3_CANDIDATE_B_SPEC_DRIVE_ID,'full_domain_spec_drive_id':PHASE3_CANDIDATE_B_FULL_DOMAIN_SPEC_DRIVE_ID,
        'old_safe_count':old_count,'new_safe_count':new_count,'excluded_count':old_count-new_count,'retained_fraction':retention,
        'retention_floor':PHASE3_CANDIDATE_B_RETENTION_FLOOR,'mask_sha256':mask_digest,'reason_counts':counts,'reason_digest_sha256':reason_digest,
        'edge_touched_old_safe_count':len(touched),'edge_pixel_pairs':int(pair_count),'witness_exclusion_count':len(witness),'lattice_only_exclusion_count':int(lattice_only),
        'selection_inputs':'ANALYTIC_SCENE_CAMERA_PLUS_RENDERED_OBJECT_INDEX_CLASSIFICATION_ONLY',
        'rendered_normal_used_in_selection':False,'rgb_used_in_selection':False,'acceptance_used_in_selection':False,
        'sample_identity_used_in_selection':False,'full_domain_semantics':True,'depth_authority_mutated':False,'camera_binding_steered':False,
        'reason_by_pixel':reasons,'evidence_by_pixel':evidence,
    }
    if int(counts.get('UNCLASSIFIED_ANALYTIC_AMBIGUITY',0)):
        raise RuntimeError('G100_PHASE3_CANDIDATE_B_UNCLASSIFIED_ANALYTIC_AMBIGUITY:'+str(counts['UNCLASSIFIED_ANALYTIC_AMBIGUITY']))
    return safe,result


'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f'{label}: expected exactly one anchor, got {count}')
    return text.replace(old,new,1)


def main() -> None:
    text=SOURCE.read_text(encoding='utf-8')
    if MARKER in text:
        print('GATE2_PRODUCTION_PATCH_ALREADY_APPLIED')
        return
    if CONSTANT_ANCHOR not in text or HELPER_ANCHOR not in text:
        raise RuntimeError('GATE2_SOURCE_BASELINE_ANCHOR_MISSING')

    text=replace_once(text,CONSTANT_ANCHOR,CONSTANT_ANCHOR+CONSTANTS+'\n','constant anchor')
    text=replace_once(text,HELPER_ANCHOR,HELPERS+HELPER_ANCHOR,'helper anchor')

    r21_start=text.index(HELPER_ANCHOR)
    r21_end=text.index('def _filter_safe_interior_mask',r21_start)
    r21=text[r21_start:r21_end]
    old="    filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)\n    filter_safe_count=int(filter_safe.sum())\n"
    new="    inherited_filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)\n    filter_safe,phase3_candidate_b=_phase3_candidate_b_normal_safe_mask(request,inherited_filter_safe,oid,K_override=K_override,renderer_filter_width_px=G100_CYCLES_FILTER_WIDTH_PX)\n    filter_safe_count=int(filter_safe.sum())\n"
    r21=replace_once(r21,old,new,'R21 Normal call site')
    r21=replace_once(r21,"        'boundary_explained_frac':boundary_explained_frac,\n    }\n","        'boundary_explained_frac':boundary_explained_frac,'phase3_candidate_b':phase3_candidate_b,\n    }\n",'R21 return metadata')
    text=text[:r21_start]+r21+text[r21_end:]

    validate_start=text.index('def validate_aux_gt')
    validate=text[validate_start:]
    old_initial="    filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)\n    filter_safe_count=int(filter_safe.sum())\n"
    new_initial="    inherited_filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)\n    filter_safe,phase3_candidate_b=_phase3_candidate_b_normal_safe_mask(request,inherited_filter_safe,oid,K_override=None,renderer_filter_width_px=filter_width)\n    filter_safe_count=int(filter_safe.sum())\n"
    validate=replace_once(validate,old_initial,new_initial,'canonical Normal call site')
    old_effective="        filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)\n        filter_safe_count=int(filter_safe.sum())\n"
    new_effective="        inherited_filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)\n        filter_safe,phase3_candidate_b=_phase3_candidate_b_normal_safe_mask(request,inherited_filter_safe,oid,K_override=K_norm,renderer_filter_width_px=filter_width)\n        filter_safe_count=int(filter_safe.sum())\n"
    validate=replace_once(validate,old_effective,new_effective,'effective-K Normal call site')
    validate=validate.replace("raw_err=ne['raw_err']; can_err=ne['can_err']; filter_safe=ne['filter_safe']\n","raw_err=ne['raw_err']; can_err=ne['can_err']; filter_safe=ne['filter_safe']; phase3_candidate_b=ne['phase3_candidate_b']\n")
    validate=validate.replace("filter_safe=ne['filter_safe']; filter_safe_count=ne['filter_safe_count']; filter_safe_auth_count=ne['filter_safe_auth_count']\n","filter_safe=ne['filter_safe']; phase3_candidate_b=ne['phase3_candidate_b']; filter_safe_count=ne['filter_safe_count']; filter_safe_auth_count=ne['filter_safe_auth_count']\n")
    if "phase3_candidate_b=ne['phase3_candidate_b']" not in validate:
        raise RuntimeError('Gate2 failed to wire R21/R23 metadata')
    validate=replace_once(validate,"        'acceptance_fraction_semantics':'FILTER_SAFE_INTERIOR_AUTHORITY_FRACTION_R6',\n","        'acceptance_fraction_semantics':'CONTINUOUS_CANDIDATE_B_FILTER_SAFE_INTERIOR_AUTHORITY_FRACTION_PHASE3',\n        'inherited_baseline_semantics':'FILTER_SAFE_INTERIOR_AUTHORITY_FRACTION_R6',\n",'Normal report semantics')
    report_anchor="        'renderer_filter_width_status':'PASS' if filter_width_ok else 'FAIL','filter_support_radius_px':filter_radius,\n"
    report_insert=report_anchor+"        'phase3_candidate_b_method_id':PHASE3_CANDIDATE_B_METHOD_ID,\n        'phase3_candidate_b_spec_drive_id':PHASE3_CANDIDATE_B_SPEC_DRIVE_ID,\n        'phase3_candidate_b_full_domain_spec_drive_id':PHASE3_CANDIDATE_B_FULL_DOMAIN_SPEC_DRIVE_ID,\n        'phase3_candidate_b_old_safe_pixels':phase3_candidate_b['old_safe_count'],\n        'phase3_candidate_b_new_safe_pixels':phase3_candidate_b['new_safe_count'],\n        'phase3_candidate_b_excluded_pixels':phase3_candidate_b['excluded_count'],\n        'phase3_candidate_b_retained_fraction':phase3_candidate_b['retained_fraction'],\n        'phase3_candidate_b_retention_floor':PHASE3_CANDIDATE_B_RETENTION_FLOOR,\n        'phase3_candidate_b_reason_counts':phase3_candidate_b['reason_counts'],\n        'phase3_candidate_b_reason_digest_sha256':phase3_candidate_b['reason_digest_sha256'],\n        'phase3_candidate_b_mask_sha256':phase3_candidate_b['mask_sha256'],\n        'phase3_candidate_b_edge_touched_old_safe_count':phase3_candidate_b['edge_touched_old_safe_count'],\n        'phase3_candidate_b_edge_pixel_pairs':phase3_candidate_b['edge_pixel_pairs'],\n        'phase3_candidate_b_witness_exclusion_count':phase3_candidate_b['witness_exclusion_count'],\n        'phase3_candidate_b_lattice_only_exclusion_count':phase3_candidate_b['lattice_only_exclusion_count'],\n        'phase3_candidate_b_full_domain_semantics':True,\n        'phase3_candidate_b_rendered_normal_used_in_selection':False,\n        'phase3_candidate_b_rgb_used_in_selection':False,\n        'phase3_candidate_b_acceptance_used_in_selection':False,\n        'phase3_candidate_b_sample_identity_used_in_selection':False,\n        'phase3_candidate_b_depth_authority_mutated':False,\n        'phase3_candidate_b_camera_binding_steered':False,\n"
    validate=replace_once(validate,report_anchor,report_insert,'Normal report Candidate-B provenance')
    text=text[:validate_start]+validate

    SOURCE.write_text(text,encoding='utf-8')
    print('GATE2_PRODUCTION_PATCH_APPLIED')


if __name__=='__main__':
    main()
