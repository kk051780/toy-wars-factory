"""Fail-closed #420 ART gate: 32 actual screenshots required; placeholders never PASS."""
import itertools
import json
from pathlib import Path
import unittest

FILE = Path(__file__).with_name("ART_32_IMAGE_RETEST_MATRIX.json")


def validate(m):
    if m.get("expected_comparison_images") != 32:
        raise ValueError("expected_32")
    if len(m.get("scenes", [])) != 16 or len(m.get("frames", [])) != 32:
        raise ValueError("missing_frames_or_scenes")
    expected = set()
    for scene in m["scenes"]:
        for p in ["OFF69_BASELINE", "ON70_CANDIDATE"]:
            expected.add((scene["id"], p))
    actual = {(x["scene_id"], x["profile"]) for x in m["frames"]}
    if actual != expected or len(actual) != 32:
        raise ValueError("duplicate_or_wrong_scene")
    for scene in m["scenes"]:
        if (scene["device"] not in ("PC", "ANDROID") or
                scene["rig"] not in ("R6", "R15") or
                scene["remote_player_team"] not in ("RED", "BLUE") or
                scene["distance_studs"] not in (20, 75) or
                scene["expected_candidate_crest_visible"] != (scene["distance_studs"] <= 66)):
            raise ValueError("scene_geometry_wrong")
    for frame in m["frames"]:
        if (frame["screenshot_present"] is not False or
                frame["human_art_score"] is not None or
                frame["observed_avatar_visible"] is not None or
                frame["observed_crest_visible"] is not None):
            # This gate is a source-only template, never an actual screenshot collector.
            raise ValueError("fabricated_art_evidence")
    if (m["evidence_count_received"] != 0 or m["art_gate"] != "ART_NO_GO" or
            m["product_gate"] != "PRODUCT_NO_GO" or
            m["requirements"]["pc_solo_and_studio_two_client"] != "NOT_TESTED" or
            m["requirements"]["android15_min_fps_heat"] != "NOT_TESTED" or
            "P0_PLAYER_ABSENT_ROOT_CAUSE_UNCONFIRMED" not in m["blockers"]):
        raise ValueError("false_pass_or_p0_waiver")

class MatchedScreenshotMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(FILE.read_text())

    def test_complete_32_frame_cartesian_pairing(self):
        validate(self.matrix)
        self.assertEqual(len(self.matrix["frames"]), 32)
        self.assertEqual(len(set(x["scene_id"] for x in self.matrix["frames"])), 16)

    def test_all_scenarios_unique_and_expected(self):
        expected=set(itertools.product(("PC","ANDROID"),("R6","R15"),("RED","BLUE"),(20,75)))
        found={(s["device"],s["rig"],s["remote_player_team"],s["distance_studs"]) for s in self.matrix["scenes"]}
        self.assertEqual(found,expected)

    def test_5_evidence_tamper_failures(self):
        for mutation in [
            lambda x: x.update(art_gate="ART_GO"),
            lambda x: x["frames"][0].update(screenshot_present=True),
            lambda x: x["frames"][1].update(human_art_score=5),
            lambda x: x.update(evidence_count_received=32),
            lambda x: x["frames"].pop(),
        ]:
            altered=json.loads(json.dumps(self.matrix))
            mutation(altered)
            with self.assertRaises(ValueError):
                validate(altered)

if __name__ == "__main__":
    unittest.main()
