"""Read-only source contract for a REVIEW-ONLY S1 canonical boss patch.

Runs on real GitHub checkout. It never simulates Roblox Lua or claims Studio.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import re
import subprocess
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
GAME = BASE / "candidate"
SOURCE = pathlib.Path("releases/P0D_S1_KIDS_RC01")
ORIGINAL_SHA = {
    "src/server/Game.server.luau": "d7abfc3b6ae1412cad995873faec1c5e4a1a9df1c0971991cff919564a628f3f",
    "src/client/HUD.client.luau": "97ec71f6482f1191ed7daf5e1d797f5621ba7d8c7992e4d1815b4067af968750",
}
# These are exact original public Git blobs, independently fetched by previous
# author lanes; not guessed source fragments or cleanroom alternatives.
ORIGINAL_MODULE_BLOBS = {
    "CanonicalEventBridge": "ce01536e3173e55099c4d6be543f83b9644d1950",
    "ChaosEventCore": "ee8d02ae5175d19904d357a530c05faf80b6bf8a",
    "GoroganAttackReceiptWindow": "bc8e4e954c06c1db8778649a84cda135ff56e9d1",
    "GoroganCombinedRuntime": "f10dedf357476e658857131c0843f237825a1c0f",
    "GoroganDamageBoundary": "031b0c4a5370a891434de42ada8d76642c080433",
    "GoroganRigDriver": "1f6204105be724ca734e2654e42472667a8efcc6",
    "GoroganServerAICore": "f0ecf36242f1543eccf915948129f21f99a6bc92",
    "S1CanonicalRoundHost": None,
    "S1GoroganLiveBindings": "db2a5d2ee5e655b2a9beffe33747cf1fba47c37e",
    "TrustedGoroganActivationMapper": "b30aadc41634f77109559e31cff4d63fabeff19a",
}
class S1ActualGamePatchContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = (GAME / "src/server/Game.server.luau").read_text(encoding="utf-8")
        cls.h = (GAME / "src/client/HUD.client.luau").read_text(encoding="utf-8")
        cls.cfg = json.loads((GAME / "default.project.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((GAME / "BUILD_MANIFEST.json").read_text(encoding="utf-8"))

    def test_pinned_original_game_and_hud_are_real(self):
        for path, sha in ORIGINAL_SHA.items():
            self.assertEqual(hashlib.sha256((SOURCE / path).read_bytes()).hexdigest(), sha)

    def test_entire_original_map_rules_config_are_byte_preserved(self):
        for path in ("src/server/MapBuilder.luau", "src/server/S1Rules.luau",
                     "src/shared/Config.luau", "default.project.json"):
            self.assertEqual((GAME/path).read_bytes(), (SOURCE/path).read_bytes(), path)

    def test_exact_ten_original_and_reviewed_server_modules_staged(self):
        self.assertEqual(len(ORIGINAL_MODULE_BLOBS), 10)
        for name, sha in ORIGINAL_MODULE_BLOBS.items():
            p = GAME / "src/server" / (name + ".luau")
            self.assertTrue(p.is_file(), name)
            if sha is not None:
                blob = subprocess.check_output(["git", "hash-object", str(p)], text=True).strip()
                self.assertEqual(blob, sha, name)

    def test_only_one_server_script_and_original_event_remote(self):
        self.assertEqual([p.name for p in (GAME/"src/server").glob("*.server.luau")], ["Game.server.luau"])
        self.assertEqual(self.g.count('Instance.new("RemoteEvent")'), 1)
        self.assertEqual(self.g.count("OnServerEvent:Connect"), 1)
        self.assertEqual(self.h.count("OnClientEvent:Connect"), 1)

    def test_original_single_round_egg_and_combat_owner_remains(self):
        for token in ["local function tickRound()", "local function stopRound(",
                      "local function resetRound()", "local function applyAttack(",
                      "local function snapshotFor(", "match.eggOwners",
                      "hum:TakeDamage(Config.CombatDamage", "Rules.validSeq"]:
            self.assertIn(token, self.g)
        self.assertEqual(self.g.count("local function tickRound()"), 1)

    def test_cosmetic_second_alarm_scheduler_is_gone(self):
        self.assertNotIn("nextAlarmAt", self.g)
        self.assertNotIn("now + 62", self.g)
        self.assertNotIn("now + 55", self.g)
        self.assertIn("canonicalHost:tick()", self.g)
        self.assertEqual(self.g.count("canonicalHost:tick()"), 1)

    def test_one_trusted_roll_and_two_separate_safety_gates(self):
        self.assertEqual(self.g.count("math.random(0, 99)"), 1)
        self.assertIn("local CANONICAL_S1_ENABLED = false", self.g)
        self.assertIn("local D07_D08_RELEASE_REVIEW_APPROVED = false", self.g)
        self.assertIn("if not CANONICAL_S1_ENABLED or not D07_D08_RELEASE_REVIEW_APPROVED then", self.g)
        self.assertIn("serverRoll = function(_matchId, _epoch)", self.g)

    def test_no_extra_heartbeat_or_client_rng_authority(self):
        self.assertEqual(self.g.count("while true do"), 1)
        self.assertNotIn("RunService.Heartbeat", self.g)
        self.assertNotIn("math.random", self.h)
        self.assertNotIn("Instance.new(\"RemoteEvent\")", self.h)

    def test_bind_genuine_authoritative_callback_factory(self):
        for token in ("BossBinding.new({", "getInvulnerableUntil",
                      "getPlayerTeam = getTeamName",
                      "sendBossVisual = sendBossVisual",
                      "return binding:makeCombined(mapper)",
                      "return binding:abort(roundId)",
                      "CanonicalHost.new({"):
            self.assertIn(token, self.g)

    def test_server_visual_packet_fails_closed_without_correct_epoch(self):
        for token in ('packet.matchId ~= "S1_" .. tostring(match.serial)',
                      'packet.eventId ~= "G07_" .. tostring(match.serial)',
                      'packet.bossId ~= "GOROGAN"', 'packet.seq % 1 ~= 0',
                      'kind = "BOSS_VISUAL"', "serverSentAt = serverNow()"):
            self.assertIn(token, self.g)
        self.assertNotIn("remote:FireServer", self.g)
        self.assertEqual(self.g.count("remote:FireClient(player, {"), 1)

    def test_client_shows_boss_warn_without_damage_or_extra_remote(self):
        for token in ('s.kind == "BOSS_VISUAL"', "s.serial ~= lastSerial",
                      's.eventId ~= "G07_" .. tostring(lastSerial)',
                      's.visualKind == "STOMP"', "workspace:GetServerTimeNow()",
                      "⚠ 巨獣の踏みつけ"):
            self.assertIn(token, self.h)
        self.assertNotIn("Humanoid:TakeDamage", self.h)
        self.assertNotIn("damage =", self.h)

    def test_stop_before_round_switch_both_paths(self):
        self.assertRegex(self.g, r'if match.phase ~= "ACTIVE" then return end\s+stopCanonical\("ROUND_END"\)')
        self.assertRegex(self.g, r'local function resetRound\(\)\s+stopCanonical\("ROUND_RESET"\)\s+match.serial \+= 1')
        self.assertIn('stopCanonical("INIT_FAILED")', self.g)
        self.assertIn('stopCanonical("TICK_FAILED")', self.g)

    def test_mapped_project_uses_single_rojo_game_folder(self):
        self.assertEqual(self.cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"], "src/server")
        self.assertEqual(self.cfg["tree"]["ReplicatedStorage"]["TrapRaidersShared"]["$path"], "src/shared")
        self.assertEqual(self.cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]["TrapRaidersHUD"]["$path"],
                         "src/client/HUD.client.luau")

    def test_package_root_manifest_is_strict_public_source_v1(self):
        self.assertEqual(set(self.manifest), {"files","format","game_id","packet_id","public_source_allowed","work_id"})
        self.assertEqual(self.manifest["format"], "P0D_PUBLIC_SOURCE_V1")
        self.assertEqual(self.manifest["game_id"], "TRAP_RAIDERS")
        self.assertEqual(self.manifest["public_source_allowed"], True)
        self.assertEqual(len(self.manifest["files"]), 25)

    def test_manifest_has_every_candidate_file_once_except_itself(self):
        entries = self.manifest["files"]
        named = [x["path"] for x in entries]
        self.assertEqual(len(named), len(set(named)))
        actual = sorted(p.relative_to(GAME).as_posix() for p in GAME.rglob("*")
                        if p.is_file() and p.name != "BUILD_MANIFEST.json"
                        and "__pycache__" not in p.parts and p.suffix != ".pyc")
        self.assertEqual(sorted(named), actual)
        for entry in entries:
            b = (GAME/entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(), entry["sha256"], entry["path"])
            self.assertEqual(len(b), entry["size"], entry["path"])

    def test_luau_modules_no_second_bootscript(self):
        self.assertFalse(any("CanonicalEventServerAdapter.server" in p.name for p in GAME.rglob("*")))
        self.assertFalse(any("GoroganClientAdapter.client" in p.name for p in GAME.rglob("*")))
        self.assertEqual(len(list((GAME/"src/server").glob("*.luau"))), 13)
        # 1 game Script + 2 game originals + 10 original/host/binding sibling Modules.

    def test_no_claim_of_live_engine_verification(self):
        self.assertNotIn("STUDIO_QA_PASS", self.g)
        self.assertNotIn("PUBLISH_READY", self.g)
        self.assertNotIn("PublishAsync", self.g)
        self.assertNotIn("DataStoreService", self.g)

    def test_s1_core_must_not_mutate_main_or_other_p0(self):
        for term in ("os.execute(", "shell.exec(", "GitHub", "P0A_CAS", "force=true"):
            self.assertNotIn(term, self.g)

if __name__ == "__main__":
    unittest.main()
