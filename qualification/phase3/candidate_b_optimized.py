from __future__ import annotations
import hashlib
import math
from collections import Counter
import numpy as np
import candidate_b_reference as cb

RETENTION_FLOOR = 0.9783428720083247


def _reason(center, other, rendered_oid, x, y, H, W):
    r=cb._reason_for_transition(center,other,rendered_oid,x,y,H,W,False)
    return r or 'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT'


def _choose_reason(reasons):
    vals=[r for r in reasons if r]
    return min(vals,key=lambda r:cb.REASON_PRIORITY[r]) if vals else None


def analytic_centers(request,K_override=None):
    H=int(request['camera']['height']); W=int(request['camera']['width'])
    yy,xx=np.indices((H,W),dtype=np.float64)
    o,f,a=cb.batch_signatures(request,np.column_stack([xx.ravel(),yy.ravel()]),K_override)
    return o.reshape(H,W),f.reshape(H,W),a.reshape(H,W)


def inherited_r6_mask(rendered_oid, analytic_face_id, radius=2):
    oid=np.asarray(rendered_oid,dtype=np.int32); face=np.asarray(analytic_face_id,dtype=np.int32)
    if oid.shape!=face.shape: raise RuntimeError('PHASE3_R6_SHAPE_MISMATCH')
    labels=np.where(oid>0,(oid-1)*6+face,-1).astype(np.int32)
    stable=(oid>0)&(labels>=0); H,W=oid.shape
    for dy in range(-int(radius),int(radius)+1):
        for dx in range(-int(radius),int(radius)+1):
            if dx==0 and dy==0: continue
            y0=max(0,-dy);y1=min(H,H-dy);x0=max(0,-dx);x1=min(W,W-dx)
            same=np.zeros((H,W),dtype=bool)
            if y1>y0 and x1>x0:
                same[y0:y1,x0:x1]=(oid[y0:y1,x0:x1]==oid[y0+dy:y1+dy,x0+dx:x1+dx])&(labels[y0:y1,x0:x1]==labels[y0+dy:y1+dy,x0+dx:x1+dx])
            stable &= same
    return stable


def _edge_pairs(request,old_safe,K_override=None):
    H,W=old_safe.shape; out=[]; touched=set()
    for oi,edge_index,p0,p1 in cb.projected_edges(request,K_override):
        xmin=max(0,int(math.ceil(min(p0[0],p1[0])-cb.FILTER_WIDTH_PX-1e-12)))
        xmax=min(W-1,int(math.floor(max(p0[0],p1[0])+cb.FILTER_WIDTH_PX+1e-12)))
        ymin=max(0,int(math.ceil(min(p0[1],p1[1])-cb.FILTER_WIDTH_PX-1e-12)))
        ymax=min(H-1,int(math.floor(max(p0[1],p1[1])+cb.FILTER_WIDTH_PX+1e-12)))
        if xmin>xmax or ymin>ymax: continue
        pairs=[]
        for y in range(ymin,ymax+1):
            for x in range(xmin,xmax+1):
                if not old_safe[y,x]: continue
                clipped=cb._clip_segment(p0,p1,x-cb.FILTER_WIDTH_PX,x+cb.FILTER_WIDTH_PX,y-cb.FILTER_WIDTH_PX,y+cb.FILTER_WIDTH_PX)
                if clipped is not None:
                    pairs.append((x,y,clipped)); touched.add((x,y))
        if pairs: out.append((oi,edge_index,p0,p1,pairs))
    return out,touched


def edge_witness_exclusions(request,old_safe,rendered_oid,center_o,center_f,K_override=None):
    old=np.asarray(old_safe,dtype=bool); oid=np.asarray(rendered_oid,dtype=np.int32); H,W=old.shape
    edge_groups,touched=_edge_pairs(request,old,K_override)
    evidence={}
    pair_count=0
    for oi,edge_index,p0,p1,pairs in edge_groups:
        pair_count += len(pairs)
        edge=p1-p0; n=np.asarray([-edge[1],edge[0]],dtype=np.float64); nl=float(np.linalg.norm(n))
        if nl==0.0: continue
        n/=nl
        if not (n[0]>0.0 or (n[0]==0.0 and n[1]>=0.0)): n=-n
        probes=[]; meta=[]
        for pi,(x,y,(a,b)) in enumerate(pairs):
            d=b-a; L=float(np.linalg.norm(d)); qs=[a.copy()] if L==0.0 else [a+t*d for t in (0.25,0.5,0.75)]
            for q_index,q in enumerate(qs):
                for j in cb.DYADIC_JS:
                    dist=cb.FILTER_WIDTH_PX/(2**j); qp=q+dist*n; qm=q-dist*n
                    ok=(x-cb.FILTER_WIDTH_PX-1e-12<=qp[0]<=x+cb.FILTER_WIDTH_PX+1e-12 and y-cb.FILTER_WIDTH_PX-1e-12<=qp[1]<=y+cb.FILTER_WIDTH_PX+1e-12 and 0.0<=qp[0]<=W-1 and 0.0<=qp[1]<=H-1 and x-cb.FILTER_WIDTH_PX-1e-12<=qm[0]<=x+cb.FILTER_WIDTH_PX+1e-12 and y-cb.FILTER_WIDTH_PX-1e-12<=qm[1]<=y+cb.FILTER_WIDTH_PX+1e-12 and 0.0<=qm[0]<=W-1 and 0.0<=qm[1]<=H-1)
                    if ok:
                        k=len(probes); probes.extend([qp,qm]); meta.append((pi,q_index,j,dist,k))
        if not probes: continue
        po,pf,pa=cb.batch_signatures(request,np.asarray(probes,dtype=np.float64),K_override)
        best=[None]*len(pairs)
        for pi,q_index,j,dist,k in meta:
            x,y,_=pairs[pi]; center=(int(center_o[y,x]),int(center_f[y,x])); sp=(int(po[k]),int(pf[k])); sm=(int(po[k+1]),int(pf[k+1])); ambiguous=bool(pa[k] or pa[k+1])
            if not ambiguous and not (sp!=sm and (sp!=center or sm!=center)): continue
            if ambiguous:
                reason='UNCLASSIFIED_ANALYTIC_AMBIGUITY'
            else:
                reason=_choose_reason([_reason(center,sp,oid,x,y,H,W) if sp!=center else None,_reason(center,sm,oid,x,y,H,W) if sm!=center else None])
            witness={'reason':reason,'edge_object_id':int(oi),'edge_index':int(edge_index),'q_index':int(q_index),'dyadic_j':int(j),'distance_px':float(dist),'plus_signature':sp,'minus_signature':sm}
            if best[pi] is None or cb.REASON_PRIORITY[reason]<cb.REASON_PRIORITY[best[pi]['reason']]: best[pi]=witness
        for pi,witness in enumerate(best):
            if witness is None: continue
            x,y,_=pairs[pi]; p=(x,y)
            if p not in evidence or cb.REASON_PRIORITY[witness['reason']]<cb.REASON_PRIORITY[evidence[p]['reason']]: evidence[p]=witness
    return evidence,touched,pair_count


def evaluate_mask(request,old_safe,rendered_oid,K_override=None,lattice_batch_pixels=32):
    old=np.asarray(old_safe,dtype=bool); oid=np.asarray(rendered_oid,dtype=np.int32)
    if old.shape!=oid.shape: raise RuntimeError('PHASE3_B_MASK_SHAPE_MISMATCH')
    H,W=old.shape; center_o,center_f,center_a=analytic_centers(request,K_override)
    safe=old.copy(); reasons={}; evidence={}

    # Complete support and center ambiguity are fail-closed even if a malformed
    # caller supplies an old mask containing such pixels.
    for y,x in np.argwhere(old):
        x=int(x); y=int(y)
        if x-cb.FILTER_WIDTH_PX<0.0 or x+cb.FILTER_WIDTH_PX>W-1 or y-cb.FILTER_WIDTH_PX<0.0 or y+cb.FILTER_WIDTH_PX>H-1:
            safe[y,x]=False; reasons[(x,y)]='IMAGE_BOUND_SUPPORT_INCOMPLETE'
        elif center_a[y,x]:
            safe[y,x]=False; reasons[(x,y)]='UNCLASSIFIED_ANALYTIC_AMBIGUITY'

    witness,touched,pair_count=edge_witness_exclusions(request,old,oid,center_o,center_f,K_override)
    for p,w in witness.items():
        x,y=p; safe[y,x]=False; reasons[p]=w['reason']; evidence[p]=w

    # Optimization hypothesis: every continuous signature boundary for the frozen
    # cuboid scene model lies on projected primitive geometry. Therefore the full
    # 49x49 lattice is required only for old-safe supports touched by such geometry.
    # Qualification must prove exact equality to the direct full-domain reference.
    evalpix=sorted((p for p in touched if safe[p[1],p[0]]),key=lambda p:(p[1],p[0]))
    offs=np.asarray([-cb.FILTER_WIDTH_PX+k*cb.LATTICE_STEP_PX for k in range(49)],dtype=np.float64)
    DU,DV=np.meshgrid(offs,offs,indexing='xy'); delta=np.column_stack([DU.ravel(),DV.ravel()])
    lattice_only=0
    batch=max(1,int(lattice_batch_pixels))
    for s0 in range(0,len(evalpix),batch):
        pp=evalpix[s0:s0+batch]; base=np.asarray(pp,dtype=np.float64)
        pts=(base[:,None,:]+delta[None,:,:]).reshape(-1,2)
        bo,bf,ba=cb.batch_signatures(request,pts,K_override)
        bo=bo.reshape(len(pp),-1); bf=bf.reshape(len(pp),-1); ba=ba.reshape(len(pp),-1)
        for i,(x,y) in enumerate(pp):
            center=(int(center_o[y,x]),int(center_f[y,x]))
            if bool(np.any(ba[i])):
                reason='UNCLASSIFIED_ANALYTIC_AMBIGUITY'; detail={'lattice_ambiguity':True}
            else:
                diff=(bo[i]!=center[0])|(bf[i]!=center[1])
                if not np.any(diff): continue
                k=int(np.flatnonzero(diff)[0]); other=(int(bo[i,k]),int(bf[i,k])); reason=_reason(center,other,oid,x,y,H,W); detail={'lattice_signature':other,'lattice_index':k}
            safe[y,x]=False; reasons[(x,y)]=reason; evidence[(x,y)]={'reason':reason,**detail}; lattice_only+=1

    old_count=int(np.count_nonzero(old)); new_count=int(np.count_nonzero(safe)); retention=float(new_count/old_count) if old_count else 1.0
    return safe,{
        'schema':'DF-G101-PHASE3-CANDIDATE-B-OPTIMIZED-QUALIFICATION-V1',
        'method_id':cb.METHOD_ID,
        'old_safe_count':old_count,
        'new_safe_count':new_count,
        'excluded_count':old_count-new_count,
        'retained_fraction':retention,
        'mask_sha256':hashlib.sha256(safe.astype(np.uint8).tobytes(order='C')).hexdigest(),
        'reason_counts':dict(Counter(reasons.values())),
        'edge_touched_old_safe_count':len(touched),
        'edge_pixel_pairs':int(pair_count),
        'witness_exclusion_count':len(witness),
        'lattice_only_exclusion_count':int(lattice_only),
        'reason_by_pixel':reasons,
        'evidence_by_pixel':evidence,
    }


def require_retention(result,floor=RETENTION_FLOOR):
    value=float(result['retained_fraction'])
    if value+0.0 < float(floor):
        raise RuntimeError('PHASE3_CANDIDATE_B_RETENTION_BELOW_FROZEN_FLOOR:'+str(value))
    return True
