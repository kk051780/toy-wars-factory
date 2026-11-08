"""Atomic P0-C receipt replay tests; all operations are offline test fixtures."""
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from tools.system_p0c_readonly_receipt_ledger import (
    DB_BASENAME, record_readonly_receipt_once,
)
from tools.system_p0c_windows_receive_once import HOST, PREFIX

NOW = datetime(2026,11,8,6,42,tzinfo=timezone.utc)
REPO = "kk051780/toy-wars-factory"


def comment(*, comment_id=6718344277, work_id="P0C_RECEIPT_LEDGER_20261108_A",
            nonce="0123456789abcdef0123456789abcdef", action="PING_STATUS_READONLY"):
    intent = {
        "schema":1, "repo":REPO, "issuer_claim":"kk051780",
        "source_kind":"CHATGPT_GITHUB_INTENT_UNTRUSTED",
        "action":action, "work_id":work_id, "nonce":nonce,
        "host_id":HOST, "target_branch":"main",
        "main_sha":"e5deff4d5681bca4823a3da0f848e01bc089ae6e",
        "issued_at":"2026-11-08T06:40:00Z",
        "expires_at":"2026-11-08T06:45:00Z",
    }
    return {
        "id":comment_id,
        "url":"https://api.github.com/repos/"+REPO+"/issues/comments/"+str(comment_id),
        "issue_url":"https://api.github.com/repos/"+REPO+"/issues/204",
        "html_url":"https://github.com/"+REPO+"/issues/204#issuecomment-"+str(comment_id),
        "user":{"login":"kk051780","type":"User"}, "author_association":"OWNER",
        "performed_via_github_app":{"slug":"chatgpt-codex-connector"},
        "created_at":"2026-11-08T06:41:34Z",
        "updated_at":"2026-11-08T06:41:34Z",
        "body":PREFIX+json.dumps(intent),
    }


class ReceiptLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/DB_BASENAME

    def tearDown(self):
        self.temp.cleanup()

    def record(self, obj=None, *, path=None, host=HOST, now=NOW):
        result = record_readonly_receipt_once(
            comment=comment() if obj is None else obj,
            now_utc=now, observed_host=host,
            database_path=self.path if path is None else path,
        )
        for key in ("owner_authorized","host_approved_to_execute",
                    "codex_execution_authorized","may_run_commands",
                    "pc_action_executed","is_background_receiver"):
            self.assertIs(result[key], False)
        return result

    def test_valid_metadata_creates_local_receipt_not_pc_execution(self):
        r=self.record()
        self.assertEqual(r["status"],"READ_ONLY_RECEIPT_RECORDED_NO_ACTION")
        self.assertTrue(r["receipt_written"])
        self.assertTrue(self.path.is_file())

    def test_duplicate_after_new_session_is_blocked(self):
        self.assertTrue(self.record()["receipt_written"])
        r=self.record()
        self.assertEqual(r["status"],"READ_ONLY_REPLAY_BLOCKED_NO_ACTION")

    def test_reused_work_id_even_with_new_nonce_and_comment_id_blocked(self):
        self.record()
        x=comment(comment_id=6718344278,nonce="a"*32)
        self.assertEqual(self.record(x)["status"],"READ_ONLY_REPLAY_BLOCKED_NO_ACTION")

    def test_reused_nonce_with_new_work_id_blocked(self):
        self.record()
        x=comment(comment_id=6718344278,work_id="P0C_RECEIPT_LEDGER_20261108_B")
        self.assertEqual(self.record(x)["status"],"READ_ONLY_REPLAY_BLOCKED_NO_ACTION")

    def test_reused_comment_id_with_new_work_id_and_nonce_blocked(self):
        self.record()
        x=comment(work_id="P0C_RECEIPT_LEDGER_20261108_B",nonce="a"*32)
        self.assertEqual(self.record(x)["status"],"READ_ONLY_REPLAY_BLOCKED_NO_ACTION")

    def test_distinct_valid_comments_each_record_once(self):
        self.assertTrue(self.record()["receipt_written"])
        x=comment(comment_id=6718344278,work_id="P0C_RECEIPT_LEDGER_20261108_B",nonce="a"*32)
        self.assertTrue(self.record(x)["receipt_written"])

    def test_competing_atomic_claims_at_most_one_succeeds(self):
        def attempt(i):
            return self.record()["status"]
        with ThreadPoolExecutor(max_workers=5) as pool:
            results=list(pool.map(attempt, range(8)))
        self.assertEqual(results.count("READ_ONLY_RECEIPT_RECORDED_NO_ACTION"),1)
        self.assertEqual(results.count("READ_ONLY_REPLAY_BLOCKED_NO_ACTION"),7)

    def test_expired_comment_does_not_create_db(self):
        r=self.record(now=datetime(2026,11,8,6,46,tzinfo=timezone.utc))
        self.assertFalse(r["receipt_written"])
        self.assertFalse(self.path.exists())

    def test_spoofed_actor_does_not_create_db(self):
        x=comment();x["user"]["login"]="attacker"
        self.assertFalse(self.record(x)["receipt_written"])
        self.assertFalse(self.path.exists())

    def test_shell_action_does_not_create_db(self):
        self.assertFalse(self.record(comment(action="RUN_SHELL"))["receipt_written"])
        self.assertFalse(self.path.exists())

    def test_wrong_host_does_not_create_db(self):
        self.assertFalse(self.record(host="OTHER-PC")["receipt_written"])
        self.assertFalse(self.path.exists())

    def test_naive_clock_does_not_create_db(self):
        self.assertFalse(self.record(now=datetime(2026,11,8,6,42))["receipt_written"])
        self.assertFalse(self.path.exists())

    def test_db_path_must_be_absolute(self):
        self.assertFalse(self.record(path=Path(DB_BASENAME))["receipt_written"])

    def test_db_name_must_be_fixed(self):
        self.assertFalse(self.record(path=Path(self.temp.name)/"foreign.sqlite3")["receipt_written"])

    def test_missing_parent_does_not_get_created(self):
        x=Path(self.temp.name)/"not-exist"/DB_BASENAME
        self.assertFalse(self.record(path=x)["receipt_written"])
        self.assertFalse(x.parent.exists())

    def test_corrupt_db_is_blocked(self):
        self.path.write_bytes(b"not a sqlite database")
        r=self.record()
        self.assertEqual(r["status"],"READ_ONLY_RECEIPT_BLOCKED_NO_ACTION")

    def test_ledger_stores_no_token_or_body(self):
        self.record()
        con=sqlite3.connect(str(self.path))
        try:
            cols=[x[1] for x in con.execute("PRAGMA table_info(readonly_receipts)")]
            self.assertEqual(cols,["work_id","nonce","comment_id","body_sha256","observed_utc"])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM readonly_receipts").fetchone()[0],1)
        finally:
            con.close()

    def test_unreadable_metadata_no_db(self):
        x=comment();x["body"]="P0C_READONLY_INTENT_V1\ninvalid"
        self.assertFalse(self.record(x)["receipt_written"])
        self.assertFalse(self.path.exists())

    def test_broken_symlink_database_refused(self):
        link=Path(self.temp.name)/"test-symlink"
        try:
            self.path.symlink_to(link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable in runner")
        r=self.record()
        self.assertFalse(r["receipt_written"])

    def test_same_ledger_persists_across_new_instance(self):
        self.record()
        path_copy=str(self.path)
        self.assertEqual(self.record(path=path_copy)["status"],"READ_ONLY_REPLAY_BLOCKED_NO_ACTION")


if __name__=="__main__":
    unittest.main()
