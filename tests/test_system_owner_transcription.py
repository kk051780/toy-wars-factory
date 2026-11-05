"""Regression for PR112's real misclassified checkpoint; API fixtures are synthetic.

Exact comment text can establish transcription equality, never chat authentication.
No provider calls, tokens, writes, scheduling or original-history rewriting.
"""
from copy import deepcopy
from hashlib import sha1
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import system_idea_pipeline as p
from tests.test_system_idea_pipeline import proposal, scope

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-10-28T21:50:06Z"
PROJECT = "toy-wars-factory"
REPO = scope(PROJECT)["repository"]
RAW = "このチャットではゲーム制作のキャラクター、ゲーム構造のブラッシュアップを進める。今の不満はキャラが3つしかないこと。子供は飽きる。ロブロックス見れば分かるけど、キャラの多さは命。レアキャラとかは課金に繋がる。闇雲に増やすのではなく、ゲーム構想にあったナイスキャラをまずは増やそう"
SUMMARY = "キャラ3体では飽きる。キャラを闇雲に増やさず構想に沿う差別化キャラを増やし、レアキャラの収集価値も検討する"

def comment(repo=REPO):
    return {"id":6481271808,"url":f"https://api.github.com/repos/{repo}/issues/comments/6481271808",
            "html_url":f"https://github.com/{repo}/issues/109#issuecomment-6481271808",
            "issue_url":f"https://api.github.com/repos/{repo}/issues/109",
            "created_at":"2026-10-28T21:36:21Z","updated_at":"2026-10-28T21:36:21Z",
            "body":"Transcription; original chat unavailable.\n\n> "+RAW+"\n\nDo not authenticate chat from this comment.",
            "author_association":"OWNER"}

def transcript(idea="OWNER_VERBATIM",repo=REPO):
    return p.transcription_from_comment(project_id=PROJECT,idea_id=idea,repository=repo,
                                        issue_number=109,comment=comment(repo),checked_at=NOW)

def owner(text=RAW,idea="OWNER_VERBATIM"):
    t=transcript(idea)
    return p.capture(idea_id=idea,project_id=PROJECT,origin="OWNER",original_text=text,
                     source_ref=t["source_ref"],captured_at=NOW,scope=scope(PROJECT))


class OwnerTranscriptionTests(unittest.TestCase):
    def rejected(self, fn):
        with self.assertRaises(p.IdeaValidationError):
            fn()

    def test_full_transcription_preserves_original_bytes_and_comment_link(self):
        t=transcript()
        self.assertEqual(t["original_text"].encode(),RAW.encode())
        self.assertEqual(t["comment_url"],comment()["html_url"])
        self.assertEqual(t["original_chat_url"],"NOT_AVAILABLE")
        result=p.verify_owner_transcriptions([owner()],[t])
        self.assertEqual(result["original_chat_authentication"],"NOT_VERIFIED")
        self.assertIn("NOT_AUTHENTICATION",result["basis"])

    def test_old_checkpoint_hash_passes_but_new_provenance_comparison_rejects_it(self):
        path=ROOT/"history/C00121_scoped_dual_idea_pipeline.json"
        data=path.read_bytes()
        self.assertEqual(sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest(),
                         "26aebd9badfc616e43cafc1a792669007e5387d1")
        rows=json.loads(data)["stock_checkpoint"]["records"]
        bad=next(r for r in rows if r["idea_id"]=="OWNER-20261028-CHARACTER-VARIETY")
        p.validate_record(bad)
        self.assertEqual(bad["original_text"],SUMMARY)
        self.rejected(lambda:p.verify_owner_transcriptions([bad],[transcript(bad["idea_id"],bad["scope"]["repository"])]))

    def test_summary_with_real_source_url_and_consistent_hash_is_still_not_original(self):
        bad=owner(SUMMARY)
        p.validate_record(bad)
        self.rejected(lambda:p.verify_owner_transcriptions([bad],[transcript()]))

    def test_omitting_first_sentence_is_not_verbatim_even_after_rehash(self):
        bad=owner(RAW.split("。",1)[1])
        p.validate_record(bad)
        self.rejected(lambda:p.verify_owner_transcriptions([bad],[transcript()]))

    def test_summary_is_separate_derived_record_with_original_parent(self):
        original=owner()
        summary=p.capture(idea_id="DERIVED_SUMMARY",project_id=PROJECT,origin="DERIVED",
                          original_text=SUMMARY,source_ref=transcript()["source_ref"],captured_at=NOW,
                          scope=scope(PROJECT),derived_from=[original["idea_id"]])
        p.validate_registry([original,summary])
        self.assertNotEqual(summary["idea_id"],original["idea_id"])
        self.assertEqual(summary["derived_from"],[original["idea_id"]])
        self.assertEqual(len(p.verify_owner_transcriptions([original,summary],[transcript()])["matched_active_records"]),1)

    def test_missing_duplicate_foreign_and_spoofed_transcriptions_fail_closed(self):
        good=transcript()
        for items in ([],[good,good],[transcript("OTHER_ORIGINAL")]):
            self.rejected(lambda:p.verify_owner_transcriptions([owner()],items))
        for key,value in (("repository","foreign/game"),("comment_id",6481271809),
                          ("project_id","other-game"),("original_chat_authentication","VERIFIED"),
                          ("original_chat_url","https://example.test/fake-chat"),("provider",True)):
            bad=deepcopy(good);bad[key]=value
            with self.subTest(key=key):
                self.rejected(lambda:p.verify_owner_transcriptions([owner()],[bad]))

    def test_ambiguous_missing_or_wrong_issue_comment_is_rejected(self):
        for key,value in (("body","No quoted transcription"),("body","> first quote\n\n> second quote"),
                          ("issue_url",f"https://api.github.com/repos/{REPO}/issues/110"),
                          ("html_url",f"https://github.com/foreign/game/issues/109#issuecomment-6481271808"),
                          ("updated_at","2026-10-29T21:36:21Z"),("id",True)):
            bad=comment();bad[key]=value
            with self.subTest(key=key):
                self.rejected(lambda:p.transcription_from_comment(project_id=PROJECT,idea_id="OWNER_VERBATIM",
                              repository=REPO,issue_number=109,comment=bad,checked_at=NOW))

    def test_comment_author_labels_are_never_chat_authentication(self):
        c=comment();c["provider_verified"]=True;c["owner_authenticated"]=True
        t=p.transcription_from_comment(project_id=PROJECT,idea_id="OWNER_VERBATIM",repository=REPO,
                                       issue_number=109,comment=c,checked_at=NOW)
        self.assertEqual(t["original_chat_authentication"],"NOT_VERIFIED")
        self.assertNotIn("provider_verified",t)

    def test_withdrawn_wrong_owner_is_retained_but_not_a_provenance_match(self):
        bad=owner(SUMMARY,"OWNER_REJECTED")
        closed=p.advance(bad,"WITHDRAWN",actor="META_REPAIR",occurred_at=NOW,reason="AI summary mislabeled as original")
        rows=p.merge_registry([bad],[closed,owner()])
        result=p.verify_owner_transcriptions(rows,[transcript()])
        self.assertEqual(result["archived_unverified_owner_ids"],["OWNER_REJECTED"])
        self.assertEqual(rows[0]["original_text"],SUMMARY)
        self.assertEqual(bad["stage"],"CAPTURED")

    def test_candidate_cannot_use_archived_original_or_its_descendant(self):
        original=owner()
        closed=p.advance(original,"WITHDRAWN",actor="META_REPAIR",occurred_at=NOW,reason="Provenance rejected by independent review")
        child=p.capture(idea_id="DERIVED_BAD_PARENT",project_id=PROJECT,origin="DERIVED",original_text="Candidate using withdrawn provenance",
                        source_ref="NOT_AVAILABLE",captured_at=NOW,scope=scope(PROJECT),derived_from=[original["idea_id"]])
        for ref in (closed["idea_id"],child["idea_id"]):
            proposals=[proposal("VARIANT_A",[ref]),proposal("VARIANT_B",[ref])]
            with self.assertRaisesRegex(p.IdeaValidationError,"archived"):
                p.assess_candidates(PROJECT,[closed,child],proposals)

    def test_comparison_without_transcript_explicitly_remains_unverified(self):
        r=owner();proposals=[proposal("VARIANT_A",[r["idea_id"]]),proposal("VARIANT_B",[r["idea_id"]])]
        out=p.assess_candidates(PROJECT,[r],proposals)
        self.assertEqual(out["owner_source_provenance"]["basis"],"NOT_VERIFIED")
        out=p.assess_candidates(PROJECT,[r],proposals,owner_transcriptions=[transcript()])
        self.assertEqual(out["owner_source_provenance"]["original_chat_authentication"],"NOT_VERIFIED")
        self.assertTrue(all(v is False for v in out["execution"].values()))

    def test_cli_rejects_hash_consistent_paraphrase_with_transcript(self):
        for text,expected in ((RAW,0),(SUMMARY,2)):
            r=owner(text);data={"project_id":PROJECT,"ideas":[r],"owner_transcriptions":[transcript()],
                "proposals":[proposal("VARIANT_A",[r["idea_id"]]),proposal("VARIANT_B",[r["idea_id"]])]}
            output=io.StringIO()
            with patch("sys.stdin",io.StringIO(json.dumps(data))),patch("sys.stdout",output):
                self.assertEqual(p.main(),expected)
            parsed=json.loads(output.getvalue())
            if expected:
                self.assertEqual(parsed["error"],"INVALID_IDEA_INPUT")
                self.assertNotIn(SUMMARY,output.getvalue())
            else:
                self.assertEqual(parsed["owner_source_provenance"]["original_chat_authentication"],"NOT_VERIFIED")


    def test_append_only_repair_checkpoint_has_exact_original_and_derived_summary(self):
        old=json.loads((ROOT/"history/C00121_scoped_dual_idea_pipeline.json").read_text())["stock_checkpoint"]
        current=json.loads((ROOT/"history/C00122_owner_verbatim_review_repair.json").read_text())["stock_checkpoint"]
        rows=current["records"]
        raw=next(r for r in rows if r["idea_id"]=="OWNER-20261028-CHARACTER-VERBATIM")
        summary=next(r for r in rows if r["idea_id"]=="MIX-20261029-CHARACTER-SUMMARY")
        rejected=next(r for r in rows if r["idea_id"]=="OWNER-20261028-CHARACTER-VARIETY")
        self.assertEqual(raw["original_text"],RAW)
        self.assertEqual(raw["origin"],"OWNER_ORIGINAL_IDEA")
        self.assertEqual(summary["original_text"],SUMMARY)
        self.assertEqual(summary["origin"],"DERIVED")
        self.assertEqual(summary["derived_from"],[raw["idea_id"]])
        self.assertEqual(rejected["stage"],"WITHDRAWN")
        for row in old["records"]:
            if row["origin"]=="WEB_RESEARCH_IDEA" or row["idea_id"]=="OWNER-20261028-DUAL-EVOLUTION":
                self.assertEqual(next(r for r in rows if r["idea_id"]==row["idea_id"]),row)
        result=p.verify_owner_transcriptions(rows,current["owner_transcriptions"])
        self.assertEqual(result["original_chat_authentication"],"NOT_VERIFIED")
        self.assertEqual(len(result["matched_active_records"]),2)
        self.assertIn(rejected["idea_id"],result["archived_unverified_owner_ids"])
        for domain,proposals in current["proposals"].items():
            out=p.assess_candidates(PROJECT,rows,proposals,owner_transcriptions=current["owner_transcriptions"])
            self.assertEqual(out["domain"],domain)
            self.assertTrue(all(v is False for v in out["execution"].values()))


if __name__=="__main__":
    unittest.main()
