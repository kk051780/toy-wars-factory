"""Strict source manifest positive and fail-closed corrupt/undeclared negative tests."""
from pathlib import Path
import json,shutil,tempfile,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_manifest import verify
class ManifestTests(unittest.TestCase):
 def test_actual_source_and_six_mutations(self):
  m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text("utf-8"))
  with tempfile.TemporaryDirectory() as t:
   d=Path(t)
   for row in m["files"]:
    dest=d/row["path"]
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/row["path"],dest)
   (d/"BUILD_MANIFEST.json").write_text(json.dumps(m),encoding="utf-8")
   self.assertEqual(verify(d),len(m["files"]))
   def bad(change):
    corrupt=json.loads(json.dumps(m))
    change(corrupt)
    (d/"BUILD_MANIFEST.json").write_text(json.dumps(corrupt),encoding="utf-8")
    with self.assertRaises(ValueError):verify(d)
   bad(lambda d:d.update({"game_id":"OTHER"}))
   bad(lambda d:d.update({"public_source_allowed":False}))
   bad(lambda d:d["files"][0].update({"sha256":"0"*64}))
   bad(lambda d:d["files"][0].update({"size":d["files"][0]["size"]+1}))
   bad(lambda d:d["files"][0].update({"path":"../unsafe"}))
   bad(lambda d:d.update({"packet_id":"OTHER"}))
   (d/"BUILD_MANIFEST.json").write_text(json.dumps(m),encoding="utf-8")
   (d/"hidden.client.lua").write_text("print('unauthorized')",encoding="utf-8")
   with self.assertRaises(ValueError):verify(d)
if __name__=="__main__":unittest.main()
