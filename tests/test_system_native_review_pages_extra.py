"""Supplemental no-network adversarial cases for PR60's pagination normalizer.

Synthetic records only. A passing result is NOT evidence of original GitHub
responses, native approvals, reviewer permission, or merge eligibility.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_native_review_pages import PageError, collect_pages, next_review_page

REPO = "kk051780/toy-wars-factory"
PREFIX = f"https://api.github.com/repos/{REPO}/pulls/60/reviews"
LINK = (f'<{PREFIX}?per_page=100&page=2>; rel="next", '
        f'<{PREFIX}?per_page=100&page=2>; rel="last"')

def row(i=1, state="APPROVED", submitted="2026-10-25T00:35:00Z", login="reviewer"):
    obj = {"id": i, "state": state, "commit_id": "a"*40,
           "user": {"login": login, "type": "User"}}
    if submitted is not None: obj["submitted_at"] = submitted
    return obj

class NativeReviewPageExtra(unittest.TestCase):
    def collect(self, rows, permissions=None, link=None):
        def fetch(path):
            self.assertEqual(path,f"/repos/{REPO}/pulls/60/reviews?per_page=100&page=1")
            return {"status":200,"body":rows,"link":link}
        return collect_pages(fetch, REPO, 60, {"reviewer":"write"} if permissions is None else permissions)
    def blocked(self, rows, permissions=None, link=None):
        with self.assertRaises(PageError): self.collect(rows,permissions,link)
    def test_unhashable_state_denied(self):
        x=row();x["state"]=["APPROVED"];self.blocked([x])
    def test_boolean_id_denied(self):
        x=row();x["id"]=True;self.blocked([x])
    def test_missing_commit_sha_denied(self):
        x=row();del x["commit_id"];self.blocked([x])
    def test_nonhex_commit_sha_denied(self):
        x=row();x["commit_id"]="x"*40;self.blocked([x])
    def test_invalid_user_type_denied(self):
        x=row();x["user"]["type"]="Organization";self.blocked([x])
    def test_space_in_login_denied(self):
        x=row(login="bad name");self.blocked([x])
    def test_noncanonical_role_key_denied(self):
        self.blocked([row()],{"Reviewer":"write"})
    def test_timezone_offset_order_uses_instants(self):
        rows=[row(1,"COMMENTED","2026-10-25T01:30:00+02:00"),
              row(2,"APPROVED","2026-10-25T00:35:00Z")]
        self.assertEqual(len(self.collect(rows)["reviews"]),2)
    def test_time_reversed_in_utc_denied(self):
        rows=[row(1,"COMMENTED","2026-10-25T00:30:00Z"),
              row(2,"APPROVED","2026-10-25T01:40:00+02:00")]
        self.blocked(rows)
    def test_naive_time_denied(self):
        self.blocked([row(submitted="2026-10-25T00:35:00")])
    def test_invalid_time_denied(self):
        self.blocked([row(submitted="2026-99-99T01:00:00Z")])
    def test_future_last_with_no_next_denied(self):
        link=f'<{PREFIX}?per_page=100&page=4>; rel="last"'
        with self.assertRaises(PageError): next_review_page(link,REPO,60,2)
    def test_last_page_smaller_than_next_denied(self):
        link=(f'<{PREFIX}?per_page=100&page=2>; rel="next", '
              f'<{PREFIX}?per_page=100&page=1>; rel="last"')
        with self.assertRaises(PageError): next_review_page(link,REPO,60,1)
    def test_first_link_not_one_denied(self):
        link=f'<{PREFIX}?per_page=100&page=3>; rel="first"'
        with self.assertRaises(PageError): next_review_page(link,REPO,60,2)
    def test_pending_is_not_a_complete_attestation(self):
        x=self.collect([row(state="PENDING",submitted=None)])
        self.assertIsNone(x["reviews"][0]["submitted_at"])
        self.assertFalse(x["provider_authenticated"])
        self.assertNotIn("source",x)
        self.assertNotIn("complete",x)
    def test_bot_actor_carries_original_type(self):
        x=row(state="COMMENTED",login="review-bot")
        x["user"]["type"]="Bot"
        got=self.collect([x],{"review-bot":"read"})
        self.assertEqual(got["reviews"][0]["user"]["type"],"Bot")
    def test_true_http_status_is_not_200(self):
        with self.assertRaises(PageError):
            collect_pages(lambda _: {"status":True,"body":[row()],"link":None},REPO,60,{"reviewer":"write"})
    def test_duplicate_review_id_in_same_page_denied(self):
        self.blocked([row(1),row(1)])
    def test_bad_next_pr_scope_denied(self):
        with self.assertRaises(PageError): next_review_page(LINK.replace("pulls/60", "pulls/61"),REPO,60,1)

if __name__ == "__main__":
    unittest.main()
