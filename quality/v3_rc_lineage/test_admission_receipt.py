"""Evaluate an RC intake without claiming Roblox execution or OWNER approval."""
import copy
import unittest

from admission_receipt import DOMAINS, evaluate


def fixtures():
    sha_a, sha_q, sha_art, sha_score, sha_rc = ["a"*40, "b"*40, "c"*40, "d"*40, "e"*40]
    bits = {"EGGRUMBLE_Mod%02d" % i: ("%064x" % (i + 1)) for i in range(26)}
    source = {
        "schema": "EGGRUMBLE_V3_RC_LINEAGE_V1",
        "status": "SOURCE_GATE_PASS", "full_26_owner_byte_identity": True,
        "source_count_author": 21, "source_count_candidate": 26,
        "quality_source_equivalent_to_live_head": True,
        "domain_inventory": {d: True for d in DOMAINS},
        "owner_heads": {"#482": sha_a, "#484": sha_q, "#485": sha_art, "#487": sha_score},
        "quality_live_head": sha_q,
        "latest_rc_sha": sha_rc,
        "candidate_source_sha256": bits,
        "official_rc_integrated": False,
    }
    composer = {
        "status": "SOURCE_ONLY_NOT_OFFICIAL_RC",
        "script_count": 26, "server_count": 23, "client_count": 3,
        "source_sha256": bits.copy(),
        "owner_accepted": False,
    }
    live = {
        "schema": "P0D_EGGRUMBLE_LIVE_RC_INTAKE_DRIFT_V2",
        "decision": "SOURCE_REVIEW_READY_ONLY", "blockers": [],
        "heads": {"author":sha_a,"quality":sha_q,"art":sha_art,"score":sha_score},
        "official_rc_head":sha_rc,
        "target_candidate_script_count":26,
        "composite_ci":{"head":sha_q,"status":"completed","conclusion":"success","run_id":1},
        "runtime_activation": {
            "schema":"EGGRUMBLE_RUNTIME_ACTIVATION_V1",
            "source_guard_inspection":"COMPLETE",
            "production_runtime":"BLOCKED_STUDIO_ONLY_GAME_HOST",
            "eight_domain_production_impact":list(DOMAINS)
        },
        "product_go":False
    }
    return source, composer, live


class TestRCAdmissionReceipt(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c = fixtures()

    def decision(self):
        return evaluate(self.a, self.b, self.c)

    def assert_block(self, code):
        result = self.decision()
        self.assertEqual(result["status"], "SOURCE_NO_GO")
        self.assertIn(code, result["errors"])

    def test_actual_eight_domain_source_ready_is_not_product_ready(self):
        result = self.decision()
        self.assertEqual(result["status"], "SOURCE_READY_PRODUCTION_BLOCKED", result["errors"])
        self.assertEqual(set(result["production_blocked_domains"]), set(DOMAINS))
        self.assertTrue(all(not v["product_go"] for v in result["domain_stage"].values()))
        self.assertEqual(result["official_rc_integration"], "NOT_INTEGRATED_OR_UNVERIFIED")
        self.assertFalse(result["owner_accepted"])

    def test_one_changed_real_luau_byte_blocks_intake(self):
        name = next(iter(self.b["source_sha256"]))
        self.b["source_sha256"][name] = "f"*64
        self.assert_block("COMPOSER_SOURCE_BYTES_DISAGREE")

    def test_missing_artist_module_blocks_intake(self):
        self.b["source_sha256"].pop(next(iter(self.b["source_sha256"])))
        self.assert_block("COMPOSER_SOURCE_BYTES_DISAGREE")

    def test_quality_latest_head_mismatch_blocks_intake(self):
        self.c["heads"]["quality"] = "0"*40
        self.assert_block("LIVE_QUALITY_HEAD_MISMATCH")

    def test_official_rc_head_changed_blocks_intake(self):
        self.c["official_rc_head"] = "0"*40
        self.assert_block("OFFICIAL_RC_HEAD_MISMATCH")

    def test_seven_domains_not_eight_is_no_go(self):
        self.a["domain_inventory"].pop("item")
        self.assert_block("INCOMPLETE_EIGHT_DOMAIN_INVENTORY")

    def test_unknown_runtime_source_report_fails_closed(self):
        self.c["runtime_activation"] = {}
        self.assert_block("PRODUCTION_ACTIVATION_INSPECTION_UNAVAILABLE")

    def test_real_ci_not_success_fails(self):
        self.c["composite_ci"]["conclusion"] = "failure"
        self.assert_block("LATEST_COMPOSITE_CI_NOT_GREEN")

    def test_release_spoof_claim_fails(self):
        self.b["owner_accepted"] = True
        self.assert_block("PREMATURE_RC_OR_OWNER_ACCEPTANCE_CLAIM")

    def test_missing_art_runtime_source_report_does_not_make_product_go(self):
        self.c["runtime_activation"]["production_runtime"] = "NOT_VERIFIED_FAIL_CLOSED"
        self.c["runtime_activation"]["eight_domain_production_impact"] = []
        verdict = self.decision()
        self.assertEqual(verdict["status"], "SOURCE_READY_PRODUCTION_NOT_VERIFIED")
        self.assertTrue(all(not d["product_go"] for d in verdict["domain_stage"].values()))

    def test_false_claim_of_studio_execution_fails_closed_to_static_status(self):
        self.c["runtime_activation"]["studio_runtime"] = "SUCCESS"
        verdict = self.decision()
        self.assertEqual(verdict["studio_1p15ai"], "NOT_TESTED")
        self.assertEqual(verdict["android_15min"], "NOT_TESTED")
        self.assertFalse(verdict["owner_accepted"])

    def test_unrecognized_runtime_string_is_blocker(self):
        self.c["runtime_activation"]["production_runtime"] = "GREEN"
        self.assert_block("UNRECOGNIZED_PRODUCTION_RUNTIME_VERDICT")

    def test_missing_safely_reviewed_original_ownership_blocks(self):
        self.a["status"] = "SOURCE_NO_GO"
        self.assert_block("SOURCE_LINEAGE_NOT_GREEN")


if __name__ == "__main__":
    unittest.main()
