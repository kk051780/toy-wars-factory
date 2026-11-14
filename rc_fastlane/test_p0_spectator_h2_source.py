import tempfile,unittest
from pathlib import Path
from rc_fastlane import apply_p0_spectator_h2_78 as m

class SpectatorPrivate78(unittest.TestCase):
    def test_two_original_owner_sources_only(self):
        text=Path(m.__file__).read_text("utf8")
        self.assertEqual({m.GAME,m.BOT},{"server/Game.server.luau","server/SoloTeamBots.luau"})
        self.assertIn('assert {k for k in before if before[k]!=after[k]}=={GAME,BOT}',text)
        self.assertIn('other76_byte_exact',text)
        self.assertIn('os.replace(stage,out)',text)
        self.assertIn('assert read(base)==before',text)
    def test_all_five_solo_roster_authority_contracts(self):
        text=Path(m.__file__).read_text("utf8")
        for anchor in (
            'local function eligibleSoloPlayers(): {Player}',
            'player:SetAttribute("P0D_LateJoinSpectator",true)',
            'roundReady[entrant]=false',
            'LobbyIsland.spawn("RED")',
            'local count = #eligibleSoloPlayers()',
            'local online = eligibleSoloPlayers()',
            '#eligibleSoloPlayers()>1 and chosenMode==ModeVote.SCORE',
            'stopRound("DRAW","SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY")',
            'if eligible~=1 then Bot.stop();return end',
            'and team and (team.Name=="RED" or team.Name=="BLUE")',
        ):
            self.assertIn(anchor,text,anchor)
    def test_off_is_strict_zero_write_and_invalid_parent_fails_before_output(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            self.assertFalse(m.apply(p/"nonexistent",p/"candidate",False))
            self.assertFalse((p/"candidate").exists())
            (p/"wrong").mkdir()
            with self.assertRaises(AssertionError):
                m.apply(p/"wrong",p/"candidate",True)
            self.assertFalse((p/"candidate").exists())
    def test_author_group_fencing_and_replay(self):
        text=Path(m.__file__).read_text("utf8")
        self.assertIn('assert FIX not in src,"SPECTATOR_ALREADY_PATCHED"',text)
        self.assertIn('assert H2_REASON not in src',text)
        self.assertIn('assert "P0D_LateJoinSpectator" not in src',text)
        self.assertIn('assert src.count("remote.OnServerEvent:Connect(")==1',text)

if __name__=="__main__":unittest.main()
