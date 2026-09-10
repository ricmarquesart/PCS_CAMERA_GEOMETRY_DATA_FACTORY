from __future__ import annotations
import importlib.util,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load_runner():
    spec=importlib.util.spec_from_file_location('g101_runner_focused_r2',HERE/'df_g101_scale1k.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    m=load_runner();checks={};details={}
    checks['source_release_id_r2']=m.SOURCE_RELEASE_ID=='DF_G101_SCALE1K_V1_R1_TOOL_R2'
    checks['dataset_release_split_frozen']=(m.DATASET_ID=='PCS_CAMERA_GEOMETRY_SCALE1K_V1' and m.RELEASE_ID=='DF_G101_SCALE1K_V1_R1' and m.PARTITION=='SCALE1K_QUALIFICATION_ONLY')
    checks['r2_spec_binding']=m.G101_R2_SPEC_DRIVE_ID=='1tidiKAl6NspDeIq0yQyf5l2hc-DQjEcHVq-tO0aUSJk'
    checks['r1_failure_authority']=m._g101_r2_failure_authority_identity()['sha256']==m.G101_R1_FAILURE_AUTHORITY_SHA256
    aud=m._g101_r2_verify_policy_audit_authority();details['policy_audit']=aud;checks['full_policy_audit_authority']=aud['status']=='PASS' and aud['r2_count']==10
    rr=m._g101_retry_regression();details['retry']=rr;checks['r34_retry_regression']=all(rr.values())
    bat=(HERE/'RUN_DF_G101_SCALE1K.bat').read_bytes();psb=(HERE/'RUN_DF_G101_SCALE1K_GUARDIAN.ps1').read_bytes();ps=psb.decode('utf-8-sig')
    checks['bat_crlf_only']=bat.count(b'\n')==bat.count(b'\r\n') and bat.count(b'\r\n')>=30
    checks['guardian_r2_existing_runroot_gate']='BLOCKED_REQUIRED_R1_FAILURE_RUNROOT_MISSING' in ps
    checks['guardian_second_attempt_gate']='BLOCKED_R2_RECOVERY_ALREADY_INITIALIZED_DO_NOT_RERUN' in ps
    checks['guardian_10_shards']='$ShardFiles.Count -eq 10' in ps
    checks['guardian_failure_packager']="'package-failure'" in ps
    checks['guardian_firewalls']='scale_10k_authorized = $false' in ps and 'training_started = $false' in ps and 'test77_accessed = $false' in ps
    reports=['DF_G101_R2_EXACT_TARGET0005_FIXTURE.json','DF_G101_R2_INHERITED_R33_R36_REGRESSION.json','DF_G101_R2_ELIGIBILITY_AST_AUDIT.json','DF_G101_R2_SYNTHETIC_RECOVERY_SELFTEST.json','DF_G101_R2_FAILURE_TRANSPORT_SELFTEST.json']
    details['report_statuses']={}
    for n in reports:
        p=HERE/n;o=json.loads(p.read_text()) if p.is_file() else {'status':'MISSING'};details['report_statuses'][n]=o.get('status');checks['report_'+n]=o.get('status')=='PASS'
    compile_errors=[]
    for p in [HERE/'df_g101_scale1k.py']+sorted((HERE/'SOURCE').glob('*.py')):
        try:compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
        except Exception as e:compile_errors.append(f'{p.name}:{e}')
    checks['python_sources_compile']=not compile_errors;details['compile_errors']=compile_errors
    out={'schema':'DF-G101-R2-FOCUSED-PRE-REAL-SELFTEST-V1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'details':details,'authority':{'r2_real_recovery_authorized':False,'scale_10k_authorized':False,'training_started':False,'test77_accessed':False,'maya_mutated':False,'product_mutated':False}}
    (HERE/'DF_G101_R2_FOCUSED_PRE_REAL_SELFTEST.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
