"""No-extraction verifier for deterministic D16 ZIP (not a Studio attestation)."""
import hashlib
import io
import json
import posixpath
import stat
import sys
import zipfile

LIMIT=2_000_000

def no_duplicate_fields(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError('DUPLICATE_JSON_KEY')
        out[k]=v
    return out

def verify(data):
    if not 0<len(data)<=LIMIT: raise ValueError('ZIP_SIZE')
    with zipfile.ZipFile(io.BytesIO(data),'r') as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or 'BUILD_MANIFEST.json' not in names: raise ValueError('DUPLICATE_OR_NO_MANIFEST')
        actual={}
        for info in z.infolist():
            p=info.filename
            if (not p or p.startswith('/') or '\\' in p or ':' in p or p.endswith('/') or
                any(segment in ('','..','.') for segment in p.split('/')) or
                posixpath.normpath(p)!=p or
                stat.S_ISLNK(info.external_attr >> 16) or info.file_size>LIMIT):
                raise ValueError('UNSAFE_ZIP_PATH_OR_TYPE')
            body=z.read(info)
            if len(body)>LIMIT: raise ValueError('ZIP_FILE_TOO_LARGE')
            if p!='BUILD_MANIFEST.json': actual[p]=hashlib.sha256(body).hexdigest()
        try: manifest=json.loads(z.read('BUILD_MANIFEST.json'),object_pairs_hook=no_duplicate_fields)
        except (json.JSONDecodeError,UnicodeError) as e: raise ValueError('BAD_MANIFEST') from e
        if manifest.get('format')!='P0D_D16_MANIFEST_V1' or manifest.get('packet_id')!='P0D-D16-SCALE-FX-20261110-01':
            raise ValueError('MANIFEST_ID_MISMATCH')
        if manifest.get('files')!=actual: raise ValueError('MANIFEST_HASH_MISMATCH')
        return {'zip_sha256':hashlib.sha256(data).hexdigest(), 'manifest_sha256':hashlib.sha256(z.read('BUILD_MANIFEST.json')).hexdigest(), 'files':len(actual)}

if __name__=='__main__':
    print(verify(open(sys.argv[1],'rb').read()))
