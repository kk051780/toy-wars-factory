"""Fail-closed mutation checks on exact real source files in temporary isolation."""
from pathlib import Path
import json,sys,shutil,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_manifest import verify

class SourceManifestMutations(unittest.TestCase):
    def test_true_files_and_corruptions(self):
        source=json.loads((ROOT/"BUILD_MANIFEST.json").read_text("utf-8"))
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            for rec in source["files"]:
                target=directory/rec["path"]
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/rec["path"],target)
            self.assertEqual(verify(directory,source),len(source["files"]))
            def tamper(change):
                wrong=json.loads(json.dumps(source))
                change(wrong)
                with self.assertRaises(ValueError):
                    verify(directory,wrong)
            tamper(lambda m:m.update({"game_id":"OTHER"}))
            tamper(lambda m:m.update({"public_source_allowed":False}))
            tamper(lambda m:m["files"][0].update({"sha256":"0"*64}))
            tamper(lambda m:m["files"][0].update({"size":m["files"][0]["size"]+1}))
            tamper(lambda m:m["files"][0].update({"path":"../escape"}))
            tamper(lambda m:m.update({"packet_id":"WRONG"}))
            (directory/"unexpected-client.lua").write_text("print('danger')",encoding="utf-8")
            with self.assertRaises(ValueError):verify(directory,source)
if __name__=="__main__":
    unittest.main()
