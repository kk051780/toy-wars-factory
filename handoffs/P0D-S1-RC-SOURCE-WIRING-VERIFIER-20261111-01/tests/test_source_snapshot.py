"""Synthetic adversarial tests for source snapshot gate. Not real game tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from verify_source_snapshot import QAError, audit_source


def encode(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()


class SnapshotFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = {
            "README.md": b"source only\n",
            "default.project.json": encode({"name": "TRAP RAIDERS", "tree": {
                "$className": "DataModel",
                "ServerScriptService": {"$path": "src/server"},
                "ReplicatedStorage": {"$path": "src/shared"},
                "StarterPlayer": {"StarterPlayerScripts": {"$path": "src/client"}},
            }}),
            "docs/RELEASE_STATUS.json": encode({
                "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19",
                "release_id": "P0D-S1-KIDS-RC01", "game_ready": False,
                "studio_status": "NOT_TESTED", "release_approved": False}),
            "src/server/Game.server.luau": b"print('game')\n",
            "src/server/Rules.luau": b"return {}\n",
            "src/shared/Config.luau": b"return {}\n",
            "src/client/HUD.client.luau": b"print('hud')\n",
            "tests/test_game.py": b"assert True\n",
        }
        self.manifest = {"format": "P0D_PUBLIC_SOURCE_V1", "game_id": "TRAP_RAIDERS",
                         "work_id": "p0d-siege-v19", "public_source_allowed": True,
                         "files": []}
        self.flush()

    def flush(self):
        entries = []
        for rel, blob in self.raw.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
            entries.append({"path": rel, "sha256": hashlib.sha256(blob).hexdigest(), "size": len(blob)})
        self.manifest["files"] = entries
        (self.root / "BUILD_MANIFEST.json").write_bytes(encode(self.manifest))

    def deny(self, contains):
        with self.assertRaises(QAError) as err:
            audit_source(self.root)
        self.assertIn(contains, str(err.exception))


class SourceSnapshotTests(SnapshotFixture):
    def test_good_pre_rc(self):
        report = audit_source(self.root)
        self.assertEqual(report["status"], "PASS_SOURCE_SNAPSHOT_ONLY__NOT_FINAL_RC")
        self.assertEqual(report["source_files_sha256_verified"], len(self.raw))
        self.assertEqual(report["rojo_project_mappings_verified"], 3)
        self.assertFalse(report["publish_approved"])
        self.assertEqual(report["studio_2client_mobile"], "NOT_TESTED")

    def test_sha_tampered_source(self):
        (self.root / "src/server/Game.server.luau").write_text("print('malicious')")
        self.deny("FILE_CONTENT_DIGEST_MISMATCH")

    def test_source_delete(self):
        (self.root / "src/shared/Config.luau").unlink()
        self.deny("MISSING_MANIFESTED_FILE")

    def test_source_add_not_in_manifest(self):
        (self.root / "src/server/Other.server.luau").write_text("print(1)")
        self.deny("UNTRACKED_SOURCE_OR_FILE")

    def test_manifest_duplicate(self):
        self.manifest["files"].append(copy.deepcopy(self.manifest["files"][0]))
        (self.root / "BUILD_MANIFEST.json").write_bytes(encode(self.manifest))
        self.deny("DUPLICATE_MANIFEST_ENTRY")

    def test_manifest_wrong_sha(self):
        self.manifest["files"][1]["sha256"] = "0" * 64
        (self.root / "BUILD_MANIFEST.json").write_bytes(encode(self.manifest))
        self.deny("FILE_CONTENT_DIGEST_MISMATCH")

    def test_false_ready_status(self):
        status = json.loads(self.raw["docs/RELEASE_STATUS.json"])
        status["game_ready"] = True
        self.raw["docs/RELEASE_STATUS.json"] = encode(status)
        self.flush()
        self.deny("FALSE_STUDIO_OR_GAME_READY_CLAIM")

    def test_false_studio_pass(self):
        status = json.loads(self.raw["docs/RELEASE_STATUS.json"])
        status["studio_status"] = "PASS"
        self.raw["docs/RELEASE_STATUS.json"] = encode(status)
        self.flush()
        self.deny("FALSE_STUDIO_OR_GAME_READY_CLAIM")

    def test_false_owner_approval(self):
        status = json.loads(self.raw["docs/RELEASE_STATUS.json"])
        status["release_approved"] = True
        self.raw["docs/RELEASE_STATUS.json"] = encode(status)
        self.flush()
        self.deny("FALSE_RELEASE_APPROVAL")

    def test_missing_status(self):
        self.raw.pop("docs/RELEASE_STATUS.json")
        (self.root / "docs/RELEASE_STATUS.json").unlink()
        self.flush()
        self.deny("MISSING_SOURCE_STATUS")

    def test_broken_project_mapping(self):
        project = json.loads(self.raw["default.project.json"])
        project["tree"]["ServerScriptService"]["$path"] = "src/deleted"
        self.raw["default.project.json"] = encode(project)
        self.flush()
        self.deny("PROJECT_MAPPING_NOT_FOUND")

    def test_unmounted_script(self):
        self.raw["src/server/HIDDEN.luau"] = b"return {}"
        self.flush()
        self.assertEqual(audit_source(self.root)["source_files_sha256_verified"], len(self.raw))
        # a new file within mounted server subtree is valid; outside tree is not.
        self.raw.pop("src/server/HIDDEN.luau")
        self.raw["src/unmounted/HIDDEN.luau"] = b"return {}"
        self.flush()
        (self.root / "src/server/HIDDEN.luau").unlink()
        self.deny("SOURCE_LUAU_NOT_MOUNTED")

    def test_wrong_client_mount(self):
        project = json.loads(self.raw["default.project.json"])
        project["tree"]["ServerScriptService"]["$path"] = "src/client"
        project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["$path"] = "src/server"
        self.raw["default.project.json"] = encode(project)
        self.flush()
        self.deny("CLIENT_SCRIPT_OUTSIDE_CLIENT")

    def test_wrong_path_traversal(self):
        self.manifest["files"][0]["path"] = "../../escape"
        (self.root / "BUILD_MANIFEST.json").write_bytes(encode(self.manifest))
        self.deny("PATH_TRAVERSAL")

    def test_unexpected_source_root(self):
        self.raw["private.txt"] = b"secret"
        self.flush()
        self.deny("UNEXPECTED_MANIFEST_PATH")

    def test_missing_server_bootstrap(self):
        self.raw.pop("src/server/Game.server.luau")
        self.raw["src/server/Game.luau"] = b"return {}"
        self.flush()
        (self.root / "src/server/Game.server.luau").unlink()
        self.deny("NO_SERVER_BOOTSTRAP")

    def test_missing_client_bootstrap(self):
        self.raw.pop("src/client/HUD.client.luau")
        self.raw["src/client/HUD.luau"] = b"return {}"
        self.flush()
        (self.root / "src/client/HUD.client.luau").unlink()
        self.deny("NO_CLIENT_BOOTSTRAP")

    def test_symlink_denied(self):
        dest = self.root / "src/server/symlink.server.luau"
        try:
            dest.symlink_to(self.root / "src/server/Game.server.luau")
        except (OSError, NotImplementedError):
            self.skipTest("symlink unsupported")
        self.deny("SYMLINK_OR_NONFILE")

    def test_false_rc_receipt(self):
        (self.root / "CHAT_RC_RECEIPT.json").write_text("{}")
        self.deny("UNTRACKED_SOURCE_OR_FILE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
