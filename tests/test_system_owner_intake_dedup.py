"""Local-only adversarial cases for a proposed advisory owner-intake reducer."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_owner_intake_dedup import calculate_work_id, classify, strict_json


def sample():
    return {
        "schema": 2,
        "project_id": "toy-wars-factory",
        "repository": "kk051780/toy-wars-factory",
        "main_sha": "a" * 40,
        "collection_complete": True,
        "incoming": {"idea_id": "owner:oct31:a", "kind": "gameplay",
                     "objective": "Add a toy repair character"},
        "records": []
    }


def existing(data, idea_id="owner:oct30:b", objective="Add a toy repair character", status="OPEN"):
    return {"idea_id": idea_id, "kind": data["incoming"]["kind"],
            "project_id": data["project_id"], "repository": data["repository"],
            "objective": objective, "status": status,
            "work_id": calculate_work_id(data["project_id"], data["repository"],
                                         data["incoming"]["kind"], objective)}


class OwnerIdeaIntakeTests(unittest.TestCase):
    def test_v2_scoped_record_can_join_without_cross_game_ambiguity(self):
        d = sample()
        d["schema"] = 2
        row = existing(d)
        row.update(project_id=d["project_id"], repository=d["repository"])
        d["records"] = [row]
        r = classify(d)
        self.assertEqual(r["decision"], "JOIN_EXISTING_ADVISORY")
        self.assertEqual(r["schema"], 2)

    def test_v2_empty_inventory_is_valid_new_candidate(self):
        d = sample()
        d["schema"] = 2
        r = classify(d)
        self.assertEqual(r["decision"], "NEW_ID_CANDIDATE_ONLY")
        self.assertFalse(r["may_write"])

    def test_v1_unscoped_records_must_be_refused_after_migration(self):
        d = sample()
        d["schema"] = 1
        row = existing(d)
        del row["project_id"], row["repository"]
        d["records"] = [row]
        with self.assertRaises(ValueError):
            classify(d)

    def test_v2_unscoped_record_must_not_be_silently_assumed_local(self):
        d = sample()
        d["schema"] = 2
        row = existing(d)
        del row["project_id"], row["repository"]
        d["records"] = [row]
        with self.assertRaises(ValueError):
            classify(d)

    def test_v2_foreign_project_with_even_forged_local_work_id_fails(self):
        d = sample()
        d["schema"] = 2
        row = existing(d)
        row.update(project_id="other-game", repository=d["repository"])
        d["records"] = [row]
        with self.assertRaises(ValueError):
            classify(d)

    def test_v2_foreign_repository_with_own_work_id_fails(self):
        d = sample()
        d["schema"] = 2
        row = existing(d)
        row.update(project_id=d["project_id"], repository="other/repository")
        d["records"] = [row]
        with self.assertRaises(ValueError):
            classify(d)

    def test_v2_self_consistent_foreign_scope_is_still_refused(self):
        d = sample()
        d["schema"] = 2
        row = existing(d)
        row.update(project_id="other-game", repository="other/repository")
        row["work_id"] = calculate_work_id(
            row["project_id"], row["repository"], row["kind"], row["objective"])
        d["records"] = [row]
        with self.assertRaises(ValueError):
            classify(d)

    def test_v2_malformed_scope_types_fail_closed(self):
        for field, value in (("project_id", False), ("project_id", "Other"),
                             ("repository", []), ("repository", "other\\repo")):
            with self.subTest(field=field, value=str(value)):
                d = sample()
                d["schema"] = 2
                row = existing(d)
                row.update(project_id=d["project_id"], repository=d["repository"])
                row[field] = value
                d["records"] = [row]
                with self.assertRaises(ValueError):
                    classify(d)

    def test_first_intake_is_only_a_candidate(self):
        r = classify(sample())
        self.assertEqual(r["decision"], "NEW_ID_CANDIDATE_ONLY")
        self.assertFalse(r["cas_performed"])

    def test_same_goal_two_chat_origins_join_one_work_id(self):
        d = sample()
        d["records"] = [existing(d)]
        r = classify(d)
        self.assertEqual(r["decision"], "JOIN_EXISTING_ADVISORY")
        self.assertEqual(r["proposed_work_id"], d["records"][0]["work_id"])

    def test_two_simultaneous_unregistered_chats_are_not_a_cas_claim(self):
        first = sample()
        second = sample()
        second["incoming"]["idea_id"] = "chat:other-conversation"
        a, b = classify(first), classify(second)
        self.assertEqual(a["proposed_work_id"], b["proposed_work_id"])
        self.assertEqual((a["decision"], b["decision"]),
                         ("NEW_ID_CANDIDATE_ONLY", "NEW_ID_CANDIDATE_ONLY"))
        self.assertFalse(a["may_claim"] or b["may_claim"])
        self.assertFalse(a["cas_performed"] or b["cas_performed"])

    def test_same_owner_idea_repeated_is_idempotent(self):
        d = sample()
        d["records"] = [existing(d, idea_id=d["incoming"]["idea_id"])]
        self.assertEqual(classify(d)["decision"], "JOIN_EXISTING_ADVISORY")

    def test_whitespace_fullwidth_unicode_equivalence(self):
        d = sample()
        d["records"] = [existing(d, objective="  Ａｄｄ　a toy   repair character ")]
        self.assertEqual(classify(d)["decision"], "JOIN_EXISTING_ADVISORY")

    def test_existing_done_must_not_restart(self):
        d = sample()
        d["records"] = [existing(d, status="DONE")]
        r = classify(d)
        self.assertEqual((r["decision"], r["existing_status"]),
                         ("JOIN_EXISTING_ADVISORY", "DONE"))

    def test_cancelled_record_does_not_silently_recreate(self):
        d = sample()
        d["records"] = [existing(d, status="CANCELLED")]
        self.assertEqual(classify(d)["existing_status"], "CANCELLED")

    def test_owner_idea_id_drift_wait(self):
        d = sample()
        d["records"] = [existing(d, idea_id=d["incoming"]["idea_id"],
                                 objective="Add a fast factory machine")]
        self.assertEqual(classify(d)["decision"], "WAIT_OWNER_ID_DRIFT")

    def test_renamed_paraphrase_not_claimed_as_semantic_duplicate(self):
        d = sample()
        d["records"] = [existing(d, objective="Create a maintenance toy")]
        r = classify(d)
        self.assertEqual(r["decision"], "NEW_ID_CANDIDATE_ONLY")
        self.assertFalse(r["may_claim"])

    def test_cross_project_and_repo_produce_distinct_ids(self):
        d = sample()
        a = classify(d)["proposed_work_id"]
        d["project_id"] = "other-game"
        b = classify(d)["proposed_work_id"]
        d["repository"] = "other/repository"
        c = classify(d)["proposed_work_id"]
        self.assertEqual(len({a, b, c}), 3)

    def test_github_repository_case_aliases_share_work_id(self):
        d = sample()
        args = (d["project_id"], d["incoming"]["kind"], d["incoming"]["objective"])
        lower = calculate_work_id(args[0], "kk051780/toy-wars-factory", args[1], args[2])
        mixed = calculate_work_id(args[0], "Kk051780/Toy-Wars-Factory", args[1], args[2])
        upper = calculate_work_id(args[0], "KK051780/TOY-WARS-FACTORY", args[1], args[2])
        self.assertEqual(lower, mixed)
        self.assertEqual(lower, upper)

    def test_uppercase_repository_intake_fails_closed(self):
        d = sample()
        d["repository"] = "KK051780/TOY-WARS-FACTORY"
        with self.assertRaises(ValueError):
            classify(d)

    def test_case_mismatched_existing_record_fails_closed(self):
        d = sample()
        d["records"] = [existing(d)]
        d["records"][0]["repository"] = "KK051780/TOY-WARS-FACTORY"
        with self.assertRaises(ValueError):
            classify(d)

    def test_existing_lowercase_repository_work_id_remains_stable(self):
        d = sample()
        observed = calculate_work_id(d["project_id"], d["repository"],
                                     d["incoming"]["kind"], d["incoming"]["objective"])
        self.assertEqual(observed, "work-ee37da2c214de8b04dbc49b8")

    def test_duplicate_work_id_rejected(self):
        d = sample()
        d["records"] = [existing(d), existing(d, idea_id="owner:c")]
        with self.assertRaises(ValueError):
            classify(d)

    def test_spoofed_noncanonical_id_rejected(self):
        d = sample()
        d["records"] = [existing(d)]
        d["records"][0]["work_id"] = "work-spoofed"
        with self.assertRaises(ValueError):
            classify(d)

    def test_conflicting_historic_idea_id_rejected(self):
        d = sample()
        d["records"] = [existing(d, idea_id="owner:x"),
                        existing(d, idea_id="owner:x", objective="Build a new workshop")]
        with self.assertRaises(ValueError):
            classify(d)

    def test_wrong_main_sha_rejected(self):
        d = sample()
        d["main_sha"] = "oops"
        with self.assertRaises(ValueError):
            classify(d)

    def test_collection_incomplete_rejected(self):
        d = sample()
        d["collection_complete"] = False
        with self.assertRaises(ValueError):
            classify(d)

    def test_unknown_fields_or_wrong_schema_rejected(self):
        for k, v in (("schema", True), ("schema", 1), ("extra", "yes")):
            d = sample()
            d[k] = v
            with self.assertRaises(ValueError):
                classify(d)

    def test_wrong_repo_and_project_rejected(self):
        for k, v in (("repository", "../elsewhere"), ("project_id", "X")):
            d = sample()
            d[k] = v
            with self.assertRaises(ValueError):
                classify(d)

    def test_malformed_unhashable_kind_or_status_rejected(self):
        d = sample()
        d["incoming"]["kind"] = []
        with self.assertRaises(ValueError):
            classify(d)
        d = sample()
        d["records"] = [existing(d)]
        d["records"][0]["status"] = []
        with self.assertRaises(ValueError):
            classify(d)

    def test_control_and_bidi_objectives_rejected(self):
        for suffix in ("\u202e", "\u200b", "\x00"):
            d = sample()
            d["incoming"]["objective"] += suffix
            with self.assertRaises(ValueError):
                classify(d)

    def test_all_outcomes_cannot_authorize(self):
        for mode in ("new", "join", "drift"):
            d = sample()
            if mode == "join":
                d["records"] = [existing(d)]
            if mode == "drift":
                d["records"] = [existing(d, idea_id=d["incoming"]["idea_id"],
                                         objective="Build a new workshop")]
            r = classify(d)
            for key in ("github_authenticated", "provider_run_authenticated", "may_claim",
                        "may_write", "may_dispatch", "may_merge", "cas_performed"):
                self.assertFalse(r[key], (mode, key))

    def test_cli_valid_and_drift_exit_codes(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "system_owner_intake_dedup.py"
        d = sample()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "request.json"
            p.write_text(json.dumps(d))
            run = subprocess.run([sys.executable, str(script), "--input", str(p)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            d["records"] = [existing(d, idea_id=d["incoming"]["idea_id"],
                                     objective="Build a new workshop")]
            p.write_text(json.dumps(d))
            run = subprocess.run([sys.executable, str(script), "--input", str(p)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)

    def test_cli_duplicate_json_key_and_nonfinite_fail(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "system_owner_intake_dedup.py"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "request.json"
            for raw in ('{"schema":1,"schema":1}', '{"schema":NaN}'):
                p.write_text(raw)
                run = subprocess.run([sys.executable, str(script), "--input", str(p)], capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertIn("WAIT_INVALID_INPUT", run.stdout)

    def test_deep_json_parser_returns_bounded_value_error(self):
        from system_owner_intake_dedup import strict_json
        raw = "[" * 40000 + "0" + "]" * 40000
        self.assertLess(len(raw.encode("utf-8")), 128 * 1024)
        with self.assertRaisesRegex(ValueError, "JSON nesting too deep"):
            strict_json(raw)

    def test_deep_json_cli_fail_closed_without_traceback(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "system_owner_intake_dedup.py"
        raw = "[" * 40000 + "0" + "]" * 40000
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "deep.json"
            p.write_text(raw, encoding="utf-8")
            result = subprocess.run([sys.executable, str(script), "--input", str(p)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "WAIT_INVALID_INPUT")
        self.assertIs(payload["may_write"], False)
        self.assertEqual(payload["reason"], "JSON nesting too deep")

    def test_cli_oversize_rejected(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "system_owner_intake_dedup.py"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "request.json"
            p.write_text(" " * (128 * 1024 + 1))
            run = subprocess.run([sys.executable, str(script), "--input", str(p)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)


if __name__ == "__main__":
    unittest.main()
