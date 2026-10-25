"""P3 read-only scheduling: no forged JSON should ever dispatch a worker."""
import copy
import json
from pathlib import Path
import unittest

from studio_autopilot.scheduler import UnsafePlan, propose

ROOT = Path(__file__).resolve().parents[1]
TOY = json.loads((ROOT / "studio_autopilot/projects/toy_wars.json").read_text(encoding="utf-8"))
DEMO = json.loads((ROOT / "studio_autopilot/projects/skyline_parkour_template.json").read_text(encoding="utf-8"))
MAIN = "a" * 40


def second_game():
    obj = copy.deepcopy(TOY)
    obj["game_id"] = "parkour-live-example"
    obj["title"] = "Parkour example with independent repository"
    obj["repository"] = "example/parkour-live"
    obj["coordination_ref"] = "parkour-coordinator"
    obj["roles"] = {"author": "a"*32, "reviewer": "b"*32, "meta": "c"*32}
    obj["quality"] = {k: "NOT_RUN" for k in obj["quality"]}
    return obj


def snapshot(project, **updates):
    d = {"repository": project["repository"], "main_sha": MAIN, "qa_sha": MAIN,
         "qa": "PASS", "lease_epoch": 17, "holder": None, "open_prs": 0,
         "last_served_cycle": 3, "live_read_claim": True}
    d.update(updates)
    return d


def signal(game, trigger="scheduled", key="one"):
    return {"game_id": game["game_id"], "trigger": trigger, "occurrence_key": key}


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.one, self.two = TOY, second_game()
        self.projects = [self.one, self.two, DEMO]
        self.snapshots = {
            self.one["game_id"]: snapshot(self.one, last_served_cycle=4),
            self.two["game_id"]: snapshot(self.two, last_served_cycle=2),
        }
        self.events = [signal(self.one), signal(self.two)]

    def execute(self, **kw):
        kwargs = {"cycle": 10, "max_slots": 1, "occupied_slots": 0}
        kwargs.update(kw)
        return propose(self.projects, self.snapshots, self.events, **kwargs)

    def test_fairness_older_eligible_game_selected(self):
        result = self.execute()
        selected = [x for x in result["candidates"] if x["selected"]]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["game_id"], self.two["game_id"])
        self.assertFalse(result["execution"]["dispatch_allowed"])

    def test_two_slots_two_games(self):
        result = self.execute(max_slots=2)
        self.assertEqual(sum(x["selected"] for x in result["candidates"]), 2)

    def test_manual_go_and_scheduled_are_coalesced(self):
        self.events.append(signal(self.one, "manual_go", "manual"))
        self.events.append(signal(self.one, "manual_go", "manual"))
        result = self.execute()
        toy = next(x for x in result["candidates"] if x["game_id"] == self.one["game_id"])
        self.assertEqual(toy["trigger"], "manual_go")
        self.assertEqual(toy["coalesced"], ["manual_go", "scheduled"])
        self.assertEqual(len(result["candidates"]), 2)

    def test_coalesced_idempotency_ignores_trigger_duplicates(self):
        one = self.execute()
        self.events.extend([signal(self.one,"manual_go","manual"),signal(self.one,"manual_go","manual")])
        two = self.execute()
        def key(result):
            return next(x["idempotency_key"] for x in result["candidates"]
                        if x["game_id"] == self.one["game_id"])
        self.assertEqual(key(one),key(two))

    def test_changed_epoch_main_or_cycle_changes_key(self):
        base = self.execute()
        game = self.one["game_id"]
        def key(r):
            return next(x["idempotency_key"] for x in r["candidates"] if x["game_id"] == game)
        old = key(base)
        self.snapshots[game]["lease_epoch"] += 1
        self.assertNotEqual(key(self.execute()), old)
        self.snapshots[game]["lease_epoch"] -= 1
        self.snapshots[game]["main_sha"] = "b"*40
        self.assertNotEqual(key(self.execute()), old)
        self.snapshots[game]["main_sha"] = MAIN
        self.assertNotEqual(key(self.execute(cycle=11)), old)

    def test_held_lock_blocks_only_its_game(self):
        self.snapshots[self.two["game_id"]]["holder"] = "REVIEWER"
        out = self.execute()
        self.assertEqual([x["game_id"] for x in out["candidates"] if x["selected"]],
                         [self.one["game_id"]])
        self.assertEqual(out["candidates"][-1]["issues"], ["JOIN_EXISTING_LEASE"])

    def test_mismatched_main_qa_blocks(self):
        self.snapshots[self.two["game_id"]]["qa_sha"] = "b"*40
        self.assertIn("WAIT_CURRENT_MAIN_QA",self.execute()["candidates"][-1]["issues"])

    def test_main_qa_failure_blocks_regardless_of_good_claim(self):
        self.snapshots[self.two["game_id"]]["qa"] = "FAIL"
        self.assertIn("REPAIR_MAIN_FIRST",self.execute()["candidates"][-1]["issues"])

    def test_future_last_served_cycle_rejected(self):
        self.snapshots[self.two["game_id"]]["last_served_cycle"] = 11
        with self.assertRaisesRegex(UnsafePlan, "future"):
            self.execute(cycle=10)
        self.snapshots[self.two["game_id"]]["last_served_cycle"] = 10
        self.assertIsInstance(self.execute(cycle=10), dict)

    def test_main_pending_blocks(self):
        self.snapshots[self.two["game_id"]]["qa"] = "PENDING"
        self.assertIn("WAIT_MAIN_QA",self.execute()["candidates"][-1]["issues"])

    def test_pr_limit_blocks_new_work(self):
        self.snapshots[self.two["game_id"]]["open_prs"] = self.two["safety"]["max_open_prs"]
        self.assertIn("WAIT_PR_CAPACITY",self.execute()["candidates"][-1]["issues"])

    def test_fake_source_claim_is_only_diagnostic(self):
        result=self.execute()
        self.assertTrue(any(x["selected"] for x in result["candidates"]))
        self.assertTrue(all(not x["dispatch_allowed"] and not x["merge_allowed"] and
                            not x["publish_allowed"] and not x["external_spend_allowed"]
                            for x in result["candidates"]))

    def test_missing_evidence_claim_blocks_proposal(self):
        self.snapshots[self.two["game_id"]]["live_read_claim"] = False
        self.assertIn("VERIFY_LIVE_GITHUB_EVIDENCE",self.execute()["candidates"][-1]["issues"])

    def test_unbound_template_signal_is_rejected(self):
        self.events.append(signal(DEMO))
        with self.assertRaises(UnsafePlan):self.execute()

    def test_same_repository_different_project_rejected(self):
        self.two["repository"]=self.one["repository"]
        with self.assertRaises(UnsafePlan):self.execute()

    def test_duplicate_roles_across_games_rejected(self):
        self.two["roles"]["author"]=self.one["roles"]["author"]
        with self.assertRaises(UnsafePlan):self.execute()

    def test_duplicate_coordination_refs_rejected(self):
        self.two["coordination_ref"]=self.one["coordination_ref"]
        with self.assertRaises(UnsafePlan):self.execute()

    def test_wrong_snapshot_repo_rejected(self):
        self.snapshots[self.two["game_id"]]["repository"]="attacker/repository"
        with self.assertRaises(UnsafePlan):self.execute()

    def test_forged_extra_snapshot_rejected(self):
        self.snapshots["foreign"]=snapshot(self.one)
        with self.assertRaises(UnsafePlan):self.execute()

    def test_malformed_boolean_int_rejected(self):
        for field in ("lease_epoch","open_prs","last_served_cycle"):
            old=self.snapshots[self.one["game_id"]][field]
            self.snapshots[self.one["game_id"]][field]=True
            with self.subTest(field=field),self.assertRaises(UnsafePlan):self.execute()
            self.snapshots[self.one["game_id"]][field]=old

    def test_invalid_capacity_rejected(self):
        for capacity in (0, 11, True):
            with self.subTest(capacity=capacity),self.assertRaises(UnsafePlan):
                self.execute(max_slots=capacity)

    def test_occupied_slots_consumed_first(self):
        result=self.execute(occupied_slots=1,max_slots=1)
        self.assertFalse(any(c["selected"] for c in result["candidates"]))

    def test_scheduled_and_manual_does_not_create_two_lanes(self):
        self.events=[signal(self.one,"manual_go","m1"),signal(self.one,"scheduled","s1")]
        result=self.execute()
        self.assertEqual(len(result["candidates"]),1)
        self.assertEqual(result["candidates"][0]["trigger"],"manual_go")

    def test_invalid_signals_rejected(self):
        self.events.append({"game_id":self.one["game_id"],"trigger":"unknown","occurrence_key":"x"})
        with self.assertRaises(UnsafePlan):self.execute()


if __name__ == "__main__":
    unittest.main()
