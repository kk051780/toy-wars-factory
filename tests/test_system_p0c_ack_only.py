"""P0-C ACK candidate regression tests: fake transport, zero GitHub writes."""
import json
import unittest
from datetime import datetime, timezone
from tools.system_p0c_ack_only import (
    ACK_PREFIX, AckBlocked, ROOT, POST_URL, make_ack_only,
    post_ack_only_once,
)
from tools.system_p0c_windows_receive_once import HOST, PREFIX, REPO, api_url

NOW = datetime(2026, 11, 8, 10, 17, 35, tzinfo=timezone.utc)
SHA = "e5deff4d5681bca4823a3da0f848e01bc089ae6e"
CID = 6720260802
WORK = "P0C_LIVE_RECEIVER_20261108101723_3043571"
FAKE = "fake_token_only_in_unit_test_123456"


def original_comment():
    intent = {
        "schema": 1, "repo": REPO, "issuer_claim": "kk051780",
        "source_kind": "CHATGPT_GITHUB_INTENT_UNTRUSTED",
        "action": "PING_STATUS_READONLY", "work_id": WORK,
        "nonce": "000001a1baa9a973b1de71647eb7b37d",
        "host_id": HOST, "target_branch": "main", "main_sha": SHA,
        "issued_at": "2026-11-08T10:17:23Z",
        "expires_at": "2026-11-08T10:25:23Z",
    }
    return {
        "id": CID, "url": api_url(CID),
        "issue_url": ROOT + "/issues/204",
        "html_url": "https://github.com/" + REPO + "/issues/204#issuecomment-" + str(CID),
        "user": {"login": "kk051780", "type": "User"},
        "author_association": "OWNER",
        "performed_via_github_app": {"slug": "chatgpt-codex-connector"},
        "created_at": "2026-11-08T10:17:30Z",
        "updated_at": "2026-11-08T10:17:30Z",
        "body": PREFIX + json.dumps(intent),
    }


class Response:
    def __init__(self, url, body, status=201):
        self.url, self.body, self.status = url, body, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, n):
        return self.body[:n]


class AckOnlyTests(unittest.TestCase):
    def setUp(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        self.get_calls = []
        self.post_calls = []
        self.source_impl = lambda cid: original_comment()
        self.post_impl = lambda req, timeout: self.fail("unexpected outbound POST")
        def fake_get(comment_id):
            self.get_calls.append(comment_id)
            return self.source_impl(comment_id)
        def fake_post(req, timeout):
            self.post_calls.append((req, timeout))
            return self.post_impl(req, timeout)
        self.p_get = patch("tools.system_p0c_ack_only.fetch_comment_once", side_effect=fake_get)
        self.p_opener = patch("tools.system_p0c_ack_only.build_opener",
                              return_value=SimpleNamespace(open=fake_post))
        self.p_get.start()
        self.addCleanup(self.p_get.stop)
        self.p_opener.start()
        self.addCleanup(self.p_opener.stop)

    def preview(self, obj=None, now=NOW, host=HOST, sha=SHA):
        return make_ack_only(original_comment() if obj is None else obj,
                             now_utc=now, observed_host=host,
                             expected_main_sha=sha)

    def deliver(self, obj=None, now=NOW, host=HOST, sha=SHA,
                optin=True, token=FAKE):
        return post_ack_only_once(
            original_comment() if obj is None else obj,
            now_utc=now, observed_host=host, expected_main_sha=sha,
            owner_opt_in=optin, approved_issues_write_token=token,
        )

    def test_valid_ping_receipt_has_no_exec_rights(self):
        result = json.loads(self.preview()[len(ACK_PREFIX):])
        self.assertEqual(result["source_comment_id"], CID)
        self.assertEqual(result["kind"],
                         "UNATTESTED_PING_RECEIPT_CANDIDATE_NO_EXECUTION")
        self.assertEqual(result["work_id"], WORK)
        for key in ("owner_execution_authorized", "codex_executed",
                    "studio_executed", "git_source_written", "host_attested",
                    "host_origin_verified",
                    "github_app_proves_owner_pc_authorization"):
            self.assertIs(result[key], False)

    def test_bad_action_rejected(self):
        obj = original_comment()
        data = json.loads(obj["body"][len(PREFIX):])
        data["action"] = "RUN_CODEX"
        obj["body"] = PREFIX + json.dumps(data)
        with self.assertRaises(AckBlocked):
            self.preview(obj)

    def test_extra_shell_key_rejected(self):
        obj = original_comment()
        data = json.loads(obj["body"][len(PREFIX):])
        data["shell"] = "echo bad"
        obj["body"] = PREFIX + json.dumps(data)
        with self.assertRaises(AckBlocked):
            self.preview(obj)

    def test_wrong_source_user_rejected(self):
        obj = original_comment()
        obj["user"]["login"] = "attacker"
        with self.assertRaises(AckBlocked):
            self.preview(obj)

    def test_wrong_source_app_rejected(self):
        obj = original_comment()
        obj["performed_via_github_app"]["slug"] = "other"
        with self.assertRaises(AckBlocked):
            self.preview(obj)

    def test_edited_source_rejected(self):
        obj = original_comment()
        obj["updated_at"] = "2026-11-08T10:17:31Z"
        with self.assertRaises(AckBlocked):
            self.preview(obj)

    def test_wrong_host_rejected(self):
        with self.assertRaises(AckBlocked):
            self.preview(host="OTHER-PC")

    def test_main_head_mismatch_rejected(self):
        with self.assertRaises(AckBlocked):
            self.preview(sha="a" * 40)

    def test_expired_rejected(self):
        with self.assertRaises(AckBlocked):
            self.preview(now=datetime(2026, 11, 8, 10, 26, tzinfo=timezone.utc))

    def test_default_without_optin_makes_no_get_or_post(self):
        with self.assertRaisesRegex(AckBlocked, "OPT_IN"):
            self.deliver(optin=False)
        self.assertEqual(self.get_calls, [])
        self.assertEqual(self.post_calls, [])

    def test_without_approved_token_makes_no_get_or_post(self):
        with self.assertRaisesRegex(AckBlocked, "TOKEN"):
            self.deliver(token=None)
        self.assertEqual(self.get_calls, [])
        self.assertEqual(self.post_calls, [])

    def test_single_fixed_post_receipt_not_execution(self):
        def post(req, timeout):
            self.assertEqual(req.full_url, POST_URL)
            self.assertEqual(req.get_method(), "POST")
            self.assertEqual(timeout, 10)
            data = json.loads(req.data.decode("utf-8"))["body"]
            self.assertTrue(data.startswith(ACK_PREFIX))
            self.assertNotIn(FAKE, data)
            body = json.dumps({"id": 1234, "body": data,
                               "issue_url": ROOT + "/issues/204"}).encode()
            return Response(POST_URL, body)
        self.post_impl = post
        result = self.deliver()
        self.assertEqual(self.get_calls, [CID])
        self.assertEqual(len(self.post_calls), 1)
        self.assertEqual(result["ack_comment_id"], 1234)
        self.assertIs(result["codex_executed"], False)
        self.assertIs(result["globally_idempotent"], False)
        self.assertIs(result["host_origin_verified"], False)

    def test_redirected_post_response_rejected(self):
        self.post_impl = lambda req, timeout: Response("https://evil.example/", b"{}")
        with self.assertRaises(AckBlocked):
            self.deliver()
        self.assertEqual(self.get_calls, [CID])
        self.assertEqual(len(self.post_calls), 1)

    def test_missing_source_get_fails_closed_before_post(self):
        self.source_impl = lambda cid: (_ for _ in ()).throw(OSError("offline"))
        with self.assertRaisesRegex(AckBlocked, "GET_FAILED_NO_POST"):
            self.deliver()
        self.assertEqual(self.get_calls, [CID])
        self.assertEqual(self.post_calls, [])

    def test_forged_caller_body_rejected_before_post(self):
        caller = original_comment()
        caller["body"] += "\nEXECUTE_CODEX"
        with self.assertRaisesRegex(AckBlocked, "BODY_MISMATCH_NO_POST"):
            self.deliver(obj=caller)
        self.assertEqual(self.post_calls, [])

    def test_git_source_id_mismatch_is_not_accepted(self):
        def wrong_source(cid):
            obj = original_comment()
            obj["id"] = CID + 1
            return obj
        self.source_impl = wrong_source
        with self.assertRaisesRegex(AckBlocked, "ID_MISMATCH_NO_POST"):
            self.deliver()
        self.assertEqual(self.post_calls, [])

    def test_expired_source_on_fresh_get_blocks_post(self):
        with self.assertRaisesRegex(AckBlocked, "SOURCE_PING_NOT_VALID"):
            self.deliver(now=datetime(2026, 11, 8, 10, 26,
                                      tzinfo=timezone.utc))
        self.assertEqual(self.post_calls, [])

    def test_unapproved_token_never_fetches_source(self):
        with self.assertRaisesRegex(AckBlocked, "TOKEN_REQUIRED"):
            self.deliver(token=None)
        self.assertEqual(self.get_calls, [])

    def test_transport_errors_do_not_echo_credential(self):
        def fail(req, timeout):
            raise RuntimeError("accidental secret " + FAKE)
        self.post_impl = fail
        with self.assertRaises(AckBlocked) as context:
            self.deliver()
        self.assertNotIn(FAKE, str(context.exception))

    def test_caller_cannot_inject_fake_github_source(self):
        with self.assertRaises(TypeError):
            post_ack_only_once(original_comment(), now_utc=NOW,
                observed_host=HOST, expected_main_sha=SHA,
                owner_opt_in=True, approved_issues_write_token=FAKE,
                source_fetcher=lambda cid: original_comment())
        self.assertEqual(self.get_calls, [])
        self.assertEqual(self.post_calls, [])

    def test_caller_cannot_inject_fake_post_transport(self):
        with self.assertRaises(TypeError):
            post_ack_only_once(original_comment(), now_utc=NOW,
                observed_host=HOST, expected_main_sha=SHA,
                owner_opt_in=True, approved_issues_write_token=FAKE,
                transport=lambda req, timeout: Response(POST_URL, b"{}"))
        self.assertEqual(self.get_calls, [])
        self.assertEqual(self.post_calls, [])

    def test_malformed_source_does_not_post(self):
        self.source_impl = lambda cid: {"id": CID, "body": "not a P0C intent"}
        with self.assertRaisesRegex(AckBlocked, "BODY_MISMATCH_NO_POST"):
            self.deliver()
        self.assertEqual(self.post_calls, [])


if __name__ == "__main__":
    unittest.main()
