import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_candidates as v


def fixture(packet='P0D-TEST-CLEANROOM-20261111', payload=b'return {}\n'):
    doc = {'format': 'P0D_PUBLIC_SOURCE_V1', 'game_id': 'TRAP_RAIDERS',
           'work_id': 'p0d-siege-v19', 'packet_id': packet,
           'public_source_allowed': True,
           'files': [{'path': 'luau/main.luau', 'size': len(payload),
                      'sha256': hashlib.sha256(payload).hexdigest()}]}
    encoded = (json.dumps(doc) + '\n').encode()
    e = {'packet_id': packet, 'legacy_old_packet_id': 'P0D-OLD-TEST-20261111',
         'commit_sha': 'a' * 40, 'manifest_sha256': v.sha256(encoded)}
    f = {f'handoffs/{packet}/BUILD_MANIFEST.json': encoded,
         f'handoffs/{packet}/luau/main.luau': payload}
    return e, f


class Unit(unittest.TestCase):
    def test_registry_five(self):
        self.assertEqual(len(v.load_registry()), 5)

    def test_registry_kind(self):
        self.assertEqual(len({x['legacy_old_packet_id'] for x in v.load_registry()}), 5)

    def test_valid_source(self):
        e, files = fixture()
        self.assertEqual(v.validate_bytes(e, files)['files_verified'], 1)

    def test_not_original(self):
        e, files = fixture()
        self.assertFalse(v.validate_bytes(e, files)['original_source_migrated'])

    def test_manifest_mutation_blocked(self):
        e, files = fixture()
        files[next(x for x in files if x.endswith('BUILD_MANIFEST.json'))] += b'\n'
        with self.assertRaisesRegex(v.Blocked, 'pinned manifest'):
            v.validate_bytes(e, files)

    def test_source_mutation_blocked(self):
        e, files = fixture()
        files[next(x for x in files if x.endswith('main.luau'))] = b'not original'
        with self.assertRaisesRegex(v.Blocked, 'source SHA'):
            v.validate_bytes(e, files)

    def test_missing_file_blocked(self):
        e, files = fixture()
        files.pop(next(x for x in files if x.endswith('main.luau')))
        with self.assertRaisesRegex(v.Blocked, 'missing or unexpected'):
            v.validate_bytes(e, files)

    def test_extra_file_blocked(self):
        e, files = fixture()
        files[f'handoffs/{e["packet_id"]}/extra.txt'] = b'bad'
        with self.assertRaisesRegex(v.Blocked, 'missing or unexpected'):
            v.validate_bytes(e, files)

    def test_unsafe_absolute(self):
        with self.assertRaises(v.Blocked): v.safe_path('/abs/x.py')

    def test_unsafe_windows(self):
        with self.assertRaises(v.Blocked): v.safe_path('C:\\run\\p.py')

    def test_unsafe_traversal(self):
        with self.assertRaises(v.Blocked): v.safe_path('src/../bad.py')

    def test_unsafe_hidden(self):
        with self.assertRaises(v.Blocked): v.safe_path('.git/config.json')

    def test_unsafe_filetype(self):
        with self.assertRaises(v.Blocked): v.safe_path('binary.exe')

    def test_bad_public_flag(self):
        e, files = fixture()
        m = json.loads(next(y for x, y in files.items() if x.endswith('BUILD_MANIFEST.json')))
        m['public_source_allowed'] = False
        with self.assertRaisesRegex(v.Blocked, 'manifest authority'):
            v.check_manifest(e['packet_id'], json.dumps(m).encode())

    def test_bad_size_type(self):
        e, files = fixture()
        m = json.loads(next(y for x, y in files.items() if x.endswith('BUILD_MANIFEST.json')))
        m['files'][0]['size'] = True
        with self.assertRaisesRegex(v.Blocked, 'bad manifest size'):
            v.check_manifest(e['packet_id'], json.dumps(m).encode())

    def test_bad_duplicate_case(self):
        e, files = fixture()
        m = json.loads(next(y for x, y in files.items() if x.endswith('BUILD_MANIFEST.json')))
        m['files'].append({**m['files'][0], 'path': 'Luau/MAIN.LUAU'})
        with self.assertRaisesRegex(v.Blocked, 'duplicate'):
            v.check_manifest(e['packet_id'], json.dumps(m).encode())

    def test_output_exists(self):
        with tempfile.TemporaryDirectory() as p:
            e, _ = fixture()
            with self.assertRaisesRegex(v.Blocked, 'destination exists'):
                v.receive(Path(p), [e])

    def test_cleanup_readonly(self):
        with tempfile.TemporaryDirectory() as p:
            with v.private_temp(Path(p)) as q:
                f = q / 'read_only.pack'
                f.write_text('test')
                f.chmod(stat.S_IREAD)
            self.assertFalse(q.exists())

    def test_end_to_end_local_git(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); source = base / 'source'; source.mkdir()
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'config', 'user.email', 'no@example.invalid'], check=True)
            subprocess.run(['git', '-C', str(source), 'config', 'user.name', 'Test'], check=True)
            e, files = fixture()
            for name, content in files.items():
                path = source / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
            subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(source), 'commit', '-qm', 'candidate'], check=True)
            e['commit_sha'] = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD']).decode().strip()
            previous = v.REPO
            v.REPO = str(source)
            try:
                out = base / 'out'
                receipt = v.receive(out, [e])
                self.assertEqual(receipt['candidate_packets_verified'], 1)
                self.assertEqual(receipt['original_legacy_packets_migrated_by_this_tool'], 0)
                self.assertEqual(receipt['roblox_studio_qa'], 'NOT_TESTED')
                self.assertEqual((out / 'packs' / e['packet_id'] / 'luau/main.luau').read_bytes(), b'return {}\n')
                with self.assertRaises(v.Blocked): v.receive(out, [e])
            finally:
                v.REPO = previous


if __name__ == '__main__':
    unittest.main()
