"""Fail closed against source corruption, extra hidden scripts and key edits."""
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_manifest import verify

class SourceLockTests(unittest.TestCase):
    def test_original_and_mutations(self):
        m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text("utf-8"))
        with TemporaryDirectory() as dir:
            target=Path(dir)
            for x in m["files"]:
                p=target/x["path"];p.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/x["path"],p)
            self.assertEqual(verify(target,m),len(m["files"]))
            def mutate(fn):
                copied=json.loads(json.dumps(m))
                fn(copied)
                with self.assertRaises(ValueError):verify(target,copied)
            mutate(lambda m:m.update({"game_id":"NOT_THIS_GAME"}))
            mutate(lambda m:m["files"][0].update({"size":m["files"][0]["size"]+1}))
            mutate(lambda m:m["files"][0].update({"sha256":"0"*64}))
            mutate(lambda m:m["files"][0].update({"path":"../x"}))
            mutate(lambda m:m.update({"public_source_allowed":False}))
            (target/"hidden.lua").write_text("print('unexpected')",encoding="utf-8")
            with self.assertRaises(ValueError):verify(target,m)
if __name__=="__main__":
    unittest.main()
