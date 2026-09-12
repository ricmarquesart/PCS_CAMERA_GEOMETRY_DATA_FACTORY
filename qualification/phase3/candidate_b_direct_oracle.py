from __future__ import annotations
import hashlib
import numpy as np
import candidate_b_reference as cb


def full_lattice_mask(request,old_safe,K_override=None,row_block=128):
    """Direct full-domain 49x49 Candidate-B lattice oracle.

    This intentionally does not use projected-edge culling. It evaluates the
    entire raster-aligned 1/16-px analytic signature grid, then applies every
    49x49 support window to every inherited old-safe pixel. Geometry-seeded edge
    witnesses are a separate Candidate-B family and are qualified independently.
    """
    old=np.asarray(old_safe,dtype=bool); H,W=old.shape
    yy,xx=np.indices((H,W),dtype=np.float64)
    co,cf,ca=cb.batch_signatures(request,np.column_stack([xx.ravel(),yy.ravel()]),K_override)
    co=co.reshape(H,W); cf=cf.reshape(H,W); ca=ca.reshape(H,W)

    xs=np.arange((W-1)*16+1,dtype=np.float64)/16.0
    ys=np.arange((H-1)*16+1,dtype=np.float64)/16.0
    go=np.empty((len(ys),len(xs)),dtype=np.int32)
    gf=np.empty((len(ys),len(xs)),dtype=np.int16)
    ga=np.empty((len(ys),len(xs)),dtype=bool)
    rb=max(1,int(row_block))
    for y0 in range(0,len(ys),rb):
        yv=ys[y0:y0+rb]; X,Y=np.meshgrid(xs,yv,indexing='xy')
        o,f,a=cb.batch_signatures(request,np.column_stack([X.ravel(),Y.ravel()]),K_override)
        go[y0:y0+len(yv)]=o.reshape(len(yv),len(xs)); gf[y0:y0+len(yv)]=f.reshape(len(yv),len(xs)); ga[y0:y0+len(yv)]=a.reshape(len(yv),len(xs))

    safe=old.copy(); ambiguous=np.zeros_like(old)
    cy=np.arange(H,dtype=np.int64)*16; cx=np.arange(W,dtype=np.int64)*16
    for dy in range(-24,25):
        gy=cy+dy; yok=(gy>=0)&(gy<go.shape[0]); yi=np.where(yok)[0]
        if not len(yi): continue
        for dx in range(-24,25):
            gx=cx+dx; xok=(gx>=0)&(gx<go.shape[1]); xi=np.where(xok)[0]
            if not len(xi): continue
            subo=go[np.ix_(gy[yi],gx[xi])]; subf=gf[np.ix_(gy[yi],gx[xi])]; suba=ga[np.ix_(gy[yi],gx[xi])]
            same=(subo==co[np.ix_(yi,xi)])&(subf==cf[np.ix_(yi,xi)])&(~suba)
            current=safe[np.ix_(yi,xi)]; current &= same; safe[np.ix_(yi,xi)]=current
            amb=ambiguous[np.ix_(yi,xi)]; amb |= suba&old[np.ix_(yi,xi)]; ambiguous[np.ix_(yi,xi)]=amb

    # Explicit closed-support bounds. In ordinary use the inherited radius-2
    # mask already excludes these, but the direct oracle remains fail-closed.
    for y,x in np.argwhere(old):
        x=int(x); y=int(y)
        if x-cb.FILTER_WIDTH_PX<0.0 or x+cb.FILTER_WIDTH_PX>W-1 or y-cb.FILTER_WIDTH_PX<0.0 or y+cb.FILTER_WIDTH_PX>H-1 or ca[y,x]:
            safe[y,x]=False
    return safe,{
        'schema':'DF-G101-PHASE3-CANDIDATE-B-DIRECT-FULL-LATTICE-ORACLE-V1',
        'old_safe_count':int(np.count_nonzero(old)),
        'lattice_safe_count':int(np.count_nonzero(safe)),
        'lattice_excluded_count':int(np.count_nonzero(old&~safe)),
        'ambiguity_pixels':int(np.count_nonzero(ambiguous&old)),
        'mask_sha256':hashlib.sha256(safe.astype(np.uint8).tobytes(order='C')).hexdigest(),
        'fine_grid_shape':[int(go.shape[0]),int(go.shape[1])],
    }
