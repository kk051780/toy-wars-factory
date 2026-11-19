import copy
import importlib.util
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("pq470_obs", ROOT/"validate_observations.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.template=json.loads((ROOT/"OBSERVATION_TEMPLATE.json").read_text(encoding="utf-8"))
    def test_missing_observations_do_not_pass(self):
        r=mod.check(self.template)
        self.assertEqual(r["decision"],"NOT_MEASURED")
        self.assertEqual(r["valid_observations"],0)
    def test_no_fake_p0d_sha(self):
        o=copy.deepcopy(self.template)
        o["observations"]=[{"game_id":"p0d_official_rc","scenario_id":"FIELD_ROUTE","trial":1,"source_url":"https://example.org/recording","video_timecode":"00:05","device":"Android","capture_date":"2026-11-15","observer":"QA","game_version_or_sha":"unknown","metrics":{"base_to_base_seconds":75,"usable_distinct_routes":3,"traversal_blockers":0,"egg_escape_branches":2}}]
        self.assertIn("0:UNPINNED_OFFICIAL_RC",mod.check(o)["problems"])
    def test_complete_observation_must_be_repeatable(self):
        o=copy.deepcopy(self.template)
        a={"game_id":"bedwars","scenario_id":"FIELD_ROUTE","trial":1,"source_url":"https://example.org/video","video_timecode":"01:02","device":"Android","capture_date":"2026-11-15","observer":"QA","game_version_or_sha":"test","metrics":{"base_to_base_seconds":65,"usable_distinct_routes":3,"traversal_blockers":0,"egg_escape_branches":1}}
        o["observations"]=[a,copy.deepcopy(a)]
        self.assertIn("1:DUPLICATE_TRIAL",mod.check(o)["problems"])
    def test_negative_counts_rejected(self):
        o=copy.deepcopy(self.template)
        a={"game_id":"bedwars","scenario_id":"MOB_CLEAR_30S","trial":1,"source_url":"https://example.org/video","video_timecode":"01:02","device":"Android","capture_date":"2026-11-15","observer":"QA","game_version_or_sha":"test","metrics":{"kills_30s":-1,"max_valid_targets_one_attack":3,"input_to_first_hit_ms":60}}
        o["observations"]=[a]
        self.assertIn("0:INVALID_METRIC:kills_30s",mod.check(o)["problems"])

if __name__=="__main__":
    unittest.main()
