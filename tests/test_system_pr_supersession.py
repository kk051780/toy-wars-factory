"""Fail-closed tests for the distinct read-only stale-source PR advisory."""
import copy
import unittest

from tools.system_pr_supersession import evaluate


H = "a" * 40
M = "b" * 40
MERGE = "c" * 40
ALT = "d" * 40
REPO = "kk051780/toy-wars-factory"
STAMP = "2026-10-31T07:30:00Z"


def fixture():
    return {
        "repository": REPO, "main_head": M, "observed_at": STAMP,
        "open_prs": [{
            "number": 17, "head": H, "state": "open", "base": "main",
            "changed_paths": ["src/ToyWarsServer.server.lua", "tests/test_selector_authority.py"]
        }],
        "adoptions": [{
            "source_pr": 17, "source_head": H, "via_pr": 30,
            "via_merge_sha": MERGE, "observed_main": M,
            "observed_at": STAMP, "main_contains_merge": True,
            "adopted_paths": ["src/ToyWarsServer.server.lua", "tests/test_selector_authority.py"],
            "evidence_url": "https://github.com/" + REPO + "/pull/30"
        }]
    }


class SupersessionAdvisoryTests(unittest.TestCase):
    def test_candidate_never_authorizes_mutation(self):
        out = evaluate(fixture())
        self.assertEqual(out["status"], "ADVISORY_READY")
        self.assertEqual(out["candidates"], 1)
        self.assertEqual(out["items"][0]["status"], "POSSIBLY_SUPERSEDED_REVIEW_ONLY")
        for key in ("may_close", "may_merge", "may_skip_review", "may_write", "independently_verified"):
            self.assertIs(out[key], False)

    def test_source_head_drift(self):
        item = fixture()
        item["open_prs"][0]["head"] = ALT
        self.assertEqual(evaluate(item)["items"][0]["status"], "STALE_SOURCE_HEAD")

    def test_main_head_drift(self):
        item = fixture()
        item["main_head"] = ALT
        self.assertEqual(evaluate(item)["items"][0]["status"], "STALE_MAIN_HEAD")

    def test_ancestry_is_never_implied(self):
        item = fixture()
        item["adoptions"][0]["main_contains_merge"] = False
        self.assertEqual(evaluate(item)["items"][0]["status"], "ANCESTRY_UNPROVEN")

    def test_partial_path_is_not_candidate(self):
        item = fixture()
        item["adoptions"][0]["adopted_paths"].pop()
        out = evaluate(item)
        self.assertEqual(out["candidates"], 0)
        self.assertEqual(out["items"][0]["status"], "INCOMPLETE_PATH_COVERAGE")

    def test_receipt_absent_not_a_duplicate(self):
        item = fixture()
        item["adoptions"] = []
        self.assertEqual(evaluate(item)["items"][0]["status"], "NO_ADOPTION_RECEIPT")

    def test_empty_inventory_safe(self):
        item = fixture()
        item["open_prs"] = []
        item["adoptions"] = []
        self.assertEqual(evaluate(item)["scanned"], 0)

    def test_multiple_prs_sorted(self):
        item = fixture()
        other = copy.deepcopy(item["open_prs"][0])
        other["number"] = 2
        item["open_prs"].append(other)
        out = evaluate(item)
        self.assertEqual([x["pr"] for x in out["items"]], [2, 17])
        self.assertEqual(out["candidates"], 1)

    def test_failclosed_bad_receipts_and_prs(self):
        original = fixture()
        modifications = (
            lambda x: x["adoptions"].append(copy.deepcopy(x["adoptions"][0])),
            lambda x: x["open_prs"].append(copy.deepcopy(x["open_prs"][0])),
            lambda x: x["adoptions"][0].update(source_pr=True),
            lambda x: x["open_prs"][0].update(number=True),
            lambda x: x["adoptions"][0].update(via_pr=17),
            lambda x: x["adoptions"][0].update(main_contains_merge="true"),
            lambda x: x["adoptions"][0].update(via_merge_sha="invalid"),
            lambda x: x["adoptions"][0].update(evidence_url="https://evil.example/pull/30"),
            lambda x: x["adoptions"][0].update(observed_at="2026-11-01T00:00:00Z"),
            lambda x: x["adoptions"][0].update(observed_at="2026-10-31T07:30:00"),
            lambda x: x["adoptions"][0].update(adopted_paths=["../src/file"]),
            lambda x: x["open_prs"][0].update(changed_paths=["src/file", "src/file"]),
            lambda x: x["open_prs"][0].update(state="closed"),
            lambda x: x["open_prs"][0].update(head=1234),
            lambda x: x.update(main_head="invalid"),
            lambda x: x.update(repository="other/repo/extra"),
            lambda x: x.update(observed_at="not-a-date"),
            lambda x: x.update(adoptions=None),
            lambda x: x.update(open_prs="not-list"),
            lambda x: x.update(extra=True),
        )
        for f in modifications:
            item = copy.deepcopy(original)
            f(item)
            with self.subTest(index=modifications.index(f)):
                result = evaluate(item)
                self.assertEqual(result["status"], "WAIT_METADATA")
                self.assertFalse(result["may_write"])

    def test_no_hints_are_treated_as_provider_attestation(self):
        out = evaluate(fixture())
        self.assertFalse(out["independently_verified"])
        self.assertIn("not provider-attested", out["warning"])


if __name__ == "__main__":
    unittest.main()
