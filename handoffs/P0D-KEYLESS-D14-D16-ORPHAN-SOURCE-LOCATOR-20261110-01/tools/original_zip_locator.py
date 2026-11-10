#!/usr/bin/env python3
"""Read-only original ZIP locator and optional isolated staging for P0D D14/D16.

NO decryption, GitHub writes, source synthesis, Studio, or shared worktree access.
Original unencrypted ZIPs must match the known historical SHA-256 EXACTLY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

GAME = 'TRAP_RAIDERS'
WORK = 'p0d-siege-v19'
EXPECTED_ZIP_SHA256 = {
    'P0D-D14-VEHICLE-SEATS-20261110-01': '475616bd21e88164158db88b3a97e33d4a9b1ce9aaa872fa7a816adf485c9fd3',
    'P0D-D14-RAFT-WATER-MOTION-20261110-03': 'd218baef4ba958195b9e0ad22a4046313c52c3d150b424e0e99981cb351854c6',
    'P0D-D14-RIDER-ATTACH-SAFETY-20261110-04': '11b7bae8ce25d48e2ba813058583f3a882a4bf19890ca6e004a9e519647616fe',
    'P0D-D16-SCALE-FX-20261110-01': 'd5df52cd3b2fdf26bca05bc38123ac81d27024c944c4a465d66e3a4e0ad0c7cd',
    'P0D-D16-VISUAL-REPLICA-20261110-02': '31a53ead53095152ac57d2b0ee49b49c37477c5341ef0bdd25c8c463fd911d7d',
    'P0D-D16-CLOCK-RAIN-VFX-20261110-03': 'bcee9a949dc897b1d9a54557a93959ccd8b0e068223310594a8d27ec4fdcea62',
    'P0D-D16-GLIDE-AUTH-20261110-04': '872e8f9ec5ef38535ee3b295bf301a612e2063835e85cae67ab87bb370aee2cc',
}
ALLOWED = {'.luau', '.lua', '.py', '.json', '.md', '.txt', '.csv', '.toml', '.yaml', '.yml'}
MAX_ARCHIVE_SIZE = 25 * 1024 * 1024
MAX_ENTRY_SIZE = 2 * 1024 * 1024
MAX_FILES = 250
SECRET_RE = [re.compile(x, re.I) for x in (
    rb'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    rb'\bgh[pousr]_[A-Za-z0-9]{20,}\b',
    rb'\bgithub_pat_[A-Za-z0-9_]{20,}\b',
    rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b',
)]


class Rejected(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    if not name or len(name) > 260 or '\\' in name or ':' in name or '\x00' in name or name.startswith('/'):
        raise Rejected('unsafe path')
    parts = PurePosixPath(name).parts
    if not parts or any(p in ('', '.', '..') or p.startswith('.') for p in parts):
        raise Rejected('traversal/hidden path')
    if '/'.join(parts) != name or PurePosixPath(name).suffix.lower() not in ALLOWED:
        raise Rejected('noncanonical or non-source path')
    return name


def examine(path: Path, packet_id: str) -> dict[str, bytes]:
    if packet_id not in EXPECTED_ZIP_SHA256:
        raise Rejected('unknown old packet')
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_ARCHIVE_SIZE:
        raise Rejected('missing/unsafe/oversize original ZIP')
    if sha256(path.read_bytes()) != EXPECTED_ZIP_SHA256[packet_id]:
        raise Rejected('original ZIP SHA mismatch: do not claim recovered')
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(path) as archive:
        entries = [z for z in archive.infolist() if not z.is_dir()]
        if not entries or len(entries) > MAX_FILES:
            raise Rejected('empty or too many files')
        if len(entries) != len({z.filename.casefold() for z in entries}):
            raise Rejected('duplicate/case-colliding entries')
        total = 0
        for entry in entries:
            name = safe_name(entry.filename)
            if entry.flag_bits & 1:
                raise Rejected('password encrypted ZIP member')
            if entry.file_size > MAX_ENTRY_SIZE:
                raise Rejected('oversize member')
            mode = entry.external_attr >> 16
            if stat.S_IFMT(mode) == stat.S_IFLNK:
                raise Rejected('archive symlink member')
            data = archive.read(entry)
            try:
                data.decode('utf-8', errors='strict')
            except UnicodeError as exc:
                raise Rejected('non-UTF8 original source') from exc
            if any(pattern.search(data) for pattern in SECRET_RE):
                raise Rejected('potential credential in original source')
            total += len(data)
            if total > 10 * 1024 * 1024:
                raise Rejected('total uncompressed size too large')
            out[name] = data
    return out


def scan(folder: Path) -> dict:
    found = {k: [] for k in EXPECTED_ZIP_SHA256}
    all_zips = sorted(x for x in folder.rglob('*.zip') if x.is_file() and not x.is_symlink())
    for path in all_zips:
        if path.stat().st_size > MAX_ARCHIVE_SIZE:
            continue
        digest = sha256(path.read_bytes())
        for packet, expected in EXPECTED_ZIP_SHA256.items():
            if digest == expected:
                try:
                    members = examine(path, packet)
                    found[packet].append({'path': str(path), 'status': 'ORIGINAL_SOURCE_ZIP_VERIFIED', 'files': len(members)})
                except (Rejected, OSError, zipfile.BadZipFile) as exc:
                    found[packet].append({'path': str(path), 'status': 'ZIP_CONTENT_BLOCKED', 'reason': str(exc)})
    return {'game_id': GAME, 'work_id': WORK, 'keyless_source_zips': found,
            'found_packets': sum(bool(v) for v in found.values()), 'total_packets': len(found),
            'note': 'LOCAL DISCOVERY ONLY. Not a GitHub PUBLIC_SOURCE delivery or Studio QA.'}


def stage(path: Path, packet: str, output: Path) -> dict:
    members = examine(path, packet)
    if output.exists():
        raise Rejected('target already exists; never overwrite')
    # The output is a NEW isolated directory; do not stage into the live PC game tree.
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in members.items():
        if name == 'BUILD_MANIFEST.json':
            name = 'docs/LEGACY_BUILD_MANIFEST.json'
            if name in members:
                raise Rejected('legacy manifest path collision')
        dest = output.joinpath(*PurePosixPath(name).parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
    return {'status': 'STAGED_UNPUBLISHED_SOURCE', 'old_packet_id': packet,
            'output': str(output), 'files': len(members),
            'next': 'manual review + canonical p0d_public_pack.py build/verify + isolated branch + full remote fixed-SHA readback'}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    a = sub.add_parser('scan', help='find exact original unencrypted ZIPs read-only')
    a.add_argument('folder', type=Path)
    b = sub.add_parser('stage', help='extract exact approved ZIP to a new isolated folder only')
    b.add_argument('--zip', type=Path, required=True)
    b.add_argument('--packet', required=True)
    b.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == 'scan':
            if not args.folder.is_dir():
                raise Rejected('scan directory not found')
            result = scan(args.folder)
        else:
            result = stage(args.zip, args.packet, args.output)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (Rejected, OSError, zipfile.BadZipFile) as exc:
        print('KEYLESS_RECOVERY_BLOCKED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
