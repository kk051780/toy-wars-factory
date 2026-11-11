#!/usr/bin/env python3
"""Read-only source regression for two corrective S1 Luau modules.

Native Luau and Roblox Studio are NOT run by this suite.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOST = (ROOT / "src/server/S1CanonicalRoundHost.luau").read_text("utf-8")
BIND = (ROOT / "src/server/S1GoroganLiveBindings.luau").read_text("utf-8")
LOCK = json.loads((ROOT / "SOURCE_LOCK.json").read_text("utf-8"))

def gitblob(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()

def select_user(ids, actor_id):
    if not isinstance(actor_id, str) or not re.fullmatch(r"-?\d+", actor_id):
        return None
    matches = [uid for uid in ids if str(uid) == actor_id]
    return matches[0] if len(matches) == 1 else None

def terminal(closed, reason, active, same_epoch, good_tick, current, retired, enabled):
    if closed:
        return bool(reason == "EVENT_FINISHED" and active and same_epoch)
    if not good_tick:
        return False
    if current:
        return True
    return bool(retired and enabled)

class PublicPacketContract(unittest.TestCase):
    def test_pinned_source_blob(self):
        names = {p["path"]: p["git_blob_sha1"] for p in LOCK["corrections"]}
        for rel, expected in names.items():
            data = (ROOT / rel).read_bytes()
            self.assertEqual(gitblob(data), expected)
    def test_packet_source_only(self):
        self.assertTrue(LOCK["source_only"])
        self.assertFalse(LOCK["studio_tested"])
        self.assertFalse(LOCK["release_approved"])
    def test_two_unique_source_targets(self):
        self.assertEqual(len({v["path"] for v in LOCK["corrections"]}), 2)
    def test_git_original_commit_pins(self):
        self.assertEqual(LOCK["baseline_source_commit"], "4b66dd8a9b34a45cf12e58684e0e4372df3f8b07")
        self.assertEqual(LOCK["original_host_git_blob"], "db28bafed6372f9fb2d4fa53c433d046999b64e2")
        self.assertEqual(LOCK["original_binding_git_blob"], "db2a5d2ee5e655b2a9beffe33747cf1fba47c37e")
    def test_manifest_schema_and_exact_source_files(self):
        m = json.loads((ROOT / "BUILD_MANIFEST.json").read_text("utf-8"))
        self.assertEqual(set(m), {"files", "format", "game_id", "work_id",
                                  "packet_id", "public_source_allowed"})
        self.assertEqual(m["format"], "P0D_PUBLIC_SOURCE_V1")
        self.assertEqual(m["game_id"], "TRAP_RAIDERS")
        self.assertTrue(m["public_source_allowed"])
        listed = {x["path"] for x in m["files"]}
        actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        self.assertEqual(actual, listed | {"BUILD_MANIFEST.json"})
        for row in m["files"]:
            self.assertEqual(set(row), {"path", "size", "sha256"})
            v = (ROOT / row["path"]).read_bytes()
            self.assertEqual(len(v), row["size"])
            self.assertEqual(hashlib.sha256(v).hexdigest(), row["sha256"])

class HostSourceContract(unittest.TestCase):
    def test_terminal_success_reason(self):
        self.assertIn('self:stop("EVENT_FINISHED")', HOST)
        self.assertIn('return true, "EVENT_FINISHED"', HOST)
    def test_terminates_only_attested_retired_current_epoch(self):
        self.assertIn('self.bridge.retired[key] ~= true', HOST)
        self.assertIn('self.bridge.enabled ~= true', HOST)
        self.assertIn('self.activeEpoch', HOST)
    def test_must_match_live_game_epoch(self):
        self.assertIn('m.serial ~= self.activeEpoch', HOST)
        self.assertIn('m.phase ~= "ACTIVE"', HOST)
    def test_stale_fails_closed(self):
        self.assertIn('return false, "STALE_TERMINAL_HOST"', HOST)
    def test_original_false_failure_still_fails(self):
        self.assertIn('self:stop("D08_FAILED")', HOST)
        self.assertIn('return false, why or "D08_FAILED"', HOST)
    def test_no_extra_chooser_or_remote(self):
        self.assertNotIn("OnServerEvent:Connect", HOST)
        self.assertNotIn('Instance.new("RemoteEvent")', HOST)
        self.assertNotIn("math.random(", HOST)
    def test_original_host_api_retained(self):
        for marker in ("function Host.new(deps)", "function Host:tick()",
                       "function Host:stop(reason)", "function Host:status()"):
            self.assertIn(marker, HOST)

class PlayerBindingSourceContract(unittest.TestCase):
    def test_exact_server_roster_mapping(self):
        self.assertIn('tostring(player.UserId) == playerId', BIND)
        self.assertIn("Players:GetPlayers()", BIND)
    def test_studio_negative_user_id(self):
        self.assertIn('playerId:match("^%-?%d+$")', BIND)
        self.assertNotIn('playerId:match("^%d+$")', BIND)
    def test_duplicate_user_id_fails_closed(self):
        self.assertIn("if found ~= nil then return nil end", BIND)
    def test_original_core_and_gate_unmodified(self):
        self.assertIn('local Combined = require(script.Parent:WaitForChild("GoroganCombinedRuntime"))', BIND)
        self.assertIn('local Gate = require(script.Parent:WaitForChild("GoroganDamageBoundary"))', BIND)
    def test_binding_cannot_receive_client_remote(self):
        self.assertNotIn("OnServerEvent:Connect", BIND)
        self.assertNotIn("FireServer(", BIND)
    def test_damage_gate_unique_existing(self):
        self.assertIn('function Binding:makeCombined(mapper)', BIND)
        self.assertNotIn(':TakeDamage(', BIND)

class IdentityAndEventOracle(unittest.TestCase):
    def test_valid_real_player(self):
        self.assertEqual(select_user([12, 123], "123"), 123)
    def test_studio_negative_one(self):
        self.assertEqual(select_user([-1, -2], "-1"), -1)
    def test_studio_negative_two(self):
        self.assertEqual(select_user([-1, -2], "-2"), -2)
    def test_leading_zero_alias_rejected(self):
        self.assertIsNone(select_user([12], "012"))
    def test_duplicate_id_rejected(self):
        self.assertIsNone(select_user([-1, -1], "-1"))
    def test_client_like_injection_rejected(self):
        self.assertIsNone(select_user([-1], "-1;DROP"))
    def test_unknown_actor_rejected(self):
        self.assertIsNone(select_user([99], "-1"))
    def test_normal_roll_boundaries(self):
        def classify(r): return "NORMAL" if r < 65 else "BOSS" if r < 90 else "WEATHER"
        self.assertEqual([classify(x) for x in [0,64,65,89,90,99]],
                         ["NORMAL","NORMAL","BOSS","BOSS","WEATHER","WEATHER"])
    def test_ongoing_event_allowed(self):
        self.assertTrue(terminal(False,"",True,True,True,True,False,True))
    def test_attested_terminal_allowed(self):
        self.assertTrue(terminal(False,"",True,True,True,False,True,True))
    def test_repeat_same_epoch_allowed(self):
        self.assertTrue(terminal(True,"EVENT_FINISHED",True,True,False,False,True,False))
    def test_stale_epoch_rejected(self):
        self.assertFalse(terminal(True,"EVENT_FINISHED",True,False,False,False,True,False))
    def test_closed_wrong_reason_rejected(self):
        self.assertFalse(terminal(True,"D08_FAILED",True,True,False,False,True,False))
    def test_unattested_terminal_rejected(self):
        self.assertFalse(terminal(False,"",True,True,True,False,False,True))
    def test_disabled_terminal_rejected(self):
        self.assertFalse(terminal(False,"",True,True,True,False,True,False))
    def test_runtime_failure_rejected(self):
        self.assertFalse(terminal(False,"",True,True,False,False,True,True))

if __name__ == "__main__":
    unittest.main(verbosity=2)
