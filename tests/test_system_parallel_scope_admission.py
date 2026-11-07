"""Pure proposal tests; no real GitHub claim, author, runner or writer exists."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_parallel_scope_admission import compare_claims, normalized_path, InvalidScope

BASE = "a" * 40


def scope(work="a-work", branch="controller/first-work", write=None, read=None,
          generated=None, resources=None, **overrides):
    value = {
        "project_id": "toy-wars-factory",
        "repository": "kk051780/toy-wars-factory",
        "work_id": work,
        "branch": branch,
        "base_sha": BASE,
        "write_paths": write if write is not None else ["tools/test_a.py"],
        "read_paths": read if read is not None else [],
        "generated_paths": generated if generated is not None else [],
        "shared_resources": resources if resources is not None else [],
        "status": "ACTIVE",
    }
    value.update(overrides)
    return value


def proposed(a, b):
    return compare_claims([a], b)["decision"]


class ScopeAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.a = scope()
        self.b = scope("b-work", "controller/second-work",
                       write=["tests/test_b.py"])

    def test_disjoint_two_writers_advisory(self):
        result = compare_claims([self.a], self.b)
        self.assertEqual(result["decision"], "PROPOSE_DISJOINT")
        self.assertFalse(result["may_write"])
        self.assertFalse(result["may_dispatch"])
        self.assertFalse(result["github_authenticated"])
        self.assertFalse(result["real_parallel_verified"])

    def test_no_existing_scope_is_advisory(self):
        self.assertEqual(compare_claims([], self.a)["decision"], "PROPOSE_DISJOINT")

    def test_same_work_rejoins(self):
        self.assertEqual(proposed(self.a, copy.deepcopy(self.a)), "JOIN_EXISTING")

    def test_same_work_different_branch_blocked(self):
        self.assertEqual(proposed(self.a, scope("a-work", "controller/other-work")),
                         "WAIT_WORK_ID_DRIFT")

    def test_same_branch_different_work_blocked(self):
        self.assertEqual(proposed(self.a, scope("b-work", "controller/first-work")),
                         "WAIT_BRANCH_COLLISION")

    def test_identical_file(self):
        self.b["write_paths"] = ["tools/test_a.py"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_WRITE_COLLISION")

    def test_casefold_file_alias(self):
        self.b["write_paths"] = ["TOOLS/TEST_A.py"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_WRITE_COLLISION")

    def test_directory_overlap(self):
        self.a["write_paths"] = ["tests"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_WRITE_COLLISION")

    def test_read_write_conflict(self):
        self.b["read_paths"] = ["tools/test_a.py"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_READ_WRITE_COLLISION")

    def test_same_read_only_dependency_is_allowed(self):
        self.a["read_paths"] = ["README.md"]
        self.b["read_paths"] = ["README.md"]
        self.assertEqual(proposed(self.a, self.b), "PROPOSE_DISJOINT")

    def test_explicit_semantic_overlap(self):
        self.a["shared_resources"] = ["game:world-state"]
        self.b["shared_resources"] = ["game:world-state"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_SEMANTIC_COLLISION")

    def test_implicit_canonical_game_interface_overlap(self):
        self.a["write_paths"] = ["src/ToyWarsBalance.lua"]
        self.b["write_paths"] = ["config/characters.json"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_SEMANTIC_COLLISION")

    def test_generated_file_shared(self):
        self.a["write_paths"] = ["history/C01234.json"]
        self.a["generated_paths"] = ["history/C01234.json"]
        self.b["write_paths"] = ["history/c01234.json"]
        self.b["generated_paths"] = ["history/c01234.json"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_WRITE_COLLISION")

    def test_generated_file_undeclared_rejected(self):
        self.b["generated_paths"] = ["history/missing.json"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_INVALID_SCOPE")

    def test_any_protected_policy_change_remains_exclusive(self):
        self.b["write_paths"] = [".github/workflows/test.yml"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_EXCLUSIVE_SCOPE")

    def test_coordinator_change_exclusive(self):
        self.b["write_paths"] = ["ops/REPAIR_COORDINATOR.json"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_EXCLUSIVE_SCOPE")

    def test_three_writers_blocked(self):
        third = scope("c-work", "controller/third-work", write=["tools/c.py"])
        self.assertEqual(compare_claims([self.a, self.b], third)["decision"],
                         "WAIT_CAPACITY")

    def test_drifted_main_blocked(self):
        self.b["base_sha"] = "b" * 40
        self.assertEqual(proposed(self.a, self.b), "WAIT_BASE_DRIFT")

    def test_foreign_project_blocked(self):
        self.b["project_id"] = "another-game"
        self.assertEqual(proposed(self.a, self.b), "WAIT_FOREIGN_PROJECT")

    def test_foreign_repository_blocked(self):
        self.b["repository"] = "kk051780/other-game"
        self.assertEqual(proposed(self.a, self.b), "WAIT_FOREIGN_PROJECT")

    def test_invalid_project_or_repo(self):
        self.b["repository"] = "../other-game"
        self.assertEqual(proposed(self.a, self.b), "WAIT_INVALID_SCOPE")

    def test_duplicate_normalized_write_paths_fail_closed(self):
        self.b["write_paths"] = ["src/X.lua", "src/x.lua"]
        self.assertEqual(proposed(self.a, self.b), "WAIT_INVALID_SCOPE")

    def test_duplicate_work_records_fail_closed(self):
        self.assertEqual(compare_claims([self.a, self.a], self.b)["decision"],
                         "WAIT_INVALID_SCOPE")

    def test_ambiguous_path_forms_fail_closed(self):
        for bad in ("src/../config/a", "src\\a", "src/%2e%2e/a",
                    "/src/a", "src//a", "src/*.lua", "src/a/",
                    "src/./a", ".git/config", "src/a.", "src/ａ.py"):
            with self.subTest(path=bad):
                with self.assertRaises(InvalidScope):
                    normalized_path(bad)

    def test_untrusted_schema_extra_key_rejected(self):
        self.b["verified_by_chat"] = True
        self.assertEqual(proposed(self.a, self.b), "WAIT_INVALID_SCOPE")

    def test_unrecognized_status_rejected(self):
        self.b["status"] = "SUCCESS"
        self.assertEqual(proposed(self.a, self.b), "WAIT_INVALID_SCOPE")

    def test_closed_predecessor_does_not_claim_active_slot(self):
        self.a["status"] = "CLOSED"
        self.assertEqual(proposed(self.a, self.b), "PROPOSE_DISJOINT")

    def test_all_decisions_non_authorizing(self):
        for candidate in (self.b, copy.deepcopy(self.a),
                          scope("x-work", "controller/other-work", write=["AGENTS.md"])):
            result = compare_claims([self.a], candidate)
            self.assertFalse(result["may_write"])
            self.assertFalse(result["may_dispatch"])
            self.assertFalse(result["github_authenticated"])


if __name__ == "__main__":
    unittest.main()
