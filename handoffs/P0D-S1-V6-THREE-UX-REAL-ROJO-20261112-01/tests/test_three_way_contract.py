import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"tools/check_three_ux_rojo.py"
spec=importlib.util.spec_from_file_location("three_ux",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
lock=json.loads((ROOT/"SELECTION_LOCK.json").read_text(encoding="utf8"))

class ThreeWayReview(unittest.TestCase):
    def test_exact_rc(self):
        self.assertEqual(lock["official_rc_base"],"1263a03701211a652b99b91d2339575dc8104eff")
    def test_all_21_scripts_and_project(self):
        self.assertEqual(len([r for r in lock["files"] if r["path"].endswith(".luau")]),21)
        self.assertEqual(len(lock["files"]),22)
    def test_only_three_overrides(self):
        changed={r["path"] for r in lock["files"] if r["git_blob"]!=r["original_git_blob"]}
        self.assertEqual(changed,{m.MAP_FILE,m.HELP_FILE,m.HUD_FILE})
    def test_original_server_game_unchanged(self):
        g=next(r for r in lock["files"] if r["path"]=="src/server/Game.server.luau")
        self.assertEqual(g["git_blob"],g["original_git_blob"])
    def test_guardian_hud_actual_vetted_sha(self):
        h=next(r for r in lock["files"] if r["path"]==m.HUD_FILE)
        self.assertEqual(h["git_blob"],"b3d3996c40c690e19007a36a847d5b10fc6a1522")
        self.assertEqual(h["bytes"],9017)
    def test_all_source_bytes_and_sha(self):
        for r in lock["files"]:
            with self.subTest(r["path"]):
                raw=(ROOT/"preview"/r["path"]).read_bytes()
                self.assertEqual(len(raw),r["bytes"])
                self.assertEqual(m.gitblob(raw),r["git_blob"])
    def test_real_script_topology(self):
        selected={r["path"]:(ROOT/"preview"/r["path"]).read_bytes() for r in lock["files"]}
        mapped=m.expected_script_paths(selected)
        self.assertEqual(len(mapped),21)
        self.assertEqual(sum(v[0]=="Script" for v in mapped.values()),1)
        self.assertEqual(sum(v[0]=="LocalScript" for v in mapped.values()),3)
        self.assertEqual(sum(v[0]=="ModuleScript" for v in mapped.values()),17)
    def test_client_buttons_exact(self):
        s=(ROOT/"preview/src/client/HUD.client.luau").read_text()
        self.assertIn("UDim2.new(1, -140, 1, -110)",s)
        self.assertNotIn("UDim2.new(.02, 0, 1, -16)",s)
        self.assertIn('action("PLACE_TRAP", nil)',s)
    def test_japanese_and_guardian_help_present(self):
        b=(ROOT/"preview/src/server/MapBuilder.luau").read_text()
        c=(ROOT/"preview/src/shared/FirstMinuteModel.luau").read_text()
        self.assertIn("卵を届ける",b)
        self.assertIn("20秒",c)
    def test_unpublished_flags(self):
        self.assertIs(lock["studio_tested"],False)
        self.assertIs(lock["roblox_published"],False)
    def test_stable_git_blob(self):
        self.assertEqual(m.gitblob(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")
    def test_source_override_input_refs(self):
        self.assertEqual(lock["mobile_hud_input_commit"],m.HUD_INPUT)
        self.assertEqual(lock["guardian_help_input_commit"],m.HELP_INPUT)
        self.assertEqual(lock["japanese_map_input_commit"],m.MAP_INPUT)

if __name__=="__main__":
    unittest.main()
