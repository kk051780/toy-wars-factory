#!/usr/bin/env python3
"""No external dependencies. Verify P0D_PUBLIC_SOURCE_V1 manifest, blobs and no secrets."""
import hashlib, json, pathlib, re, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
EXPECTED={"format","game_id","work_id","packet_id","public_source_allowed","files"}
BLACKLIST=("BEGIN"+" PRIVATE KEY", "gh"+"p_", "AK"+"IA", "Authorization:"+" Bearer", "AES"+"-GCM")

def verify(root=ROOT):
    manifest=json.loads((root/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
    if set(manifest)!=EXPECTED: raise ValueError('manifest keys mismatch')
    if manifest['format']!='P0D_PUBLIC_SOURCE_V1' or manifest['public_source_allowed'] is not True: raise ValueError('format flag')
    if manifest['game_id']!='TRAP_RAIDERS' or manifest['work_id']!='p0d-siege-v19': raise ValueError('game identity')
    if manifest['packet_id']!='P0D-D18-STARLAUNCH-THUNDERHORN-SHOWCASE-20261112-03': raise ValueError('packet identity')
    paths=[]
    for f in manifest['files']:
        if set(f)!={'path','sha256','size'}: raise ValueError('bad record')
        name=f['path']; p=pathlib.PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or not name or name.startswith('.'): raise ValueError('traversal')
        file=root/name
        if not file.is_file() or file.is_symlink(): raise ValueError('missing or linked')
        b=file.read_bytes()
        if len(b)!=f['size'] or hashlib.sha256(b).hexdigest()!=f['sha256']: raise ValueError('bytes/hash mismatch: '+name)
        decoded=b.decode('utf-8')
        if any(token in decoded for token in BLACKLIST): raise ValueError('secret token')
        paths.append(name)
    if len(paths)!=len(set(paths)): raise ValueError('duplicate path')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if actual - set(paths) - {'BUILD_MANIFEST.json'}: raise ValueError('untracked files: '+repr(actual-set(paths)-{'BUILD_MANIFEST.json'}))
    if len(paths)<9: raise ValueError('missing package source')
    return len(paths)
if __name__=='__main__':
    try: print('PUBLIC_SOURCE_V1 VERIFIED',verify())
    except Exception as e: print('FAILED',e,file=sys.stderr);raise SystemExit(1)
