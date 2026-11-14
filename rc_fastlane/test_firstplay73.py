#!/usr/bin/env python3
"""Cumulative first-play source QA: NOT physical Studio, FPS or owner FUN proof."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location(
    "firstplay73",ROOT/"rc_fastlane/apply_firstplay73.py")
assert spec and spec.loader
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FirstPlay73(unittest.TestCase):
    def test_author_adapter_exact_immutable_original_sha(self):
        self.assertEqual(len(m.AUTHORS),3)
        for name,filename,sha,feat in m.AUTHORS:
            self.assertEqual(m.gitblob((m.AUTH/filename).read_bytes()),sha)
        self.assertEqual(set(m.load_authors()),{"ready","lobby","solo"})

    def test_genuine_lobby_and_bot_modules_same_pinned_source(self):
        self.assertEqual(len(m.modules()),2)
        for dest,path,sha in m.MODULES:
            self.assertEqual(m.gitblob((m.AUTH/path).read_bytes()),sha)

    def test_no_second_authority_in_modules(self):
        for dest,raw in m.modules().items():
            self.assertNotIn(b'Instance.new("RemoteEvent")',raw)
            self.assertNotIn(b"OnServerEvent:Connect(",raw)
            self.assertNotIn(b"UpdateAsync(",raw)
        self.assertIn("ONLY_OLD_SINGLE_GAME",
            (ROOT/"rc_fastlane/apply_firstplay73.py").read_text())

    def test_composition_uses_one_game_and_three_authored_patches(self):
        src=(ROOT/"rc_fastlane/apply_firstplay73.py").read_text()
        for anchor in (
            'source=author["ready"].patch_game(source)',
            'source=author["lobby"].patch_game(source)',
            'source=author["solo"].patch_game(source)',
            'updated[CONFIG]=author["ready"].patch_config(',
            'updated[HUD]=author["ready"].patch_hud(',
            'updated[V4]=author["lobby"].patch_v4(',
            'assert source.count("remote.OnServerEvent:Connect(")==1',
            '"solo_bot_teams":"2_ally_3_enemy"',
            '"solo_classic_egg_only":True',
        ):
            self.assertIn(anchor,src)

    def test_original_5_art_source_bytes_retain(self):
        src=(ROOT/"rc_fastlane/apply_firstplay73.py").read_text()
        for key in (
            "server/CastleBattlefield.server.luau",
            "server/H1CoastalSeascape.server.luau",
            "server/FantasyWorldArt.server.luau",
            "server/ArtMinionSilhouette.server.luau",
            "client/ConfirmedSlashFX.client.luau",
            "assert all(previous[p]==updated[p] for p in previous if p not in MODIFIED)",
        ):
            self.assertIn(key,src)

    def test_studio_only_classic_and_no_fake_five_egg(self):
        all_src="".join((m.AUTH/f).read_text() for _,f,_,_ in m.AUTHORS)
        self.assertIn("studioSoloRoundStarted",all_src)
        self.assertIn("EXPERIMENTAL_FIVE_EGG_MODE",all_src)
        self.assertIn("allPlayersReadyForRound",all_src)
        self.assertIn("SoloTeamBots.stop()",all_src)
        self.assertIn("LobbyIsland.spawn(team)",all_src)

    def test_new_castle_bounds_extend_active_only_lobby_safety_retained(self):
        src=(ROOT/"rc_fastlane/apply_firstplay73.py").read_text()
        self.assertIn('before_bounds="math.abs(position.X) > 130 or math.abs(position.Z) > 76"',src)
        self.assertIn('"math.abs(position.X) > 182 or math.abs(position.Z) > 145"',src)
        self.assertIn('"FIRSTPLAY_EXPANDED_CASTLE_RECOVERY_DRIFT"',src)
        self.assertIn('author["lobby"].patch_game(source)',src)
        self.assertIn('LobbyIsland.spawn(team)',(m.AUTH/"author_lobby.py").read_text())

    def test_seven_layers_correct_counts(self):
        self.assertEqual(m.BEFORE,71)
        self.assertEqual(m.AFTER,73)
        self.assertEqual(m.MODIFIED,{
            "server/Game.server.luau","shared/Config.luau",
            "client/HUD.client.luau","server/V4TrainingBridge.server.luau"})

    def test_off_zero_write_including_missing_dir(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"no_files"
            self.assertFalse(m.apply(path,False))
            self.assertFalse(path.exists())
            path.mkdir()
            sentinel=path/"sentinel.txt"
            sentinel.write_text("do not touch")
            self.assertFalse(m.apply(path,False))
            self.assertEqual(sentinel.read_text(),"do not touch")

    def test_source_wrong_count_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)
            (path/"src").mkdir()
            with self.assertRaisesRegex(AssertionError,"FIRSTPLAY_REQUIRES_ART71"):
                m.apply(path,True)

    def test_unresolved_engine_studio_risks_not_claimed(self):
        src=(ROOT/"rc_fastlane/apply_firstplay73.py").read_text()
        self.assertIn('"real_studio":"NOT_TESTED"',src)
        self.assertIn('"owner_fun":"FUN_NO_GO"',src)
        self.assertIn('"android_fps":"NOT_TESTED"',src)
        self.assertIn('"studio_overlap_castle_sea_lobby":"NOT_TESTED"',src)
        self.assertIn('"five_egg_ai":"NOT_SUPPORTED"',src)


if __name__=="__main__":
    unittest.main()
