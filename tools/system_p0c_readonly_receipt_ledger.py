"""P0-C: opt-in durable, fail-closed READ-ONLY comment receipt ledger.

This is NOT owner authorization, a Codex bridge, or an auto-running Windows
receiver. A caller with explicit host-side consent may record *metadata* of a
previously fetched GitHub comment. Exactly one atomic SQLite INSERT grants
no command-execution permission.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from tools.system_p0c_windows_receive_once import (
    HOST, PREFIX, _no_duplicates, examine_comment,
)

DB_BASENAME = "p0c-readonly-receipts.sqlite3"
_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS readonly_receipts(
    work_id TEXT PRIMARY KEY NOT NULL,
    nonce TEXT NOT NULL UNIQUE,
    comment_id INTEGER NOT NULL UNIQUE,
    body_sha256 TEXT NOT NULL,
    observed_utc TEXT NOT NULL
);
"""
_STATUS_DENIED = "READ_ONLY_RECEIPT_BLOCKED_NO_ACTION"


def _out(status, reason, *, comment_id=None, work_id=None):
    return {
        "status": status, "reason": reason, "comment_id": comment_id,
        "work_id": work_id, "receipt_written": status == "READ_ONLY_RECEIPT_RECORDED_NO_ACTION",
        "owner_authorized": False, "host_approved_to_execute": False,
        "codex_execution_authorized": False, "may_run_commands": False,
        "pc_action_executed": False, "is_background_receiver": False,
    }


def _target_path(database_path):
    """Require an explicit existing directory. Never select a default location."""
    try:
        value = Path(database_path)
        if not value.is_absolute() or value.name != DB_BASENAME:
            raise ValueError("ledger must be absolute with fixed filename")
        if value.is_symlink() or value.parent.is_symlink():
            raise ValueError("symlink path refused")
        if not value.parent.is_dir():
            raise ValueError("parent directory missing")
        if value.exists() and not value.is_file():
            raise ValueError("ledger is not a file")
        return value
    except (TypeError, ValueError, OSError) as exc:
        raise ValueError("invalid ledger path") from exc


def record_readonly_receipt_once(*, comment, now_utc, observed_host, database_path):
    """Persist a comment ID/work ID/nonce once, without executing a task.

    GitHub metadata is informative, not cryptographically owner-authenticated.
    The SQLite database is local state, not distributed CAS. Other devices or
    deleted/tampered ledgers are not covered. No code path can run commands.
    """
    if observed_host != HOST:
        return _out(_STATUS_DENIED, "wrong PC host")
    if (not isinstance(now_utc, datetime) or now_utc.tzinfo is None
            or now_utc.utcoffset() is None):
        return _out(_STATUS_DENIED, "non-UTC-aware clock")
    if type(comment) is not dict or type(comment.get("id")) is not int:
        return _out(_STATUS_DENIED, "missing GitHub comment identity")
    comment_id = comment["id"]
    verdict = examine_comment(
        comment, comment_id=comment_id,
        now_utc=now_utc, observed_host=observed_host,
    )
    if verdict.get("status") != "READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION":
        return _out(_STATUS_DENIED, "GitHub comment diagnostic invalid", comment_id=comment_id)
    try:
        body = comment["body"]
        if not body.startswith(PREFIX):
            raise ValueError("not a P0-C body")
        intent = json.loads(body[len(PREFIX):], object_pairs_hook=_no_duplicates)
        work_id, nonce = intent["work_id"], intent["nonce"]
        if work_id != verdict["work_id"]:
            raise ValueError("work ID mismatch")
        path = _target_path(database_path)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        now = now_utc.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, KeyError, TypeError, UnicodeError, OSError):
        return _out(_STATUS_DENIED, "untrusted receipt input or unsafe path", comment_id=comment_id)
    con = None
    try:
        # sqlite3 BEGIN IMMEDIATE serializes competing writers for one DB.
        # All identifiers are fixed in SQL, and untrusted values use parameters.
        con = sqlite3.connect(str(path), timeout=1.0, isolation_level=None)
        con.execute("BEGIN IMMEDIATE")
        con.execute(_DB_SCHEMA)
        con.execute(
            "INSERT INTO readonly_receipts "
            "(work_id, nonce, comment_id, body_sha256, observed_utc) "
            "VALUES (?, ?, ?, ?, ?)",
            (work_id, nonce, comment_id, digest, now),
        )
        con.commit()
    except sqlite3.IntegrityError:
        if con is not None:
            con.rollback()
        return _out("READ_ONLY_REPLAY_BLOCKED_NO_ACTION",
                    "work ID, nonce or comment ID already recorded",
                    comment_id=comment_id, work_id=work_id)
    except sqlite3.Error:
        if con is not None:
            con.rollback()
        return _out(_STATUS_DENIED, "local ledger unavailable or corrupt",
                    comment_id=comment_id, work_id=work_id)
    finally:
        if con is not None:
            con.close()
    return _out("READ_ONLY_RECEIPT_RECORDED_NO_ACTION",
                "one local diagnostic receipt recorded; NO execution",
                comment_id=comment_id, work_id=work_id)
