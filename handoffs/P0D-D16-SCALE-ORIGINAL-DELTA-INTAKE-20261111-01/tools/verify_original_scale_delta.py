#!/usr/bin/env python3
"""Read-only, immutable-commit D16 original ScaleFx keyless intake.

Input is an isolated repo clone with the pinned original source commit present.
Outputs only to a fresh external staging directory. Does not run any game code.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess

COMMIT = '584b11ef24cf3d44695d86b505207491bbd3844e'
PACKET = 'P0D-D16-SCALE-FX-ORIGINAL-PUBLIC-RECOVER-20261111-01'
ROOT = 'handoffs/' + PACKET
MANIFEST_SHA256 = '2d5050efe5952aea82720a4b06ead61684da01d6f7286f26ddd3ff41740d264f'
ORIGINAL_LUAU_SHA256 = '5f07a14aec3d0b76fa2184ac3daf19e965794fda6ecd992653262c0c3cf68463'
CLEANROOM_LUAU_SHA256 = 'ceee7452e7ce645cbad6057acd9927b0faeb05ce915a8d3dfbae648665a8d5db'
EXPECTED = {'format':'P0D_PUBLIC_SOURCE_V1', 'game_id':'TRAP_RAIDERS',
            'work_id':'p0d-siege-v19', 'packet_id':PACKET, 'public_source_allowed':True}

class IntakeError(RuntimeError):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git(repo, *args):
    p = subprocess.run(['git', '-C', str(repo), *args], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=False, timeout=15)
    if p.returncode:
        raise IntakeError('git command failed (verify commit exists and repo is accessible)')
    return p.stdout

def safe_path(path):
    if not isinstance(path, str) or not path or '\\' in path or '\x00' in path:
        raise IntakeError('unsafe path')
    p = PurePosixPath(path)
    if p.is_absolute() or any(part in ('..', '.') for part in path.split('/')) or ':' in path:
        raise IntakeError('unsafe path')
    if any(part.startswith('.') for part in p.parts):
        raise IntakeError('hidden path')
    return p

def get_blob(repo, commit, fullpath):
    safe_path(fullpath)
    line = git(repo, 'ls-tree', commit, '--', fullpath).decode('utf8', errors='strict').strip()
    chunks = line.split('\t', 1)
    if len(chunks) != 2 or chunks[1] != fullpath or not chunks[0].startswith(('100644 blob ', '100755 blob ')):
        raise IntakeError('missing or non-regular git blob: ' + fullpath)
    b = git(repo, 'show', commit + ':' + fullpath)
    if len(b) > 2_000_000:
        raise IntakeError('oversize blob')
    b.decode('utf8')
    return b

def verify(repo, commit=COMMIT, root=ROOT, manifest_hash=MANIFEST_SHA256):
    repo = Path(repo).resolve()
    if not re.fullmatch(r'[a-f0-9]{40}', commit):
        raise IntakeError('pin must be a full 40-character commit SHA')
    safe_path(root)
    if git(repo, 'cat-file', '-t', commit).strip() != b'commit':
        raise IntakeError('not a commit')
    m = get_blob(repo, commit, root+'/BUILD_MANIFEST.json')
    if digest(m) != manifest_hash:
        raise IntakeError('manifest hash mismatch')
    obj = json.loads(m)
    for k,v in EXPECTED.items():
        if obj.get(k) != v:
            raise IntakeError('wrong game/packet/protocol: '+k)
    fs = obj.get('files')
    if not isinstance(fs, list) or not fs or len(fs) > 250:
        raise IntakeError('invalid file listing')
    output = {'BUILD_MANIFEST.json': m}
    seen = set()
    for e in fs:
        if not isinstance(e, dict) or set(e) != {'path','sha256','size'}:
            raise IntakeError('unexpected manifest entry')
        p = e['path']
        safe_path(p)
        if p in seen or p == 'BUILD_MANIFEST.json':
            raise IntakeError('duplicate/reserved entry')
        seen.add(p)
        if not isinstance(e['size'], int) or not 0 <= e['size'] <= 2_000_000:
            raise IntakeError('bad size')
        if not re.fullmatch(r'[a-f0-9]{64}', e['sha256']):
            raise IntakeError('bad sha')
        b = get_blob(repo, commit, root+'/'+p)
        if len(b) != e['size'] or digest(b) != e['sha256']:
            raise IntakeError('byte/SHA mismatch: '+p)
        output[p] = b
    if set(output) != set(seen)|{'BUILD_MANIFEST.json'}:
        raise IntakeError('incomplete pack')
    scale = next(x for x in fs if x['path']=='src/ScaleFxCore.luau')
    if scale['sha256'] != ORIGINAL_LUAU_SHA256 or scale['sha256'] == CLEANROOM_LUAU_SHA256:
        raise IntakeError('wrong/incompatible ScaleFx API implementation')
    code = output['src/ScaleFxCore.luau'].decode('utf8')
    if 'function M.new(matchId)' not in code or 'function M.begin(s, matchId, eventId, kind, actorId, roster, now)' not in code:
        raise IntakeError('original ScaleFx API contract mismatch')
    return output

def stage(repo, target, *, commit=COMMIT, root=ROOT, manifest_hash=MANIFEST_SHA256):
    repo, target = Path(repo).resolve(), Path(target).resolve()
    if target == repo or repo in target.parents:
        raise IntakeError('target must be outside repository')
    if target.exists():
        raise IntakeError('target already exists; refusing overwrite')
    files = verify(repo, commit=commit, root=root, manifest_hash=manifest_hash)
    target.mkdir(parents=True, exist_ok=False)
    try:
        for rel,data in files.items():
            dest = target/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:
                f.write(data)
        receipt = {'game_id':'TRAP_RAIDERS','work_id':'p0d-siege-v19',
                   'packet_id':PACKET,'source_commit':commit,
                   'source_manifest_sha256':manifest_hash,
                   'file_count':len(files), 'file_sha256':{x:digest(y) for x,y in sorted(files.items())},
                   'status':'SOURCE_BYTE_VERIFIED__NO_STUDIO_CLAIM',
                   'incompatible_cleanroom_and_gate_v1_v2':'DO_NOT_INSTALL_WITH_ORIGINAL'}
        (target/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf8')
    except Exception:
        shutil.rmtree(target)
        raise
    return receipt

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True, help='isolated local clone; never the live PC game')
    ap.add_argument('--output', required=True, help='new external staging folder, must not already exist')
    args = ap.parse_args()
    print(json.dumps(stage(args.repo, args.output),indent=2,sort_keys=True))

if __name__ == '__main__':
    main()
