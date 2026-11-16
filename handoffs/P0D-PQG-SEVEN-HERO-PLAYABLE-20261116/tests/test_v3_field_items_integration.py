"""Source-negative tests for reusing FieldItemPickups inside real V3 TEAM/BR.
Passing here only establishes source contract, not Roblox Studio play.
"""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LOBBY=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
ITEMS=(ROOT/"EGGRUMBLE_FieldItemPickups.luau").read_text(encoding="utf-8")
PROJECT=(ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8")

def missing(lobby=LOBBY,items=ITEMS,project=PROJECT):
    tree=json.loads(project)["tree"]["ServerScriptService"]
    req="EGGRUMBLE_FieldItemPickups"
    checks={
        "one V3 module require":lobby.count('WaitForChild("EGGRUMBLE_FieldItemPickups")')==1,
        "one item game start":lobby.count("FieldItems.start(session,itemPositions)")==1,
        "rules active before pickup":lobby.find("Rules.start(session.rules)")>=0 and lobby.find("Rules.start(session.rules)") < lobby.find("FieldItems.start(session,itemPositions)"),
        "no second lobby host":'EGGRUMBLE_FieldItemPreview.server.luau' not in project,
        "Rojo source exact":tree.get(req,{}).get("$path")=="EGGRUMBLE_FieldItemPickups.luau",
        "twelve item orbs":'for lane=1,3 do' in lobby and 'for slot=1,4 do' in lobby,
        "three live tactical lanes":'295+(lane-1)*170' in lobby,
        "symmetric arena width":'worldX+(slot-2.5)*150' in lobby,
        "nonfloating lane surface":'worldX+(slot-2.5)*150,-.95,295+(lane-1)*170' in lobby,
        "game-only world":'FieldItems.start(session,itemPositions)' in lobby,
        "three original consumables":all(t in items for t in ('HEAL={','DASH={','SHIELD={')),
        "same server active roster":'session.rules.phase=="ACTIVE"' in items and 'castle.alive==true' in items,
        "server distance":'(root.Position-part.Position).Magnitude>10' in items,
        "single consumed token":'consumed[id]=true;lastUse[key]=now' in items,
        "no paid economy":all(word not in items for word in ('MarketplaceService','DataStoreService','RemoteEvent')),
        "no permanent prompt UI":'Instance.new("ScreenGui")' not in items,
        "explicit Studio guard":'assert(RunService:IsStudio()' in items,
        "parent world cleanup":'folder.Parent=session.world' in items,
    }
    return [k for k,v in checks.items() if not v]

class TestRealV3ItemIntegration(unittest.TestCase):
    def test_source_integrity(self):self.assertEqual([],missing())
    def test_unwired_require(self):
        self.assertIn("one V3 module require",missing(lobby=LOBBY.replace('WaitForChild("EGGRUMBLE_FieldItemPickups")','WaitForChild("missing")')))
    def test_orphan_item_spawner(self):
        self.assertIn("one item game start",missing(lobby=LOBBY.replace("FieldItems.start(session,itemPositions)","-- disconnected")))
    def test_wrong_phase(self):
        self.assertIn("rules active before pickup",missing(lobby=LOBBY.replace("Rules.start(session.rules)","-- no start")))
    def test_wrong_map_lane(self):
        self.assertIn("three live tactical lanes",missing(lobby=LOBBY.replace("295+(lane-1)*170","99999")))
    def test_asymmetric_field(self):
        self.assertIn("symmetric arena width",missing(lobby=LOBBY.replace("worldX+(slot-2.5)*150","worldX+99999")))
    def test_no_rojo_module(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"].pop("EGGRUMBLE_FieldItemPickups")
        self.assertIn("Rojo source exact",missing(project=json.dumps(p)))
    def test_extra_item_preview_host(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"]["EGGRUMBLE_FieldItemPreview"]={"$path":"EGGRUMBLE_FieldItemPreview.server.luau"}
        self.assertIn("no second lobby host",missing(project=json.dumps(p)))
    def test_dual_pickup(self):
        self.assertIn("single consumed token",missing(items=ITEMS.replace("consumed[id]=true;lastUse[key]=now","-- no token")))
    def test_unauthorized_potion(self):
        self.assertIn("same server active roster",missing(items=ITEMS.replace('session.rules.phase=="ACTIVE"','true')))
    def test_remote_item_use(self):
        self.assertIn("no paid economy",missing(items=ITEMS+" RemoteEvent"))
    def test_invisible_prompt_item(self):
        self.assertIn("server distance",missing(items=ITEMS.replace("(root.Position-part.Position).Magnitude>10","false")))
if __name__=="__main__": unittest.main()
