"""Source-level regression and adversarial checks of ONE actually built full H1 game.
NO assertion claims live Roblox physics, multi-client, Android or FUN verification.
"""
from pathlib import Path
import hashlib,json,unittest

HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
NEW=OWN/"dist/EGG_RAID_RUMBLE_SINGLE_GAME_TWO_MODES_PRIVATE_STUDIO"
OLD=REPO/"handoffs/P0D-EGG-RUMBLE-H1-SCORE-MODE-20261113/dist/EGG_RAID_RUMBLE_H1_ORIGINAL_RULES_PRIVATE_STUDIO"
def blobs(d):return {p.relative_to(d/"src").as_posix():p.read_bytes() for p in sorted((d/"src").rglob("*.luau"))}
def sha(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def contract(game,hud,vote):
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('elseif data.action == "MODE_VOTE" then')==1
    assert game.count('if EXPERIMENTAL_FIVE_EGG_MODE then')>=3
    assert 'ModeVote.canVote(match.phase,data.mode,RunService:IsStudio()' in game
    assert 'Rules.validSeq(data.seq,lastSeq[player] or 0)' in game
    assert 'lastSeq[player]=data.seq -- consume invalid/replayed vote intents' in game
    assert 'modeVotes[player]=data.mode' in game
    assert 'if modeVotes[player]~=data.mode then' in game
    assert 'local chosenMode=ModeVote.tally(modeVotes,Players:GetPlayers())' in game
    assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in game
    assert 'modeVotes[player]=nil' in game
    assert 'table.clear(modeVotes)' in game
    assert 'table.clear(lastModeVote)' in game
    assert 'if not RunService:IsStudio() then return end' in game
    assert 'if RunService:IsStudio() then' in game
    assert 'h2Ids[player]=h2NextId' in game
    assert 'if EXPERIMENTAL_FIVE_EGG_MODE then "FIVE_EGG_SCORE" else "ONE_EGG_CAPTURE"' in game
    assert 'modeVotingOpen = match.phase=="LOBBY" or match.phase=="COUNTDOWN"' in game
    assert 'modeScoreAvailable = RunService:IsStudio()' in game
    assert 'H2Score.pickup(h2ScoreState,id,uid,side)' in game
    assert 'H2Score.deposit(h2ScoreState,uid,side)' in game
    assert 'H2Score.advance(h2ScoreState,1)' in game
    assert 'H2Score.assertConserved(h2ScoreState)' in game
    assert 'TrapRules.canPlace({' in game and 'WindRules.canActivate({' in game
    assert 'local EXPERIMENTAL_FIVE_EGG_MODE = false' in game
    assert 'if not ModeVote.canVote(' not in game # guard always includes server team & phase
    assert hud.count('local seq = 0')==1
    assert hud.count('remote:FireServer(')==2
    assert 'if kind == "MODE_VOTE" then' in hud
    assert 'mode = role, seq = seq' in hud
    assert 'classicMode.MouseButton1Click:Connect' in hud
    assert 'scoreMode.MouseButton1Click:Connect' in hud
    assert 'modePanel.Visible=canChoose' in hud
    assert 'and s.modeScoreAvailable==true' in hud
    assert 's.modeVote=="SCORE_5"' in hud
    assert 'modeHint.Text=' in hud
    assert 'FIVE_EGG_SCORE_240S' in hud
    assert '卵5こ' in hud
    assert 'function R.tally(' in vote
    assert 'function R.canVote(' in vote
    assert 'if phase~="LOBBY" and phase~="COUNTDOWN" then return false end' in vote
    assert 'if isStudio~=true and mode==R.SCORE then return false end' in vote
    assert 'return if five>classic then R.SCORE else R.CLASSIC' in vote
    for dangerous in ("FireServer","FireClient","DataStore","MarketplaceService","Instance.new("):
        assert dangerous not in vote,dangerous

class FullGameVoteSourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=blobs(OLD)
        cls.new=blobs(NEW)
        cls.game=cls.new["server/Game.server.luau"].decode()
        cls.hud=cls.new["client/HUD.client.luau"].decode()
        cls.vote=cls.new["server/ModeVoteRules.luau"].decode()
    def test_real_base31(self):self.assertEqual(len(self.base),31)
    def test_actual_game32(self):self.assertEqual(len(self.new),32)
    def test_extra_file_only_vote_module(self):
        self.assertEqual(set(self.new)-set(self.base),{"server/ModeVoteRules.luau"})
    def test_only_original_server_game_and_original_hud_updated(self):
        self.assertEqual({p for p in self.base if self.base[p]!=self.new[p]},
                         {"server/Game.server.luau","client/HUD.client.luau"})
    def test_other29_original_h1_gamescripts_identical(self):
        for p,v in self.base.items():
            if p not in ("server/Game.server.luau","client/HUD.client.luau"):
                self.assertEqual(self.new[p],v,p)
    def test_pure_original_five_egg_server_score_unmodified(self):
        self.assertEqual(sha(self.new["server/H2FiveEggRules.luau"]),
                         "0999d69391c176b9b95b04c5444d822e63d7ce04")
    def test_single_real_authority(self):self.assertEqual(len([p for p in self.new if p.endswith("/Game.server.luau")]),1)
    def test_single_remote_all_actions_same_seq(self):
        self.assertEqual(self.game.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertEqual(self.game.count('remote.OnServerEvent:Connect('),1)
    def test_full_contract(self):contract(self.game,self.hud,self.vote)
    def test_default_classic_in_both_lobby_and_no_vote(self):
        self.assertIn("local EXPERIMENTAL_FIVE_EGG_MODE = false",self.game)
        self.assertIn("else R.CLASSIC",self.vote)
    def test_mode_switch_only_on_round_reset(self):
        self.assertEqual(self.game.count("EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE"),1)
        start=self.game.index("local function resetRound()")
        end=self.game.index("local function chooseTeam(",start)
        self.assertIn("ModeVote.tally(modeVotes,Players:GetPlayers())",self.game[start:end])
    def test_score_mode_server_studio_only(self):self.assertIn("RunService:IsStudio() and chosenMode==ModeVote.SCORE",self.game)
    def test_new_three_eggs_have_neutral(self):
        for ident in ("R2","B2","N1"):self.assertIn(ident,self.game)
        self.assertIn('if RunService:IsStudio() then\n    for _,id in ipairs({"R2","B2","N1"})',self.game)
    def test_voters_only_lobby_or_countdown(self):self.assertIn('phase~="LOBBY" and phase~="COUNTDOWN"',self.vote)
    def test_monotonic_seq_same_hud(self):self.assertEqual(self.hud.count("local seq = 0"),1)
    def test_mode_switch_delayed_until_next_game(self):
        self.assertIn('    elseif match.phase == "COUNTDOWN" then',self.game)
        self.assertIn('if now >= match.phaseUntil then resetRound() end',self.game)
    def test_vote_counts_not_client_owned(self):
        self.assertIn("ModeVote.tally(modeVotes,Players:GetPlayers())",self.game)
        self.assertNotIn('data.scores',self.game)
    def test_private_studio_not_publishable(self):
        x=json.loads((NEW/"SOURCE_LOCK.json").read_text())
        for key in ("real_studio_2client_tested","mobile_tested","fun_gate_accepted",
                    "official_RC_adopted","published","paid",
                    "hatch_owned_equip_real_gameplay_implemented"):
            self.assertIs(x[key],False,key)
    def test_original_sky_sea_beast_remain(self):
        self.assertIn("TacticalAlternativeRoute",self.new["server/H1FunWorld.server.luau"].decode())
        self.assertIn('Models.create("SPACE",creatures)',self.new["server/H1FunWorld.server.luau"].decode())
    def test_5_egg_score_native_rules_original(self):
        self.assertIn('Rules.LENGTH_SECONDS = 240',self.new["server/H2FiveEggRules.luau"].decode())
    def test_mutant_invalid_nonstudio_enabled_rejected(self):
        with self.assertRaises(AssertionError):
            contract(self.game.replace('RunService:IsStudio() and chosenMode==ModeVote.SCORE',
                'chosenMode==ModeVote.SCORE'),self.hud,self.vote)
    def test_mutant_active_mode_voting_rejected(self):
        with self.assertRaises(AssertionError):
            contract(self.game,self.hud,self.vote.replace(
                'if phase~="LOBBY" and phase~="COUNTDOWN" then return false end',
                'if phase=="RESULTS" then return false end'))
    def test_mutant_tie_defaults_5eggs_rejected(self):
        with self.assertRaises(AssertionError):
            contract(self.game,self.hud,self.vote.replace("if five>classic","if five>=classic"))
    def test_mutant_client_secondary_seq_rejected(self):
        with self.assertRaises(AssertionError):
            contract(self.game,self.hud+"local seq = 0",self.vote)
    def test_mutant_new_authority_rejected(self):
        with self.assertRaises(AssertionError):
            contract(self.game+'remote.Name = "TrapRaidersS1Remote"',self.hud,self.vote)
    def test_mutant_unrestricted_client_mode_rejected(self):
        with self.assertRaises(AssertionError):
            contract(self.game,self.hud.replace('and s.modeScoreAvailable==true',
                              'and true'),self.vote)
    def test_mutant_vote_replay_disabler_rejected(self):
        with self.assertRaises(AssertionError):
            contract(self.game.replace('Rules.validSeq(data.seq,lastSeq[player] or 0)',
                                       'data.seq~=nil'),self.hud,self.vote)
if __name__=="__main__":unittest.main()
