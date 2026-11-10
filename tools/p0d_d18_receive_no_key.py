#!/usr/bin/env python3
"""P0-D D18 keyless OWNER->Windows-Codex intake: verify SHA then stage data only.

This script NEVER reads keys, connects to network, modifies game source, or launches Studio.
Public-safe and deterministic. Python 3.10+ standard library only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import sys
import tempfile
import zipfile

FILENAME = 'TRAP_RAIDERS_D18_V7_NO_KEY_OWNER_TRANSFER.zip'
MANIFEST = 'BUILD_MANIFEST.json'
MAX_ARCHIVE = 20 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_ONE = 20 * 1024 * 1024
MAX_FILES = 40
EXPECTED_SCHEMAS = {'P0D_D18_V7_KEYLESS_SELF_CONTAINED'}

class IntakeError(Exception):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def candidate_locations(home: pathlib.Path) -> tuple[pathlib.Path, ...]:
    return (home / 'Downloads' / FILENAME, home / 'TRAP_RAIDERS' / 'handoff' / 'inbox' / FILENAME)


def resolve_archive(explicit: str | None, home: pathlib.Path) -> pathlib.Path:
    if explicit:
        f = pathlib.Path(explicit).expanduser()
        if not f.is_file():
            raise IntakeError('ARCHIVE_NOT_FOUND: explicit --archive path does not exist')
        return f
    found = [p for p in candidate_locations(home) if p.is_file()]
    if len(found) == 0:
        raise IntakeError('ARCHIVE_NOT_FOUND: expected only Downloads or TRAP_RAIDERS/handoff/inbox; never search entire disk')
    if len(found) > 1:
        raise IntakeError('AMBIGUOUS_ARCHIVES: remove one duplicate or specify --archive; no automatic latest selection')
    return found[0]


def validate_archive(path: pathlib.Path, expected_sha: str):
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha):
        raise IntakeError('EXPECTED_SHA_INVALID: must be 64 lowercase hexadecimal characters')
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE:
        raise IntakeError('ARCHIVE_TOO_LARGE_OR_MISSING')
    with path.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else None
    if digest is None:
        with path.open('rb') as f:
            h=hashlib.sha256()
            for chunk in iter(lambda:f.read(1024*1024),b''):
                h.update(chunk)
            digest=h.hexdigest()
    if digest != expected_sha:
        raise IntakeError(f'OUTER_SHA_MISMATCH: got {digest}, expected {expected_sha}')
    with zipfile.ZipFile(path, 'r', allowZip64=False) as z:
        infos = z.infolist()
        if len(infos) < 2 or len(infos) > MAX_FILES:
            raise IntakeError('ENTRY_COUNT_INVALID')
        names = [info.filename for info in infos]
        if len(set(names)) != len(names):
            raise IntakeError('DUPLICATE_MEMBER_NAME')
        if MANIFEST not in names:
            raise IntakeError('MANIFEST_MISSING')
        total = 0
        for info in infos:
            name=info.filename
            if info.is_dir() or '/' in name or '\\' in name or name.startswith('.') or ':' in name or len(name)>120:
                raise IntakeError('UNSAFE_MEMBER_PATH')
            if info.flag_bits & 0x1:
                raise IntakeError('ENCRYPTED_ZIP_NOT_ACCEPTED: D18 V7 must not require a key')
            if (info.external_attr >> 16) & 0o170000 == stat.S_IFLNK:
                raise IntakeError('SYMLINK_MEMBER_REJECTED')
            if info.file_size>MAX_ONE:
                raise IntakeError('MEMBER_TOO_LARGE')
            if info.file_size and info.file_size/max(info.compress_size,1)>250:
                raise IntakeError('COMPRESSION_RATIO_EXCESSIVE')
            total+=info.file_size
            if total>MAX_TOTAL:
                raise IntakeError('TOTAL_UNCOMPRESSED_TOO_LARGE')
        raw_manifest=z.read(MANIFEST)
        if len(raw_manifest)>100000:
            raise IntakeError('MANIFEST_TOO_LARGE')
        try:m=json.loads(raw_manifest)
        except (UnicodeDecodeError,json.JSONDecodeError):raise IntakeError('MANIFEST_INVALID_JSON')
        if m.get('schema_version') not in EXPECTED_SCHEMAS or m.get('game_id')!='TRAP_RAIDERS':
            raise IntakeError('MANIFEST_SCHEMA_OR_GAME_INVALID')
        if m.get('work_id')!='p0d-siege-v19' or m.get('revision')!='WAVE5_NO_KEY_HANDOFF_V7':
            raise IntakeError('WORK_ID_OR_REVISION_INVALID')
        files=m.get('files')
        if not isinstance(files,list) or len(files)!=len(names)-1:
            raise IntakeError('MANIFEST_FILE_COUNT_INVALID')
        recorded=[x.get('path') for x in files if isinstance(x,dict)]
        if len(recorded)!=len(files) or set(recorded)!=set(names)-{MANIFEST} or len(set(recorded))!=len(recorded):
            raise IntakeError('MANIFEST_CONTENT_SET_MISMATCH')
        byname={x['path']:x for x in files}
        for name in sorted(set(names)-{MANIFEST}):
            data=z.read(name)
            meta=byname[name]
            if len(data)!=meta.get('bytes') or sha256(data)!=meta.get('sha256'):
                raise IntakeError('MANIFEST_MEMBER_HASH_MISMATCH')
        view=json.loads(z.read('catalog_flat_648_v7.json'))
        entries=view['entries'];info=view['metadata']
        if len(entries)!=648 or len({e['id'] for e in entries})!=648:
            raise IntakeError('CATALOG_ID_COUNT_INVALID')
        edited=sum('editorial' in e for e in entries)
        heroes=sum(e.get('is_hero') and 'editorial' in e for e in entries)
        if edited!=66 or heroes!=60 or info.get('individual_editorial')!=66:
            raise IntakeError('CATALOG_EDITORIAL_COUNT_INVALID')
        new=json.loads(z.read('wave5_12_hero_editorial_v7.json'))
        if len(new.get('items',[]))!=12 or len({e['id'] for e in new['items']})!=12:
            raise IntakeError('NEW_WAVE_COUNT_INVALID')
        return m, {name:z.read(name) for name in names if name!=MANIFEST}, raw_manifest


def stage_validated(bundle, manifest_bytes, expected_sha: str, home: pathlib.Path, out_root: pathlib.Path | None = None) -> pathlib.Path:
    root = out_root or (home/'TRAP_RAIDERS'/'handoff'/'staged')
    root.mkdir(parents=True,exist_ok=True)
    target=root/f'D18_V7_{expected_sha[:12]}'
    if target.exists():
        raise IntakeError('STAGE_ALREADY_EXISTS: no implicit overwrite of previous work')
    tempdir=pathlib.Path(tempfile.mkdtemp(prefix='.d18_v7_tmp_',dir=root))
    try:
        for name,data in bundle.items():
            (tempdir/name).write_bytes(data)
        (tempdir/MANIFEST).write_bytes(manifest_bytes)
        (tempdir/'RECEIVE_STATUS.txt').write_text(
            'D18 V7 KEYLESS LOCAL STAGING VERIFIED\n'
            f'ZIP_SHA256={expected_sha}\n'
            'SOURCE=OWNER LOCAL FILE, NOT PUBLIC GITHUB\n'
            'INTEGRATED_INTO_GAME=NO\nROBLOX_STUDIO_QA=NOT_TESTED\n', encoding='utf-8')
        tempdir.rename(target)
    except Exception:
        shutil.rmtree(tempdir,ignore_errors=True)
        raise
    return target


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description='Verify an OWNER-provided D18 V7 ZIP without any private decryption key, then stage locally only.')
    parser.add_argument('--expected-sha',required=True,help='Exact SHA-256 pinned to the public GitHub handoff manifest')
    parser.add_argument('--archive',help='Explicit local zip path; otherwise only Downloads/inbox are checked')
    parser.add_argument('--stage-root',help='Optional isolated output root for tests (never game source)')
    parser.add_argument('--verify-only',action='store_true',help='No filesystem writes even after successful verification')
    args=parser.parse_args(argv)
    try:
        home=pathlib.Path.home()
        path=resolve_archive(args.archive,home)
        m,bundle,manifest=validate_archive(path,args.expected_sha)
        if args.verify_only:
            print(f'PASS VERIFY_ONLY archive={path.name} sha256={args.expected_sha} entries={len(bundle)} catalog=648 edited=66 flagship=60')
            return 0
        target=stage_validated(bundle,manifest,args.expected_sha,home,pathlib.Path(args.stage_root) if args.stage_root else None)
        print(f'PASS STAGED_ONLY location={target} sha256={args.expected_sha} models=NOT_IMPLEMENTED studio=NOT_TESTED')
        return 0
    except (IntakeError,ValueError,zipfile.BadZipFile,PermissionError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:
        print(f'FAIL_CLOSED {e}',file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(main())