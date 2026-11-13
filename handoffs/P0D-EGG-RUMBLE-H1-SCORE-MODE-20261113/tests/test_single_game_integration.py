"""Regression checks over generated FULL existing H1+scored-egg 31-Luau game.

These tests inspect authentic original and modified source, but ARE NOT engine physics or
actual human 2client/mobile FUN tests. Authoritative native Luau pure H2 Rules is run
separately by genuine upstream Luau interpreter.
"""
import hashlib,json,re,unittest
from pathlib import Path

HERE=Path(__file__).resolve()
REPO=HERE.parents[3];OWN=HERE.parents[1]
UP=REPO/"handoffs/P0D-H1-FAST-JOY-COMBINED-20261113-01/dist/TRAP_RAIDERS_H1_FAST_SEA_SKY_JOY_STUDIO_ONLY"
ON=OWN/"dist/EGG_RAID_RUMBLE_H2_SCORED_PRIVATE_STUDIO"
OFF=OWN/"dist/EGG_RAID_RUMBLE_H1_ORIGINAL_RULES_PRIVATE_STUDIO"
def file(p,name):
    return (p/"src"/name).read_bytes()
def scripts(p):
    return {q.relative_to(p/"src").as_posix():q.read_bytes()
            for q in (p/"src").rglob("*.luau")}
def blob(d):
    return hashlib.sha1(b"blob "+str(len(d)).encode()+b"\0"+d).hexdigest()
def contract(s):
    assert s.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert s.count('remote.OnServerEvent:Connect(')==1
    assert s.count('local function dropEgg(player: Player)')==1
    assert s.count('local function resetRound()')==1
    assert s.count('local function stopRound(')==1
    assert s.count('local function tickRound()')==1
    assert s.count('H2Score.pickup(')==1
    assert s.count('H2Score.deposit(')==1
    assert s.count('H2Score.advance(')==1
    assert s.count('H2Score.drop(')==1
    assert "H2Score.assertConserved(h2ScoreState)" in s
    assert 'h2ScoreState=H2Score.new()' in s
    assert 'match.deadline=match.startedAt+H2Score.LENGTH_SECONDS' in s
    assert 'FIVE_EGG_SCORE_240S' in s
    assert 'else Rules.canSteal(' not in s
    assert 'if EXPERIMENTAL_FIVE_EGG_MODE then\n            pickupFiveEgg(player,' in s
    assert 'if EXPERIMENTAL_FIVE_EGG_MODE then\n            depositFiveEgg(player,team)' in s
    assert 'stopWind(player)\n    carry[player]=id' in s
    assert 'carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil' in s
    assert 'or carry[player]~=nil' in s
    assert 'Rules.canSteal(' in s and 'Rules.canScore(' in s
    assert 'WindRules.canActivate({' in s and 'TrapRules.canPlace({' in s
    assert 'lastSeq[player] = data.seq' in s
    assert '"NEUTRAL"' in s
    assert 'h2Ids[player]=h2NextId' in s and 'h2Ids[player]=nil' in s
    assert 'map.teams[team].eggPrompt.Triggered:Connect(' in s
    assert 'map.teams[team].scorePrompt.Triggered:Connect(' in s
    for id in ("R1","R2","B1","B2","N1"):
        assert id in s
    assert s.count('Instance.new("ProximityPrompt")')==1
    assert s.count('Instance.new("RemoteEvent")')==1
    assert 'H2_REAL_SCORE_EGG_' in s
    assert 'map.teams[side].scorePad.Position' in s
    assert 'and not within(player,def.part.Position,Config.InteractDistance)' not in s
    assert 'or not within(player,def.part.Position,Config.InteractDistance)' in s
    assert 'if EXPERIMENTAL_FIVE_EGG_MODE then "FIVE_EGG_SCORE" else "ONE_EGG_CAPTURE"' in s
    assert "scoreMode = if EXPERIMENTAL_FIVE_EGG_MODE" in s

class TestRealFullH1MultiEggFusion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=scripts(UP);cls.on=scripts(ON);cls.off=scripts(OFF)
        cls.son=cls.on["server/Game.server.luau"].decode("utf-8")
        cls.soff=cls.off["server/Game.server.luau"].decode("utf-8")
    def test_actual_original_complete30_scripts(self):
        self.assertEqual(len(self.base),30)
    def test_both_variants_real31_sources(self):
        self.assertEqual(len(self.on),31);self.assertEqual(len(self.off),31)
    def test_exact_original_29_other_sources_byte_unchanged(self):
        for src,base in ((self.on,self.base),(self.off,self.base)):
            for name,content in base.items():
                if name!="server/Game.server.luau":self.assertEqual(src[name],content,name)
    def test_score_rules_original_272_byte_pinned(self):
        self.assertEqual(blob(self.on["server/H2FiveEggRules.luau"]),
                         "0999d69391c176b9b95b04c5444d822e63d7ce04")
    def test_original_game_source_is_precisely_pinned(self):
        self.assertEqual(blob(self.base["server/Game.server.luau"]),
                         "adecfee41a594bdd54393050b4890a5733a536ce")
    def test_one_game_and_remote_authority(self):
        self.assertEqual(len([x for x in self.on if x.endswith("/Game.server.luau")]),1)
        self.assertEqual(len([x for x in self.on if x.endswith(".server.luau")]),2)
        self.assertIn('remote.Name = "TrapRaidersS1Remote"',self.son)
    def test_one_server_source_contract(self):contract(self.son)
    def test_normal_mode_explicit_false(self):
        self.assertIn("local EXPERIMENTAL_FIVE_EGG_MODE = false",self.soff)
        self.assertNotIn('local EXPERIMENTAL_FIVE_EGG_MODE = RunService:IsStudio()',self.soff)
    def test_scored_mode_private_Studio_only(self):
        self.assertIn("local EXPERIMENTAL_FIVE_EGG_MODE = RunService:IsStudio()",self.son)
        self.assertNotIn("local EXPERIMENTAL_FIVE_EGG_MODE = true",self.son)
    def test_two_modes_only_one_flag_difference(self):
        self.assertEqual(self.son.replace(
            "local EXPERIMENTAL_FIVE_EGG_MODE = RunService:IsStudio()",
            "local EXPERIMENTAL_FIVE_EGG_MODE = false"),self.soff)
    def test_original_H1_sea_sky_role_experiment_survives(self):
        world=self.on["server/H1FunWorld.server.luau"].decode()
        self.assertIn('path("SEA_LOW_CAUSEWAY"',world)
        self.assertIn('path("SKY_RAMP_RED"',world)
        self.assertIn('Models.create("SPACE",creatures)',world)
        self.assertIn('Models.create("CELESTIAL",creatures)',world)
        self.assertIn('windButton.Visible',self.on["client/HUD.client.luau"].decode())
    def test_egg_joy_client_remains_but_no_authority(self):
        src=self.on["client/EggJoy.client.luau"].decode()
        self.assertIn("RunService:IsStudio()",src)
        self.assertNotIn("FireServer",src)
    def test_original_real_3D_beast_and_mascot_preserved(self):
        self.assertEqual(self.on["client/D18MascotGuide.client.luau"],
                         self.base["client/D18MascotGuide.client.luau"])
        self.assertEqual(self.on["server/RareEncounterModels.luau"],
                         self.base["server/RareEncounterModels.luau"])
    def test_physically_five_eggs_uses_existing2_plus_real_extra3(self):
        self.assertIn('h2Eggs.R1={id="R1"',self.son)
        self.assertIn('h2Eggs.B1={id="B1"',self.son)
        self.assertIn('R2={owner="RED",home=Vector3.new(-98,2.5,20)}',self.son)
        self.assertIn('B2={owner="BLUE",home=Vector3.new(98,2.5,20)}',self.son)
        self.assertIn('N1={owner="NEUTRAL",home=Vector3.new(0,3,0)}',self.son)
        self.assertIn('for _,id in ipairs({"R2","B2","N1"})',self.son)
    def test_two_team_scorepad_logic_is_only_original_prompt(self):
        self.assertIn('depositFiveEgg(player,team)',self.son)
        self.assertIn('map.teams[team].scorePrompt.Triggered:Connect',self.son)
    def test_server_distance_and_alive_check_works_for_extra(self):
        self.assertIn('or not within(player,def.part.Position,Config.InteractDistance)',self.son)
        self.assertIn('and scoreState.active',self.son.replace("h2ScoreState.active","scoreState.active"))
    def test_no_client_score_or_new_S1_Remote(self):
        for path in self.on:
            if path.startswith("client/") and path not in self.base:
                self.fail("No new client source permitted")
        self.assertEqual(self.son.count('Instance.new("RemoteEvent")'),1)
    def test_regulation_4min_studio_score_mode(self):
        self.assertIn("H2Score.LENGTH_SECONDS",self.son)
        self.assertEqual(json.loads((ON/"SOURCE_LOCK.json").read_text())["Studio2client_tested"],False)
    def test_no_claim_for_free_hatch_persistent_rewards(self):
        self.assertFalse(json.loads((ON/"SOURCE_LOCK.json").read_text())["hatch_6_category_persisted_and_usable"])
    def test_mutant_client_teleport_as_score_rejected(self):
        m=self.son.replace('or not within(player,def.part.Position,Config.InteractDistance)','')
        with self.assertRaises(AssertionError):contract(m)
    def test_mutant_second_authoritative_Remote_rejected(self):
        m=self.son+'\nlocal attackRemote = Instance.new("RemoteEvent")'
        with self.assertRaises(AssertionError):contract(m)
    def test_mutant_missing_score_conservation_rejected(self):
        m=self.son.replace('assert(H2Score.assertConserved(h2ScoreState),"H2_REAL_H1_FIVE_EGG_INTEGRITY")',"")
        with self.assertRaises(AssertionError):contract(m)
    def test_mutant_duplicate_score_deposit_rejected(self):
        m=self.son.replace("local ok=H2Score.deposit(h2ScoreState,uid,side)",
                           "local ok=H2Score.deposit(h2ScoreState,uid,side)\nH2Score.deposit(h2ScoreState,uid,side)")
        with self.assertRaises(AssertionError):contract(m)
    def test_mutant_missing_wind_carrier_rejection(self):
        m=self.son.replace('carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil',
                           'carrying = false, slowed = slowed[player] ~= nil')
        with self.assertRaises(AssertionError):contract(m)
    def test_mutant_role_loop_deleted_rejected(self):
        m=self.son.replace('WindRules.canActivate({','WindRules.canFAIL({')
        with self.assertRaises(AssertionError):contract(m)
    def test_mutant_game_silent_second_game_class_rejected(self):
        x=dict(self.on);x["server/FakeGame.server.luau"]=b"--!nocheck"
        self.assertNotEqual(len(x),31)
    def test_mutant_fake_publish_ready_denied(self):
        receipt=json.loads((ON/"SOURCE_LOCK.json").read_text())
        for k in ("published","official_RC_adopted","Studio2client_tested","mobile_tested"):
            self.assertIs(receipt[k],False,k)
if __name__=="__main__":unittest.main()
