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
        self.assertGreaterEqual(len(watched), 16)
        for name in watched:
            fragment = re.sub(r"-?1$", "", name.removeprefix("ART_"))
            self.assertIn(fragment, self.author, msg=f"original #374 art missing {name}")

    def test_animation_budget_and_spawn_reset(self):
        s = self.motion
        for term in (
            "MAX_MODELS = 16", "MAX_ACTIVE_COSMETIC_PARTS = 56",
            "VIEW_RANGE_STUDS = 105", "ANIM_STEP = 1 / 25",
            "horde.ChildAdded", "model.Destroying", "script.Destroying",
            "core.CFrame:ToObjectSpace(art.CFrame)",
            "if #attachments ~= #watchedParts[kind] then return false end",
            "core.CFrame * visual.offset * localMotion",
        ):
            self.assertIn(term, s)


if __name__ == "__main__":
    unittest.main()
