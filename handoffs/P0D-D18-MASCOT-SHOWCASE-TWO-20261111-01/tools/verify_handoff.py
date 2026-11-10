#!/usr/bin/env python3
"""Fail-closed local source-only manifest build/verify, compatible with P0D_PUBLIC_SOURCE_V1 manifest format.

Independent implementation of the published format for self-contained reproducibility;
not a substitute for running the canonical pinned p0d_public_pack.py on the PC.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re

FORMAT='P0D_PUBLIC_SOURCE_V1'
GAME='TRAP_RAIDERS'
WORK='p0d-siege-v19'
PACKET='P0D-D18-MASCOT-SHOWCASE-TWO-20261111-01'
SUFFIX={'.luau','.lua','.py','.md','.json','.txt','.csv','.toml','.yaml','.yml'}
SECRETS=[
    re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----'),
    re.compile(rb'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b'),
    re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{20,}\b'),
    re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b'),
    re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
]


def collect(root:Path)->list[dict]:
    if not root.is_dir() or root.is_symlink(): raise ValueError('invalid root')
    records=[]; total=0; names=set()
    for base, ds, fs in os.walk(root):
        for d in ds:
            p=Path(base)/d
            if p.is_symlink() or d.startswith('.'): raise ValueError('unsafe directory')
        for name in fs:
            p=Path(base)/name
            rel=p.relative_to(root).as_posix()
            if rel=='BUILD_MANIFEST.json': continue
            pp=PurePosixPath(rel)
            if not p.is_file() or p.is_symlink() or rel!=str(pp) or any(x in ('','.','..') or x.startswith('.') for x in pp.parts) or ':' in rel or '\\' in rel or pp.suffix not in SUFFIX: raise ValueError(f'unsafe source path {rel}')
            if rel.casefold() in names: raise ValueError('case collision')
            names.add(rel.casefold())
            b=p.read_bytes(); total+=len(b)
            if len(b)>2*1024*1024 or total>10*1024*1024: raise ValueError('size cap')
            b.decode('utf-8',errors='strict')
            for pattern in SECRETS:
                if pattern.search(b): raise ValueError(f'secret-like data {rel}')
            records.append({'path':rel,'sha256':hashlib.sha256(b).hexdigest(),'size':len(b)})
    if not records or len(records)>250: raise ValueError('invalid count')
    return sorted(records,key=lambda x:x['path'])


def manifest_for(root:Path)->dict:
    return {'files':collect(root),'format':FORMAT,'game_id':GAME,'packet_id':PACKET,'public_source_allowed':True,'work_id':WORK}


def do(mode:str,root:Path):
    manifest=manifest_for(root)
    path=root/'BUILD_MANIFEST.json'
    if mode=='build':
        path.write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    else:
        old=json.loads(path.read_text(encoding='utf-8'))
        if old!=manifest: raise ValueError('manifest mismatch; source changed')
    raw=path.read_bytes()
    print(f'{mode.upper()}_PASS entries={len(manifest["files"])} manifest_sha256={hashlib.sha256(raw).hexdigest()}')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['build','verify']);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=ap.parse_args();do(args.mode,args.root)
