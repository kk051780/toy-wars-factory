"""Adversarial P3 bridge tests. Fixtures never attest actual GitHub reads."""
import copy
import json
from pathlib import Path
import unittest

from tools.system_multigame_bridge import (
    BridgeRejected, snapshots_from_reports, plan_advisory)

ROOT = Path(__file__).resolve().parents[1]
ONE = ROOT / "studio_autopilot" / "projects" / "toy_wars.json"


class MultiGameBridgeTests(unittest.TestCase):
    def setUp(self):
        self.a = json.loads(ONE.read_text(encoding="utf-8"))
        self.b = copy.deepcopy(self.a)
        self.b.update(game_id="other-playtest", repository="example/other-playtest",
                      coordination_ref="other-playtest-lease")
        self.b["roles"] = {"author": "a" * 32, "reviewer": "b" * 32, "meta": "c" * 32}
        self.games = [self.a, self.b]
        self.reports = {
            self.a["game_id"]: self.report(self.a, "1"),
            self.b["game_id"]: self.report(self.b, "2")}

    @staticmethod
    def report(game, suffix):
        deny = {"dispatch_allowed": False, "merge_allowed": False,
                "publish_allowed": False, "external_spend_allowed": False}
        role_runs = {role: {"task_id": game["roles"][role],
                            "last_run": {"id": f"{suffix * 8}-1234-4123-8123-{dict(author='a', reviewer='b', meta='c')[role] * 12}"}}
                     for role in ("author", "reviewer", "meta")}
        return {
            "verification": "NOT_VERIFIED", "authority": deny,
            "transport": {"verification": "NOT_VERIFIED", "mode": "READ_ONLY_INPUT_ADAPTER",
                          "repository": game["repository"], "roles_bound_to_pinned_blobs": True,
                          "closed": False, "calls": 12, "trace": [{"method": "GET"}],
                          "authority": deny},
            "observation": {"verification": "NOT_VERIFIED", "mode": "ADVISORY_ONLY",
                            "game_id": game["game_id"], "repository": game["repository"],
                            "main_sha": suffix * 40,
                            "coordinator": {"ref_sha": suffix * 40, "blob_sha": suffix * 40,
                                            "epoch": 45, "holder": None},
                            "services": role_runs, "get_trace": [{"method": "GET"}],
                            "peek_trace": [{"method": "PEEK"}], "authority": deny}}

    def test_distinct_projects_stay_isolated_and_have_no_authority(self):
        result = snapshots_from_reports(self.games, self.reports)
        self.assertEqual(set(result["snapshots"]), {g["game_id"] for g in self.games})
        for g in self.games:
            row = result["snapshots"][g["game_id"]]
            self.assertEqual(row["repository"], g["repository"])
            self.assertEqual(row["qa"], "PENDING")
            self.assertNotEqual(row["main_sha"], row["qa_sha"])
            self.assertFalse(row["live_read_claim"])
            self.assertEqual(row["open_prs"], g["safety"]["max_open_prs"])
            self.assertEqual(row["holder"], "UNVERIFIED_LEASE_STATE")
            self.assertFalse(result["receipts"][g["game_id"]]["origin_attested"])

    def test_fair_priority_remains_advisory_only(self):
        events = [{"game_id": g["game_id"], "trigger": "scheduled",
                   "occurrence_key": "once"} for g in self.games]
        result = plan_advisory(self.games, self.reports, events, cycle=5, max_slots=2)
        ordered = result["plan"]["candidates"]
        self.assertEqual(len(ordered), 2)
        self.assertEqual([r["game_id"] for r in ordered], sorted(g["game_id"] for g in self.games))
        for candidate in ordered:
            self.assertFalse(candidate["selected"])
            self.assertFalse(candidate["dispatch_allowed"])
            self.assertIn("VERIFY_LIVE_GITHUB_EVIDENCE", candidate["issues"])
            self.assertIn("WAIT_MAIN_QA", candidate["issues"])
        self.assertFalse(result["authority"]["dispatch_allowed"])

    def test_cross_game_replay_is_rejected(self):
        self.reports[self.b["game_id"]] = copy.deepcopy(self.reports[self.a["game_id"]])
        with self.assertRaisesRegex(BridgeRejected, "FOREIGN_OR_UNBOUND_REPORT"):
            snapshots_from_reports(self.games, self.reports)

    def test_duplicate_service_run_across_games_rejected(self):
        self.reports[self.b["game_id"]]["observation"]["services"]["meta"]["last_run"]["id"] = (
            self.reports[self.a["game_id"]]["observation"]["services"]["meta"]["last_run"]["id"])
        with self.assertRaisesRegex(BridgeRejected, "REPLAYED_OR_CROSS_PROJECT_RUN"):
            snapshots_from_reports(self.games, self.reports)

    def test_unverified_cannot_claim_live(self):
        self.reports[self.a["game_id"]]["verification"] = "LIVE_VERIFIED"
        with self.assertRaisesRegex(BridgeRejected, "FOREIGN_OR_UNBOUND_REPORT"):
            snapshots_from_reports(self.games, self.reports)

    def test_spoofed_dispatch_permission_rejected(self):
        self.reports[self.a["game_id"]]["authority"]["dispatch_allowed"] = True
        with self.assertRaisesRegex(BridgeRejected, "AUTHORITY_CLAIMED"):
            snapshots_from_reports(self.games, self.reports)

    def test_no_historical_lease_expiry_can_grant_availability(self):
        self.reports[self.a["game_id"]]["observation"]["coordinator"]["holder"] = {
            "kind": "WORKER", "epoch": 45, "expires_at": "2000-01-01T00:00:00Z"}
        row = snapshots_from_reports(self.games, self.reports)["snapshots"][self.a["game_id"]]
        self.assertEqual(row["holder"], "UNVERIFIED_LEASE_STATE")

    def test_missing_report_and_role_rejected(self):
        self.reports.pop(self.b["game_id"])
        with self.assertRaisesRegex(BridgeRejected, "EXACT_ONE_REPORT"):
            snapshots_from_reports(self.games, self.reports)
        self.reports[self.b["game_id"]] = self.report(self.b, "2")
        self.reports[self.b["game_id"]]["observation"]["services"].pop("meta")
        with self.assertRaisesRegex(BridgeRejected, "MISSING_BOUND_STATE"):
            snapshots_from_reports(self.games, self.reports)

    def test_wrong_ci_or_missing_trace_is_never_silently_promoted(self):
        self.reports[self.a["game_id"]]["transport"]["trace"] = []
        with self.assertRaisesRegex(BridgeRejected, "MISSING_OBSERVATION_TRACE"):
            snapshots_from_reports(self.games, self.reports)
        self.reports[self.a["game_id"]] = self.report(self.a, "1")
        self.reports[self.a["game_id"]]["observation"]["main_qa"] = "PASS"
        row = snapshots_from_reports(self.games, self.reports)["snapshots"][self.a["game_id"]]
        self.assertEqual(row["qa"], "PENDING")


if __name__ == "__main__":
    unittest.main()
