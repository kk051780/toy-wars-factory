"""Executable negative/positive cases for the non-authorizing stacked PR planner."""
import copy
import unittest

from tools.system_stacked_pr_dependency import evaluate


R = "kk051780/toy-wars-factory"
M = "a" * 40
A = "b" * 40
B = "c" * 40
C = "d" * 40
STALE = "e" * 40
TIME = "2026-10-31T08:55:00Z"


def entry(n, head, head_sha, base="main", base_sha=M):
    return {"number": n, "state": "open", "draft": True,
            "head_repo": R, "head_ref": head, "head_sha": head_sha,
            "base_repo": R, "base_ref": base, "base_sha": base_sha}


def sample():
    return {"repository": R, "default_branch": "main", "default_head": M,
            "observed_at": TIME, "pulls": [
                entry(150, "controller/a14-windows", C, "controller/studio", B),
                entry(147, "controller/artifact", A),
                entry(149, "controller/studio", B, "controller/artifact", A),
                entry(168, "controller/collision", STALE),
            ]}


class StackedPRDependencyTests(unittest.TestCase):
    def test_topological_order_is_parent_first_for_unsorted_input(self):
        out = evaluate(sample())
        self.assertEqual(out["status"], "ADVISORY_READY")
        self.assertEqual(out["dependency_order"], [147, 149, 150, 168])
        self.assertEqual(out["main_review_candidates"], [147, 168])
        self.assertEqual([i["depth"] for i in out["items"]], [0, 1, 2, 0])
        self.assertEqual([i["status"] for i in out["items"]],
                         ["MAIN_BASE_REVIEW_ONLY", "WAIT_OPEN_PARENT",
                          "WAIT_OPEN_PARENT", "MAIN_BASE_REVIEW_ONLY"])

    def test_never_grants_approval_or_write_rights(self):
        out = evaluate(sample())
        for flag in ("provider_verified", "may_write", "may_merge", "may_rebase",
                     "may_mark_ready", "may_skip_independent_review"):
            self.assertIs(out[flag], False)
        self.assertTrue(all(x["requires_independent_review"] for x in out["items"]))

    def test_same_snapshot_has_no_mutation(self):
        s = sample()
        before = copy.deepcopy(s)
        self.assertEqual(evaluate(s), evaluate(s))
        self.assertEqual(s, before)

    def test_stale_default_branch_not_review_candidate(self):
        s = sample()
        s["pulls"][-1]["base_sha"] = STALE
        out = evaluate(s)
        self.assertEqual(out["main_review_candidates"], [147])
        self.assertEqual(out["items"][-1]["status"], "WAIT_STALE_DEFAULT_BASE")

    def test_child_parent_sha_drift_waits(self):
        s = sample()
        s["pulls"][2]["base_sha"] = STALE
        out = evaluate(s)
        self.assertEqual(out["items"][1]["status"], "WAIT_PARENT_HEAD_MISMATCH")
        self.assertEqual(out["items"][2]["status"], "WAIT_ANCESTOR_UNRESOLVED")

    def test_unknown_nondefault_base_waits(self):
        s = sample()
        s["pulls"][2]["base_ref"] = "controller/closed-unknown"
        out = evaluate(s)
        self.assertEqual(out["items"][1]["status"], "WAIT_UNTRACKED_BASE")
        self.assertIsNone(out["items"][1]["depth"])
        self.assertEqual(out["items"][2]["status"], "WAIT_ANCESTOR_UNRESOLVED")

    def test_direct_child_of_stale_root_waits(self):
        s = sample()
        s["pulls"][1]["base_sha"] = STALE
        out = evaluate(s)
        self.assertEqual(out["items"][0]["status"], "WAIT_STALE_DEFAULT_BASE")
        self.assertEqual(out["items"][1]["status"], "WAIT_ANCESTOR_UNRESOLVED")

    def test_branch_cycle_cannot_be_treated_as_merge_order(self):
        s = sample()
        s["pulls"][1]["base_ref"] = "controller/studio"
        s["pulls"][1]["base_sha"] = B
        out = evaluate(s)
        self.assertEqual(out["status"], "WAIT_METADATA")
        self.assertIn("cycle", out["reason"])
        self.assertFalse(out["may_merge"])

    def test_single_root(self):
        s = sample()
        s["pulls"] = [entry(3, "feature/test", A)]
        self.assertEqual(evaluate(s)["main_review_candidates"], [3])

    def test_empty_open_snapshot_is_not_provider_proof(self):
        s = sample()
        s["pulls"] = []
        out = evaluate(s)
        self.assertEqual(out["status"], "EMPTY_INVENTORY")
        self.assertFalse(out["provider_verified"])
        self.assertEqual(out["total_open_prs"], 0)

    def test_independent_siblings_and_nested_branches(self):
        s = sample()
        s["pulls"].append(entry(160, "controller/p3", STALE, "controller/artifact", A))
        out = evaluate(s)
        self.assertEqual(out["total_open_prs"], 5)
        i = next(x for x in out["items"] if x["number"] == 160)
        self.assertEqual((i["depth"], i["depends_on_pr"]), (1, 147))

    def test_draft_flag_does_not_change_advice(self):
        s = sample()
        s["pulls"][1]["draft"] = False
        out = evaluate(s)
        self.assertEqual(out["main_review_candidates"], [147, 168])
        self.assertFalse(out["items"][0]["draft"])
        self.assertFalse(out["may_merge"])

    def test_large_valid_chain(self):
        s = sample()
        s["pulls"] = [entry(1, "feature/chain1", A)]
        for n in range(2, 81):
            prev = s["pulls"][-1]
            s["pulls"].append(entry(n, f"feature/chain{n}", B,
                                    prev["head_ref"], prev["head_sha"]))
        out = evaluate(s)
        self.assertEqual(out["total_open_prs"], 80)
        self.assertEqual(out["dependency_order"], list(range(1, 81)))
        self.assertEqual(out["items"][-1]["depth"], 79)
        self.assertEqual(out["main_review_candidates"], [1])

    def test_malformed_snapshots_fail_closed(self):
        edits = [
            lambda s: s.update(repository="not-a-repo"),
            lambda s: s.update(default_branch="refs/heads/main"),
            lambda s: s.update(default_head="badsha"),
            lambda s: s.update(observed_at="2026-10-31T08:55:00"),
            lambda s: s.update(observed_at="not-a-date"),
            lambda s: s.update(pulls=None),
            lambda s: s.update(pulls="not a list"),
            lambda s: s.update(extra="untrusted field"),
            lambda s: s["pulls"].append(copy.deepcopy(s["pulls"][0])),
            lambda s: s["pulls"][0].update(number=True),
            lambda s: s["pulls"][0].update(number=0),
            lambda s: s["pulls"][0].update(state="closed"),
            lambda s: s["pulls"][0].update(draft="true"),
            lambda s: s["pulls"][0].update(head_repo="foreign/repo"),
            lambda s: s["pulls"][0].update(base_repo="foreign/repo"),
            lambda s: s["pulls"][0].update(head_ref="main"),
            lambda s: s["pulls"][0].update(base_ref="controller/a14-windows"),
            lambda s: s["pulls"][0].update(base_ref="../private"),
            lambda s: s["pulls"][0].update(head_ref="feature//double"),
            lambda s: s["pulls"][0].update(head_ref="feature/../escape"),
            lambda s: s["pulls"][0].update(head_sha="invalid"),
            lambda s: s["pulls"][0].update(base_sha=42),
            lambda s: s["pulls"][0].update(extra="field"),
            lambda s: s["pulls"][0].update(head_ref="controller/artifact"),
            lambda s: s.update(pulls=[entry(1, f"feature/p{i}", A)
                                      for i in range(301)]),
        ]
        for i, edit in enumerate(edits):
            with self.subTest(case=i):
                s = sample()
                edit(s)
                result = evaluate(s)
                self.assertEqual(result["status"], "WAIT_METADATA")
                self.assertFalse(result["may_merge"])


if __name__ == "__main__":
    unittest.main()
