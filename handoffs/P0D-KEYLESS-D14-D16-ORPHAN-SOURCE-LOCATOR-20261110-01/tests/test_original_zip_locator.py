import io
import pathlib
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import original_zip_locator as m

PACKET = next(iter(m.EXPECTED_ZIP_SHA256))


def archive(entries):
    s = io.BytesIO()
    with zipfile.ZipFile(s, 'w') as z:
        for k, v in entries.items():
            z.writestr(k, v)
    return s.getvalue()


class TestOriginalSourceLocator(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.dir = pathlib.Path(self.t.name)
        self.zip = self.dir / 'original.zip'
        self.raw = archive({'src/Test.luau': b'return {}\n', 'tests/test_a.py': b'assert 1\n'})
        self.zip.write_bytes(self.raw)
        self.old = m.EXPECTED_ZIP_SHA256[PACKET]
        m.EXPECTED_ZIP_SHA256[PACKET] = m.sha256(self.raw)
        self.addCleanup(lambda: m.EXPECTED_ZIP_SHA256.__setitem__(PACKET, self.old))

    def test_exact_sha_and_files(self):
        self.assertEqual(len(m.examine(self.zip, PACKET)), 2)

    def test_hash_mismatch(self):
        self.zip.write_bytes(self.raw + b'X')
        with self.assertRaisesRegex(m.Rejected, 'SHA mismatch'):
            m.examine(self.zip, PACKET)

    def test_unknown_packet(self):
        with self.assertRaisesRegex(m.Rejected, 'unknown'):
            m.examine(self.zip, 'WRONG')

    def test_absolute_path(self):
        with self.assertRaises(m.Rejected):
            m.safe_name('/tmp/a.py')

    def test_traversal(self):
        with self.assertRaises(m.Rejected):
            m.safe_name('../a.py')

    def test_windows_path(self):
        with self.assertRaises(m.Rejected):
            m.safe_name('C:\\evil.lua')

    def test_bad_extension(self):
        with self.assertRaises(m.Rejected):
            m.safe_name('bin.exe')

    def test_duplicate_case_entries(self):
        self.raw = archive({'A.py': b'x', 'a.py': b'y'})
        self.zip.write_bytes(self.raw)
        m.EXPECTED_ZIP_SHA256[PACKET] = m.sha256(self.raw)
        with self.assertRaisesRegex(m.Rejected, 'duplicate'):
            m.examine(self.zip, PACKET)

    def test_secret_block(self):
        raw = archive({'a.py': b'-----BEGIN RSA PRIVATE KEY-----'})
        self.zip.write_bytes(raw)
        m.EXPECTED_ZIP_SHA256[PACKET] = m.sha256(raw)
        with self.assertRaisesRegex(m.Rejected, 'credential'):
            m.examine(self.zip, PACKET)

    def test_scan_and_stage(self):
        result = m.scan(self.dir)
        self.assertEqual(result['found_packets'], 1)
        output = self.dir / 'clean'
        s = m.stage(self.zip, PACKET, output)
        self.assertEqual(s['status'], 'STAGED_UNPUBLISHED_SOURCE')
        self.assertEqual((output / 'src/Test.luau').read_bytes(), b'return {}\n')
        with self.assertRaisesRegex(m.Rejected, 'already exists'):
            m.stage(self.zip, PACKET, output)

    def test_manifest_rename(self):
        raw = archive({'BUILD_MANIFEST.json': b'{}', 'x.py': b'pass'})
        self.zip.write_bytes(raw)
        m.EXPECTED_ZIP_SHA256[PACKET] = m.sha256(raw)
        output = self.dir / 'out'
        m.stage(self.zip, PACKET, output)
        self.assertEqual((output / 'docs/LEGACY_BUILD_MANIFEST.json').read_bytes(), b'{}')


if __name__ == '__main__':
    unittest.main()
