"""Native offline regression for the immutable Core36 source-input lock."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_core36_forwardlock as gate


class Core36ForwardLockTests(unittest.TestCase):
    def setUp(self):
        self.changed = set(gate.ORIGINAL_ADOPTION)
        self.observed = dict(gate.INPUT_BLOBS)

    def test_original_adoption_green(self):
        self.assertEqual(gate.verify_changed_paths(self.changed, self.observed)["locked_source_inputs"], 4)

    def test_unrelated_next_rc_feature_keeps_core36_rebuildable(self):
        changed = self.changed | {"rc_fastlane/FEATURE_CATALOG.json", "docs/new-receipt.md"}
        result = gate.verify_changed_paths(changed, self.observed)
        self.assertEqual(result["noninput_paths_since_adoption"], 2)

    def test_manifest_mutation_is_red(self):
        modified = dict(self.observed)
        modified["rc_fastlane/EGGRUMBLE_V3_CORE36.json"] = "0" * 40
        with self.assertRaisesRegex(gate.SourceLockViolation, "RED_CORE36_REAL_INPUT_DRIFT"):
            gate.verify_changed_paths(self.changed, modified)

    def test_active_profile_mutation_is_red(self):
        modified = dict(self.observed)
        modified["rc_fastlane/ACTIVE.json"] = "0" * 40
        with self.assertRaises(gate.SourceLockViolation):
            gate.verify_changed_paths(self.changed, modified)

    def test_lss_gameplay_source_mutation_is_red_even_if_diff_has_unrelated_paths(self):
        modified = dict(self.observed)
        key = next(p for p in modified if "LandSeaSkyTraversal" in p)
        modified[key] = "a" * 40
        with self.assertRaisesRegex(gate.SourceLockViolation, "RED_CORE36_REAL_INPUT_DRIFT"):
            gate.verify_changed_paths(self.changed | {"docs/change.md"}, modified)

    def test_rehydration_behavior_change_is_red(self):
        modified = dict(self.observed)
        key = next(p for p in modified if "rehydrate_real31.py" in p)
        del modified[key]
        with self.assertRaisesRegex(gate.SourceLockViolation, "RED_CORE36_REAL_INPUT_DRIFT"):
            gate.verify_changed_paths(self.changed, modified)

    def test_missing_adoption_provenance_is_red(self):
        with self.assertRaisesRegex(gate.SourceLockViolation, "RED_ADOPTION_PROVENANCE_MISSING"):
            gate.verify_changed_paths(self.changed - {"rc_fastlane/ACTIVE.json"}, self.observed)

    def test_invalid_compare_status_is_red(self):
        with self.assertRaisesRegex(gate.SourceLockViolation, "RED_CORE36_BASE_ANCESTRY"):
            gate.verify_compare_response({"status": "diverged", "files": []})

    def test_compare_missing_files_is_red(self):
        with self.assertRaisesRegex(gate.SourceLockViolation, "RED_CORE36_COMPARE_FILES_MISSING"):
            gate.verify_compare_response({"status": "ahead"})

    def test_actual_compare_with_untouched_pinned_inputs_green(self):
        response = {"status": "ahead", "files": [{"filename": p} for p in self.changed]}
        with patch.object(gate, "hash_checked_out_inputs", return_value=self.observed):
            result = gate.verify_compare_response(response)
        self.assertEqual(result["original_adoption_paths"], 3)

    def test_mutant_old_exact_change_set_rejects_valid_future(self):
        future_changed = self.changed | {"docs/legitimate-rc-receipt.md"}
        self.assertNotEqual(future_changed, gate.ORIGINAL_ADOPTION)
        self.assertEqual(gate.verify_changed_paths(future_changed, self.observed)["noninput_paths_since_adoption"], 1)


if __name__ == "__main__":
    unittest.main()
