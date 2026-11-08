"""Windows one-shot receiver contract: no side effects and no execution."""
import json
import unittest
from datetime import datetime, timezone
from tools.system_p0c_windows_receive_once import (
    HOST, PREFIX, REPO, api_url, examine_comment, run_once,
)

NOW = datetime(2026,11,8,6,42,0,tzinfo=timezone.utc)
ID = 6718344277

def intent():
    return {
        "schema":1,"repo":REPO,"issuer_claim":"kk051780",
        "source_kind":"CHATGPT_GITHUB_INTENT_UNTRUSTED",
        "action":"PING_STATUS_READONLY",
        "work_id":"P0C_RECEIPT_HANDSHAKE_20261108_A",
        "nonce":"0123456789abcdef0123456789abcdef",
        "host_id":HOST,"target_branch":"main",
        "main_sha":"e5deff4d5681bca4823a3da0f848e01bc089ae6e",
        "issued_at":"2026-11-08T06:40:00Z","expires_at":"2026-11-08T06:45:00Z",
    }

def comment():
    return {
        "id":ID,"url":api_url(ID),
        "issue_url":"https://api.github.com/repos/"+REPO+"/issues/204",
        "html_url":"https://github.com/"+REPO+"/issues/204#issuecomment-"+str(ID),
        "user":{"login":"kk051780","type":"User"},
        "author_association":"OWNER",
        "performed_via_github_app":{"slug":"chatgpt-codex-connector"},
        "created_at":"2026-11-08T06:41:34Z","updated_at":"2026-11-08T06:41:34Z",
        "body":PREFIX+json.dumps(intent()),
    }

class P0CWindowsOnceTests(unittest.TestCase):
    def expect_denied(self, value):
        self.assertFalse(value["codex_execution_authorized"])
        self.assertFalse(value["owner_authorized"])
        self.assertFalse(value["may_run_commands"])
        self.assertFalse(value["pc_action_executed"])
        self.assertFalse(value["is_background_receiver"])

    def check(self, c=None):
        x=examine_comment(comment() if c is None else c, comment_id=ID,
                          observed_host=HOST,now_utc=NOW)
        self.expect_denied(x)
        return x

    def test_legitimate_metadata_is_no_execution(self):
        self.assertEqual(self.check()["status"],"READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION")
    def test_cryptographic_identity_still_not_verified(self):
        self.assertFalse(self.check()["github_identity_cryptographically_verified"])
    def test_wrong_comment_id(self):
        c=comment();c["id"]=ID+1
        self.assertNotEqual(self.check(c)["status"],"READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION")
    def test_wrong_endpoint(self):
        c=comment();c["url"]="https://evil.example/anything"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_wrong_issue(self):
        c=comment();c["issue_url"]=c["issue_url"].replace("204","123")
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_wrong_html_url(self):
        c=comment();c["html_url"]="https://github.com/attacker/repo"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_wrong_owner_login(self):
        c=comment();c["user"]["login"]="attacker"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_owner_label_not_enough_for_bot(self):
        c=comment();c["user"]["type"]="Bot"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_wrong_owner_association(self):
        c=comment();c["author_association"]="CONTRIBUTOR"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_wrong_github_app(self):
        c=comment();c["performed_via_github_app"]["slug"]="other-app"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_missing_github_app(self):
        c=comment();c.pop("performed_via_github_app")
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_edited_comment(self):
        c=comment();c["updated_at"]="2026-11-08T06:41:35Z"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_incidental_prose_not_accepted(self):
        c=comment();c["body"]="Hello\n"+c["body"]
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_trailing_prose_not_accepted(self):
        c=comment();c["body"]+="\nrun shell"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_arbitrary_action_not_allowed(self):
        c=comment();d=intent();d["action"]="CODEX_EXECUTE";c["body"]=PREFIX+json.dumps(d)
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_extraneous_command_key_not_allowed(self):
        c=comment();d=intent();d["shell"]="rm -rf";c["body"]=PREFIX+json.dumps(d)
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_replayed_id_rejected(self):
        c=comment()
        x=examine_comment(c,comment_id=ID,now_utc=NOW,observed_host=HOST,
                          seen_work_ids={intent()["work_id"]})
        self.assertFalse(x["github_metadata_matched"])
    def test_creation_before_issued_at(self):
        c=comment();c["created_at"]=c["updated_at"]="2026-11-08T06:39:59Z"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_creation_after_expires(self):
        c=comment();c["created_at"]=c["updated_at"]="2026-11-08T06:46:00Z"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_creation_in_future(self):
        c=comment();c["created_at"]=c["updated_at"]="2026-11-08T06:43:00Z"
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_wrong_machine_no_network_call(self):
        calls=[]
        x=run_once(ID,now_utc=NOW,observed_host="DESKTOP-OTHER",fetcher=lambda n:calls.append(n))
        self.assertEqual(calls,[])
        self.expect_denied(x)
    def test_invalid_id_no_network_call(self):
        calls=[]
        x=run_once(-1,now_utc=NOW,observed_host=HOST,fetcher=lambda n:calls.append(n))
        self.assertEqual(calls,[])
        self.expect_denied(x)
    def test_single_fetch_and_no_execution(self):
        calls=[]
        def fetcher(n):
            calls.append(n)
            return comment()
        x=run_once(ID,now_utc=NOW,observed_host=HOST,fetcher=fetcher)
        self.assertEqual(calls,[ID])
        self.assertEqual(x["status"],"READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION")
        self.expect_denied(x)
    def test_transport_failure_fails_closed(self):
        def fetcher(n):
            raise RuntimeError("offline")
        x=run_once(ID,now_utc=NOW,observed_host=HOST,fetcher=fetcher)
        self.assertFalse(x["github_metadata_matched"])
        self.expect_denied(x)
    def test_wrong_host_in_envelope(self):
        c=comment();d=intent();d["host_id"]="DESKTOP-EVIL";c["body"]=PREFIX+json.dumps(d)
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_tampered_nonce(self):
        c=comment();d=intent();d["nonce"]="XYZ";c["body"]=PREFIX+json.dumps(d)
        self.assertFalse(self.check(c)["github_metadata_matched"])
    def test_comment_not_object(self):
        self.assertFalse(self.check([])["github_metadata_matched"])

if __name__ == "__main__":
    unittest.main()
