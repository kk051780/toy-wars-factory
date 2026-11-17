import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

FILE=Path(__file__).resolve().parent/"compose_real32.py"
SPEC=importlib.util.spec_from_file_location("regen_compose",FILE)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class Real32Composer(unittest.TestCase):
    def fixture(self,base):
        root=Path(base); sources=root/"sources";sources.mkdir()
        nodes={}
        names=["EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SwarmCombat"]+["CANON_%02d"%i for i in range(29)]
        assert len(names)==31
        for name in names:
            if name=="EGGRUMBLE_LobbyCastleModesPreview":
                source=('local RunService=game:GetService("RunService")\n'
                  'local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))\n'
                  'if humanoid and humanoid:IsA("Humanoid") then\n'
                  'end\n')
            else: source="return {}\n"
            path=sources/(name+(".server.luau" if name.endswith("Preview") else ".luau"))
            path.write_text(source,encoding="utf-8")
            nodes[name]={"$path":"sources/"+path.name}
        project=root/"CURRENT31_REAL_SOURCE.project.json"
        project.write_text(json.dumps({"name":"real31","tree":{"ServerScriptService":nodes}},indent=2))
        return project
    def test_on32_off31_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            source=self.fixture(Path(td)/"input")
            on=Path(td)/"ON32"/"ON32.project.json"
            off=Path(td)/"OFF31"/"OFF31.project.json"
            a=MOD.compose(source,on)
            b=MOD.compose(source,off,True)
            self.assertEqual((a["count"],b["count"]),(32,31))
            self.assertTrue(a["old30_byte_exact"])
            self.assertTrue(b["inverse_original31"])
            model=json.loads(on.read_text())
            host=model["tree"]["ServerScriptService"]["EGGRUMBLE_LobbyCastleModesPreview"]
            patched=(on.parent/host["$path"]).read_text()
            self.assertIn("BATTLE_HP_REGEN",patched)
            self.assertIn("Humanoid.HealthChanged",patched)
            self.assertIn("lastDamageAt",patched)
            self.assertIn("session.rules.phase",patched)
            with self.assertRaisesRegex(ValueError,"RED_OVERWRITE"):
                MOD.compose(source,on)
    def test_unknown_host_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            source=self.fixture(Path(td)/"input")
            model=json.loads(source.read_text())
            item=model["tree"]["ServerScriptService"]["EGGRUMBLE_LobbyCastleModesPreview"]
            path=source.parent/item["$path"]
            path.write_text(path.read_text().replace(MOD.BIND_ANCHOR,"if false then"))
            with self.assertRaisesRegex(ValueError,"RED_HOST_ADAPTER"):
                MOD.compose(source,Path(td)/"ON32"/"ON32.project.json")
if __name__=="__main__":
    unittest.main()
