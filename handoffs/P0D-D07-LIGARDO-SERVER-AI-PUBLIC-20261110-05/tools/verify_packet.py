"""Read-only ZIP/manifest validator. Never extracts; no filesystem writes.
Rejects unsafe paths, collisions, oversized archives, missing/extra entries and hash mismatch.
"""
import hashlib
import io
import json
import stat
import zipfile
from pathlib import PurePosixPath

MAX_FILES=64
MAX_UNCOMPRESSED=2_000_000

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def verify(blob):
    if not isinstance(blob,bytes) or len(blob)>2_000_000 or len(blob)<64:raise ValueError('ZIP_SIZE')
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        infos=z.infolist()
        if len(infos)<2 or len(infos)>MAX_FILES:raise ValueError('COUNT')
        names=set()
        total=0
        content={}
        for f in infos:
            n=f.filename
            if not n or n.startswith(('/', '\\')) or '\\' in n or ':' in n or f.is_dir() or any(x in ('','.','..') for x in n.split('/')):
                raise ValueError('ZIP_PATH')
            if n.casefold() in names:raise ValueError('ZIP_COLLISION')
            names.add(n.casefold())
            mode=(f.external_attr>>16)&0xffff
            if mode and stat.S_IFMT(mode) not in (0,stat.S_IFREG):raise ValueError('ZIP_SPECIAL')
            if f.flag_bits & 1:raise ValueError('ZIP_ENCRYPTED')
            total += f.file_size
            if total>MAX_UNCOMPRESSED:raise ValueError('ZIP_BOMB')
            content[n]=z.read(f)
        if 'BUILD_MANIFEST.json' not in content:raise ValueError('NO_MANIFEST')
        manifest=json.loads(content.pop('BUILD_MANIFEST.json'))
        if manifest.get('schema')!='P0D_HANDOFF_SHA256_V1':raise ValueError('SCHEMA')
        if manifest.get('packet_id')!='P0D-D07-LIGARDO-SERVER-AI-20261110-04':raise ValueError('PACKET_ID')
        entries=manifest.get('entries')
        if not isinstance(entries,list) or len(entries)!=len(content):raise ValueError('ENTRY_COUNT')
        indexed={}
        for row in entries:
            if not isinstance(row,dict) or set(row)!={'path','size','sha256'} or row['path'] in indexed:raise ValueError('BAD_ENTRY')
            indexed[row['path']]=row
        if indexed.keys()!=content.keys():raise ValueError('ENTRY_SET')
        for path,data in content.items():
            row=indexed[path]
            if row['size']!=len(data) or row['sha256']!=sha256(data):raise ValueError('CONTENT_SHA_MISMATCH')
        return {'packet_id':manifest['packet_id'],'entry_count':len(content),'total_bytes':total,'zip_sha256':sha256(blob)}
