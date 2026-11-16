"""Fail-closed source/authority regression gate; native syntax is separate in CI."""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import compose_patch as patch


class BossWavePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_path = os.environ.get("GQ_ORIGINAL_BOSS")
        if not raw_path:
            raise RuntimeError("GQ_ORIGINAL_BOSS is mandatory; never test a made-up copy")
        cls.original = Path(raw_path).read_bytes()
        cls.patched = patch.patch_bytes(cls.original).decode("utf-8")
        cls.original_text = cls.original.decode("utf-8")

    def test_source_identity_is_fixed_original_blob(self):
        self.assertEqual(patch.git_blob_sha(self.original), patch.ORIGINAL_BLOB)

    def test_original_reproduces_no_wall_gate(self):
        self.assertEqual(self.original_text.count(patch.DAMAGE_ANCHOR), 1)
        self.assertNotIn("shockwaveClear(c,root)", self.original_text)

    def test_patch_only_two_exact_hunks(self):
        restored = self.patched.replace(patch.FUNCTION_ADD, "", 1).replace(
            patch.DAMAGE_REPLACEMENT, patch.DAMAGE_ANCHOR, 1
        )
        self.assertEqual(restored, self.original_text)

    def test_collision_aware_line_of_sight(self):
        self.assertIn("params.RespectCanCollide=true", self.patched)
        self.assertIn("params.FilterDescendantsInstances={model,character}", self.patched)
        self.assertIn("workspace:Raycast(origin,direction,params)==nil", self.patched)

    def test_damage_must_follow_range_height_and_wall_gate(self):
        self.assertIn(
            "if d<=11 and math.abs(root.Position.Y-at.Y)<=8\n"
            "      and shockwaveClear(c,root) then",
            self.patched,
        )
        self.assertEqual(self.patched.count("h:TakeDamage(28)"), 1)

    def test_live_character_fail_closed(self):
        self.assertIn("if not character then return false end", self.patched)
        self.assertIn("if direction.Magnitude<=0.01 then return true end", self.patched)

    def test_no_second_boss_or_remote_or_damage_authority(self):
        for word in ("function Boss.spawn(", "local function damageFrom(", "h:TakeDamage(28)"):
            self.assertEqual(self.patched.count(word), self.original_text.count(word))
        self.assertNotIn("RemoteEvent", patch.FUNCTION_ADD)

    def test_tampered_original_must_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Git blob drift"):
            patch.patch_bytes(self.original + b" ")

    def test_reapplication_must_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Git blob drift"):
            patch.patch_bytes(self.patched.encode("utf-8"))

    def test_no_change_to_existing_boss_attack_or_cooldowns(self):
        for code in ("MIN_HIT_INTERVAL=.22", "health=900", "task.wait(5)", "task.wait(2)",
                     "maxReach=if fromAuthorizedSkill==true then 36 else 14"):
            self.assertIn(code, self.patched)


if __name__ == "__main__":
    unittest.main()
