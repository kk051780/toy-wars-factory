"""Actual V3 matchmaking: integrate existing item author, don't rebuild other lanes.

Tests verify source wiring/fair spatial distribution, not game engine playability.
Native Luau functional version runs in GitHub Actions separately.
"""
from pathlib import Path
import json
import re
import unittest
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
HOST=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
INTAKE=(ROOT/"EGGRUMBLE_RaidItemIntake.luau").read_text(encoding="utf-8")
ITEMS=(ROOT/"EGGRUMBLE_FieldItemPickups.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))
PLAN=[(int(x),int(z),kind) for x,z,kind in re.findall(
    r'\{x=(-?\d+),z=(\d+),kind="(HEAL|DASH|SHIELD)"\}',INTAKE)]
KINDS={"HEAL","DASH","SHIELD"}

class ExistingLanesIntegration(unittest.TestCase):
    def test_exactly_nine_item_sites_with_route_and_flank_fairness(self):
        self.assertEqual(len(PLAN),9)
        self.assertEqual(len({(x,z) for x,z,_ in PLAN}),9)
        by_z=defaultdict(set);by_x=defaultdict(set)
        for x,z,kind in PLAN:
            self.assertIn(x,(-140,0,140))
            self.assertIn(z,(300,470,640))
            by_z[z].add(kind);by_x[x].add(kind)
        for lane in list(by_z.values())+list(by_x.values()):
            self.assertEqual(lane,KINDS)
        for i,(_,_,kind) in enumerate(PLAN):
            self.assertEqual(kind,("HEAL","DASH","SHIELD")[i%3])

    def test_existing_real_item_author_called_once_not_rewritten(self):
        self.assertIn('local FieldItems=require(script.Parent:WaitForChild("EGGRUMBLE_FieldItemPickups"))',HOST)
        self.assertIn('local RaidItemIntake=require(script.Parent:WaitForChild("EGGRUMBLE_RaidItemIntake"))',HOST)
        self.assertEqual(HOST.count('return RaidItemIntake.start(session,root,FieldItems)'),1)
        self.assertLess(HOST.index("Rules.start(session.rules)"),
                        HOST.index("return RaidItemIntake.start("))
        self.assertIn('session.itemIntakeStatus="YELLOW_ITEM_OPTIONAL"',HOST)
        self.assertIn('session.fieldItemCount=0',HOST)
        self.assertIn('session.itemIntakeStatus="READY"',HOST)
        self.assertIn("authorItems.start(session,points)",INTAKE)
        self.assertIn('assert(session.itemIntakeStarted~=true',INTAKE)
        self.assertIn('if partial then partial:Destroy() end',INTAKE)
        self.assertIn('session.itemIntakeStarted=false',INTAKE)
        self.assertIn('error(err)',INTAKE)
        self.assertNotIn('function Items.start(',INTAKE)
        self.assertNotIn('Instance.new("ProximityPrompt")',INTAKE)

    def test_two_modes_spatially_isolated_and_discrete_physical_pickups(self):
        self.assertIn('session.mode=="TEAM" or session.mode=="BATTLE_ROYALE"',INTAKE)
        self.assertIn('if session.mode=="TEAM" then -620 else 620',INTAKE)
        self.assertIn('origin+Vector3.new(xCenter+site.x,1.8,site.z)',INTAKE)
        self.assertIn('local consumed:{[string]:boolean}={}',ITEMS)
        self.assertIn('if consumed[id] or not part.Parent or not part.CanQuery or not canUse(player,session) then return end',ITEMS)
        self.assertIn('consumed[id]=true;lastUse[key]=now',ITEMS)
        self.assertIn('castle.alive==true and session.rules.phase=="ACTIVE"',ITEMS)
        self.assertIn('if (root.Position-part.Position).Magnitude>10 then return end',ITEMS)
        self.assertIn('prompt.Enabled=false',ITEMS)
        self.assertIn('local RESPAWN_SECONDS=35',ITEMS)
        self.assertIn('if not matchActive() or not part.Parent then return end',ITEMS)
        self.assertIn('part.Transparency=0;part.CanQuery=true;prompt.Enabled=true',ITEMS)
        self.assertIn('session.itemStop=function()',ITEMS)

    def test_source_owned_code_not_doubled_or_running_standalones(self):
        server=PROJECT["tree"]["ServerScriptService"]
        self.assertEqual(server["EGGRUMBLE_FieldItemPickups"]["$path"],
                         "EGGRUMBLE_FieldItemPickups.luau")
        self.assertEqual(server["EGGRUMBLE_RaidItemIntake"]["$path"],
                         "EGGRUMBLE_RaidItemIntake.luau")
        for standalone in ("EGGRUMBLE_FieldItemPreview",
                           "EGGRUMBLE_NeutralBossPreview",
                           "EGGRUMBLE_CastleWalkthrough",
                           "EGGRUMBLE_LobbyUXStandalone",
                           "EGGRUMBLE_ValleyArtPreview"):
            self.assertNotIn(standalone,server)
        self.assertEqual(sum(key=="EGGRUMBLE_LobbyCastleModesPreview" for key in server),1)
        self.assertIn('if session.world.Parent then session.world:Destroy() end',HOST)

    def test_character_battle_castle_neutral_item_lobby_still_in_one_host(self):
        for anchor in (
            'SevenRoleCombat.equip(session,p,role)',
            'SwarmCombat.start(session)',
            'BotActors.start(session,Rules)',
            'Rules.takeFieldEgg(session.rules,',
            'Rules.damageCastle(state,entry.id,from,120)',
            'RaidItemIntake.start(session,root,FieldItems)',
            'joinQueue("TEAM",p)',
            'joinQueue("BATTLE_ROYALE",p)',
            'for i,role in ipairs(SevenRoleCombat.roleOrder())',
            'for j=1,3 do',
            'getCastlePoint(session.mode,index)',
            'session.closeRound=function(abandoned:boolean?)',
        ):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor,HOST)

if __name__=="__main__":
    unittest.main()
