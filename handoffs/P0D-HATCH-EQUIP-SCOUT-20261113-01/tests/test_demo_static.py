"""Static Rojo + authority invariants for private 2-client scout demo.
This is NOT engine QA, native Luau compilation or live economy testing.
"""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SERVER=(ROOT/"demo/ScoutArena.server.luau").read_text(encoding="utf-8")
CLIENT=(ROOT/"demo/ScoutArena.client.luau").read_text(encoding="utf-8")
POLICY=(ROOT/"src/RewardEquipRules.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"default.project.json").read_text(encoding="utf-8"))

class PrivateDemoStaticQA(unittest.TestCase):
    def test_rojo_mapping_real_sources(self):
        tree=PROJECT["tree"]
        paths=[
            tree["ServerScriptService"]["RewardEquipRules"]["$path"],
            tree["ServerScriptService"]["ScoutArena"]["$path"],
            tree["StarterPlayer"]["StarterPlayerScripts"]["ScoutArena"]["$path"],
        ]
        self.assertEqual(len(paths),len(set(paths)))
        self.assertEqual(set(paths),{
            "src/RewardEquipRules.luau",
            "demo/ScoutArena.server.luau",
            "demo/ScoutArena.client.luau",
        })
        self.assertTrue(all((ROOT/path).is_file() for path in paths))

    def test_studio_only_server_and_client(self):
        self.assertIn('if not RunService:IsStudio() then return end',SERVER)
        self.assertIn('if not RunService:IsStudio() then return end',CLIENT)

    def test_no_money_data_or_game_deployment(self):
        banned=("MarketplaceService","PromptProductPurchase","ProcessReceipt",
                "DataStoreService","SetAsync","UpdateAsync","PublishAsync","TeleportService")
        for term in banned:
            with self.subTest(term=term):
                self.assertNotIn(term,SERVER+CLIENT)

    def test_one_server_rules_owner(self):
        self.assertIn('local Rules = require(script.Parent:WaitForChild("RewardEquipRules"))',SERVER)
        self.assertNotIn('require(',CLIENT)

    def test_no_client_hatch_claim(self):
        self.assertNotIn('FireServer("HATCH"',CLIENT)
        self.assertNotIn('FireServer("REWARD"',CLIENT)
        self.assertNotIn('FireServer("FINISH"',CLIENT)
        self.assertIn('Rules.claimFreeHatch(s,uid,epoch,prng:NextInteger(1,10000))',SERVER)

    def test_server_receipt_idempotence(self):
        self.assertIn("if p.receipts[epoch] then",POLICY)
        self.assertIn("p.receipts[epoch]=item",POLICY)

    def test_server_authorized_eq_class(self):
        self.assertIn('Rules.equip(s,uid,arg,"BEASTMASTER")',SERVER)
        self.assertIn("if not ITEMS[item] or not p.owned[item]",POLICY)
        self.assertIn('s.phase~="LOBBY"',POLICY)

    def test_scout_cooldown_bound_to_round(self):
        self.assertIn('if s.phase~="ACTIVE" or s.epoch~=epoch',POLICY)
        self.assertIn('p.nextUseAt=now+COOLDOWN',POLICY)
        self.assertIn('COOLDOWN = 18',POLICY)

    def test_server_3d_visual_replication(self):
        self.assertIn('Instance.new("Model")',SERVER)
        self.assertIn('model.Parent=map',SERVER)
        self.assertIn('model:PivotTo(CFrame.new(nextPos))',SERVER)
        self.assertIn('Instance.new("Highlight")',SERVER)

    def test_real_counterplay_enemy_and_range(self):
        self.assertIn('prompt.Triggered:Connect(function(actor)',SERVER)
        self.assertIn('teams[actorUid]==teams[uid]',SERVER)
        self.assertIn('(actorRoot.Position-model:GetPivot().Position).Magnitude>9',SERVER)

    def test_safe_rare_egg_holder_authority(self):
        self.assertIn('rarePrompt.Triggered:Connect(function(actor)',SERVER)
        self.assertIn('s.phase~="ACTIVE" or rareHolderId',SERVER)
        self.assertIn('rare[uid]=(rareHolderId==uid)',SERVER)
        self.assertIn('if not root or not humanoid or humanoid.Health<=0 then',SERVER)

    def test_rare_hatch_probability_owned_server(self):
        self.assertIn('rnd.special[uid] and 500 or 50',POLICY)
        self.assertIn('rare[uid]=(rareHolderId==uid)',SERVER)
        self.assertIn('prng:NextInteger(1,10000)',SERVER)

    def test_mobile_buttons_real_click_callbacks(self):
        self.assertIn('summon.MouseButton1Click:Connect',CLIENT)
        self.assertIn('equip.MouseButton1Click:Connect',CLIENT)
        self.assertIn('event:FireServer("SCOUT")',CLIENT)
        self.assertIn('event:FireServer("EQUIP",target)',CLIENT)

    def test_no_unbounded_detection_spam(self):
        self.assertIn('if not entry.detected then',SERVER)
        self.assertIn('entry.detected=false',SERVER)

    def test_missing_character_does_not_consume_scout(self):
        self.assertRegex(SERVER, r'if not getRoot\(player\) then[\s\S]*?return[\s\S]*?Rules\.requestScout')

    def test_countdown_requires_two_players(self):
        self.assertIn('if #allPlayers()>=2 and s.phase=="LOBBY" then',SERVER)

    def test_round_and_hatch_remain_server_only(self):
        self.assertIn('Rules.startRound(s,epoch)',SERVER)
        self.assertIn('Rules.finishRound(s,epoch,eligible,rare)',SERVER)
        self.assertNotIn('Rules.finishRound',CLIENT)

if __name__=="__main__":
    unittest.main(verbosity=2)
