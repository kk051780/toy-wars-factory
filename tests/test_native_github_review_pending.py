"""PR60: unsubmitted PENDING reviews and conflicting same-second decisions.
Synthetic structure tests only: NOT proof of native GitHub provenance or approval.
"""
import unittest
from test_native_github_review_history import fixture, event
from native_github_review_gate import verified_native_approval as verify

class NativePendingRegressions(unittest.TestCase):
    def good(self, rows, threshold=1):
        self.assertTrue(verify(*fixture(rows, threshold)))
    def hold(self, rows, threshold=1):
        self.assertFalse(verify(*fixture(rows, threshold)))

    def test_pending_null_before_independent_approval(self):
        self.good([event(1, "reviewer-b", "PENDING", None), event(2)])
    def test_pending_null_after_existing_approval(self):
        self.good([event(1), event(2, "reviewer-a", "PENDING", None)])
    def test_pending_without_submitted_at_field_is_neutral(self):
        pending=event(1,"reviewer-b","PENDING",None)
        pending.pop("submitted_at")
        self.good([pending,event(2)])
    def test_author_unsubmitted_draft_is_neutral(self):
        self.good([event(1,"owner","PENDING",None),event(2)])
    def test_pending_does_not_clear_change_request(self):
        self.hold([event(1,"reviewer-b","CHANGES_REQUESTED"),
                   event(2,"reviewer-b","PENDING",None),event(3)])
    def test_pending_not_counted_toward_two_approvals(self):
        self.hold([event(1,"reviewer-b","PENDING",None),event(2)],2)
    def test_pending_only_is_not_an_approval(self):
        self.hold([event(1,"reviewer-b","PENDING",None)])
    def test_pending_with_submitted_timestamp_rejected(self):
        self.hold([event(1,"reviewer-b","PENDING"),event(2)])
    def test_pending_invalid_sha_rejected(self):
        self.hold([event(1,"reviewer-b","PENDING",None,sha="BAD"),event(2)])
    def test_pending_duplicate_id_rejected(self):
        self.hold([event(1,"reviewer-b","PENDING",None),event(1)])
    def test_same_second_change_then_approval_not_order_trusted(self):
        self.hold([event(1,state="CHANGES_REQUESTED"),event(2)])
    def test_same_second_approval_then_change_not_order_trusted(self):
        self.hold([event(1),event(2,state="CHANGES_REQUESTED")])
    def test_same_second_two_distinct_reviewers_still_valid(self):
        self.good([event(1),event(2,login="reviewer-b")],2)
    def test_later_approval_can_clear_previous_change_request(self):
        self.good([event(1,state="CHANGES_REQUESTED",at="2026-10-25T00:40:00Z"),event(2)])
    def test_same_actor_never_counts_twice(self):
        self.hold([event(1),event(2)],2)
