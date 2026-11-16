#!/usr/bin/env python3
"""Regression/negative tests for one existing V3 lobby Host source patch."""
import unittest
from select_lobby_safe_spawn import (
    transform, MARK, BEFORE_ROOT, BEFORE_FOLDER, BEFORE_QUEUE
)

FIXTURE="\n".join((
    "--!strict",
    "local Players=game:GetService(\"Players\")",
    BEFORE_ROOT,
    BEFORE_FOLDER,
    "local sessions:{[string]:any}={}",
    "local joined:{[number]:string}={}",
    BEFORE_QUEUE,
    "local MODE_SEATS=16",
    'local function joinQueue(mode:string,p:Player) end',
    'prompt(gateTeam,"参加する","TEAM",function(p) joinQueue("TEAM",p) end)',
    'prompt(gateBR,"参加する","BR",function(p) joinQueue("BATTLE_ROYALE",p) end)',
    "for i,role in ipairs(SevenRoleCombat.roleOrder()) do end",
    "local function startSession(mode:string) end",
))

class TestLobbySafeSpawn(unittest.TestCase):
    def test_fallback_root_and_floor_geometry(self):
        s=transform(FIXTURE)
        self.assertIn('local root=spawn and spawn.Position or Vector3.new(0,4,0)',s)
        self.assertIn('lobbyFloor.Size=Vector3.new(190,6,180)',s)
        self.assertIn('lobbyFloor.Position=root+Vector3.new(0,-4,40)',s)
        self.assertIn('lobbyFloor.Anchored=true',s)
        self.assertIn('lobbyFloor.CanCollide=true',s)
        self.assertIn('lobbyFloor.Parent=folder',s)
    def test_neutral_spawn(self):
        s=transform(FIXTURE)
        for expected in ('Instance.new("SpawnLocation")',
                         'lobbySpawn.Neutral=true','lobbySpawn.Duration=0',
                         'lobbySpawn.AllowTeamChangeOnTouch=false',
                         'player.RespawnLocation=lobbySpawn'):
            self.assertIn(expected,s)
    def test_active_match_stays_in_battle(self):
        s=transform(FIXTURE)
        self.assertEqual(s.count('if mode and sessions[mode] then return end'),2)
        self.assertIn('player.Character~=character',s)
        self.assertIn('player.Parent~=Players',s)
        self.assertEqual(s.count('character:PivotTo('),1)
    def test_studio_existing_player_arrival(self):
        s=transform(FIXTURE)
        self.assertIn('Players.PlayerAdded:Connect(gqBindLobbyArrival)',s)
        self.assertIn('Players:GetPlayers()',s)
        self.assertIn('if player.Character then onLobbyCharacter(player.Character) end',s)
    def test_dual_modes_roles_and_original_rules_unchanged(self):
        s=transform(FIXTURE)
        for phrase in ('joinQueue("TEAM",p)','joinQueue("BATTLE_ROYALE",p)',
                       'SevenRoleCombat.roleOrder()',
                       'local function startSession(mode:string) end'):
            self.assertEqual(s.count(phrase),FIXTURE.count(phrase))
    def test_exact_off_rollback(self):
        s=transform(FIXTURE)
        from select_lobby_safe_spawn import PLATFORM,BIND
        back=s.replace(BEFORE_QUEUE+"\n"+BIND,BEFORE_QUEUE,1)
        back=back.replace(BEFORE_FOLDER+"\n"+PLATFORM,BEFORE_FOLDER,1)
        self.assertEqual(back,FIXTURE)
        self.assertEqual(s.count(MARK),1)
    def test_refuse_double_apply(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            transform(transform(FIXTURE))
    def test_fail_closed_when_host_drifted(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR_DRIFT"):
            transform(FIXTURE.replace(BEFORE_FOLDER,""))
    def test_fail_closed_when_queues_drifted(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR_DRIFT"):
            transform(FIXTURE.replace('joinQueue("TEAM",p)',"queueTEAM(p)"))
    def test_no_second_runtime_script(self):
        s=transform(FIXTURE)
        self.assertNotIn('Instance.new("Script")',s)
        self.assertNotIn('Instance.new("RemoteEvent")',s)
        self.assertNotIn('DataStoreService',s)

if __name__=="__main__":
    unittest.main()
