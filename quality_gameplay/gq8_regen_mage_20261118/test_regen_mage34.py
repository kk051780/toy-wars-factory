import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("regen_mage34",ROOT/"compose_regen_mage34.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Reuse the source-author runtime composer, not a reimplementation of its policy.
REGENDIR=ROOT.parents[1]/"handoffs"/"EGGRUMBLE-HP-REGEN-20261118"
regen_spec=importlib.util.spec_from_file_location("regen_owner",REGENDIR/"compose_regen32.py")
regen=importlib.util.module_from_spec(regen_spec)
regen_spec.loader.exec_module(regen)

class Crosslane(unittest.TestCase):
    def make_base(self,root):
        root.mkdir(parents=True)
        names=["EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SevenRoleCombat",
               "EGGRUMBLE_SwarmCombat"]+["Original%02d"%i for i in range(28)]
        server={}
        for name in names:
            source=("local SevenRoleCombat=require(script.Parent:WaitForChild(\"EGGRUMBLE_SevenRoleCombat\"))\n"
                    "local function run(session,p,role)\n"
                    " SevenRoleCombat.equip(session,p,role)\n"
                    " task.delay(.8,function()\n"
                    "  SevenRoleCombat.equip(session,p,role)\n"
                    " end)\nend\n") if name=="EGGRUMBLE_LobbyCastleModesPreview" else "return {}\n"
            file=root/(name+(".server.luau" if name=="EGGRUMBLE_LobbyCastleModesPreview" else ".luau"))
            file.write_text(source)
            server[name]={"$path":file.name}
        project=root/"ORIGINAL31.project.json"
        project.write_text(json.dumps({"name":"GenuineShape31","tree":{"ServerScriptService":server}}))
        return project
    def setup(self,top):
        original=self.make_base(top/"input")
        runtime=top/"regen33"/"REGEN33.project.json"
        regen.compose(original,runtime)
        source=top/"mage"/"EGGRUMBLE_MageRevive.luau"
        source.parent.mkdir()
        source.write_text("local Rescue={}\nreturn Rescue\n")
        return original,runtime,source
    def test_34_and_unmodified_authors(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            original,regen33,mage=self.setup(root)
            combined=root/"combined"/"ON34.project.json"
            mod.compose(original,regen33,mage,combined,mod.git_blob(mage))
            _,base=mod.files(original)
            _,old=mod.files(regen33)
            _,new=mod.files(combined)
            self.assertEqual((len(base),len(old),len(new)),(31,33,34))
            self.assertEqual(set(new)-set(old),{mod.MAGE})
            host=new[mod.HOST].read_text()
            self.assertEqual(host.count(mod.REGEN_ATTACH),2)
            self.assertEqual(host.count(mod.MAGE_ATTACH),2)
            self.assertEqual(host.count(mod.MAGE_REQUIRE),1)
            self.assertEqual(host.count("SevenRoleCombat.equip(session,p,role)"),2)
            for k in old:
                if k!=mod.HOST:
                    self.assertEqual(old[k].read_bytes(),new[k].read_bytes())
            for k in base:
                if k!=mod.HOST:
                    self.assertEqual(base[k].read_bytes(),new[k].read_bytes())
            self.assertTrue(json.loads(combined.with_suffix(".receipt.json").read_text())["host_sole_authority"])
            with self.assertRaisesRegex(ValueError,"RED_OUTPUT_OVERWRITE"):
                mod.compose(original,regen33,mage,combined,mod.git_blob(mage))
    def test_mutated_mage_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);original,regen33,mage=self.setup(root)
            with self.assertRaisesRegex(ValueError,"RED_MAGE_SOURCE_BLOB_CHANGED"):
                mod.compose(original,regen33,mage,root/"output"/"COMBO34.project.json")
    def test_existing_unapproved_host_change_is_red(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);original,regen33,mage=self.setup(root)
            _,r=mod.files(regen33)
            old=r[mod.HOST].read_text()
            r[mod.HOST].write_text(old+"\n-- suspicious independent HP authority\n")
            with self.assertRaisesRegex(ValueError,"RED_REGEN_HOST_UNAPPROVED_EDIT"):
                mod.compose(original,regen33,mage,root/"output"/"COMBO34.project.json",mod.git_blob(mage))
    def test_regen_and_mage_downed_contract(self):
        natural=(REGENDIR/"EGGRUMBLE_NaturalRegen.luau").read_text()
        self.assertIn('p:GetAttribute("EGGRUMBLE_Downed")==true',natural)
        self.assertIn("Policy.regenDelta",natural)
        self.assertIn("HealthChanged:Connect",natural)
        self.assertIn("RunService.Heartbeat:Connect",natural)
if __name__=="__main__":
    unittest.main()
