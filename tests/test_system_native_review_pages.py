"""Native review REST pagination safety: standalone untrusted, read-only normalization."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from system_native_review_pages import collect_pages, next_review_page, PageError

REPO="kk051780/toy-wars-factory"
URL=f"https://api.github.com/repos/{REPO}/pulls/60/reviews"
LINK=f'<{URL}?per_page=100&page=2>; rel="next", <{URL}?per_page=100&page=2>; rel="last"'
SHA="a"*40

def review(i,state="COMMENTED",user="reviewer",submitted="2026-10-25T00:35:00Z"):
    r={"id":i,"state":state,"commit_id":SHA,
       "user":{"login":user,"type":"User"}}
    if submitted is not None:r["submitted_at"]=submitted
    return r

def fetcher(pages,observed):
    def get(path):
        observed.append(path)
        return pages[int(path.split("page=")[-1])]
    return get

class NativeReviewPages(unittest.TestCase):
    def collect(self,pages,permissions=None):
        seen=[]
        out=collect_pages(fetcher(pages,seen),REPO,60,
                          {"reviewer":"write"} if permissions is None else permissions)
        return out,seen

    def assertDenied(self,pages,permissions=None):
        with self.assertRaises(PageError):
            self.collect(pages,permissions)

    def test_single_page_no_attestation(self):
        a,seen=self.collect({1:{"status":200,"body":[review(1,"APPROVED")],"link":None}})
        self.assertEqual((len(a["reviews"]),a["pages_read"]),(1,1))
        self.assertEqual(seen,[f"/repos/{REPO}/pulls/60/reviews?per_page=100&page=1"])
        self.assertFalse(a["provider_authenticated"])
        self.assertNotIn("source",a)
        self.assertNotIn("complete",a)

    def test_all_101_paginated_rows_retained(self):
        p={1:{"status":200,"body":[review(i) for i in range(1,101)],"link":LINK},
           2:{"status":200,"body":[review(101,"APPROVED")],"link":None}}
        a,seen=self.collect(p)
        self.assertEqual((len(a["reviews"]),a["pages_read"],len(seen)),(101,2,2))

    def test_pending_without_submitted_at(self):
        a,_=self.collect({1:{"status":200,"body":[review(1,"PENDING",submitted=None),
                                               review(2,"APPROVED")],"link":None}})
        self.assertIsNone(a["reviews"][0]["submitted_at"])

    def test_duplicate_id_across_pages_is_denied(self):
        self.assertDenied({1:{"status":200,"body":[review(i) for i in range(1,101)],"link":LINK},
                          2:{"status":200,"body":[review(100)],"link":None}})

    def test_non_200_blocks(self):
        self.assertDenied({1:{"status":403,"body":[],"link":None}})

    def test_status_bool_not_accepted(self):
        self.assertDenied({1:{"status":True,"body":[],"link":None}})

    def test_nonlist_body_blocks(self):
        self.assertDenied({1:{"status":200,"body":{"message":"rate-limit"},"link":None}})

    def test_overfull_page_blocks(self):
        self.assertDenied({1:{"status":200,"body":[review(i) for i in range(1,102)],"link":None}})

    def test_short_page_with_next_blocks(self):
        self.assertDenied({1:{"status":200,"body":[review(1)],"link":LINK}})

    def test_missing_permission_blocks(self):
        self.assertDenied({1:{"status":200,"body":[review(1,"APPROVED")],"link":None}},{})

    def test_pending_with_submission_blocks(self):
        self.assertDenied({1:{"status":200,"body":[review(1,"PENDING")],"link":None}})

    def test_unhashable_review_state_fails_closed(self):
        r=review(1);r["state"]=["APPROVED"]
        self.assertDenied({1:{"status":200,"body":[r],"link":None}})

    def test_unknown_response_key_blocks(self):
        self.assertDenied({1:{"status":200,"body":[],"link":None,"secret":"x"}})

    def test_wrong_origin_next_link_blocks(self):
        with self.assertRaises(PageError):
            next_review_page(LINK.replace("api.github.com","attacker.invalid"),REPO,60,1)

    def test_foreign_repo_next_link_blocks(self):
        with self.assertRaises(PageError):
            next_review_page(LINK.replace(REPO,"other/repo"),REPO,60,1)

    def test_skip_page_blocks(self):
        with self.assertRaises(PageError):
            next_review_page(LINK.replace("page=2","page=3"),REPO,60,1)

    def test_duplicate_next_blocks(self):
        link=f'<{URL}?per_page=100&page=2>; rel="next"'
        with self.assertRaises(PageError):
            next_review_page(link+", "+link,REPO,60,1)

    def test_wrong_per_page_blocks(self):
        with self.assertRaises(PageError):
            next_review_page(LINK.replace("per_page=100","per_page=30"),REPO,60,1)

    def test_invalid_pr_or_repo_blocks_before_fetch(self):
        with self.assertRaises(PageError):
            collect_pages(lambda path: self.fail("must not fetch"),REPO,True,{})
        with self.assertRaises(PageError):
            collect_pages(lambda path: self.fail("must not fetch"),"bad/../repo",60,{})

if __name__=="__main__":
    unittest.main()
