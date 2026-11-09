#!/usr/bin/env python3
"""Read-only, fail-closed verifier of this public-source handoff ZIP manifest."""
import hashlib
import io
import json
import re
import stat
import sys
import zipfile
from pathlib import Path


def verify_zip(path):
    raw = Path(path).read_bytes()
    if not raw or len(raw) > 2_000_000:
        raise ValueError('ZIP_SIZE')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if len(entries) > 20 or z.testzip() is not None:
            raise ValueError('ZIP_ENTRIES_OR_CRC')
        names = [i.filename for i in entries]
        if len(set(n.casefold() for n in names)) != len(names):
            raise ValueError('ZIP_DUPLICATE_NAME')
        for entry in entries:
            n = entry.filename
            mode = (entry.external_attr >> 16) & 0xFFFF
            if (n.startswith(('/', '\\')) or '\\' in n or ':' in n
                    or any(part in ('', '.', '..') for part in n.split('/'))
                    or entry.is_dir() or (mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG))):
                raise ValueError('ZIP_UNSAFE_PATH')
        manifest = json.loads(z.read('BUILD_MANIFEST.json'))
        if manifest.get('packet_id') != 'P0D-D11-V43A-ACCEPTANCE-GATE-20261110-01':
            raise ValueError('PACKET_MISMATCH')
        expected = {item['path']: item for item in manifest['files']}
        if set(names) != set(expected) | {'BUILD_MANIFEST.json'} or len(expected) != len(manifest['files']):
            raise ValueError('MANIFEST_MISMATCH')
        for n, info in expected.items():
            if not re.fullmatch('[0-9a-f]{64}', info['sha256']):
                raise ValueError('INVALID_SHA')
            blob = z.read(n)
            if len(blob) != info['size'] or hashlib.sha256(blob).hexdigest() != info['sha256']:
                raise ValueError('CONTENT_MISMATCH')
    return True


if __name__ == '__main__':
    try:
        verify_zip(sys.argv[1])
        print('ZIP_MANIFEST_SHA_PASS')
    except (ValueError, OSError, KeyError, IndexError, zipfile.BadZipFile) as exc:
        print('ZIP_MANIFEST_BLOCKED:' + type(exc).__name__)
        raise SystemExit(2)