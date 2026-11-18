"""Validate historical Core36 adoption receipt against both canonical manifests.

This script proves internal receipt *consistency*, not that the Roblox Studio
engine, Android, FUN or current future RC HEAD has passed. No author game source
is copied, patched or executed by this checker.
"""
import argparse
import copy
import json
import re
import unittest
from pathlib import Path

HEAD = "f77b4d4393d9e9b19b65566413432a7a9f13962b"
RUN = 44232589275
ARTIFACT_ID = 14396515259
ZIP_BYTES = 366128

def validate(active, core):
    assert active["active_profile"] == "rich51", "do not switch S1 default"
    v3 = active["source_profiles"]["eggrumble_v3_core36"]
    assert v3["source_count"] == core["source_count"] == 36
    assert core["baseline_source_count"] == 31
    assert core["source_profile"] == "eggrumble_v3_core36"
    assert core["primary_s1_profile_unchanged"] == "rich51"
    assert core["production_published"] is False
    assert v3["status"] == "RC_SOURCE_ADOPTED_AT_VERIFIED_HEAD_NOT_STUDIO_ACCEPTED"
    a = core["acceptance"]
    for key in ("same_head_source_compiler", "same_head_rojo_source_class", "off31"):
        assert a[key] == "SUCCESS_AT_VERIFIED_HEAD", key
    assert a["official_nonforce_expected_sha_cas"] is True
    assert a["same_head_receipt_is_historical"] is True
    for key in ("studio_2client", "android_15min", "human_fun"):
        assert a[key] == "NOT_TESTED", key
    assert a["owner_acceptance"] is False
    r = core["verified_rc_source_receipt"]
    s = v3["last_verified_source_receipt"]
    assert re.fullmatch(r"[0-9a-f]{40}", r["official_rc_head"])
    assert r["official_rc_head"] == s["official_rc_head"] == HEAD
    assert r["official_workflow_run_id"] == s["run_id"] == RUN
    assert r["official_workflow_conclusion"] == s["conclusion"] == "success"
    assert r["official_artifact_id"] == ARTIFACT_ID
    assert r["official_artifact_zip_bytes"] == s["artifact_zip_bytes"] == ZIP_BYTES
    assert r["artifact_is_zip_not_rbxlx"] is True
    assert r["actual_studio_rbxlx_bytes"] == "UNKNOWN_NOT_MEASURED"
    assert r["source_count_on"] == 36 and r["source_count_off"] == 31
    assert r["adoption_scope"] == "PRIVATE_V3_SOURCE_ONLY"
    assert r["current_rc_head_must_be_rechecked"] is True
    assert r["no_owner_fun_studio_android_acceptance"] is True
    assert core["server_authorities"]["combat"] == 1
    assert core["server_authorities"]["host"] == 1
    assert core["server_authorities"]["swarm"] == 1
    assert core["server_authorities"]["new_remote_owner"] == 0
    assert core["server_authorities"]["new_store_owner"] == 0
    return True

class ReceiptRegression(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.active = json.loads((root / "rc_fastlane/ACTIVE.json").read_text())
        self.core = json.loads((root / "rc_fastlane/EGGRUMBLE_V3_CORE36.json").read_text())

    def test_verified_historical_receipt(self):
        self.assertTrue(validate(self.active, self.core))

    def test_fake_studio_acceptance_rejected(self):
        candidate = copy.deepcopy(self.core)
        candidate["acceptance"]["studio_2client"] = "PASS"
        with self.assertRaises(AssertionError):
            validate(self.active, candidate)

    def test_fake_artifact_not_accepted_as_place(self):
        candidate = copy.deepcopy(self.core)
        candidate["verified_rc_source_receipt"]["artifact_is_zip_not_rbxlx"] = False
        with self.assertRaises(AssertionError):
            validate(self.active, candidate)

    def test_stale_run_or_head_cannot_pass(self):
        candidate = copy.deepcopy(self.core)
        candidate["verified_rc_source_receipt"]["official_workflow_run_id"] = RUN - 1
        with self.assertRaises(AssertionError):
            validate(self.active, candidate)
        candidate = copy.deepcopy(self.active)
        candidate["source_profiles"]["eggrumble_v3_core36"]["last_verified_source_receipt"]["official_rc_head"] = "0"*40
        with self.assertRaises(AssertionError):
            validate(candidate, self.core)

    def test_cannot_switch_live_default_or_claim_publish(self):
        candidate = copy.deepcopy(self.active)
        candidate["active_profile"] = "eggrumble_v3_core36"
        with self.assertRaises(AssertionError):
            validate(candidate, self.core)
        candidate = copy.deepcopy(self.core)
        candidate["production_published"] = True
        with self.assertRaises(AssertionError):
            validate(self.active, candidate)

if __name__ == "__main__":
    unittest.main()
