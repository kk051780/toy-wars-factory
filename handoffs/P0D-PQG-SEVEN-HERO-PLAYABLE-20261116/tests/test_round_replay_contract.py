"""EGGRUMBLE V3 round lifecycle regression; source contracts, not Roblox Studio play.
No second game owner, score system or lobby GUI is allowed.
"""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LOBBY=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text("utf-8")
REPLAY=(ROOT/"EGGRUMBLE_RoundReplay.luau").read_text("utf-8")
RESULT=(ROOT/"EGGRUMBLE_MatchResultService.luau").read_text("utf-8")
PROJECT=json.loads((ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text("utf-8"))

class RoundReplayContract(unittest.TestCase):
    def test_replay_only_after_results_and_real_winner(self):
        self.assertIn('session.rules.phase~="FINISHED"',REPLAY)
        self.assertIn("session.rules.winner==nil then return false end",REPLAY)
        self.assertIn("session.roundReplayScheduled=true",REPLAY)
        self.assertIn("RoundReplay.schedule(session,session.closeRound)",LOBBY)
        result=LOBBY.index("ResultService.showIfFinished(session,queue,mode)")
        replay=LOBBY.index("RoundReplay.schedule(session,session.closeRound)")
        self.assertLess(result,replay)

    def test_hold_result_before_releasing_player(self):
        self.assertIn("Replay.RESULT_HOLD_SECONDS=10",REPLAY)
        self.assertIn("local DISPLAY_SECONDS=8",RESULT)
        self.assertIn("task.delay(Replay.RESULT_HOLD_SECONDS,function()",REPLAY)
        self.assertIn("if session.rules.phase==\"FINISHED\" then closeRound() end",REPLAY)

    def test_requeue_modes_are_independent_and_old_round_cannot_wipe_new(self):
        for line in ("if sessions[mode]~=session or (not abandoned and session.rules.phase~=\"FINISHED\") then return end",
                     "sessions[mode]=nil","queues[mode]={}","queueEpoch[mode]+=1",
                     "local expectedEpoch=queueEpoch[mode]",
                     "RoundReplay.canStartCountdown(mode,expectedEpoch,queues,queueEpoch,sessions)"):
            with self.subTest(line=line):
                self.assertIn(line,LOBBY)
        self.assertNotIn("sessions={}",LOBBY)
        self.assertNotIn("queues={TEAM={},BATTLE_ROYALE={}}\n  -- reset",LOBBY)

    def test_lifecycle_callbacks_disconnected_after_round(self):
        self.assertIn("lifeConnections={},",LOBBY)
        self.assertIn("connection:Disconnect()",LOBBY)
        self.assertIn("table.insert(session.lifeConnections,humanoid.Died:Connect(function()",LOBBY)
        self.assertIn("table.insert(session.lifeConnections,player.CharacterAdded:Connect(bindCarrierLife))",LOBBY)
        self.assertIn("table.insert(session.lifeConnections,p.CharacterAdded:Connect(function(character)",LOBBY)
        self.assertIn("session.world:Destroy()",LOBBY)

    def test_saved_role_options_remain_but_match_attributes_reset(self):
        self.assertIn("SevenRoleCombat.clear(player)",LOBBY)
        self.assertIn("InteractionGuard.clear(player)",LOBBY)
        self.assertIn("local loaded=pcall(function() p:LoadCharacter() end)",REPLAY)
        self.assertIn("if not loaded then",REPLAY)
        self.assertIn("task.delay(1,function()",REPLAY)
        self.assertIn('p:GetAttribute("EGGRUMBLE_QueuedMode")~=nil',REPLAY)
        self.assertIn("if alive and alive.Health>0 then return end",REPLAY)
        self.assertIn("RoundReplay.resetHuman(player,root+Vector3.new(0,8,-5),session.walkBaseline[tostring(player.UserId)])",LOBBY)
        self.assertIn('p:SetAttribute("EGGRUMBLE_QueuedMode",nil)',REPLAY)
        self.assertIn('p:SetAttribute("EGGRUMBLE_Eliminated",nil)',REPLAY)
        self.assertIn('p:SetAttribute("EGGRUMBLE_NeutralKOs",0)',REPLAY)
        self.assertIn('p:SetAttribute("EGGRUMBLE_SlashEvolution","BASE")',REPLAY)
        self.assertIn('ko.Value=0',REPLAY)
        self.assertNotIn('p:SetAttribute("EGGRUMBLE_SelectedRole",nil)',REPLAY)

    def test_last_human_disconnect_abandons_only_orphaned_ai_session(self):
        self.assertIn("function Replay.abandonIfEmpty(", REPLAY)
        self.assertIn('if session.rules.phase~="ACTIVE" or session.roundReplayScheduled then return false end', REPLAY)
        self.assertIn("Players:GetPlayerByUserId(userId)", REPLAY)
        self.assertIn("joined[userId]==session.mode", REPLAY)
        self.assertIn('if abandoned then session.rules.phase="ABANDONED" end', LOBBY)
        self.assertIn("RoundReplay.abandonIfEmpty(scene,joined,function()", LOBBY)
        self.assertIn("scene.closeRound(true)", LOBBY)
        self.assertIn("if not abandoned and scene.takeover then", LOBBY)
        self.assertIn("if session.world.Parent then session.world:Destroy() end", LOBBY)
        self.assertNotIn("session.rules.winner=\"AI_1\"", LOBBY)

    def test_gate_toggle_and_mode_switch_without_extra_hud(self):
        self.assertIn("function Replay.leaveWaitingQueue(",REPLAY)
        self.assertIn("function Replay.canStartCountdown(",REPLAY)
        self.assertIn("if sessions[mode] or joined[p.UserId]~=mode then return false end",REPLAY)
        self.assertIn("if #q==0 then",REPLAY)
        self.assertIn("queueEpoch[mode]=(queueEpoch[mode] or 0)+1",REPLAY)
        self.assertIn("queueEpoch[mode]==expectedEpoch",REPLAY)
        self.assertIn("sessions[mode]==nil and waiting~=nil and #waiting>0",REPLAY)
        self.assertIn("if sessions[previous] then return end",LOBBY)
        self.assertIn("RoundReplay.leaveWaitingQueue(previous,p,queues,joined,queueEpoch,sessions)",LOBBY)
        self.assertIn("if previous==mode then return end",LOBBY)
        self.assertIn("RoundReplay.leaveWaitingQueue(mode,p,queues,joined,queueEpoch,sessions)",LOBBY)
        self.assertIn('p:SetAttribute("EGGRUMBLE_QueuedMode",nil)',LOBBY)
        self.assertIn('チーム戦（再操作で解除）',LOBBY)
        self.assertIn('BR戦（再操作で解除）',LOBBY)
        self.assertNotIn("ScreenGui",REPLAY)
        self.assertNotIn("RemoteEvent",REPLAY)

    def test_live_avatar_returns_to_the_original_castle(self):
        # One original server-owned reentry path, no duplicate weapon or castle.
        self.assertIn("function Replay.returnToActiveCastle(",REPLAY)
        self.assertIn("p.Character~=character",REPLAY)
        self.assertIn('session.rules.phase~="ACTIVE"',REPLAY)
        self.assertIn("not session.world.Parent",REPLAY)
        self.assertIn("not castle.alive or not session.castleLocations[id]",REPLAY)
        self.assertIn('character:FindFirstChildOfClass("Humanoid")',REPLAY)
        self.assertIn('character:FindFirstChild("HumanoidRootPart")',REPLAY)
        self.assertIn("root.CFrame=CFrame.new(arrival)",REPLAY)
        self.assertIn("sessions[mode]==session and session.rules.phase==\"ACTIVE\"",LOBBY)
        self.assertIn("local home=session.castleLocations[id]",LOBBY)
        self.assertIn('character:WaitForChild("HumanoidRootPart",5)',LOBBY)
        arrive="RoundReplay.returnToActiveCastle(session,p,character,home+Vector3.new(0,7,-45))"
        self.assertIn(arrive,LOBBY)
        n=LOBBY.index(arrive)
        self.assertIn("SevenRoleCombat.equip(session,p,role)",LOBBY[n:n+130])
        self.assertNotIn("RemoteEvent",REPLAY)

    def test_previous_match_item_shield_dash_and_debuff_do_not_transfer(self):
        self.assertIn("function Replay.captureWalkBaseline(",REPLAY)
        self.assertIn("session.walkBaseline[tostring(p.UserId)]=RoundReplay.captureWalkBaseline(p)",LOBBY)
        self.assertIn("walkBaseline={}",LOBBY)
        self.assertIn('ch:FindFirstChild("EGGRUMBLE_ItemShield")',REPLAY)
        self.assertIn('shield:IsA("ForceField")',REPLAY)
        self.assertIn("shield:Destroy()",REPLAY)
        self.assertIn("hum.WalkSpeed=original",REPLAY)
        self.assertIn('hum:SetAttribute("EGGRUMBLE_OriginalWalkSpeed",nil)',REPLAY)
        self.assertIn('hum:SetAttribute("EGGRUMBLE_SlowExpiry",nil)',REPLAY)
        self.assertIn('hum:SetAttribute("EGGRUMBLE_MarkedUntil",nil)',REPLAY)
        self.assertIn("baseWalkSpeed<=32",REPLAY)
        self.assertNotIn("MarketplaceService",REPLAY)

    def test_single_rojo_game_host_and_no_remote_or_stores(self):
        scripts=PROJECT["tree"]["ServerScriptService"]
        self.assertEqual(scripts["EGGRUMBLE_RoundReplay"]["$path"],"EGGRUMBLE_RoundReplay.luau")
        self.assertEqual(sum(x=="EGGRUMBLE_LobbyCastleModesPreview" for x in scripts),1)
        self.assertNotIn("Game",scripts)
        for forbidden in ("RemoteEvent","DataStoreService","MarketplaceService",
                          "TeleportService","PromptProductPurchase"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,REPLAY)
        self.assertIn('assert(RunService:IsStudio()',REPLAY)

if __name__=="__main__":
    unittest.main()
