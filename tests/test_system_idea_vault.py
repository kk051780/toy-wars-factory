"""Scoped stock and negative controls for the legal META port of manual PR110."""
from copy import deepcopy
import io
import json
import unittest
from unittest.mock import patch

from tools import system_idea_pipeline as pipeline
from tests.test_system_idea_pipeline import NOW, owner, web, proposal, scope


class VaultTests(unittest.TestCase):
    def rejected(self, fn):
        with self.assertRaises(pipeline.IdeaValidationError):
            fn()

    def test_unscoped_intake_is_not_a_stock_record(self):
        self.rejected(lambda: pipeline.capture(idea_id="ORIGINAL", project_id="game-one",
                      origin="OWNER", original_text="The original words", source_ref="NOT_AVAILABLE",
                      captured_at=NOW))

    def test_two_games_have_independent_repos_and_three_roles(self):
        rows = [owner("game-one"), owner("game-two")]
        self.assertEqual(pipeline.validate_registry(rows), rows)
        self.assertNotEqual(rows[0]["scope"]["repository"], rows[1]["scope"]["repository"])
        self.assertFalse(set(rows[0]["scope"]["tasks"].values()) & set(rows[1]["scope"]["tasks"].values()))

    def test_project_repository_reassignment_is_rejected(self):
        a = owner("game-one", "ORIGINAL_A")
        b = pipeline.capture(idea_id="ORIGINAL_B", project_id="game-one", origin="OWNER",
                             original_text="Other words in another repository", source_ref="NOT_AVAILABLE",
                             captured_at=NOW, scope=scope("game-two"))
        self.rejected(lambda: pipeline.validate_registry([a, b]))

    def test_cross_game_task_reuse_is_rejected(self):
        a = owner("game-one")
        s = scope("game-two"); s["tasks"]["WORKER"] = a["scope"]["tasks"]["WORKER"]
        b = pipeline.capture(idea_id="ORIGINAL_B", project_id="game-two", origin="OWNER",
                             original_text="Other game original words", source_ref="NOT_AVAILABLE",
                             captured_at=NOW, scope=s)
        self.rejected(lambda: pipeline.validate_registry([a, b]))

    def test_cross_game_repository_reuse_is_rejected(self):
        a = owner("game-one")
        s = scope("game-two"); s["repository"] = a["scope"]["repository"]
        b = pipeline.capture(idea_id="ORIGINAL_B", project_id="game-two", origin="OWNER",
                             original_text="Other game original words", source_ref="NOT_AVAILABLE",
                             captured_at=NOW, scope=s)
        self.rejected(lambda: pipeline.validate_registry([a, b]))

    def test_role_impersonation_and_permission_fields_are_rejected(self):
        for bad in (None, {}, {"repository": "fixture/game", "tasks": {}, "merge": True}):
            with self.subTest(bad=bad):
                self.rejected(lambda: pipeline.capture(idea_id="ORIGINAL", project_id="game-one",
                              origin="OWNER", original_text="Original words unchanged", source_ref="NOT_AVAILABLE",
                              captured_at=NOW, scope=bad))
        s=scope("game-one"); s["tasks"]["REVIEWER"]=s["tasks"]["META"]
        self.rejected(lambda: pipeline.capture(idea_id="ORIGINAL", project_id="game-one", origin="OWNER",
                      original_text="Original words unchanged", source_ref="NOT_AVAILABLE", captured_at=NOW, scope=s))

    def test_renamed_origin_is_preserved_as_distinct_canonical_type(self):
        self.assertEqual(owner()["origin"], "OWNER_ORIGINAL_IDEA")
        self.assertEqual(web()["origin"], "WEB_RESEARCH_IDEA")

    def test_rehashed_rewrite_cannot_replace_a_stored_original(self):
        old = owner()
        replacement = pipeline.capture(idea_id=old["idea_id"], project_id=old["project_id"],
                      origin="OWNER", original_text="AI rewriting the original to something else",
                      source_ref=old["source_ref"], captured_at=NOW, scope=old["scope"])
        pipeline.validate_record(replacement)  # Hash consistency alone is not authenticity.
        self.rejected(lambda: pipeline.merge_registry([old], [replacement]))

    def test_rehashed_reclassification_cannot_replace_owner_with_web(self):
        old=owner()
        replacement=web(idea=old["idea_id"])
        pipeline.validate_record(replacement)
        self.rejected(lambda: pipeline.merge_registry([old], [replacement]))

    def test_append_idempotence_and_inputs_not_mutated(self):
        old=owner(); before=deepcopy(old)
        after=pipeline.advance(old,"RESEARCHED",actor="META",occurred_at=NOW,reason="Dated research inspected")
        result=pipeline.merge_registry([old],[after])
        self.assertEqual(pipeline.merge_registry(result,[after]),result)
        self.assertEqual(old,before)
        result[0]["original_text"]="Changed copy"
        self.assertEqual(old,before)

    def test_duplicate_input_and_event_rewrite_cannot_erase_history(self):
        old=pipeline.advance(owner(),"RESEARCHED",actor="META",occurred_at=NOW,reason="Dated research inspected")
        changed=deepcopy(old);changed["events"][0]["reason"]="Replace the historical reason"
        pipeline.validate_record(changed)
        self.rejected(lambda:pipeline.merge_registry([old],[changed]))
        self.rejected(lambda:pipeline.merge_registry([old],[owner()]))
        self.rejected(lambda:pipeline.merge_registry([old],[old,old]))

    def test_failed_and_withdrawn_preserve_words_and_block_restart(self):
        for status in ("FAILED","WITHDRAWN","DEFERRED","REJECTED"):
            with self.subTest(status=status):
                original=owner()
                closed=pipeline.advance(original,status,actor="META",occurred_at=NOW,reason="Negative evidence retained")
                self.assertEqual(closed["original_text"],original["original_text"])
                self.rejected(lambda:pipeline.advance(closed,"RESEARCHED",actor="META",occurred_at=NOW,reason="Illegal restart of closed idea"))

    def test_required_common_stages_and_protected_evidence_boundary(self):
        row=owner()
        for stage in ("RESEARCHED","COMPARED","EXPERIMENT_DESIGNED"):
            row=pipeline.advance(row,stage,actor="META",occurred_at=NOW,reason="Actual planning evidence reviewed")
        self.rejected(lambda:pipeline.advance(row,"PROTOTYPE_PR",actor="provider=true",occurred_at=NOW,reason="Caller JSON claims success"))
        fake=deepcopy(row);fake["stage"]="MERGED_MAIN_QA"
        self.rejected(lambda:pipeline.validate_record(fake))

    def test_variant_duplicate_links_are_scoped_and_acyclic(self):
        root=owner()
        child=pipeline.capture(idea_id="VARIANT_A",project_id=root["project_id"],origin="DERIVED",
                              original_text="Distinct support tactic variant",source_ref="NOT_AVAILABLE",captured_at=NOW,
                              derived_from=[root["idea_id"]],variant_of=root["idea_id"],scope=root["scope"])
        self.assertEqual(pipeline.merge_registry([root],[child]),[root,child])
        a=deepcopy(child);a["duplicate_of"]="VARIANT_B";a["provenance_sha256"]=pipeline._provenance_hash(a)
        b=deepcopy(child);b["idea_id"]="VARIANT_B";b["duplicate_of"]="VARIANT_A";b["provenance_sha256"]=pipeline._provenance_hash(b)
        self.rejected(lambda:pipeline.validate_registry([root,a,b]))
        child["variant_of"]="FOREIGN_ID";child["provenance_sha256"]=pipeline._provenance_hash(child)
        self.rejected(lambda:pipeline.validate_registry([root,child]))

    def test_observation_facts_are_separate_from_hypotheses_and_source_class(self):
        row=web(); self.assertEqual(row["observations"][0]["source_kind"],"PRIMARY_OFFICIAL")
        for kind in ("COMMUNITY_REACTION","DEVELOPER_CASE","SECONDARY_REPORT","UNCLASSIFIED"):
            obs=deepcopy(row["observations"]);obs[0]["source_kind"]=kind
            captured=pipeline.capture(idea_id="WEB_SOURCE",project_id=row["project_id"],origin="WEB_RESEARCH",
                         original_text="Separate source report, not game effect",source_ref=row["source_ref"],captured_at=NOW,
                         observations=obs,scope=row["scope"])
            obs[0]["observed_fact"]="Changed external input"
            self.assertNotEqual(captured["observations"][0]["observed_fact"],obs[0]["observed_fact"])
        changed=deepcopy(row);changed["observations"][0]["observed_fact"]="Altered reported fact"
        self.rejected(lambda:pipeline.validate_record(changed))

    def test_system_ideas_and_game_ideas_use_separate_experiments(self):
        a=owner()
        b=pipeline.capture(idea_id="SYSTEM_ORIGINAL",project_id=a["project_id"],origin="OWNER",domain="SYSTEM",
                          original_text="Improve generic autonomous development",source_ref="NOT_AVAILABLE",captured_at=NOW,scope=a["scope"])
        pipeline.validate_registry([a,b])
        self.rejected(lambda:pipeline.assess_candidates(a["project_id"],[a,b],
                      [proposal("VARIANT_A",[a["idea_id"]]),proposal("VARIANT_B",[b["idea_id"]])]))
        result=pipeline.assess_candidates(a["project_id"],[a,b],
                      [proposal("VARIANT_A",[b["idea_id"]]),proposal("VARIANT_B",[b["idea_id"]])])
        self.assertEqual(result["domain"],"SYSTEM")

    def test_publication_date_precision_is_preserved_without_inventing_a_time(self):
        original=web()
        def capture_date(value):
            observations=deepcopy(original["observations"]);observations[0]["published_at"]=value
            return pipeline.capture(idea_id="WEB_DATED",project_id=original["project_id"],origin="WEB_RESEARCH",
                                    original_text="Dated source fact with limited precision",source_ref=original["source_ref"],
                                    captured_at=NOW,scope=original["scope"],observations=observations)
        self.assertEqual(capture_date("2026-10-24")["observations"][0]["published_at"],"2026-10-24")
        for invalid in ("2026-11-01", "2026-02-30", False):
            self.rejected(lambda:capture_date(invalid))

    def test_comparison_retains_unmeasured_metrics_and_no_grants(self):
        a=owner();p=[proposal("VARIANT_A",[a["idea_id"]]),proposal("VARIANT_B",[a["idea_id"]])]
        result=pipeline.assess_candidates(a["project_id"],[a],p)
        self.assertEqual(result["scope"],a["scope"])
        self.assertTrue(all(v=="NOT_MEASURED" for v in result["metric_status"].values()))
        self.assertEqual(result["player_status"],"NOT_MEASURED")
        self.assertEqual(result["engine_status"],"NOT_RUN")
        self.assertTrue(all(v is False for v in result["execution"].values()))
        self.assertNotIn("NORMALIZED",result["lifecycle"])

    def test_cli_reads_only_and_masks_invalid_input(self):
        a=owner();data={"project_id":a["project_id"],"ideas":[a],"proposals":[proposal("VARIANT_A",[a["idea_id"]]),proposal("VARIANT_B",[a["idea_id"]])]}
        stdout=io.StringIO()
        with patch("sys.stdin",io.StringIO(json.dumps(data))),patch("sys.stdout",stdout):
            self.assertEqual(pipeline.main(),0)
        self.assertFalse(json.loads(stdout.getvalue())["execution"]["write"])
        for raw in ('{"project_id":"x","project_id":"y"}', '{"token":"never-echo-this"}', 'NaN'):
            stdout=io.StringIO()
            with patch("sys.stdin",io.StringIO(raw)),patch("sys.stdout",stdout):
                self.assertEqual(pipeline.main(),2)
            self.assertNotIn("never-echo-this",stdout.getvalue())
            self.assertEqual(json.loads(stdout.getvalue())["error"],"INVALID_IDEA_INPUT")


if __name__ == "__main__":
    unittest.main()
