#!/usr/bin/env python3
"""Pinned, no-key, source-only intake for D16 Visual original (23rd recovered source).

Operates against disposable Git clones, not live game or Studio. Never runs Luau.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess

REPO_URL = 'https://github.com/kk051780/toy-wars-factory.git'
COMMIT = '226a5664ed50131868391289723c130d35abf48f'
PACKET = 'P0D-D16-VISUAL-REPLICA-ORIGINAL-PUBLIC-RECOVER-20261111-01'
ROOT = 'handoffs/' + PACKET
MANIFEST_SHA = 'f6d18f35db3b089c897d988b2524d36a17be42af6e71fa0ba18ccc792b0d9030'
CODE_HASHES = {
    'src/ScaleFxClientBootstrap.client.luau': 'c7989ab10b21f1a88ab73db9367decb3b8037be4704db2254e9f231c1d0dc11f',
    'src/ScaleFxClientPolicy.luau': '1b59e61dcb81eb0850074cdc8e217eab396716187be848f5faa4bb874cec3e14',
    'src/ScaleFxSnapshotBridge.luau': 'e8a9cdc15108c77017dd6da1a2538973ccf68776cdfd2ac129d0f5d867a6f4ea',
    'src/ScaleVisualReplica.luau': 'f90ea0e6bb36042fd7bd1caf5a6f2b86c6d870a36a441b9ecb5f086a55b84de2',
}
REQUIRED_API = {
    'src/ScaleFxClientPolicy.luau': ['function P.accept(state, packet, expectedMatchId, now)', 'function P.tick(state, expectedMatchId, now)'],
    'src/ScaleFxSnapshotBridge.luau': ['function B.build(snapshot, elapsedSeconds)'],
    'src/ScaleVisualReplica.luau': ['function Replica.new(remote, currentMatchId)', 'function Replica:destroy()'],
}
META = {'format': 'P0D_PUBLIC_SOURCE_V1', 'game_id': 'TRAP_RAIDERS',
        'work_id': 'p0d-siege-v19', 'packet_id': PACKET, 'public_source_allowed': True}

class ReceiptError(RuntimeError):
    pass

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe_path(x):
    if not isinstance(x, str) or not x or '\\' in x or '\x00' in x or ':' in x:
        raise ReceiptError('unsafe source path')
    p = PurePosixPath(x)
    if p.is_absolute() or any(part in ('', '.', '..') or part.startswith('.') for part in x.split('/')):
        raise ReceiptError('unsafe source path')
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-./' for c in x):
        raise ReceiptError('unsupported source path')
    return p

def git(repo, *args):
    try:
        p = subprocess.run(['git','-C',str(repo),*args], capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ReceiptError('git unavailable or timed out') from e
    if p.returncode != 0:
        raise ReceiptError('source commit/blob not present in isolated clone')
    return p.stdout

def blob(repo, commit, rel):
    safe_path(rel)
    line = git(repo,'ls-tree',commit,'--',rel).decode('utf8').strip()
    a=line.split('\t',1)
    if len(a)!=2 or a[1]!=rel or not (a[0].startswith('100644 blob ') or a[0].startswith('100755 blob ')):
        raise ReceiptError('missing/nonregular Git source blob: '+rel)
    result=git(repo,'show',commit+':'+rel)
    if len(result)>2_000_000:
        raise ReceiptError('oversized source blob')
    result.decode('utf8')
    return result

def verify(repo, *, commit=COMMIT, manifest_sha=MANIFEST_SHA, code_hashes=None, required_api=None):
    repo=Path(repo).resolve()
    if not re.fullmatch('[a-f0-9]{40}',commit):
        raise ReceiptError('full immutable 40-character commit SHA required')
    if git(repo,'cat-file','-t',commit).strip()!=b'commit':
        raise ReceiptError('not a Git commit')
    raw=blob(repo,commit,ROOT+'/BUILD_MANIFEST.json')
    if sha(raw)!=manifest_sha:
        raise ReceiptError('original manifest SHA mismatch')
    manifest=json.loads(raw)
    for k,v in META.items():
        if manifest.get(k)!=v:
            raise ReceiptError('wrong source identity: '+k)
    entries=manifest.get('files')
    if not isinstance(entries,list) or not (1<=len(entries)<=100):
        raise ReceiptError('malformed file list')
    files={'BUILD_MANIFEST.json':raw}; seen=set()
    for entry in entries:
        if not isinstance(entry,dict) or set(entry)!={'path','sha256','size'}:
            raise ReceiptError('malformed file descriptor')
        path=entry['path'];safe_path(path)
        if path in seen or path=='BUILD_MANIFEST.json':
            raise ReceiptError('duplicate/reserved file')
        seen.add(path)
        if type(entry['size']) is not int or entry['size']<0 or entry['size']>2_000_000:
            raise ReceiptError('bad declared size')
        if not isinstance(entry['sha256'],str) or not re.fullmatch('[a-f0-9]{64}',entry['sha256']):
            raise ReceiptError('bad declared SHA')
        content=blob(repo,commit,ROOT+'/'+path)
        if len(content)!=entry['size'] or sha(content)!=entry['sha256']:
            raise ReceiptError('file bytes mismatch: '+path)
        files[path]=content
    hashes=CODE_HASHES if code_hashes is None else code_hashes
    api=REQUIRED_API if required_api is None else required_api
    for path,digest in hashes.items():
        if path not in files or sha(files[path])!=digest:
            raise ReceiptError('wrong source code implementation: '+path)
    for path,phrases in api.items():
        if path not in files or any(p not in files[path].decode('utf8') for p in phrases):
            raise ReceiptError('incompatible original visual API: '+path)
    return files

def stage(repo, output, *, commit=COMMIT, manifest_sha=MANIFEST_SHA, code_hashes=None, required_api=None):
    repo=Path(repo).resolve(); out=Path(output).resolve()
    if out==repo or repo in out.parents:
        raise ReceiptError('destination must be outside cloned repository')
    if out.exists():
        raise ReceiptError('destination already exists; do not overwrite')
    files=verify(repo,commit=commit,manifest_sha=manifest_sha,code_hashes=code_hashes,required_api=required_api)
    out.mkdir(parents=True,exist_ok=False)
    try:
        for name,content in files.items():
            dest=out/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as fp:fp.write(content)
        receipt={'game_id':'TRAP_RAIDERS','work_id':'p0d-siege-v19',
                 'packet_id':PACKET,'git_commit_sha':commit,
                 'manifest_sha256':manifest_sha,'file_count':len(files),
                 'content_sha256':{p:sha(b) for p,b in sorted(files.items())},
                 'status':'PINNED_ORIGINAL_SOURCE_RECEIVED__NOT_STUDIO_TESTED',
                 'warning':'Original visual only. Never combine with D16 cleanroom visual 356dcd0d26aecf7bb5ab3e7d7a697e78a59db74e or extra Remote listeners. No game writes.'}
        (out/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
        return receipt
    except Exception:
        shutil.rmtree(out)
        raise

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',required=True,help='disposable isolated clone containing immutable source commit')
    ap.add_argument('--output',required=True,help='brand-new folder outside cloned repository and live PC game')
    args=ap.parse_args()
    print(json.dumps(stage(args.repo,args.output),ensure_ascii=False,indent=2,sort_keys=True))

if __name__=='__main__':main()
