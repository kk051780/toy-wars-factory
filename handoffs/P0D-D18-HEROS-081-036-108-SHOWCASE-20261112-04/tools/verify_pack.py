#!/usr/bin/env python3
"""Strict self-contained immutable bytes/sha manifest verifier; refuses extra files and symlinks."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={'files','format','game_id','packet_id','public_source_allowed','work_id'}
def verify():
    manifest=json.loads((ROOT/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
    if set(manifest)!=REQUIRED or manifest['format']!='P0D_PUBLIC_SOURCE_V1' or manifest['game_id']!='TRAP_RAIDERS' or manifest['work_id']!='p0d-siege-v19' or manifest['public_source_allowed'] is not True or manifest['packet_id']!='P0D-D18-HEROS-081-036-108-SHOWCASE-20261112-04':
        raise ValueError('manifest contract')
    records=manifest['files'];listed=[]
    for entry in records:
        if set(entry)!={'path','sha256','size'}:raise ValueError('file schema')
        p=entry['path']
        if not isinstance(p,str) or p.startswith('/') or '\\' in p or any(c in ('.','..','') for c in p.split('/')) or p=='BUILD_MANIFEST.json':raise ValueError('unsafe path')
        if p in listed:raise ValueError('duplicate')
        listed.append(p)
        target=ROOT/p
        if target.is_symlink() or not target.is_file():raise ValueError('not regular file')
        b=target.read_bytes()
        if len(b)!=entry['size'] or hashlib.sha256(b).hexdigest()!=entry['sha256']:raise ValueError('bytes mismatch '+p)
        b.decode('utf-8')
    actual={x.relative_to(ROOT).as_posix() for x in ROOT.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.suffix!='.pyc'}
    if actual!=(set(listed)|{'BUILD_MANIFEST.json'}):raise ValueError('unexpected path '+str(actual-set(listed)-{'BUILD_MANIFEST.json'}))
    if listed!=sorted(listed):raise ValueError('nondeterministic ordering')
    return len(listed)
if __name__=='__main__':
    print('PUBLIC_SOURCE_V1_VERIFIED_FILES',verify())
