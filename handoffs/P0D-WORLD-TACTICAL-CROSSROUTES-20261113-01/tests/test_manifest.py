import hashlib, json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
M=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
class TestPinnedFiles(unittest.TestCase):
    def test_manifest_paths_and_hashes(self):
        self.assertEqual(M["status"],"KEYLESS_SOURCE_SHA256")
        self.assertEqual(len(M["files"]),4)
        self.assertEqual({x["path"] for x in M["files"]},{"README.md","world_contract.json","tests/test_world_contract.py","tests/test_manifest.py"})
        for f in M["files"]:
            self.assertFalse(f["path"].startswith("/") or ".." in pathlib.PurePosixPath(f["path"]).parts)
            body=(ROOT/f["path"]).read_bytes()
            self.assertEqual(len(body),f["bytes"],f["path"])
            self.assertEqual(hashlib.sha256(body).hexdigest(),f["sha256"],f["path"])
    def test_corrupted_readback_fails(self):
        f=M["files"][0]
        body=(ROOT/f["path"]).read_bytes()
        self.assertNotEqual(hashlib.sha256(body+b"forged").hexdigest(),f["sha256"])
    def test_no_forged_studio_pass(self):
        self.assertEqual(M["studio"],"NOT_TESTED")
        self.assertEqual(M["official_S1_rc_write"],False)
if __name__=="__main__": unittest.main()
