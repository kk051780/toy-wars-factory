"""Independent pack safety/size/SHA checker; uses Python stdlib only."""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'BUILD_MANIFEST.json'
NAMES = {'format', 'game_id', 'work_id', 'packet_id', 'public_source_allowed', 'files'}


def check():
    x = json.loads(MANIFEST.read_text(encoding='utf8'))
    assert set(x) == NAMES
    assert x['format'] == 'P0D_PUBLIC_SOURCE_V1'
    assert x['game_id'] == 'TRAP_RAIDERS' and x['work_id'] == 'p0d-siege-v19'
    assert x['public_source_allowed'] is True
    listed = [entry['path'] for entry in x['files']]
    assert len(listed) == len(set(listed)) and listed == sorted(listed)
    actual = []
    for fp in ROOT.rglob('*'):
        if fp.is_symlink():
            raise AssertionError(f'symlink: {fp}')
        if fp.is_file() and '__pycache__' not in fp.parts:
            actual.append(fp.relative_to(ROOT).as_posix())
    assert sorted(actual) == sorted(listed + ['BUILD_MANIFEST.json']), (actual, listed)
    for entry in x['files']:
        fp = (ROOT / entry['path']).resolve()
        assert fp.is_relative_to(ROOT.resolve())
        b = fp.read_bytes()
        assert len(b) == entry['size']
        assert hashlib.sha256(b).hexdigest() == entry['sha256']
    return {'source_files': len(listed), 'total_files': len(actual),
            'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}


if __name__ == '__main__':
    print(check())
