"""Source contract regression for Sourcery Oracle, phase and bounded NPC LOS.
Only this independent PREP child, not a Roblox engine test.
"""
import hashlib
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/"rc_fastlane/features/talking_npc"
class NPCSafetyAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=(F/"TalkingNPCRuntime.server.luau").read_text("utf8")
        cls.d=(F/"TalkingNPCDirector.luau").read_text("utf8")
        cls.lock=json.loads((F/"PREP_SOURCE_LOCK.json").read_text("utf8"))
    def test_sources_match_git_blobs(self):
        for name, expected in self.lock["files"].items():
            raw=(F/name).read_bytes()
            digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            self.assertEqual(digest,expected,name)
    def test_realm_hints_use_true_session_discovery(self):
        for t in ('"P0D_RealmHunt_Enabled"','"P0D_RealmHunt_" .. id',
                  '{"SKY", "SEA", "EMBER", "STAR"}',
                  '"P0D_RealmHunt_Complete"','facts.missingRealm = missing',
                  'facts.allRealmsComplete = true'):
            self.assertIn(t,self.r)
        self.assertNotIn('facts.secretTier = type(discovered)',self.r)
    def test_director_hint_completion_denies_fake_secret(self):
        self.assertIn('local place = REALM_NAMES[facts.missingRealm]',self.d)
        self.assertIn('facts.allRealmsComplete == true',self.d)
        self.assertNotIn('4つの秘境の印を集めると、不思議な光が現れる',self.d)
    def test_canonical_egg_prompt_phase_proxy(self):
        for t in ('local function matchLikelyActive()',
                  'arena:FindFirstChild(team .. "_CASTLE")',
                  'castle:FindFirstChild(team .. "_EGG")',
                  'prompt.Enabled == true',
                  'if not matchLikelyActive() then return nil end'):
            self.assertIn(t,self.r)
    def test_bounded_shared_raycast_budget(self):
        for t in ('MAX_ENEMY_CANDIDATES = 12','SCAN_RAYCAST_BUDGET = 24',
                  'MANUAL_RAYCAST_BUDGET = 6','quota.remaining -= 1',
                  'local quota = {remaining=SCAN_RAYCAST_BUDGET}',
                  'if quota.remaining <= 0 then break end',
                  'enemy, enemyRoot = observedEnemy, observedRoot',
                  'speak(player, "NAVI", "AUTO_ENEMY_ALERT", arena, enemy, enemyRoot)'):
            self.assertIn(t,self.r)
    def test_canonical_game_cannot_enable_egg_prompts_in_lobby(self):
        game=(ROOT/"releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau").read_text("utf8")
        map_builder=(ROOT/"releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau").read_text("utf8")
        self.assertIn('p.Enabled = false',map_builder)
        self.assertIn('eggPrompt = prompt(egg, "Steal egg"',map_builder)
        self.assertIn('map.teams[team].eggPrompt.Enabled = match.phase == "ACTIVE"',game)
        self.assertIn('map.teams[name].eggPrompt.Enabled = enabled and match.eggOwners[name] == nil',game)
        self.assertIn('match.phase = "LOBBY"',game)
    def test_original_authority_preserved(self):
        for token in ('Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                      'GetDataStore(','MarketplaceService'):
            self.assertNotIn(token,self.r)
        self.assertIn('active.remote:FireClient(player, {',self.r)
if __name__=="__main__":
    unittest.main()
