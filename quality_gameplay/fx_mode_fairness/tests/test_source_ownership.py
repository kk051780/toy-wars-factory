import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parents[1]
PARENT=HERE.parent.parent/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
PROJECT=HERE/"EGGRUMBLE_V3_FX_FAIR_22_STUDIO.project.json"
def entries(node, root):
    for name, child in node.items():
        if name.startswith("$") or not isinstance(child, dict): continue
        if "$path" in child:
            yield name,(root/child["$path"]).resolve(strict=True)
        else:yield from entries(child,root)
class TestNonOverlap(unittest.TestCase):
    def test_22_exact_project(self):
        values=dict(entries(json.loads(PROJECT.read_text())["tree"],HERE))
        self.assertEqual(len(values),22)
        orig=dict(entries(json.loads((PARENT/"EGGRUMBLE_V3_STUDIO.project.json").read_text())["tree"],PARENT))
        self.assertEqual(len(orig),21)
        self.assertEqual(set(values),set(orig)|{"EGGRUMBLE_FXModeFairQuota"})
        for name,path in orig.items():
            if name!="EGGRUMBLE_SkillFX": self.assertEqual(values[name].read_bytes(),path.read_bytes(),name)
    def test_original_skillfx_selective_diff(self):
        original=(PARENT/"EGGRUMBLE_SkillFX.luau").read_text()
        patched=(HERE/"EGGRUMBLE_SkillFX_ModeFair_Overlay.luau").read_text()
        self.assertIn("ModeFairQuota.new(72,12)",patched)
        self.assertIn("fairQuota:canStart(parent.Name,MAX_NEW_PER_PULSE)",patched)
        self.assertIn("fairQuota:acquire(parent.Name)",patched)
        self.assertIn("fairQuota:release(lease)",patched)
        self.assertIn("SkillFX.emit(parent:Instance,role:string,slot:string",patched)
        self.assertEqual(original.count("function SkillFX.emit"),patched.count("function SkillFX.emit"))
        for feature in ("WarGod_FlyingSlash","Mage_CrystalStorm","Assassin_ShadowAfterimage","Esper_PsiOrbit","MadScientist_RailShot","Beast_FangClaw","CurseMaster_SoulFlame","ULTIMATE_WarGod_DivineHalo"):
            self.assertIn(feature,patched)
    def test_no_game_authority_duplication(self):
        q=(HERE/"EGGRUMBLE_FXModeFairQuota.luau").read_text()
        for bad in ("Game","DataStoreService","RemoteEvent","FireServer","TakeDamage","Humanoid","Instance.new","task.wait"):
            self.assertNotIn(bad,q)
        self.assertIn("self.tickets[id]=nil",q)
        self.assertIn("self.usage[mode]-=1",q)
    def test_project_isolation_and_single_game(self):
        s=PROJECT.read_text()
        self.assertEqual(s.count("EGGRUMBLE_LobbyCastleModesPreview.server.luau"),1)
        self.assertEqual(s.count("EGGRUMBLE_SkillFX_ModeFair_Overlay.luau"),1)
if __name__=="__main__":unittest.main()
