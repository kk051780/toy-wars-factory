"""PR60 native GitHub review history must evaluate effective decisions safely.

These are untrusted structural fixtures only: no native GitHub identity, independent
approval or merge authority is granted by a passing unit test.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_github_review_gate import verified_native_approval as verify

HEAD = "b" * 40
BASE = "c" * 40
NOW = "2026-10-25T01:00:00Z"


def event(i, login="reviewer-a", state="APPROVED",
          at="2026-10-25T00:50:00Z", sha=HEAD, permission="write"):
    return {"id":i, "state":state, "commit_id":sha, "submitted_at":at,
            "user":{"login":login, "type":"User"},
            "reviewer_permission":permission}


def fixture(history=None, approvals=1):
    policy = {"repository":"kk051780/toy-wars-factory"}
    main = {"sha":BASE, "branch_protection":{"required_approving_review_count":approvals}}
    pr = {"number":60, "head":HEAD, "author_login":"owner",
          "last_pusher_login":"owner", "last_push_at":"2026-10-25T00:20:00Z"}
    snapshot = {"native_approval":{
        "source":"GITHUB_LIVE_PR_REVIEWS_AND_PERMISSIONS",
        "repository":policy["repository"], "pr_number":60, "head_sha":HEAD,
        "base_main_sha":BASE, "author_login":"owner",
        "last_pusher_login":"owner", "last_push_at":pr["last_push_at"],
        "observed_at":"2026-10-25T00:55:00Z", "complete":True,
        "reviews":history if history is not None else [event(1)]}}
    return policy, main, pr, snapshot, NOW


class ReviewHistoryRegression(unittest.TestCase):
    def good(self, events, approvals=1):
        self.assertTrue(verify(*fixture(events, approvals)))
    def blocked(self, events, approvals=1):
        self.assertFalse(verify(*fixture(events, approvals)))

    def test_one_fresh_independent_approval(self):
        self.good([event(1)])

    def test_other_users_comment_then_approval(self):
        self.good([event(1, "commenter", "COMMENTED", "2026-10-25T00:35:00Z", permission="read"), event(2)])

    def test_same_actor_comment_then_approval(self):
        self.good([event(1, "reviewer-a", "COMMENTED", "2026-10-25T00:35:00Z"), event(2)])

    def test_approval_then_comment_does_not_revoke(self):
        self.good([event(1), event(2, "reviewer-a", "COMMENTED", "2026-10-25T00:52:00Z")])

    def test_change_request_then_new_valid_approval(self):
        self.good([event(1, "reviewer-a", "CHANGES_REQUESTED", "2026-10-25T00:30:00Z"), event(2)])

    def test_approval_then_change_request_blocks(self):
        self.blocked([event(1, at="2026-10-25T00:40:00Z") if False else
                      event(1, "reviewer-a", "APPROVED", "2026-10-25T00:40:00Z"),
                      event(2, "reviewer-a", "CHANGES_REQUESTED")])

    def test_dismissed_then_new_approval(self):
        self.good([event(1, "reviewer-a", "DISMISSED", "2026-10-25T00:40:00Z"), event(2)])

    def test_approval_then_dismissal_blocks(self):
        self.blocked([event(1, "reviewer-a", "APPROVED", "2026-10-25T00:40:00Z"),
                      event(2, "reviewer-a", "DISMISSED")])

    def test_151_complete_reviews_not_truncated(self):
        history = [event(i, "commenter", "COMMENTED",
                         "2026-10-25T00:40:00Z", permission="read")
                   for i in range(1, 151)]
        history.append(event(151))
        self.good(history)

    def test_more_than_hundred_comments_without_approval_blocked(self):
        self.blocked([event(i, "commenter", "COMMENTED",
                            "2026-10-25T00:40:00Z", permission="read")
                      for i in range(1, 151)])

    def test_two_distinct_approvals(self):
        self.good([event(1, "reviewer-a", "APPROVED", "2026-10-25T00:40:00Z"),
                   event(2, "reviewer-b")], approvals=2)

    def test_repeat_same_approver_is_not_two(self):
        self.blocked([event(1, "reviewer-a", "APPROVED", "2026-10-25T00:40:00Z"),
                      event(2, "reviewer-a")], approvals=2)

    def test_foreign_change_request_blocks_other_approval(self):
        self.blocked([event(1, "reviewer-a", "APPROVED", "2026-10-25T00:40:00Z"),
                      event(2, "reviewer-b", "CHANGES_REQUESTED")])

    def test_self_comment_is_not_native_approval(self):
        self.good([event(1, "owner", "COMMENTED",
                         "2026-10-25T00:35:00Z", permission="read"), event(2)])

    def test_duplicate_review_id_blocks(self):
        self.blocked([event(1, "reviewer-a"), event(1, "reviewer-b")])

    def test_unhashable_state_blocks_without_crashing(self):
        row=event(1);row["state"]=[]
        self.blocked([row])

    def test_unhashable_user_type_blocks_without_crashing(self):
        row=event(1);row["user"]["type"]={}
        self.blocked([row])

    def test_stale_head_approval_does_not_count(self):
        self.blocked([event(1, sha="d"*40)])

    def test_unverified_incomplete_history_rejected(self):
        args=list(fixture());args[3]["native_approval"]["complete"]=False
        self.assertFalse(verify(*args))
