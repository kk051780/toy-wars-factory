#!/usr/bin/env python3
"""Verify SHA/size of this public source-free D14 bundle; no network/execution."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'BUILD_MANIFEST.json').read_text('utf-8'))
assert manifest['schema']=='P0D_D14_PUBLIC_QA_MANIFEST_V1'
assert manifest['packet_id']=='P0D-D14-TRIAD-CONTRACT-QA-20261110-01'
for e in manifest['files']:
    path=e['path']
    assert path==Path(path).as_posix() and '..' not in Path(path).parts and not Path(path).is_absolute(), 'UNSAFE_PATH'
    p=ROOT/path
    assert p.is_file() and not p.is_symlink(), 'FILE_MISSING_OR_SYMLINK'
    data=p.read_bytes()
    assert len(data)==e['size'] and hashlib.sha256(data).hexdigest()==e['sha256'], 'HASH_MISMATCH:'+path
print('PUBLIC_MANIFEST_VERIFIED',len(manifest['files']))
