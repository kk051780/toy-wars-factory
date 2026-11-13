"""Source-only guards for distinct private evolution action demo.
NOT genuine native compiler, Roblox Studio, network replication or owner FUN.
"""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
POLICY=(ROOT/"src/EvolutionRules.luau").read_text(encoding="utf-8")
SERVER=(ROOT/"battle/EvolutionCombat.server.luau").read_text(encoding="utf-8")
CLIENT=(ROOT/"battle/EvolutionCombat.client.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"battle.project.json").read_text(encoding="utf-8"))

class EvolutionBattleStatic(unittest.TestCase):
    def test_private_game_hard_gates(self):
        self.assertIn("if not RunService:IsStudio() then return end",SERVER)
        self.assertIn("if not RunService:IsStudio() then return end",CLIENT)

    def test_no_original_game_authority(self):
        for forbidden in ("TrapRaidersS1Remote","Game.server.luau","DataStoreService",
                          "MarketplaceService","ProcessReceipt","PublishAsync",
                          "UpdateAsync","TeleportService"):
            with self.subTest(term=forbidden):
                self.assertNotIn(forbidden,SERVER+CLIENT)

    def test_one_isolated_remote(self):
        self.assertIn('remote.Name="EggRumbleEvolutionPvEDemoOnly"',SERVER)
        self.assertIn('ReplicatedStorage:WaitForChild("EggRumbleEvolutionPvEDemoOnly",15)',CLIENT)
        self.assertNotIn("RequestHatch",CLIENT)

    def test_rojo_single_policy_server_and_client(self):
        t=PROJECT["tree"]
        self.assertEqual(t["ServerScriptService"]["EvolutionRules"]["$path"],
                         "src/EvolutionRules.luau")
        self.assertEqual(t["ServerScriptService"]["EvolutionCombat"]["$path"],
                         "battle/EvolutionCombat.server.luau")
        self.assertEqual(t["StarterPlayer"]["StarterPlayerScripts"]["EvolutionCombat"]["$path"],
                         "battle/EvolutionCombat.client.luau")
        for f in ("src/EvolutionRules.luau","battle/EvolutionCombat.server.luau",
                  "battle/EvolutionCombat.client.luau"):
            self.assertTrue((ROOT/f).is_file())

    def test_only_server_uses_real_evolution_policy(self):
        self.assertIn('E=require(script.Parent:WaitForChild("EvolutionRules"))',SERVER)
        self.assertNotIn("EvolutionRules",CLIENT)

    def test_reward_not_real_and_preview_warning(self):
        self.assertIn("SIMULATED server-certified progression",SERVER)
        self.assertIn("No real match/earned shards/XP",SERVER)
        self.assertIn("STUDIO専用の実戦試作",CLIENT)

    def test_preview_must_be_whitelisted(self):
        self.assertIn('if action=="PREVIEW" then',SERVER)
        self.assertIn('if not selection then return end',SERVER)
        self.assertIn('if now()-st.lastSelect<1 then return end',SERVER)

    def test_uses_real_policy_for_evolution(self):
        self.assertIn('E.creditRound(profile,',SERVER)
        self.assertIn('E.evolve(profile,"forest_scout"',SERVER)
        self.assertIn('E.form(profile,"forest_scout",owned)',SERVER)

    def test_two_branch_two_stage_preview(self):
        for stage in ("ASSAULT2","GUARD2","ASSAULT3","GUARD3"):
            with self.subTest(stage=stage):
                self.assertIn(stage,SERVER)
                self.assertIn(stage,CLIENT)

    def test_no_client_arbitrary_level(self):
        self.assertNotIn('FireServer("XP"',CLIENT)
        self.assertNotIn('FireServer("LEVEL"',CLIENT)
        self.assertNotIn('FireServer("FRAGMENTS"',CLIENT)
        self.assertIn('remote:FireServer("PREVIEW",opt.key)',CLIENT)
        self.assertIn('remote:FireServer("CAST")',CLIENT)

    def test_cast_guarded_by_real_evolution_form(self):
        self.assertIn("st.form.stage<2",SERVER)
        self.assertIn("form.formId~=st.form.formId",SERVER)
        self.assertIn('form.category~="BEAST"',SERVER)

    def test_cast_has_real_server_cooldown(self):
        self.assertIn("if now()-st.lastCast<12 then",SERVER)
        self.assertIn("st.lastCast=now()",SERVER)

    def test_assault_only_targets_npc_models(self):
        self.assertIn('npc:SetAttribute("EvolutionStudioTrainingNPC",true)',SERVER)
        self.assertIn('entry.humanoid:TakeDamage(',SERVER)
        self.assertIn("for _,entry in pairs(living) do",SERVER)
        self.assertNotIn("player.Character.Humanoid:TakeDamage",SERVER)

    def test_assault_has_bounded_aoe(self):
        self.assertIn("local radius=if form.stage>=3 then 25 else 17",SERVER)
        self.assertIn("(entry.pos-origin).Magnitude<=radius",SERVER)
        self.assertIn("MaxHealth=60",SERVER)

    def test_guard_effect_blocks_castle_damage(self):
        self.assertIn('if form.branch=="ASSAULT" then',SERVER)
        self.assertIn('elseif form.branch=="GUARD" then',SERVER)
        self.assertIn("shieldHits-=1",SERVER)
        self.assertIn("castleHealth=math.max(0,castleHealth-7)",SERVER)

    def test_guard_bounded_hits_and_duration(self):
        self.assertIn("shieldHits=if form.stage>=3 then 5 else 3",SERVER)
        self.assertIn("shieldUntil=now()+8",SERVER)
        self.assertIn("if shieldHits==0 then clearShield() end",SERVER)

    def test_no_ability_doubles_pvp_multiplier(self):
        self.assertIn("additionalPvpStatMultiplier=0",POLICY)
        self.assertNotIn("PlayerHumanoid:TakeDamage",SERVER)

    def test_npcs_bounded(self):
        self.assertIn("local maxNpcs=14",SERVER)
        self.assertIn("if liveCount()>=maxNpcs then return end",SERVER)

    def test_state_always_from_server(self):
        self.assertIn('remote:FireClient(player,kind,data)',SERVER)
        self.assertIn('if kind=="STATE" and type(payload)=="table"',CLIENT)

    def test_rare_collectible_unaffected(self):
        self.assertNotIn("DataStore",CLIENT)
        self.assertNotIn("ownedItems",CLIENT)
        self.assertNotIn("Purchase",CLIENT)

    def test_server_pve_objective_fort_has_health(self):
        self.assertIn("local castleHealth=120",SERVER)
        self.assertIn('fortText.Text="城のHP "',SERVER)
        self.assertIn("castleHealth<=0",SERVER)

    def test_original_source_is_not_modified_here(self):
        self.assertIn("function E.evolve(",POLICY)
        self.assertIn("function E.switchBranch(",POLICY)
        self.assertIn('modelId="NOT_INTEGRATED"',POLICY)

if __name__=="__main__":
    unittest.main(verbosity=2)
