"""Negative QA for the P0D conditional multiwriter system."""
import unittest
from datetime import datetime,timezone
from copy import deepcopy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import gate
import cas

A="a"*40
B="b"*40
C="c"*40
D="d"*40
E="e"*40
F="f"*40
NOW=datetime(2026,11,15,2,0,tzinfo=timezone.utc)

def fixture():
    registry={
        "schema":"P0D_EXCLUSIVE_CLAIMS_V1",
        "release":"P0D-S1-KIDS-RC01",
        "multiwriter_production_enabled":True,
        "claims":[
            {"claim_id":"g1","feature_id":"WORLD_FOREST_V1",
             "owner":"writer1","authenticated_actor_id":101,
             "resources":["FOREST"],
             "target_paths":["rc_fastlane/features/forest/**"],
             "expires_at":"2026-11-16T00:00:00+00:00","state":"GRANTED"},
            {"claim_id":"g2","feature_id":"MOB_BATTLE_V1",
             "owner":"writer2","authenticated_actor_id":202,
             "resources":["HORDE"],
             "target_paths":["rc_fastlane/features/mobs/**"],
             "expires_at":"2026-11-16T00:00:00+00:00","state":"GRANTED"}
        ]
    }
    candidate={"claim_id":"g1","feature_id":"WORLD_FOREST_V1","owner":"writer1",
               "source_head":B,"base_rc":A,"branch":"feature/forest1"}
    observation={
        "official_head":A,"source_head":B,"ci_source_head":B,"source_ci":"success",
        "high_severity_findings":0,"changed_files":["rc_fastlane/features/forest/Foliage.luau"],
        "authenticated_actor_id":101,"independent_reviewer_actor_id":303,
        "reviewed_source_head":B,"claims_guard_result":"CLAIM_SCOPE_PASS_NOT_RC_ADOPTION",
        "official_branch_protected":True,
        "coordinator_branch_protected":True,
        "protected_registry_blob_sha":C,"live_registry_blob_sha":C,
        "github_trusted_runner":True,"github_branch_rules_verified":True
    }
    return registry,candidate,observation

class AdmissionTest(unittest.TestCase):
    def evaluate(self,mutate=None):
        r,c,o=fixture()
        if mutate:
            mutate(r,c,o)
        return gate.assess(r,c,o,NOW)
    def test_two_disjoint_writers_are_admissible_in_protected_fictional_setup(self):
        r,c,o=fixture()
        self.assertEqual("EVIDENCE_READY_NOT_AUTHORIZATION",gate.assess(r,c,o,NOW)["decision"])
        c.update(claim_id="g2",feature_id="MOB_BATTLE_V1",owner="writer2",
                 source_head=D,branch="feature/mob")
        o.update(source_head=D,ci_source_head=D,reviewed_source_head=D,
                 authenticated_actor_id=202,changed_files=["rc_fastlane/features/mobs/Zombie.luau"])
        self.assertEqual("EVIDENCE_READY_NOT_AUTHORIZATION",gate.assess(r,c,o,NOW)["decision"])
    def test_missing_grants_as_current_registry_holds(self):
        self.assertEqual("NO_UNIQUE_COORDINATOR_GRANT",
             self.evaluate(lambda r,c,o:r.update(claims=[]))["reason"])
    def test_race_stale_base(self):
        self.assertEqual("STALE_BASE_REBASE_REQUIRED",
            self.evaluate(lambda r,c,o:o.update(official_head=E))["reason"])
    def test_overlapping_writer_paths(self):
        def overlap(r,c,o):
            r["claims"][1]["target_paths"]=["rc_fastlane/features/forest/**"]
        self.assertEqual("OVERLAPPING_ACTIVE_CLAIMS",self.evaluate(overlap)["reason"])
    def test_duplicate_alias_resource(self):
        self.assertEqual("DUPLICATE_RESOURCE_GRANTED",
            self.evaluate(lambda r,c,o:r["claims"][1].update(resources=["FOREST"]))["reason"])
    def test_duplicate_feature(self):
        self.assertEqual("DUPLICATE_FEATURE_GRANTED",
            self.evaluate(lambda r,c,o:r["claims"][1].update(feature_id="WORLD_FOREST_V1"))["reason"])
    def test_expired_lease(self):
        self.assertEqual("LEASE_EXPIRED",
            self.evaluate(lambda r,c,o:r["claims"][0].update(expires_at="2026-11-14T00:00:00Z"))["reason"])
    def test_unprotected_official_branch_holds(self):
        self.assertEqual("PROTECTED_BRANCH_NOT_ENFORCED",
            self.evaluate(lambda r,c,o:o.update(official_branch_protected=False))["reason"])
    def test_unprotected_coord_branch_holds(self):
        self.assertEqual("PROTECTED_BRANCH_NOT_ENFORCED",
            self.evaluate(lambda r,c,o:o.update(coordinator_branch_protected=False))["reason"])
    def test_production_flag_off(self):
        self.assertEqual("PRODUCTION_NOT_ENABLED_BY_TRUSTED_COORDINATOR",
            self.evaluate(lambda r,c,o:r.update(multiwriter_production_enabled=False))["reason"])
    def test_self_claimed_reviewer_rejected(self):
        self.assertEqual("INDEPENDENT_REVIEW_MISSING",
            self.evaluate(lambda r,c,o:o.update(independent_reviewer_actor_id=101))["reason"])
    def test_source_ci_wrong_sha(self):
        self.assertEqual("NO_VERIFIED_SOURCE_HEAD_CI",
            self.evaluate(lambda r,c,o:o.update(ci_source_head=E))["reason"])
    def test_actor_mismatch(self):
        self.assertEqual("ACTOR_NOT_IN_GRANT",
            self.evaluate(lambda r,c,o:o.update(authenticated_actor_id=404))["reason"])
    def test_outside_claim(self):
        self.assertEqual("CHANGED_PATH_OUTSIDE_CLAIM",
            self.evaluate(lambda r,c,o:o.update(changed_files=["server/Game.server.luau"]))["reason"])
    def test_shared_game_authority_needs_exclusive_lease(self):
        def change(r,c,o):
            r["claims"][0]["target_paths"]=["server/Game.server.luau"]
            o.update(changed_files=["server/Game.server.luau"])
        self.assertEqual("SHARED_AUTHORITY_LOCK_REQUIRED",self.evaluate(change)["reason"])
    def test_path_traversal(self):
        self.assertEqual("INVALID_PATH",
            self.evaluate(lambda r,c,o:o.update(changed_files=["../server/Game.server.luau"]))["reason"])
    def test_no_forged_identity_of_runner(self):
        self.assertEqual("RUNNER_IDENTITY_UNVERIFIED",
            self.evaluate(lambda r,c,o:o.update(github_trusted_runner=False))["reason"])
    def test_no_green_without_claim_guard(self):
        self.assertEqual("CLAIM_GUARD_NOT_PASS",
            self.evaluate(lambda r,c,o:o.update(claims_guard_result="CLAIM_PENDING"))["reason"])
    def test_missing_registry_blob_proof(self):
        self.assertEqual("REGISTRY_SHA_NOT_PINNED",
            self.evaluate(lambda r,c,o:o.update(live_registry_blob_sha=F))["reason"])
    def test_hard_negative_high_severity(self):
        self.assertEqual("HIGH_SEVERITY_QA_UNCLEAR",
            self.evaluate(lambda r,c,o:o.update(high_severity_findings=1))["reason"])

class FakeGit:
    def __init__(self):
        self.head=A
        self.protected={cas.RC:True,cas.COORD:True}
        self.commits={A:{"tree":B,"parents":[]},
                      D:{"tree":C,"parents":[A]}}
        self.next_commit=E
        self.race=False
        self.writes=0
    def is_protected(self,branch):
        return self.protected[branch]
    def get_head(self,branch):
        return self.head
    def get_commit(self,sha):
        return self.commits[sha]
    def source_blobs(self,source,paths):
        return {p:F for p in paths}
    def create_tree(self,base_tree,blobs):
        self.writes+=1
        return C
    def create_commit(self,message,tree,parents):
        self.writes+=1
        self.commits[E]={"tree":tree,"parents":parents}
        return E
    def patch_ref(self,branch,new_sha,force=False):
        if force:
            raise AssertionError("FORCE_IS_FORBIDDEN")
        if self.race:
            self.head=D
        parent=self.commits[new_sha]["parents"][0]
        if parent!=self.head:
            raise RuntimeError("422: non fast-forward")
        self.head=new_sha
        self.writes+=1

def submit(g):
    return cas.atomic_source_selective_cas(
        g, official_branch=cas.RC,expected_head=A,source_head=F,
        exact_paths=["rc_fastlane/features/forest/Foliage.luau"],
        independent_authorization={
            "decision":"PROTECTED_WORKFLOW_AUTHORIZE_SINGLE_CAS","source_sha":F,
            "expected_rc_head":A,
            "paths":["rc_fastlane/features/forest/Foliage.luau"]},
        message="P0D/FB-009 source-selective")

class CASTest(unittest.TestCase):
    def test_valid_nonforce_atomic_acceptance(self):
        g=FakeGit()
        receipt=submit(g)
        self.assertEqual(E,g.head)
        self.assertEqual("CAS_REF_PATCH_ACCEPTED_SOURCE_QA_NOT_STUDIO_GO",receipt["result"])
        self.assertEqual("PENDING",receipt["same_head_full_ci"])
        self.assertIsNone(receipt["place_bytes"])
        self.assertEqual(3,g.writes)
    def test_branch_protection_off_means_no_writes(self):
        g=FakeGit();g.protected[cas.RC]=False
        with self.assertRaisesRegex(cas.CASBlocked,"MISSING_GITHUB_BRANCH_PROTECTION"):
            submit(g)
        self.assertEqual(0,g.writes)
    def test_coord_protection_off_means_no_writes(self):
        g=FakeGit();g.protected[cas.COORD]=False
        with self.assertRaisesRegex(cas.CASBlocked,"MISSING_GITHUB_BRANCH_PROTECTION"):
            submit(g)
        self.assertEqual(0,g.writes)
    def test_changed_ref_before_work(self):
        g=FakeGit();g.head=D
        with self.assertRaisesRegex(cas.CASConflict,"BASE_MOVED"):
            submit(g)
        self.assertEqual(0,g.writes)
    def test_racing_writer_cannot_overwrite_head(self):
        g=FakeGit();g.race=True
        with self.assertRaisesRegex(cas.CASConflict,"NON_FAST_FORWARD"):
            submit(g)
        self.assertEqual(D,g.head)
    def test_no_plain_preflight_report_authorization(self):
        g=FakeGit()
        with self.assertRaisesRegex(cas.CASBlocked,"NOT_AUTHORIZED"):
            cas.atomic_source_selective_cas(
                g,official_branch=cas.RC,expected_head=A,source_head=F,
                exact_paths=["rc_fastlane/features/forest/Foliage.luau"],
                independent_authorization={"decision":"EVIDENCE_READY_NOT_AUTHORIZATION"},
                message="P0D/test")
        self.assertEqual(0,g.writes)
    def test_reject_relative_parent_path_before_any_write(self):
        g=FakeGit()
        with self.assertRaisesRegex(cas.CASBlocked,"INVALID_TARGET_PATH"):
            cas.atomic_source_selective_cas(
                g,official_branch=cas.RC,expected_head=A,source_head=F,
                exact_paths=["../secret.lua"],
                independent_authorization={
                    "decision":"PROTECTED_WORKFLOW_AUTHORIZE_SINGLE_CAS",
                    "source_sha":F,"expected_rc_head":A,
                    "paths":["../secret.lua"]},
                message="P0D/test")
        self.assertEqual(0,g.writes)

    def test_no_wholesale_merge_or_meta_paths(self):
        g=FakeGit()
        with self.assertRaisesRegex(cas.CASBlocked,"SHARED_META"):
            cas.atomic_source_selective_cas(
                g,official_branch=cas.RC,expected_head=A,source_head=F,
                exact_paths=[".github/workflows/check.yml"],
                independent_authorization={
                    "decision":"PROTECTED_WORKFLOW_AUTHORIZE_SINGLE_CAS",
                    "source_sha":F,"expected_rc_head":A,
                    "paths":[".github/workflows/check.yml"]},
                message="P0D/test")
        self.assertEqual(0,g.writes)

if __name__ == "__main__":
    unittest.main()
