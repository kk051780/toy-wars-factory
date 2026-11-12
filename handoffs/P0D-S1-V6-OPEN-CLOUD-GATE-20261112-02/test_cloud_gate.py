"""Offline regression; never performs Roblox API calls."""
import hashlib
import json
import pathlib
import unittest
from unittest import mock

import cloud_gate as mod

SCRIPT = mod.PROBE_PATH.read_bytes()


def good():
    return {"environment": "PRIVATE_STAGING", "rc_commit_sha": mod.EXPECTED_RC,
            "universe_id": 10, "place_id": 20, "version_id": 30,
            "probe_sha256": hashlib.sha256(SCRIPT).hexdigest(),
            "owner_approved_for_readonly_cloud_qa": True}


class GateTests(unittest.TestCase):
    def test_valid_pinned_private_staging(self):
        self.assertEqual(mod.validate_receipt(good(), SCRIPT)["version_id"], 30)

    def test_reject_public_environment(self):
        for value in ("PRODUCTION", "PUBLIC", "STAGING"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                mod.validate_receipt({**good(), "environment": value}, SCRIPT)

    def test_reject_old_rc(self):
        with self.assertRaises(ValueError):
            mod.validate_receipt({**good(), "rc_commit_sha": "0" * 40}, SCRIPT)

    def test_reject_unapproved(self):
        with self.assertRaises(ValueError):
            mod.validate_receipt({**good(), "owner_approved_for_readonly_cloud_qa": False}, SCRIPT)

    def test_reject_boolean_ids(self):
        for key in ("universe_id", "place_id", "version_id"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                mod.validate_receipt({**good(), key: True}, SCRIPT)

    def test_reject_missing_or_extra_fields(self):
        d = good(); del d["place_id"]
        with self.assertRaises(ValueError): mod.validate_receipt(d, SCRIPT)
        with self.assertRaises(ValueError): mod.validate_receipt({**good(), "secret": "do not send"}, SCRIPT)

    def test_reject_tampered_script(self):
        with self.assertRaises(ValueError):
            mod.validate_receipt(good(), SCRIPT + b"-- attacker")

    def test_version_pinned_task_endpoint(self):
        self.assertEqual(mod.task_endpoint(good()),
            "https://apis.roblox.com/cloud/v2/universes/10/places/20/versions/30/luau-execution-session-tasks")

    def test_validate_task_path(self):
        name = "universes/10/places/20/versions/30/luau-execution-sessions/abc-10/tasks/task_20"
        self.assertEqual(mod.safe_task_url(name, good()), mod.BASE + name)

    def test_block_path_or_host_injection(self):
        for name in ("https://evil.invalid/", "../../evil", "universes/9/places/20/versions/30/luau-execution-sessions/x/tasks/y", "universes/10/places/20/versions/30/luau-execution-sessions/x/tasks/y?token=1"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                mod.safe_task_url(name, good())

    def test_default_is_offline(self):
        with mock.patch.object(mod, "request_json", side_effect=AssertionError("unexpected network")):
            self.assertEqual(mod.main([]), 0)

    def test_execute_without_approval_fails_before_network(self):
        with mock.patch.object(mod, "request_json", side_effect=AssertionError("unexpected network")):
            with self.assertRaises(ValueError):
                mod.main(["--execute"])

    def test_source_is_read_only(self):
        text = SCRIPT.decode("utf-8")
        for forbidden in ("Instance.new(", ":Destroy(", ":FireServer(", ":FireClient(",
                          "SavePlaceAsync(", "SetAsync(", "UpdateAsync(", ":SetAttribute("):
            self.assertNotIn(forbidden, text)
        for required in ("RED_CASTLE", "BLUE_CASTLE", "S1_GUARDIAN_TRAPS",
                         "TrapRaidersS1Remote", "P0D_CLOUD_GATE_PASS", "provesTwoClientOrMobile = false"):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
