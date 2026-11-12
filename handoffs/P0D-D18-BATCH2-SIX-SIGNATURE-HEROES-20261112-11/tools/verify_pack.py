#!/usr/bin/env python3
"""Public source V1: reject unknown extra and wrong-hash files; no passwords."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED_KEYS={'format','game_id','work_id','packet_id','public_source_allowed','files'}
MANIFEST=ROOT/'BUILD_MANIFEST.json'
def check(root=ROOT):
    m=json.loads((root/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
    if set(m)!=REQUIRED_KEYS or m['format']!='P0D_PUBLIC_SOURCE_V1' or m['game_id']!='TRAP_RAIDERS' or m['public_source_allowed'] is not True:raise ValueError('invalid_public_manifest')
    entries=m['files']
    if not isinstance(entries,list) or not entries:raise ValueError('empty_manifest')
    seen=set()
    for item in entries:
        if set(item)!={'path','sha256','size_bytes'}:raise ValueError('bad_manifest_row')
        p=item['path']
        if not isinstance(p,str) or p.startswith('/') or '..' in Path(p).parts or '\\' in p or p in seen:raise ValueError('unsafe_manifest_path')
        seen.add(p)
        f=root/p
        if f.is_symlink() or not f.is_file():raise ValueError('missing_source')
        raw=f.read_bytes()
        if b'\0' in raw:raise ValueError('non_text_source')
        raw.decode('utf-8')
        if len(raw)!=item['size_bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('tampered_source '+p)
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if seen|{'BUILD_MANIFEST.json'} != actual:raise ValueError('extra_or_missing_source')
    return len(seen)
if __name__=='__main__':
    print('P0D_PUBLIC_SOURCE_V1_OK sha256_byte_count=',check())
