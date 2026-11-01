"""PR158 security regression: fresh clock and exact single-file CAS commit.

All callbacks are synthetic; a success cannot authenticate a GitHub provider
or grant a Roblox POST. These are requirements for a future reviewed host.
"""
from __future__ import annotations
import unittest
from test_cloud_global_trusted_callbacks import (
    m, GitHubFake, request, OWNER, AT, PARENT, FIRST
)

RESOURCE = "ops/REPAIR_COORDINATOR.json"
OPEN = "2026-10-31T01:30:00Z"
LATE = "2026-10-31T01:49:00Z"
EARLIER = "2026-10-31T01:29:59Z"

class Clock:
    def __init__(self, *values):
        self.values = list(values)
        self.count = 0
    def __call__(self):
        i = min(self.count, len(self.values)-1)
        self.count += 1
        return self.values[i]

class ClockAndScopeTests(unittest.TestCase):
    def call(self, g, *, clock=None, commit=None, provide_clock=True):
        def read_commit(repo, sha):
            if commit is not None:
                return commit(repo, sha)
            return {**g.commit(repo, sha), "changed_paths": [RESOURCE], "changes_complete": True}
        kwargs=dict(request=request(), owner_id=OWNER, epoch=306, now=AT,
                    read=g.read, cas=g.cas, read_commit=read_commit)
        if provide_clock:
            kwargs["clock"]=clock or Clock(OPEN, OPEN, OPEN)
        return m.persist_proposal_via_trusted_callbacks(**kwargs)

    def deny(self, f, reason):
        with self.assertRaises(m.Blocked) as caught:
            f()
        self.assertEqual(str(caught.exception), reason)

    def test_01_missing_trusted_clock_denied(self):
        g=GitHubFake()
        self.deny(lambda:self.call(g,provide_clock=False),"TRUSTED_CLOCK_MISSING")
        self.assertEqual(g.cas_calls,[])

    def test_02_fresh_clock_required_before_cas(self):
        g=GitHubFake(); clock=Clock(OPEN,LATE,LATE)
        self.deny(lambda:self.call(g,clock=clock),"LEASE_NOT_LIVE")
        self.assertEqual(g.cas_calls,[])

    def test_03_fresh_clock_required_after_cas(self):
        g=GitHubFake(); clock=Clock(OPEN,OPEN,LATE)
        self.deny(lambda:self.call(g,clock=clock),"LEASE_NOT_LIVE")
        self.assertEqual(len(g.cas_calls),1)

    def test_04_monotonic_clock_rollback_rejected(self):
        g=GitHubFake(); clock=Clock(OPEN,EARLIER,EARLIER)
        self.deny(lambda:self.call(g,clock=clock),"CLOCK_ROLLBACK_HOLD")
        self.assertEqual(g.cas_calls,[])

    def test_05_clock_exception_redacted(self):
        g=GitHubFake()
        def fail():
            raise RuntimeError("private-token-must-not-leak")
        self.deny(lambda:self.call(g,clock=fail),"TRUSTED_CLOCK_UNAVAILABLE_HOLD")
        self.assertEqual(g.cas_calls,[])

    def test_06_clock_must_be_timezone_aware(self):
        g=GitHubFake();clock=Clock("2026-10-31T01:30:00")
        self.deny(lambda:self.call(g,clock=clock),"INVALID_TIME")
        self.assertEqual(g.cas_calls,[])

    def test_07_changed_source_file_in_cas_commit_denied(self):
        g=GitHubFake()
        def altered(repo, sha):
            return {**g.commit(repo,sha), "changed_paths": [RESOURCE, "src/ToyWarsServer.server.lua"],"changes_complete":True}
        self.deny(lambda:self.call(g,commit=lambda repo,sha:altered(repo,sha)),"COMMIT_SCOPE_NOT_PROVEN_HOLD")
        self.assertEqual(len(g.cas_calls),1)

    def test_08_unverified_incomplete_change_list_denied(self):
        g=GitHubFake()
        def forged(repo,sha):
            return {**g.commit(repo,sha),"changed_paths":[RESOURCE],"changes_complete":False}
        self.deny(lambda:self.call(g,commit=forged),"COMMIT_SCOPE_NOT_PROVEN_HOLD")

    def test_09_missing_changed_paths_denied(self):
        g=GitHubFake()
        def incomplete(repo,sha):return {**g.commit(repo,sha),"changed_paths":None,"changes_complete":True}
        self.deny(lambda:self.call(g,commit=incomplete),"COMMIT_SCOPE_NOT_PROVEN_HOLD")

    def test_10_duplicate_scope_paths_denied(self):
        g=GitHubFake()
        def duplicates(repo,sha):
            return {**g.commit(repo,sha),"changed_paths":[RESOURCE,RESOURCE],"changes_complete":True}
        self.deny(lambda:self.call(g,commit=duplicates),"COMMIT_SCOPE_NOT_PROVEN_HOLD")

    def test_11_wrong_path_scope_denied(self):
        g=GitHubFake()
        def wrong(repo,sha):
            return {**g.commit(repo,sha),"changed_paths":["tools/cloud_global_intent_fence.py"],"changes_complete":True}
        self.deny(lambda:self.call(g,commit=wrong),"COMMIT_SCOPE_NOT_PROVEN_HOLD")

    def test_12_exact_clock_and_diff_stays_non_authorizing(self):
        g=GitHubFake();clock=Clock(OPEN,OPEN,OPEN)
        result=self.call(g,clock=clock)
        self.assertEqual(result["status"],"EXACT_PARENT_CAS_READBACK_STRUCTURAL_ONLY")
        self.assertEqual(clock.count,3)
        self.assertEqual(len(g.cas_calls),1)
        for attr in ("post_authorized","github_provider_authenticated",
                     "roblox_engine_verified","merge_authorized","replay_authorized"):
            self.assertIs(result[attr],False)

    def test_13_missing_commit_scope_metadata_denied(self):
        g=GitHubFake()
        def missing(repo,sha):return g.commit(repo,sha)
        self.deny(lambda:self.call(g,commit=missing),"COMMIT_SCOPE_NOT_PROVEN_HOLD")

    def test_14_extra_unknown_commit_metadata_denied(self):
        g=GitHubFake()
        def extra(repo,sha):
            return {**g.commit(repo,sha),"changed_paths":[RESOURCE],
                    "changes_complete":True,"claimed_ok":True}
        self.deny(lambda:self.call(g,commit=extra),"COMMIT_SCOPE_NOT_PROVEN_HOLD")

    def test_15_clock_after_readback_unavailable_holds(self):
        g=GitHubFake();count=[0]
        def clock():
            count[0]+=1
            if count[0]==3:raise RuntimeError("hidden key")
            return OPEN
        self.deny(lambda:self.call(g,clock=clock),"TRUSTED_CLOCK_UNAVAILABLE_HOLD")
        self.assertEqual(len(g.cas_calls),1)

    def test_16_clock_before_cas_unavailable_does_not_write(self):
        g=GitHubFake();count=[0]
        def clock():
            count[0]+=1
            if count[0]==2:raise RuntimeError("hidden key")
            return OPEN
        self.deny(lambda:self.call(g,clock=clock),"TRUSTED_CLOCK_UNAVAILABLE_HOLD")
        self.assertEqual(g.cas_calls,[])

if __name__=="__main__":
    unittest.main()
