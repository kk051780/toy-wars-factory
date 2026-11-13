#!/usr/bin/env python3
"""Run against an ACTUAL original author 42-Luau dist clone, not made-up mocks."""
import hashlib, os, pathlib, unittest
from importlib.util import spec_from_file_location, module_from_spec

ROOT=pathlib.Path(__file__).resolve().parents[1]
DIST=pathlib.Path(os.environ["P0D_SOLO_DIST"])
BASE=pathlib.Path(os.environ["P0D_SOLO_GAME_BASE"])
OUT=DIST/"src/server/Game.server.luau"
spec=spec_from_file_location("patch",ROOT/"tools/studio_solo_patch.py")
mod=module_from_spec(spec)
spec.loader.exec_module(mod)
def eligible(studio,teams):
    return studio and len(teams)==1 and teams[0] in ("RED","BLUE")
def start(studio,teams):
    return (len(teams)>=2 and "RED" in teams and "BLUE" in teams) or eligible(studio,teams)
def active(studio,teams,was_solo):
    if not teams:return False
    if len(teams)==1:return was_solo and eligible(studio,teams)
    return "RED" in teams and "BLUE" in teams

class ActualSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=BASE.read_text("utf-8")
        cls.new=OUT.read_text("utf-8")
    def test_original_fixed(self):self.assertEqual(mod.sha(self.original.encode()),mod.EXPECTED_OLD_SHA256)
    def test_new_fixed(self):self.assertEqual(mod.sha(self.new.encode()),mod.EXPECTED_NEW_SHA256)
    def test_exact_patch(self):self.assertEqual(self.new,mod.patch_game(self.original))
    def test_42_scripts_retained(self):self.assertEqual(len(list((DIST/"src").rglob("*.luau"))),42)
    def test_one_original_game(self):
        self.assertEqual(len(list((DIST/"src").rglob("Game.server.luau"))),1)
    def test_one_studio_guard(self):self.assertIn('if not RunService:IsStudio() then return false end',self.new)
    def test_exactly_one_real_player(self):self.assertIn('if #online ~= 1 then return false end',self.new)
    def test_no_neutral_player(self):self.assertIn('return t == "RED" or t == "BLUE"',self.new)
    def test_round_latch(self):self.assertIn('studioSoloRound = isStudioSoloPlayer()',self.new)
    def test_lobby_extension(self):self.assertIn('or isStudioSoloPlayer() then',self.new)
    def test_countdown_extension(self):self.assertIn('if not isStudioSoloPlayer() and',self.new)
    def test_active_no_empty_team_false_win(self):
        self.assertIn('studioSoloRound and isStudioSoloPlayer()',self.new)
    def test_production_original_count_and_teams_remains(self):
        self.assertIn('count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0',self.new)
    def test_unchanged_original_server_authority(self):
        for token in ('remote.OnServerEvent:Connect(', 'First90WaypointRules',
                      'First90GuideRules','PersistentHatchStore','Evolution.nextEvolution('):
            self.assertEqual(self.new.count(token),self.original.count(token),token)
    def test_single_changed_script(self):
        import subprocess
        from pathlib import Path
        # Parent author source manifest locks original Game and Horde. Only original Game changed.
        self.assertGreater(len(self.new),90000)
        self.assertEqual(mod.sha(OUT.read_bytes()),mod.EXPECTED_NEW_SHA256)
    def test_negative_duplicate_marker_rejected(self):
        with self.assertRaises(ValueError):mod.patch_game(self.original+self.original)
    def test_negative_missing_marker_rejected(self):
        with self.assertRaises(ValueError):mod.patch_game(self.original.replace('local function resetRound()','local function removedResetRound()'))

class ScenarioOracle(unittest.TestCase):
    def test_empty_studio_denied(self):self.assertFalse(start(True,[]))
    def test_empty_live_denied(self):self.assertFalse(start(False,[]))
    def test_studio_red_one_starts(self):self.assertTrue(start(True,["RED"]))
    def test_studio_blue_one_starts(self):self.assertTrue(start(True,["BLUE"]))
    def test_live_red_one_denied(self):self.assertFalse(start(False,["RED"]))
    def test_live_blue_one_denied(self):self.assertFalse(start(False,["BLUE"]))
    def test_neutral_studio_one_denied(self):self.assertFalse(start(True,["NONE"]))
    def test_two_red_denied(self):self.assertFalse(start(True,["RED","RED"]))
    def test_two_blue_denied(self):self.assertFalse(start(False,["BLUE","BLUE"]))
    def test_both_teams_live_allowed(self):self.assertTrue(start(False,["RED","BLUE"]))
    def test_both_teams_studio_allowed(self):self.assertTrue(start(True,["RED","BLUE"]))
    def test_solo_round_studio_keeps_active(self):self.assertTrue(active(True,["RED"],True))
    def test_solo_round_live_denied(self):self.assertFalse(active(False,["RED"],True))
    def test_normal_two_player_disconnect_ends(self):self.assertFalse(active(True,["RED"],False))
    def test_solo_round_no_players_ends(self):self.assertFalse(active(True,[],True))
    def test_solo_later_two_join_works(self):self.assertTrue(active(True,["RED","BLUE"],True))

if __name__=="__main__":unittest.main(verbosity=2)
