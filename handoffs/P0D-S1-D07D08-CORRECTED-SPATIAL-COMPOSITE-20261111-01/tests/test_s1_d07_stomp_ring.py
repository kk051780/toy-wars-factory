"""Offline source+negative contracts for S1 local STOMP ring (NOT Luau runtime)."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/"candidate"
ORIG="351bf52e78020de0f879aa74064caf9fb8231ade"

class SpatialTelegraphSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=(GAME/"src/server/Game.server.luau").read_text(encoding="utf-8")
        cls.client=(GAME/"src/client/S1GoroganStompRing.client.luau").read_text(encoding="utf-8")
        cls.original_policy=(GAME/"src/client/GoroganVisualPolicy.luau")
        cls.project=json.loads((GAME/"default.project.json").read_text(encoding="utf-8"))

    def test_exact_unmodified_original_d07_policy(self):
        got=subprocess.check_output(["git","hash-object",str(self.original_policy)],text=True).strip()
        self.assertEqual(got,ORIG)

    def test_source_policy_validates_replay_and_start_single_use(self):
        p=self.original_policy.read_text(encoding="utf-8")
        self.assertIn("seq <= state.highestSeq",p)
        self.assertIn("state.seenStart = true",p)
        self.assertIn('if snapshot.kind == "STOMP" then',p)
        self.assertIn("MAX_STOMP_COUNT = 3",p)
        self.assertIn("now + 2 > state.expiresAt",p)

    def test_single_real_remote_no_new_remote(self):
        self.assertEqual(self.server.count('Instance.new("RemoteEvent")'),1)
        self.assertEqual(self.server.count("OnServerEvent:Connect"),1)
        self.assertEqual(self.server.count('remote:FireClient(player, {'),1)
        self.assertEqual(self.client.count("OnClientEvent:Connect"),1)
        self.assertNotIn('Instance.new("RemoteEvent")',self.client)
        self.assertNotIn("FireServer(",self.client)

    def test_packet_carries_real_original_center(self):
        s=self.server
        self.assertIn("local p = packet.position",s)
        self.assertIn("position = {x = p.x, y = p.y, z = p.z}",s)
        self.assertIn("position = position,",s)
        self.assertIn('packet.kind == "STOMP"',s)
        self.assertIn('packet.kind == "START"',s)

    def test_packet_rejects_malformed_infinite_nan_or_oob_center(self):
        s=self.server
        for part in ("p.x ~= p.x","p.y ~= p.y","p.z ~= p.z",
                     "math.abs(p.x) > 2048","math.abs(p.z) > 2048",
                     "p.y < -100","p.y > 700"):
            self.assertIn(part,s)

    def test_single_game_round_authority(self):
        self.assertEqual(self.server.count("local function tickRound()"),1)
        self.assertEqual(self.server.count("canonicalHost:tick()"),1)
        self.assertNotIn("nextAlarmAt",self.server)
        self.assertEqual(self.server.count("math.random(0, 99)"),1)
        self.assertEqual(self.server.count("local function sendBossVisual("),1)

    def test_source_server_off_by_default(self):
        self.assertIn("local CANONICAL_S1_ENABLED = false",self.server)
        self.assertIn("local D07_D08_RELEASE_REVIEW_APPROVED = false",self.server)
        self.assertIn("if not CANONICAL_S1_ENABLED or not D07_D08_RELEASE_REVIEW_APPROVED then",self.server)

    def test_client_requires_canonical_same_round_and_event(self):
        c=self.client
        for value in ('s.serial ~= lastSerial','s.bossId ~= "GOROGAN"',
                      's.stageId ~= "S1"', 's.eventId ~= "G07_" .. tostring(lastSerial)',
                      's.seq > 10000'):
            self.assertIn(value,c)

    def test_client_rejects_replayed_old_or_future_packets(self):
        c=self.client
        self.assertIn("s.serverSentAt > now + 0.5",c)
        self.assertIn("now - s.serverSentAt > 2",c)
        self.assertIn("s.seq % 1 ~= 0",c)
        self.assertIn("Policy.apply(visual",c)
        self.assertIn("Policy.apply(candidate",c)

    def test_client_uses_authoritative_server_time_clock(self):
        c=self.client
        self.assertIn("workspace:GetServerTimeNow()",c)
        self.assertNotIn("os.clock()",c)
        self.assertIn("s.serverSentAt + 14",c)
        self.assertIn("math.min(visual.telegraphUntil, s.serverSentAt + 2)",c)

    def test_attack_center_is_actual_stomp_position_not_spawn_origin(self):
        c=self.client
        self.assertIn("showRing(s.position, deadline)",c)
        self.assertIn("Vector3.new(position.x, position.y + 0.3, position.z)",c)
        self.assertNotIn("spawnPoint.Position",c)
        self.assertNotIn("Players:GetPlayers()",c)

    def test_no_damage_loot_or_collidable_parts_client(self):
        c=self.client
        for prohibited in ("TakeDamage","FireServer(","DataStore","BindableEvent",
                           "Humanoid","RemoteEvent") :
            if prohibited=="RemoteEvent":
                self.assertNotIn('Instance.new("RemoteEvent")',c)
            else:
                self.assertNotIn(prohibited,c)
        for required in ("part.CanCollide = false","part.CanTouch = false",
                         "part.CanQuery = false","part.Anchored = true"):
            self.assertIn(required,c)

    def test_ring_parts_bounded_and_throttled(self):
        c=self.client
        self.assertIn("local segments = 8",c)
        self.assertIn("if tickBudget < 0.1 then return end",c)
        self.assertIn("local radius = 7",c)
        self.assertIn("part:Destroy()",c)
        self.assertIn("ringUntil > 0 and now >= ringUntil",c)

    def test_cleanup_on_phase_serial_end_expire_destroy(self):
        c=self.client
        self.assertIn('s.phase ~= "ACTIVE" then clearRound()',c)
        self.assertIn('s.visualKind == "END"',c)
        self.assertIn('if result == "EXPIRED" then endVisual() end',c)
        self.assertIn('if result == "ENDED" then endVisual() end',c)
        self.assertIn('lastEventId = nil -- only reset for a NEW epoch or non-ACTIVE phase',c)
        self.assertIn("script.Destroying:Connect",c)
        self.assertIn("connection:Disconnect()",c)
        self.assertIn("heartbeat:Disconnect()",c)

    def test_rojo_maps_two_distinct_clients_and_original_policy(self):
        mapped=self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertEqual(mapped["TrapRaidersHUD"]["$path"],"src/client/HUD.client.luau")
        self.assertEqual(mapped["GoroganVisualPolicy"]["$path"],"src/client/GoroganVisualPolicy.luau")
        self.assertEqual(mapped["S1GoroganStompRing"]["$path"],"src/client/S1GoroganStompRing.client.luau")
        self.assertEqual(len(mapped),4)

    def test_no_duplicate_client_or_server_bootstrap(self):
        self.assertEqual(len(list((GAME/"src/server").glob("*.server.luau"))),1)
        self.assertEqual(len(list((GAME/"src/client").glob("*.client.luau"))),2)

    def test_strict_manifest_once_created(self):
        f=GAME/"BUILD_MANIFEST.json"
        if not f.is_file(): self.skipTest("official generator populates manifest in CI")
        m=json.loads(f.read_bytes())
        self.assertEqual(set(m),{"files","format","game_id","packet_id","public_source_allowed","work_id"})
        files={x["path"]:x for x in m["files"]}
        self.assertEqual(len(files),27)
        self.assertEqual(len(m["files"]),len(files))
        self.assertIn("src/client/GoroganVisualPolicy.luau",files)
        self.assertIn("src/client/S1GoroganStompRing.client.luau",files)
        for p,entry in files.items():
            b=(GAME/p).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),entry["sha256"],p)
            self.assertEqual(len(b),entry["size"],p)

    def test_game_no_production_release_authority(self):
        self.assertNotIn("PublishAsync",self.server)
        self.assertNotIn("DataStoreService",self.server)
        self.assertNotIn("HttpService:PostAsync",self.server)

if __name__=="__main__":
    unittest.main()
