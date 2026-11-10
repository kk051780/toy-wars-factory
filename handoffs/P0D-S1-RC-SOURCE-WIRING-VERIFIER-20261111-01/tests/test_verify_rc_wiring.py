"""Adversarial synthetic fixtures for independent S1 release-source QA (NOT game QA)."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from verify_rc_wiring import QAError, audit, read_json

PIN = "a" * 40
CAPS = [
    "match_lifecycle", "team_spawn", "input_mobile", "capture_objective",
    "combat_damage", "victory_defeat", "client_hud", "map_art", "entrypoint",
]


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dump(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


class ReleaseFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.rc = self.parent / "rc"
        self.rc.mkdir()
        self.plan_path = self.parent / "source_plan.json"
        self.project = {
            "name": "TRAP_RAIDERS_S1",
            "tree": {
                "$className": "DataModel",
                "ServerScriptService": {"$path": "src/server"},
                "ReplicatedStorage": {"$path": "src/shared"},
                "StarterPlayer": {"StarterPlayerScripts": {"$path": "src/client"}},
            },
        }
        self.contents = {
            "default.project.json": (json.dumps(self.project, sort_keys=True) + "\n").encode(),
            "src/server/Round.server.luau": b"print('round')\n",
            "src/server/Events.server.luau": b"print('event')\n",
            "src/server/Damage.server.luau": b"print('damage')\n",
            "src/shared/State.luau": b"return {}\n",
            "src/client/HUD.client.luau": b"print('HUD')\n",
        }
        self.units = []
        for rel, data in self.contents.items():
            (self.rc / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.rc / rel).write_bytes(data)
            auth = {
                "src/server/Round.server.luau": "round",
                "src/server/Events.server.luau": "event_chooser",
                "src/server/Damage.server.luau": "damage",
            }.get(rel, "none")
            self.units.append({
                "unit_id": "u" + str(len(self.units)), "source_commit": PIN,
                "source_path": "source/" + rel,
                "target_path": rel, "sha256": digest(data), "authority": auth,
            })
        self.plan = {
            "format": "P0D_CHAT_RELEASE_PLAN_V1", "game_id": "TRAP_RAIDERS",
            "work_id": "p0d-siege-v19", "release_id": "P0D-S1-KIDS-RC01",
            "phase": "CHAT_BUILD_READY", "capabilities": CAPS,
            "studio_status": "NOT_TESTED", "publish_approved": False,
            "units": self.units,
        }
        self.receipt = {
            "format": "P0D_CHAT_SOURCE_ASSEMBLY_RECEIPT_V1",
            "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19",
            "release_id": self.plan["release_id"],
            "source_plan_sha256": "", "studio_status": "NOT_TESTED",
            "release_approved": False, "assembly_status": "CHAT_BUILD_READY__OFFLINE_EVIDENCE_ONLY",
            "contents": [
                {"path": p, "size": len(data), "sha256": digest(data)}
                for p, data in self.contents.items()
            ],
            "source_units": [
                {key: v[key] for key in ("unit_id", "source_commit", "target_path", "sha256")}
                for v in self.units
            ],
        }
        self.save()

    def save(self):
        dump(self.plan_path, self.plan)
        self.receipt["source_plan_sha256"] = digest(self.plan_path.read_bytes())
        dump(self.rc / "CHAT_RC_RECEIPT.json", self.receipt)

    def assertFails(self, substring=None):
        with self.assertRaises(QAError) as caught:
            audit(self.rc, self.plan_path)
        if substring is not None:
            self.assertIn(substring, str(caught.exception))


class TestWiring(ReleaseFixture):
    def test_clean_source_and_three_authorities(self):
        got = audit(self.rc, self.plan_path)
        self.assertEqual(got["result"], "PASS_SOURCE_WIRING_ONLY")
        self.assertEqual(got["source_files_verified"], 6)
        self.assertEqual(got["project_path_mappings_verified"], 3)
        self.assertEqual(len(got["authority_declarations"]), 3)
        self.assertEqual(got["studio_2client_mobile"], "NOT_TESTED")
        self.assertFalse(got["publish_approved"])

    def test_missing_receipt(self):
        (self.rc / "CHAT_RC_RECEIPT.json").unlink()
        self.assertFails("RECEIPT_NOT_FOUND")

    def test_modified_luau(self):
        (self.rc / "src/server/Round.server.luau").write_text("print('tampered')")
        self.assertFails("CONTENT_BYTES_MISMATCH")

    def test_removed_luau(self):
        (self.rc / "src/server/Round.server.luau").unlink()
        self.assertFails("RECEIPT_FILE_MISSING")

    def test_untracked_luau(self):
        (self.rc / "src/server/untracked.server.luau").write_text("print('rogue')")
        self.assertFails("UNTRACKED_OR_UNRECEIPTED_SOURCE")

    def test_plan_tampering_rejected(self):
        self.plan["release_id"] = "INJECTED"
        dump(self.plan_path, self.plan)
        self.assertFails("RELEASE_ID_MISMATCH")

    def test_plan_same_release_modified_rejected(self):
        self.plan["units"][1]["depends_on"] = ["u0"]
        dump(self.plan_path, self.plan)
        self.assertFails("SOURCE_PLAN_BYTES_MISMATCH")

    def test_receipt_tampered_commit(self):
        self.receipt["source_units"][1]["source_commit"] = "f" * 40
        self.save()
        self.assertFails("PLAN_UNIT_NOT_IN_RECEIPT")

    def test_invalid_commit_format(self):
        self.receipt["source_units"][0]["source_commit"] = "not40"
        self.save()
        self.assertFails("RECEIPT_UNIT_ID_OR_SHA_INVALID")

    def test_duplicate_receipt_source_path(self):
        self.receipt["contents"].append(copy.deepcopy(self.receipt["contents"][0]))
        self.save()
        self.assertFails("DUPLICATE_CONTENT_PATH")

    def test_duplicate_authority_declared(self):
        self.plan["units"][5]["authority"] = "round"
        self.save()
        self.assertFails("DUPLICATE_OR_INVALID_AUTHORITY")

    def test_removed_event_chooser_authority(self):
        self.plan["units"][2]["authority"] = "none"
        self.save()
        self.assertFails("MISSING_CANONICAL_AUTHORITY")

    def test_studio_claim_denied(self):
        self.receipt["studio_status"] = "PASS"
        self.save()
        self.assertFails("STUDIO_OR_LIVE_RELEASE_CLAIM_FORBIDDEN")

    def test_release_claim_denied(self):
        self.receipt["release_approved"] = True
        self.save()
        self.assertFails("STUDIO_OR_LIVE_RELEASE_CLAIM_FORBIDDEN")

    def test_missing_project_mapping(self):
        self.project["tree"]["ServerScriptService"]["$path"] = "src/missing"
        self.replace_project()
        self.assertFails("PROJECT_MAPPING_NOT_FOUND")

    def test_project_path_traversal(self):
        self.project["tree"]["ServerScriptService"]["$path"] = "src/../../escape"
        self.replace_project()
        self.assertFails("PATH_TRAVERSAL")

    def test_server_script_misplaced_into_shared(self):
        self.project["tree"]["ReplicatedStorage"]["$path"] = "src/server"
        self.project["tree"]["ServerScriptService"]["$path"] = "src/shared"
        self.replace_project()
        self.assertFails("SERVER_SCRIPT_OUTSIDE_SERVER")

    def test_client_script_misplaced_into_server(self):
        self.project["tree"]["ServerScriptService"]["$path"] = "src/client"
        self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["$path"] = "src/server"
        self.replace_project()
        self.assertFails("CLIENT_SCRIPT_OUTSIDE_CLIENT")

    def test_server_unmounted(self):
        self.project["tree"]["ServerScriptService"]["$path"] = "src/shared"
        self.replace_project()
        self.assertFails("SOURCE_LUAU_NOT_MOUNTED")

    def test_case_collision_in_source(self):
        (self.rc / "src/server/ROUND.server.luau").write_text("-- malicious shadow")
        self.assertFails("CASE_COLLISION")

    def test_case_collision_directory(self):
        (self.rc / "SRC").mkdir()
        self.assertFails("CASE_COLLISION_DIRECTORY")

    def test_source_symlink_blocked(self):
        a = self.rc / "src/server/shortcut.server.luau"
        try:
            a.symlink_to(self.rc / "src/server/Round.server.luau")
        except (OSError, NotImplementedError):
            self.skipTest("symlink denied by platform")
        self.assertFails("SYMLINK_OR_NONFILE")

    def test_duplicate_json_key_denied(self):
        (self.rc / "CHAT_RC_RECEIPT.json").write_text('{"format":"a","format":"b"}')
        self.assertFails("JSON_DUPLICATE_KEY")

    def test_non_asset_project_path(self):
        (self.rc / "src/shared/State.luau").unlink()
        (self.rc / "src/shared/State.txt").write_text("hello")
        self.assertFails("RECEIPT_FILE_MISSING")

    def replace_project(self):
        b = (json.dumps(self.project, sort_keys=True) + "\n").encode()
        (self.rc / "default.project.json").write_bytes(b)
        self.plan["units"][0]["sha256"] = digest(b)
        self.receipt["source_units"][0]["sha256"] = digest(b)
        self.receipt["contents"][0]["sha256"] = digest(b)
        self.receipt["contents"][0]["size"] = len(b)
        self.save()


if __name__ == "__main__":
    unittest.main(verbosity=2)
