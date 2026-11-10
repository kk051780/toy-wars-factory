import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import p0d_public_pack as P


class PublicHandoffTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp())
        self.root = self.work / 'packet'
        self.root.mkdir()
        (self.root / 'luau').mkdir()
        (self.root / 'luau' / 'Core.luau').write_text('return { ok = true }\n', encoding='utf-8')
        self.packet = 'P0D-D07-TEST-V1'

    def tearDown(self):
        shutil.rmtree(self.work)

    def manifest(self):
        doc = P.build(self.root, self.packet)
        (self.root / P.MANIFEST).write_bytes(P.serialized(doc))
        return doc

    def assert_reject(self):
        with self.assertRaises(P.PackError):
            P.gather(self.root)

    def test_01_build_verify(self):
        self.manifest()
        self.assertEqual(P.verify(self.root, self.packet)['file_count'], 1)

    def test_02_deterministic_manifest(self):
        self.manifest()
        first = (self.root / P.MANIFEST).read_bytes()
        self.manifest()
        self.assertEqual(first, (self.root / P.MANIFEST).read_bytes())

    def test_03_file_changes_block(self):
        self.manifest()
        (self.root / 'luau' / 'Core.luau').write_text('different')
        with self.assertRaises(P.PackError): P.verify(self.root, self.packet)

    def test_04_extra_file_blocks(self):
        self.manifest()
        (self.root / 'README.md').write_text('new')
        with self.assertRaises(P.PackError): P.verify(self.root, self.packet)

    def test_05_removed_file_blocks(self):
        self.manifest()
        (self.root / 'luau' / 'Core.luau').unlink()
        with self.assertRaises(P.PackError): P.verify(self.root, self.packet)

    def test_06_packet_mismatch_blocks(self):
        self.manifest()
        with self.assertRaises(P.PackError): P.verify(self.root, 'DIFFERENT-ID')

    def test_07_noncanonical_json_blocks(self):
        self.manifest()
        f = self.root / P.MANIFEST
        f.write_text(f.read_text() + ' ', encoding='utf-8')
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_08_false_public_flag_blocks(self):
        d = self.manifest()
        d['public_source_allowed'] = False
        (self.root / P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_09_other_game_blocks(self):
        d = self.manifest()
        d['game_id'] = 'OTHER'
        (self.root / P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_10_other_work_blocks(self):
        d = self.manifest()
        d['work_id'] = 'other'
        (self.root / P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_11_duplicate_manifest_key(self):
        self.manifest()
        (self.root / P.MANIFEST).write_text('{"format": 1, "format": 2}')
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_12_boolean_size_rejected(self):
        d = self.manifest();d['files'][0]['size'] = True
        (self.root / P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_13_wrong_sha_rejected(self):
        d = self.manifest();d['files'][0]['sha256'] = 'f' * 64
        (self.root / P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_14_bad_file_schema_rejected(self):
        d = self.manifest();d['files'][0]['surprise'] = 3
        (self.root / P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError): P.verify(self.root)

    def test_15_secret_pem_rejected(self):
        (self.root / 'README.md').write_text('-----BEGIN OPENSSH' + ' PRIVATE KEY-----')
        self.assert_reject()

    def test_16_secret_github_token_rejected(self):
        (self.root / 'README.md').write_text('ghp_' + 'a'*30)
        self.assert_reject()

    def test_17_secret_finegrained_rejected(self):
        (self.root / 'README.md').write_text('github_pat_' + 'a'*40)
        self.assert_reject()

    def test_18_secret_openai_rejected(self):
        (self.root / 'README.md').write_text('sk-proj-' + 'a'*40)
        self.assert_reject()

    def test_19_aws_secret_rejected(self):
        (self.root / 'README.md').write_text('AKIA'+'A'*16)
        self.assert_reject()

    def test_20_bad_file_extension(self):
        (self.root / 'dump.zip').write_text('not allowed')
        self.assert_reject()

    def test_21_invalid_utf8(self):
        (self.root / 'bad.py').write_bytes(b'\xff\xfe')
        self.assert_reject()

    def test_22_path_symlink(self):
        target = self.root / 'luau' / 'Core.luau'
        try:
            (self.root / 'link.py').symlink_to(target)
        except (OSError, NotImplementedError): self.skipTest('symlink unavailable')
        self.assert_reject()

    def test_23_directory_symlink(self):
        try:
            (self.root / 'newdir').symlink_to(self.root / 'luau', target_is_directory=True)
        except (OSError, NotImplementedError): self.skipTest('symlink unavailable')
        self.assert_reject()

    def test_24_casefold_duplicate(self):
        (self.root / 'A.md').write_text('a')
        (self.root / 'a.md').write_text('b')
        if len(list(self.root.glob('*md'))) < 2:self.skipTest('case insensitive filesystem')
        self.assert_reject()

    def test_25_oversize_file(self):
        (self.root / 'README.md').write_bytes(b'a'*(P.MAX_FILE_BYTES+1))
        self.assert_reject()

    def test_26_empty_pack(self):
        (self.root / 'luau' / 'Core.luau').unlink()
        self.assert_reject()

    def test_27_block_traversal(self):
        for text in ('../secret.py', '/absolute.py', 'a\\b.py', 'foo//bar.py', 'foo/./bar.py', '.env', 'C:/temp.py'):
            with self.subTest(text=text), self.assertRaises(P.PackError):P.safe_relative(text)

    def test_28_bad_packet(self):
        for pkt in ('', 'abc', 'space bad', '../../src', 'a'*200):
            with self.subTest(pkt=pkt), self.assertRaises(P.PackError):P.build(self.root, pkt)

    def test_29_nested_valid_file(self):
        (self.root / 'luau' / 'Module.lua').write_text('return {}')
        self.manifest()
        self.assertEqual(P.verify(self.root, self.packet)['file_count'], 2)

    def test_30_manifest_symlink(self):
        target = self.root / 'README.md'
        target.write_text('{}')
        try:
            (self.root / P.MANIFEST).symlink_to(target)
        except (OSError, NotImplementedError): self.skipTest('symlink unavailable')
        with self.assertRaises(P.PackError):P.verify(self.root)

    def test_31_duplicate_json_in_manifest(self):
        self.manifest()
        txt=(self.root/P.MANIFEST).read_text()
        txt=txt.replace('"game_id": "TRAP_RAIDERS",', '"game_id": "TRAP_RAIDERS", "game_id": "TRAP_RAIDERS",')
        (self.root/P.MANIFEST).write_text(txt)
        with self.assertRaises(P.PackError):P.verify(self.root)

    def test_32_extra_field_in_manifest(self):
        d=self.manifest();d['private_key']='x'
        (self.root/P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError):P.verify(self.root)

    def test_33_tamper_file_size(self):
        d=self.manifest();d['files'][0]['size'] += 1
        (self.root/P.MANIFEST).write_bytes(P.serialized(d))
        with self.assertRaises(P.PackError):P.verify(self.root)

    def test_34_file_name_secret(self):
        (self.root/'credentials.json').write_text('{}')
        self.assert_reject()

    def test_35_build_cli_and_verify_cli(self):
        self.assertEqual(P.main(['build','--root',str(self.root),'--packet-id',self.packet]),0)
        self.assertEqual(P.main(['verify','--root',str(self.root),'--packet-id',self.packet]),0)

if __name__=='__main__':unittest.main()
