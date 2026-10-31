"""Advisory-only overlapping PR path guard for parallel development.

Inputs MUST be collected from authenticated GitHub PR/file-list APIs by the
caller, including all pages and rename old paths. This module cannot prove
input provenance or grant a lease, CI approval, merge, or writing authority.
"""
import argparse
import json
from pathlib import PurePosixPath
import re
import sys
import unicodedata

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _sha(value):
    _require(isinstance(value, str) and _HEX40.fullmatch(value), "invalid sha")


def _path(value):
    _require(isinstance(value, str) and 0 < len(value) <= 512, "invalid path")
    _require(not (value.startswith("/") or value.endswith("/") or "\\" in value or "\x00" in value),
             "unsafe path")
    _require(all(c not in ("", ".", "..") for c in value.split("/")), "traversing path")
    _require(str(PurePosixPath(value)) == value, "unnormalized path")
    return value


def _canonical(value):
    return unicodedata.normalize("NFC", _path(value)).casefold()


def audit(snapshot):
    """Return evidence-collision warnings; even CLEAR is NOT execution approval.

    ``collection_complete`` is a caller assertion, not an authenticated fact.
    Never use this reducer itself to authorize or prevent a GitHub mutation.
    """
    _require(type(snapshot) is dict and set(snapshot) ==
             {"schema", "repository", "base_sha", "collection_complete", "candidate", "pulls"},
             "invalid envelope")
    _require(type(snapshot["schema"]) is int and snapshot["schema"] == 1, "invalid schema")
    repo = snapshot["repository"]
    _require(isinstance(repo, str) and _REPO.fullmatch(repo), "invalid repository")
    _sha(snapshot["base_sha"])
    _require(snapshot["collection_complete"] is True, "partial PR discovery")
    candidate = snapshot["candidate"]
    _require(type(candidate) is dict and set(candidate) == {"branch", "paths"}, "invalid candidate")
    _require(isinstance(candidate["branch"], str) and
             re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,180}", candidate["branch"]) and
             ".." not in candidate["branch"], "invalid branch")
    paths = candidate["paths"]
    _require(type(paths) is list and len(paths) > 0, "missing candidate paths")
    proposed = {}
    for path in paths:
        key = _canonical(path)
        _require(key not in proposed, "candidate duplicate/case-fold path")
        proposed[key] = path

    pulls = snapshot["pulls"]
    _require(type(pulls) is list, "missing PR inventory")
    observed = set()
    collisions = []
    stacked_prs_checked = 0
    for pr in pulls:
        _require(type(pr) is dict and set(pr) ==
                 {"number", "repository", "base_branch", "state", "head_sha", "paths"},
                 "invalid PR record")
        n = pr["number"]
        _require(type(n) is int and n > 0 and n not in observed, "duplicate/invalid PR number")
        observed.add(n)
        # Stacked PRs deliberately target another same-repo branch. They still
        # touch files and must remain visible to other concurrent authors.
        # Treat their overlap as advisory, not evidence of an invalid PR.
        base_branch = pr["base_branch"]
        _require(isinstance(base_branch, str) and
                 re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,180}", base_branch) and
                 not base_branch.endswith("/") and ".." not in base_branch and
                 "//" not in base_branch, "invalid PR base branch")
        _require(pr["repository"] == repo and pr["state"] == "open",
                 "wrong repo or closed PR")
        stacked_prs_checked += base_branch != "main"
        _sha(pr["head_sha"])
        _require(type(pr["paths"]) is list and len(pr["paths"]) > 0,
                 "missing PR path page")
        seen = set()
        for old_or_new in pr["paths"]:
            key = _canonical(old_or_new)
            _require(key not in seen, "duplicate PR file path")
            seen.add(key)
            if key in proposed:
                collisions.append({"pr": n, "candidate_path": proposed[key],
                                   "existing_path": old_or_new,
                                   "base_branch": base_branch, "stacked": base_branch != "main",
                                   "kind": "EXACT" if old_or_new == proposed[key] else "CASE_OR_UNICODE"})
    collisions.sort(key=lambda x: (x["pr"], x["candidate_path"], x["existing_path"]))
    return {"decision": "BLOCK_OVERLAP" if collisions else "CLEAR_ADVISORY",
            "grant_write_authority": False,
            "source_authenticated": False,
            "checked_open_prs": len(pulls),
            "main_prs_checked": len(pulls) - stacked_prs_checked,
            "stacked_prs_checked": stacked_prs_checked,
            "candidate_paths": len(paths),
            "collisions": collisions,
            "warning": "Input authenticity, pagination, head freshness and lease ownership require external checks"}



def from_rest_observations(*, repository, main_before_sha, main_after_sha,
                           candidate, prs_before, prs_after, changed_files_by_pr):
    """Convert *complete single-page* GitHub REST observations to the advisory schema.

    No network operations or trust attestation: the caller must obtain each
    response through an authenticated provider connection and immediately
    recheck open PR numbers/heads/bases and the actual main SHA. A full GitHub
    page of 100 is deliberately rejected rather than silently truncating.
    Changed-file pages with >=100 items likewise require a different collector.
    """
    _require(isinstance(repository, str) and _REPO.fullmatch(repository),
             "invalid repository")
    _sha(main_before_sha)
    _sha(main_after_sha)
    _require(main_before_sha == main_after_sha, "main advanced during PR scan")
    _require(type(prs_before) is list and type(prs_after) is list and
             len(prs_before) < 100 and len(prs_after) < 100,
             "incomplete PR listing; pagination required")
    _require(type(changed_files_by_pr) is dict, "missing changed-file listing")

    def parse_prs(rows):
        normalized = {}
        for row in rows:
            _require(type(row) is dict, "invalid PR metadata")
            number = row.get("number")
            _require(type(number) is int and number > 0 and number not in normalized,
                     "duplicate/invalid PR number")
            head, base = row.get("head"), row.get("base")
            _require(type(head) is dict and type(base) is dict and
                     type(head.get("repo")) is dict and type(base.get("repo")) is dict,
                     "missing authenticated PR lineage metadata")
            _require(head["repo"].get("full_name") == repository and
                     base["repo"].get("full_name") == repository,
                     "foreign PR repository")
            _require(row.get("state") == "open", "closed PR in open PR inventory")
            _sha(head.get("sha"))
            branch = base.get("ref")
            _require(isinstance(branch, str) and
                     re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,180}", branch) and
                     not branch.endswith("/") and ".." not in branch and "//" not in branch,
                     "invalid stacked PR base")
            normalized[number] = (head["sha"], branch)
        return normalized

    before, after = parse_prs(prs_before), parse_prs(prs_after)
    _require(before == after, "PR list/heads/bases changed during collection")
    _require(set(changed_files_by_pr) == {str(n) for n in before},
             "missing or unexpected changed-file page")
    pulls = []
    for number in sorted(before):
        head_sha, base_ref = before[number]
        files = changed_files_by_pr[str(number)]
        _require(type(files) is list and 0 < len(files) < 100,
                 "missing or truncated changed-file page; pagination required")
        unique, paths = set(), []
        for file in files:
            _require(type(file) is dict and type(file.get("filename")) is str and
                     type(file.get("status")) is str,
                     "invalid GitHub file metadata")
            status = file["status"]
            _require(status in {"added", "removed", "modified", "renamed", "copied",
                                "changed", "unchanged"}, "unknown changed-file status")
            names = [file["filename"]]
            if status == "renamed":
                _require(type(file.get("previous_filename")) is str,
                         "rename without previous_filename")
                names.append(file["previous_filename"])
            else:
                _require("previous_filename" not in file,
                         "unexpected previous_filename without rename")
            # A case-only rename may map both names to the same canonical path.
            # That repetition is valid only *within one* observed rename record.
            local = set()
            for name in names:
                key = _canonical(name)
                if key not in local:
                    _require(key not in unique, "two GitHub file records alias one path")
                    unique.add(key)
                    paths.append(name)
                    local.add(key)
        pulls.append({"number": number, "repository": repository,
                      "base_branch": base_ref, "state": "open",
                      "head_sha": head_sha, "paths": paths})
    snapshot = {"schema": 1, "repository": repository,
                "base_sha": main_before_sha, "collection_complete": True,
                "candidate": candidate, "pulls": pulls}
    # Validate all reducer invariants before returning a mechanically complete
    # *but unauthenticated* snapshot. Even CLEAR_ADVISORY grants no right to edit.
    audit(snapshot)
    return snapshot

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="GitHub-observed PR path snapshot JSON")
    args = parser.parse_args()
    try:
        with open(args.input, encoding="utf-8") as handle:
            result = audit(json.load(handle))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "WAIT_METADATA", "grant_write_authority": False,
                          "reason": str(exc)}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if result["collisions"] else 0


if __name__ == "__main__":
    sys.exit(main())
