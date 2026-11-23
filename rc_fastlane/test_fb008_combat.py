#!/usr/bin/env python3
"""FB-008/015 SOURCE safety; not a substitute for Studio visual FUN tests."""
from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
filename = ROOT / "rc_fastlane/apply_fb008_combat.py"
spec = importlib.util.spec_from_file_location("apply_fb008_combat", filename)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ConfirmedCombatVisual(unittest.TestCase):
    def setUp(self):
        self.raw = mod.SOURCE.read_bytes()
        self.text = self.raw.decode("utf8")

    def test_exact_original_client_fx_gitblob(self):
        self.assertEqual(mod.gitblob(self.raw),mod.BLOB)
        self.assertIn("FB008_CONFIRMED_SLASH_VFX_CLIENT_ONLY",self.text)
        mod.source_safety()

    def test_only_real_server_horde_hit_or_ko_gives_visuals(self):
        for needle in (
            'core:FindFirstChild("RealDamagePopup")',
            'popup:GetPropertyChangedSignal("Enabled"):Connect(',
            'if not alive or not popup.Enabled or not model.Parent then return end',
            'renderConfirmedHit(model,core,popup)',
            'local isKO = string.find(markerText,"撃破",1,true)',
            "if isKO then",
        ):
            self.assertIn(needle,self.text)
        self.assertNotIn('UserInputService',self.text)
        self.assertNotIn('FireServer(',self.text)
        self.assertNotIn('TakeDamage(',self.text)
        self.assertNotIn('Touched:Connect(',self.text)

    def test_slash_geometry_and_ko_ripple_two_separate_visuals(self):
        for needle in (
            "for i=1,3 do",
            '"CONFIRMED_HIT_SLASH_"..i',
            '"CONFIRMED_KO_GROUND_RIPPLE"',
            "Enum.Material.Neon",
            "TweenService:Create(trail",
            "TweenService:Create(ring",
            "p.CastShadow = false",
            "p.CanCollide = false",
            "p.CanTouch = false",
            "p.CanQuery = false",
        ):
            self.assertIn(needle,self.text)

    def test_hard_budget_and_view_culling_no_unbounded_heartbeat(self):
        for needle in (
            "MAX_ACTIVE_PARTS = 48",
            "VIEW_DISTANCE = 115",
            "MIN_PER_TARGET_INTERVAL = .09",
            "if not alive or not container.Parent or active >= MAX_ACTIVE_PARTS",
            "root.Position - core.Position",
            "Debris:AddItem(p, .34)",
            "task.delay(.35, function()",
        ):
            self.assertIn(needle,self.text)
        self.assertNotIn("RunService.Heartbeat:Connect",self.text)
        self.assertNotIn("RenderStepped:Connect",self.text)

    def test_uses_real_horde_reset_lifecycle(self):
        self.assertIn('horde.ChildAdded:Connect(',self.text)
        self.assertIn('model.Name:match("^MUSOU_MINION_%d+$")',self.text)
        self.assertIn('model.Name == "MUSOU_ELITE_TELEGRAPH"',self.text)
        self.assertIn('model.Destroying:Connect(',self.text)
        self.assertIn('horde.Destroying:Connect(',self.text)
        self.assertIn("script.Destroying:Connect",self.text)

    def test_strict_studio_client_scope_and_no_game_authority(self):
        self.assertIn("if not RunService:IsStudio() then return end",self.text)
        self.assertIn('Players.LocalPlayer',self.text)
        self.assertIn('NoGameplayAuthority", true',self.text)
        for unsafe in ('DataStoreService','RemoteEvent','MarketplaceService',
                       'UpdateAsync(', 'TakeDamage(', 'LoadCharacter(',
                       'SetAttribute("Score"', 'Terrain:FillBlock'):
            self.assertNotIn(unsafe,self.text)

    def test_source_tamper_rejects(self):
        altered=self.raw.replace(b'CONFIRMED_KO_GROUND_RIPPLE',b'FALSE_RIPPLE_VISUAL',1)
        self.assertNotEqual(mod.gitblob(altered),mod.BLOB)
        # Tamper would be rejected if the authored file differed from pin.

    def test_off_does_not_create_or_modify_files(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"not_created"
            self.assertFalse(mod.apply(path,False))
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
