import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from p0d_two_lane_queue import (manifest, choose_latest, OFFICIAL, REPO,
                                RUN_NAME, REAL69_ARTIFACT, ART15_PR,
                                ART15_FEATURE, ART15_SOURCE_LOCK,
                                ART15_RUN_NAME, ART15_ARTIFACT)

OLD="a"*40
NEW="b"*40
NEWER="c"*40

def pr(n,head=NEW,features="WCS_NEW",updated="2026-11-14T00:10:00Z",draft=False,label=True,base=OLD):
    return {"number":n,"state":"open","draft":draft,"title":"new scene", "updated_at":updated,
            "labels":[{"name":"p0d-prep-ready"}] if label else [],
            "base":{"ref":OFFICIAL,"sha":base}, "head":{"sha":head,"repo":{"full_name":REPO}},
            "body":"\n".join(["P0D_PREP_READY_V1",f"PINNED_HEAD: {head}",f"BASE_RC: {base}",
                      f"FEATURE_IDS: {features}","SOURCE_LOCK: rc_fastlane/SOURCE_LOCK.json",
                      "ROLLBACK: Disable independent feature flags and rebuild source exact",
                      "OWNER_FAST_ADMISSION_V2", "DECISION: ADOPT",
                      "DESIGN_SOURCE: https://github.com/kk051780/toy-wars-factory/issues/219",
                      "QUALITY_EVIDENCE: https://github.com/kk051780/toy-wars-factory/issues/470",
                      "VALUE_DELTA: Improve first-minute clarity and make egg-stealing wins more exciting"])}

def api(path):
    if "/commits/" in path:
        sha=path.rsplit("/",1)[1]
        stamp="2026-11-14T00:20:00Z" if sha==NEWER else "2026-11-14T00:10:00Z"
        return {"commit":{"committer":{"date":stamp}}}
    if "/compare/" in path:return {"status":"ahead","ahead_by":1,"behind_by":0}
    if "/actions/runs?" in path:
        sha=path.split("head_sha=")[1].split("&")[0]
        return {"workflow_runs":[{"head_sha":sha,"name":RUN_NAME,"status":"completed",
             "conclusion":"success","event":"pull_request","id":99,"created_at":"2026-11-14T00:10:30Z"}]}
    if "/actions/runs/99/artifacts?" in path:
        return {"artifacts":[{"id":900,"name":REAL69_ARTIFACT,"expired":False,"size_in_bytes":1935000}]}
    raise AssertionError("unexpected " + path)

class TwoLaneQueueTests(unittest.TestCase):
    def test_valid_ready(self):
        d=choose_latest(OLD,[pr(400)],api)
        self.assertEqual(d["ready_count"],1)
        self.assertTrue(d["no_auto_merge"])
        self.assertEqual(d["selected"][0]["head"],NEW)
        self.assertEqual(d["selected"][0]["candidate_artifact_zip_bytes"],1935000)
        self.assertEqual(d["selected"][0]["candidate_artifact_id"],900)
    def test_only_opted_in_and_non_draft(self):
        bare=pr(400,label=False)
        bare["body"]="Not yet ready"
        d=choose_latest(OLD,[bare,pr(401,draft=True)],api)
        self.assertEqual(d["ready_count"],0)
    def test_stale_manifest_is_not_approved(self):
        x=pr(402)
        x["head"]["sha"]=NEWER
        d=choose_latest(OLD,[x],api)
        self.assertEqual(d["ready_count"],0)
        self.assertEqual(d["all_labeled_candidates"][0]["reason"],"STALE_PREP_MANIFEST_SHA")
    def test_stale_base_is_not_approved(self):
        d=choose_latest(OLD,[pr(403,base=NEW)],api)
        self.assertEqual(d["ready_count"],0)
    def test_latest_success_only_and_exact_head(self):
        def failed(path):
            if "/compare/" in path:return {"status":"ahead","ahead_by":1,"behind_by":0}
            return {"workflow_runs":[
                {"head_sha":NEW,"name":RUN_NAME,"status":"completed","conclusion":"failure","event":"pull_request","id":100,"created_at":"2026-11-14T00:11:30Z"},
                {"head_sha":NEW,"name":RUN_NAME,"status":"completed","conclusion":"success","event":"pull_request","id":99,"created_at":"2026-11-14T00:10:30Z"}]}
        d=choose_latest(OLD,[pr(404)],failed)
        self.assertEqual(d["ready_count"],0)
        self.assertEqual(d["all_labeled_candidates"][0]["reason"],"LATEST_SAME_HEAD_FULL_RC_CI_NOT_GREEN")
    def test_not_fast_forward_rejected(self):
        def divergent(path):
            if "/compare/" in path:return {"status":"diverged","ahead_by":2,"behind_by":1}
            return api(path)
        d=choose_latest(OLD,[pr(405)],divergent)
        self.assertEqual(d["ready_count"],0)
    def test_latest_per_feature_dedup(self):
        x=pr(406,head=NEW,updated="2026-11-14T00:00:00Z")
        y=pr(407,head=NEWER,updated="2026-11-14T00:20:00Z")
        d=choose_latest(OLD,[x,y],api)
        self.assertEqual(d["ready_count"],1)
        self.assertEqual(d["selected"][0]["pr"],407)
        self.assertEqual(next(x for x in d["all_labeled_candidates"] if x["pr"]==406)["status"],"SUPERSEDED_SAME_FEATURE")
    def test_parallel_independent_features(self):
        d=choose_latest(OLD,[pr(408,features="SEA_BIOME"),pr(409,head=NEWER,features="PVE_CAPTURE")],api)
        self.assertEqual(d["ready_count"],2)
    def test_newest_source_commit_not_newest_pr_edit(self):
        old=pr(417,head=NEW,updated="2026-11-14T00:40:00Z")
        newest=pr(418,head=NEWER,updated="2026-11-14T00:10:00Z")
        d=choose_latest(OLD,[old,newest],api)
        self.assertEqual(d["ready_count"],1)
        self.assertEqual(d["selected"][0]["head"],NEWER)
    def test_multifeature_cumulative_not_double_adopted(self):
        d=choose_latest(OLD,[pr(410,features="SEA_BIOME,PVE_CAPTURE"),
                             pr(411,head=NEWER,features="PVE_CAPTURE",updated="2026-11-14T00:30:00Z")],api)
        self.assertEqual(d["ready_count"],1)
    def test_manifest_duplicate_or_traversal_rejected(self):
        x=pr(412)
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            manifest(x["body"]+"\nPINNED_HEAD: "+NEW)
        with self.assertRaisesRegex(ValueError,"INVALID_SOURCE_LOCK"):
            manifest(x["body"].replace("rc_fastlane/SOURCE_LOCK.json","../bad.json"))
    def test_v2_quality_design_value_and_decision_required(self):
        original=pr(419)
        for token, reason in (
            ("OWNER_FAST_ADMISSION_V2", "MISSING_UNIQUE_OWNER_FAST_ADMISSION_V2"),
            ("DECISION: ADOPT", "MISSING_FIELDS_DECISION"),
            ("QUALITY_EVIDENCE: https://github.com/kk051780/toy-wars-factory/issues/470",
             "MISSING_FIELDS_QUALITY_EVIDENCE"),
        ):
            candidate=dict(original)
            candidate["body"]=original["body"].replace(token, "")
            got=choose_latest(OLD,[candidate],api)
            self.assertEqual(got["ready_count"],0)
            self.assertIn(reason,got["all_labeled_candidates"][0]["reason"])
        no_value=pr(420)
        no_value["body"]=no_value["body"].replace("DECISION: ADOPT","DECISION: REWORK")
        got=choose_latest(OLD,[no_value],api)
        self.assertEqual(got["all_labeled_candidates"][0]["reason"],"NOT_ADOPT_DECISION")
        bogus=pr(421)
        bogus["body"]=bogus["body"].replace(
            "https://github.com/kk051780/toy-wars-factory/issues/470",
            "https://example.com/fake")
        got=choose_latest(OLD,[bogus],api)
        self.assertIn("INVALID_QUALITY_EVIDENCE_URL",got["all_labeled_candidates"][0]["reason"])
    def test_v2_quality_fields_propagate_to_selected(self):
        got=choose_latest(OLD,[pr(422)],api)
        selected=got["selected"][0]
        self.assertEqual(selected["decision"],"ADOPT")
        self.assertIn("/issues/470",selected["quality_evidence"])
        self.assertIn("egg-stealing",selected["value_delta"])

    def test_reject_green_rich51_without_real69_composite(self):
        def legacy_only(path):
            if "/actions/runs?" in path:
                return {"workflow_runs":[{"head_sha":NEW,"name":"P0D canonical RC fast-lane Studio build",
                                          "event":"pull_request","status":"completed","conclusion":"success",
                                          "id":98,"created_at":"2026-11-14T00:10:30Z"}]}
            return api(path)
        d=choose_latest(OLD,[pr(423)],legacy_only)
        self.assertEqual(d["ready_count"],0)
        self.assertEqual(d["all_labeled_candidates"][0]["reason"],"LATEST_SAME_HEAD_FULL_RC_CI_NOT_GREEN")

    def test_reject_real69_green_but_missing_or_bad_artifact(self):
        def artifact_replaced(payload):
            def g(path):
                if "/actions/runs/99/artifacts?" in path:return {"artifacts":payload}
                return api(path)
            return g
        for artifacts in ([],[{"id":900,"name":REAL69_ARTIFACT,"expired":True,"size_in_bytes":1935000}],
                          [{"id":900,"name":REAL69_ARTIFACT,"expired":False,"size_in_bytes":0}],
                          [{"id":900,"name":REAL69_ARTIFACT,"expired":False,"size_in_bytes":1935000},
                           {"id":901,"name":REAL69_ARTIFACT,"expired":False,"size_in_bytes":1935000}]):
            d=choose_latest(OLD,[pr(424)],artifact_replaced(artifacts))
            self.assertEqual(d["ready_count"],0)
            self.assertEqual(d["all_labeled_candidates"][0]["reason"],"REAL69_CANDIDATE_ARTIFACT_MISSING_OR_DUPLICATE")

    def test_official_head_recheck_at_selection(self):
        d=choose_latest(NEW,[pr(413,base=OLD)],api)
        self.assertEqual(d["ready_count"],0)
    def test_fail_if_invalid_official_sha(self):
        with self.assertRaises(ValueError):choose_latest("missing",[pr(414)],api)


class Art15SourcePacketAdmissionTests(unittest.TestCase):
    """Review-only #966 source packet must never count as official adoption."""
    def art15(self, n=ART15_PR, feat=ART15_FEATURE):
        candidate = pr(n, features=feat)
        candidate["body"] = candidate["body"].replace(
            "rc_fastlane/SOURCE_LOCK.json", ART15_SOURCE_LOCK)
        return candidate

    def art15_api(self, path, runs=None, artifacts=None):
        if "/actions/runs?head_sha=" in path:
            if runs is not None:
                return {"workflow_runs": runs}
            return {"workflow_runs": [{
                "head_sha": NEW, "name": ART15_RUN_NAME, "event": "pull_request",
                "status": "completed", "conclusion": "success",
                "id": 966, "created_at": "2026-11-21T01:10:00Z",
            }]}
        if "/actions/runs/966/artifacts?" in path:
            if artifacts is not None:
                return {"artifacts": artifacts}
            return {"artifacts": [{
                "id": 14682237123, "name": ART15_ARTIFACT,
                "size_in_bytes": 866308, "expired": False,
            }]}
        return api(path)

    def test_known_art15_source_packet_is_ready_only_for_b220_review(self):
        d = choose_latest(OLD, [self.art15()], self.art15_api)
        self.assertEqual(d["ready_count"], 1)
        selected = d["selected"][0]
        self.assertEqual(selected["pr"], 966)
        self.assertEqual(selected["candidate_evidence_kind"],
                         "ART15_SOURCE_ONLY_NOT_FORMAL")
        self.assertEqual(selected["candidate_artifact_id"], 14682237123)
        self.assertEqual(selected["candidate_artifact_zip_bytes"], 866308)
        self.assertEqual(selected["status"], "READY_FOR_SOLE_WRITER_REVIEW")
        self.assertTrue(d["no_auto_merge"])
        self.assertTrue(d["studio_and_fun_not_inferred"])
        self.assertEqual(d["next_owner"],
                         "SOLE_AUTHENTICATED_ISSUE_220_INTEGRATOR_CAS_ONLY")

    def test_other_pr_cannot_borrow_art15_workflow(self):
        d = choose_latest(OLD, [self.art15(n=969)], self.art15_api)
        self.assertEqual(d["ready_count"], 0)
        self.assertEqual(d["all_labeled_candidates"][0]["reason"],
                         "LATEST_SAME_HEAD_FULL_RC_CI_NOT_GREEN")

    def test_art15_feature_and_source_lock_cannot_be_swapped(self):
        for candidate in (
            self.art15(feat="FAKE_ART_BRIDGE"),
            self.art15(),
        ):
            if ART15_FEATURE in candidate["body"]:
                candidate["body"] = candidate["body"].replace(
                    ART15_SOURCE_LOCK, "source_packets/other.json")
            d = choose_latest(OLD, [candidate], self.art15_api)
            self.assertEqual(d["ready_count"], 0)
            self.assertEqual(d["all_labeled_candidates"][0]["reason"],
                             "ART15_CONTRACT_IDENTITY_MISMATCH")

    def test_art15_expired_missing_or_duplicate_packet_fails_closed(self):
        good = {"id": 14682237123, "name": ART15_ARTIFACT,
                "size_in_bytes": 866308, "expired": False}
        for entries in ([], [{**good, "expired": True}],
                        [{**good, "size_in_bytes": 0}], [good, good],
                        [{**good, "name": REAL69_ARTIFACT}]):
            d = choose_latest(OLD, [self.art15()],
                              lambda path: self.art15_api(
                                  path, artifacts=entries))
            self.assertEqual(d["ready_count"], 0)
            self.assertEqual(d["all_labeled_candidates"][0]["reason"],
                             "REAL69_CANDIDATE_ARTIFACT_MISSING_OR_DUPLICATE")

    def test_art15_same_head_latest_failure_rejects_older_success(self):
        runs = [
            {"head_sha": NEW, "name": ART15_RUN_NAME,
             "event": "pull_request", "status": "completed",
             "conclusion": "failure", "id": 967,
             "created_at": "2026-11-21T01:20:00Z"},
            {"head_sha": NEW, "name": ART15_RUN_NAME,
             "event": "pull_request", "status": "completed",
             "conclusion": "success", "id": 966,
             "created_at": "2026-11-21T01:10:00Z"},
        ]
        d = choose_latest(OLD, [self.art15()],
                          lambda path: self.art15_api(path, runs=runs))
        self.assertEqual(d["ready_count"], 0)
        self.assertEqual(d["all_labeled_candidates"][0]["reason"],
                         "LATEST_SAME_HEAD_FULL_RC_CI_NOT_GREEN")

    def test_art15_wrong_head_and_non_ff_fail(self):
        wrong = self.art15()
        wrong["head"]["sha"] = NEWER
        d = choose_latest(OLD, [wrong], self.art15_api)
        self.assertEqual(d["ready_count"], 0)
        self.assertEqual(d["all_labeled_candidates"][0]["reason"],
                         "STALE_PREP_MANIFEST_SHA")
        def diverged(path):
            if "/compare/" in path:
                return {"status": "diverged", "ahead_by": 1, "behind_by": 1}
            return self.art15_api(path)
        d = choose_latest(OLD, [self.art15()], diverged)
        self.assertEqual(d["ready_count"], 0)
        self.assertEqual(d["all_labeled_candidates"][0]["reason"],
                         "NOT_A_FAST_FORWARD_FROM_OFFICIAL")


if __name__=="__main__": unittest.main()
