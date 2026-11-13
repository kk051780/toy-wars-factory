"""Reject solo-preview bypasses that would accidentally modify live 2-client S1."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOLO=(ROOT/"src/StudioSoloGateRules.luau").read_text("utf-8")
BUILDER=(ROOT/"tools/build_48_studio_solo.py").read_text("utf-8")

class StudioOnlyPolicy(unittest.TestCase):
    def test_policy_untrusted_values_are_rejected(self):
        self.assertIn('isStudio~=true',SOLO)
        self.assertIn('players==1',SOLO)
        self.assertIn('(red==1 and blue==0) or (red==0 and blue==1)',SOLO)
    def test_public_play_never_drops_two_team_requirement(self):
        self.assertIn('players>=minPlayers and red>0 and blue>0',SOLO)
    def test_no_extra_server_or_remote(self):
        for s in ('OnServerEvent','RemoteEvent','Instance.new','DataStore',
                  'TakeDamage','MarketplaceService','FireServer'):
            self.assertNotIn(s,SOLO)
    def test_all_three_original_start_or_team_empty_gates_patched(self):
        for s in ('if count >= Config.MinPlayers and teamCount("RED") > 0',
                  'if count < Config.MinPlayers or teamCount("RED") == 0',
                  'if teamCount("RED") <= 0 then stopRound("BLUE"'):
            self.assertIn(s,BUILDER)
        self.assertIn('g.count(\'StudioSoloGateRules.canStart(\')==2',BUILDER)
        self.assertIn('g.count(\'StudioSoloGateRules.isPractice(\')==2',BUILDER)
    def test_immutable_game_loop_and_double_elite_hooks_checked(self):
        self.assertIn('g.count(\'s2HeistGate:beforeHit(horde)\')==2',BUILDER)
        self.assertIn('g.count(\'s2HeistGate:tick(\')==1',BUILDER)
        self.assertIn('g.count(\'remote.OnServerEvent:Connect(\')==1',BUILDER)
    def test_no_overwrite_all_47_original_unchanged_except_game(self):
        self.assertIn('assert not private_dir.exists()',BUILDER)
        self.assertIn('assert not c1_dir.exists()',BUILDER)
        self.assertIn('if k!="server/Game.server.luau"',BUILDER)
        self.assertIn('assert len(all_new)==48',BUILDER)
    def test_public_not_claimed_playable(self):
        for s in ('"public_or_live_solo_allowed":False',
                  '"studio_play":"NOT_TESTED"',
                  '"official_rc_adopted":False'):
            self.assertIn(s,BUILDER)

if __name__=="__main__":
    unittest.main()
