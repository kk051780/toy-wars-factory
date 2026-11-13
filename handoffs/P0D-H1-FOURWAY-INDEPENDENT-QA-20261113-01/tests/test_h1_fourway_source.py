"""Independent H1 28-source whole-game contract QA, no Roblox Studio claims.
All reads come from genuinely assembled #255 frozen source. This QA never changes game files.
"""
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

P=Path(__file__).resolve()
REPO=P.parents[3]
WOW=REPO/"handoffs/P0D-H1-WOW-4WAY-20261113-01"
BASE=REPO/"handoffs/P0D-H1-COMPOSITE-20261113-01"
SRC=WOW/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY/src"
PROJECT=WOW/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY/default.project.json"
SOURCE_LOCK=WOW/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY/SOURCE_LOCK.json"

EXPECTED_BLOBS={
    "server/Game.server.luau":"adecfee41a594bdd54393050b4890a5733a536ce",
    "server/MapBuilder.luau":"94655d019fdf9798fa24a350ebf49f8290465ac0",
    "server/S1RaiderWindRules.luau":"7d5706774b874759e7ab994dc0654c3ae9a46502",
    "server/H1FunWorld.server.luau":"cc764b9caaa293ff747489e02e607af4502ddca4",
    "client/HUD.client.luau":"6d273404800e1d25fb1405bc52249b3ab47c1b41",
    "client/D18Batch8Catalog.luau":"41079553d2141940fc3fee57b23969e292770614",
    "client/D18MascotGuideRules.luau":"328b8a4d70261e633f163a5e166822a29d7eb1ba",
    "client/D18MascotGuide.client.luau":"39a2e35e4b2e8635d6d87359cd86f783aedf8756"
}
ROUTE_PATTERN=re.compile(r'path\("([^"]+)",Vector3\.new\(([^)]+)\),Vector3\.new\(([^)]+)\),\s*(\d+)\s*,')
ROUTE_NAMES={
    "SEA_LOW_CAUSEWAY","SEA_ENTRY_RED","SEA_ENTRY_BLUE",
    "SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE"
}

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def full_contents():
    assert SRC.is_dir(),"Must first execute original #255 tools/assemble.py --assemble"
    paths=sorted(SRC.rglob("*.luau"))
    assert len(paths)==28,("actual assembled Luau source count",len(paths))
    return {p.relative_to(SRC).as_posix():p.read_text(encoding="utf-8") for p in paths}

def check_exact_blobs():
    for p,h in EXPECTED_BLOBS.items():
        x=SRC/p
        assert x.is_file(),p
        actual=blob(x.read_bytes())
        assert actual==h,(p,actual,h)

def bounded_route_geometry(map_source,world):
    assert 'Vector3.new(sign * 103, 7, z)' in map_source
    assert 'Vector3.new(40, 14, 5)' in map_source
    assert 'Vector3.new(i * 20, 3, if i % 2 == 0 then 32 else -32)' in map_source
    assert "p.CanCollide = collide ~= false" in map_source
    paths={}
    for m in ROUTE_PATTERN.finditer(world):
        name=m.group(1)
        assert name not in paths
        a=tuple(float(x.strip()) for x in m.group(2).split(","))
        b=tuple(float(x.strip()) for x in m.group(3).split(","))
        width=float(m.group(4))
        assert len(a)==3 and len(b)==3
        paths[name]=(a,b,width)
    assert set(paths)==ROUTE_NAMES,(set(paths),ROUTE_NAMES)
    solids={}
    for team,x in (("RED",-103),("BLUE",103)):
        for z in (-44,44):
            solids[f"{team}_wall_{z}"]=((x-20,x+20),(z-2.5,z+2.5))
    for i in range(-2,3):
        x=20*i; z=32 if i%2==0 else -32
        solids[f"rock_{i}"]=((x-3.5,x+3.5),(z-3.5,z+3.5))
    def overlap(a,b):
        return min(a[1],b[1])>max(a[0],b[0])
    for name,(a,b,width) in paths.items():
        horiz=((min(a[0],b[0])-width/2,max(a[0],b[0])+width/2),
               (min(a[2],b[2])-width/2,max(a[2],b[2])+width/2))
        for obstacle,rect in solids.items():
            assert not (overlap(horiz[0],rect[0]) and overlap(horiz[1],rect[1])),(name,obstacle)
        assert 8<=width<=18
        assert abs(a[0])<=125 and abs(b[0])<=125 and abs(a[2])<=69 and abs(b[2])<=69
        dx=b[0]-a[0];dz=b[2]-a[2]
        assert abs(b[1]-a[1]) <= .55*(dx*dx+dz*dz)**.5
    def same(p,q):return sum((a-b)**2 for a,b in zip(p,q))<.00001
    assert same(paths["SKY_RAMP_RED"][1],paths["SKY_WALKWAY"][0])
    assert same(paths["SKY_WALKWAY"][1],paths["SKY_RAMP_BLUE"][0])
    assert same(paths["SEA_ENTRY_RED"][0],paths["SEA_LOW_CAUSEWAY"][0])
    assert same(paths["SEA_ENTRY_BLUE"][0],paths["SEA_LOW_CAUSEWAY"][1])
    return paths

def source_contract(s):
    g=s["server/Game.server.luau"]
    h=s["client/HUD.client.luau"]
    m=s["server/MapBuilder.luau"]
    w=s["server/H1FunWorld.server.luau"]
    t=s["server/S1TrapRules.luau"]
    wind=s["server/S1RaiderWindRules.luau"]
    guide=s["client/D18MascotGuide.client.luau"]
    rules=s["client/D18MascotGuideRules.luau"]
    assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert g.count('remote.OnServerEvent:Connect(')==1
    assert g.count('local function applyWind(')==1
    assert 'if role ~= "RAIDER" and role ~= "GUARDIAN" then return end' in g
    assert 'elseif data.action == "WIND_BURST" then applyWind(player, data)' in g
    assert 'WindRules.canActivate({' in g
    assert 'lastSeq[player] = data.seq -- consume all replayed and rejected intents' in g
    assert 'carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil' in g
    assert 'stopWind(player) -- cannot carry an egg at burst speed' in g
    assert 'stopWind(player) -- Guardian trap always cancels Raider wind.' in g
    assert 'map.teams[team].eggPrompt.Triggered:Connect(' in g
    assert 'map.teams[team].scorePrompt.Triggered:Connect(' in g
    assert 'Rules.canSteal(' in g and 'Rules.canScore(' in g
    assert 'dropEgg(player)' in g and 'match.scores[team] += 1' in g
    assert 'math.abs(position.X) > 130' in g and 'math.abs(position.Z) > 76' in g
    assert 'WindRules.SPEED' in g and 'windUntil[player] = now + WindRules.DURATION' in g
    assert 's.role ~= "GUARDIAN"' in t and 's.carrying == true' in t
    assert 's.role ~= "RAIDER"' in wind and 's.carrying == true' in wind
    assert 'Wind.COOLDOWN = 18' in wind and 'Wind.SPEED = 27' in wind
    assert 'button(gui, "RaiderRole"' in h and 'button(gui, "GuardianRole"' in h
    assert 'action("WIND_BURST", nil)' in h
    assert 'windButton.Visible = s.phase == "ACTIVE" and s.role == "RAIDER"' in h
    assert 'trapButton.Visible = s.phase == "ACTIVE" and s.role == "GUARDIAN"' in h
    assert 'if not RunService:IsStudio() then' in w
    assert 'if not RunService:IsStudio() then return end' in guide
    assert 'Models.create("SPACE",creatures)' in w
    assert 'Models.create("CELESTIAL",creatures)' in w
    assert 'D18_Original_Lava_Dragon_ClientOnly' in guide
    assert 'remote.OnClientEvent:Connect' in guide
    assert 'if not int(update) or update<=previousUpdate then return nil end' in rules
    assert 'partName=destTeam.."_"..objective' in rules
    assert 's.kind~="SNAPSHOT"' in rules
    for p in ("server/H1FunWorld.server.luau","client/D18MascotGuide.client.luau"):
        x=s[p]
        for bad in ("FireServer", "MarketplaceService", "DataStore", "TeleportService",
                    "remote.OnServerEvent:Connect", "RemoteEvent", "TakeDamage"):
            assert bad not in x,(p,bad)
    assert 'RunService:IsStudio()' in w and 'if not arena then' in w
    bounded_route_geometry(m,w)
    return True

class TestIndependentH1FourWay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=full_contents()
    def test_28_source_count_and_unique_runtime(self):
        self.assertEqual(len(self.s),28)
        self.assertEqual([p for p in self.s if p.endswith("/Game.server.luau")],["server/Game.server.luau"])
        self.assertEqual(len([p for p in self.s if p.endswith(".server.luau")]),2)
        self.assertEqual(len([p for p in self.s if p.endswith(".client.luau")]),4)
    def test_independent_source_blob_readback(self):check_exact_blobs()
    def test_original_twentyfive_source_unchanged_except_world(self):
        original=sorted((BASE/"src").rglob("*.luau"))
        self.assertEqual(len(original),25)
        changed=[]
        for f in original:
            rel=f.relative_to(BASE/"src").as_posix()
            if f.read_bytes()!=(SRC/rel).read_bytes():changed.append(rel)
        self.assertEqual(changed,["server/H1FunWorld.server.luau"])
    def test_role_wind_trap_egg_and_guide(self):
        self.assertTrue(source_contract(self.s))
    def test_project_mounts_all_three_d18_real_local_modules(self):
        p=json.loads(PROJECT.read_text(encoding="utf-8"))
        kids=p["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        for key,name in (("D18Batch8Catalog","D18Batch8Catalog.luau"),
                         ("D18MascotGuideRules","D18MascotGuideRules.luau"),
                         ("D18MascotGuide","D18MascotGuide.client.luau")):
            self.assertEqual(kids[key]["$path"],"src/client/"+name)
        self.assertEqual(p["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"],"src/server")
    def test_original_full_game_lock_not_official_rc(self):
        receipt=json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_count"],28)
        self.assertFalse(receipt["not_authorized"]["official_RC_adopted"])
        self.assertFalse(receipt["not_authorized"]["Studio_2client_tested"])
        self.assertFalse(receipt["not_authorized"]["OWNER_H0_H1_fun_accepted"])
    def test_original_frozen_wall_centerline_pass(self):
        w=self.s["server/H1FunWorld.server.luau"]
        lines=bounded_route_geometry(self.s["server/MapBuilder.luau"],w)
        self.assertEqual(len(lines),6)
    def test_no_client_selected_attack_or_score(self):
        g=self.s["server/Game.server.luau"]
        h=self.s["client/HUD.client.luau"]
        self.assertIn('remote:FireServer({action = kind, role = role, seq = seq})',h)
        for bad in ("position = root.Position","damage = Config.CombatDamage","score = match.scores"):
            self.assertNotIn(bad,h)
        self.assertIn("Rules.canScore(",g)
    def test_mutant_new_server_remote_blocked(self):
        s=dict(self.s)
        s["server/Game.server.luau"]=s["server/Game.server.luau"].replace(
            'remote.Name = "TrapRaidersS1Remote"',
            'remote.Name = "TrapRaidersS1Remote"\nremote.Name = "TrapRaidersS1Remote"')
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_7_role_unapproved_blocked(self):
        s=dict(self.s)
        s["server/Game.server.luau"]=s["server/Game.server.luau"].replace(
            'if role ~= "RAIDER" and role ~= "GUARDIAN" then return end',
            'if type(role) ~= "string" then return end')
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_burst_carry_blocked(self):
        s=dict(self.s)
        s["server/S1RaiderWindRules.luau"]=s["server/S1RaiderWindRules.luau"].replace(
            's.carrying == true','s.carrying == false')
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_ghost_trap_guardian_blocked(self):
        s=dict(self.s)
        s["server/S1TrapRules.luau"]=s["server/S1TrapRules.luau"].replace(
            's.carrying == true','s.carrying == false')
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_not_just_cosmetic_broken_sea_blocked(self):
        s=dict(self.s)
        s["server/H1FunWorld.server.luau"]=s["server/H1FunWorld.server.luau"].replace(
            'Vector3.new(-72,0,-55),Vector3.new(72,0,-55)',
            'Vector3.new(-99,0,-45),Vector3.new(99,0,-45)')
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_paid_route_blocked(self):
        s=dict(self.s)
        s["server/H1FunWorld.server.luau"]+='local x=game:GetService("MarketplaceService")'
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_d18_malicious_remote_blocked(self):
        s=dict(self.s)
        s["client/D18MascotGuide.client.luau"]+='remote:FireServer({action="SCORE", seq=0})'
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_d18_out_of_order_snapshot_blocked(self):
        s=dict(self.s)
        s["client/D18MascotGuideRules.luau"]=s["client/D18MascotGuideRules.luau"].replace(
            "update<=previousUpdate","update<previousUpdate")
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_route_unreachable_gap_blocked(self):
        s=dict(self.s)
        s["server/H1FunWorld.server.luau"]=s["server/H1FunWorld.server.luau"].replace(
            'Vector3.new(-46,16,32.5),Vector3.new(46,16,32.5)',
            'Vector3.new(-35,16,32.5),Vector3.new(46,16,32.5)')
        with self.assertRaises(AssertionError):source_contract(s)
    def test_mutant_missing_fantasy_creature_blocked(self):
        s=dict(self.s)
        s["server/H1FunWorld.server.luau"]=s["server/H1FunWorld.server.luau"].replace(
            'Models.create("SPACE",creatures)','Models.create("EARTH",creatures)')
        with self.assertRaises(AssertionError):source_contract(s)
if __name__=="__main__":
    unittest.main()
