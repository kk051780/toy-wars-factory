"""P0D H1 live-release-gate source QA. No in-engine PASS claimed."""
from pathlib import Path
import hashlib,json,re,unittest

HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
SRC=OWN/"dist/TRAP_RAIDERS_H1_LIVE_GATE_OFF_STUDIO_ONLY/src"
INPUT=OWN/"inputs"
ORIG=REPO/"handoffs/P0D-H1-WOW-4WAY-20261113-01/dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY/src"
PROJECT=OWN/"dist/TRAP_RAIDERS_H1_LIVE_GATE_OFF_STUDIO_ONLY/default.project.json"
RECEIPT=OWN/"dist/TRAP_RAIDERS_H1_LIVE_GATE_OFF_STUDIO_ONLY/SOURCE_LOCK.json"
ORIGINAL={
    "server/H1FunWorld.server.luau":"cc764b9caaa293ff747489e02e607af4502ddca4",
    "client/D18MascotGuide.client.luau":"39a2e35e4b2e8635d6d87359cd86f783aedf8756"
}
NEW={
    "server/H1FunWorld.server.luau":"1c1974799790d58110d56c0d62b44943961cff00",
    "client/D18MascotGuide.client.luau":"1244d09b2dc3bce6acabb58db154bbe62edceb01",
    "shared/H1ReleaseGate.luau":"59eb9aa6e3f41b52b6bfb5e23147ae42dc451b57"
}
def blob(content):
    return hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
def validate_gate(s):
    assert "local LIVE_ENABLE = false" in s
    assert "local APPROVED_GAME_ID = 0" in s
    assert "local APPROVED_PLACE_ID = 0" in s
    assert "if isStudio == true then return true end" in s
    assert "if isStudio ~= false then return false end" in s
    assert "return LIVE_ENABLE == true" in s
    assert "and validId(APPROVED_GAME_ID) and validId(APPROVED_PLACE_ID)" in s
    assert "and validId(gameId) and validId(placeId)" in s
    assert "and gameId == APPROVED_GAME_ID and placeId == APPROVED_PLACE_ID" in s
    for bad in ("RemoteEvent","DataStore","MarketplaceService","GetAttribute","SetAttribute",
                "FireServer","FireClient","getfenv","loadstring","_G."):
        assert bad not in s,bad
def verify_source(base,new,gate,world,guide):
    validate_gate(gate)
    assert set(new)-set(base)=={"shared/H1ReleaseGate.luau"}
    assert {p for p in base if base[p]!=new[p]}=={
        "server/H1FunWorld.server.luau","client/D18MascotGuide.client.luau"}
    for rel in ("server/H1FunWorld.server.luau","client/D18MascotGuide.client.luau"):
        source=new[rel]
        assert source.count("ReleaseGate.canRun(RunService:IsStudio(),game.GameId,game.PlaceId)")==1
        assert source.count('WaitForChild("H1ReleaseGate",30)')==1
        assert 'SetAttribute("PreviewOnly",RunService:IsStudio())' in source
        assert "H1_RELEASE_GATE_DENIED" in source and "H1_RELEASE_GATE_MISSING" in source
        for bad in ("FireServer","FireClient","RemoteEvent","MarketplaceService","DataStore"):
            assert bad not in source,(rel,bad)
        # Studio only early return was removed, not all the harmless world/guide code.
        assert 'if not RunService:IsStudio() then return end' not in source
        assert 'warn("H1 private Studio source only; refused live execution")' not in source
    assert 'Models.create("SPACE",creatures)' in world
    assert 'Models.create("CELESTIAL",creatures)' in world
    assert 'D18_Original_Lava_Dragon_ClientOnly' in guide
    assert 'remote.OnClientEvent:Connect' in guide
    assert "remote.OnServerEvent:Connect" not in guide
    assert "CFrame.lookAt" in world
    assert 'FreeToAllRoles' in world
    assert 'TacticalAlternativeRoute' in world
    # Future approved live modules must not change original authority/gameplay.
    game=new["server/Game.server.luau"]
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert 'Rules.canSteal(' in game and 'Rules.canScore(' in game
    assert 'WindRules.canActivate({' in game
    assert "TrapRules.canPlace({" in game
    assert 'if role ~= "RAIDER" and role ~= "GUARDIAN" then return end' in game
    assert 'CANONICAL_S1_ENABLED = false' in game
    assert 'D07_D08_RELEASE_REVIEW_APPROVED = false' in game
    return True

class TestSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert SRC.is_dir(),"must first run own tools/assemble.py --assemble"
        cls.base={p.relative_to(ORIG).as_posix():p.read_bytes() for p in ORIG.rglob("*.luau")}
        cls.new={p.relative_to(SRC).as_posix():p.read_bytes() for p in SRC.rglob("*.luau")}
        cls.gate=cls.new["shared/H1ReleaseGate.luau"].decode()
        cls.s={p:b.decode() for p,b in cls.new.items()}
    def test_exact_original_source_count(self):
        self.assertEqual(len(self.base),28)
    def test_new_full_game_count(self):
        self.assertEqual(len(self.new),29)
    def test_original_inputs_sha(self):
        for name,sha in ORIGINAL.items():self.assertEqual(blob(self.base[name]),sha,name)
    def test_new_source_sha(self):
        for name,sha in NEW.items():self.assertEqual(blob(self.new[name]),sha,name)
    def test_game_unchanged_except_two_overlay_scripts(self):
        self.assertEqual([p for p in sorted(self.base) if self.base[p]!=self.new[p]],
                         ["client/D18MascotGuide.client.luau","server/H1FunWorld.server.luau"])
    def test_game_rules_unchanged_exact_source(self):
        for p in self.base:
            if p not in ORIGINAL:self.assertEqual(self.base[p],self.new[p])
    def test_failclosed_gate(self):self.assertTrue(validate_gate(self.gate) is None)
    def test_failclosed_29_source_contract(self):
        self.assertTrue(verify_source(
            {k:v.decode() for k,v in self.base.items()},self.s,self.gate,
            self.s["server/H1FunWorld.server.luau"],
            self.s["client/D18MascotGuide.client.luau"]))
    def test_approved_live_id_not_mounted_or_enabled(self):
        self.assertNotIn("local LIVE_ENABLE = true",self.gate)
        self.assertNotIn("local APPROVED_PLACE_ID = 1",self.gate)
    def test_project_uses_one_shared_module(self):
        p=json.loads(PROJECT.read_text(encoding="utf-8"))
        self.assertEqual(p["tree"]["ReplicatedStorage"]["TrapRaidersShared"]["$path"],"src/shared")
        self.assertIn("function ReleaseGate.canRun(",self.new["shared/H1ReleaseGate.luau"].decode())
    def test_receipt_no_live_pass(self):
        r=json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertFalse(r["module_live_enable"])
        self.assertFalse(r["official_RC_adopted"])
        self.assertFalse(r["owner_Studio_2client_tested"])
        self.assertFalse(r["published"])
    def test_mutant_live_enable_premature_rejected(self):
        with self.assertRaises(AssertionError):
            validate_gate(self.gate.replace("local LIVE_ENABLE = false","local LIVE_ENABLE = true"))
    def test_mutant_unrestricted_gameid_rejected(self):
        with self.assertRaises(AssertionError):
            validate_gate(self.gate.replace(
                "and gameId == APPROVED_GAME_ID and placeId == APPROVED_PLACE_ID",
                "and gameId == gameId and placeId == placeId"))
    def test_mutant_missing_studio_gate_rejected(self):
        s=dict(self.s);s["server/H1FunWorld.server.luau"]=s["server/H1FunWorld.server.luau"].replace(
            "ReleaseGate.canRun(RunService:IsStudio(),game.GameId,game.PlaceId)","true")
        with self.assertRaises(AssertionError):
            verify_source({k:v.decode() for k,v in self.base.items()},s,self.gate,
                          s["server/H1FunWorld.server.luau"],s["client/D18MascotGuide.client.luau"])
    def test_mutant_guide_remote_authority_rejected(self):
        s=dict(self.s);s["client/D18MascotGuide.client.luau"]+='remote:FireServer({action="SCORE"})'
        with self.assertRaises(AssertionError):
            verify_source({k:v.decode() for k,v in self.base.items()},s,self.gate,
                          s["server/H1FunWorld.server.luau"],s["client/D18MascotGuide.client.luau"])
    def test_mutant_original_game_replaced_rejected(self):
        s=dict(self.s);s["server/Game.server.luau"]=s["server/Game.server.luau"].replace(
            'if role ~= "RAIDER" and role ~= "GUARDIAN" then return end',
            'if type(role) ~= "string" then return end')
        with self.assertRaises(AssertionError):
            verify_source({k:v.decode() for k,v in self.base.items()},s,self.gate,
                          s["server/H1FunWorld.server.luau"],s["client/D18MascotGuide.client.luau"])
    def test_mutant_preview_attribute_rejected(self):
        s=dict(self.s);s["server/H1FunWorld.server.luau"]=s["server/H1FunWorld.server.luau"].replace(
            'SetAttribute("PreviewOnly",RunService:IsStudio())','SetAttribute("PreviewOnly",true)')
        with self.assertRaises(AssertionError):
            verify_source({k:v.decode() for k,v in self.base.items()},s,self.gate,
                          s["server/H1FunWorld.server.luau"],s["client/D18MascotGuide.client.luau"])
if __name__=="__main__":unittest.main()
