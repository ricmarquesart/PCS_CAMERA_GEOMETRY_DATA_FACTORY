from __future__ import annotations
import itertools
import numpy as np

FILTER_WIDTH_PX = 1.5
LATTICE_STEP_PX = 1.0 / 16.0
DYADIC_JS = tuple(range(5, 17))
METHOD_ID = 'DF_G101_POST_R2_GEOMETRY_SEEDED_SUBPIXEL_VISIBILITY_REFERENCE_B_V1'
REASON_PRIORITY = {
    'IMAGE_BOUND_SUPPORT_INCOMPLETE': 1,
    'SUBPIXEL_THIN_OCCLUDER_SUPPORT': 2,
    'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT': 3,
    'CONTINUOUS_FACE_NORMAL_DISCONTINUITY_SUPPORT': 4,
    'CONTINUOUS_OBJECT_SILHOUETTE_SUPPORT': 5,
    'UNCLASSIFIED_ANALYTIC_AMBIGUITY': 6,
}
_SIGNS = np.asarray(list(itertools.product([-1.0, 1.0], repeat=3)), dtype=np.float64)
_EDGE_PAIRS = []
for _i, _a in enumerate(_SIGNS):
    for _j, _b in enumerate(_SIGNS):
        if _j > _i and np.count_nonzero(_a != _b) == 1:
            _EDGE_PAIRS.append((_i, _j))
_EDGE_PAIRS = tuple(_EDGE_PAIRS)


def _snap_rotation_for_plane_signature(R):
    A = np.asarray(R, dtype=np.float64)
    tau = 8.0 * np.finfo(np.float64).eps
    S = np.zeros((3, 3), dtype=np.float64)
    used = set()
    for i in range(3):
        j = int(np.argmax(np.abs(A[i])))
        if j in used or abs(abs(float(A[i, j])) - 1.0) > tau:
            return A
        if any(abs(float(A[i, k])) > tau for k in range(3) if k != j):
            return A
        S[i, j] = 1.0 if A[i, j] >= 0.0 else -1.0
        used.add(j)
    if len(used) != 3 or float(np.linalg.det(S)) != 1.0 or np.max(np.abs(A - S)) > tau:
        return A
    return S


def _face_plane_signatures(request):
    out = []
    for obj in request['scene']['objects']:
        R = _snap_rotation_for_plane_signature(obj['R_local_to_world'])
        ctr = np.asarray(obj['center_world'], dtype=np.float64)
        half = np.asarray(obj['dimensions_m'], dtype=np.float64) / 2.0
        faces = []
        for a in range(3):
            for sign in (-1.0, 1.0):
                n = R[:, a] * sign
                point = ctr + R[:, a] * (sign * half[a])
                d = float(np.dot(n, point))
                first = next(float(v) for v in n if float(v) != 0.0)
                if first < 0.0:
                    n = -n
                    d = -d
                faces.append(
                    tuple(0.0 if float(v) == 0.0 else float(v) for v in n)
                    + (0.0 if d == 0.0 else d,)
                )
        out.append(tuple(faces))
    return tuple(out)


def _camera_parts(request, K_override=None):
    K = np.asarray(request['camera']['K'] if K_override is None else K_override, dtype=np.float64)
    C = np.asarray(request['camera']['pose']['camera_center_world'], dtype=np.float64)
    Rwc = np.asarray(request['camera']['pose']['R_world_to_camera_cv'], dtype=np.float64)
    Rcw = Rwc.T
    twc = np.asarray(request['camera']['pose']['t_world_to_camera_cv'], dtype=np.float64)
    return K, C, Rwc, Rcw, twc


def batch_signatures(request, uv, K_override=None, chunk=80000):
    """Exact analytic arbitrary-ray frontmost signatures used by Candidate B."""
    uv = np.asarray(uv, dtype=np.float64)
    if uv.ndim != 2 or uv.shape[1] != 2:
        raise ValueError('uv must be N x 2')
    objs = request['scene']['objects']
    K, C, _Rwc, Rcw, _twc = _camera_parts(request, K_override)
    plane = _face_plane_signatures(request)
    N = len(uv)
    OO = np.empty(N, dtype=np.int32)
    FF = np.empty(N, dtype=np.int16)
    AA = np.zeros(N, dtype=bool)
    for s0 in range(0, N, chunk):
        u = uv[s0:s0 + chunk]
        n = len(u)
        dc = np.column_stack([
            (u[:, 0] - K[0, 2]) / K[0, 0],
            (u[:, 1] - K[1, 2]) / K[1, 1],
            np.ones(n, dtype=np.float64),
        ])
        dwb = dc @ Rcw.T
        Ts = []
        Fs = []
        for obj in objs:
            R = np.asarray(obj['R_local_to_world'], dtype=np.float64)
            Rt = R.T
            ctr = np.asarray(obj['center_world'], dtype=np.float64)
            half = np.asarray(obj['dimensions_m'], dtype=np.float64) / 2.0
            ol = Rt @ (C - ctr)
            dl = dwb @ Rt.T
            tn = np.full(n, -np.inf, dtype=np.float64)
            tf = np.full(n, np.inf, dtype=np.float64)
            for a in range(3):
                da = dl[:, a]
                oa = ol[a]
                par = np.abs(da) < 1e-15
                outside = par & ((oa < -half[a]) | (oa > half[a]))
                den = np.where(par, 1.0, da)
                t1 = (-half[a] - oa) / den
                t2 = (half[a] - oa) / den
                lo = np.where(par, -np.inf, np.minimum(t1, t2))
                hi = np.where(par, np.inf, np.maximum(t1, t2))
                lo = np.where(outside, np.inf, lo)
                hi = np.where(outside, -np.inf, hi)
                tn = np.maximum(tn, lo)
                tf = np.minimum(tf, hi)
            valid = tf >= np.maximum(tn, 0.0)
            t = np.where(valid, np.where(tn > 0.0, tn, tf), np.inf)
            with np.errstate(invalid='ignore'):
                pl = ol[None, :] + dl * t[:, None]
            residuals = []
            for a in range(3):
                for sign in (-1.0, 1.0):
                    residuals.append(np.abs(pl[:, a] - sign * half[a]))
            face = np.argmin(np.stack(residuals, axis=1), axis=1).astype(np.int16)
            face[~np.isfinite(t)] = -1
            Ts.append(t)
            Fs.append(face)
        if not Ts:
            OO[s0:s0 + n] = 0
            FF[s0:s0 + n] = -1
            continue
        T = np.stack(Ts, axis=1)
        F = np.stack(Fs, axis=1)
        mt = np.min(T, axis=1)
        idx = np.argmin(T, axis=1)
        oo = np.where(np.isfinite(mt), idx + 1, 0).astype(np.int32)
        ff = np.where(np.isfinite(mt), F[np.arange(n), idx], -1).astype(np.int16)
        eq = (T == mt[:, None]) & np.isfinite(T)
        for ii in np.where(eq.sum(axis=1) > 1)[0]:
            js = np.where(eq[ii])[0]
            sigs = {(int(j + 1), int(F[ii, j])) for j in js}
            planes = {plane[j][int(F[ii, j])] for j in js if int(F[ii, j]) >= 0}
            if len(planes) > 1:
                AA[s0 + ii] = True
            elif sigs:
                oo[ii], ff[ii] = min(sigs)
        OO[s0:s0 + n] = oo
        FF[s0:s0 + n] = ff
    return OO, FF, AA


def _clip_segment(p0, p1, x0, x1, y0, y1):
    d = p1 - p0
    t0 = 0.0
    t1 = 1.0
    for p, q in [(-d[0], p0[0] - x0), (d[0], x1 - p0[0]), (-d[1], p0[1] - y0), (d[1], y1 - p0[1])]:
        if p == 0.0:
            if q < 0.0:
                return None
        else:
            r = q / p
            if p < 0.0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return None
    return p0 + t0 * d, p0 + t1 * d


def projected_edges(request, K_override=None):
    K, _C, Rwc, _Rcw, twc = _camera_parts(request, K_override)
    out = []
    for oi, obj in enumerate(request['scene']['objects'], 1):
        R = np.asarray(obj['R_local_to_world'], dtype=np.float64)
        ctr = np.asarray(obj['center_world'], dtype=np.float64)
        half = np.asarray(obj['dimensions_m'], dtype=np.float64) / 2.0
        vertices = (_SIGNS * half) @ R.T + ctr
        cam = vertices @ Rwc.T + twc
        validz = cam[:, 2] > 1e-12
        uv = np.column_stack([
            K[0, 0] * cam[:, 0] / cam[:, 2] + K[0, 2],
            K[1, 1] * cam[:, 1] / cam[:, 2] + K[1, 2],
        ])
        for edge_index, (a, b) in enumerate(_EDGE_PAIRS):
            if not validz[a] and not validz[b]:
                continue
            out.append((oi, edge_index, uv[a].copy(), uv[b].copy()))
    return tuple(out)


def _reason_for_transition(center, other, rendered_oid, x, y, H, W, ambiguous=False):
    if ambiguous:
        return 'UNCLASSIFIED_ANALYTIC_AMBIGUITY'
    if other == center:
        return None
    if other[0] != center[0]:
        if other[0] == 0 or center[0] == 0:
            return 'CONTINUOUS_OBJECT_SILHOUETTE_SUPPORT'
        nh = rendered_oid[max(0, y - 2):min(H, y + 3), max(0, x - 2):min(W, x + 3)]
        if not np.any(nh == other[0]):
            return 'SUBPIXEL_THIN_OCCLUDER_SUPPORT'
        return 'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT'
    if other[1] != center[1]:
        return 'CONTINUOUS_FACE_NORMAL_DISCONTINUITY_SUPPORT'
    return None


def evaluate_pixel(request, x, y, rendered_oid, K_override=None):
    """Literal Candidate-B reference for one inherited old-R6-safe pixel."""
    H = int(request['camera']['height'])
    W = int(request['camera']['width'])
    if x - FILTER_WIDTH_PX < 0.0 or x + FILTER_WIDTH_PX > W - 1 or y - FILTER_WIDTH_PX < 0.0 or y + FILTER_WIDTH_PX > H - 1:
        return {'safe': False, 'reason': 'IMAGE_BOUND_SUPPORT_INCOMPLETE', 'method_id': METHOD_ID}

    center_o, center_f, center_a = batch_signatures(request, np.asarray([[float(x), float(y)]]), K_override)
    center = (int(center_o[0]), int(center_f[0]))
    if bool(center_a[0]):
        return {'safe': False, 'reason': 'UNCLASSIFIED_ANALYTIC_AMBIGUITY', 'method_id': METHOD_ID, 'center_signature': center}

    offs = np.asarray([-FILTER_WIDTH_PX + k * LATTICE_STEP_PX for k in range(49)], dtype=np.float64)
    DU, DV = np.meshgrid(offs, offs, indexing='xy')
    points = np.column_stack([float(x) + DU.ravel(), float(y) + DV.ravel()])
    oo, ff, aa = batch_signatures(request, points, K_override)
    if np.any(aa):
        return {
            'safe': False,
            'reason': 'UNCLASSIFIED_ANALYTIC_AMBIGUITY',
            'method_id': METHOD_ID,
            'center_signature': center,
            'lattice_ambiguity': True,
        }
    diff = (oo != center[0]) | (ff != center[1])
    lattice_reason = None
    lattice_signature = None
    if np.any(diff):
        k = int(np.flatnonzero(diff)[0])
        other = (int(oo[k]), int(ff[k]))
        lattice_reason = _reason_for_transition(center, other, rendered_oid, x, y, H, W, False)
        lattice_signature = other
        if lattice_reason is None:
            lattice_reason = 'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT'

    edge_reason = None
    edge_witness = None
    for oi, edge_index, p0, p1 in projected_edges(request, K_override):
        clipped = _clip_segment(p0, p1, x - FILTER_WIDTH_PX, x + FILTER_WIDTH_PX, y - FILTER_WIDTH_PX, y + FILTER_WIDTH_PX)
        if clipped is None:
            continue
        a, b = clipped
        d = b - a
        L = float(np.linalg.norm(d))
        qs = [a.copy()] if L == 0.0 else [a + t * d for t in (0.25, 0.5, 0.75)]
        edge = p1 - p0
        n = np.asarray([-edge[1], edge[0]], dtype=np.float64)
        nl = float(np.linalg.norm(n))
        if nl == 0.0:
            continue
        n /= nl
        if not (n[0] > 0.0 or (n[0] == 0.0 and n[1] >= 0.0)):
            n = -n
        probes = []
        meta = []
        for q_index, q in enumerate(qs):
            for j in DYADIC_JS:
                dist = FILTER_WIDTH_PX / (2 ** j)
                qp = q + dist * n
                qm = q - dist * n
                ok = (
                    x - FILTER_WIDTH_PX - 1e-12 <= qp[0] <= x + FILTER_WIDTH_PX + 1e-12
                    and y - FILTER_WIDTH_PX - 1e-12 <= qp[1] <= y + FILTER_WIDTH_PX + 1e-12
                    and 0.0 <= qp[0] <= W - 1
                    and 0.0 <= qp[1] <= H - 1
                    and x - FILTER_WIDTH_PX - 1e-12 <= qm[0] <= x + FILTER_WIDTH_PX + 1e-12
                    and y - FILTER_WIDTH_PX - 1e-12 <= qm[1] <= y + FILTER_WIDTH_PX + 1e-12
                    and 0.0 <= qm[0] <= W - 1
                    and 0.0 <= qm[1] <= H - 1
                )
                if ok:
                    k = len(probes)
                    probes.extend([qp, qm])
                    meta.append((q_index, j, dist, k))
        if not probes:
            continue
        po, pf, pa = batch_signatures(request, np.asarray(probes, dtype=np.float64), K_override)
        for q_index, j, dist, k in meta:
            sp = (int(po[k]), int(pf[k]))
            sm = (int(po[k + 1]), int(pf[k + 1]))
            ambiguous = bool(pa[k] or pa[k + 1])
            if not ambiguous and not (sp != sm and (sp != center or sm != center)):
                continue
            if ambiguous:
                reason = 'UNCLASSIFIED_ANALYTIC_AMBIGUITY'
            else:
                candidates = []
                for other in (sp, sm):
                    r = _reason_for_transition(center, other, rendered_oid, x, y, H, W, False)
                    if r is not None:
                        candidates.append(r)
                reason = min(candidates, key=lambda r: REASON_PRIORITY[r]) if candidates else 'CONTINUOUS_FRONTMOST_VISIBILITY_TRANSITION_SUPPORT'
            witness = {
                'edge_object_id': int(oi),
                'edge_index': int(edge_index),
                'q_index': int(q_index),
                'dyadic_j': int(j),
                'distance_px': float(dist),
                'plus_signature': sp,
                'minus_signature': sm,
            }
            if edge_reason is None or REASON_PRIORITY[reason] < REASON_PRIORITY[edge_reason]:
                edge_reason = reason
                edge_witness = witness

    reasons = [r for r in (lattice_reason, edge_reason) if r is not None]
    if reasons:
        reason = min(reasons, key=lambda r: REASON_PRIORITY[r])
        return {
            'safe': False,
            'reason': reason,
            'method_id': METHOD_ID,
            'center_signature': center,
            'lattice_signature': lattice_signature,
            'edge_witness': edge_witness,
        }
    return {'safe': True, 'reason': None, 'method_id': METHOD_ID, 'center_signature': center}


def evaluate_pixels(request, pixels, rendered_oid, K_override=None):
    out = {}
    for x, y in pixels:
        out[(int(x), int(y))] = evaluate_pixel(request, int(x), int(y), rendered_oid, K_override)
    return out
