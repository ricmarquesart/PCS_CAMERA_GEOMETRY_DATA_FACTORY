from __future__ import annotations
import base64, hashlib, json, lzma, sys, time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'SOURCE'))
import pcs_factory_micro100_gt as gt
FIX=HERE/'fixtures'/'g101_gateb_v1g'
MANIFEST=FIX/'manifest.json'; SHARDS=[FIX/f'part{i:02d}.b64' for i in range(1,5)]
MANIFEST_BYTES=443
MANIFEST_SHA='7adfc54d3a6a2e0ad23409e38f3e57559f46e5939788d72c51c336b4f7a5fb24'
B64_BYTES=32240; B64_SHA='de329e26776b49b817d93b1bcb5add740cf60198412e60163632c3e799864dd8'
SHARD_SHA=['0a67b41ef0573cfe82f27917f0f3efda513a1685c21d7dec026a059b6b9c2d07','fce66f1f6b43c34652cb3480768fe98c4e012ea9fd48658e5633361a36e37d14','31216b5a173e3a74e8a6ba59f7440f871152c4e3f52cb64a9fb0ac1d2f967aa9','e9d023a5b41bfb4d682b4cfcfd22c5a5748a59bedcdacc6fd734f52a6f0f93b2']
XZ_BYTES=24180; XZ_SHA='5dd2a5a6c018932b19c6704c3886afd2dac3292b5932f21df446f1b6bebc8f45'
JSON_BYTES=151947; JSON_SHA='7e8b64fa8ad27b53796e97ec28a54e9e7339107f694330723db1fc8de40ff02a'
PROD_BLOB='9e67ad85499d779239d5004dc11e81c1e0c1baea'
SOURCE_RETURN='aa8ad77e253e6d515f789f86b3b403d2b58ef7e6721927666bec930a07e3eb26'
SOURCE_SUBSET='f42fd9783af6cdba9bfd24515f7bf3b44da73a8508b1577f9342d1e763362d0a'
SAMPLE_DIGEST='4475d6ddc122011e30af6ca422912adcf9c897d295a7357e902ae1b5cb359034'
MASK_DIGEST='20e91ceeb3d6966cb96420abe380eebb7577ebd49ccbe2f22e6f735eca6fee15'
TOTAL=2438043
RENDERED_ORDS={'0010','0022'}

def req(c,m):
    if not c: raise AssertionError(m)
def sha(b): return hashlib.sha256(b).hexdigest()
def git_blob_sha1(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def decode_rle(meta):
    h,w=map(int,meta['shape']); r=meta['rle']; req(len(r)%2==0,'OID_RLE_ODD')
    a=np.empty(h*w,dtype='<i4'); p=0
    for i in range(0,len(r),2):
        v=int(r[i]); n=int(r[i+1]); req(n>0 and p+n<=a.size,'OID_RLE_RANGE'); a[p:p+n]=v;p+=n
    req(p==a.size,'OID_RLE_LENGTH')
    req(sha(a.tobytes(order='C'))==meta['int32_le_sha256'],'OID_RLE_SHA')
    return a.reshape(h,w).astype(np.int32)

def analytic_oid(request,K):
    h=int(request['camera']['height']); w=int(request['camera']['width']); C=np.asarray(request['camera']['pose']['camera_center_world'],float)
    _pred,pid=gt._predict_depth_and_id(request,C,h,w,K)
    return np.asarray(pid,dtype=np.int32)
def rebuild_old(request,oid,K,radius):
    h,w=oid.shape; C=np.asarray(request['camera']['pose']['camera_center_world'],float); _dcv,dw=gt._ray_grid(request,h,w,K_override=K)
    labels=np.full((h,w),-1,dtype=np.int32)
    for j,obj in enumerate(request['scene']['objects'],1):
        _t,_nc,face=gt._object_hit_surface(C,dw,obj); m=(oid==j); labels[m]=(j-1)*6+face[m].astype(np.int32)
    return gt._filter_safe_interior_mask(oid,labels,int(radius))

def main():
    mb=MANIFEST.read_bytes(); req(len(mb)==MANIFEST_BYTES and sha(mb)==MANIFEST_SHA,'MANIFEST_ID')
    man=json.loads(mb); req(man['schema']=='DF-G101-PHASE3-GATE-B-MINIMAL-HYBRID-OID-TRANSPORT-MANIFEST-V1G','MANIFEST_SCHEMA')
    chunks=[]
    for p,h in zip(SHARDS,SHARD_SHA):
        b=p.read_bytes(); req(len(b)==8060 and sha(b)==h,'SHARD_ID:'+p.name); chunks.append(b)
    bb=b''.join(chunks); req(len(bb)==B64_BYTES and sha(bb)==B64_SHA,'B64_ID')
    xb=base64.b64decode(bb,validate=True); req(len(xb)==XZ_BYTES and sha(xb)==XZ_SHA,'XZ_ID')
    raw=lzma.decompress(xb,format=lzma.FORMAT_XZ); req(len(raw)==JSON_BYTES and sha(raw)==JSON_SHA,'JSON_ID')
    cap=json.loads(raw); req(cap['schema']=='DF-G101-PHASE3-GATE-B-MINIMAL-HYBRID-OID-TRANSPORT-V1G','CAPSULE_SCHEMA')
    prod=(REPO/'SOURCE'/'pcs_factory_micro100_gt.py').read_bytes(); req(git_blob_sha1(prod)==PROD_BLOB,'PRODUCTION_BLOB_DRIFT')
    auth=cap['authority']; req(auth['production_blob_sha1']==PROD_BLOB,'PROD_AUTH'); req(auth['source_return_sha256']==SOURCE_RETURN,'SOURCE_RETURN_AUTH'); req(auth['source_subset_authority_digest_sha256']==SOURCE_SUBSET,'SOURCE_SUBSET_AUTH'); req(auth['sample_id_digest_sha256']==SAMPLE_DIGEST,'SAMPLE_AUTH'); req(auth['baseline_mask_digest_sha256']==MASK_DIGEST,'MASK_AUTH'); req(int(auth['aggregate_old_safe_pixels'])==TOTAL,'TOTAL_AUTH')
    samples=cap['samples']; req(len(samples)==34,'COUNT'); req([s['ordinal'] for s in samples]==[f'{i:04d}' for i in range(34)],'ORDINALS'); req({s['ordinal'] for s in samples if s['oid_mode']=='RENDERED_RLE'}==RENDERED_ORDS,'RENDERED_SET')
    req(sha(''.join(s['sample_id']+'\n' for s in samples).encode())==SAMPLE_DIGEST,'SAMPLE_DIGEST')
    req(sha(''.join(s['old']['sha256']+'\n' for s in samples).encode())==MASK_DIGEST,'OLD_DIGEST')
    old_total=new_total=0; new_hash=[]; rows=[]; t0=time.perf_counter()
    for i,s in enumerate(samples,1):
        sid=s['sample_id']; r=s['request_minimal']; req('sample_id' not in r,sid+':ID_LEAK')
        q=s['qa']; req(all(q[k]=='PASS' for k in ('sample_status','object_status','depth_status','normal_status')),sid+':QA_PASS'); req(float(q['authority_fraction'])==1.0 and int(q['unexplained'])==0,sid+':QA_AUTH'); req(float(q['filter_width'])==float(gt.G100_CYCLES_FILTER_WIDTH_PX),sid+':FILTER_WIDTH')
        K=np.asarray(r['camera']['K'],float); d=np.asarray(s['final_binding']['delta_px'],float); Ke=K.copy();Ke[0,2]+=d[0];Ke[1,2]+=d[1]; req(np.array_equal(Ke,np.asarray(s['final_binding']['K_effective'],float)),sid+':K')
        if s['oid_mode']=='RENDERED_RLE': oid=decode_rle(s['rendered_object_index'])
        else: req(s['oid_mode']=='ANALYTIC_PID_HASH_GATED',sid+':OID_MODE'); oid=analytic_oid(r,Ke)
        old=rebuild_old(r,oid,Ke,s['old']['radius']); ob=old.astype(np.uint8).tobytes(order='C'); req(len(ob)==int(s['old']['bytes']),sid+':OLD_BYTES'); req(int(old.sum())==int(s['old']['safe_pixels']),sid+':OLD_COUNT'); req(sha(ob)==s['old']['sha256'],sid+':OLD_SHA')
        new,res=gt._phase3_candidate_b_normal_safe_mask(r,old,oid,K_override=Ke,renderer_filter_width_px=gt.G100_CYCLES_FILTER_WIDTH_PX)
        req(np.array_equal(new,old),sid+':MASK_CHANGED'); req(int(res['excluded_count'])==0,sid+':EXCL'); req(float(res['retained_fraction'])==1.0,sid+':RET'); req(res['reason_counts']=={},sid+':REASONS'); req(res['method_id']==gt.PHASE3_CANDIDATE_B_METHOD_ID,sid+':METHOD'); req(res['full_domain_semantics'] is True,sid+':DOMAIN')
        for k in ('rendered_normal_used_in_selection','rgb_used_in_selection','acceptance_used_in_selection','sample_identity_used_in_selection','depth_authority_mutated','camera_binding_steered'): req(res[k] is False,sid+':'+k)
        nh=sha(new.astype(np.uint8).tobytes(order='C')); req(nh==s['old']['sha256']==res['mask_sha256'],sid+':NEW_SHA')
        old_total+=int(res['old_safe_count']);new_total+=int(res['new_safe_count']);new_hash.append(nh);rows.append({'ordinal':s['ordinal'],'sample_id':sid,'oid_mode':s['oid_mode'],'safe_pixels':int(res['new_safe_count']),'status':'PASS'})
        print(f'[{i:02d}/34] {sid}: PASS mode={s["oid_mode"]} safe={int(res["new_safe_count"])}')
    corrected=sha(''.join(x+'\n' for x in new_hash).encode());req(old_total==TOTAL and new_total==TOTAL,'TOTAL_RESULT');req(corrected==MASK_DIGEST,'CORRECTED_DIGEST')
    report={'schema':'DF-G101-PHASE3-GATE-B-GITHUB-QUALIFICATION-V1G','status':'PASS','sample_count':34,'aggregate_old_safe_pixels':old_total,'aggregate_new_safe_pixels':new_total,'aggregate_exclusions':0,'corrected_mask_digest_sha256':corrected,'production_blob_sha1':PROD_BLOB,'runtime_seconds':time.perf_counter()-t0,'samples':rows}
    Path('gateb_v1g_result.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='samples'},sort_keys=True))
if __name__=='__main__': main()
