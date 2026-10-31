"""Read-only immutable-Git source-merge size planning for Issue #76.

No network access, no Git writes, no authority to merge, no provider attestation.
Independent author records can disagree with chronological main totals when two
PRs share a base and modify *disjoint* Lua files. Prove exact blob changes from
Git objects, rather than accepting a JSON correction or rewriting history.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

SOURCES = (
    "src/ToyWarsBalance.lua",
    "src/ToyWarsServer.server.lua",
    "src/ToyWarsHUD.client.lua",
    "src/ToyWarsSmokeTest.server.lua",
)
SHA = re.compile(r"[0-9a-f]{40}\Z")
_DENY = {"merge_allowed": False, "dispatch_allowed": False,
         "publish_allowed": False, "external_spend_allowed": False}


class SourceLedgerRejected(ValueError):
    pass


def _need(value, why):
    if not value:
        raise SourceLedgerRejected(why)


class ReadOnlyGit:
    def __init__(self, root):
        self.root = Path(root).resolve()
        _need((self.root / ".git").exists(), "MISSING_GIT_REPOSITORY")

    def git(self, *args):
        try:
            call = subprocess.run(["git", *args], cwd=self.root,
                                  capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SourceLedgerRejected("GIT_UNAVAILABLE") from exc
        _need(call.returncode == 0, "GIT_EVIDENCE_UNAVAILABLE")
        return call.stdout

    def commit(self, oid):
        _need(type(oid) is str and SHA.fullmatch(oid), "INVALID_COMMIT_ID")
        _need(self.git("cat-file", "-t", oid).strip() == b"commit", "NOT_COMMIT")
        _need(self.git("rev-parse", "--verify", oid + "^{commit}").decode().strip() == oid,
              "NONCANONICAL_COMMIT")
        return oid

    def ancestor(self, earlier, later):
        try:
            p = subprocess.run(["git", "merge-base", "--is-ancestor", earlier, later],
                               cwd=self.root, capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SourceLedgerRejected("GIT_UNAVAILABLE") from exc
        _need(p.returncode in (0, 1), "GIT_ANCESTRY_ERROR")
        return p.returncode == 0

    def main_head(self):
        return self.commit(self.git("rev-parse", "--verify",
                                    "refs/heads/main").decode().strip())

    def snapshot(self, commit):
        raw = self.git("ls-tree", "-r", "-z", commit, "--", "src/")
        files = {}
        for record in raw.split(b"\0"):
            if not record:
                continue
            try:
                header, path_bytes = record.split(b"\t", 1)
                mode, kind, blob = header.split(b" ")
                path = path_bytes.decode("utf-8", "strict")
                oid = blob.decode("ascii", "strict")
            except (ValueError, UnicodeDecodeError):
                raise SourceLedgerRejected("INVALID_TREE") from None
            _need(path not in files and path in SOURCES and
                  mode == b"100644" and kind == b"blob" and
                  SHA.fullmatch(oid), "UNEXPECTED_SOURCE_OR_MODE")
            size_text = self.git("cat-file", "-s", oid).decode("ascii", "strict").strip()
            _need(size_text.isdecimal(), "INVALID_GIT_BLOB_SIZE")
            files[path] = {"sha": oid, "bytes": int(size_text)}
        _need(set(files) == set(SOURCES), "CANONICAL_SOURCE_SET_CHANGED")
        return files


def author_ledger_from_git(repo, authored_base_sha, author_head_sha):
    """Construct a candidate record from local Git only; not an attestation."""
    git = ReadOnlyGit(repo)
    base, author = git.commit(authored_base_sha), git.commit(author_head_sha)
    _need(git.ancestor(base, author) and base != author, "NOT_AUTHORED_FROM_BASE")
    old, new = git.snapshot(base), git.snapshot(author)
    changed = [
        {"path": p, "before_sha": old[p]["sha"], "after_sha": new[p]["sha"],
         "before_bytes": old[p]["bytes"], "after_bytes": new[p]["bytes"],
         "delta_bytes": new[p]["bytes"] - old[p]["bytes"]}
        for p in SOURCES if old[p]["sha"] != new[p]["sha"]
    ]
    _need(changed, "NO_SOURCE_CHANGE")
    return {"schema": 1, "authored_base_sha": base, "author_head_sha": author,
            "source_metrics_lua_bytes": sum(v["bytes"] for v in new.values()),
            "changes": changed}


def plan_source_merge(repo, authored_base_sha, author_head_sha, main_sha, author_ledger):
    """Compare exact source blobs in base, author and current main.

    Even success is ONLY a non-authorizing size forecast. Test/installer/history
    conflicts, GitHub CI and independent reviewer provenance are out of scope.
    """
    git = ReadOnlyGit(repo)
    base, author, main = (git.commit(v) for v in
                          (authored_base_sha, author_head_sha, main_sha))
    _need(git.main_head() == main, "STALE_MAIN_REF")
    _need(base != author and git.ancestor(base, author), "WRONG_AUTHOR_ANCESTRY")
    _need(git.ancestor(base, main), "WRONG_MAIN_ANCESTRY")
    _need(not git.ancestor(author, main), "AUTHOR_ALREADY_IN_MAIN")
    baseline, authored, current = (git.snapshot(c) for c in (base, author, main))
    author_changed = {p for p in SOURCES if baseline[p]["sha"] != authored[p]["sha"]}
    main_changed = {p for p in SOURCES if baseline[p]["sha"] != current[p]["sha"]}
    _need(author_changed, "NO_SOURCE_CHANGE")
    _need(not (author_changed & main_changed), "SAME_SOURCE_FILE_CHANGED")
    _need(type(author_ledger) is dict and
          set(author_ledger) == {"schema", "authored_base_sha", "author_head_sha",
                                 "source_metrics_lua_bytes", "changes"} and
          type(author_ledger["schema"]) is int and author_ledger["schema"] == 1 and
          author_ledger["authored_base_sha"] == base and
          author_ledger["author_head_sha"] == author,
          "INVALID_AUTHOR_LEDGER")
    expected = author_ledger_from_git(repo, base, author)
    _need(author_ledger == expected, "AUTHOR_BLOB_OR_METRIC_MISMATCH")
    # A second read fences a local refs/heads/main change during this query.
    _need(git.main_head() == main, "MAIN_REF_MOVED_DURING_OBSERVATION")
    merged = {p: authored[p] if p in author_changed else current[p] for p in SOURCES}
    current_bytes = sum(v["bytes"] for v in current.values())
    proposed_bytes = sum(v["bytes"] for v in merged.values())
    authored_bytes = sum(v["bytes"] for v in authored.values())
    return {
        "schema": 1, "verification": "LOCAL_GIT_OBJECT_CONSISTENCY_ONLY",
        "repository_root": str(git.root), "authored_base_sha": base,
        "author_head_sha": author, "observed_main_sha": main,
        "source_paths": list(SOURCES),
        "author_changed_paths": sorted(author_changed),
        "intervening_main_changed_paths": sorted(main_changed),
        "source_blob_reconciliation": merged,
        "author_base_local_bytes": authored_bytes,
        "observed_main_bytes": current_bytes,
        "candidate_post_merge_bytes": proposed_bytes,
        "delta_bytes": proposed_bytes - current_bytes,
        "source_only_commutativity": True,
        "exact_full_diff_checked": False, "history_id_reserved": False,
        "qa_verified": False, "independent_review_verified": False,
        "provider_origin_verified": False,
        "authority": dict(_DENY),
    }
