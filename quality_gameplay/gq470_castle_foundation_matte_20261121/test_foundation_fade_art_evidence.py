"""Source-only test for explicitly unmeasured 150..190-stud fade and dual-route budget."""
import unittest
from emit_art_report import LOD_TRIAL_DISTANCES, planned_fade_alpha, foundation_lod_evidence


class FoundationFadeEvidenceTests(unittest.TestCase):
    def test_camera_distance_expected_envelope_not_actual_camera_proof(self):
        self.assertEqual(LOD_TRIAL_DISTANCES, [130, 150, 160, 175, 189, 195])
        self.assertEqual([planned_fade_alpha(d) for d in LOD_TRIAL_DISTANCES],
                         [0.0, 0.0, 0.25, 0.625, 0.975, None])

    def test_all_device_human_evidence_remains_empty(self):
        e = foundation_lod_evidence()
        self.assertEqual(e["gate"], "ART_NO_GO_NOT_TESTED")
        self.assertFalse(e["approve_dual_adoption_without_mobile_runtime_evidence"])
        self.assertFalse(e["studio_2client_verified"])
        self.assertEqual(len(e["same_camera_distance_trials"]), 6)
        self.assertTrue(all(x["status"] == "NOT_TESTED" and
                            x["actual_studio_capture"] is None and
                            x["actual_device_fps"] is None and
                            x["actual_rendered_visibility"] is None
                            for x in e["same_camera_distance_trials"]))
        self.assertTrue(all(v == "NOT_TESTED" for v in e["streaming_cases"].values()))

    def test_dual_optional_max_part_risk_not_accepted(self):
        b = foundation_lod_evidence()["source_budget_parts"]
        self.assertEqual(b["foundation_982_touch"] + b["approach_988_touch"],
                         b["both_optional_touch"])
        self.assertEqual(b["foundation_982_pc"] + b["approach_988_pc"],
                         b["both_optional_pc"])
        self.assertEqual(b["both_optional_touch"], 32)
        self.assertEqual(b["both_optional_pc"], 48)


if __name__ == "__main__":
    unittest.main()
