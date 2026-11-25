import unittest
from guard import evaluate, SCHEMA

A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40
E = "e" * 40
NOW = "2026-11-15T01:30:00Z"


def sample():
    p = "rc_fastlane/features/castle/Art.luau"
    registry = dict(schema=SCHEMA, release_branch="rc/p0d-s1-kids-rc01", grants=[
        dict(feature_id="FB015_CASTLE", actor="writer-one", status="GRANTED", expires_at="2026-11-15T10:00:00Z", allowed_paths=["rc_fastlane/features/castle"], exclusive_groups=["area:castle"]),
        dict(feature_id="FB015_FOREST", actor="writer-two", status="GRANTED", expires_at="2026-11-15T10:00:00Z", allowed_paths=["rc_fastlane/features/forest"], exclusive_groups=["area:forest"]),
    ])
    candidate = dict(schema=SCHEMA, feature_id="FB015_CASTLE", actor="writer-one", base_head=A, proposed_parent_sha=A, proposed_commit_sha=B, changes=[dict(path=p, base_blob_sha=C, new_blob_sha=D)], validation=dict(commit_sha=B, conclusion="success", source_exact=True, source_lock=True, no_high_critical=True, unique_game_authority=True))
    current = dict(branch="rc/p0d-s1-kids-rc01", head_sha=A, file_blobs={p:C})
    return candidate, registry, current


def check(mod=None):
    a,b,c=sample()
    if mod: mod(a,b,c)
    return evaluate(a,b,c,"writer-one",NOW)


class TestGuard(unittest.TestCase):
    def test_good_solo(self): self.assertEqual(check()["status"], "STAGED_CAS_ELIGIBLE")
    def test_no_writer_self_grant(self): self.assertEqual(check(lambda a,b,c:b.update(grants=[]))["reason"], "GRANT_MISSING_OR_DUPLICATE")
    def test_actor_spoof(self): self.assertEqual(check(lambda a,b,c:a.update(actor="writer-two"))["reason"], "ACTOR_MISMATCH")
    def test_expired(self): self.assertEqual(check(lambda a,b,c:b["grants"][0].update(expires_at="2026-11-14T00:00:00Z"))["reason"], "GRANT_EXPIRED")
    def test_wrong_branch(self): self.assertEqual(check(lambda a,b,c:c.update(branch="main"))["reason"], "CURRENT_BRANCH_MISMATCH")
    def test_wrong_registry_branch(self): self.assertEqual(check(lambda a,b,c:b.update(release_branch="main"))["reason"], "BRANCH_NOT_ALLOWED")
    def test_wrong_ci_head(self): self.assertEqual(check(lambda a,b,c:a["validation"].update(commit_sha=A))["reason"], "CI_NOT_SAME_HEAD")
    def test_failed_ci(self): self.assertEqual(check(lambda a,b,c:a["validation"].update(conclusion="failure"))["reason"], "CI_NOT_GREEN")
    def test_source_not_exact(self): self.assertEqual(check(lambda a,b,c:a["validation"].update(source_exact=False))["reason"], "SOURCE_PROOF_MISSING")
    def test_major_vulnerability(self): self.assertEqual(check(lambda a,b,c:a["validation"].update(no_high_critical=False))["reason"], "SAFETY_QA_MISSING")
    def test_nonunique_game(self): self.assertEqual(check(lambda a,b,c:a["validation"].update(unique_game_authority=False))["reason"], "AUTHORITY_PROOF_MISSING")
    def test_modified_same_path(self): self.assertEqual(check(lambda a,b,c:c["file_blobs"].update({a["changes"][0]["path"]:E}))["reason"], "EDIT_CONFLICT_CHANGED_SINCE_BASE")
    def test_changed_head_other_path(self): self.assertEqual(check(lambda a,b,c:c.update(head_sha=E))["status"], "REBUILD_RETEST_REQUIRED")
    def test_changed_parent(self): self.assertEqual(check(lambda a,b,c:a.update(proposed_parent_sha=E))["status"], "REBUILD_RETEST_REQUIRED")
    def test_unauthorized_scope(self): self.assertEqual(check(lambda a,b,c:(a["changes"][0].update(path="src/server/HUD.client.luau"),c["file_blobs"].update({"src/server/HUD.client.luau":C})))["reason"], "UNGRANTED_PATH")
    def test_path_traversal(self): self.assertEqual(check(lambda a,b,c:a["changes"][0].update(path="../main"))["reason"], "PATH_TRAVERSAL")
    def test_edit_policy(self): self.assertEqual(check(lambda a,b,c:(b["grants"][0].update(allowed_paths=[".github"]),a["changes"][0].update(path=".github/workflows/x.yml"),c["file_blobs"].update({".github/workflows/x.yml":C})))["reason"], "FORBIDDEN_POLICY_EDIT")
    def test_duplicate_path_casefold(self): self.assertEqual(check(lambda a,b,c:(a["changes"].append(dict(path="rc_fastlane/features/castle/art.luau",base_blob_sha=C,new_blob_sha=E))))["reason"], "DUPLICATE_CHANGED_PATH")
    def test_overlapping_grant(self): self.assertEqual(check(lambda a,b,c:b["grants"][1].update(allowed_paths=["rc_fastlane/features"]))["reason"], "ACTIVE_PATH_CLAIM_OVERLAP")
    def test_shared_authority(self): self.assertEqual(check(lambda a,b,c:b["grants"][1].update(exclusive_groups=["area:castle"]))["reason"], "AUTHORITY_LEASE_OVERLAP")
    def test_duplicate_feature(self): self.assertEqual(check(lambda a,b,c:b["grants"][1].update(feature_id="FB015_CASTLE"))["reason"], "GRANT_MISSING_OR_DUPLICATE")
    def test_repeated_noop(self): self.assertEqual(check(lambda a,b,c:a["changes"][0].update(new_blob_sha=C))["reason"], "NOOP_CHANGE")
    def test_fake_new_path(self): self.assertEqual(check(lambda a,b,c:c.update(file_blobs={}))["reason"], "CURRENT_PATH_EVIDENCE_MISSING")
    def test_reserved_authority_needs_lease(self):
        def modify(a,b,c):
            p="rc_fastlane/features/castle/Game.server.luau";a["changes"][0]["path"]=p;c["file_blobs"]={p:C}
        self.assertEqual(check(modify)["reason"],"MISSING_AUTHORITY_LEASE")
    def test_reserved_authority_with_lease(self):
        def modify(a,b,c):
            p="rc_fastlane/features/castle/Game.server.luau";a["changes"][0]["path"]=p;c["file_blobs"]={p:C};b["grants"][0]["exclusive_groups"].append("authority:game")
        self.assertEqual(check(modify)["status"],"STAGED_CAS_ELIGIBLE")
    def test_no_global_quality_go(self): self.assertEqual(check()["product_quality"], "NO_GO_UNTIL_HUMAN_ACCEPTANCE")
    def test_no_direct_push_flag(self): self.assertIs(check()["rc_write_allowed"],False)


if __name__ == "__main__": unittest.main(verbosity=2)
