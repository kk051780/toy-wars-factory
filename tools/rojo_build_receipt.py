#!/usr/bin/env python3
"""Build-only .rbxl receipt; no networking, secrets, Studio, or Roblox API.

Requires the source-contract check to run earlier in a reviewed manual-only
GitHub job. Emits UNTRUSTED local metadata, never a provider attestation.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from rojo_rbxl_gate import inspect as inspect_binary, MAX_BYTES

REPO = 'kk051780/toy-wars-factory'
OUTDIR = Path('.qa/rojo')
BINARY = 'toy-wars-private-test.rbxl'
RECEIPT = 'build-receipt.json'
SHA = re.compile(r'[0-9a-f]{40}\Z')


def make(root: Path, env: dict) -> dict:
    if (type(env) is not dict or env.get('GITHUB_REPOSITORY') != REPO or
        env.get('GITHUB_REF') != 'refs/heads/main' or
        env.get('GITHUB_EVENT_NAME') != 'workflow_dispatch' or
        type(env.get('GITHUB_SHA')) is not str or
        SHA.fullmatch(env['GITHUB_SHA']) is None):
        raise ValueError('WRONG_MANUAL_MAIN_IDENTITY')
    base = root / OUTDIR
    binary_path = base / BINARY
    receipt_path = base / RECEIPT
    if (not base.is_dir() or base.is_symlink() or binary_path.is_symlink() or
        not binary_path.is_file() or receipt_path.exists() or receipt_path.is_symlink()):
        raise ValueError('INVALID_BUILD_OUTPUT_PATH')
    if set(p.name for p in base.iterdir()) != {BINARY}:
        raise ValueError('UNEXPECTED_BUILD_ARTIFACT')
    if binary_path.stat().st_size > MAX_BYTES:
        raise ValueError('OVERSIZED_BUILD_OUTPUT')
    # The actual pinned PR143 gate checks RBXL framing, not Roblox engine data.
    blob = binary_path.read_bytes()
    check = inspect_binary(blob)
    if (check.get('engine_verified') is not False or
        check.get('sha256') != hashlib.sha256(blob).hexdigest() or
        check.get('bytes') != len(blob)):
        raise ValueError('BUILD_GATE_MISMATCH')
    receipt = {
        'repository': REPO,
        'source_main_sha': env['GITHUB_SHA'],
        'rbxl_sha256': hashlib.sha256(blob).hexdigest(),
        'rbxl_bytes': len(blob),
        'build_only': True,
        'engine_verified': False,
    }
    # Fail closed on repeated command, symlink or stale artifact.
    with receipt_path.open('x', encoding='utf8') as target:
        json.dump(receipt, target, sort_keys=True, separators=(',', ':'))
        target.write('\n')
    if set(p.name for p in base.iterdir()) != {BINARY, RECEIPT}:
        raise ValueError('BUILD_OUTPUT_CHANGED')
    return receipt


def main() -> int:
    try:
        make(Path.cwd(), dict(os.environ))
        print('PR144_COMPATIBLE_RECEIPT_WRITTEN_NOT_ENGINE_VERIFIED')
        return 0
    except (OSError, ValueError, TypeError):
        print('BUILD_RECEIPT_DENIED_NO_ROBLOX_ACTION', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
