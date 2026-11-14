#!/usr/bin/env python3
"""Native contract: five distinct, authored exact-source art overlays; FUN not asserted."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location(
    "p0d_five_art",ROOT/"rc_fastlane/apply_five_art_composite.py")
assert spec and spec.loader
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FiveArtSingleCandidate(unittest.TestCase):
    def test_five_independent_original_sources_exact_pins(self):
        self.assertEqual(len(m.PREPS),5)
        self.assertEqual(len(m.safety()),5)
        self.assertEqual(set(r[0] for r in m.PREPS),{
            "ART-CASTLE","ART-SEA","ART-WORLD","ART-MINION","ART-COMBAT"})
        for cat,feat,path,dest,pin in m.PREPS:
            self.assertEqual(m.gitblob((m.ROOT/"features"/path).read_bytes()),pin)
            self.assertTrue(dest.startswith(("server/","client/")))

    def test_real_original_horde_and_visual_only_single_authority(self):
        self.assertEqual(set(m.safety()),{r[3] for r in m.PREPS})
        for source in m.safety().values():
            self.assertNotIn(b"FireServer(",source)
            self.assertNotIn(b"OnServerEvent:Connect(",source)
            self.assertNotIn(b"TakeDamage(",source)
            self.assertIn(b"RunService:IsStudio()",source)

    def test_all_original_six_game_systems_preserved_with_one_client(self):
        text=(ROOT/"rc_fastlane/apply_five_art_composite.py").read_text()
        for name in ("server/Game.server.luau","server/MusouHorde.luau",
                     "server/MapBuilder.luau","server/H1FunWorld.server.luau",
                     "client/HUD.client.luau","original66_all_bytes_identical",
                     "CLIENT_PROJECT_NAME","total_scripts","total_sources"):
            self.assertIn(name,text)
        self.assertEqual(sum(path.startswith("client/") for path in m.safety()),1)

    def test_disconnected_features_not_false_counted(self):
        src=(ROOT/"rc_fastlane/apply_five_art_composite.py").read_text()
        self.assertIn('"solo_bots":"MISSING_NOT_IN_THIS_CANDIDATE"',src)
        self.assertIn('"lobby_dojos":"MISSING_NOT_IN_THIS_CANDIDATE"',src)
        self.assertIn('"owner_approved":False',src)
        self.assertIn('"studio_single_player":"NOT_TESTED"',src)
        self.assertIn('"android_fps":"NOT_TESTED"',src)

    def test_studio_source_timing_and_finite_render_budget(self):
        contents=m.safety()
        sea=contents["server/H1CoastalSeascape.server.luau"].decode()
        world=contents["server/FantasyWorldArt.server.luau"].decode()
        minion=contents["server/ArtMinionSilhouette.server.luau"].decode()
        combat=contents["client/ConfirmedSlashFX.client.luau"].decode()
        for needle in ("terra:FillBlock","SEA_BOARDWALK_DECK_",'"COSMETIC_SEA"'):
            self.assertIn(needle,sea)
        self.assertIn("CanCollide=false",world)
        self.assertIn("MAX_ACTIVE_PARTS = 48",combat)
        self.assertIn("MIN_PER_TARGET_INTERVAL = .09",combat)
        self.assertIn('popup:GetPropertyChangedSignal("Enabled")',combat)
        self.assertIn("CanCollide = false",minion)

    def test_overlap_risk_remains_unproven(self):
        castle=m.safety()["server/CastleBattlefield.server.luau"].decode()
        sea=m.safety()["server/H1CoastalSeascape.server.luau"].decode()
        self.assertIn('"NORTH_WOODLAND_TRAIL"',castle)
        self.assertIn("side * 67",castle)
        self.assertIn('"COAST_ISLAND_"',sea)
        self.assertIn('"castle_sea_world_overlap":"UNTESTED_STUDIO_REVIEW_REQUIRED"',
                      (ROOT/"rc_fastlane/apply_five_art_composite.py").read_text())

    def test_off_does_not_touch_any_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"does_not_exist"
            self.assertFalse(m.apply(dest,False))
            self.assertFalse(dest.exists())
            dest.mkdir()
            existing=dest/"original-script"
            existing.write_bytes(b"abcd")
            self.assertFalse(m.apply(dest,False))
            self.assertEqual(existing.read_bytes(),b"abcd")

    def test_fail_closed_if_not_exact_66(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            (dest/"src").mkdir()
            with self.assertRaisesRegex(AssertionError,"FIVE_ART_REQUIRES_OFFICIAL66"):
                m.apply(dest,True)

    def test_feature_flags_unique_not_doubled(self):
        self.assertEqual(len({r[1] for r in m.PREPS}),5)
        self.assertNotIn("FB015_CHARACTER_VISUAL_STAGE1",set(r[1] for r in m.PREPS))
        self.assertNotIn("ART_COMBAT_SLASH_READONLY_V1",set(r[1] for r in m.PREPS))

if __name__=="__main__":
    unittest.main()
