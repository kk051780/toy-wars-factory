#!/usr/bin/env python3
"""P0-D keyless source batch verification and PRIVATE-only staging. stdlib + gh CLI."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

EXPECTED_REPO = 'kk051780/trap-raiders-private-source'
PACKET_RE = re.compile(r'^[A-Z0-9][A-Z0-9_.-]{3,127}$')
SHA_RE = re.compile(r'^[a-f0-9]{64}$')
MAX_TOTAL = 40_000_000
MAX_FILE = 2_000_000

class PolicyError(Exception):
    pass


def safe_name(name: str) -> str:
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name or name.startswith('/'):
        raise PolicyError('unsafe name')
    p = PurePosixPath(name)
    if any(x in ('', '.', '..', '.git') for x in name.split('/')) or p.is_absolute():
        raise PolicyError('unsafe path components')
    if any(part.startswith('.') for part in p.parts):
        raise PolicyError('hidden paths forbidden')
    if p.suffix not in ('.luau','.lua','.py','.json','.md','.txt'):
        raise PolicyError('unexpected file type: '+p.suffix)
    return name


def load_manifest(root: Path) -> dict:
    mf = (root/'migration_manifest.json')
    if mf.is_symlink() or not mf.is_file() or mf.stat().st_size>1_000_000:
        raise PolicyError('manifest unavailable')
    def no_dupes(pairs):
        obj={}
        for k,v in pairs:
            if k in obj:raise PolicyError('duplicate json key')
            obj[k]=v
        return obj
    doc=json.loads(mf.read_text('utf-8'), object_pairs_hook=no_dupes)
    if doc.get('format')!='P0D_KEYLESS_BATCH_V1' or doc.get('target_private_repo')!=EXPECTED_REPO:
        raise PolicyError('manifest/repository incompatible')
    packs=doc.get('packets')
    if not isinstance(packs,list) or not packs or len(packs)>100:
        raise PolicyError('bad packet list')
    ids=set();total=0
    for pack in packs:
        pid=pack.get('packet_id')
        if not isinstance(pid,str) or not PACKET_RE.fullmatch(pid) or pid in ids:
            raise PolicyError('bad/duplicate packet ID')
        ids.add(pid)
        files=pack.get('files')
        if not isinstance(files,list) or not files or len(files)>100:
            raise PolicyError('bad file list')
        names=set()
        for f in files:
            rel=safe_name(f.get('path'))
            if rel in names:raise PolicyError('duplicate file path')
            names.add(rel)
            sha=f.get('sha256');size=f.get('bytes')
            if not isinstance(sha,str) or not SHA_RE.fullmatch(sha) or type(size)!=int or size<0 or size>MAX_FILE:
                raise PolicyError('bad digest/size')
            p=root/'source_packages'/pid/rel
            if p.is_symlink() or not p.is_file():raise PolicyError('source file missing or symlink')
            actual=p.read_bytes()
            if len(actual)!=size or hashlib.sha256(actual).hexdigest()!=sha:
                raise PolicyError('source file mismatch: '+pid+'/'+rel)
            total+=size
            if total>MAX_TOTAL:raise PolicyError('batch too large')
        discovered=set()
        for path in (root/'source_packages'/pid).rglob('*'):
            if path.is_symlink():raise PolicyError('source symlink forbidden')
            if path.is_file():discovered.add(path.relative_to(root/'source_packages'/pid).as_posix())
        if names!=discovered:raise PolicyError('unmanifested sources: '+pid)
    extra=[]
    root_source=root/'source_packages'
    for p in root_source.iterdir():
        if p.name not in ids:extra.append(p.name)
    if extra:raise PolicyError('extra packet dirs')
    return doc


def shell(args: list[str]) -> str:
    try:
        p=subprocess.run(args,check=True,text=True,capture_output=True,timeout=15)
        return p.stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise PolicyError('authenticated git/gh check failed: '+str(exc)) from exc


def require_private_repo(repo_path: Path, repo_name: str) -> None:
    if repo_name!=EXPECTED_REPO:raise PolicyError('unauthorized target repo')
    if not repo_path.is_dir():raise PolicyError('target checkout does not exist')
    result=shell(['gh','repo','view',repo_name,'--json','nameWithOwner,visibility'])
    info=json.loads(result)
    if info.get('nameWithOwner')!=repo_name or info.get('visibility')!='PRIVATE':
        raise PolicyError('target repo is not confirmed PRIVATE')
    checkout=Path(shell(['git','-C',str(repo_path),'rev-parse','--show-toplevel'])).resolve()
    if checkout !=repo_path.resolve():raise PolicyError('target must be top level checkout')
    remote=shell(['git','-C',str(repo_path),'remote','get-url','origin'])
    if not re.fullmatch(r'(?:https://github\.com/|git@github\.com:)kk051780/trap-raiders-private-source(?:\.git)?',remote):
        raise PolicyError('origin is not the private target')
    branch=shell(['git','-C',str(repo_path),'branch','--show-current'])
    if not branch or branch in ('main','master'):
        raise PolicyError('work only on isolated non-default branch')
    if shell(['git','-C',str(repo_path),'status','--porcelain']):
        raise PolicyError('target checkout has modifications: require clean tree')


def stage(root:Path, private_repo:Path, repo_name:str):
    doc=load_manifest(root)
    require_private_repo(private_repo,repo_name)
    base=private_repo/'handoffs'/'keyless-v1'
    targets=[]
    for pack in doc['packets']:
        for f in pack['files']:
            rel=Path('handoffs')/'keyless-v1'/pack['packet_id']/f['path']
            p=private_repo/rel
            if p.exists() or p.is_symlink():raise PolicyError('would overwrite '+str(rel))
            targets.append((root/'source_packages'/pack['packet_id']/f['path'],p))
    staged=[]
    try:
        for src,dst in targets:
            for parent in (dst.parent, *dst.parent.parents):
                if parent == private_repo.parent: break
                if parent.is_symlink(): raise PolicyError('target symlink parent forbidden')
            if not dst.resolve().is_relative_to(private_repo.resolve()):
                raise PolicyError('target path escapes checkout')
            dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('xb') as out: out.write(src.read_bytes())
            staged.append(dst)
        m=base/'KEYLESS_MIGRATION_MANIFEST.json'
        m.parent.mkdir(parents=True,exist_ok=True)
        with m.open('xb') as out:out.write((root/'migration_manifest.json').read_bytes())
        staged.append(m)
    except BaseException:
        for p in reversed(staged):p.unlink(missing_ok=True)
        raise
    return len(targets)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--bundle-root',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--stage-to',type=Path)
    p.add_argument('--repo',default=EXPECTED_REPO)
    args=p.parse_args()
    try:
        manifest=load_manifest(args.bundle_root)
        count=sum(len(z['files']) for z in manifest['packets'])
        print(f'KEYLESS_BATCH_VERIFIED packets={len(manifest["packets"])} files={count}')
        if args.stage_to:
            moved=stage(args.bundle_root,args.stage_to,args.repo)
            print(f'PRIVATE_ONLY_STAGED source_files={moved} -- not committed/pushed/merged')
        else:print('CHECK_ONLY: no files staged')
        return 0
    except (PolicyError,ValueError,TypeError,KeyError, OSError) as e:
        print('KEYLESS_HOLD: '+str(e),file=sys.stderr)
        return 2
if __name__=='__main__':raise SystemExit(main())
