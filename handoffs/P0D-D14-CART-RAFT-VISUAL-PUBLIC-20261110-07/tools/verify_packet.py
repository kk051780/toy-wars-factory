"""Read-only ZIP manifest/entry validator; does not extract archive files."""
from __future__ import annotations
import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import PurePosixPath

MAX_FILES = 64
MAX_ZIP_BYTES = 2_000_000
MAX_FILE_BYTES = 512_000


class BadPacket(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_bytes(blob: bytes) -> dict:
    if not blob or len(blob) > MAX_ZIP_BYTES:
        raise BadPacket('ZIP_SIZE')
    try:
        with zipfile.ZipFile(io.BytesIO(blob), 'r') as z:
            info = z.infolist()
            if not info or len(info) > MAX_FILES:
                raise BadPacket('ENTRY_COUNT')
            names = set()
            content = {}
            for f in info:
                n = f.filename
                if not n or not isinstance(n, str) or n.startswith(('/', '\\')) or ':' in n or '\\' in n:
                    raise BadPacket('UNSAFE_PATH')
                if any(p in ('', '.', '..') for p in n.split('/')) or f.is_dir():
                    raise BadPacket('UNSAFE_PATH')
                lower = n.casefold()
                if lower in names:
                    raise BadPacket('DUPLICATE_PATH')
                names.add(lower)
                if f.flag_bits & 1:
                    raise BadPacket('ENCRYPTED_ENTRY')
                mode = (f.external_attr >> 16) & 0xFFFF
                if mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                    raise BadPacket('SPECIAL_FILE')
                if f.file_size > MAX_FILE_BYTES:
                    raise BadPacket('FILE_EXPANSION')
                data = z.read(f)
                if len(data) != f.file_size:
                    raise BadPacket('SIZE_MISMATCH')
                content[n] = data
            if 'BUILD_MANIFEST.json' not in content:
                raise BadPacket('NO_MANIFEST')
            try:
                m = json.loads(content['BUILD_MANIFEST.json'], object_pairs_hook=unique_pairs)
            except Exception as e:
                raise BadPacket('BAD_MANIFEST') from e
            if not isinstance(m, dict) or m.get('packet_id') != 'P0D-D14-CART-RAFT-VISUAL-20261110-02':
                raise BadPacket('MANIFEST_ID')
            expected=m.get('entries')
            if not isinstance(expected, dict) or set(expected) != set(content)-{'BUILD_MANIFEST.json'}:
                raise BadPacket('MANIFEST_ENTRIES')
            for name, metadata in expected.items():
                if not isinstance(metadata, dict) or set(metadata) != {'bytes', 'sha256'}:
                    raise BadPacket('MANIFEST_SCHEMA')
                if type(metadata['bytes']) is not int or metadata['bytes'] != len(content[name]) or sha(content[name]) != metadata['sha256']:
                    raise BadPacket('DIGEST_MISMATCH')
            return m
    except (zipfile.BadZipFile, RuntimeError, OSError, EOFError, KeyError, ValueError, UnicodeError) as exc:
        if isinstance(exc, BadPacket):
            raise
        raise BadPacket('CORRUPT_ZIP') from exc


def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d:
            raise BadPacket('DUPLICATE_JSON_KEY')
        d[k]=v
    return d
