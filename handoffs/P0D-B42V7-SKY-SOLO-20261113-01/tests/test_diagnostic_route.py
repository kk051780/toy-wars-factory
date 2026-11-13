#!/usr/bin/env python3
"""Actual source-string contract for Studio-only read-only observable sky egg route.
Does not simulate Roblox engine, physics, human play, or prove route transport.
"""
import os, pathlib, re, unittest
ROOT=pathlib.Path(os.environ["P0D_SOLO_DIST"])/"src"
AUDIT=(ROOT/"client/P0DStudioTrialAudit.client.luau").read_text()
GAME=(ROOT/"server/Game.server.luau").read_text()
WORLD=(ROOT/"server/H1FunWorld.server.luau").read_text()
MAP=(ROOT/"server/MapBuilder.luau").read_text()

def safe(s):
    forbid=("FireServer(", "OnServerEvent:Connect(", "Instance.new(\"RemoteEvent\")",
            "DataStoreService", "MarketplaceService", "TeleportService",
            "PromptProductPurchase", "UserId", "GetFullName(")
    return ("if not RunService:IsStudio() then return end" in s
      and all(f not in s for f in forbid)
      and s.count("remote.OnClientEvent:Connect(")==1
      and "skyWithEggSerial==serial and activeSerial==serial" in s
      and "hum.FloorMaterial~=Enum.Material.Air" in s
      and "workspace:Raycast(pos,Vector3.new(0,-9,0),rayParams)" in s
      and "hit.Instance==deck" in s
      and "local previousCarry=lastCarry" in s
      and "qualifiesSkyScore(scoreRose,carry,previousCarry" in s
      and "invalidatesSkyRoute(skyWithEggSerial==serial" in s)

class OriginalSourceAndAudit(unittest.TestCase):
    def test_source_count_43(self):
        self.assertEqual(len(list(ROOT.rglob("*.luau"))),43)
    def test_one_server_game(self):
        self.assertEqual(len(list(ROOT.rglob("Game.server.luau"))),1)
    def test_no_new_server_authority(self):
        self.assertTrue(safe(AUDIT))
    def test_studio_guard_before_gui(self):
        self.assertLess(AUDIT.index("if not RunService:IsStudio() then return end"),
                        AUDIT.index('Instance.new("ScreenGui")'))
    def test_one_bounded_observer(self):
        self.assertIn("if n>=110 then return end",AUDIT)
        self.assertEqual(AUDIT.count("remote.OnClientEvent:Connect("),1)
    def test_original_snapshot_schema(self):
        for token in ('kind = "SNAPSHOT"', 'serial = match.serial',
                      'scores = {RED = match.scores.RED, BLUE = match.scores.BLUE}',
                      'carrying = if', 'scoreMode = if', 'first90 = first90',
                      'redPlayers = teamCount("RED")', 'bluePlayers = teamCount("BLUE")'):
            self.assertIn(token,GAME,token)
    def test_audit_parses_actual_snapshot(self):
        for token in ('msg.kind~="SNAPSHOT"', 'msg.serial','msg.team',
                      'msg.carrying','msg.scores[team]', 'msg.scoreMode',
                      'msg.first90','msg.phase'):
            self.assertIn(token,AUDIT,token)
    def test_original_team_and_egg_authority_preserved(self):
        for token in ('remote.OnServerEvent:Connect(', 'scorePrompt.Triggered:Connect',
                      'Rules.canScore(', 'match.scores[team] += 1'):
            self.assertIn(token,GAME,token)
    def test_replicated_world_is_original(self):
        self.assertIn('world.Name="H1_FUN_WORLD"',WORLD)
        self.assertIn('local fort=box("FLOATING_SKY_ISLAND",Vector3.new(50,8,20)',WORLD)
        self.assertIn("Vector3.new(0,28,49),rgb(103,194,151),true",WORLD)
    def test_actual_objective_names(self):
        for token in ('base.Name = name .. "_CASTLE"', 'name .. "_EGG"',
                      'name .. "_SCORE_PAD"', 'Instance.new("ProximityPrompt")'):
            self.assertIn(token,MAP,token)
    def test_gui_noninteractive(self):
        for token in ('label.Active=false', 'screen.ResetOnSpawn=false',
                      'label.TextWrapped=true', 'Instance.new("ScreenGui")'):
            self.assertIn(token,AUDIT,token)
    def test_egg_on_floor_client_observation(self):
        for token in ('and lastCarry~=""', 'hum.Health>0',
                      'hum.FloorMaterial~=Enum.Material.Air',
                      'skyWithEggSerial=lastSerial', 'pos.Y>=top+1',
                      'pos.Y<=top+6'):
            self.assertIn(token,AUDIT,token)
    def test_sky_segment_same_match_only(self):
        for token in ('activeSerial==lastSerial',
                      'skyWithEggSerial~=lastSerial',
                      'skyWithEggSerial==serial and activeSerial==serial',
                      'scoreAfterSkySerial=serial'):
            self.assertIn(token,AUDIT,token)
    def test_serial_reset_prevents_stale_completion(self):
        self.assertIn("skyWithEggSerial=-1;scoreAfterSkySerial=-1",AUDIT)
        self.assertIn("carried=false;scored=false",AUDIT)
    def test_fails_if_out_of_studio(self):
        self.assertFalse(safe(AUDIT.replace('if not RunService:IsStudio() then return end',"")))
    def test_fails_if_client_can_fire(self):
        self.assertFalse(safe(AUDIT+' remote:FireServer({action="SCORE"})'))
    def test_fails_if_score_before_sky(self):
        self.assertFalse(safe(AUDIT.replace("skyWithEggSerial==serial and activeSerial==serial",
                                            "activeSerial==serial")))
    def test_fails_if_airborne_counts_as_on_floor(self):
        self.assertFalse(safe(AUDIT.replace("hum.FloorMaterial~=Enum.Material.Air","true")))
    def test_fails_if_extra_remote_listener(self):
        self.assertFalse(safe(AUDIT+' remote.OnClientEvent:Connect(function() end)'))
    def test_deck_requires_exact_physical_raycast(self):
        self.assertIn("rayParams.FilterDescendantsInstances={character}",AUDIT)
        self.assertIn("if hit and hit.Instance==deck then",AUDIT)
    def test_drop_before_score_clears_sky_progress(self):
        self.assertIn("local previousCarry=lastCarry",AUDIT)
        self.assertIn("local validSameEggDeposit=qualifiesSkyScore",AUDIT)
        self.assertIn('log("ROUTE_RESET"',AUDIT)
        self.assertIn("skyCarryEgg=\"\"",AUDIT)
    def test_previous_carry_read_before_overwrite(self):
        self.assertLess(AUDIT.index("local previousCarry=lastCarry"),AUDIT.index("lastCarry=carry"))
    def test_false_score_blocked_for_multiple_players(self):
        self.assertIn("population==1",AUDIT)
        self.assertIn('log("SCORE_NOT_QUALIFIED"',AUDIT)
    def test_false_score_blocked_for_respawn(self):
        self.assertIn("player.Character==skyCarryCharacter",AUDIT)
    def test_fails_if_exact_deck_raycast_replaced(self):
        self.assertFalse(safe(AUDIT.replace("hit.Instance==deck","true")))
    def test_fails_if_previous_carry_ignored(self):
        self.assertFalse(safe(AUDIT.replace("qualifiesSkyScore(scoreRose,carry,previousCarry","qualifiesSkyScore(scoreRose,carry,lastCarry")))
    def test_fails_if_route_invalidated_ignored(self):
        self.assertFalse(safe(AUDIT.replace("invalidatesSkyRoute(skyWithEggSerial==serial","false or (skyWithEggSerial==serial")))
    def test_user_facing_distinction(self):
        self.assertIn("real walking/FUN still owner-verified",AUDIT)
        self.assertIn("Owner must physically walk/carry/play",AUDIT)

if __name__=="__main__":unittest.main(verbosity=2)
