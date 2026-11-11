#!/usr/bin/env python3
"""Canonical six-field PUBLIC_SOURCE_V1 plain-text source package validator."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
assert set(manifest)=={'format','game_id','work_id','packet_id','public_source_allowed','files'}
assert manifest['format']=='P0D_PUBLIC_SOURCE_V1'
assert manifest['game_id']=='TRAP_RAIDERS'
assert manifest['work_id']=='p0d-siege-v19'
assert manifest['public_source_allowed'] is True
assert manifest['packet_id']=='P0D-S1-LOBBY-NATIVE-LUAU-SEMANTIC-REPLAY-20261112-01'
items=manifest['files']
assert len(items)==5
assert len(set(x['path'] for x in items))==len(items)
for x in items:
    assert set(x)=={'path','size','sha256'}
    p=(ROOT/x['path']).resolve(strict=True)
    assert p.is_relative_to(ROOT.resolve()) and p.is_file() and not p.is_symlink()
    data=p.read_bytes()
    assert len(data)==x['size'] and hashlib.sha256(data).hexdigest()==x['sha256']
actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.name != '.DS_Store'}
assert actual==set(x['path'] for x in items)|{'BUILD_MANIFEST.json'},(actual,items)
print('PUBLIC_SOURCE_V1_NATIVE_REPLAY_SHA256_PASS files=',len(items))
