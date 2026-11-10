#!/usr/bin/env python3
"""Read-only manifest and ZIP integrity verification for Chat-to-Codex handoff."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import stat
import zipfile

MAX_ZIP_BYTES = 10_000_000
MAX_FILES = 256
MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_UNCOMPRESSED = 20_000_000


def verify_bytes(contents):
    if not isinstance(contents, bytes) or len(contents) > MAX_ZIP_BYTES:
        raise ValueError('ZIP_TOO_LARGE')
    try:
        archive = zipfile.ZipFile(io.BytesIO(contents))
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError('ZIP_INVALID') from exc
    with archive as z:
        infos = z.infolist()
        names = [entry.filename for entry in infos]
        if not 1 <= len(names) <= MAX_FILES:
            raise ValueError('ZIP_ENTRY_COUNT')
        if len(names) != len(set(names)) or len(names) != len({x.casefold() for x in names}):
            raise ValueError('ZIP_DUPLICATE_PATH')
        total_uncompressed = 0
        for entry in infos:
            name = entry.filename
            total_uncompressed += entry.file_size
            mode = (entry.external_attr >> 16) & 0xffff
            kind = stat.S_IFMT(mode)
            if kind not in (0, stat.S_IFREG):
                raise ValueError("ZIP_SPECIAL_FILE")
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError("ZIP_UNPACKED_TOO_LARGE")
            if (not name or name.startswith(('/', '\\')) or '\\' in name
                    or ':' in name or any(v in ('.', '..', '') for v in name.split('/'))
                    or entry.is_dir() or entry.file_size > MAX_FILE_BYTES):
                raise ValueError('ZIP_UNSAFE_ENTRY')
        if 'BUILD_MANIFEST.json' not in names:
            raise ValueError('MANIFEST_MISSING')
        if z.testzip() is not None:
            raise ValueError('ZIP_CORRUPT')
        manifest = json.loads(z.read('BUILD_MANIFEST.json'))
        if manifest.get('schema_version') != 1 or manifest.get('classification') != 'REFERENCE_ONLY':
            raise ValueError('INVALID_MANIFEST_HEADER')
        files = manifest.get('files')
        if manifest.get('packet_id') != 'P0D-D07-GOROGAN-RIG-NAV-DAMAGE-20261110-03':
            raise ValueError('WRONG_PACKET_ID')
        if not isinstance(files, dict) or set(files) != (set(names) - {'BUILD_MANIFEST.json'}):
            raise ValueError('MANIFEST_FILES_MISMATCH')
        for name, spec in files.items():
            data = z.read(name)
            if spec.get('sha256') != hashlib.sha256(data).hexdigest() or spec.get('size_bytes') != len(data):
                raise ValueError('SHA_MISMATCH: '+name)
        return {
            'ok': True, 'file_count': len(files),
            'zip_sha256': hashlib.sha256(contents).hexdigest(),
            'packet_id': manifest.get('packet_id'), 'studio_verified': False,
        }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('zip_path', type=Path)
    args = p.parse_args()
    try:
        print(json.dumps(verify_bytes(args.zip_path.read_bytes()), sort_keys=True))
    except Exception as exc:
        print('VERIFY_FAILED: '+str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
