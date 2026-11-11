"""Source-only truthful S1 FTUE client integration into corrected D07 D08 spatial+lobby.
Checks REAL immutable Git blobs and structural APIs. NOT Roblox or Luau execution.
"""
from __future__ import annotations
import hashlib,json,pathlib,re,subprocess,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
GAME=ROOT/"candidate"
OLD=pathlib.Path("handoffs/P0D-S1-D07D08-SPATIAL-LOBBY-COMPOSITE-20261112-01/candidate")
EVIDENCE=ROOT/"ftue-original-evidence"
MODEL="src/shared/FirstMinuteModel.luau"
CLIENT="src/client/FirstMinuteCoach.client.luau"
BLOBS={MODEL:"fcdc399bf95b6cd0532691718f5a54e8a4fd84b4",
       CLIENT:"63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9"}
def gitblob(path):
    return subprocess.check_output(["git","hash-object",str(path)],text=True).strip()
class FirstMinuteSourceIntegration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.g=(GAME/"src/server/Game.server.luau").read_text("utf8")
    cls.coach=(GAME/CLIENT).read_text("utf8")
    cls.model=(GAME/MODEL).read_text("utf8")
    cls.cfg=json.loads((GAME/"default.project.json").read_text("utf8"))
 def test_original_FTUE_sources_exact_Git_blobs(self):
    for path,sha in BLOBS.items():
        self.assertEqual(gitblob(GAME/path),sha,path)
 def test_original_FTUE_sources_byte_identical_to_author_evidence(self):
    for path,name in [(MODEL,"FirstMinuteModel.luau"),(CLIENT,"FirstMinuteCoach.client.luau")]:
        self.assertEqual((GAME/path).read_bytes(),(EVIDENCE/"src"/name).read_bytes(),name)
 def test_only_three_source_differences_against_previous_game(self):
    previous={p.relative_to(OLD).as_posix():p for p in OLD.rglob("*") if p.is_file() and p.name!="BUILD_MANIFEST.json"}
    self.assertEqual(len(previous),28)
    for path,old in previous.items():
        if path=="default.project.json":continue
        self.assertEqual((GAME/path).read_bytes(),old.read_bytes(),path)
    expected={str(x.relative_to(GAME)).replace("\\","/") for x in GAME.rglob("*") if x.is_file() and x.name!="BUILD_MANIFEST.json"}
    self.assertEqual(expected-set(previous),set(BLOBS))
 def test_rojo_original_shared_require_and_single_new_client(self):
    t=self.cfg["tree"]
    self.assertEqual(t["ReplicatedStorage"]["TrapRaidersShared"]["$path"],"src/shared")
    self.assertEqual(t["ServerScriptService"]["TrapRaidersS1"]["$path"],"src/server")
    c=t["StarterPlayer"]["StarterPlayerScripts"]
    self.assertEqual(c["TrapRaidersCoach"],{"$path":CLIENT})
    self.assertEqual(c["TrapRaidersHUD"],{"$path":"src/client/HUD.client.luau"})
    self.assertEqual(c["S1GoroganStompRing"],{"$path":"src/client/S1GoroganStompRing.client.luau"})
    self.assertEqual(c["GoroganVisualPolicy"],{"$path":"src/client/GoroganVisualPolicy.luau"})
    self.assertEqual(len(c),5)
 def test_original_rojo_mapping_only_added_one_client(self):
    old=json.loads((OLD/"default.project.json").read_text("utf8"))
    now=json.loads((GAME/"default.project.json").read_text("utf8"))
    scripts=now["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    self.assertEqual(scripts.pop("TrapRaidersCoach"),{"$path":CLIENT})
    self.assertEqual(now,old)
 def test_one_authoritative_server_and_only_old_remote(self):
    scripts=list((GAME/"src/server").glob("*.server.luau"))
    self.assertEqual([x.name for x in scripts],["Game.server.luau"])
    self.assertEqual(self.g.count('Instance.new("RemoteEvent")'),1)
    self.assertEqual(self.g.count("OnServerEvent:Connect"),1)
    self.assertNotIn("Instance.new(\"RemoteEvent\")",self.coach)
    self.assertNotIn("FireServer(",self.coach)
 def test_no_extra_game_loop_or_boss_authority_in_first_minute(self):
    for s in (self.coach,self.model):
        for banned in ("RunService","Heartbeat","RenderStepped","while true","Humanoid:TakeDamage","SetAsync","MarketplaceService","ProcessReceipt","PublishAsync","TeleportService","math.random"):
            self.assertNotIn(banned,s)
    self.assertEqual(self.coach.count("OnClientEvent:Connect"),1)
    self.assertEqual(len(list((GAME/"src/client").glob("*.client.luau"))),3)
 def test_real_server_snapshot_contains_all_consumed_fields(self):
    for token in ['kind = "SNAPSHOT"',"serial = match.serial","phase = match.phase",
                  "time = seconds","scores = {RED = match.scores.RED, BLUE = match.scores.BLUE}",
                  "team = getTeamName(player)",'role = roles[player] or "RAIDER"',
                  'carrying = carry[player] or ""']:
        self.assertIn(token,self.g)
    for token in ['packet.kind ~= "SNAPSHOT"','packet.serial < state.serial',
                  "packet.phase","packet.time","packet.scores.RED","packet.scores.BLUE",
                  "packet.carrying","packet.role"]:
        self.assertIn(token,self.model)
 def test_help_is_optional_only_existing_snapshot(self):
    self.assertIn('WaitForChild("TrapRaidersS1Remote")',self.coach)
    self.assertIn('WaitForChild("FirstMinuteModel")',self.coach)
    self.assertIn("Model.consume(state, snapshot, time())",self.coach)
    self.assertIn("Model.view(state, time())",self.coach)
    self.assertIn('panel.Name = "CoachPanel"',self.coach)
    self.assertIn("close.MouseButton1Click",self.coach)
    self.assertIn("help.MouseButton1Click",self.coach)
 def test_first_minute_cues_and_no_fake_revenue(self):
    for cue in ("卵をゲット！","敵のお城","守護","60 and not state.manualHelp","RESULTS","COUNTDOWN"):
        self.assertIn(cue,self.model)
    for s in (self.coach,self.model):
        for disallowed in ("AnalyticsService","MarketplaceService","Purchase","leaderstats","DataStore","coins","Revenue"):
            self.assertNotIn(disallowed,s)
 def test_hud_position_not_overwritten_and_server_d07_off_by_default(self):
    for s in ['local CANONICAL_S1_ENABLED = false','local D07_D08_RELEASE_REVIEW_APPROVED = false']:
        self.assertIn(s,self.g)
    self.assertIn("panel.Position = UDim2.new(0.5, 0, 0, 108)",self.coach)
    self.assertIn("help.Position = UDim2.new(1, -38, 0, 105)",self.coach)
 def test_new_manifest_strict_30_files(self):
    m=json.loads((GAME/"BUILD_MANIFEST.json").read_bytes())
    self.assertEqual(set(m),{"files","format","game_id","packet_id","public_source_allowed","work_id"})
    self.assertEqual(m["format"],"P0D_PUBLIC_SOURCE_V1")
    self.assertEqual(len(m["files"]),30)
    seen=set()
    for f in m["files"]:
        self.assertNotIn(f["path"],seen);seen.add(f["path"])
        raw=(GAME/f["path"]).read_bytes()
        self.assertEqual(len(raw),f["size"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),f["sha256"])
    self.assertIn(MODEL,seen);self.assertIn(CLIENT,seen)
if __name__=="__main__":unittest.main()
