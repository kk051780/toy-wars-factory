"""P0-C scan-once: no manual comment-id, no PC action."""
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from tools.system_p0c_windows_receive_once import HOST, PREFIX
from tools.system_p0c_windows_scan_once import (
    MAX_PAGES, PAGE_SIZE, page_url, fetch_issue_comments_page,
    inspect_issue_intents, run_scan_once,
)

NOW = datetime(2026,11,8,6,42,tzinfo=timezone.utc)
REPO="kk051780/toy-wars-factory"

def real_candidate(n=6718344277, work_id="P0C_SCAN_ONCE_SAMPLE_20261108_A"):
    intent={
        "schema":1,"repo":REPO,"issuer_claim":"kk051780",
        "source_kind":"CHATGPT_GITHUB_INTENT_UNTRUSTED",
        "action":"PING_STATUS_READONLY","work_id":work_id,
        "nonce":format(n, "032x"),
        "host_id":HOST,"target_branch":"main",
        "main_sha":"e5deff4d5681bca4823a3da0f848e01bc089ae6e",
        "issued_at":"2026-11-08T06:40:00Z",
        "expires_at":"2026-11-08T06:45:00Z",
    }
    return {
        "id":n,"url":"https://api.github.com/repos/"+REPO+"/issues/comments/"+str(n),
        "issue_url":"https://api.github.com/repos/"+REPO+"/issues/204",
        "html_url":"https://github.com/"+REPO+"/issues/204#issuecomment-"+str(n),
        "user":{"login":"kk051780","type":"User"},
        "author_association":"OWNER",
        "performed_via_github_app":{"slug":"chatgpt-codex-connector"},
        "created_at":"2026-11-08T06:41:34Z",
        "updated_at":"2026-11-08T06:41:34Z",
        "body":PREFIX+json.dumps(intent),
    }

class ScanOnceTests(unittest.TestCase):
    def deny(self, r):
        for key in ("owner_authorized","codex_execution_authorized",
                    "may_run_commands","pc_action_executed","is_background_receiver"):
            self.assertIs(r[key],False)
    def scan(self, pages, host=HOST):
        calls=[]
        def get(page):
            calls.append(page)
            return pages.get(page, [])
        r=inspect_issue_intents(fetcher=get,observed_host=host,now_utc=NOW)
        self.deny(r)
        return r,calls
    def test_one_page_valid(self):
        r,calls=self.scan({1:[{"body":"unrelated"},real_candidate()]})
        self.assertEqual(r["status"],"READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION")
        self.assertEqual(calls,[1])
    def test_latest_comment_by_id(self):
        r,_=self.scan({1:[real_candidate(100),real_candidate(101, "P0C_SCAN_ONCE_SAMPLE_20261108_B")]})
        self.assertEqual(r["comment_id"],101)
        self.assertEqual(r["validated_candidates"],2)
    def test_no_comment_is_not_success(self):
        r,calls=self.scan({1:[]})
        self.assertEqual(r["status"],"READ_ONLY_NO_VALID_INTENT")
        self.assertEqual(calls,[1])
    def test_untrusted_issue_comment_ignored(self):
        c=real_candidate();c["user"]["login"]="attacker"
        r,_=self.scan({1:[c]})
        self.assertEqual(r["status"],"READ_ONLY_NO_VALID_INTENT")
    def test_untrusted_malicious_action_ignored(self):
        c=real_candidate();c["body"]+=chr(10)+"powershell"
        r,_=self.scan({1:[c]})
        self.assertEqual(r["status"],"READ_ONLY_NO_VALID_INTENT")
    def test_edited_comment_ignored(self):
        c=real_candidate();c["updated_at"]="2026-11-08T06:41:40Z"
        r,_=self.scan({1:[c]})
        self.assertEqual(r["status"],"READ_ONLY_NO_VALID_INTENT")
    def test_wrong_host_blocks_before_fetch(self):
        r,calls=self.scan({1:[real_candidate()]},host="OTHER-PC")
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
        self.assertEqual(calls,[])
    def test_untrusted_naive_clock_blocks_before_fetch(self):
        calls=[]
        r=inspect_issue_intents(fetcher=lambda page:calls.append(page),observed_host=HOST,now_utc=datetime(2026,11,8))
        self.assertEqual(calls,[])
        self.deny(r)
    def test_multi_page_bound(self):
        junk=[{"body":"irrelevant"} for _ in range(PAGE_SIZE)]
        r,calls=self.scan({1:junk,2:[real_candidate()]})
        self.assertEqual(r["pages_checked"],2)
        self.assertEqual(calls,[1,2])
    def test_incomplete_max_pages_fails_closed(self):
        junk=[{"body":"irrelevant"} for _ in range(PAGE_SIZE)]
        r,calls=self.scan({p:junk for p in range(1,MAX_PAGES+1)})
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
        self.assertEqual(calls,list(range(1,MAX_PAGES+1)))
    def test_malformed_page_fails_closed(self):
        r,_=self.scan({1:"not a list"})
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
    def test_malformed_comment_fails_closed(self):
        r,_=self.scan({1:["oops"]})
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
    def test_page_read_exception_fail_closed(self):
        r=inspect_issue_intents(fetcher=lambda page:1/0,observed_host=HOST,now_utc=NOW)
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
        self.deny(r)
    def test_hardcoded_url(self):
        self.assertEqual(page_url(2),"https://api.github.com/repos/"+REPO+"/issues/204/comments?per_page=100&page=2")
    def test_invalid_page_out_of_bound(self):
        for x in [-1,0,MAX_PAGES+1,True,1.4,"1"]:
            with self.assertRaises(ValueError):page_url(x)
    def test_no_network_if_wrong_pc(self):
        calls=[]
        r=run_scan_once(now_utc=NOW,observed_host="OTHER",fetcher=lambda page:calls.append(page))
        self.assertEqual(calls,[])
        self.deny(r)
    def test_no_network_on_linux_default(self):
        with patch("tools.system_p0c_windows_scan_once.sys.platform","linux"):
            r=run_scan_once(now_utc=NOW,observed_host=HOST)
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
    def test_local_mocked_provider_only_once(self):
        seen=[]
        r=run_scan_once(now_utc=NOW,observed_host=HOST,fetcher=lambda p:(seen.append(p) or [real_candidate()]))
        self.assertEqual(seen,[1])
        self.assertEqual(r["status"],"READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION")
        self.deny(r)

    def test_duplicate_work_id_blocks_entire_scan(self):
        a=real_candidate(110,"P0C_SCAN_ONCE_SAMPLE_20261108_A")
        b=real_candidate(111,"P0C_SCAN_ONCE_SAMPLE_20261108_A")
        r,_=self.scan({1:[a,b]})
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
        self.assertIn("duplicate",r["reason"])
    def test_same_nonce_across_different_work_ids_blocks(self):
        a=real_candidate(110,"P0C_SCAN_ONCE_SAMPLE_20261108_A")
        b=real_candidate(111,"P0C_SCAN_ONCE_SAMPLE_20261108_B")
        body=json.loads(b["body"][len(PREFIX):])
        body["nonce"]=json.loads(a["body"][len(PREFIX):])["nonce"]
        b["body"]=PREFIX+json.dumps(body)
        r,_=self.scan({1:[a,b]})
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
        self.assertIn("duplicate",r["reason"])
    def test_seen_work_id_external_claim_blocks(self):
        a=real_candidate()
        r=inspect_issue_intents(fetcher=lambda page:[a],observed_host=HOST,now_utc=NOW,
                                seen_work_ids={"P0C_SCAN_ONCE_SAMPLE_20261108_A"})
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
    def test_seen_nonce_external_claim_blocks(self):
        a=real_candidate(110)
        r=inspect_issue_intents(fetcher=lambda page:[a],observed_host=HOST,now_utc=NOW,
                                seen_nonces={format(110,"032x")})
        self.assertEqual(r["status"],"READ_ONLY_RECEIVER_BLOCKED")
    def test_one_shot_replay_is_not_persistent_proof(self):
        r,_=self.scan({1:[real_candidate()]})
        self.assertIs(r["replay_history_verified"],False)
        r2,_=self.scan({1:[real_candidate()]})
        self.assertIs(r2["replay_history_verified"],False)
        self.assertEqual(r2["status"],"READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION")
    def test_real_windows_scan_filters_recent_updates(self):
        seen=[]
        def fake(page,*,token,since):
            seen.append((page,token,since))
            return [real_candidate()]
        with patch("tools.system_p0c_windows_scan_once.sys.platform","win32"), patch(
            "tools.system_p0c_windows_scan_once.fetch_issue_comments_page",side_effect=fake
        ):
            r=run_scan_once(now_utc=NOW,observed_host=HOST,token=None)
        self.assertEqual(r["status"],"READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION")
        self.assertEqual(seen,[(1,None,"2026-11-08T06:31:00Z")])
    def test_since_url_cannot_inject_other_host(self):
        u=page_url(1,since="2026-11-08T06:31:00Z")
        self.assertIn("since=2026-11-08T06%3A31%3A00Z",u)
        for bad in ("https://evil.com","2026-11-08T06:31:00Z&x=evil","2026-15-99T06:31:00Z"):
            with self.assertRaises(ValueError):page_url(1,since=bad)

class FakeResponse:
    status=200
    def __init__(self,url,payload):self.url=url;self.payload=payload
    def geturl(self):return self.url
    def read(self,n):return self.payload[:n]
    def __enter__(self):return self
    def __exit__(self,*a):return False

class FakeOpener:
    def __init__(self,response):self.response=response;self.requests=[]
    def open(self,req,timeout):self.requests.append(req);return self.response

class TransportTests(unittest.TestCase):
    def test_auth_header_not_embedded_in_url(self):
        url=page_url(1)
        o=FakeOpener(FakeResponse(url,b"[]"))
        r=fetch_issue_comments_page(1,token="TEST_READ_TOKEN",opener=o)
        self.assertEqual(r,[])
        self.assertEqual(o.requests[0].get_header("Authorization"),"Bearer TEST_READ_TOKEN")
        self.assertNotIn("TEST_READ_TOKEN",o.requests[0].full_url)
        self.assertEqual(o.requests[0].get_method(),"GET")
    def test_anonymous_public_get_never_adds_authorization(self):
        o=FakeOpener(FakeResponse(page_url(1),b"[]"))
        result=fetch_issue_comments_page(1,token=None,opener=o)
        self.assertEqual(result,[])
        self.assertIsNone(o.requests[0].get_header("Authorization"))
        self.assertEqual(o.requests[0].get_method(),"GET")
    def test_invalid_empty_supplied_token_rejected_before_network(self):
        o=FakeOpener(FakeResponse(page_url(1),b"[]"))
        with self.assertRaises(ValueError):fetch_issue_comments_page(1,token="",opener=o)
        self.assertEqual(o.requests,[])
    def test_redirected_endpoint_fails(self):
        o=FakeOpener(FakeResponse("https://example.org/evil",b"[]"))
        with self.assertRaises(ValueError):fetch_issue_comments_page(1,token="TEST_READ_TOKEN",opener=o)
    def test_malformed_remote_json_rejected(self):
        o=FakeOpener(FakeResponse(page_url(1),b'{"not":"a list"}'))
        with self.assertRaises(ValueError):fetch_issue_comments_page(1,token="TEST_READ_TOKEN",opener=o)
    def test_duplicate_json_keys_rejected(self):
        o=FakeOpener(FakeResponse(page_url(1),b'[{"id":1,"id":2}]'))
        with self.assertRaises(ValueError):fetch_issue_comments_page(1,token="TEST_READ_TOKEN",opener=o)
    def test_large_response_rejected(self):
        o=FakeOpener(FakeResponse(page_url(1),b"X"*2000001))
        with self.assertRaises(ValueError):fetch_issue_comments_page(1,token="TEST_READ_TOKEN",opener=o)

if __name__=="__main__":unittest.main()
