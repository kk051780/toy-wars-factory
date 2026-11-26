#!/usr/bin/env python3
"""Actual immutable author source checks and mutation probes, no copied Mage policy."""
import unittest
from pathlib import Path
from compose_fence import patch_text,gitblob,ORIGINAL_MAGE_GIT_BLOB,CURRENT_GUARD,ALLY_GUARD
ORIGINAL=Path(__file__).resolve().parents[2]/"_mage777/handoffs/EGGRUMBLE-MAGE-REVIVE-20261118/EGGRUMBLE_MageRevive.luau"

class MageCurrentHumanFence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=ORIGINAL.read_text(encoding="utf-8")
 def test_original_pin(self):
  self.assertEqual(gitblob(self.source.encode("utf-8")),ORIGINAL_MAGE_GIT_BLOB)
 def test_reuse_original_and_two_exact_fences(self):
  good=patch_text(self.source)
  self.assertEqual(good.count(CURRENT_GUARD),1)
  self.assertEqual(good.count(ALLY_GUARD),1)
  self.assertEqual(good.count("s.isCurrentHuman(target)"),1)
  self.assertEqual(good.count("s.isCurrentHuman(healer)"),1)
  self.assertEqual(good.count('e.humanoid.Health=math.max('),1)
 def test_missing_original_guard_rejected(self):
  with self.assertRaisesRegex(ValueError,"RED_ORIGINAL"):
   patch_text(self.source.replace("if healer==target","if false or healer==target",1))
 def test_second_owner_source_rejected(self):
  with self.assertRaisesRegex(ValueError,"RED_ORIGINAL"):
   patch_text(self.source+"\nreturn OtherMage\n")
 def test_original_equip_and_cooldown_unchanged(self):
  out=patch_text(self.source)
  for anchor in ('local MAGE_COOLDOWN_SECONDS=40','local PROMPT_HOLD_SECONDS=3',
                 'local DOWNED_SECONDS=60','e.humanoid.MaxHealth*REVIVE_FRACTION',
                 'prompt.Triggered:Connect(function(healer:Player)'):
   self.assertEqual(self.source.count(anchor),out.count(anchor))
if __name__=="__main__":unittest.main()
