from __future__ import annotations
import hashlib, json, unicodedata
SEED_SCHEMA_VERSION='DF-G03-SEED-V1'
PREFIX='PCS_CAMERA_FACTORY_SEED_V1'

def _norm(s:str)->str:
    return unicodedata.normalize('NFC', str(s))

def derive_seed(parent_seed_u64:int, namespace:str, stable_key:str, ordinal:int=0):
    if not (0 <= int(parent_seed_u64) < 2**64): raise ValueError('parent seed out of uint64 range')
    if int(ordinal)<0: raise ValueError('ordinal must be non-negative')
    msg=f"{PREFIX}|{_norm(namespace)}|{int(parent_seed_u64)}|{_norm(stable_key)}|{int(ordinal)}".encode('utf-8')
    digest=hashlib.sha256(msg).hexdigest()
    u64=int.from_bytes(bytes.fromhex(digest[:16]),'big',signed=False)
    return {'schema':SEED_SCHEMA_VERSION,'seed_u64':u64,'digest_sha256':digest,'namespace':_norm(namespace),'stable_key':_norm(stable_key),'ordinal':int(ordinal),'parent_seed_u64':int(parent_seed_u64)}

def hierarchy(root_seed:int, base_scene_key:str, camera_key:str, appearance_key:str):
    scene=derive_seed(root_seed,'base_scene',base_scene_key,0)
    geometry=derive_seed(scene['seed_u64'],'geometry',base_scene_key,0)
    asset=derive_seed(scene['seed_u64'],'asset',base_scene_key,0)
    camera=derive_seed(scene['seed_u64'],'camera',camera_key,0)
    lighting=derive_seed(scene['seed_u64'],'lighting',appearance_key,0)
    material=derive_seed(scene['seed_u64'],'material',appearance_key,0)
    style=derive_seed(scene['seed_u64'],'style',appearance_key,0)
    clutter=derive_seed(scene['seed_u64'],'clutter',appearance_key,0)
    render=derive_seed(style['seed_u64'],'render',appearance_key,0)
    return {'root_seed':root_seed,'base_scene':scene,'geometry':geometry,'asset':asset,'camera':camera,'lighting':lighting,'material':material,'style':style,'clutter':clutter,'render':render}

def canonical_json_bytes(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def identity_digest(identity_obj):
    return hashlib.sha256(canonical_json_bytes(identity_obj)).hexdigest()
