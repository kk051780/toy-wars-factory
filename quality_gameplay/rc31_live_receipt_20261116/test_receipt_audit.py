"""Mutation-oriented regression tests for RC31 read-only head/eight-domain receipts."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).with_name("receipt_audit.py")
spec = importlib.util.spec_from_file_location("receipt_audit", MODULE)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)

OLD = "a" * 40
HEAD = "b" * 40


def fixtures():
    owners = {owner: OLD for names in gate.LANES.values() for owner in names}
    manifest = {
        "canonical_branch": "rc/p0d-s1-kids-rc01",
        "enabled": True,
        "source_count": 31,
        "source_heads": owners,
        "feature_flags": {key: True for key in gate.FLAGS},
        "publication_authorized": False,
        "last_verified_rc_run": {"rc_head_sha": OLD, "run_id": 123},
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "art_fun_owner": "NO_GO",
    }
    active = {
        "active_profile": "rich51",
        "source_profiles": {
            "eggrumble_v3_31": {
                "source_count": 31,
                "source_manifest": "rc_fastlane/EGGRUMBLE_V3_ACTIVE.json",
                "last_verified_rc_run": {"rc_head_sha": OLD},
            }
        },
    }
    catalog = {"verified_rc_head": OLD, "rows": [
        {"id": "P0D-001", "stage": "RC"},
        {"id": "P0D-008", "stage": "SOURCE"},
        {"id": "P0D-011", "stage": "IDEA"},
    ]}
    return manifest, active, catalog


class ReceiptTests(unittest.TestCase):
    def test_eight_lanes_and_historical_receipt_not_claimed_current(self):
        m, a, c = fixtures()
        r = gate.audit(m, a, c, HEAD)
        self.assertEqual(set(r["eight_lane_author_pins_present"]), set(gate.LANES))
        self.assertFalse(r["recorded_receipts_match_live_head"])
        self.assertEqual(r["receipt_status"], "HISTORICAL_RECEIPT_ONLY")
        self.assertEqual(r["same_head_actual_ci"], "NOT_VERIFIED_BY_THIS_AUDIT")
        self.assertIsNone(r["zip_bytes"])
        self.assertFalse(r["v3_is_primary"])
        self.assertFalse(r["release_accepted"])

    def test_receipt_only_fresh_when_both_manifests_same_live_head(self):
        m, a, c = fixtures()
        m["last_verified_rc_run"]["rc_head_sha"] = HEAD
        a["source_profiles"]["eggrumble_v3_31"]["last_verified_rc_run"]["rc_head_sha"] = HEAD
        r = gate.audit(m, a, c, HEAD)
        self.assertTrue(r["recorded_receipts_match_live_head"])
        self.assertEqual(r["receipt_status"], "CURRENT_RECORDED_HEAD_ONLY")
        self.assertEqual(r["same_head_actual_ci"], "NOT_VERIFIED_BY_THIS_AUDIT")

    def test_one_manifest_stale_must_stay_historical(self):
        m, a, c = fixtures()
        m["last_verified_rc_run"]["rc_head_sha"] = HEAD
        self.assertFalse(gate.audit(m, a, c, HEAD)["recorded_receipts_match_live_head"])

    def test_reject_invalid_source_pin_per_domain(self):
        for lane, owners in gate.LANES.items():
            with self.subTest(lane=lane):
                m, a, c = fixtures()
                m["source_heads"][owners[0]] = "not-a-sha"
                with self.assertRaisesRegex(ValueError, lane):
                    gate.audit(m, a, c, HEAD)

    def test_reject_missing_required_source_flag(self):
        for flag in gate.FLAGS:
            with self.subTest(flag=flag):
                m, a, c = fixtures()
                m["feature_flags"][flag] = False
                with self.assertRaisesRegex(ValueError, "flag"):
                    gate.audit(m, a, c, HEAD)

    def test_reject_duplicate_catalog_ids(self):
        m, a, c = fixtures()
        c["rows"].append(copy.deepcopy(c["rows"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            gate.audit(m, a, c, HEAD)

    def test_reject_unknown_catalog_stage(self):
        m, a, c = fixtures()
        c["rows"][0]["stage"] = "FAKE_PASS"
        with self.assertRaisesRegex(ValueError, "unknown stage"):
            gate.audit(m, a, c, HEAD)

    def test_reject_fake_source_count(self):
        m, a, c = fixtures()
        m["source_count"] = 30
        with self.assertRaisesRegex(ValueError, "31 sources"):
            gate.audit(m, a, c, HEAD)

    def test_reject_primary_manifest_mismatch(self):
        m, a, c = fixtures()
        a["source_profiles"]["eggrumble_v3_31"]["source_count"] = 30
        with self.assertRaisesRegex(ValueError, "disagree"):
            gate.audit(m, a, c, HEAD)

    def test_reject_improper_publication_authority(self):
        m, a, c = fixtures()
        m["publication_authorized"] = True
        with self.assertRaisesRegex(ValueError, "publication"):
            gate.audit(m, a, c, HEAD)

    def test_no_cas_or_release_claim_if_primary_profile_switches(self):
        m, a, c = fixtures()
        a["active_profile"] = "eggrumble_v3_31"
        r = gate.audit(m, a, c, HEAD)
        self.assertTrue(r["v3_is_primary"])
        self.assertFalse(r["release_accepted"])
        self.assertEqual(r["owner_fun"], "NO_GO")

    def test_reject_non_hex_live_sha(self):
        m, a, c = fixtures()
        with self.assertRaisesRegex(ValueError, "official_head"):
            gate.audit(m, a, c, "main")

    def test_cli_returns_2_for_stale_when_requested(self):
        m, a, c = fixtures()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "rc_fastlane"
            folder.mkdir()
            for name, obj in [("EGGRUMBLE_V3_ACTIVE.json", m),
                              ("ACTIVE.json", a), ("FEATURE_CATALOG.json", c)]:
                (folder / name).write_text(json.dumps(obj), encoding="utf-8")
            with patch.object(sys, "argv", [
                "receipt_audit", "--repo-root", str(root), "--official-head", HEAD,
                "--require-current-recorded-receipt",
            ]):
                self.assertEqual(gate.main(), 2)


if __name__ == "__main__":
    unittest.main()
