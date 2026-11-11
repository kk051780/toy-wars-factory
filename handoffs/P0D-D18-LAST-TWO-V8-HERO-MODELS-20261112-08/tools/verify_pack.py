#!/usr/bin/env python3
"""Strict fail-closed PUBLIC_SOURCE_V1 packet validation, no keys."""
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PKT='P0D-D18-LAST-TWO-V8-HERO-MODELS-20261112-08'
REQUIRED={'files','format','game_id','packet_id','public_source_allowed','work_id'}

def verify(root=ROOT):
    root=Path(root)
    obj=json.loads((root/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
    assert set(obj)==REQUIRED, 'invalid 6-key format'
    assert obj['format']=='P0D_PUBLIC_SOURCE_V1'
    assert obj['game_id']=='TRAP_RAIDERS'
    assert obj['work_id']=='p0d-siege-v19'
    assert obj['packet_id']==PKT
    assert obj['public_source_allowed'] is True
    entries=obj['files']
    assert isinstance(entries,list) and len(entries)==9
    seen=set()
    for x in entries:
        assert set(x)=={'path','sha256','size'},'invalid entry'
        p=x['path']; assert isinstance(p,str) and '/' not in p[:1] and '\\' not in p and '..' not in Path(p).parts and p not in seen
        seen.add(p)
        f=(root/p).resolve(); assert f.is_relative_to(root.resolve()) and f.is_file() and not f.is_symlink()
        b=f.read_bytes(); assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256'],p
    assert 'BUILD_MANIFEST.json' not in seen
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'} == seen | {'BUILD_MANIFEST.json'}
    return len(seen)

if __name__=='__main__':
    try: print('SOURCE_MANIFEST_PASS',verify(),'files')
    except Exception as exc:
        print('SOURCE_MANIFEST_FAIL',exc,file=sys.stderr)
        sys.exit(2)
