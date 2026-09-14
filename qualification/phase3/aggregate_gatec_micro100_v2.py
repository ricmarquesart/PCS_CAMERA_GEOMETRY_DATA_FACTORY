from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_SAFE = 7066304
EXPECTED_DIGEST = '4a31f4df0b059d22c29bb61f93f24059aec4c7f90dcc43b09f4591916e733383'
EXPECTED_BLOB = '9e67ad85499d779239d5004dc11e81c1e0c1baea'
EXPECTED_JSON = '0ab266c1a0bc585934be2b172be531832841e9abbdcb0c51ae90f65c21079088'
EXPECTED_XZ = '8c5c7a773ecfdc338db4683a9beb210f72bd7e02d377fb2abb465f65f7fb0c7f'
EXPECTED_MANIFEST = '20c52048a83236bdc056b1bf61ed28ea7136882a6266c8a7a9c0f03b11f86840'

def sha256(b): return hashlib.sha256(b).hexdigest()
def fail(m): raise AssertionError(m)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input-dir',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    files=sorted(Path(a.input_dir).rglob('gatec_shard_*.json'))
    if len(files)!=10: fail(f'GATEC_AGGREGATE_EXPECTED_10_SHARDS:{len(files)}')
    allrows=[]
    for p in files:
        r=json.loads(p.read_text(encoding='utf-8'))
        if r.get('schema')!='DF-G101-PHASE3-GATE-C-MICRO100-SHARD-RESULT-V2' or r.get('status')!='PASS': fail('GATEC_AGGREGATE_SHARD_STATUS:'+str(p))
        if r['production_source_git_blob_sha1']!=EXPECTED_BLOB: fail('GATEC_AGGREGATE_SOURCE_BLOB_MISMATCH')
        if r['capsule_json_sha256']!=EXPECTED_JSON or r['capsule_xz_sha256']!=EXPECTED_XZ or r['manifest_sha256']!=EXPECTED_MANIFEST: fail('GATEC_AGGREGATE_TRANSPORT_IDENTITY_MISMATCH')
        if not r['all_retention_exact_1'] or not r['all_exclusions_zero'] or not r['all_reason_counts_empty']: fail('GATEC_AGGREGATE_SHARD_SCIENCE_MISMATCH')
        allrows.extend(r['samples'])
    allrows.sort(key=lambda x:int(x['ordinal']))
    if [int(x['ordinal']) for x in allrows]!=list(range(100)): fail('GATEC_AGGREGATE_ORDINAL_SET_MISMATCH')
    if len({x['sample_id'] for x in allrows})!=100: fail('GATEC_AGGREGATE_SAMPLE_ID_UNIQUENESS_MISMATCH')
    total_old=sum(int(x['old_safe_count']) for x in allrows); total_new=sum(int(x['new_safe_count']) for x in allrows)
    excl=sum(int(x['excluded_count']) for x in allrows)
    if total_old!=EXPECTED_SAFE or total_new!=EXPECTED_SAFE or excl!=0: fail(f'GATEC_AGGREGATE_SAFE_MISMATCH:{total_old}:{total_new}:{excl}')
    hashes=[x['new_mask_sha256'] for x in allrows]
    digest=sha256(('\n'.join(hashes)+'\n').encode('ascii'))
    if digest!=EXPECTED_DIGEST: fail('GATEC_AGGREGATE_CORRECTED_MASK_DIGEST_MISMATCH')
    rendered=[int(x['ordinal']) for x in allrows if x['oid_mode']=='RENDERED_RLE_HASH_GATED']
    if rendered!=[3,27,39,51,63,75,87,99]: fail('GATEC_AGGREGATE_RENDERED_CONTROL_SET_MISMATCH')
    report={'schema':'DF-G101-PHASE3-GATE-C-MICRO100-AGGREGATE-RESULT-V2','status':'PASS','sample_count':100,'aggregate_old_safe_pixels':total_old,'aggregate_new_safe_pixels':total_new,'aggregate_exclusions':excl,'corrected_mask_digest_sha256':digest,'production_source_git_blob_sha1':EXPECTED_BLOB,'rendered_oid_control_ordinals':rendered,'all_retention_exact_1':True,'all_exclusions_zero':True,'all_reason_counts_empty':True}
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,sort_keys=True))
if __name__=='__main__': main()
