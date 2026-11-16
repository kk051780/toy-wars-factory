#!/usr/bin/env python3
"""Unit regressions for independent P0D V3 concept/RC trace integrity."""
import copy
import json
import unittest

from check_trace import CATALOG, MATRIX, TraceFailure, validate


class DesignTraceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = CATALOG.read_bytes()
        cls.catalog = json.loads(cls.raw)
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_original_catalog_is_mapped_all_67_and_eight_domains(self):
        report = validate(self.catalog, self.matrix, self.raw)
        self.assertEqual(report["mapped"], 67)
        self.assertEqual(len(report["domains"]), 8)
        self.assertEqual(report["historical_claims"], {"RC": 31, "SOURCE": 26, "IDEA": 10})
        self.assertEqual(report["verified_v3_official_adopted"], 0)
        self.assertEqual(report["verified_owner_accepted"], 0)

    def test_reject_absent_feature(self):
        bad = copy.deepcopy(self.matrix)
        bad["rows"].pop(10)
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)

    def test_reject_duplicate_feature(self):
        bad = copy.deepcopy(self.matrix)
        bad["rows"][10]["CONCEPT_ID"] = bad["rows"][9]["CONCEPT_ID"]
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)

    def test_latest_owner_7_roles_and_revival_release_required(self):
        self.assertTrue(all(self.matrix["rows"][i - 1]["RELEASE_REQUIRED"] for i in range(8, 16)))
        self.assertTrue(self.matrix["rows"][18]["RELEASE_REQUIRED"])
        bad = copy.deepcopy(self.matrix)
        bad["rows"][10]["RELEASE_REQUIRED"] = False
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)

    def test_cannot_claim_v3_official_rc_without_exact_binary_and_ci(self):
        bad = copy.deepcopy(self.matrix)
        bad["rows"][9]["V3_NEW_SOURCE_OFFICIAL_ADOPTED"] = True
        bad["verified_v3_new_official_adopted"] = 1
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)

    def test_cannot_claim_owner_fun_before_studio_android_art(self):
        bad = copy.deepcopy(self.matrix)
        bad["rows"][9]["OWNER_ACCEPTED"] = True
        bad["verified_v3_owner_accepted"] = 1
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)

    def test_cannot_forge_source_authority_into_official(self):
        bad = copy.deepcopy(self.matrix)
        bad["rows"][9]["REAL_SOURCE_PATHS_SHA"][0]["official_rc_adopted"] = True
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)

    def test_domain_and_rc_head_fences(self):
        bad = copy.deepcopy(self.matrix)
        bad["rows"][45]["DOMAIN"] = "OTHER"
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)
        bad = copy.deepcopy(self.matrix)
        bad["rows"][0]["ACTUAL_RC_HEAD"] = "0" * 40
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)

    def test_historical_claim_cannot_be_reclassified(self):
        bad = copy.deepcopy(self.matrix)
        bad["rows"][7]["CATALOG_STAGE_CLAIM_HISTORICAL"] = "RC"
        with self.assertRaises(TraceFailure):
            validate(self.catalog, bad, self.raw)


if __name__ == "__main__":
    unittest.main()
