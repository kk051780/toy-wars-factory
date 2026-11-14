"""#388 ART-MOTION SOURCE_WIP: offline safety assertions only.

Run: python3 -m unittest rc_fastlane.test_art_motion_source -v
Static checks are not native Luau compilation or Studio/Android proof.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
MOTION = ROOT / "features" / "art_motion" / "NeutralMotion.client.luau"
ART = ROOT / "features" / "art_minion" / "MinionArtSilhouette.server.luau"


class ArtMotionSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.motion = MOTION.read_text(encoding="utf-8")
        cls.author = ART.read_text(encoding="utf-8")

    def test_visual_only_and_studio_gate(self):
        s = self.motion
        self.assertIn('if not RunService:IsStudio() then return end', s)
        for prohibited in (
            ":FireServer(", ":InvokeServer(", "OnServerEvent", "DataStoreService",
            "SetAttribute(\"P0D_ART_MINION_V1\"", "Damage =",
            "Instance.new(\"RemoteEvent\")", "TakeDamage(",
        ):
            self.assertNotIn(prohibited, s)

    def test_existing_art_consumed_no_new_geometry(self):
        s = self.motion
        self.assertNotIn('Instance.new("Part")', s)
        self.assertNotIn('Instance.new("ParticleEmitter")', s)
        # Only user-facing animated attachments count as authored parts.
        # Diagnostic labels such as ART_MOTION_NO_ARENA are not geometry.
        declaration = s.split("local watchedParts = {", 1)[1].split("\n}\n", 1)[0]
        watched = re.findall(r'"(ART_[A-Z_0-9-]+)"', declaration)
        self.assertEqual(len(watched), 41)
        self.assertEqual(len(set(watched)), 41, "No repeated part names")
        for name in watched:
            fragment = re.sub(r"-?1$", "", name.removeprefix("ART_"))
            self.assertIn(fragment, self.author, msg=f"original #374 art missing {name}")

    def test_original_full_41_silhouettes_and_spawn_ghost_guard(self):
        s=self.motion
        art=s.split("local watchedParts = {",1)[1].split("\n}\n",1)[0]
        variants={}
        for species in ("KNIGHT","WRAITH","BRUTE","ELITE"):
            chunk=art.split(species+" = {",1)[1].split("}",1)[0]
            variants[species]=re.findall(r'"(ART_[A-Z_0-9-]+)"',chunk)
        self.assertEqual({k:len(v) for k,v in variants.items()},
                         {"KNIGHT":10,"WRAITH":10,"BRUTE":11,"ELITE":10})
        self.assertEqual(3*10+3*10+2*11+1*10,92)
        self.assertIn("MAX_ACTIVE_COSMETIC_PARTS = 104",s)
        # All original static body art is hidden at equip AND out-of-range;
        # never draw frozen helmets and armor at previous spawn locations.
        self.assertIn("for _,visual in ipairs(attachments) do",s)
        lod=s.split("            else\n                -- LOD:",1)[1].split(
            "            end\n",1)[0]
        self.assertIn("visual.original.LocalTransparencyModifier = 1",lod)
        self.assertNotIn("visual.initialModifier",lod)
        self.assertIn("model.Destroying",s)
        self.assertIn("if not isRunning or not isMinion(model)",s)

    def test_animation_budget_and_spawn_reset(self):
        s = self.motion
        for term in (
            "MAX_MODELS = 16", "MAX_ACTIVE_COSMETIC_PARTS = 104",
            "VIEW_RANGE_STUDS = 105", "ANIM_STEP = 1 / 25",
            "horde.ChildAdded", "model.Destroying", "script.Destroying",
            "core.CFrame:ToObjectSpace(source.CFrame)",
            "if #originals ~= #watchedParts[kind]",
            "local copy = source:Clone()",
            "original.LocalTransparencyModifier",
            "visual.copy.CFrame = core.CFrame * visual.offset * localMotion",
            "cue.OnClientEvent:Connect(",
            "lastHitSerial[id] = serial",
            "local lastEpoch = nil",
            "P0D_ART_RECENT_V1",
            "P0D_ART_EPOCH_V1",
            "replayRecent()",
            "local function syncServerEpoch()",
            "if not isRunning or not isMinion(model)",
            "if lastEpoch ~= nil and epoch < lastEpoch then return false end",
            "local pendingHits = {}",
            "pendingHits[id] = {at=now, ko=isKO}",
            "if now - pending.at >= .7 then return false end",
            "if pending.ko then entry.koAt = pending.at end",
            "local added = horde.ChildAdded:Connect(",
            'Workspace:WaitForChild("TRAP_RAIDERS_S1")',
        ):
            self.assertIn(term, s)


if __name__ == "__main__":
    unittest.main()
