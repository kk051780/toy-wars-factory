import hashlib
import tempfile
import unittest
from pathlib import Path
from admission_gate import evaluate

SHA = "a" * 40
RECEIPT = {
    "adoption_id": "P0D-LOBBY-TRAINING-001", "official_rc_sha": SHA,
    "candidate_source_sha": SHA, "rollback_sha": SHA,
    "feature_source_qa": "PASS", "product_official_rc_selected": True,
    "independent_rc_qa": True, "studio_2client": True,
    "android": True, "owner_fun": True,
    "source_lock_verified": True, "single_authority_review": True,
    "expected_script_counts": {"Script": 1, "LocalScript": 0, "ModuleScript": 0},
}
XML = b'<roblox><Item class="Script"><Properties><string name="Name">Game</string></Properties></Item></roblox>'

class AdmissionTests(unittest.TestCase):
    def test_draft_current_h1_must_fail(self):
        draft = dict(RECEIPT, product_official_rc_selected=False, studio_2client=False,
                     android=False, owner_fun=False, independent_rc_qa=False)
        result = evaluate(draft)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("PRODUCT_NOT_OFFICIALLY_SELECTED", result["blockers"])
        self.assertIn("STUDIO_2CLIENT_NOT_VERIFIED", result["blockers"])
    def test_unscanned_place_blocks_even_when_everything_else_true(self):
        self.assertIn("PLACE_NOT_INDEPENDENTLY_SCANNED", evaluate(RECEIPT)["blockers"])
    def test_real_xml_static_gate(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/"dummy.rbxlx"; p.write_bytes(XML)
            r = dict(RECEIPT, expected_place_sha256=hashlib.sha256(XML).hexdigest())
            self.assertEqual(evaluate(r, p)["decision"], "ELIGIBLE_FOR_SOLE_INTEGRATOR_REVIEW")
    def test_wrong_place_sha_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/"dummy.rbxlx"; p.write_bytes(XML)
            r = dict(RECEIPT, expected_place_sha256="0" * 64)
            self.assertIn("PLACE_SHA256_MISMATCH", evaluate(r, p)["blockers"])
    def test_duplicate_game_blocks(self):
        dup = XML.replace(b'</roblox>', b'<Item class="Script"><Properties><string name="Name">Game</string></Properties></Item></roblox>')
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/"dummy.rbxlx"; p.write_bytes(dup)
            r = dict(RECEIPT, expected_place_sha256=hashlib.sha256(dup).hexdigest(),
                     expected_script_counts={"Script": 2, "LocalScript": 0, "ModuleScript": 0})
            self.assertIn("SINGLE_GAME_SCRIPT_NOT_VERIFIED", evaluate(r, p)["blockers"])
    def test_malformed_or_entity_xml_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/"dummy.rbxlx"; p.write_bytes(b'<!DOCTYPE foo><roblox/>')
            self.assertTrue(any(x.startswith("INVALID_PLACE") for x in evaluate(RECEIPT, p)["blockers"]))
    def test_missing_required_data_fails_closed(self):
        self.assertIn("MISSING_FIELD:owner_fun", evaluate({"adoption_id":"x"})["blockers"])
    def test_bad_sha_fails_closed(self):
        r = dict(RECEIPT, official_rc_sha="not40", candidate_source_sha="short")
        self.assertIn("INVALID_OFFICIAL_SHA", evaluate(r)["blockers"])
        self.assertIn("INVALID_CANDIDATE_SHA", evaluate(r)["blockers"])

if __name__ == "__main__":
    unittest.main()
