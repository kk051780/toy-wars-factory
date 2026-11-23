import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from p0d_work_claim_guard import check

H = "a" * 40
B = "b" * 40
NOW = datetime(2026, 11, 15, 0, 0, tzinfo=timezone.utc)


def row(claim="CLAIM-1", feat="ART-CASTLE", owner="PREP-ONE", resources=None, paths=None, expires="2026-11-16T00:00:00Z"):
    return {"claim_id": claim, "feature_id": feat, "owner": owner, "resources": resources or ["ART-CASTLE"],
            "target_paths": paths or ["releases/P0D_S1_KIDS_RC01/src/server/World*.luau"],
            "state": "GRANTED", "expires_at": expires}


def registry(rows=None):
    return {"schema": "P0D_EXCLUSIVE_CLAIMS_V1", "aliases": {"CASTLE_3D": "ART_CASTLE", "WORLD_CASTLE": "ART_CASTLE",
            "SEA_BIOME": "ART_SEA"}, "claims": rows if rows is not None else [row()]}


def cand(**kwargs):
    return {**{"claim_id": "CLAIM-1", "feature_id": "ART-CASTLE", "owner": "PREP-ONE",
            "resources": ["WORLD_CASTLE"], "source_head": B, "base_rc": H}, **kwargs}


PATH = ["releases/P0D_S1_KIDS_RC01/src/server/WorldArt.luau"]


class ClaimGuardTests(unittest.TestCase):
    def test_authorized_scope(self):
        a = check(registry(), cand(), PATH, H, NOW)
        self.assertEqual(a["result"], "CLAIM_SCOPE_PASS_NOT_RC_ADOPTION")

    def test_missing_claim_fails(self):
        with self.assertRaisesRegex(ValueError, "CLAIM_NOT_GRANTED"):
            check(registry([]), cand(), PATH, H, NOW)

    def test_different_owner_fails(self):
        with self.assertRaisesRegex(ValueError, "OWNER_MISMATCH"):
            check(registry(), cand(owner="PREP-TWO"), PATH, H, NOW)

    def test_same_feature_claim_conflict_fails(self):
        r = registry([row(), row(claim="CLAIM-2", owner="PREP-TWO", paths=["other/path.luau"])])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)

    def test_different_alias_but_same_resource_fails(self):
        r = registry([row(), row(claim="CLAIM-2", feat="DIFFERENT", owner="PREP-TWO", resources=["CASTLE_3D"], paths=["other/path.luau"])])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)

    def test_overlapping_paths_block_different_features(self):
        r = registry([row(), row(claim="CLAIM-2", feat="ART-SEA", owner="PREP-TWO", resources=["ART-SEA"], paths=PATH)])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)

    def test_distinct_features_parallel(self):
        r = registry([row(), row(claim="CLAIM-2", feat="ART-SEA", owner="PREP-TWO", resources=["ART-SEA"], paths=["releases/P0D_S1_KIDS_RC01/src/client/WaterArt.luau"])])
        self.assertEqual(check(r, cand(), PATH, H, NOW)["changed_files"], 1)

    def test_expired_claim_never_auto_reassign(self):
        r = registry([row(expires="2026-11-14T00:00:00Z")])
        with self.assertRaisesRegex(ValueError, "STALE_CLAIM"):
            check(r, cand(), PATH, H, NOW)

    def test_changed_file_outside_scope(self):
        with self.assertRaisesRegex(ValueError, "CHANGED_FILES_EXCEED_GRANT"):
            check(registry(), cand(), PATH + ["src/server/Game.server.luau"], H, NOW)

    def test_unreserved_resource(self):
        with self.assertRaisesRegex(ValueError, "RESOURCE_SCOPE_EXCEEDS_GRANT"):
            check(registry(), cand(resources=["ART-SEA"]), PATH, H, NOW)

    def test_old_rc_base_fails(self):
        with self.assertRaisesRegex(ValueError, "STALE_RC_BASE"):
            check(registry(), cand(base_rc=B), PATH, H, NOW)

    def test_no_diff_file_list_fails(self):
        with self.assertRaisesRegex(ValueError, "MISSING_CHANGED_PATHS"):
            check(registry(), cand(), [], H, NOW)

    def test_duplicate_claim_id_fails(self):
        r = registry([row(), row(claim="CLAIM-1", feat="ART-SEA", resources=["ART-SEA"], paths=["other/path.luau"])])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CLAIM_ID"):
            check(r, cand(), PATH, H, NOW)

    def test_malicious_path_fails(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TARGET_PATH"):
            check(registry(), cand(), ["../../secrets.txt"], H, NOW)

    def test_closed_claim_does_not_authorize_candidate(self):
        r = registry([{**row(), "state": "RC_INTEGRATED"}])
        with self.assertRaisesRegex(ValueError, "CLAIM_NOT_GRANTED"):
            check(r, cand(), PATH, H, NOW)

    def test_glob_overlap_is_conservative(self):
        r = registry([row(), row(claim="CLAIM-2", feat="ART-SEA", resources=["ART-SEA"], paths=["releases/P0D_S1_KIDS_RC01/src/server/*.luau"])])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)


# Synthetic source-increment snapshots exercise the offline evidence contract.
# They are not authenticated GitHub objects, grants, publication or CI receipts.
import io
import json
import tempfile
from contextlib import redirect_stdout
from unittest.mock import patch
import p0d_work_claim_guard as source_guard


def source_fixture(phase="PREPARED", legacy_g4=False):
    """Fresh inline version of the frozen synthetic schema; no external inputs."""
    u, a, h, b, m = (v * 20 for v in ("10", "20", "30", "40", "50"))
    ta, th, tm = (v * 20 for v in ("60", "70", "80"))
    repo = "synthetic-owner/synthetic-claim-guard"
    branch, base_ref = "feature/synthetic-claim-guard", "feature/synthetic-base"
    workflow = ".github/workflows/p0d-work-claim-gate.yml"
    document = "rc_fastlane/NO_DUPLICATE_WORK_V1.md"
    test_path = "tests/test_p0d_work_claim_guard.py"
    guard_path = "tools/p0d_work_claim_guard.py"
    mutable = [test_path, guard_path]
    frozen = {workflow: "91" * 20, document: "92" * 20}
    if legacy_g4:
        # Same legacy flag shape and 2/7/9 partition, still synthetic evidence.
        frozen.update({f"rc_fastlane/SYNTHETIC_FROZEN_{i}.md": f"{i + 145:02x}" * 20
                       for i in range(3, 8)})
    targets = sorted([*frozen, *mutable])
    leaves = [(p, sha, sha) for p, sha in frozen.items()] + [
        ("src/game.luau", "93" * 20, "93" * 20),
        (test_path, "b1" * 20, "b2" * 20),
        (guard_path, "a1" * 20, "a2" * 20),
    ]
    directories = [
        (".github", "c1" * 20, "c1" * 20),
        (".github/workflows", "c2" * 20, "c2" * 20),
        ("rc_fastlane", "c3" * 20, "c3" * 20),
        ("src", "c4" * 20, "c4" * 20),
        ("tests", "e1" * 20, "e2" * 20),
        ("tools", "d1" * 20, "d2" * 20),
    ]

    def entries(head):
        result = [{"path": p, "type": "tree", "mode": "040000", "sha": after if head else before}
                  for p, before, after in directories]
        result += [{"path": p, "type": "blob", "mode": "100644", "sha": after if head else before}
                   for p, before, after in leaves]
        return sorted(result, key=lambda item: item["path"])

    grant = {
        "claim_id": "SYNTHETIC-CLAIM-GUARD-INPLACE",
        "owner": "SYNTHETIC_AUTHOR", "feature_id": "SYNTHETIC_CLAIM_GUARD",
        "resources": ["SYNTHETIC_CLAIM_GUARD"], "state": "GRANTED",
        "expires_at": "2026-11-24T00:00:00Z",
        "target_paths": targets, "mutable_paths": mutable,
        "preserved_pr_diff_blobs": frozen,
        "source_head_before": a, "maintenance_base_sha": a, "source_head": None,
        "base_rc_sha": u, "prep_branch": branch, "pr": 469,
        "pr_base_ref": base_ref, "pr_base_sha": b,
        "source_increment_policy": {
            "schema": "P0D_SOURCE_INCREMENT_POLICY_V1",
            "kind": "IN_PLACE_REGULAR_BLOBS",
        },
    }
    if legacy_g4:
        del grant["source_increment_policy"]
        grant["source_increment_validation"] = {
            "compare_base": a,
            "allowed_changed_paths": list(mutable),
            "requires_actual_GitHub_compare_newHEAD": True,
            "requires_actual_cumulative_PR_diff9": True,
            "requires_frozen7_blob_readback": True,
            "guard_PASS_alone_does_not_grant_frozen_paths": True,
            "requires_independent_prepublication_actual_commit_tree_review": True,
            "candidate_must_descend_from_expected_donor_head": True,
            "only_modify_existing_two_regular_blob_files_in_place": True,
            "no_add_delete_rename_copy_or_type_mode_change": True,
            "must_include_previous_filename_or_old_path_in_complete_delta": True,
            "frozen7_must_preserve_path_type_mode_blob": True,
            "type_mode_reference": "Actual immutable maintenance-anchor tree; do not assume contents-API mode values.",
            "nonforce_expected_source_branch_HEAD_required": True,
            "repeat_actual_API_readback_after_publish": True,
        }
    observed = a if phase == "PREPARED" else h
    after = {p: sha for p, _, sha in leaves}
    evidence = {
        "schema": "P0D_SOURCE_INCREMENT_EVIDENCE_V1", "phase": phase,
        "repository_full_name": repo, "source_ref": branch,
        "observed_source_head": observed,
        "pr": {"number": 469, "repository_full_name": repo, "base_ref": base_ref,
               "base_sha": b, "head_sha": observed},
        "commits": {
            "anchor": {"sha": a, "tree_sha": ta, "parents": [m]},
            "candidate": {"sha": h, "tree_sha": th, "parents": [a]},
            "pr_base": {"sha": b, "tree_sha": tm, "parents": [m]},
            "merge_base": {"sha": m, "tree_sha": tm, "parents": []},
        },
        "trees": {
            ta: {"sha": ta, "truncated": False, "entries": entries(False)},
            th: {"sha": th, "truncated": False, "entries": entries(True)},
            tm: {"sha": tm, "truncated": False, "entries": [
                {"path": "src", "type": "tree", "mode": "040000", "sha": "c4" * 20},
                {"path": "src/game.luau", "type": "blob", "mode": "100644", "sha": "93" * 20},
            ]},
        },
        "increment": {
            "base_sha": a, "head_sha": h, "merge_base_sha": a,
            "status": "ahead", "ahead_by": 1, "behind_by": 0,
            "complete": True, "truncated": False,
            "files": [{"filename": p, "status": "modified", "old_path": p,
                       "previous_filename": None, "sha": after[p]} for p in mutable],
        },
        "cumulative": {
            "base_sha": b, "head_sha": h, "merge_base_sha": m,
            "complete": True, "truncated": False, "changed_files": len(targets),
            "files": [{"filename": p, "status": "added", "old_path": None,
                       "previous_filename": None, "sha": after[p]} for p in targets],
        },
        "provenance": {
            "kind": "LOCAL_PREPARED_GIT" if phase == "PREPARED" else "GITHUB_API_READBACK",
            "repository_full_name": repo, "candidate_sha": h,
            "observed_source_head": observed, "observed_pr_head": observed,
            "observed_refs": [
                {"role": "source", "repository_full_name": repo, "ref": branch, "sha": observed},
                {"role": "pr_head", "repository_full_name": repo, "ref": "pull/469/head", "sha": observed},
                {"role": "pr_base", "repository_full_name": repo, "ref": base_ref, "sha": b},
                {"role": "official_rc", "repository_full_name": repo, "ref": "rc/synthetic-official", "sha": u},
            ],
        },
    }
    return {
        "registry": {"schema": "P0D_EXCLUSIVE_CLAIMS_V1", "aliases": {}, "claims": [grant]},
        "candidate": {"claim_id": grant["claim_id"], "owner": grant["owner"],
                      "feature_id": grant["feature_id"], "resources": list(grant["resources"]),
                      "source_head": h, "base_rc": u},
        "actual_paths": list(targets), "official_head": u,
        "now": datetime(2026, 11, 23, tzinfo=timezone.utc), "evidence": evidence,
    }


def source_call(data):
    return source_guard.check_source_increment(
        data["registry"], data["candidate"], data["actual_paths"],
        data["official_head"], data["now"], data["evidence"])


def source_cli(data, evidence_mode=None):
    """Exercise the real entrypoint without subprocesses or external services."""
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        argv = ["p0d_work_claim_guard.py", "--official-head", data["official_head"],
                "--now", data["now"].isoformat()]
        for flag, value in (("registry", data["registry"]), ("candidate", data["candidate"]),
                            ("changed-files", data["actual_paths"])):
            path = folder / (flag + ".json")
            path.write_text(json.dumps(value), encoding="utf-8")
            argv.extend(["--" + flag, str(path)])
        if evidence_mode == "empty":
            argv.extend(["--source-evidence", ""])
        elif evidence_mode is not None:
            path = folder / "source-evidence.json"
            if evidence_mode == "present":
                path.write_text(json.dumps(data["evidence"]), encoding="utf-8")
            argv.extend(["--source-evidence", str(path)])
        output = io.StringIO()
        with patch.object(sys, "argv", argv), redirect_stdout(output):
            exit_code = source_guard.main()
        return exit_code, json.loads(output.getvalue())


class SourceIncrementTests(unittest.TestCase):
    def entry(self, data, commit, path):
        evidence = data["evidence"]
        tree = evidence["trees"][evidence["commits"][commit]["tree_sha"]]
        return next(item for item in tree["entries"] if item["path"] == path)

    def assert_evidence_only(self, answer, phase, cumulative=4, frozen=2):
        self.assertEqual(answer["result"], "SOURCE_INCREMENT_EVIDENCE_CONSISTENT_NOT_RC_ADOPTION")
        self.assertEqual(answer["schema"], "P0D_SOURCE_INCREMENT_GATE_V1")
        self.assertEqual(answer["phase"], phase)
        for field in ("provider_evidence_authenticated", "independent_approval_verified",
                      "publication_authorized", "same_head_ci_verified"):
            self.assertIs(answer[field], False)
        self.assertIs(answer["no_merge"], True)
        for field, value in (("incremental_changed_files", 2),
                             ("cumulative_changed_files", cumulative), ("frozen_files", frozen)):
            self.assertIs(type(answer[field]), int)
            self.assertEqual(answer[field], value)

    def test_strict_prepared_and_default_cli_scope(self):
        data = source_fixture()
        answer = source_call(data)
        self.assert_evidence_only(answer, "PREPARED")
        evidence = data["evidence"]
        self.assertEqual(answer["source_anchor"], evidence["commits"]["anchor"]["sha"])
        self.assertEqual(answer["source_head"], data["candidate"]["source_head"])
        self.assertEqual(answer["official_head"], data["official_head"])
        self.assertEqual(answer["pr_base"], evidence["pr"]["base_sha"])
        self.assertEqual(answer["merge_base"], evidence["cumulative"]["merge_base_sha"])
        self.assertEqual(len({answer[k] for k in
                              ("official_head", "source_anchor", "source_head", "pr_base", "merge_base")}), 5)
        code, default = source_cli(data)
        self.assertEqual(code, 0)
        self.assertEqual(default["schema"], "P0D_CLAIM_GATE_V1")
        self.assertEqual(default["result"], "CLAIM_SCOPE_PASS_NOT_RC_ADOPTION")
        self.assertNotIn("phase", default)
        self.assertEqual(default["changed_files"], 4)

    def test_strict_published_and_opt_in_cli(self):
        data = source_fixture("PUBLISHED")
        self.assert_evidence_only(source_call(data), "PUBLISHED")
        code, answer = source_cli(data, "present")
        self.assertEqual(code, 0)
        self.assert_evidence_only(answer, "PUBLISHED")
        code, missing = source_cli(data, "missing")
        self.assertEqual(code, 2)
        self.assertEqual(missing["result"], "BLOCKED")
        self.assertTrue(missing["reason"])
        code, empty = source_cli(data, "empty")
        self.assertEqual(code, 2)
        self.assertEqual(empty["schema"], "P0D_SOURCE_INCREMENT_GATE_V1")
        self.assertEqual(empty["result"], "BLOCKED")

    def test_strict_policy_selection_rejects_weakening(self):
        legacy = source_fixture(legacy_g4=True)
        self.assert_evidence_only(source_call(legacy), "PREPARED", cumulative=9, frozen=7)
        for case in ("missing", "unknown_kind", "weakening_key", "conflicting_policy", "g4_false"):
            with self.subTest(case=case):
                data = source_fixture(legacy_g4=(case == "g4_false"))
                grant = data["registry"]["claims"][0]
                if case == "missing":
                    del grant["source_increment_policy"]
                elif case == "unknown_kind":
                    grant["source_increment_policy"]["kind"] = "ALLOW_ADDITIONS"
                elif case == "weakening_key":
                    grant["source_increment_policy"]["allow_additions"] = True
                elif case == "conflicting_policy":
                    grant["source_increment_validation"] = {}
                else:
                    grant["source_increment_validation"]["no_add_delete_rename_copy_or_type_mode_change"] = False
                with self.assertRaises(ValueError):
                    source_call(data)
        for feature in ("GQ_BOSS_SHOCKWAVE_WALL_OCCLUSION_20261116",
                        "GQ8_REALM_PERMANENT_LAND_SEA_AIR_SUBSEA_20261118"):
            with self.subTest(unsupported=feature):
                data = source_fixture()
                grant = data["registry"]["claims"][0]
                del grant["source_increment_policy"]
                grant["feature_id"] = data["candidate"]["feature_id"] = feature
                ordinary = check(data["registry"], data["candidate"], data["actual_paths"],
                                 data["official_head"], data["now"])
                self.assertEqual(ordinary["result"], "CLAIM_SCOPE_PASS_NOT_RC_ADOPTION")
                with self.assertRaises(ValueError):
                    source_call(data)

    def test_strict_identity_and_ancestry_bindings(self):
        for case in ("anchor", "candidate", "base_ref", "tree", "merge_base",
                     "empty_parents", "behind", "source_ref", "repository"):
            with self.subTest(case=case):
                data = source_fixture()
                evidence = data["evidence"]
                if case == "anchor":
                    data["registry"]["claims"][0]["maintenance_base_sha"] = "ab" * 20
                elif case == "candidate":
                    data["candidate"]["source_head"] = "ab" * 20
                elif case == "base_ref":
                    evidence["pr"]["base_ref"] = "feature/wrong-base"
                elif case == "tree":
                    evidence["commits"]["candidate"]["tree_sha"] = evidence["commits"]["anchor"]["tree_sha"]
                elif case == "merge_base":
                    evidence["increment"]["merge_base_sha"] = evidence["pr"]["base_sha"]
                elif case == "empty_parents":
                    evidence["commits"]["candidate"]["parents"] = []
                elif case == "behind":
                    evidence["increment"]["behind_by"] = 1
                elif case == "source_ref":
                    evidence["source_ref"] = "feature/wrong-source"
                else:
                    evidence["provenance"]["observed_refs"][0]["repository_full_name"] = "different/repository"
                with self.assertRaises(ValueError):
                    source_call(data)
        descendant = source_fixture()
        descendant["evidence"]["commits"]["candidate"]["parents"] = ["31" * 20]
        descendant["evidence"]["increment"]["ahead_by"] = 2
        # The contract requires supplied ancestry facts, not direct-parent-only history.
        self.assert_evidence_only(source_call(descendant), "PREPARED")

    def test_strict_complete_and_typed_evidence(self):
        for case in ("missing_tree", "truncated_tree", "incomplete_files", "numeric_complete",
                     "numeric_truncated", "bool_ahead", "bool_behind", "float_count",
                     "duplicate_entry", "missing_observations"):
            with self.subTest(case=case):
                data = source_fixture()
                evidence = data["evidence"]
                anchor = evidence["trees"][evidence["commits"]["anchor"]["tree_sha"]]
                if case == "missing_tree":
                    del evidence["trees"][evidence["commits"]["merge_base"]["tree_sha"]]
                elif case == "truncated_tree":
                    anchor["truncated"] = True
                elif case == "incomplete_files":
                    evidence["increment"]["complete"] = False
                elif case == "numeric_complete":
                    evidence["increment"]["complete"] = 1
                elif case == "numeric_truncated":
                    anchor["truncated"] = 0
                elif case == "bool_ahead":
                    evidence["increment"]["ahead_by"] = True
                elif case == "bool_behind":
                    evidence["increment"]["behind_by"] = False
                elif case == "float_count":
                    evidence["cumulative"]["changed_files"] = 4.0
                elif case == "duplicate_entry":
                    anchor["entries"].append(dict(anchor["entries"][0]))
                else:
                    evidence["provenance"]["observed_refs"] = []
                with self.assertRaises(ValueError):
                    source_call(data)

    def test_strict_hidden_incremental_change_rejected(self):
        for path in ("src/game.luau", ".github/workflows/p0d-work-claim-gate.yml"):
            with self.subTest(hidden_path=path):
                data = source_fixture()
                self.entry(data, "candidate", path)["sha"] = "f1" * 20
                # The reported two-file increment deliberately omits this actual leaf change.
                with self.assertRaises(ValueError):
                    source_call(data)

    def test_strict_rename_and_old_path_rejected(self):
        for case in ("renamed", "copied", "case_only", "old_path",
                     "previous_filename", "missing_previous_filename"):
            with self.subTest(case=case):
                data = source_fixture()
                change = data["evidence"]["increment"]["files"][0]
                if case in ("renamed", "copied"):
                    change.update(status=case, old_path="outside/original.py",
                                  previous_filename="outside/original.py")
                elif case == "case_only":
                    original = change["filename"]
                    changed = original.replace("test_p0d", "TEST_p0d")
                    self.entry(data, "candidate", original)["path"] = changed
                    change.update(status="renamed", filename=changed,
                                  old_path=original, previous_filename=original)
                elif case == "old_path":
                    change["old_path"] = "outside/original.py"
                elif case == "previous_filename":
                    change["previous_filename"] = "outside/original.py"
                else:
                    del change["previous_filename"]
                with self.assertRaises(ValueError):
                    source_call(data)

    def test_strict_in_place_file_kind_and_mode(self):
        path = "tests/test_p0d_work_claim_guard.py"
        for case in ("added", "removed", "symlink", "gitlink", "mode"):
            with self.subTest(case=case):
                data = source_fixture()
                evidence = data["evidence"]
                change = evidence["increment"]["files"][0]
                if case in ("added", "removed"):
                    side = "anchor" if case == "added" else "candidate"
                    tree = evidence["trees"][evidence["commits"][side]["tree_sha"]]
                    tree["entries"] = [item for item in tree["entries"] if item["path"] != path]
                    change["status"] = case
                    if case == "added":
                        change["old_path"] = None
                else:
                    item = self.entry(data, "candidate", path)
                    if case == "symlink":
                        item["mode"] = "120000"
                    elif case == "gitlink":
                        item.update(type="commit", mode="160000")
                    else:
                        item["mode"] = "100755"
                with self.assertRaises(ValueError):
                    source_call(data)
        executable = source_fixture()
        for side in ("anchor", "candidate"):
            self.entry(executable, side, path)["mode"] = "100755"
        self.assertEqual({item["status"] for item in executable["evidence"]["cumulative"]["files"]}, {"added"})
        self.assert_evidence_only(source_call(executable), "PREPARED")

    def test_strict_frozen_and_unrelated_tree_preserved(self):
        path = ".github/workflows/p0d-work-claim-gate.yml"
        for case in ("pin", "mode", "type", "path", "unrelated_directory", "missing_parent"):
            with self.subTest(case=case):
                data = source_fixture()
                evidence = data["evidence"]
                if case == "pin":
                    data["registry"]["claims"][0]["preserved_pr_diff_blobs"][path] = "f2" * 20
                elif case == "mode":
                    self.entry(data, "candidate", path)["mode"] = "100755"
                elif case == "type":
                    self.entry(data, "candidate", path).update(type="commit", mode="160000")
                elif case == "path":
                    self.entry(data, "candidate", path)["path"] = ".github/workflows/other.yml"
                elif case == "unrelated_directory":
                    self.entry(data, "candidate", "src")["sha"] = "f3" * 20
                else:
                    tree = evidence["trees"][evidence["commits"]["candidate"]["tree_sha"]]
                    tree["entries"] = [item for item in tree["entries"] if item["path"] != "tests"]
                with self.assertRaises(ValueError):
                    source_call(data)
        actual_anchor_mode = source_fixture()
        for side in ("anchor", "candidate"):
            self.entry(actual_anchor_mode, side, path)["mode"] = "100755"
        self.assert_evidence_only(source_call(actual_anchor_mode), "PREPARED")
        case_distinct_unrelated = source_fixture()
        for tree in case_distinct_unrelated["evidence"]["trees"].values():
            tree["entries"].extend([
                {"path": "src/Kept.luau", "type": "blob", "mode": "100644", "sha": "f5" * 20},
                {"path": "src/kept.luau", "type": "blob", "mode": "100644", "sha": "f6" * 20},
            ])
        self.assert_evidence_only(source_call(case_distinct_unrelated), "PREPARED")

    def test_strict_cumulative_and_phase_binding(self):
        for case in ("missing", "extra", "duplicate", "old_name", "blob", "count",
                     "merge_base", "published_old_head", "wrong_phase_kind"):
            with self.subTest(case=case):
                data = source_fixture("PUBLISHED" if case == "published_old_head" else "PREPARED")
                evidence = data["evidence"]
                cumulative = evidence["cumulative"]
                if case == "missing":
                    cumulative["files"].pop()
                elif case == "extra":
                    cumulative["files"].append({"filename": "src/game.luau", "status": "modified",
                                                "old_path": "src/game.luau", "previous_filename": None,
                                                "sha": "93" * 20})
                    cumulative["changed_files"] += 1
                elif case == "duplicate":
                    cumulative["files"].append(dict(cumulative["files"][0]))
                    cumulative["changed_files"] += 1
                elif case == "old_name":
                    cumulative["files"][0].update(status="renamed", old_path="outside/original.yml",
                                                 previous_filename="outside/original.yml")
                elif case == "blob":
                    cumulative["files"][0]["sha"] = "f4" * 20
                elif case == "count":
                    cumulative["changed_files"] = 3
                elif case == "merge_base":
                    cumulative["merge_base_sha"] = evidence["pr"]["base_sha"]
                elif case == "published_old_head":
                    evidence["observed_source_head"] = evidence["commits"]["anchor"]["sha"]
                else:
                    evidence["provenance"]["kind"] = "GITHUB_API_READBACK"
                with self.assertRaises(ValueError):
                    source_call(data)


if __name__ == "__main__":
    unittest.main()
