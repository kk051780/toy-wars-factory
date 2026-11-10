#!/usr/bin/env python3
"""Read-only SHA+path+manifest verification of a sealed P0-D ZIP. Never extracts."""
import hashlib
import json
from pathlib import PurePosixPath
import stat
import sys
import zipfile

MAX_FILES=64
MAX_TOTAL=5_000_000
MAX_FILE=1_000_000


def sha(b): return hashlib.sha256(b).hexdigest()


def verify(path, expected_zip_sha=None):
    p=__import__('pathlib').Path(path)
    data=p.read_bytes()
    if len(data) > MAX_TOTAL: raise ValueError('ZIP_TOO_LARGE')
    if expected_zip_sha is not None and sha(data) != expected_zip_sha: raise ValueError('ZIP_SHA_MISMATCH')
    with zipfile.ZipFile(p) as z:
        infos=z.infolist()
        if not infos or len(infos)>MAX_FILES: raise ValueError('ZIP_ENTRY_COUNT')
        names=[i.filename for i in infos]
        if len(set(x.lower() for x in names))!=len(names): raise ValueError('ZIP_DUPLICATE_OR_CASE_CONFLICT')
        if 'BUILD_MANIFEST.json' not in names: raise ValueError('MISSING_MANIFEST')
        total=0
        for i in infos:
            name=i.filename
            parts=name.split('/')
            if (not name or len(name)>180 or name.startswith(('/', '\\')) or
                '\\' in name or ':' in name or any(t in ('','.','..') for t in parts) or
                PurePosixPath(name).is_absolute() or name.endswith('/')):
                raise ValueError('ZIP_UNSAFE_PATH')
            typ=(i.external_attr >> 16) & 0o170000
            if typ not in (0, stat.S_IFREG): raise ValueError('ZIP_NON_REGULAR')
            if i.file_size > MAX_FILE: raise ValueError('ZIP_FILE_TOO_LARGE')
            total+=i.file_size
            if total>MAX_TOTAL: raise ValueError('ZIP_UNCOMPRESSED_TOO_LARGE')
        doc=json.loads(z.read('BUILD_MANIFEST.json'))
        if doc.get('format')!='P0D_BUILD_MANIFEST_V1': raise ValueError('MANIFEST_FORMAT')
        files=doc.get('files')
        if not isinstance(files,list): raise ValueError('MANIFEST_FILES')
        entries={k:v for k,v in ((x['path'],x) for x in files)}
        if len(entries)!=len(files) or set(entries)!=(set(names)-{'BUILD_MANIFEST.json'}):
            raise ValueError('MANIFEST_MISSING_EXTRA')
        for name,v in entries.items():
            content=z.read(name)
            if sha(content)!=v['sha256'] or len(content)!=v['size']:
                raise ValueError('FILE_SHA_OR_SIZE_MISMATCH')
        if z.testzip() is not None: raise ValueError('ZIP_CRC_FAIL')
        return {'zip_sha256':sha(data),'manifest_sha256':sha(z.read('BUILD_MANIFEST.json')),
                'file_count':len(entries),'total_uncompressed':total}


if __name__=='__main__':
    if len(sys.argv) not in (2,3): raise SystemExit('usage: verify_packet.py ZIP [ZIP_SHA256]')
    print(json.dumps(verify(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None),sort_keys=True))
