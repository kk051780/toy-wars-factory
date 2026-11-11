"""True source merge check: previously audited D07/D08 S1 plus lobby 4-hunk transform.
Not an interpreter or Roblox Studio integration test.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/"candidate"
PREVIOUS=Path("handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/candidate")
LOBBY_SCRIPT=ROOT/"lobby-evidence/tools/apply_game_patch.py"
LOBBY_SOURCE=ROOT/"lobby-evidence/src/LobbyTeamRecovery.luau"
SOURCE_IDS={
  "host":"61501c982619e54db6a09cf11b188ef872c1666e",
  "binding":"9cde26d7806a6ec20cd8648953eb37d1eefdc2c8",
  "lobby":"db1a369133550bc8356a4ee3ac22b97fcb1b46c4",
}
def blob(p):
    return subprocess.check_output(["git","hash-object",str(p)],text=True).strip()

class ActualLobbyAndD07D08Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current=(GAME/"src/server/Game.server.luau").read_text("utf8")
        cls.prior=(PREVIOUS/"src/server/Game.server.luau").read_text("utf8")
        spec=importlib.util.spec_from_file_location("source_lobby_patch",LOBBY_SCRIPT)
        assert spec and spec.loader
        cls.module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_lobby_original_planner_blob_exact(self):
        current=GAME/"src/server/LobbyTeamRecovery.luau"
        self.assertEqual(current.read_bytes(),LOBBY_SOURCE.read_bytes())
        self.assertEqual(blob(current),SOURCE_IDS["lobby"])

    def test_exact_four_reviewed_lobby_hunks_on_corrected_game(self):
        self.assertEqual(len(self.module.REPLACEMENTS),4)
        self.assertEqual(self.module.transform_source(self.prior),self.current)

    def test_inverse_all_four_hunks_restores_full_previous_Game(self):
        c=self.current
        for old,new in reversed(self.module.REPLACEMENTS):
            self.assertEqual(c.count(new),1)
            c=c.replace(new,old,1)
        self.assertEqual(c,self.prior)

    def test_original_d07_d08_host_binding_same_reviewed_blobs(self):
        for name,expected in [
            ("S1CanonicalRoundHost.luau",SOURCE_IDS["host"]),
            ("S1GoroganLiveBindings.luau",SOURCE_IDS["binding"]),
        ]: self.assertEqual(blob(GAME/"src/server"/name),expected)

    def test_all_other_game_project_modules_byte_exact(self):
        old={f.relative_to(PREVIOUS).as_posix():f for f in PREVIOUS.rglob("*")
             if f.is_file() and f.name != "BUILD_MANIFEST.json"}
        assert len(old)==27
        for relative,p in old.items():
            if relative in ("src/server/Game.server.luau","default.project.json"): continue
            self.assertEqual((GAME/relative).read_bytes(),p.read_bytes(),relative)

    def test_unique_main_server_no_secondary_round_or_network(self):
        scripts=sorted(p.name for p in (GAME/"src/server").glob("*.server.luau"))
        self.assertEqual(scripts,["Game.server.luau"])
        self.assertEqual(self.current.count('Instance.new("RemoteEvent")'),1)
        self.assertEqual(self.current.count("OnServerEvent:Connect"),1)
        self.assertEqual(self.current.count("local function tickRound()"),1)
        self.assertEqual(self.current.count("local function rebalanceLobbyTeams()"),1)

    def test_only_in_lobby_move_fresh_game_not_live(self):
        src=self.current
        self.assertIn('if match.phase ~= "LOBBY" then return end',src)
        self.assertEqual(src.count('        rebalanceLobbyTeams()'),1)
        self.assertEqual(src.count("LobbyTeamRecovery.plan(roster)"),1)
        self.assertIn("dropEgg(player)",src)
        self.assertIn("player.Team = teamInstances[move.to]",src)
        self.assertIn("root.CFrame = map.teams[move.to].spawn",src)

    def test_countdown_revalidates_both_sides_when_players_leave(self):
        src=self.current
        self.assertIn('if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then',src)
        self.assertIn('match.phase = "LOBBY"\n        elseif now >= match.phaseUntil then resetRound() end',src)

    def test_server_roll_and_actual_boss_visual_single_authority(self):
        src=self.current
        self.assertEqual(src.count("math.random(0, 99)"),1)
        self.assertEqual(src.count("canonicalHost:tick()"),1)
        self.assertNotIn("nextAlarmAt",src)
        self.assertIn('kind = "BOSS_VISUAL"',src)
        self.assertIn("position = position,",src)

    def test_boss_stays_off_pending_native_owner_review(self):
        self.assertIn("local CANONICAL_S1_ENABLED = false",self.current)
        self.assertIn("local D07_D08_RELEASE_REVIEW_APPROVED = false",self.current)
        self.assertNotIn("PublishAsync",self.current)

    def test_rojo_mounts_server_directory_and_existing_visual_clients(self):
        project=json.loads((GAME/"default.project.json").read_text("utf8"))
        self.assertEqual(project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"],"src/server")
        scripts=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertEqual(scripts["GoroganVisualPolicy"]["$path"],"src/client/GoroganVisualPolicy.luau")
        self.assertEqual(scripts["S1GoroganStompRing"]["$path"],"src/client/S1GoroganStompRing.client.luau")

    def test_canonical_manifest_all_28_files_and_1_planner(self):
        m=json.loads((GAME/"BUILD_MANIFEST.json").read_text("utf8"))
        self.assertEqual(set(m),{"format","game_id","work_id","packet_id","public_source_allowed","files"})
        self.assertEqual(len(m["files"]),30)
        names={x["path"] for x in m["files"]}
        self.assertEqual(len(names),30)
        self.assertIn("src/server/LobbyTeamRecovery.luau",names)
        for row in m["files"]:
            b=(GAME/row["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),row["sha256"],row["path"])
            self.assertEqual(len(b),row["size"],row["path"])

if __name__=="__main__":
    unittest.main()
