"""Offline-only regression for owner-origin idea preservation and proposal evaluation."""
import unittest
from copy import deepcopy

from tools.system_idea_pipeline import (capture, validate_record, validate_registry,
                                        advance, assess_candidates, IdeaValidationError)

NOW = "2026-10-28T12:00:00+00:00"
WORDS = "今の不満はキャラが3つしかないこと。子供は飽きる。ロブロックス見れば分かるけど、キャラの多さは命。レアキャラとかは課金に繋がる。闇雲に増やすのではなく、ゲーム構想にあったナイスキャラをまずは増やそう"

def owner(project="toy-wars-factory", idea="OWN20261028_CHARACTERS"):
    return capture(idea_id=idea, project_id=project, origin="OWNER",
                   original_text=WORDS, source_ref="NOT_AVAILABLE", captured_at=NOW)

def web(project="toy-wars-factory", idea="WEB20261028_DISCOVERY"):
    return capture(idea_id=idea, project_id=project, origin="WEB_RESEARCH",
                   original_text="Roblox Discovery highlights early bounce and return play days as important signals, but this does not prove any proposed character improves either.",
                   source_ref="https://create.roblox.com/docs/discovery", captured_at=NOW,
                   observations=[{"source_url":"https://create.roblox.com/docs/discovery", "checked_at":NOW,
                                  "observed_fact":"Discovery documentation describes return play and early bounce signals.",
                                  "limitation":"The document does not establish a causal impact for Toy Wars."}])

def proposal(pid, refs, score=4):
    return {"candidate_id":pid,"idea_refs":refs,
            "hypothesis":"Differentiated silhouettes will increase willingness to try varied unit tactics.",
            "test_plan":"Test distinctive models in headless combat then on a small unpublished Roblox scene.",
            "falsifier":"No improvement in experimental player comprehension or strategy after fair comparison.",
            "benefit":{"acquisition":score,"retention":score,"strategy":score,"originality":score},
            "effort":{"engineering":3,"qa":2,"performance":2},
            "confidence":1,"open_risks":["Roblox actual mobile FPS unmeasured"]}

class PipelineTests(unittest.TestCase):
    def assertRejected(self, call):
        with self.assertRaises(IdeaValidationError):
            call()

    def test_owner_original_exact_and_hash(self):
        row=owner()
        self.assertEqual(row["original_text"],WORDS)
        self.assertEqual(row["stage"],"CAPTURED")
        self.assertEqual(validate_record(row),row)

    def test_modifying_original_is_detected(self):
        row=owner();row["original_text"]+=" (rewritten)"
        self.assertRejected(lambda: validate_record(row))

    def test_origin_cannot_be_replaced(self):
        row=owner();row["origin"]="FAKE_ORIGIN"
        self.assertRejected(lambda: validate_record(row))
        row=owner();row["origin"]="DERIVED";row["derived_from"]=["OWN20261028_OTHER"]
        self.assertRejected(lambda: validate_record(row))

    def test_web_needs_real_dated_source(self):
        row=web();self.assertEqual(validate_record(row),row)
        row["observations"]=[]
        self.assertRejected(lambda: validate_record(row))

    def test_no_credentials_or_insecure_research_url(self):
        row=web();row["observations"][0]["source_url"]="http://unverified.example/a"
        self.assertRejected(lambda: validate_record(row))
        row=web();row["source_ref"]="https://user:password@example.com/"
        self.assertRejected(lambda: validate_record(row))

    def test_derived_ideas_must_link_to_originals(self):
        def child(parents=None):
            return capture(idea_id="MIX20261028_CHILD",project_id="toy-wars-factory",origin="DERIVED",
                    original_text="Owner idea with AI-derived variation as a testable option",
                    source_ref="NOT_AVAILABLE",captured_at=NOW, derived_from=parents)
        self.assertRejected(lambda:child())
        row=child(["OWN20261028_CHARACTERS"])
        self.assertEqual(validate_record(row),row)

    def test_event_sequence_cannot_run_backwards(self):
        row=advance(owner(),"NORMALIZED",actor="META",occurred_at=NOW,reason="Plan candidate for test")
        row["events"][0]["occurred_at"]="2026-10-27T12:00:00+00:00"
        self.assertRejected(lambda:validate_record(row))

    def test_stage_chain_keeps_raw_idea(self):
        original=owner()
        normalized=advance(original,"NORMALIZED",actor="META",occurred_at=NOW,reason="Detail distinct toy silhouettes")
        self.assertEqual(original["stage"],"CAPTURED")
        self.assertEqual(normalized["original_text"],WORDS)
        self.assertEqual(normalized["events"][0]["to"],"NORMALIZED")

    def test_no_skipping(self):
        self.assertRejected(lambda: advance(owner(),"COMPARED",actor="META",occurred_at=NOW,reason="Skip research"))

    def test_unauthenticated_merge_not_authorized(self):
        for stage in ("PROTOTYPE_PR","OFFLINE_VERIFIED","INDEPENDENT_APPROVED",
                      "MERGED_MAIN_QA","ENGINE_VERIFIED","PLAYER_MEASURED","ADOPTED"):
            with self.subTest(stage=stage):
                self.assertRejected(lambda: advance(owner(),stage,actor="META",occurred_at=NOW,reason="Claimed success from an unverified JSON"))

    def test_archive_keeps_idea_provenance(self):
        row=advance(owner(),"DEFERRED",actor="META",occurred_at=NOW,reason="Current engine remains unverified")
        self.assertEqual(row["original_text"],WORDS)
        self.assertEqual(row["events"][0]["reason"],"Current engine remains unverified")

    def test_duplicate_and_cross_project_ids(self):
        self.assertRejected(lambda:validate_registry([owner(),owner()]))
        row=owner("different-game", "OWN20261028_SECOND")
        row["derived_from"]=["OWN20261028_CHARACTERS"]
        self.assertRejected(lambda:validate_registry([owner(),row]))

    def test_derivation_requires_parent(self):
        row=owner(idea="OWN20261028_CHILD")
        row["derived_from"]=["OWN20261028_CHARACTERS"]
        validate_registry([owner(),row])
        self.assertRejected(lambda:validate_registry([row]))

    def test_requires_two_alternatives(self):
        self.assertRejected(lambda:assess_candidates("toy-wars-factory",[owner()],[proposal("CUREBO",["OWN20261028_CHARACTERS"])]))

    def test_ranking_heuristic_is_not_market_effect(self):
        items=[owner(),web()]
        p1=proposal("CUREBO",[items[0]["idea_id"],items[1]["idea_id"]])
        p2=proposal("KURURIN",[items[0]["idea_id"]],score=3)
        ranked=assess_candidates("toy-wars-factory",items,[p1,p2])
        self.assertEqual(ranked["ranking"][0]["candidate_id"],"CUREBO")
        self.assertEqual(ranked["ranking"][0]["measured_effect"],"NOT_MEASURED")
        self.assertFalse(ranked["execution"]["dispatch"])
        self.assertFalse(ranked["execution"]["merge"])
        self.assertEqual(ranked["baseline"]["candidate_id"],"NO_CHANGE")

    def test_forged_cross_game_candidate_rejected(self):
        items=[owner(),owner("another-game", "OWN20261028_OTHER")]
        c1=proposal("CUREBO",["OWN20261028_CHARACTERS"])
        c2=proposal("KURURIN",["OWN20261028_OTHER"])
        self.assertRejected(lambda:assess_candidates("toy-wars-factory",items,[c1,c2]))

    def test_nan_and_negative_scorings_rejected(self):
        p1=proposal("CUREBO",["OWN20261028_CHARACTERS"])
        p2=proposal("KURURIN",["OWN20261028_CHARACTERS"])
        p2["effort"]["qa"]=-1
        self.assertRejected(lambda:assess_candidates("toy-wars-factory",[owner()],[p1,p2]))
        p2["effort"]["qa"]=float("nan")
        self.assertRejected(lambda:assess_candidates("toy-wars-factory",[owner()],[p1,p2]))

    def test_immutable_history_ledger_detects_tamper(self):
        row=advance(owner(),"NORMALIZED",actor="META",occurred_at=NOW,reason="Define strategy and role")
        fake=deepcopy(row);fake["events"][0]["from"]="RESEARCHED"
        self.assertRejected(lambda:validate_record(fake))

    def test_provenance_rejects_two_node_cycle(self):
        a=capture(idea_id="DERA",project_id="toy-wars-factory",origin="DERIVED",
                  original_text="Derived from B",source_ref="NOT_AVAILABLE",captured_at=NOW,derived_from=["DERB"])
        b=capture(idea_id="DERB",project_id="toy-wars-factory",origin="DERIVED",
                  original_text="Derived from A",source_ref="NOT_AVAILABLE",captured_at=NOW,derived_from=["DERA"])
        self.assertRejected(lambda:validate_registry([a,b]))

    def test_provenance_rejects_three_node_cycle_with_owner_root(self):
        a=capture(idea_id="DERA",project_id="toy-wars-factory",origin="DERIVED",
                  original_text="One parent is a source, another a cycle",source_ref="NOT_AVAILABLE",
                  captured_at=NOW,derived_from=["OWN20261028_CHARACTERS","DERC"])
        b=capture(idea_id="DERB",project_id="toy-wars-factory",origin="DERIVED",
                  original_text="Derived from A",source_ref="NOT_AVAILABLE",captured_at=NOW,derived_from=["DERA"])
        c=capture(idea_id="DERC",project_id="toy-wars-factory",origin="DERIVED",
                  original_text="Derived from B",source_ref="NOT_AVAILABLE",captured_at=NOW,derived_from=["DERB"])
        self.assertRejected(lambda:validate_registry([owner(),a,b,c]))

    def test_provenance_diamond_and_long_chain_work_without_recursion(self):
        one=owner()
        two=web()
        children=[
            capture(idea_id="DERA",project_id="toy-wars-factory",origin="DERIVED",
                    original_text="Owner derived path",source_ref="NOT_AVAILABLE",
                    captured_at=NOW,derived_from=[one["idea_id"]]),
            capture(idea_id="DERB",project_id="toy-wars-factory",origin="DERIVED",
                    original_text="Web derived path",source_ref="NOT_AVAILABLE",
                    captured_at=NOW,derived_from=[two["idea_id"]]),
        ]
        joined=capture(idea_id="DERC",project_id="toy-wars-factory",origin="DERIVED",
                       original_text="Merged owner and web branches",source_ref="NOT_AVAILABLE",
                       captured_at=NOW,derived_from=["DERA","DERB"])
        chain=[one,two]+children+[joined]
        parent=joined["idea_id"]
        for idx in range(250):
            idea_id="DER%04d" % idx
            chain.append(capture(idea_id=idea_id,project_id="toy-wars-factory",
                                 origin="DERIVED",original_text="Deep chain #%d"%idx,
                                 source_ref="NOT_AVAILABLE",captured_at=NOW,
                                 derived_from=[parent]))
            parent=idea_id
        self.assertEqual(validate_registry(chain),chain)

    def test_provenance_rejects_impossible_parent_timestamp(self):
        child=capture(idea_id="DERA",project_id="toy-wars-factory",origin="DERIVED",
                      original_text="A derived candidate before its source",source_ref="NOT_AVAILABLE",
                      captured_at="2026-10-27T12:00:00+00:00",
                      derived_from=["OWN20261028_CHARACTERS"])
        self.assertRejected(lambda:validate_registry([owner(),child]))

    def test_baseline_id_is_reserved_for_no_change(self):
        p1=proposal("NO_CHANGE",["OWN20261028_CHARACTERS"])
        p2=proposal("KURURIN",["OWN20261028_CHARACTERS"])
        self.assertRejected(lambda:assess_candidates("toy-wars-factory",[owner()],[p1,p2]))

    def test_duplicate_candidates_rejected(self):
        c=proposal("CUREBO",["OWN20261028_CHARACTERS"])
        self.assertRejected(lambda:assess_candidates("toy-wars-factory",[owner()],[c,c]))

if __name__ == "__main__":
    unittest.main()
