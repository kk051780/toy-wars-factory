"""Manifest negative controls deliberately tamper real source copies in temporary folders."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json, shutil, sys, unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_manifest import verify

class WF13ManifestTests(unittest.TestCase):
    def test_mutations(self):
        source_m = json.loads((ROOT / "BUILD_MANIFEST.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            for record in source_m["files"]:
                target = d / record["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / record["path"], target)
            (d / "BUILD_MANIFEST.json").write_text(
                json.dumps(source_m, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(verify(d), len(source_m["files"]))
            changed = json.loads(json.dumps(source_m))
            changed["files"][0]["sha256"] = "0"*64
            with self.assertRaises(ValueError):
                verify(d, changed)
            changed = json.loads(json.dumps(source_m))
            changed["files"][0]["size"] += 1
            with self.assertRaises(ValueError):
                verify(d, changed)
            changed = json.loads(json.dumps(source_m))
            changed["files"][0]["path"] = "../escape.txt"
            with self.assertRaises(ValueError):
                verify(d, changed)
            changed = json.loads(json.dumps(source_m))
            changed["game_id"] = "OTHER_GAME"
            with self.assertRaises(ValueError):
                verify(d, changed)
            (d / "evil_hidden.luau").write_text("print('surprise')", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify(d)

if __name__ == "__main__":
    unittest.main()
