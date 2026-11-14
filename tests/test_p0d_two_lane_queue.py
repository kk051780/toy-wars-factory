import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from p0d_two_lane_queue import manifest, choose_latest, OFFICIAL, REPO, RUN_NAME

OLD="a"*40
NEW="b"*40
NEWER="c"*40

def pr(n,head=NEW,features="WCS_NEW",updated="2026-11-14T00:10:00Z",draft=False,label=True,base=OLD):
    return {"number":n,"state":"open","draft":draft,"title":"new scene", "updated_at":updated,
            "labels":[{"name":"p0d-prep-ready"}] if label else [],
            "base":{"ref":OFFICIAL,"sha":base}, "head":{"sha":head,"repo":{"full_name":REPO}},
            "body":"\n".join(["P0D_PREP_READY_V1",f"PINNED_HEAD: {head}",f"BASE_RC: {base}",
                      f"FEATURE_IDS: {features}","SOURCE_LOCK: rc_fastlane/SOURCE_LOCK.json",
                      "ROLLBACK: Disable independent feature flags and rebuild source exact"])}

def api(path):
    if "/commits/" in path:
        sha=path.rsplit("/",1)[1]
        stamp="2026-11-14T00:20:00Z" if sha==NEWER else "2026-11-14T00:10:00Z"
        return {"commit":{"committer":{"date":stamp}}}
    if "/compare/" in path:return {"status":"ahead","ahead_by":1,"behind_by":0}
    if "/actions/runs?" in path:
        sha=path.split("head_sha=")[1].split("&")[0]
        return {"workflow_runs":[{"head_sha":sha,"name":RUN_NAME,"status":"completed",
             "conclusion":"success","id":99,"created_at":"2026-11-14T00:10:30Z"}]}
    raise AssertionError("unexpected " + path)

class TwoLaneQueueTests(unittest.TestCase):
    def test_valid_ready(self):
        d=choose_latest(OLD,[pr(400)],api)
        self.assertEqual(d["ready_count"],1)
        self.assertTrue(d["no_auto_merge"])
        self.assertEqual(d["selected"][0]["head"],NEW)
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
                {"head_sha":NEW,"name":RUN_NAME,"status":"completed","conclusion":"failure","id":100,"created_at":"2026-11-14T00:11:30Z"},
                {"head_sha":NEW,"name":RUN_NAME,"status":"completed","conclusion":"success","id":99,"created_at":"2026-11-14T00:10:30Z"}]}
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
    def test_official_head_recheck_at_selection(self):
        d=choose_latest(NEW,[pr(413,base=OLD)],api)
        self.assertEqual(d["ready_count"],0)
    def test_fail_if_invalid_official_sha(self):
        with self.assertRaises(ValueError):choose_latest("missing",[pr(414)],api)

if __name__=="__main__": unittest.main()
