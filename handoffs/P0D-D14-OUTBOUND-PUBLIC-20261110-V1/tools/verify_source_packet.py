#!/usr/bin/env python3
"""Validate sealed reference ZIP's BUILD_MANIFEST.json (no extraction)."""
import hashlib,json,sys,zipfile
from pathlib import PurePosixPath

def digest(b):return hashlib.sha256(b).hexdigest()

def verify(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or 'BUILD_MANIFEST.json' not in names:
            raise ValueError('DUPLICATE_OR_NO_MANIFEST')
        for name in names:
            p=PurePosixPath(name)
            if name.startswith('/') or '\\' in name or '..' in p.parts or ':' in name or name.endswith('/'):
                raise ValueError('UNSAFE_ARCHIVE_PATH')
        m=json.loads(z.read('BUILD_MANIFEST.json'))
        expected={f['path']:f for f in m['files']}
        if set(expected)!=set(names)-{'BUILD_MANIFEST.json'}:
            raise ValueError('FILE_SET_MISMATCH')
        for name,record in expected.items():
            blob=z.read(name)
            if len(blob)!=record['size'] or digest(blob)!=record['sha256']:
                raise ValueError('HASH_MISMATCH '+name)
        return m

if __name__=='__main__':
    x=verify(sys.argv[1]);print('PASS',len(x['files']))
