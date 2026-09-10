from __future__ import annotations
import hashlib, json, math, struct, zlib, os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# This module is imported by Blender's bundled Python. Blender 4.5.13 is expected
# to provide numpy. The dependency is fail-closed and is checked by the G100 preflight.
try:
    import numpy as np
except Exception as e:  # pragma: no cover in ordinary CPython package selftest
    np = None
    _NUMPY_IMPORT_ERROR = repr(e)
else:
    _NUMPY_IMPORT_ERROR = None

C_FROM_B = ((1.0,0.0,0.0),(0.0,0.0,1.0),(0.0,-1.0,0.0))
B_FROM_C = ((1.0,0.0,0.0),(0.0,0.0,-1.0),(0.0,1.0,0.0))
NORMAL_TOL = 1e-5
DEPTH_GEOM_TOL_M = 1e-4
NORMAL_GEOM_TOL = 1e-5
MIN_NORMAL_AUTHORITY_FRACTION = 0.90
RENDERER_PP_BINDING_MAX_PX = 0.001
RENDERER_PP_FD_EPS_PX = 1e-4
RENDERER_PP_MAX_ITERS = 3
RENDERER_PP_MIN_FIT_PIXELS = 1000
R3_ADDENDUM_DRIVE_ID = '1zTxwLTjw4KWG-Zy9DMjQW--RDNihqRMJPvFxtSJKdB0'
R4_ADDENDUM_DRIVE_ID = '1SsURu6T-equZR4vM1FZIsLf9erSSwdpy8NYpNhpiLf8'
R5_ADDENDUM_DRIVE_ID = '12lsY4Rvk6vlCaS6Z47NH3dbGzmkPj3deynHWyZgT62c'
R6_ADDENDUM_DRIVE_ID = '1aJbPlstezBMzHV3231_n3cdXvN6ZIMYV0SwdhxwVadw'
R7_ADDENDUM_DRIVE_ID = '1a4RMZ-4hrQW79EGNwYEvBgQZAazQWtgvrYwI0wwtKco'
R8_ADDENDUM_DRIVE_ID = '1H7WpHBr6_oXHQrBusEvzUjYIZzgKZAAeTBZVfnRxTEc'
R11_ADDENDUM_DRIVE_ID = '1LTqAivl2_XoofEfteWUEq-wy-gibI8JkJstkuSVVBEU'
R12_ADDENDUM_DRIVE_ID = '1FuzdzW-YD2VH7MAq-aCS-6fAEZbJqVlbXHe85VO6hd8'
G100_CYCLES_FILTER_WIDTH_PX = 1.5
VISIBILITY_TIE_IMPLEMENTATION_ID = 'EXACT_COPLANAR_CO_NEAREST_VISIBILITY_R4_V1'
RENDERER_BINDING_IMPLEMENTATION_ID = 'CYCLES_EFFECTIVE_PP_BOX_CONSTRAINED_R7_V1'
DEPTH_RESCUE_FITMASK_IMPLEMENTATION_ID = 'DEPTH_OBJECT_EXACT_IDENTITY_ALL_OBJECT_PIXELS_R8_V1'
VISIBILITY_BOOTSTRAP_IMPLEMENTATION_ID = 'CANONICAL_EXACT_SUBSET_TO_FULL_EFFECTIVE_EXACT_VISIBILITY_R11_V1'
NORMAL_VISIBLE_SIDE_IMPLEMENTATION_ID = 'RENDERER_VISIBLE_SIDE_CUBOID_NORMAL_R12_V1'
R18_REFINEMENT_IMPLEMENTATION_ID = 'CYCLES_EFFECTIVE_PP_MINIMAX_MICROGRID_R18_V1'
R19_VISIBILITY_IMPLEMENTATION_ID = 'EXACT_GEOMETRIC_COINCIDENT_FACE_VISIBILITY_R19_V1'
R19_NUMERIC_VISIBILITY_EPSILON = 0.0
R27_PLANE_SIGNATURE_IMPLEMENTATION_ID = 'SIGNED_PERMUTATION_CANONICAL_WORLD_PLANE_SIGNATURE_R27_V1'
R27_SIGNED_PERMUTATION_ULPS = 8
R27_SPEC_DRIVE_ID = '1x0EUv2o5vq7WYyV_YbebXOcGj1DKMb5h9DBaf7Et1KE'
R29_DEPTH_AUTHORITY_SEMANTICS_ID = 'FILTER_SAFE_INTERIOR_EXACT_DEPTH_R29_V1'
R29_SPEC_DRIVE_ID = '1_OkDftof9W8Eegc9GyOKhsBxQPWxFkkLUH1WWUwdmsM'
R29_ACTIVATION_SAMPLE_ID = 'g100v2_005_stairs_ramps_low_camera_blueprint'
R20_NORMAL_REFERENCE_IMPLEMENTATION_ID = 'RENDERER_EFFECTIVE_NORMAL_REFERENCE_R20_V1'
R18_MICROSTEP_PX = RENDERER_PP_FD_EPS_PX / 10.0
R18_GRID_INDICES = tuple(range(-4,5))


def _require_numpy():
    if np is None:
        raise RuntimeError('G100_BLENDER_NUMPY_UNAVAILABLE:' + str(_NUMPY_IMPORT_ERROR))


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()


def _header_bytes(data: bytes):
    off=8; attrs={}
    def cstr(o):
        e=data.index(b'\0',o); return data[o:e].decode(errors='replace'), e+1
    magic,ver=struct.unpack_from('<II',data,0)
    if magic != 20000630:
        raise RuntimeError(f'EXR_BAD_MAGIC:{magic}')
    while True:
        name,off=cstr(off)
        if not name: break
        typ,off=cstr(off); sz=struct.unpack_from('<I',data,off)[0]; off+=4
        attrs[name]=(typ,data[off:off+sz]); off+=sz
    return attrs,off,magic,ver


def _chlist(v: bytes):
    o=0; out=[]
    while o<len(v):
        e=v.index(b'\0',o); n=v[o:e].decode(); o=e+1
        if not n: break
        ptype=struct.unpack_from('<i',v,o)[0]; o+=4
        plinear=v[o]; o+=4
        xs,ys=struct.unpack_from('<ii',v,o); o+=8
        out.append({'name':n,'pixel_type':ptype,'xSampling':xs,'ySampling':ys,'pLinear':plinear})
    return out


def exr_header(path: Path):
    data=Path(path).read_bytes(); attrs,_end,magic,ver=_header_bytes(data)
    dw=struct.unpack('<4i',attrs['dataWindow'][1]); ch=_chlist(attrs['channels'][1])
    return {'magic':magic,'version':ver,'data_window':list(dw),'width':dw[2]-dw[0]+1,'height':dw[3]-dw[1]+1,
            'compression':attrs['compression'][1][0],'channels':ch,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def _undo_predictor(buf: bytes):
    b=bytearray(buf)
    for i in range(1,len(b)): b[i]=(b[i-1]+b[i]-128)&255
    return b


def _undo_reorder(buf: bytes):
    n=len(buf); out=bytearray(n); a=0; b=(n+1)//2
    for i in range(0,n,2):
        out[i]=buf[a]; a+=1
        if i+1<n: out[i+1]=buf[b]; b+=1
    return out


def decode_exr(path: Path):
    _require_numpy()
    data=Path(path).read_bytes(); attrs,hend,_magic,_ver=_header_bytes(data)
    xmin,ymin,xmax,ymax=struct.unpack('<4i',attrs['dataWindow'][1]); w=xmax-xmin+1; h=ymax-ymin+1
    comp=attrs['compression'][1][0]; lines={0:1,2:1,3:16}.get(comp)
    if lines is None: raise RuntimeError(f'UNSUPPORTED_EXR_COMPRESSION:{comp}')
    ch=_chlist(attrs['channels'][1]); nchunks=math.ceil(h/lines)
    offsets=[struct.unpack_from('<Q',data,hend+8*i)[0] for i in range(nchunks)]
    dtypes={0:('<u4',4),1:('<f2',2),2:('<f4',4)}
    arrs={c['name']:np.empty((h,w),dtype=np.dtype(dtypes[c['pixel_type']][0])) for c in ch}
    for coff in offsets:
        y0,sz=struct.unpack_from('<ii',data,coff); enc=data[coff+8:coff+8+sz]
        nlines=min(lines,ymax-y0+1); expected=0
        for yy in range(y0,y0+nlines):
            for c in ch:
                if (yy-ymin)%c['ySampling']: continue
                nx=(w+c['xSampling']-1)//c['xSampling']; expected+=nx*dtypes[c['pixel_type']][1]
        raw=bytearray(enc) if comp==0 else _undo_reorder(_undo_predictor(zlib.decompress(enc)))
        if len(raw)!=expected: raise RuntimeError(f'EXR_RAW_SIZE:{len(raw)}!={expected}')
        o=0
        for yy in range(y0,y0+nlines):
            iy=yy-ymin
            for c in ch:
                if iy%c['ySampling']: continue
                nx=(w+c['xSampling']-1)//c['xSampling']; nb=nx*dtypes[c['pixel_type']][1]
                vals=np.frombuffer(bytes(raw[o:o+nb]),dtype=dtypes[c['pixel_type']][0],count=nx); o+=nb
                arrs[c['name']][iy,::c['xSampling']][:nx]=vals
    return arrs


def _ray_grid(request, h, w, K_override=None):
    K=np.asarray(request['camera']['K'] if K_override is None else K_override,dtype=np.float64)
    Rcw=np.asarray(request['camera']['pose']['R_world_to_camera_cv'],dtype=np.float64).T
    yy,xx=np.indices((h,w),dtype=np.float64)
    dcv=np.stack([(xx-K[0,2])/K[0,0],(yy-K[1,2])/K[1,1],np.ones_like(xx)],axis=-1)
    dw=np.einsum('ij,hwj->hwi',Rcw,dcv)
    return dcv,dw


def _object_hit_surface(C, dw, obj):
    """Return analytic cuboid hit distance, outward normal and exact local-face id.

    face_id is 0..5 in axis/sign order and -1 where there is no finite hit.
    R6 uses this identity only to decide whether the Cycles reconstruction-filter
    footprint crosses an analytic surface discontinuity. It never consumes the
    rendered Normal values to construct the filter-safe mask.
    """
    R=np.asarray(obj['R_local_to_world'],dtype=np.float64); Rt=R.T
    ctr=np.asarray(obj['center_world'],dtype=np.float64); half=np.asarray(obj['dimensions_m'],dtype=np.float64)/2.0
    ol=Rt@(C-ctr); dl=np.einsum('ij,hwj->hwi',Rt,dw); h,w=dw.shape[:2]
    tnear=np.full((h,w),-np.inf); tfar=np.full((h,w),np.inf)
    for a in range(3):
        da=dl[...,a]; oa=ol[a]; par=np.abs(da)<1e-15
        outside=par & ((oa < -half[a]) | (oa > half[a]))
        den=np.where(par,1.0,da); t1=(-half[a]-oa)/den; t2=(half[a]-oa)/den
        lo=np.where(par,-np.inf,np.minimum(t1,t2)); hi=np.where(par,np.inf,np.maximum(t1,t2))
        lo=np.where(outside,np.inf,lo); hi=np.where(outside,-np.inf,hi)
        tnear=np.maximum(tnear,lo); tfar=np.minimum(tfar,hi)
    valid=tfar>=np.maximum(tnear,0.0); t=np.where(valid,np.where(tnear>0,tnear,tfar),np.inf)
    # Outward normal at analytic face.
    pl=ol[None,None,:]+dl*t[...,None]; residuals=[]; normals=[]
    for a in range(3):
        for s in (-1.0,1.0):
            residuals.append(np.abs(pl[...,a]-s*half[a])); n=np.zeros(3); n[a]=s; normals.append(n)
    ci=np.argmin(np.stack(residuals,axis=-1),axis=-1).astype(np.int16)
    nloc=np.asarray(normals,dtype=np.float64)[ci]
    ncan=np.einsum('ij,hwj->hwi',R,nloc); finite=np.isfinite(t)
    ncan[~finite]=0.0
    face_id=np.where(finite,ci,-1).astype(np.int16)
    return t,ncan,face_id


def _renderer_visible_side_normal(n_outward, ray_dir):
    """Orient an analytic outward normal to the renderer-visible side.

    A cuboid ray that starts inside a solid exits through a geometric backface:
    its outward normal has dot(n_outward, ray_dir) > 0 while Cycles reports the
    visible side normal facing the incident ray. R12 flips exactly those proved
    backface/exit hits. Frontfaces (dot < 0) and tangencies (dot == 0) remain
    unchanged. There is no epsilon and no arbitrary n <-> -n equivalence.
    """
    n=np.asarray(n_outward,dtype=np.float64); d=np.asarray(ray_dir,dtype=np.float64)
    if n.shape != d.shape or n.ndim < 1 or n.shape[-1] != 3:
        raise RuntimeError('G100_R12_VISIBLE_NORMAL_SHAPE_MISMATCH')
    dot=np.sum(n*d,axis=-1)
    flip=np.isfinite(dot) & (dot > 0.0)
    out=np.array(n,copy=True)
    out[flip] *= -1.0
    return out,flip


def _object_hit(C, dw, obj):
    t,ncan,_face_id=_object_hit_surface(C,dw,obj)
    return t,ncan


def _stats(a):
    a=np.asarray(a,dtype=np.float64)
    if not a.size: return {'count':0,'min':None,'max':None,'median':None,'mean':None,'p99':None}
    return {'count':int(a.size),'min':float(np.min(a)),'max':float(np.max(a)),'median':float(np.median(a)),
            'mean':float(np.mean(a)),'p99':float(np.quantile(a,.99))}




def _hit_stack(request, C, h, w, K_override=None):
    _dcv,dw=_ray_grid(request,h,w,K_override=K_override)
    hits=[]
    for obj in request['scene']['objects']:
        t,_nc=_object_hit(C,dw,obj)
        hits.append(t)
    return np.stack(hits,axis=-1)


def _r19_clean_signed_zero(x):
    x=float(x)
    return 0.0 if x == 0.0 else x


def _r27_signed_permutation_for_plane_signature(R):
    """Return an exact proper signed-permutation matrix only when R is already
    within 8 float64 ulps of that discrete rotation class.

    This is a representation classifier for plane-signature construction only.
    It is not used by ray/OBB intersection, camera projection, rendered buffers,
    hit-distance comparison, depth, normal or any acceptance tolerance.
    """
    _require_numpy()
    A=np.asarray(R,dtype=np.float64)
    if A.shape!=(3,3) or not np.isfinite(A).all():
        raise RuntimeError('G100_R27_SIGNED_PERMUTATION_SHAPE_OR_FINITE')
    tau=float(R27_SIGNED_PERMUTATION_ULPS)*float(np.finfo(np.float64).eps)
    S=np.zeros((3,3),dtype=np.float64); used=set()
    for i in range(3):
        j=int(np.argmax(np.abs(A[i])))
        if j in used: return A,False
        if abs(abs(float(A[i,j]))-1.0)>tau: return A,False
        for k in range(3):
            if k!=j and abs(float(A[i,k]))>tau: return A,False
        S[i,j]=1.0 if float(A[i,j])>=0.0 else -1.0
        used.add(j)
    if len(used)!=3 or float(np.linalg.det(S))!=1.0: return A,False
    if np.max(np.abs(A-S))>tau: return A,False
    return S,True


def _r19_face_plane_signatures(request):
    """Exact deterministic unoriented world-plane signatures for cuboid faces.

    R27 changes representation only for transforms that are already within
    eight float64 ulps of a proper signed-permutation rotation. Those transforms
    are represented by the exact signed permutation for plane signatures. All
    other matrices remain raw. No ray-hit or visibility-distance epsilon exists.
    """
    _require_numpy()
    out=[]
    for obj in request['scene']['objects']:
        R=np.asarray(obj['R_local_to_world'],dtype=np.float64)
        ctr=np.asarray(obj['center_world'],dtype=np.float64)
        half=np.asarray(obj['dimensions_m'],dtype=np.float64)/2.0
        if R.shape!=(3,3) or ctr.shape!=(3,) or half.shape!=(3,):
            raise RuntimeError('G100_R19_FACE_PLANE_GEOMETRY_SHAPE')
        if not (np.isfinite(R).all() and np.isfinite(ctr).all() and np.isfinite(half).all()):
            raise RuntimeError('G100_R19_FACE_PLANE_GEOMETRY_NONFINITE')
        R_sig,_snapped=_r27_signed_permutation_for_plane_signature(R)
        faces=[]
        for a in range(3):
            for sign in (-1.0,1.0):
                n=R_sig[:,a]*sign
                point=ctr + R_sig[:,a]*(sign*half[a])
                d=float(np.dot(n,point))
                first=None
                for v in n:
                    fv=float(v)
                    if fv != 0.0:
                        first=fv
                        break
                if first is None:
                    raise RuntimeError('G100_R19_FACE_PLANE_ZERO_NORMAL')
                if first < 0.0:
                    n=-n; d=-d
                sig=tuple(_r19_clean_signed_zero(v) for v in n)+( _r19_clean_signed_zero(d), )
                faces.append(sig)
        out.append(tuple(faces))
    return tuple(out)


def _exact_conearest_identity_from_stack(T, oid, face_stack=None, plane_signatures=None):
    """Exact set-valued visibility identity with R19 geometric coincidence.

    R4 bit-for-bit co-nearest equality remains valid unchanged. R19 adds only a
    second exact branch: if rendered and singular-nearest analytic hits are on
    faces with exactly the same canonical world-plane signature, and both face
    hits are finite at this pixel, they are the same geometric surface even if
    alternate local-transform arithmetic makes their float64 t values differ by
    machine-roundoff. No numeric visibility epsilon exists.
    """
    T=np.asarray(T,dtype=np.float64)
    oid=np.asarray(oid,dtype=np.int32)
    if T.ndim != 3 or oid.shape != T.shape[:2]:
        raise RuntimeError('G100_R4_VISIBILITY_SHAPE_MISMATCH')
    h,w,nobj=T.shape
    if np.any((oid<0)|(oid>nobj)):
        valid_ids=False
    else:
        valid_ids=True
    min_t=np.min(T,axis=-1)
    singular=np.argmin(T,axis=-1)+1
    singular=np.where(np.isfinite(min_t),singular,0)
    positive=oid>0
    actual_t=np.full((h,w),np.inf,dtype=np.float64)
    for j in range(1,nobj+1):
        m=(oid==j)
        actual_t[m]=T[...,j-1][m]
    bitwise_positive=positive & np.isfinite(actual_t) & (actual_t==min_t)
    exact_background=(oid==0) & ~np.isfinite(min_t)
    bitwise_exact=bitwise_positive | exact_background

    geometric=np.zeros((h,w),dtype=bool)
    geometric_pair_hist={}
    if face_stack is not None or plane_signatures is not None:
        if face_stack is None or plane_signatures is None:
            raise RuntimeError('G100_R19_FACE_VISIBILITY_PARTIAL_ARGUMENTS')
        F=np.asarray(face_stack,dtype=np.int16)
        if F.shape != T.shape:
            raise RuntimeError('G100_R19_FACE_VISIBILITY_SHAPE_MISMATCH')
        if len(plane_signatures)!=nobj or any(len(q)!=6 for q in plane_signatures):
            raise RuntimeError('G100_R19_FACE_SIGNATURE_COUNT_MISMATCH')
        candidate=positive & ~bitwise_positive & np.isfinite(actual_t) & np.isfinite(min_t) & (singular>0)
        if np.any(candidate):
            pairs=np.stack([singular[candidate],oid[candidate]],axis=1)
            uniq=np.unique(pairs,axis=0)
            for sid,rid in uniq:
                sid=int(sid); rid=int(rid)
                pm=candidate & (singular==sid) & (oid==rid)
                sf=F[...,sid-1]; rf=F[...,rid-1]
                face_pairs=np.stack([sf[pm],rf[pm]],axis=1)
                for sface,rface in np.unique(face_pairs,axis=0):
                    sface=int(sface); rface=int(rface)
                    if sface<0 or rface<0:
                        continue
                    if plane_signatures[sid-1][sface] == plane_signatures[rid-1][rface]:
                        gm=pm & (sf==sface) & (rf==rface)
                        geometric |= gm
            if np.any(geometric):
                gpairs=np.stack([singular[geometric],oid[geometric]],axis=1)
                gu,gc=np.unique(gpairs,axis=0,return_counts=True)
                geometric_pair_hist={f'{int(a)}->{int(b)}':int(c) for (a,b),c in zip(gu,gc)}

    exact=bitwise_exact | geometric
    singular_match=(singular==oid)
    bitwise_tie_pixels=bitwise_exact & (singular!=oid)
    pair_hist={}
    if np.any(bitwise_tie_pixels):
        pairs=np.stack([singular[bitwise_tie_pixels],oid[bitwise_tie_pixels]],axis=1)
        uniq,cnt=np.unique(pairs,axis=0,return_counts=True)
        pair_hist={f'{int(a)}->{int(b)}':int(c) for (a,b),c in zip(uniq,cnt)}
    return {
        'min_t':min_t,
        'singular_pred_id':singular,
        'actual_rendered_id_t':actual_t,
        'exact_match_mask':exact,
        'bitwise_exact_match_mask':bitwise_exact,
        'geometric_coincident_match_mask':geometric,
        'singular_match_mask':singular_match,
        'exact_tie_mask':bitwise_tie_pixels,
        'id_range_valid':bool(valid_ids),
        'exact_all':bool(valid_ids and np.all(exact)),
        'singular_match_pixels':int(np.count_nonzero(singular_match)),
        'singular_match_fraction':float(np.mean(singular_match)),
        'exact_match_pixels':int(np.count_nonzero(exact)),
        'exact_match_fraction':float(np.mean(exact)),
        'bitwise_exact_match_pixels':int(np.count_nonzero(bitwise_exact)),
        'bitwise_exact_match_fraction':float(np.mean(bitwise_exact)),
        'exact_tie_pixel_count':int(np.count_nonzero(bitwise_tie_pixels)),
        'tie_pair_histogram':pair_hist,
        'geometric_coincident_match_pixels':int(np.count_nonzero(geometric)),
        'geometric_coincident_match_fraction':float(np.mean(geometric)),
        'geometric_coincident_pair_histogram':geometric_pair_hist,
        'non_nearest_mismatch_pixels':int(np.count_nonzero(~exact)),
        'visibility_semantics':R19_VISIBILITY_IMPLEMENTATION_ID,
        'numeric_visibility_epsilon':R19_NUMERIC_VISIBILITY_EPSILON,
        'plane_signature_representation_semantics':R27_PLANE_SIGNATURE_IMPLEMENTATION_ID,
        'r27_signed_permutation_ulps':R27_SIGNED_PERMUTATION_ULPS,
        'r27_spec_drive_id':R27_SPEC_DRIVE_ID,
    }


def _hit_stack_with_faces(request, C, h, w, K_override=None):
    _dcv,dw=_ray_grid(request,h,w,K_override=K_override)
    hits=[]; faces=[]
    for obj in request['scene']['objects']:
        t,_nc,face=_object_hit_surface(C,dw,obj)
        hits.append(t); faces.append(face)
    return np.stack(hits,axis=-1),np.stack(faces,axis=-1)


def _predict_depth_and_id(request, C, h, w, K_override=None):
    T=_hit_stack(request,C,h,w,K_override=K_override)
    pred_t=np.min(T,axis=-1)
    pred_id=np.argmin(T,axis=-1)+1
    pred_id=np.where(np.isfinite(pred_t),pred_id,0)
    return pred_t,pred_id

def _bounded_lstsq_2d(J, residual, lower, upper, cumulative_before):
    """Exact deterministic active-set solve for min ||J step-residual||^2 in a 2D box.

    No scipy/runtime dependency. Candidate set is complete for a two-variable
    box-constrained linear least-squares problem: feasible unconstrained point,
    four one-active-edge optima, and four corners.
    """
    _require_numpy()
    J=np.asarray(J,dtype=np.float64); residual=np.asarray(residual,dtype=np.float64)
    lower=np.asarray(lower,dtype=np.float64); upper=np.asarray(upper,dtype=np.float64)
    cumulative_before=np.asarray(cumulative_before,dtype=np.float64)
    if J.ndim!=2 or J.shape[1]!=2 or residual.shape!=(J.shape[0],):
        raise RuntimeError('G100_R7_BOUNDED_LS_SHAPE')
    if not (np.isfinite(J).all() and np.isfinite(residual).all() and np.isfinite(lower).all() and np.isfinite(upper).all()):
        raise RuntimeError('G100_R7_BOUNDED_LS_NONFINITE')
    if np.any(lower>upper):
        raise RuntimeError('G100_R7_BOUNDED_LS_BAD_BOX')

    unc,_res,rank_arr,_s=np.linalg.lstsq(J,residual,rcond=None)
    rank=int(rank_arr)
    if rank!=2 or not np.isfinite(unc).all():
        raise RuntimeError(f'G100_R3_RENDERER_PP_SOLVE_RANK:{rank}')

    candidates=[]
    def add(label, x):
        x=np.asarray(x,dtype=np.float64)
        if x.shape!=(2,) or not np.isfinite(x).all(): return
        if np.any(x < lower-1e-15) or np.any(x > upper+1e-15): return
        x=np.minimum(np.maximum(x,lower),upper)
        rr=residual-J@x
        obj=float(np.dot(rr,rr))
        cumulative=cumulative_before+x
        key=(obj,float(np.max(np.abs(cumulative))),float(np.linalg.norm(cumulative)),float(cumulative[0]),float(cumulative[1]),label)
        candidates.append((key,label,x,obj,cumulative))
    if np.all(unc>=lower) and np.all(unc<=upper):
        add('UNCONSTRAINED_INTERIOR',unc)

    # x fixed -> exact optimal y on that edge.
    for xi,label in ((lower[0],'X_LOWER'),(upper[0],'X_UPPER')):
        jy=J[:,1]
        den=float(np.dot(jy,jy))
        if den>0 and np.isfinite(den):
            y=float(np.dot(jy,residual-J[:,0]*xi)/den)
            add(label,[xi,min(max(y,lower[1]),upper[1])])
    # y fixed -> exact optimal x on that edge.
    for yi,label in ((lower[1],'Y_LOWER'),(upper[1],'Y_UPPER')):
        jx=J[:,0]
        den=float(np.dot(jx,jx))
        if den>0 and np.isfinite(den):
            x=float(np.dot(jx,residual-J[:,1]*yi)/den)
            add(label,[min(max(x,lower[0]),upper[0]),yi])
    for xi,xl in ((lower[0],'X_LOWER'),(upper[0],'X_UPPER')):
        for yi,yl in ((lower[1],'Y_LOWER'),(upper[1],'Y_UPPER')):
            add(xl+'_'+yl,[xi,yi])
    if not candidates:
        raise RuntimeError('G100_R7_BOUNDED_LS_NO_CANDIDATE')
    candidates.sort(key=lambda z:z[0])
    best=candidates[0]
    return {
        'step':best[2],
        'rank':rank,
        'unconstrained_step_px':[float(unc[0]),float(unc[1])],
        'selected_label':best[1],
        'selected_objective':float(best[3]),
        'boundary_active':bool(np.any(np.isclose(best[4],-RENDERER_PP_BINDING_MAX_PX,atol=1e-15)) or np.any(np.isclose(best[4],RENDERER_PP_BINDING_MAX_PX,atol=1e-15))),
        'candidate_summaries':[{
            'label':label,
            'step_px':[float(x[0]),float(x[1])],
            'cumulative_delta_px':[float(cum[0]),float(cum[1])],
            'objective':float(obj)
        } for _key,label,x,obj,cum in candidates],
    }


def _fit_renderer_effective_principal_point(request, C, depth, oid, fitmask):
    """R7 bounded-feasible deterministic 2-DOF Cycles raster binding.

    Canonical K remains authority. Only cx/cy may move, and the selected
    cumulative correction can never leave the inherited ±0.001 px box. R7 fixes
    a solver false-block: an unconstrained optimum outside the box is not proof
    that no acceptable in-box solution exists.
    """
    _require_numpy()
    count=int(np.count_nonzero(fitmask))
    if count < RENDERER_PP_MIN_FIT_PIXELS:
        raise RuntimeError(f'G100_R3_RENDERER_PP_INSUFFICIENT_PIXELS:{count}')
    baseK=np.asarray(request['camera']['K'],dtype=np.float64)
    delta=np.zeros(2,dtype=np.float64)
    rank=0
    iterations=0
    last_step=np.zeros(2,dtype=np.float64)
    iteration_diagnostics=[]
    for it in range(RENDERER_PP_MAX_ITERS):
        iterations=it+1
        K=baseK.copy()
        K[0,2]+=delta[0]; K[1,2]+=delta[1]
        pred,_pid=_predict_depth_and_id(request,C,depth.shape[0],depth.shape[1],K)
        perturbed=[]
        for axis in range(2):
            Kp=K.copy(); Kp[axis,2]+=RENDERER_PP_FD_EPS_PX
            pp,_=_predict_depth_and_id(request,C,depth.shape[0],depth.shape[1],Kp)
            perturbed.append(pp)
        # R21 lab: fit only on the inherited bootstrap pixels that remain finite
        # under the current and both finite-difference predictions. This drops
        # unstable grazing-boundary observations from the fit only; final full-
        # raster Object/Depth/Normal adjudication remains unchanged and exact.
        stable=np.asarray(fitmask,dtype=bool).copy()
        stable &= np.isfinite(depth) & (depth>0) & np.isfinite(pred) & (pred>0)
        for pp in perturbed:
            stable &= np.isfinite(pp) & (pp>0)
        stable_count=int(np.count_nonzero(stable))
        if stable_count < RENDERER_PP_MIN_FIT_PIXELS:
            raise RuntimeError(f'G100_R21_RENDERER_PP_INSUFFICIENT_STABLE_PIXELS:{stable_count}')
        residual=depth[stable]-pred[stable]
        if not np.isfinite(residual).all():
            raise RuntimeError('G100_R21_RENDERER_PP_STABLE_RESIDUAL_NONFINITE')
        cols=[]
        for pp in perturbed:
            col=(pp[stable]-pred[stable])/RENDERER_PP_FD_EPS_PX
            if not np.isfinite(col).all():
                raise RuntimeError('G100_R21_RENDERER_PP_STABLE_JACOBIAN_NONFINITE')
            cols.append(col)
        J=np.column_stack(cols)
        lower=np.full(2,-RENDERER_PP_BINDING_MAX_PX,dtype=np.float64)-delta
        upper=np.full(2,+RENDERER_PP_BINDING_MAX_PX,dtype=np.float64)-delta
        sol=_bounded_lstsq_2d(J,residual,lower,upper,delta)
        step=np.asarray(sol['step'],dtype=np.float64); rank=int(sol['rank'])
        delta+=step; last_step=step
        if not np.isfinite(delta).all():
            raise RuntimeError('G100_R3_RENDERER_PP_NONFINITE_DELTA')
        if float(np.max(np.abs(delta))) > RENDERER_PP_BINDING_MAX_PX + 1e-15:
            raise RuntimeError('G100_R7_RENDERER_PP_INTERNAL_BOX_ESCAPE:'+json.dumps(
                {'delta_cx_px':float(delta[0]),'delta_cy_px':float(delta[1]),'bound_px':RENDERER_PP_BINDING_MAX_PX},sort_keys=True))
        iteration_diagnostics.append({
            'iteration':iterations,
            'stable_fit_pixels':stable_count,
            'dropped_unstable_fit_pixels':int(np.count_nonzero(fitmask))-stable_count,
            'r21_finite_stable_fit':True,
            'delta_before_px':[float(delta[0]-step[0]),float(delta[1]-step[1])],
            'unconstrained_step_px':sol['unconstrained_step_px'],
            'selected_step_px':[float(step[0]),float(step[1])],
            'selected_label':sol['selected_label'],
            'selected_objective':sol['selected_objective'],
            'boundary_active':sol['boundary_active'],
            'candidates':sol['candidate_summaries'],
        })
        if float(np.max(np.abs(step))) <= 1e-10:
            break
    K_eff=baseK.copy(); K_eff[0,2]+=delta[0]; K_eff[1,2]+=delta[1]
    pred_eff,pid_eff=_predict_depth_and_id(request,C,depth.shape[0],depth.shape[1],K_eff)
    return {
        'delta_cx_px':float(delta[0]), 'delta_cy_px':float(delta[1]),
        'bound_px':RENDERER_PP_BINDING_MAX_PX,
        'fit_pixels':count, 'rank':rank, 'iterations':iterations,
        'last_step_px':[float(last_step[0]),float(last_step[1])],
        'finite_difference_epsilon_px':RENDERER_PP_FD_EPS_PX,
        'solver_semantics':'BOX_CONSTRAINED_ACTIVE_SET_R7',
        'iteration_diagnostics':iteration_diagnostics,
        'K_effective':K_eff.tolist(),
        'pred_t':pred_eff, 'pred_id':pid_eff,
    }



def _r18_refine_renderer_effective_pp_minimax(request, C, depth, oid, base_binding):
    """R18 deterministic exact-all minimax microgrid refinement."""
    _require_numpy()
    depth=np.asarray(depth,dtype=np.float64); oid=np.asarray(oid,dtype=np.int32)
    h,w=depth.shape
    objmask=oid>0
    if not np.any(objmask):
        raise RuntimeError('G100_R18_NO_OBJECT_PIXELS')
    if not (np.isfinite(depth[objmask]).all() and np.all(depth[objmask]>0)):
        raise RuntimeError('G100_R18_NONFINITE_OR_NONPOSITIVE_RENDERED_DEPTH')
    baseK=np.asarray(request['camera']['K'],dtype=np.float64)
    base_delta=np.asarray([base_binding['delta_cx_px'],base_binding['delta_cy_px']],dtype=np.float64)
    plane_signatures=_r19_face_plane_signatures(request)
    candidates=[]; evaluated=0
    for ix in R18_GRID_INDICES:
        for iy in R18_GRID_INDICES:
            rel=np.asarray([float(ix)*R18_MICROSTEP_PX,float(iy)*R18_MICROSTEP_PX],dtype=np.float64)
            delta=base_delta+rel
            if float(np.max(np.abs(delta))) > RENDERER_PP_BINDING_MAX_PX + 1e-15:
                continue
            K=baseK.copy(); K[0,2]+=delta[0]; K[1,2]+=delta[1]
            T,F=_hit_stack_with_faces(request,C,h,w,K_override=K)
            vis=_exact_conearest_identity_from_stack(T,oid,face_stack=F,plane_signatures=plane_signatures)
            evaluated+=1
            if not bool(vis['exact_all']):
                continue
            pred=vis['min_t']; pv=pred[objmask]
            if not np.isfinite(pv).all():
                continue
            ae=np.abs(depth[objmask]-pv)
            if not ae.size or not np.isfinite(ae).all():
                continue
            mx=float(np.max(ae)); p99=float(np.quantile(ae,.99)); mean=float(np.mean(ae))
            rel_norm=float(np.linalg.norm(rel))
            key=(mx,p99,mean,rel_norm,float(rel[0]),float(rel[1]))
            candidates.append((key,rel,delta,K,pred,vis))
    if not candidates:
        raise RuntimeError('G100_R18_NO_EXACT_IDENTITY_MICROGRID_CANDIDATE')
    candidates.sort(key=lambda q:q[0])
    key,rel,delta,K,pred,vis=candidates[0]
    return {
        'implementation_id':R18_REFINEMENT_IMPLEMENTATION_ID,
        'microstep_px':float(R18_MICROSTEP_PX),
        'grid_indices':list(R18_GRID_INDICES),
        'candidate_grid_size':int(len(R18_GRID_INDICES)**2),
        'candidates_evaluated':int(evaluated),
        'eligible_exact_identity_candidates':int(len(candidates)),
        'base_delta_cx_px':float(base_delta[0]),
        'base_delta_cy_px':float(base_delta[1]),
        'selected_relative_dx_px':float(rel[0]),
        'selected_relative_dy_px':float(rel[1]),
        'selected_delta_cx_px':float(delta[0]),
        'selected_delta_cy_px':float(delta[1]),
        'selected_max_abs_depth_error_m':float(key[0]),
        'selected_p99_abs_depth_error_m':float(key[1]),
        'selected_mean_abs_depth_error_m':float(key[2]),
        'selected_relative_offset_norm_px':float(key[3]),
        'selection_objective':'LEXICOGRAPHIC_MAX_P99_MEAN_RELNORM_DX_DY',
        'threshold_used_in_selection':False,
        'depth_authority_masked':False,
        'exact_identity_all':bool(vis['exact_all']),
        'K_effective':K.tolist(),
        'pred_t':pred,
        'effective_vis':vis,
    }

R21_LAB_IMPLEMENTATION_ID = 'FINITE_STABLE_BINDING_PLUS_GENERALIZED_MINIMAX_R23_PRODUCTION_V1'
R23_GLOBAL_PP_IMPLEMENTATION_ID = 'GLOBAL_BOUNDED_COARSE_FINE_MICROFINE_ULTRAFINE_R23_PRODUCTION_V1'
R23_NORMAL_SEMANTICS_ID = 'FILTER_SAFE_INTERIOR_DIRECTION_ERROR_R23_PRODUCTION_V1'
R23_STAGE_D_STEP_PX = 1e-7
R23_STAGE_D_RADIUS = 20
R21_LAB_RADII = (4,8,16)

def _r21_generalized_renderer_effective_pp_refine(request, C, depth, oid, base_binding, radius):
    """Diagnostic-only deterministic microgrid around the safe-R7 base.

    Candidate selection uses Object Index + Depth only. Rendered Normal never
    participates in selection. Thresholds are not part of the objective.
    """
    _require_numpy()
    depth=np.asarray(depth,dtype=np.float64); oid=np.asarray(oid,dtype=np.int32)
    h,w=depth.shape; objmask=oid>0
    if not np.any(objmask): raise RuntimeError('G100_R21_NO_OBJECT_PIXELS')
    if not (np.isfinite(depth[objmask]).all() and np.all(depth[objmask]>0)):
        raise RuntimeError('G100_R21_NONFINITE_OR_NONPOSITIVE_RENDERED_DEPTH')
    baseK=np.asarray(request['camera']['K'],dtype=np.float64)
    center=np.asarray([base_binding.get('delta_cx_px',0.0),base_binding.get('delta_cy_px',0.0)],dtype=np.float64)
    plane_signatures=_r19_face_plane_signatures(request)
    candidates=[]
    rr=range(-int(radius),int(radius)+1); items=[]
    for ix in rr:
        for iy in rr:
            rel=np.asarray([float(ix)*R18_MICROSTEP_PX,float(iy)*R18_MICROSTEP_PX],dtype=np.float64); delta=center+rel
            if float(np.max(np.abs(delta))) <= RENDERER_PP_BINDING_MAX_PX + 1e-15: items.append((rel,delta))
    evaluated=len(items); workers=max(1,min(int(os.environ.get('PCS_R23_PP_WORKERS','8')),8))
    def fn(item):
        rel,delta=item; K=baseK.copy(); K[0,2]+=delta[0]; K[1,2]+=delta[1]
        T,F=_hit_stack_with_faces(request,C,h,w,K_override=K)
        vis=_exact_conearest_identity_from_stack(T,oid,face_stack=F,plane_signatures=plane_signatures)
        pred=vis['min_t']; pv=pred[objmask]
        if not np.isfinite(pv).all(): return None
        ae=np.abs(depth[objmask]-pv)
        if not ae.size or not np.isfinite(ae).all(): return None
        mismatch=int(vis.get('non_nearest_mismatch_pixels',0)); mx=float(np.max(ae)); p99=float(np.quantile(ae,.99)); mean=float(np.mean(ae)); rel_norm=float(np.linalg.norm(rel))
        key=(mismatch,mx,p99,mean,rel_norm,float(rel[0]),float(rel[1])); return (key,rel,delta,K,pred,vis)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for q in ex.map(fn,items):
            if q is not None: candidates.append(q)
    if not candidates:
        raise RuntimeError('G100_R21_NO_FINITE_GENERALIZED_MICROGRID_CANDIDATE')
    candidates.sort(key=lambda q:q[0])
    key,rel,delta,K,pred,vis=candidates[0]
    return {
        'implementation_id':R21_LAB_IMPLEMENTATION_ID,
        'radius_steps':int(radius),
        'microstep_px':float(R18_MICROSTEP_PX),
        'candidate_grid_size':int((2*int(radius)+1)**2),
        'candidates_evaluated':int(evaluated),
        'finite_candidates':int(len(candidates)),
        'base_delta_cx_px':float(center[0]),
        'base_delta_cy_px':float(center[1]),
        'selected_relative_dx_px':float(rel[0]),
        'selected_relative_dy_px':float(rel[1]),
        'selected_delta_cx_px':float(delta[0]),
        'selected_delta_cy_px':float(delta[1]),
        'selected_non_nearest_object_mismatch_pixels':int(key[0]),
        'selected_max_abs_depth_error_m':float(key[1]),
        'selected_p99_abs_depth_error_m':float(key[2]),
        'selected_mean_abs_depth_error_m':float(key[3]),
        'selected_relative_offset_norm_px':float(key[4]),
        'selection_objective':'LEXICOGRAPHIC_OBJECT_MISMATCH_MAXDEPTH_P99_MEAN_RELNORM_DX_DY',
        'threshold_used_in_selection':False,
        'rendered_normal_used_in_selection':False,
        'exact_identity_all':bool(vis['exact_all']),
        'K_effective':K.tolist(),
        'pred_t':pred,
        'effective_vis':vis,
    }

def _r21_global_coarse_renderer_effective_pp_search(request, C, depth, oid):
    """Diagnostic-only global bounded lattice used only when safe R7 cannot form a base.

    The full inherited +/-0.001 px box is sampled at the inherited finite-difference
    step (1e-4 px). Selection is the same threshold-free Object+Depth lexicographic
    objective as the local R21 microgrid. Rendered Normal is never consulted.
    """
    _require_numpy()
    depth=np.asarray(depth,dtype=np.float64); oid=np.asarray(oid,dtype=np.int32)
    h,w=depth.shape; objmask=oid>0
    if not np.any(objmask): raise RuntimeError('G100_R21_COARSE_NO_OBJECT_PIXELS')
    if not (np.isfinite(depth[objmask]).all() and np.all(depth[objmask]>0)):
        raise RuntimeError('G100_R21_COARSE_NONFINITE_OR_NONPOSITIVE_RENDERED_DEPTH')
    baseK=np.asarray(request['camera']['K'],dtype=np.float64)
    plane_signatures=_r19_face_plane_signatures(request)
    # Exactly cover [-0.001,+0.001] at 1e-4 px, including both boundaries.
    n=int(round(RENDERER_PP_BINDING_MAX_PX/RENDERER_PP_FD_EPS_PX))
    indices=range(-n,n+1)
    deltas=[np.asarray([float(ix)*RENDERER_PP_FD_EPS_PX,float(iy)*RENDERER_PP_FD_EPS_PX],dtype=np.float64) for ix in indices for iy in indices]
    evaluated=len(deltas); candidates=[]; workers=max(1,min(int(os.environ.get('PCS_R23_PP_WORKERS','8')),8))
    def fn(delta):
        K=baseK.copy(); K[0,2]+=delta[0]; K[1,2]+=delta[1]
        T,F=_hit_stack_with_faces(request,C,h,w,K_override=K); vis=_exact_conearest_identity_from_stack(T,oid,face_stack=F,plane_signatures=plane_signatures)
        pred=vis['min_t']; pv=pred[objmask]
        if not np.isfinite(pv).all(): return None
        ae=np.abs(depth[objmask]-pv)
        if not ae.size or not np.isfinite(ae).all(): return None
        mismatch=int(vis.get('non_nearest_mismatch_pixels',0)); mx=float(np.max(ae)); p99=float(np.quantile(ae,.99)); mean=float(np.mean(ae)); norm=float(np.linalg.norm(delta))
        key=(mismatch,mx,p99,mean,norm,float(delta[0]),float(delta[1])); return (key,delta,K,pred,vis)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for q in ex.map(fn,deltas):
            if q is not None: candidates.append(q)
    if not candidates:
        raise RuntimeError('G100_R21_NO_FINITE_GLOBAL_COARSE_CANDIDATE')
    candidates.sort(key=lambda q:q[0])
    key,delta,K,pred,vis=candidates[0]
    return {
        'implementation_id':R21_LAB_IMPLEMENTATION_ID,
        'mode':'GLOBAL_COARSE_FALLBACK_DIAGNOSTIC_ONLY',
        'coarse_step_px':float(RENDERER_PP_FD_EPS_PX),
        'bound_px':float(RENDERER_PP_BINDING_MAX_PX),
        'candidate_grid_size':int((2*n+1)**2),
        'candidates_evaluated':int(evaluated),
        'finite_candidates':int(len(candidates)),
        'selected_delta_cx_px':float(delta[0]),
        'selected_delta_cy_px':float(delta[1]),
        'selected_non_nearest_object_mismatch_pixels':int(key[0]),
        'selected_max_abs_depth_error_m':float(key[1]),
        'selected_p99_abs_depth_error_m':float(key[2]),
        'selected_mean_abs_depth_error_m':float(key[3]),
        'selected_offset_norm_px':float(key[4]),
        'selection_objective':'LEXICOGRAPHIC_OBJECT_MISMATCH_MAXDEPTH_P99_MEAN_OFFSETNORM_DX_DY',
        'threshold_used_in_selection':False,
        'rendered_normal_used_in_selection':False,
        'production_authorized':True,
        'exact_identity_all':bool(vis['exact_all']),
        'K_effective':K.tolist(),
        'pred_t':pred,
        'effective_vis':vis,
    }


def _r23_eval_pp_candidate(request, C, depth, oid, delta, plane_signatures=None, materialize_visibility=True):
    _require_numpy()
    depth=np.asarray(depth,dtype=np.float64); oid=np.asarray(oid,dtype=np.int32)
    h,w=depth.shape; objmask=oid>0
    baseK=np.asarray(request['camera']['K'],dtype=np.float64)
    delta=np.asarray(delta,dtype=np.float64)
    if delta.shape!=(2,) or float(np.max(np.abs(delta))) > RENDERER_PP_BINDING_MAX_PX + 1e-15:
        return None
    K=baseK.copy(); K[0,2]+=delta[0]; K[1,2]+=delta[1]
    T,F=_hit_stack_with_faces(request,C,h,w,K_override=K)
    vis=_exact_conearest_identity_from_stack(T,oid,face_stack=F,plane_signatures=(plane_signatures if plane_signatures is not None else _r19_face_plane_signatures(request)))
    pred=vis['min_t']; pv=pred[objmask]
    if not pv.size or not np.isfinite(pv).all(): return None
    ae=np.abs(depth[objmask]-pv)
    if not ae.size or not np.isfinite(ae).all(): return None
    mismatch=int(vis.get('non_nearest_mismatch_pixels',0))
    mx=float(np.max(ae)); p99=float(np.quantile(ae,.99)); mean=float(np.mean(ae)); norm=float(np.linalg.norm(delta))
    key=(mismatch,mx,p99,mean,norm,float(delta[0]),float(delta[1]))
    out={'key':key,'delta':delta,'K_effective':K,
            'non_nearest_object_mismatch_pixels':mismatch,'max_abs_depth_error_m':mx,
            'p99_abs_depth_error_m':p99,'mean_abs_depth_error_m':mean,'offset_norm_px':norm}
    if materialize_visibility:out.update({'pred_t':pred,'effective_vis':vis})
    return out

def _r23_pp_stage(request,C,depth,oid,center,step,radius,label):
    """Memory-bounded deterministic R23 lattice stage.

    Candidate ranking retains only scalar metrics + delta. Full pred_t/visibility
    rasters are recomputed exactly once for the deterministic winner (R23 C1).
    """
    center=np.asarray(center,dtype=np.float64)
    rr=range(-int(radius),int(radius)+1)
    deltas=[]
    for ix in rr:
        for iy in rr:
            delta=center+np.asarray([ix*step,iy*step],dtype=np.float64)
            if float(np.max(np.abs(delta)))<=RENDERER_PP_BINDING_MAX_PX+1e-15: deltas.append(delta)
    evaluated=len(deltas); planes=_r19_face_plane_signatures(request)
    workers=max(1,min(int(os.environ.get('PCS_R23_PP_WORKERS','8')),8))
    def fn(delta):
        c=_r23_eval_pp_candidate(request,C,depth,oid,delta,planes,materialize_visibility=False)
        if c is None:return None
        return {'key':tuple(c['key']),'delta':np.asarray(c['delta'],dtype=np.float64)}
    best=None; finite=0
    # Bound submitted futures as well as retained candidate state. This keeps
    # Stage D memory stable on Windows while preserving exact input order.
    batch_size=max(workers*8,32)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for off in range(0,len(deltas),batch_size):
            for c in ex.map(fn,deltas[off:off+batch_size]):
                if c is None:continue
                finite+=1
                if best is None or c['key'] < best['key']:best=c
    if best is None: raise RuntimeError('G100_R23_NO_FINITE_PP_STAGE_CANDIDATE:'+label)
    # Recompute only the selected winner to materialize full-raster evidence.
    b=_r23_eval_pp_candidate(request,C,depth,oid,best['delta'],planes,materialize_visibility=True)
    if b is None or tuple(b['key'])!=tuple(best['key']):
        raise RuntimeError('G100_R23_STREAMING_WINNER_RECOMPUTE_MISMATCH:'+label)
    return {'label':label,'step_px':float(step),'radius_steps':int(radius),'candidate_grid_size':int((2*radius+1)**2),
            'candidates_evaluated':int(evaluated),'finite_candidates':int(finite),
            'memory_selection_mode':'SCALAR_STREAMING_RECOMPUTE_WINNER_R23_C1',
            'center_delta_px':[float(center[0]),float(center[1])],
            'selected_delta_cx_px':float(b['delta'][0]),'selected_delta_cy_px':float(b['delta'][1]),
            'selected_non_nearest_object_mismatch_pixels':int(b['key'][0]),
            'selected_max_abs_depth_error_m':float(b['key'][1]),'selected_p99_abs_depth_error_m':float(b['key'][2]),
            'selected_mean_abs_depth_error_m':float(b['key'][3]),'selected_offset_norm_px':float(b['key'][4]),
            'selection_objective':'LEXICOGRAPHIC_OBJECT_MISMATCH_MAXDEPTH_P99_MEAN_OFFSETNORM_DX_DY',
            'threshold_used_in_selection':False,'rendered_normal_used_in_selection':False,
            'K_effective':b['K_effective'].tolist(),'pred_t':b['pred_t'],'effective_vis':b['effective_vis']}

def _r23_global_bounded_pp_search(request,C,depth,oid):
    """R23 production global bounded PP hierarchy; Object+Depth only."""
    depth=np.asarray(depth,dtype=np.float64); oid=np.asarray(oid,dtype=np.int32); objmask=oid>0
    if not np.any(objmask): raise RuntimeError('G100_R23_GLOBAL_NO_OBJECT_PIXELS')
    if not (np.isfinite(depth[objmask]).all() and np.all(depth[objmask]>0)): raise RuntimeError('G100_R23_GLOBAL_BAD_DEPTH')
    stages=[]
    A=_r23_pp_stage(request,C,depth,oid,[0.0,0.0],1e-4,10,'A_COARSE_1E4'); stages.append(A)
    B=_r23_pp_stage(request,C,depth,oid,[A['selected_delta_cx_px'],A['selected_delta_cy_px']],1e-5,10,'B_FINE_1E5'); stages.append(B)
    Cc=_r23_pp_stage(request,C,depth,oid,[B['selected_delta_cx_px'],B['selected_delta_cy_px']],1e-6,10,'C_MICRO_FINE_1E6'); stages.append(Cc)
    final=Cc; stage_d_triggered=False
    if int(Cc['selected_non_nearest_object_mismatch_pixels'])==0 and float(Cc['selected_max_abs_depth_error_m'])>DEPTH_GEOM_TOL_M:
        stage_d_triggered=True
        D=_r23_pp_stage(request,C,depth,oid,[Cc['selected_delta_cx_px'],Cc['selected_delta_cy_px']],R23_STAGE_D_STEP_PX,R23_STAGE_D_RADIUS,'D_ULTRA_FINE_1E7')
        stages.append(D); final=D
    return {'implementation_id':R23_GLOBAL_PP_IMPLEMENTATION_ID,'bound_px':RENDERER_PP_BINDING_MAX_PX,
            'stages':[ {k:v for k,v in x.items() if k not in {'pred_t','effective_vis'}} for x in stages],
            'stage_d_triggered':stage_d_triggered,'threshold_used_in_selection':False,'rendered_normal_used_in_selection':False,
            'selected_delta_cx_px':float(final['selected_delta_cx_px']),'selected_delta_cy_px':float(final['selected_delta_cy_px']),
            'selected_non_nearest_object_mismatch_pixels':int(final['selected_non_nearest_object_mismatch_pixels']),
            'selected_max_abs_depth_error_m':float(final['selected_max_abs_depth_error_m']),
            'selected_p99_abs_depth_error_m':float(final['selected_p99_abs_depth_error_m']),
            'selected_mean_abs_depth_error_m':float(final['selected_mean_abs_depth_error_m']),
            'K_effective':final['K_effective'],'pred_t':final['pred_t'],'effective_vis':final['effective_vis']}

def _r21_normal_eval_for_K(request, C, raw, oid, objmask, filter_radius, K_override):
    _require_numpy()
    h,w=oid.shape
    _dcv,dw=_ray_grid(request,h,w,K_override=K_override)
    nvis_all=[]; face_all=[]; flip_all=[]
    for obj in request['scene']['objects']:
        _t,nc,face=_object_hit_surface(C,dw,obj)
        nvis,flip=_renderer_visible_side_normal(nc,dw)
        nvis_all.append(nvis); face_all.append(face); flip_all.append(flip)
    pred_ncan=np.zeros((h,w,3),dtype=np.float64)
    analytic_face_labels=np.full((h,w),-1,dtype=np.int32)
    visible_backface_pixels=0
    for j,(nc,face,flip) in enumerate(zip(nvis_all,face_all,flip_all),1):
        m=(oid==j)
        pred_ncan[m]=nc[m]
        visible_backface_pixels += int(np.count_nonzero(m & flip))
        analytic_face_labels[m]=(j-1)*6 + face[m].astype(np.int32)
    CFB=np.asarray(C_FROM_B,dtype=np.float64); BFC=np.asarray(B_FROM_C,dtype=np.float64)
    pred_nb=np.einsum('ij,hwj->hwi',BFC,pred_ncan)
    derived_ncan=np.einsum('ij,hwj->hwi',CFB,raw)
    mag=np.linalg.norm(raw,axis=-1)
    authority=objmask & np.isfinite(raw).all(axis=-1) & np.isfinite(mag) & (np.abs(mag-1.0)<=NORMAL_TOL)
    auth_count=int(authority.sum()); obj_count=int(objmask.sum())
    auth_frac=float(auth_count/obj_count) if obj_count else 0.0
    raw_err_map=np.linalg.norm(raw-pred_nb,axis=-1)
    can_err_map=np.linalg.norm(derived_ncan-pred_ncan,axis=-1)
    raw_err=raw_err_map[authority]
    can_err=can_err_map[authority]
    filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)
    filter_safe_count=int(filter_safe.sum())
    filter_safe_auth=(filter_safe & authority)
    filter_safe_auth_count=int(filter_safe_auth.sum())
    filter_safe_auth_frac=float(filter_safe_auth_count/filter_safe_count) if filter_safe_count else 0.0
    safe_raw_err=raw_err_map[filter_safe_auth]
    safe_can_err=can_err_map[filter_safe_auth]
    invalid_obj=objmask & ~authority
    unexplained_invalid=invalid_obj & filter_safe
    unexplained_count=int(unexplained_invalid.sum())
    boundary_explained=invalid_obj & ~filter_safe
    boundary_explained_count=int(boundary_explained.sum())
    invalid_count=int(invalid_obj.sum())
    boundary_explained_frac=float(boundary_explained_count/invalid_count) if invalid_count else 1.0
    normal_ok=bool(filter_safe_count>0 and filter_safe_auth_frac>=MIN_NORMAL_AUTHORITY_FRACTION and unexplained_count==0 and safe_raw_err.size and np.all(safe_raw_err<=NORMAL_GEOM_TOL) and np.all(safe_can_err<=NORMAL_GEOM_TOL))
    return {
        'normal_ok':normal_ok,'pred_ncan':pred_ncan,'analytic_face_labels':analytic_face_labels,
        'visible_backface_pixels':visible_backface_pixels,'authority':authority,'auth_count':auth_count,
        'obj_count':obj_count,'auth_frac':auth_frac,'raw_err':raw_err,'can_err':can_err,'safe_raw_err':safe_raw_err,'safe_can_err':safe_can_err,
        'filter_safe':filter_safe,'filter_safe_count':filter_safe_count,'filter_safe_auth_count':filter_safe_auth_count,
        'filter_safe_auth_frac':filter_safe_auth_frac,'invalid_obj':invalid_obj,'unexplained_count':unexplained_count,
        'boundary_explained_count':boundary_explained_count,'invalid_count':invalid_count,
        'boundary_explained_frac':boundary_explained_frac,
    }

def _filter_safe_interior_mask(oid, face_labels, radius):
    """Analytic reconstruction-filter-safe interior mask.

    A pixel is eligible only when its complete Chebyshev support neighborhood
    remains on the same rendered object identity AND the same analytic cuboid
    face. Image-edge pixels without a complete support footprint are excluded.
    """
    oid=np.asarray(oid,dtype=np.int32); face_labels=np.asarray(face_labels,dtype=np.int32)
    if oid.shape!=face_labels.shape: raise RuntimeError('G100_R6_FILTER_SAFE_SHAPE_MISMATCH')
    radius=int(radius)
    if radius<0: raise RuntimeError('G100_R6_FILTER_RADIUS_NEGATIVE')
    h,w=oid.shape; stable=(oid>0) & (face_labels>=0)
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if dx==0 and dy==0: continue
            y0=max(0,-dy); y1=min(h,h-dy); x0=max(0,-dx); x1=min(w,w-dx)
            same=np.zeros((h,w),dtype=bool)
            if y1>y0 and x1>x0:
                same[y0:y1,x0:x1]=(oid[y0:y1,x0:x1]==oid[y0+dy:y1+dy,x0+dx:x1+dx]) & (face_labels[y0:y1,x0:x1]==face_labels[y0+dy:y1+dy,x0+dx:x1+dx])
            stable &= same
    return stable


def _r29_depth_authority_adjudication(depth, pred_t, oid, face_labels, renderer_filter_width_px=G100_CYCLES_FILTER_WIDTH_PX):
    """R29 exact-Depth authority adjudication.

    Raw Depth remains immutable and the numeric tolerance remains DEPTH_GEOM_TOL_M.
    The renderer reconstruction-filter boundary is explicitly non-authoritative:
    exact Depth is accepted only where the complete frozen filter footprint stays
    on the same rendered object identity and the same analytic cuboid face.
    Selection never reads RGB or adapts the support radius/tolerance.
    """
    depth=np.asarray(depth,dtype=np.float64)
    pred_t=np.asarray(pred_t,dtype=np.float64)
    oid=np.asarray(oid,dtype=np.int32)
    face_labels=np.asarray(face_labels,dtype=np.int32)
    if depth.shape!=pred_t.shape or depth.shape!=oid.shape or depth.shape!=face_labels.shape:
        raise RuntimeError('G100_R29_DEPTH_AUTHORITY_SHAPE_MISMATCH')
    filter_width=float(renderer_filter_width_px)
    filter_width_ok=bool(np.isfinite(filter_width) and abs(filter_width-G100_CYCLES_FILTER_WIDTH_PX)<=1e-12)
    if not filter_width_ok:
        raise RuntimeError('G100_R29_RENDER_FILTER_WIDTH_MISMATCH:'+json.dumps({'expected':G100_CYCLES_FILTER_WIDTH_PX,'actual':filter_width},sort_keys=True))
    filter_radius=int(math.ceil(filter_width))
    safe=_filter_safe_interior_mask(oid,face_labels,filter_radius)
    objmask=oid>0
    err_map=np.abs(depth-pred_t)
    full_vals=err_map[objmask]
    safe_vals=err_map[safe]
    depth_positive=bool(np.count_nonzero(objmask)>0 and np.all(np.isfinite(depth[objmask])) and np.all(depth[objmask]>0))
    pred_finite_safe=bool(safe_vals.size and np.all(np.isfinite(pred_t[safe])) and np.all(np.isfinite(safe_vals)))
    full_over=objmask & ((~np.isfinite(err_map)) | (err_map>DEPTH_GEOM_TOL_M))
    safe_over=safe & ((~np.isfinite(err_map)) | (err_map>DEPTH_GEOM_TOL_M))
    boundary=objmask & ~safe
    boundary_over=boundary & ((~np.isfinite(err_map)) | (err_map>DEPTH_GEOM_TOL_M))
    passed=bool(depth_positive and pred_finite_safe and int(np.count_nonzero(safe))>0 and int(np.count_nonzero(safe_over))==0)
    return {
        'status':'PASS' if passed else 'FAIL',
        'authority_semantics':R29_DEPTH_AUTHORITY_SEMANTICS_ID,
        'r29_spec_drive_id':R29_SPEC_DRIVE_ID,
        'tolerance_m':DEPTH_GEOM_TOL_M,
        'renderer_filter_width_px':filter_width,
        'renderer_filter_width_expected_px':G100_CYCLES_FILTER_WIDTH_PX,
        'renderer_filter_width_status':'PASS',
        'filter_support_radius_px':filter_radius,
        'object_pixels':int(np.count_nonzero(objmask)),
        'filter_safe_interior_pixels':int(np.count_nonzero(safe)),
        'filter_safe_interior_fraction_of_object_pixels':float(np.count_nonzero(safe)/np.count_nonzero(objmask)) if np.count_nonzero(objmask) else 0.0,
        'boundary_object_pixels':int(np.count_nonzero(boundary)),
        'full_raster_depth_abs_error_m':_stats(full_vals),
        'filter_safe_depth_abs_error_m':_stats(safe_vals),
        'full_raster_over_tolerance_pixels':int(np.count_nonzero(full_over)),
        'filter_safe_over_tolerance_pixels':int(np.count_nonzero(safe_over)),
        'boundary_over_tolerance_pixels':int(np.count_nonzero(boundary_over)),
        'positive_finite_object_pixels':depth_positive,
        'raw_exr_immutable':True,
        'safe_mask':safe,
        'error_map':err_map,
        'full_over_mask':full_over,
        'safe_over_mask':safe_over,
        'boundary_mask':boundary,
    }


def validate_aux_gt(request: dict, sample_dir: Path, renderer_filter_width_px: float = G100_CYCLES_FILTER_WIDTH_PX) -> dict:
    _require_numpy()
    sample_dir=Path(sample_dir)
    dp=sample_dir/'depth.exr'; npth=sample_dir/'normal.exr'; op=sample_dir/'object_index.exr'
    for p in (dp,npth,op):
        if not p.is_file(): raise RuntimeError('G100_AUX_GT_FILE_MISSING:'+p.name)
    d=decode_exr(dp); o=decode_exr(op); n=decode_exr(npth)
    if 'V' not in d or 'V' not in o or not all(k in n for k in ('X','Y','Z')):
        raise RuntimeError('G100_AUX_GT_CHANNEL_SCHEMA_FAIL')
    depth=d['V'].astype(np.float64); oidf=o['V'].astype(np.float64)
    raw=np.stack([n['X'],n['Y'],n['Z']],axis=-1).astype(np.float64)
    h,w=depth.shape
    if (w,h)!=(int(request['camera']['width']),int(request['camera']['height'])):
        raise RuntimeError('G100_AUX_GT_RASTER_MISMATCH')
    oid=np.rint(oidf).astype(np.int32); fracerr=np.abs(oidf-np.rint(oidf))
    if not np.isfinite(oidf).all() or float(np.max(fracerr)) != 0.0:
        raise RuntimeError('G100_OBJECT_INDEX_NOT_EXACT_INTEGER_FLOAT')
    C=np.asarray(request['camera']['pose']['camera_center_world'],dtype=np.float64)

    # Canonical request-K geometry remains the source of exact visibility and
    # Normal authority. R4 makes coincident visibility set-valued: the rendered
    # id must be an EXACT co-nearest analytic hit, never merely "close".
    dcv,dw=_ray_grid(request,h,w)
    hits=[]; hit_normals=[]; hit_normals_visible=[]; hit_normal_flips=[]; hit_faces=[]
    for obj in request['scene']['objects']:
        t,nc,face=_object_hit_surface(C,dw,obj)
        nvis,flip=_renderer_visible_side_normal(nc,dw)
        hits.append(t); hit_normals.append(nc); hit_normals_visible.append(nvis); hit_normal_flips.append(flip); hit_faces.append(face)
    T=np.stack(hits,axis=-1)
    F=np.stack(hit_faces,axis=-1)
    plane_signatures=_r19_face_plane_signatures(request)
    vis=_exact_conearest_identity_from_stack(T,oid,face_stack=F,plane_signatures=plane_signatures)
    pred_t_canonical=vis['min_t']
    singular_pred_id=vis['singular_pred_id']
    objmask=oid>0; bg=~objmask
    max_id=len(request['scene']['objects'])
    ids_ok=bool(vis['id_range_valid']) and bool(np.all((oid>=0)&(oid<=max_id)))

    # Normal authority is independent of Depth raster fitting and uses the
    # actual rendered object identity. This is essential at exact coplanar ties.
    pred_ncan=np.zeros((h,w,3),dtype=np.float64)
    analytic_face_labels=np.full((h,w),-1,dtype=np.int32)
    # Label is globally unique by object identity and local cuboid face id.
    visible_backface_pixels=0
    for j,(nc,face,flip) in enumerate(zip(hit_normals_visible,hit_faces,hit_normal_flips),1):
        m=(oid==j)
        pred_ncan[m]=nc[m]
        visible_backface_pixels += int(np.count_nonzero(m & flip))
        analytic_face_labels[m]=(j-1)*6 + face[m].astype(np.int32)
    CFB=np.asarray(C_FROM_B,dtype=np.float64); BFC=np.asarray(B_FROM_C,dtype=np.float64)
    pred_nb=np.einsum('ij,hwj->hwi',BFC,pred_ncan)
    derived_ncan=np.einsum('ij,hwj->hwi',CFB,raw)
    mag=np.linalg.norm(raw,axis=-1)
    # Raw authority semantics are inherited unchanged from G70/G100. R6 never
    # renormalizes a blended edge pixel or converts it into exact GT authority.
    authority=objmask & np.isfinite(raw).all(axis=-1) & np.isfinite(mag) & (np.abs(mag-1.0)<=NORMAL_TOL)
    auth_count=int(authority.sum()); obj_count=int(objmask.sum())
    auth_frac=float(auth_count/obj_count) if obj_count else 0.0
    raw_err_map=np.linalg.norm(raw-pred_nb,axis=-1)
    can_err_map=np.linalg.norm(derived_ncan-pred_ncan,axis=-1)
    raw_err=raw_err_map[authority]
    can_err=can_err_map[authority]

    # R6 filter-footprint-aware acceptance. Cycles' reconstruction filter is
    # intentionally allowed to blend Normal around silhouettes/creases while
    # Object Index/Z remain unfiltered. The raw authority mask remains the loss
    # mask; this second analytic mask only determines whether non-unit pixels are
    # fully explained by the renderer filter footprint.
    filter_width=float(renderer_filter_width_px)
    filter_width_ok=bool(np.isfinite(filter_width) and abs(filter_width-G100_CYCLES_FILTER_WIDTH_PX)<=1e-12)
    if not filter_width_ok:
        raise RuntimeError('G100_R6_RENDER_FILTER_WIDTH_MISMATCH:'+json.dumps({'expected':G100_CYCLES_FILTER_WIDTH_PX,'actual':filter_width},sort_keys=True))
    filter_radius=int(math.ceil(filter_width))
    filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)
    filter_safe_count=int(filter_safe.sum())
    filter_safe_auth=(filter_safe & authority)
    filter_safe_auth_count=int(filter_safe_auth.sum())
    filter_safe_auth_frac=float(filter_safe_auth_count/filter_safe_count) if filter_safe_count else 0.0
    safe_raw_err=raw_err_map[filter_safe_auth]
    safe_can_err=can_err_map[filter_safe_auth]
    invalid_obj=objmask & ~authority
    unexplained_invalid=invalid_obj & filter_safe
    unexplained_count=int(unexplained_invalid.sum())
    boundary_explained=invalid_obj & ~filter_safe
    boundary_explained_count=int(boundary_explained.sum())
    invalid_count=int(invalid_obj.sum())
    boundary_explained_frac=float(boundary_explained_count/invalid_count) if invalid_count else 1.0
    normal_ok=bool(filter_safe_count>0 and filter_safe_auth_frac>=MIN_NORMAL_AUTHORITY_FRACTION and unexplained_count==0 and safe_raw_err.size and np.all(safe_raw_err<=NORMAL_GEOM_TOL) and np.all(safe_can_err<=NORMAL_GEOM_TOL))

    # R5 canonical-first remains authoritative for a canonical all-pass.
    # R11 fixes only a validation-order circularity: a tiny renderer-effective
    # principal-point shift can make canonical boundary visibility exact, but
    # earlier versions required canonical identity to be all-pass before the
    # bounded fit could even be estimated. R11 may bootstrap the fit ONLY from
    # pixels whose canonical rendered identity is already exact/co-nearest.
    canonical_object_ok=bool(vis['exact_all']) and ids_ok
    depth_obj=depth[objmask]
    canonical_depth_err=np.abs(depth_obj-pred_t_canonical[objmask]) if depth_obj.size else np.asarray([],dtype=np.float64)
    depth_positive=bool(depth_obj.size and np.all(depth_obj>0) and np.isfinite(depth_obj).all())
    canonical_depth_ok=bool(canonical_object_ok and depth_positive and canonical_depth_err.size and np.all(canonical_depth_err<=DEPTH_GEOM_TOL_M))

    binding=None
    binding_mode='UNAVAILABLE_ID_RANGE_FAIL'
    bootstrap_fit_pixels=0
    r21_fit_failure_diagnostic=None
    r21_safe_base_binding=None
    if not ids_ok:
        pred_t_effective=pred_t_canonical
        effective_vis=vis
    elif canonical_depth_ok:
        # Canonical truth already passes. No cx/cy fit is invoked and the
        # canonical K is retained exactly.
        binding_mode='NOT_REQUIRED_CANONICAL_PASS'
        pred_t_effective=pred_t_canonical
        effective_vis=vis
        binding={
            'binding_status':binding_mode,
            'fit_invoked':False,
            'delta_cx_px':0.0,'delta_cy_px':0.0,
            'bound_px':RENDERER_PP_BINDING_MAX_PX,
            'fit_pixels':0,'rank':None,'iterations':0,'last_step_px':[0.0,0.0],
            'finite_difference_epsilon_px':RENDERER_PP_FD_EPS_PX,
            'K_effective':np.asarray(request['camera']['K'],dtype=np.float64).tolist(),
            'visibility_bootstrap':False,
        }
        r21_safe_base_binding=dict(binding)
    else:
        binding_mode='INVOKED_CANONICAL_VISIBILITY_OR_DEPTH_FAIL_R11'
        # R8 decouples Depth rescue from Normal authority. R11 additionally
        # restricts bootstrap observations to pixels already exact under the
        # canonical visibility model. No mismatching pixel participates in the
        # fit; ALL pixels are re-adjudicated after the bounded fit.
        depth_fitmask=(objmask & vis['bitwise_exact_match_mask'] & np.isfinite(depth) &
                       (depth>0) & np.isfinite(pred_t_canonical))
        bootstrap_fit_pixels=int(np.count_nonzero(depth_fitmask))
        try:
            binding=_fit_renderer_effective_principal_point(request,C,depth,oid,depth_fitmask)
        except Exception as exc:
            diag={
              'schema':'DF-G100-R21-RENDERER-BINDING-DIAGNOSTIC-V1',
              'status':'SAFE_R7_FIT_FAILED_R21_GLOBAL_FALLBACK_ELIGIBLE','binding_mode':binding_mode,
              'sample_id':request.get('sample_id'),
              'canonical_object_exact_all':bool(vis['exact_all']),
              'canonical_non_nearest_mismatch_pixels':vis['non_nearest_mismatch_pixels'],
              'bootstrap_fit_pixels':bootstrap_fit_pixels,
              'canonical_depth_abs_error_m':_stats(canonical_depth_err),
              'depth_tolerance_m':DEPTH_GEOM_TOL_M,
              'binding_bound_px':RENDERER_PP_BINDING_MAX_PX,
              'error':f'{type(exc).__name__}:{exc}',
              'canonical_K':np.asarray(request['camera']['K'],dtype=np.float64).tolist(),
              'r5_addendum_drive_id':R5_ADDENDUM_DRIVE_ID,
              'r6_addendum_drive_id':R6_ADDENDUM_DRIVE_ID,
              'r7_addendum_drive_id':R7_ADDENDUM_DRIVE_ID,
              'r8_addendum_drive_id':R8_ADDENDUM_DRIVE_ID,
              'r11_addendum_drive_id':R11_ADDENDUM_DRIVE_ID,
              'r23_production_implementation_id':R21_LAB_IMPLEMENTATION_ID,
              'depth_rescue_fitmask_semantics':DEPTH_RESCUE_FITMASK_IMPLEMENTATION_ID,
              'visibility_bootstrap_semantics':VISIBILITY_BOOTSTRAP_IMPLEMENTATION_ID,
              'production_authorized':True,
            }
            (sample_dir/'renderer_binding_diagnostic.json').write_text(json.dumps(diag,indent=2,sort_keys=True)+'\n',encoding='utf-8')
            r21_fit_failure_diagnostic=diag
            # Keep canonical K as a temporary diagnostic base. The R21 lab may
            # search the full inherited box below; this never promotes a result.
            binding_mode='R21_LAB_SAFE_R7_FAILED_GLOBAL_COARSE_FALLBACK'
            binding={
                'binding_status':binding_mode,'fit_invoked':True,'fit_failed':True,
                'fit_failure_error':diag['error'],'delta_cx_px':0.0,'delta_cy_px':0.0,
                'bound_px':RENDERER_PP_BINDING_MAX_PX,'fit_pixels':bootstrap_fit_pixels,
                'rank':None,'iterations':0,'last_step_px':[0.0,0.0],
                'finite_difference_epsilon_px':RENDERER_PP_FD_EPS_PX,
                'K_effective':np.asarray(request['camera']['K'],dtype=np.float64).tolist(),
                'visibility_bootstrap':bool(not canonical_object_ok),
                'bootstrap_fit_pixels':bootstrap_fit_pixels,
                'r23_production_authorized':True,
            }
            pred_t_effective=pred_t_canonical
            effective_vis=vis
        else:
            binding['binding_status']=binding_mode
            binding['fit_invoked']=True
            binding['visibility_bootstrap']=bool(not canonical_object_ok)
            binding['bootstrap_fit_pixels']=bootstrap_fit_pixels
            pred_t_effective=binding.pop('pred_t')
            binding.pop('pred_id',None)
            K_eff=np.asarray(binding['K_effective'],dtype=np.float64)
            T_eff,F_eff=_hit_stack_with_faces(request,C,h,w,K_override=K_eff)
            effective_vis=_exact_conearest_identity_from_stack(
                T_eff,oid,face_stack=F_eff,plane_signatures=plane_signatures)
            r21_safe_base_binding=dict(binding)

    effective_depth_err=np.abs(depth_obj-pred_t_effective[objmask]) if depth_obj.size else np.asarray([],dtype=np.float64)
    effective_identity_ok=bool(effective_vis['exact_all']) and ids_ok
    r18_refinement=None
    if binding is not None and depth_positive and effective_identity_ok and effective_depth_err.size and not np.all(effective_depth_err<=DEPTH_GEOM_TOL_M):
        r18_refinement=_r18_refine_renderer_effective_pp_minimax(request,C,depth,oid,binding)
        pred_t_effective=r18_refinement['pred_t']
        effective_vis=r18_refinement['effective_vis']
        effective_depth_err=np.abs(depth_obj-pred_t_effective[objmask])
        effective_identity_ok=bool(effective_vis['exact_all']) and ids_ok
        binding['r18_minimax_refinement']={k:v for k,v in r18_refinement.items() if k not in {'pred_t','effective_vis'}}
        binding['delta_cx_px']=float(r18_refinement['selected_delta_cx_px'])
        binding['delta_cy_px']=float(r18_refinement['selected_delta_cy_px'])
        binding['K_effective']=r18_refinement['K_effective']
        binding['final_binding_implementation_id']=R18_REFINEMENT_IMPLEMENTATION_ID
    object_ok=effective_identity_ok
    depth_ok=bool(depth_positive and effective_identity_ok and effective_depth_err.size and np.all(effective_depth_err<=DEPTH_GEOM_TOL_M))

    # R20: Normal does not fit or refine the renderer-effective raster binding.
    # It consumes the already-final K_effective selected independently by the
    # inherited Depth/Object pipeline, so all auxiliary GT channels describe
    # the same renderer raster. Raw unit-normal authority and tolerances remain
    # unchanged. If no accepted effective binding exists, canonical K remains
    # the Normal reference exactly.
    normal_reference_k_source='CANONICAL_REQUEST_K'
    normal_reference_delta_px=[0.0,0.0]
    if binding is not None and effective_identity_ok:
        K_norm=np.asarray(binding['K_effective'],dtype=np.float64)
        _dcv_norm,dw_norm=_ray_grid(request,h,w,K_override=K_norm)
        nvis_norm=[]; face_norm=[]; flip_norm=[]
        for obj in request['scene']['objects']:
            _t,nc,face=_object_hit_surface(C,dw_norm,obj)
            nvis,flip=_renderer_visible_side_normal(nc,dw_norm)
            nvis_norm.append(nvis); face_norm.append(face); flip_norm.append(flip)
        pred_ncan=np.zeros((h,w,3),dtype=np.float64)
        analytic_face_labels=np.full((h,w),-1,dtype=np.int32)
        visible_backface_pixels=0
        for j,(nc,face,flip) in enumerate(zip(nvis_norm,face_norm,flip_norm),1):
            m=(oid==j)
            pred_ncan[m]=nc[m]
            visible_backface_pixels += int(np.count_nonzero(m & flip))
            analytic_face_labels[m]=(j-1)*6 + face[m].astype(np.int32)
        pred_nb=np.einsum('ij,hwj->hwi',BFC,pred_ncan)
        derived_ncan=np.einsum('ij,hwj->hwi',CFB,raw)
        mag=np.linalg.norm(raw,axis=-1)
        authority=objmask & np.isfinite(raw).all(axis=-1) & np.isfinite(mag) & (np.abs(mag-1.0)<=NORMAL_TOL)
        auth_count=int(authority.sum()); obj_count=int(objmask.sum())
        auth_frac=float(auth_count/obj_count) if obj_count else 0.0
        raw_err_map=np.linalg.norm(raw-pred_nb,axis=-1)
        can_err_map=np.linalg.norm(derived_ncan-pred_ncan,axis=-1)
        raw_err=raw_err_map[authority]
        can_err=can_err_map[authority]
        filter_safe=_filter_safe_interior_mask(oid,analytic_face_labels,filter_radius)
        filter_safe_count=int(filter_safe.sum())
        filter_safe_auth=(filter_safe & authority)
        filter_safe_auth_count=int(filter_safe_auth.sum())
        filter_safe_auth_frac=float(filter_safe_auth_count/filter_safe_count) if filter_safe_count else 0.0
        safe_raw_err=raw_err_map[filter_safe_auth]
        safe_can_err=can_err_map[filter_safe_auth]
        invalid_obj=objmask & ~authority
        unexplained_invalid=invalid_obj & filter_safe
        unexplained_count=int(unexplained_invalid.sum())
        boundary_explained=invalid_obj & ~filter_safe
        boundary_explained_count=int(boundary_explained.sum())
        invalid_count=int(invalid_obj.sum())
        boundary_explained_frac=float(boundary_explained_count/invalid_count) if invalid_count else 1.0
        normal_ok=bool(filter_safe_count>0 and filter_safe_auth_frac>=MIN_NORMAL_AUTHORITY_FRACTION and unexplained_count==0 and safe_raw_err.size and np.all(safe_raw_err<=NORMAL_GEOM_TOL) and np.all(safe_can_err<=NORMAL_GEOM_TOL))
        normal_reference_k_source='FINAL_RENDERER_EFFECTIVE_K'
        normal_reference_delta_px=[float(binding.get('delta_cx_px',0.0)),float(binding.get('delta_cy_px',0.0))]

    # R21 systemic-repair lab. Run only when the inherited final full-raster
    # Object/Depth/Normal adjudication is not already all-pass. Candidate K is
    # selected exclusively from rendered Object Index + Depth; Normal is evaluated
    # only after selection and can never steer the raster binding.
    r21_binding_lab={
        'schema':'DF-G100-R23-SYSTEMIC-BINDING-PRODUCTION-V1',
        'implementation_id':R21_LAB_IMPLEMENTATION_ID,
        'lab_only':False,'production_authorized':True,
        'sample_id':request.get('sample_id'),
        'triggered':bool(not (object_ok and depth_ok and normal_ok)),
        'baseline':{
            'object_status':'PASS' if object_ok else 'FAIL',
            'depth_status':'PASS' if depth_ok else 'FAIL',
            'normal_status':'PASS' if normal_ok else 'FAIL',
            'binding_mode':binding_mode,
        },
        'safe_r7_fit_failure':r21_fit_failure_diagnostic,
        'global_coarse_fallback':None,
        'radius_trials':[],
        'selected_all_gt_pass':False,
        'selected_radius_steps':None,
        'rendered_normal_used_in_selection':False,
        'threshold_used_in_selection':False,
        'thresholds_unchanged':{'depth_tolerance_m':DEPTH_GEOM_TOL_M,'normal_tolerance':NORMAL_GEOM_TOL},
        'principal_point_bound_px':RENDERER_PP_BINDING_MAX_PX,
        'microstep_px':R18_MICROSTEP_PX,
    }
    if r21_binding_lab['triggered'] and ids_ok and depth_positive and binding is not None:
        # Safe-R7 is the normal center. If it could not form a finite base, use
        # the explicitly diagnostic-only global coarse lattice to learn whether
        # a bounded solution exists, then refine around that deterministic base.
        base_for_r21=r21_safe_base_binding
        if base_for_r21 is None:
            try:
                coarse=_r21_global_coarse_renderer_effective_pp_search(request,C,depth,oid)
                r21_binding_lab['global_coarse_fallback']={k:v for k,v in coarse.items() if k not in {'pred_t','effective_vis'}}
                base_for_r21={
                    'delta_cx_px':float(coarse['selected_delta_cx_px']),
                    'delta_cy_px':float(coarse['selected_delta_cy_px']),
                    'K_effective':coarse['K_effective'],
                }
            except Exception as exc:
                r21_binding_lab['global_coarse_fallback']={
                    'status':'FAIL','error':f'{type(exc).__name__}:{exc}',
                    'production_authorized':True,
                }
        if base_for_r21 is not None:
            for radius in R21_LAB_RADII:
                try:
                    cand=_r21_generalized_renderer_effective_pp_refine(request,C,depth,oid,base_for_r21,radius)
                    cand_pred=cand['pred_t']; cand_vis=cand['effective_vis']
                    cand_err=np.abs(depth_obj-cand_pred[objmask]) if depth_obj.size else np.asarray([],dtype=np.float64)
                    cand_obj_ok=bool(cand_vis['exact_all']) and ids_ok
                    cand_depth_ok=bool(depth_positive and cand_obj_ok and cand_err.size and np.all(cand_err<=DEPTH_GEOM_TOL_M))
                    ne=_r21_normal_eval_for_K(request,C,raw,oid,objmask,filter_radius,np.asarray(cand['K_effective'],dtype=np.float64))
                    cand_normal_ok=bool(ne['normal_ok'])
                    trial={k:v for k,v in cand.items() if k not in {'pred_t','effective_vis'}}
                    trial.update({
                        'object_status':'PASS' if cand_obj_ok else 'FAIL',
                        'depth_status':'PASS' if cand_depth_ok else 'FAIL',
                        'normal_status':'PASS' if cand_normal_ok else 'FAIL',
                        'full_raster_depth_abs_error_m':_stats(cand_err),
                        'normal_filter_safe_interior_authority_fraction':float(ne['filter_safe_auth_frac']),
                        'normal_unexplained_invalid_interior_pixels':int(ne['unexplained_count']),
                        'normal_raw_blender_vs_analytic_error':_stats(ne['raw_err']),
                        'normal_canonical_vs_analytic_error':_stats(ne['can_err']),
                        'all_gt_pass':bool(cand_obj_ok and cand_depth_ok and cand_normal_ok),
                    })
                    r21_binding_lab['radius_trials'].append(trial)
                    if cand_obj_ok and cand_depth_ok and cand_normal_ok:
                        pred_t_effective=cand_pred
                        effective_vis=cand_vis
                        effective_depth_err=cand_err
                        effective_identity_ok=True
                        object_ok=True; depth_ok=True; normal_ok=True
                        binding['delta_cx_px']=float(cand['selected_delta_cx_px'])
                        binding['delta_cy_px']=float(cand['selected_delta_cy_px'])
                        binding['K_effective']=cand['K_effective']
                        binding['r21_generalized_minimax_refinement']=trial
                        binding['final_binding_implementation_id']=R21_LAB_IMPLEMENTATION_ID
                        binding['r21_lab_only']=True
                        pred_ncan=ne['pred_ncan']; analytic_face_labels=ne['analytic_face_labels']
                        visible_backface_pixels=ne['visible_backface_pixels']; authority=ne['authority']
                        auth_count=ne['auth_count']; obj_count=ne['obj_count']; auth_frac=ne['auth_frac']
                        raw_err=ne['raw_err']; can_err=ne['can_err']; filter_safe=ne['filter_safe']
                        filter_safe_count=ne['filter_safe_count']; filter_safe_auth_count=ne['filter_safe_auth_count']
                        filter_safe_auth_frac=ne['filter_safe_auth_frac']; invalid_obj=ne['invalid_obj']
                        unexplained_count=ne['unexplained_count']; boundary_explained_count=ne['boundary_explained_count']
                        invalid_count=ne['invalid_count']; boundary_explained_frac=ne['boundary_explained_frac']
                        normal_reference_k_source='R23_PRODUCTION_FINAL_RENDERER_EFFECTIVE_K'
                        normal_reference_delta_px=[float(cand['selected_delta_cx_px']),float(cand['selected_delta_cy_px'])]
                        r21_binding_lab['selected_all_gt_pass']=True
                        r21_binding_lab['selected_radius_steps']=int(radius)
                        break
                except Exception as exc:
                    r21_binding_lab['radius_trials'].append({
                        'radius_steps':int(radius),'status':'FAIL_EVALUATION',
                        'error':f'{type(exc).__name__}:{exc}',
                        'all_gt_pass':False,
                    })
    # R23: if inherited/local systemic refinement still does not pass all GT,
    # evaluate the complete fixed global bounded hierarchy. Normal never selects K.
    r23_global_pp=None
    if ids_ok and depth_positive and not (object_ok and depth_ok and normal_ok):
        try:
            gp=_r23_global_bounded_pp_search(request,C,depth,oid)
            gp_pred=gp['pred_t']; gp_vis=gp['effective_vis']
            gp_err=np.abs(depth_obj-gp_pred[objmask]) if depth_obj.size else np.asarray([],dtype=np.float64)
            gp_obj_ok=bool(gp_vis['exact_all']) and ids_ok
            gp_depth_ok=bool(depth_positive and gp_obj_ok and gp_err.size and np.all(gp_err<=DEPTH_GEOM_TOL_M))
            ne=_r21_normal_eval_for_K(request,C,raw,oid,objmask,filter_radius,np.asarray(gp['K_effective'],dtype=np.float64))
            gp_normal_ok=bool(ne['normal_ok'])
            r23_global_pp={k:v for k,v in gp.items() if k not in {'pred_t','effective_vis'}}
            r23_global_pp.update({'object_status':'PASS' if gp_obj_ok else 'FAIL','depth_status':'PASS' if gp_depth_ok else 'FAIL',
                                  'normal_status':'PASS' if gp_normal_ok else 'FAIL','full_raster_depth_abs_error_m':_stats(gp_err),
                                  'normal_semantics':R23_NORMAL_SEMANTICS_ID,'production_authorized':True})
            if gp_obj_ok and gp_depth_ok and gp_normal_ok:
                pred_t_effective=gp_pred; effective_vis=gp_vis; effective_depth_err=gp_err; effective_identity_ok=True
                object_ok=True; depth_ok=True; normal_ok=True
                if binding is None: binding={}
                binding['delta_cx_px']=float(gp['selected_delta_cx_px']); binding['delta_cy_px']=float(gp['selected_delta_cy_px'])
                binding['K_effective']=gp['K_effective']; binding['r23_global_bounded_pp']=r23_global_pp
                binding['final_binding_implementation_id']=R23_GLOBAL_PP_IMPLEMENTATION_ID
                pred_ncan=ne['pred_ncan']; analytic_face_labels=ne['analytic_face_labels']; visible_backface_pixels=ne['visible_backface_pixels']
                authority=ne['authority']; auth_count=ne['auth_count']; obj_count=ne['obj_count']; auth_frac=ne['auth_frac']
                raw_err=ne['raw_err']; can_err=ne['can_err']; safe_raw_err=ne['safe_raw_err']; safe_can_err=ne['safe_can_err']
                filter_safe=ne['filter_safe']; filter_safe_count=ne['filter_safe_count']; filter_safe_auth_count=ne['filter_safe_auth_count']
                filter_safe_auth_frac=ne['filter_safe_auth_frac']; invalid_obj=ne['invalid_obj']; unexplained_count=ne['unexplained_count']
                boundary_explained_count=ne['boundary_explained_count']; invalid_count=ne['invalid_count']; boundary_explained_frac=ne['boundary_explained_frac']
                normal_reference_k_source='R23_GLOBAL_FINAL_RENDERER_EFFECTIVE_K'
                normal_reference_delta_px=[float(gp['selected_delta_cx_px']),float(gp['selected_delta_cy_px'])]
        except Exception as exc:
            r23_global_pp={'status':'FAIL_EVALUATION','error':f'{type(exc).__name__}:{exc}','production_authorized':True}

    # R29: keep every inherited camera/binding search and full-raster diagnostic
    # unchanged, then define the exact Depth authority domain from renderer
    # reconstruction-filter support. This correction cannot steer K or relax the
    # 1e-4 m tolerance; it only marks silhouette/crease boundary samples as
    # non-authoritative exact Depth while retaining them as immutable diagnostics.
    r29_depth=_r29_depth_authority_adjudication(
        depth,pred_t_effective,oid,analytic_face_labels,renderer_filter_width_px=filter_width)
    depth_ok=bool(object_ok and r29_depth['status']=='PASS')
    depth_filter_safe=np.asarray(r29_depth.pop('safe_mask'),dtype=bool)
    r29_depth.pop('error_map',None)
    r29_depth.pop('full_over_mask',None)
    r29_depth.pop('safe_over_mask',None)
    r29_depth.pop('boundary_mask',None)

    r21_binding_lab['final']={
        'object_status':'PASS' if object_ok else 'FAIL',
        'depth_status':'PASS' if depth_ok else 'FAIL',
        'normal_status':'PASS' if normal_ok else 'FAIL',
        'binding_delta_px':([float(binding.get('delta_cx_px',0.0)),float(binding.get('delta_cy_px',0.0))] if binding is not None else None),
    }
    r21_binding_lab_path=sample_dir/'r21_binding_lab.json'
    r21_binding_lab_path.write_text(json.dumps(r21_binding_lab,indent=2,sort_keys=True)+'\n',encoding='utf-8')

    mask_path=sample_dir/'normal_authority_mask.uint8.bin'
    mask_path.write_bytes(authority.astype(np.uint8).tobytes(order='C'))
    filter_safe_path=sample_dir/'normal_filter_safe_interior_mask.uint8.bin'
    filter_safe_path.write_bytes(filter_safe.astype(np.uint8).tobytes(order='C'))
    depth_filter_safe_path=sample_dir/'depth_filter_safe_interior_mask.uint8.bin'
    depth_filter_safe_path.write_bytes(depth_filter_safe.astype(np.uint8).tobytes(order='C'))
    report={
      'schema':'DF-G100-PER-SAMPLE-AUX-GT-QA-V7-R23-PRODUCTION',
      'status':'PASS' if object_ok and depth_ok and normal_ok else 'FAIL',
      'sample_id':request['sample_id'], 'width':w,'height':h,
      'r3_addendum_drive_id':R3_ADDENDUM_DRIVE_ID,
      'r4_addendum_drive_id':R4_ADDENDUM_DRIVE_ID,
      'r5_addendum_drive_id':R5_ADDENDUM_DRIVE_ID,
      'r6_addendum_drive_id':R6_ADDENDUM_DRIVE_ID,
      'r7_addendum_drive_id':R7_ADDENDUM_DRIVE_ID,
      'r8_addendum_drive_id':R8_ADDENDUM_DRIVE_ID,
      'r11_addendum_drive_id':R11_ADDENDUM_DRIVE_ID,
      'r12_addendum_drive_id':R12_ADDENDUM_DRIVE_ID,
      'r29_spec_drive_id':R29_SPEC_DRIVE_ID,
      'object_index':{
        'status':'PASS' if object_ok else 'FAIL','max_fractional_error':float(np.max(fracerr)),
        'id_range_valid':ids_ok,
        # Backward-compatible singular argmin keys remain diagnostic only.
        'analytic_identity_match_pixels':vis['singular_match_pixels'],
        'analytic_identity_match_fraction':vis['singular_match_fraction'],
        'singular_argmin_match_pixels':vis['singular_match_pixels'],
        'singular_argmin_match_fraction':vis['singular_match_fraction'],
        'exact_conearest_match_pixels':vis['exact_match_pixels'],
        'exact_conearest_match_fraction':vis['exact_match_fraction'],
        'exact_tie_pixel_count':vis['exact_tie_pixel_count'],
        'exact_tie_pair_histogram':vis['tie_pair_histogram'],
        'bitwise_exact_match_pixels':vis['bitwise_exact_match_pixels'],
        'bitwise_exact_match_fraction':vis['bitwise_exact_match_fraction'],
        'exact_geometric_coincident_face_match_pixels':vis['geometric_coincident_match_pixels'],
        'exact_geometric_coincident_face_match_fraction':vis['geometric_coincident_match_fraction'],
        'exact_geometric_coincident_face_pair_histogram':vis['geometric_coincident_pair_histogram'],
        'non_nearest_mismatch_pixels':vis['non_nearest_mismatch_pixels'],
        'canonical_exact_all':bool(vis['exact_all']),
        'canonical_non_nearest_mismatch_pixels':vis['non_nearest_mismatch_pixels'],
        'renderer_effective_exact_all':bool(effective_vis['exact_all']),
        'renderer_effective_exact_conearest_match_pixels':effective_vis['exact_match_pixels'],
        'renderer_effective_exact_conearest_match_fraction':effective_vis['exact_match_fraction'],
        'renderer_effective_exact_tie_pixel_count':effective_vis['exact_tie_pixel_count'],
        'renderer_effective_bitwise_exact_match_pixels':effective_vis['bitwise_exact_match_pixels'],
        'renderer_effective_geometric_coincident_face_match_pixels':effective_vis['geometric_coincident_match_pixels'],
        'renderer_effective_geometric_coincident_face_pair_histogram':effective_vis['geometric_coincident_pair_histogram'],
        'renderer_effective_non_nearest_mismatch_pixels':effective_vis['non_nearest_mismatch_pixels'],
        'visibility_bootstrap_semantics':VISIBILITY_BOOTSTRAP_IMPLEMENTATION_ID,
        'final_authority_semantics':R19_VISIBILITY_IMPLEMENTATION_ID,
        'visibility_identity_semantics':R19_VISIBILITY_IMPLEMENTATION_ID,
        'legacy_bitwise_tie_semantics':VISIBILITY_TIE_IMPLEMENTATION_ID,
        'identity_epsilon':0.0,
        'numeric_visibility_epsilon':R19_NUMERIC_VISIBILITY_EPSILON,
        'plane_signature_representation_semantics':R27_PLANE_SIGNATURE_IMPLEMENTATION_ID,
        'r27_signed_permutation_ulps':R27_SIGNED_PERMUTATION_ULPS,
        'r27_spec_drive_id':R27_SPEC_DRIVE_ID,
        'object_pixels':obj_count,'background_pixels':int(bg.sum()),'positive_ids_observed':[int(x) for x in np.unique(oid) if x>0],
      },
      'depth':{
        'status':'PASS' if depth_ok else 'FAIL','definition':'camera_cv_forward_z_meters','positive_finite_object_pixels':depth_positive,
        'analytic_abs_error_m':_stats(effective_depth_err),'tolerance_m':DEPTH_GEOM_TOL_M,
        'acceptance_semantics':R29_DEPTH_AUTHORITY_SEMANTICS_ID,
        'authority_semantics':R29_DEPTH_AUTHORITY_SEMANTICS_ID,
        'r29_spec_drive_id':R29_SPEC_DRIVE_ID,
        'full_raster_depth_abs_error_m':r29_depth['full_raster_depth_abs_error_m'],
        'full_raster_over_tolerance_pixels':r29_depth['full_raster_over_tolerance_pixels'],
        'filter_safe_interior_pixels':r29_depth['filter_safe_interior_pixels'],
        'filter_safe_interior_fraction_of_object_pixels':r29_depth['filter_safe_interior_fraction_of_object_pixels'],
        'filter_safe_depth_abs_error_m':r29_depth['filter_safe_depth_abs_error_m'],
        'filter_safe_over_tolerance_pixels':r29_depth['filter_safe_over_tolerance_pixels'],
        'boundary_object_pixels':r29_depth['boundary_object_pixels'],
        'boundary_over_tolerance_pixels':r29_depth['boundary_over_tolerance_pixels'],
        'renderer_filter_width_px':r29_depth['renderer_filter_width_px'],
        'renderer_filter_width_expected_px':r29_depth['renderer_filter_width_expected_px'],
        'renderer_filter_width_status':r29_depth['renderer_filter_width_status'],
        'filter_support_radius_px':r29_depth['filter_support_radius_px'],
        'non_authoritative_boundary_semantics':'NONAUTHORITATIVE_BOUNDARY_DEPTH',
        'filter_safe_interior_mask':{'path':depth_filter_safe_path.name,'bytes':depth_filter_safe_path.stat().st_size,'sha256':sha256_file(depth_filter_safe_path)},
        'raw_exr_immutable':True,
        'canonical_K_analytic_abs_error_m':_stats(canonical_depth_err),
        'canonical_K_depth_status':'PASS' if canonical_depth_ok else 'FAIL',
        'renderer_binding_mode':binding_mode,
        'renderer_binding_fitmask_semantics':DEPTH_RESCUE_FITMASK_IMPLEMENTATION_ID,
        'renderer_binding_fitmask_independent_of_normal_authority':True,
        'renderer_effective_analytic_abs_error_m':_stats(effective_depth_err),
        'renderer_effective_identity_match_fraction':effective_vis['exact_match_fraction'],
        'renderer_effective_exact_tie_pixel_count':effective_vis['exact_tie_pixel_count'],
        'renderer_effective_geometric_coincident_face_match_pixels':effective_vis['geometric_coincident_match_pixels'],
        'renderer_effective_non_nearest_mismatch_pixels':effective_vis['non_nearest_mismatch_pixels'],
        'renderer_effective_principal_point_binding':({
            'implementation_id':RENDERER_BINDING_IMPLEMENTATION_ID,
            **binding,
            'fx_fitted':False,'fy_fitted':False,'pose_fitted':False,'depth_scale_fitted':False,
            'depth_offset_fitted':False,'per_object_fit':False,'nonlinear_warp':False,
        } if binding is not None else None),
        'background_unique_values':[float(x) for x in np.unique(depth[bg])[:16]] if bg.any() else [],
      },
      'normal':{
        'status':'PASS' if normal_ok else 'FAIL','raw_frame':'BLENDER_WORLD_BASIS','canonical_frame':'PCS_CANONICAL_WORLD_RIGHT_HANDED_Y_UP',
        'reference_implementation_id':R20_NORMAL_REFERENCE_IMPLEMENTATION_ID,
        'reference_K_source':normal_reference_k_source,
        'reference_renderer_effective_delta_px':normal_reference_delta_px,
        'normal_values_used_to_fit_renderer_binding':False,
        'C_FROM_B':[list(r) for r in C_FROM_B],'normal_unit_tolerance':NORMAL_TOL,'analytic_tolerance':NORMAL_GEOM_TOL,
        'object_pixels':obj_count,'authority_pixels':auth_count,'invalid_object_pixels':invalid_count,
        # Backward-compatible raw/global metric remains exact diagnostic evidence.
        'authority_fraction':auth_frac,'raw_global_authority_fraction':auth_frac,
        'acceptance_fraction_semantics':'FILTER_SAFE_INTERIOR_AUTHORITY_FRACTION_R6',
        'min_authority_fraction':MIN_NORMAL_AUTHORITY_FRACTION,
        'renderer_filter_width_px':filter_width,'renderer_filter_width_expected_px':G100_CYCLES_FILTER_WIDTH_PX,
        'renderer_filter_width_status':'PASS' if filter_width_ok else 'FAIL','filter_support_radius_px':filter_radius,
        'filter_safe_interior_pixels':filter_safe_count,
        'filter_safe_interior_authority_pixels':filter_safe_auth_count,
        'filter_safe_interior_authority_fraction':filter_safe_auth_frac,
        'unexplained_invalid_interior_pixels':unexplained_count,
        'boundary_explained_invalid_pixels':boundary_explained_count,
        'boundary_explained_invalid_fraction':boundary_explained_frac,
        'raw_blender_vs_analytic_error':_stats(raw_err),'canonical_vs_analytic_error':_stats(can_err),
        'filter_safe_raw_blender_vs_analytic_error':_stats(safe_raw_err),'filter_safe_canonical_vs_analytic_error':_stats(safe_can_err),
        'direction_error_acceptance_semantics':R23_NORMAL_SEMANTICS_ID,
        'authority_mask':{'path':mask_path.name,'bytes':mask_path.stat().st_size,'sha256':sha256_file(mask_path)},
        'filter_safe_interior_mask':{'path':filter_safe_path.name,'bytes':filter_safe_path.stat().st_size,'sha256':sha256_file(filter_safe_path)},
        'invalid_pixels_retain_zero_exact_authority':True,
        'raw_normal_renormalized':False,
        'visible_side_orientation_semantics':NORMAL_VISIBLE_SIDE_IMPLEMENTATION_ID,
        'visible_backface_exit_pixels':visible_backface_pixels,
        'arbitrary_sign_equivalence':False,
        'orientation_epsilon':0.0,
      },
      'r23_systemic_binding_production':r21_binding_lab,
      'r23_global_bounded_pp':r23_global_pp,
      'raster':{'convention':'DIRECT_TOP_LEFT_Y_DOWN_PIXEL_CENTER','hidden_flip':False,
                'renderer_effective_subpixel_binding':True,
                'renderer_effective_binding_bound_px':RENDERER_PP_BINDING_MAX_PX},
      'raw_exr_immutable':True,
    }
    out=sample_dir/'micro100_aux_gt_qa.json'
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if report['status']!='PASS':
        raise RuntimeError('G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:'+json.dumps({'object':report['object_index']['status'],'depth':report['depth']['status'],'normal':report['normal']['status']},sort_keys=True))
    # R29 activation is enforced inside the per-sample validator, before the
    # worker can advance from recovered sample005 to sample006.
    if request.get('sample_id')==R29_ACTIVATION_SAMPLE_ID:
        dep=report.get('depth') or {}
        act={
            'object_pass':report.get('object_index',{}).get('status')=='PASS',
            'normal_pass':report.get('normal',{}).get('status')=='PASS',
            'depth_pass':dep.get('status')=='PASS',
            'authority_semantics':dep.get('authority_semantics')==R29_DEPTH_AUTHORITY_SEMANTICS_ID,
            'r29_spec':dep.get('r29_spec_drive_id')==R29_SPEC_DRIVE_ID,
            'safe_over_tolerance_zero':int(dep.get('filter_safe_over_tolerance_pixels',-1))==0,
            'filter_width_exact':abs(float(dep.get('renderer_filter_width_px',float('nan')))-G100_CYCLES_FILTER_WIDTH_PX)<=1e-12,
            'filter_radius_exact':int(dep.get('filter_support_radius_px',-1))==int(math.ceil(G100_CYCLES_FILTER_WIDTH_PX)),
        }
        if not all(act.values()):
            raise RuntimeError('G100_R29_SAMPLE005_ACTIVATION_GUARD_FAIL:'+json.dumps(act,sort_keys=True))
    return report

