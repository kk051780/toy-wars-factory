#!/usr/bin/env python3
"""Strict PUBLIC_SOURCE_V1 receipt checker: manifest, filenames, size and SHA256."""
from pathlib import Path
import json,hashlib,re,sys
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'files','format','game_id','packet_id','public_source_allowed','work_id'}

def verify(root=ROOT):
    root=Path(root)
    man=json.loads((root/'BUILD_MANIFEST.json').read_text('utf8'))
    assert set(man)==EXPECTED, 'manifest six keys exact'
    assert man['format']=='P0D_PUBLIC_SOURCE_V1' and man['public_source_allowed'] is True
    assert man['game_id']=='TRAP_RAIDERS' and man['work_id']=='p0d-siege-v19'
    assert man['packet_id']=='P0D-D18-SESSION-GALLERY-TEN-20261112-05'
    paths=[]
    for item in man['files']:
        assert set(item)=={'path','sha256','size'}
        p=item['path']
        assert isinstance(p,str) and p and '\\' not in p and not p.startswith('/')
        assert all(q not in ('','.', '..') for q in p.split('/')),f'unsafe path {p}'
        assert re.fullmatch('[a-f0-9]{64}',item['sha256'])
        assert type(item['size']) is int and item['size']>0
        f=(root/p)
        assert f.is_file() and not f.is_symlink(),p
        content=f.read_bytes()
        assert len(content)==item['size'],f'size mismatch {p}'
        assert hashlib.sha256(content).hexdigest()==item['sha256'],f'SHA mismatch {p}'
        paths.append(p)
    assert len(paths)==len(set(paths)), 'duplicate manifest path'
    actual=sorted(x.relative_to(root).as_posix() for x in root.rglob('*') if x.is_file() and '__pycache__' not in x.parts and not x.name.endswith('.pyc'))
    assert actual==sorted(paths+['BUILD_MANIFEST.json']),f'unmanifested or missing sources {set(actual)^set(paths+["BUILD_MANIFEST.json"])}'
    return len(paths)
if __name__=='__main__':print('PUBLIC_SOURCE_V1 PASS',verify(),'source files')
