from __future__ import annotations
import hashlib, json, math, re, struct, zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, Iterable
from pcs_factory_seed import derive_seed, identity_digest

ASSET_SCHEMA='DF-G32-G35-ASSET-ECOSYSTEM-V1'
ALLOWED_FORMATS={'obj','gltf','glb','fbx','usd','usda','usdc','usdz','blend'}
REDISTRIBUTION={'REDISTRIBUTABLE','LOCAL_ONLY','REGENERABLE_PROCEDURAL','FORBIDDEN_UNKNOWN'}
STRUCTURE_AUTHORITY={'MANUAL_EXACT_AXES_PLANES','PROCEDURAL_EXACT','DCC_DERIVED_CANDIDATE','UNANNOTATED_CLUTTER'}

class AssetError(ValueError): pass

def sha256_bytes(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def safe_relative_ref(s:str, allow_data_uri:bool=False)->bool:
    s=str(s).strip()
    if not s: return False
    if allow_data_uri and s.lower().startswith('data:'): return True
    if '\x00' in s or '\n' in s or '\r' in s: return False
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',s): return False
    if s.startswith(('\\\\','//','/','\\')): return False
    w=PureWindowsPath(s)
    if w.drive or w.is_absolute(): return False
    parts=PurePosixPath(s.replace('\\','/')).parts
    if any(p in {'..',''} for p in parts): return False
    if any(p.endswith(':') for p in parts): return False
    return True

def _finite(vals:Iterable[float])->bool: return all(math.isfinite(float(x)) for x in vals)

def inspect_obj(data:bytes)->Dict[str,Any]:
    try: text=data.decode('utf-8-sig')
    except UnicodeDecodeError: text=data.decode('latin-1')
    counts={k:0 for k in ['v','vt','vn','f','l','g','usemtl','mtllib']}; bbox=None; mtllib=[]
    verts=[]
    for ln,line in enumerate(text.splitlines(),1):
        t=line.strip()
        if not t or t.startswith('#'): continue
        p=t.split(); key=p[0]
        if key in counts: counts[key]+=1
        if key=='v':
            if len(p)<4: raise AssetError(f'OBJ_BAD_VERTEX_LINE:{ln}')
            try: xyz=[float(p[1]),float(p[2]),float(p[3])]
            except Exception: raise AssetError(f'OBJ_BAD_VERTEX_NUMBER:{ln}')
            if not _finite(xyz): raise AssetError(f'OBJ_NONFINITE_VERTEX:{ln}')
            verts.append(xyz)
        elif key=='mtllib':
            ref=' '.join(p[1:]).strip()
            if not safe_relative_ref(ref): raise AssetError(f'OBJ_UNSAFE_MTLLIB:{ln}')
            mtllib.append(ref)
    if verts:
        mins=[min(v[i] for v in verts) for i in range(3)]; maxs=[max(v[i] for v in verts) for i in range(3)]
        bbox={'min':mins,'max':maxs,'size':[maxs[i]-mins[i] for i in range(3)]}
    return {'format':'obj','status':'PRE_DCC_INTAKE_PASS','counts':counts,'bbox_source_units':bbox,'material_libraries':mtllib,'geometry_decoded_pre_dcc':True}

def inspect_gltf(data:bytes)->Dict[str,Any]:
    try: obj=json.loads(data.decode('utf-8-sig'))
    except Exception as e: raise AssetError(f'GLTF_JSON_INVALID:{type(e).__name__}')
    if not isinstance(obj,dict): raise AssetError('GLTF_ROOT_NOT_OBJECT')
    av=((obj.get('asset') or {}).get('version'))
    if not isinstance(av,str) or not av.startswith('2'): raise AssetError('GLTF_UNSUPPORTED_ASSET_VERSION')
    refs=[]
    for sec in ('buffers','images'):
        for x in obj.get(sec,[]) or []:
            if isinstance(x,dict) and 'uri' in x:
                u=str(x['uri'])
                if not safe_relative_ref(u,allow_data_uri=True): raise AssetError(f'GLTF_UNSAFE_URI:{u}')
                refs.append({'section':sec,'uri':u,'embedded':u.lower().startswith('data:')})
    counts={k:len(obj.get(k,[]) or []) for k in ['scenes','nodes','meshes','accessors','buffers','bufferViews','materials','images','textures','cameras']}
    return {'format':'gltf','status':'PRE_DCC_INTAKE_PASS','asset_version':av,'counts':counts,'external_refs':refs,'geometry_decoded_pre_dcc':False}

def inspect_glb(data:bytes)->Dict[str,Any]:
    if len(data)<12: raise AssetError('GLB_TOO_SHORT')
    magic,ver,total=struct.unpack_from('<III',data,0)
    if magic!=0x46546C67: raise AssetError('GLB_BAD_MAGIC')
    if ver!=2: raise AssetError('GLB_UNSUPPORTED_VERSION')
    if total!=len(data): raise AssetError('GLB_LENGTH_MISMATCH')
    pos=12; chunks=[]
    while pos<len(data):
        if pos+8>len(data): raise AssetError('GLB_TRUNCATED_CHUNK_HEADER')
        ln,typ=struct.unpack_from('<II',data,pos);pos+=8
        if pos+ln>len(data): raise AssetError('GLB_TRUNCATED_CHUNK')
        chunks.append({'type_hex':hex(typ),'bytes':ln}); pos+=ln
    if pos!=len(data): raise AssetError('GLB_TRAILING_BYTES')
    if not chunks or chunks[0]['type_hex']!='0x4e4f534a': raise AssetError('GLB_FIRST_CHUNK_NOT_JSON')
    return {'format':'glb','status':'PRE_DCC_INTAKE_PASS','version':ver,'declared_bytes':total,'chunks':chunks,'geometry_decoded_pre_dcc':False}

def inspect_fbx(data:bytes)->Dict[str,Any]:
    binary=b'Kaydara FBX Binary  \x00\x1a\x00'
    if data.startswith(binary):
        if len(data)<27: raise AssetError('FBX_BINARY_TOO_SHORT')
        version=struct.unpack_from('<I',data,23)[0]
        return {'format':'fbx','status':'PRE_DCC_INTAKE_PASS','encoding':'binary','fbx_version':version,'geometry_decoded_pre_dcc':False}
    head=data[:4096].decode('latin-1','ignore')
    if 'FBXHeaderExtension' in head or head.lstrip().startswith('; FBX'):
        m=re.search(r'FBXVersion\s*:\s*(\d+)',head)
        return {'format':'fbx','status':'PRE_DCC_INTAKE_PASS','encoding':'ascii','fbx_version':int(m.group(1)) if m else None,'geometry_decoded_pre_dcc':False}
    raise AssetError('FBX_SIGNATURE_NOT_RECOGNIZED')

def inspect_usd(data:bytes, ext:str)->Dict[str,Any]:
    ext=ext.lower().lstrip('.')
    sig='unknown'
    if data.startswith(b'#usda'): sig='USDA_ASCII'
    elif data.startswith(b'PXR-USDC'): sig='USDC_CRATE'
    elif data.startswith(b'PK\x03\x04'): sig='USDZ_ZIP'
    if ext=='usda' and sig!='USDA_ASCII': raise AssetError('USDA_SIGNATURE_MISMATCH')
    if ext=='usdc' and sig!='USDC_CRATE': raise AssetError('USDC_SIGNATURE_MISMATCH')
    if ext=='usdz' and sig!='USDZ_ZIP': raise AssetError('USDZ_SIGNATURE_MISMATCH')
    if ext=='usd' and sig=='unknown': raise AssetError('USD_SIGNATURE_NOT_RECOGNIZED')
    return {'format':ext,'status':'PRE_DCC_INTAKE_PASS','usd_signature':sig,'geometry_decoded_pre_dcc':False}

def inspect_blend(data:bytes)->Dict[str,Any]:
    if len(data)<12 or not data.startswith(b'BLENDER'): raise AssetError('BLEND_BAD_HEADER')
    ptr=chr(data[7]); endian=chr(data[8]); ver=data[9:12].decode('ascii','replace')
    if ptr not in {'_','-'} or endian not in {'v','V'} or not ver.isdigit(): raise AssetError('BLEND_HEADER_INVALID')
    return {'format':'blend','status':'PRE_DCC_INTAKE_PASS','pointer_size':64 if ptr=='-' else 32,'endianness':'little' if endian=='v' else 'big','blender_version_code':ver,'geometry_decoded_pre_dcc':False}

def inspect_asset_bytes(name:str,data:bytes)->Dict[str,Any]:
    ext=Path(name).suffix.lower().lstrip('.')
    if ext not in ALLOWED_FORMATS: raise AssetError(f'UNSUPPORTED_FORMAT:{ext}')
    if ext=='obj': info=inspect_obj(data)
    elif ext=='gltf': info=inspect_gltf(data)
    elif ext=='glb': info=inspect_glb(data)
    elif ext=='fbx': info=inspect_fbx(data)
    elif ext in {'usd','usda','usdc','usdz'}: info=inspect_usd(data,ext)
    elif ext=='blend': info=inspect_blend(data)
    else: raise AssetError('UNREACHABLE_FORMAT')
    info.update({'schema':ASSET_SCHEMA,'source_name':Path(name).name,'bytes':len(data),'sha256':sha256_bytes(data),'dcc_import_status':'PENDING_PINNED_DCC'})
    return info

def validate_license_record(x:Dict[str,Any])->Dict[str,Any]:
    req=['license_id','license_name','redistribution_class','redistribution_allowed','modification_allowed','review_date']
    errs=[f'MISSING:{k}' for k in req if k not in x]
    if x.get('redistribution_class') not in REDISTRIBUTION: errs.append('BAD_REDISTRIBUTION_CLASS')
    if x.get('redistribution_class')=='FORBIDDEN_UNKNOWN' and x.get('redistribution_allowed') is True: errs.append('UNKNOWN_CANNOT_ASSERT_REDISTRIBUTION')
    return {'status':'PASS' if not errs else 'FAIL','errors':errs}

def validate_structural_annotation(x:Dict[str,Any])->Dict[str,Any]:
    errs=[]
    if x.get('authority') not in STRUCTURE_AUTHORITY: errs.append('BAD_AUTHORITY')
    axes=x.get('direction_sets_local',[]) or []
    for a in axes:
        v=a.get('direction') if isinstance(a,dict) else None
        if not isinstance(v,list) or len(v)!=3 or not _finite(v) or sum(float(q)**2 for q in v)<=1e-18: errs.append('BAD_DIRECTION')
    return {'status':'PASS' if not errs else 'FAIL','errors':errs}

def validate_catalog_entry(x:Dict[str,Any])->Dict[str,Any]:
    req=['asset_id','source_id','format','content_sha256','bytes','license_id','redistribution_class','intake_status','dcc_import_status','structural_annotation_status']
    errs=[f'MISSING:{k}' for k in req if k not in x]
    if x.get('redistribution_class') not in REDISTRIBUTION: errs.append('BAD_REDISTRIBUTION_CLASS')
    if x.get('format') not in ALLOWED_FORMATS|{'procedural'}: errs.append('BAD_FORMAT')
    sh=str(x.get('content_sha256',''))
    if len(sh)!=64 or any(c not in '0123456789abcdef' for c in sh.lower()): errs.append('BAD_SHA256')
    return {'status':'PASS' if not errs else 'FAIL','errors':errs}

def make_catalog_entry(asset_id:str,source_id:str,intake:Dict[str,Any],license_record:Dict[str,Any],structural_status='UNANNOTATED_CLUTTER')->Dict[str,Any]:
    if validate_license_record(license_record)['status']!='PASS': raise AssetError('INVALID_LICENSE_RECORD')
    e={'schema':ASSET_SCHEMA,'asset_id':asset_id,'source_id':source_id,'format':intake['format'],'content_sha256':intake['sha256'],'bytes':intake['bytes'],'license_id':license_record['license_id'],'redistribution_class':license_record['redistribution_class'],'intake_status':intake['status'],'dcc_import_status':intake.get('dcc_import_status','PENDING_PINNED_DCC'),'structural_annotation_status':structural_status,'pre_dcc_summary':intake}
    if validate_catalog_entry(e)['status']!='PASS': raise AssetError('CATALOG_ENTRY_INVALID')
    return e

def deterministic_instance_recipe(parent_asset_seed:int,asset_id:str,ordinal:int,scale_range=(0.8,1.2),yaw_range=(-180.0,180.0))->Dict[str,Any]:
    if scale_range[0]<=0 or scale_range[1]<scale_range[0]: raise AssetError('BAD_SCALE_RANGE')
    sd=derive_seed(parent_asset_seed,'asset_instance',asset_id,ordinal)
    u=sd['seed_u64']/float(2**64-1)
    sd2=derive_seed(sd['seed_u64'],'asset_instance_yaw',asset_id,ordinal)
    v=sd2['seed_u64']/float(2**64-1)
    scale=scale_range[0]+u*(scale_range[1]-scale_range[0])
    yaw=yaw_range[0]+v*(yaw_range[1]-yaw_range[0])
    out={'schema':'DF-G34-ASSET-INSTANCE-V1','asset_id':asset_id,'ordinal':int(ordinal),'seed':sd,'uniform_scale':scale,'yaw_deg':yaw,'translation_zone':'RECIPE_DEFINED','negative_scale_allowed':False}
    out['identity_digest_sha256']=identity_digest({k:v for k,v in out.items() if k!='identity_digest_sha256'})
    return out
