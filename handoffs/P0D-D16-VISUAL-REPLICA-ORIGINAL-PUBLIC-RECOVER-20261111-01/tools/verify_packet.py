"""Fail-closed ZIP manifest verifier; no extraction, shell or network use."""
import hashlib,io,json,posixpath,stat,sys,zipfile

LIMIT=2_000_000
PACKET_ID='P0D-D16-VISUAL-REPLICA-20261110-02'

def digest(data):return hashlib.sha256(data).hexdigest()
def no_dup(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('DUPLICATE_JSON_KEY')
        result[k]=v
    return result

def verify(data):
    if not isinstance(data,bytes) or not 0<len(data)<=LIMIT:raise ValueError('ZIP_SIZE_REJECTED')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or 'BUILD_MANIFEST.json' not in names:raise ValueError('DUPLICATE_OR_MISSING_MANIFEST')
        files={}
        for info in z.infolist():
            p=info.filename
            if not p or p.startswith('/') or '\\' in p or ':' in p or p.endswith('/') or len(p)>240 or posixpath.normpath(p)!=p or any(seg in ('','..','.') for seg in p.split('/')) or stat.S_ISLNK(info.external_attr >> 16) or info.file_size>LIMIT:
                raise ValueError('UNSAFE_PATH')
            content=z.read(info)
            if len(content)>LIMIT:raise ValueError('OVERSIZE_ENTRY')
            if p!='BUILD_MANIFEST.json':files[p]=digest(content)
        try:manifest=json.loads(z.read('BUILD_MANIFEST.json'),object_pairs_hook=no_dup,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
        except (ValueError,UnicodeError,json.JSONDecodeError) as exc:raise ValueError('INVALID_MANIFEST') from exc
        if manifest.get('format')!='P0D_D16_VISUAL_MANIFEST_V1' or manifest.get('packet_id')!=PACKET_ID or manifest.get('game_id')!='TRAP_RAIDERS' or manifest.get('work_id')!='p0d-siege-v19':raise ValueError('INVALID_ID')
        if manifest.get('files')!=files:raise ValueError('FILE_HASH_MISMATCH')
        return {'zip_sha256':digest(data),'manifest_sha256':digest(z.read('BUILD_MANIFEST.json')),'files':len(files)}

if __name__=='__main__':print(verify(open(sys.argv[1],'rb').read()))
