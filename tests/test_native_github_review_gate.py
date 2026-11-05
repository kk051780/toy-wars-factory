"""Review identity structural test fixtures. NEVER authenticate GitHub or merge."""
import copy,unittest
from native_github_review_gate import verified_native_approval as verify

REPO="kk051780/toy-wars-factory";HEAD="b"*40;BASE="c"*40;NOW="2026-10-25T01:00:00Z"
def input():
    p={"repository":REPO}
    m={"sha":BASE,"branch_protection":{"required_approving_review_count":1}}
    pr={"number":60,"head":HEAD,"author_login":"owner","last_pusher_login":"owner",
        "last_push_at":"2026-10-25T00:20:00Z"}
    rv={"native_approval":{"source":"GITHUB_LIVE_PR_REVIEWS_AND_PERMISSIONS",
        "repository":REPO,"pr_number":60,"head_sha":HEAD,"base_main_sha":BASE,
        "author_login":"owner","last_pusher_login":"owner","last_push_at":"2026-10-25T00:20:00Z",
        "observed_at":"2026-10-25T00:55:00Z","complete":True,
        "reviews":[{"id":1,"state":"APPROVED","commit_id":HEAD,
                    "submitted_at":"2026-10-25T00:50:00Z",
                    "user":{"login":"reviewer-one","type":"User"},"reviewer_permission":"write"}]}}
    return p,m,pr,rv
class TestNativeReview(unittest.TestCase):
    def case(self,modifier):
        p,m,pr,r=input();modifier(p,m,pr,r)
        self.assertFalse(verify(p,m,pr,r,NOW))
    def test_good_structural(self):
        self.assertTrue(verify(*input(),NOW))
    def test_no_data(self):self.case(lambda p,m,pr,r:r.clear())
    def test_self_review(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0]["user"].update(login="OWNER"))
    def test_last_pusher(self):self.case(lambda p,m,pr,r:pr.update(last_pusher_login="reviewer-one"))
    def test_dismissed(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0].update(state="DISMISSED"))
    def test_stale_head(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0].update(commit_id="a"*40))
    def test_false_source(self):self.case(lambda p,m,pr,r:r["native_approval"].update(source="PR_BODY"))
    def test_incomplete(self):self.case(lambda p,m,pr,r:r["native_approval"].update(complete=False))
    def test_wrong_pr(self):self.case(lambda p,m,pr,r:r["native_approval"].update(pr_number=158))
    def test_wrong_repo(self):self.case(lambda p,m,pr,r:r["native_approval"].update(repository="attacker/repo"))
    def test_wrong_base(self):self.case(lambda p,m,pr,r:r["native_approval"].update(base_main_sha="a"*40))
    def test_no_write_permission(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0].update(reviewer_permission="read"))
    def test_bool_review_id(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0].update(id=True))
    def test_pre_push(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0].update(submitted_at="2026-10-25T00:19:00Z"))
    def test_future_review(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0].update(submitted_at="2026-10-25T01:01:00Z"))
    def test_future_observation(self):self.case(lambda p,m,pr,r:r["native_approval"].update(observed_at="2026-10-25T01:01:00Z"))
    def test_stale_observation(self):self.case(lambda p,m,pr,r:r["native_approval"].update(observed_at="2026-10-24T23:00:00Z"))
    def test_two_required_one_present(self):self.case(lambda p,m,pr,r:m["branch_protection"].update(required_approving_review_count=2))
    def test_two_distinct_valid(self):
        p,m,pr,r=input();m["branch_protection"]["required_approving_review_count"]=2
        x=copy.deepcopy(r["native_approval"]["reviews"][0]);x["id"]=2;x["user"]["login"]="reviewer-two"
        r["native_approval"]["reviews"].append(x)
        self.assertTrue(verify(p,m,pr,r,NOW))
    def test_duplicate_approver(self):
        p,m,pr,r=input();m["branch_protection"]["required_approving_review_count"]=2
        x=copy.deepcopy(r["native_approval"]["reviews"][0]);x["id"]=2;x["user"]["login"]="REVIEWER-ONE"
        r["native_approval"]["reviews"].append(x)
        self.assertFalse(verify(p,m,pr,r,NOW))
    def test_duplicate_review_id(self):
        p,m,pr,r=input()
        x=copy.deepcopy(r["native_approval"]["reviews"][0]);x["user"]["login"]="reviewer-two"
        r["native_approval"]["reviews"].append(x)
        self.assertFalse(verify(p,m,pr,r,NOW))
    def test_missing_author(self):self.case(lambda p,m,pr,r:pr.pop("author_login"))
    def test_missing_last_push(self):self.case(lambda p,m,pr,r:pr.pop("last_push_at"))
    def test_wrong_reviewer_role(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0]["user"].update(type="Unknown"))
    def test_forged_permission(self):self.case(lambda p,m,pr,r:r["native_approval"]["reviews"][0].update(reviewer_permission=True))
    def test_wrong_author_claim(self):self.case(lambda p,m,pr,r:r["native_approval"].update(author_login="other"))
if __name__=="__main__":unittest.main()
