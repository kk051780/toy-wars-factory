"""Actual isolated source-built S1 candidate: exact source, mapping and negative mutation checks.

No Roblox Studio/runtime equivalence is claimed.
"""
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROV = json.loads((ROOT / "docs/INTEGRATION_PROVENANCE.json").read_text(encoding="utf-8"))
EXPECTED_GAME = "TRAP_RAIDERS"
PATCH_SHA = "b2c17440a486cb94d3c033c065ad26e9f991b88411d7fba340e9ce204583cb3d"

def hash_data(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def validate_entry(root, row):
    path = pathlib.PurePosixPath(row["path"])
    if path.is_absolute() or ".." in path.parts or "\\" in row["path"]:
        raise ValueError("bad_path")
    candidate = root / row["path"]
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError("missing_or_symlink")
    data = candidate.read_bytes()
    if len(data) != row["size"] or hash_data(data) != row["sha256"]:
        raise ValueError("byte_or_sha_mismatch")
    return data

class CompositeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "BUILD_MANIFEST.json").read_text(encoding="utf-8"))
        cls.project = json.loads((ROOT / "default.project.json").read_text(encoding="utf-8"))
        cls.game = (ROOT / "src/server/Game.server.luau").read_text(encoding="utf-8")
        cls.hud = (ROOT / "src/client/HUD.client.luau").read_text(encoding="utf-8")

    def test_strict_public_manifest_all_bytes(self):
        self.assertEqual(set(self.manifest), {"files","format","game_id","packet_id","public_source_allowed","work_id"})
        self.assertEqual(self.manifest["format"], "P0D_PUBLIC_SOURCE_V1")
        self.assertEqual(self.manifest["game_id"], EXPECTED_GAME)
        self.assertTrue(self.manifest["public_source_allowed"])
        recorded = self.manifest["files"]
        names = [r["path"] for r in recorded]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 32)
        self.assertNotIn("BUILD_MANIFEST.json", names)
        for row in recorded:
            self.assertEqual(set(row), {"path","sha256","size"})
            validate_entry(ROOT, row)

    def test_only_one_luau_source_changed(self):
        original = PROV["unchanged_original_luau"]
        self.assertEqual(len(original), 19)
        actual = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "src").rglob("*.luau"))
        expected = sorted([e["path"] for e in original] + [PROV["one_changed_executable"]])
        self.assertEqual(actual, expected)
        for row in original:
            data = validate_entry(ROOT, row)
            self.assertEqual(git_blob(data), row["git_blob_sha1"])

    def test_exact_native_verified_result_hud(self):
        self.assertEqual(hash_data(self.hud.encode("utf-8")), PATCH_SHA)
        self.assertEqual(git_blob(self.hud.encode("utf-8")), PROV["chosen_result_HUD_blob_sha1"])
        self.assertIn("-- RESULT_COPY_BEGIN", self.hud)
        self.assertIn("-- RESULT_COPY_END", self.hud)
        for k in ("EGG_CAPTURE", "CASTLE_DESTROYED", "OPPONENT_LEFT", "TEAM_EMPTY", "TIME_LIMIT"):
            self.assertIn(k, self.hud)
        self.assertNotIn("tostring(s.reason)", self.hud)

    def test_only_one_Rojo_HUD_and_FTUE_mount(self):
        scripts = self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertEqual(scripts["TrapRaidersHUD"]["$path"], "src/client/HUD.client.luau")
        self.assertEqual(scripts["TrapRaidersCoach"]["$path"], "src/client/FirstMinuteCoach.client.luau")
        self.assertEqual(sum("HUD.client.luau" in str(v) for v in scripts.values()), 1)
        self.assertEqual(self.project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"], "src/server")
        self.assertEqual(self.project["tree"]["ReplicatedStorage"]["TrapRaidersShared"]["$path"], "src/shared")

    def test_no_second_authority_or_boss_approval(self):
        self.assertIn("local CANONICAL_S1_ENABLED = false", self.game)
        self.assertIn("local D07_D08_RELEASE_REVIEW_APPROVED = false", self.game)
        self.assertEqual(self.game.count("remote.OnServerEvent:Connect"), 1)
        self.assertEqual(self.game.count('remote.Name = "TrapRaidersS1Remote"'), 1)
        self.assertIn('local LobbyTeamRecovery = require', self.game)
        self.assertEqual(self.hud.count("remote:FireServer"), 1)
        self.assertEqual(self.hud.count("remote.OnClientEvent:Connect"), 1)

    def test_provenance_and_status(self):
        self.assertEqual(PROV["base_30_file_game_commit"], "b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc")
        self.assertEqual(PROV["chosen_result_HUD_sha256"], PATCH_SHA)
        self.assertEqual(PROV["studio_status"], "NOT_TESTED")
        status = json.loads((ROOT / "docs/RELEASE_STATUS.json").read_text(encoding="utf-8"))
        self.assertFalse(status["official_rc_branch_modified"])
        self.assertFalse(status["D07_D08_approved_enabled"])
        self.assertFalse(status["live_roblox_publish_approved"])

    def test_mutated_luau_hash_is_rejected(self):
        entry = PROV["unchanged_original_luau"][0]
        data = validate_entry(ROOT, entry)
        modified = data.replace(b"return", b"break_", 1)
        self.assertNotEqual(modified, data)
        self.assertNotEqual(hash_data(modified), entry["sha256"])
        self.assertNotEqual(git_blob(modified), entry["git_blob_sha1"])

    def test_mutated_HUD_hash_is_rejected(self):
        original = self.hud.encode("utf-8")
        tampered = original.replace("勝利！".encode(), "引分！".encode(), 1)
        self.assertNotEqual(tampered, original)
        self.assertNotEqual(hash_data(tampered), PATCH_SHA)

if __name__ == "__main__":
    unittest.main(verbosity=2)
