#!/usr/bin/env python3
"""P0 #431 native contracts: mobile cap, original server authority and rollback."""
import unittest
from pathlib import Path
from apply_fb015_live_combat_fx import patch,blob,BASE_BLOB,FEATURE

ART = Path(__file__).resolve().parent/"features"/"p0_playable_art77"/"ConfirmedSlashFX.client.luau"

class LiveCombatArtQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ART.read_bytes()
        cls.new = patch(cls.source).decode("utf8")

    def test_pinned_real_author_original(self):
        self.assertEqual(blob(self.source),BASE_BLOB)
        self.assertIn('popup:GetPropertyChangedSignal("Enabled"):Connect(',self.new)
        self.assertIn('local horde = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)',self.new)

    def test_live_will_not_early_return_outside_studio(self):
        self.assertNotIn('if not RunService:IsStudio() then return end',self.new)
        self.assertIn('local studioPreview = RunService:IsStudio()',self.new)
        self.assertIn('container:SetAttribute("PreviewOnly", studioPreview)',self.new)
        self.assertIn('container:SetAttribute("LiveParitySourceCandidate", true)',self.new)
        self.assertIn('if not alive or not popup.Enabled or not model.Parent then return end',self.new)

    def test_mobile_client_budget_is_bounded(self):
        self.assertIn('local MAX_ACTIVE_PARTS = if touchDevice then 16 else 32',self.new)
        self.assertIn('local VIEW_DISTANCE = if touchDevice then 70 else 110',self.new)
        self.assertIn('local MIN_PER_TARGET_INTERVAL = if touchDevice then .16 else .09',self.new)
        self.assertIn('local BURST_DURATION = if touchDevice then .17 else .23',self.new)
        self.assertIn('if not alive or not container.Parent or active >= MAX_ACTIVE_PARTS then return nil end',self.new)
        self.assertIn('Debris:AddItem(p, .34)',self.new)

    def test_no_gameplay_or_collision_or_permanent_hud(self):
        for needle in ('FireServer(', 'OnServerEvent:Connect(', 'TakeDamage(',
                       'Instance.new("ScreenGui")', 'CanCollide = true',
                       'CanQuery = true','CanTouch = true','GetDataStore('):
            self.assertNotIn(needle,self.new)
        for needle in ('p.CanCollide = false','p.CanQuery = false','p.CanTouch = false',
                       'p.Anchored = true','p.Material = Enum.Material.Neon'):
            self.assertIn(needle,self.new)

    def test_source_tampering_is_rejected(self):
        with self.assertRaises(AssertionError):
            patch(self.source+b"\n-- drift")

    def test_duplicate_patch_is_rejected(self):
        with self.assertRaises(AssertionError):
            patch(self.new.encode("utf8"))

    def test_no_fabricated_real_runtime_gate(self):
        self.assertIn('FB008_CONFIRMED_HIT_SLASH_VFX_ATTACHED_LIVE_PARITY_ART_NO_GO',self.new)
        self.assertNotIn('FB008_CONFIRMED_HIT_SLASH_VFX_ATTACHED_STUDIO_ART_NO_GO',self.new)

if __name__=="__main__":
    unittest.main()
