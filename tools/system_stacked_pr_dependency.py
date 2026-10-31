"""Fail-closed read-only topology advisory for stacked, same-repository PRs.

Checks parent branch identity and exact source SHA in a caller-provided snapshot.
No GitHub API client, credentials, write, reviewer override, or merge decision.
The caller must authenticate live provenance and verify ancestry independently.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import re

_SHA = re.compile(r"[0-9a-f]{40}")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,160}")


class UnsafeSnapshot(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise UnsafeSnapshot(reason)


def _sha(value):
    require(type(value) is str and _SHA.fullmatch(value) is not None, "invalid commit SHA")
    return value


def _repo(value):
    require(type(value) is str and _REPO.fullmatch(value) is not None
            and not value.endswith(".git") and ".." not in value,
            "invalid repository identity")
    return value


def _ref(value):
    require(type(value) is str and _REF.fullmatch(value) is not None
            and "//" not in value and ".." not in value
            and not value.endswith(("/", ".lock", "."))
            and not value.startswith("refs/"), "unsafe branch ref")
    return value


def _time(value):
    require(type(value) is str, "missing snapshot time")
    try:
        at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise UnsafeSnapshot("invalid snapshot time") from None
    require(at.tzinfo is not None, "snapshot needs timezone")
    return at


def _number(value):
    require(type(value) is int and value > 0, "invalid PR number")
    return value


def _result(status, **extra):
    return {"status": status, "mode": "READ_ONLY_STACK_TOPOLOGY",
            "provider_verified": False, "may_write": False,
            "may_merge": False, "may_rebase": False,
            "may_mark_ready": False, "may_skip_independent_review": False,
            **extra}


def evaluate(snapshot):
    """Derive an advisory order; even a MAIN_BASE result is not merge approval."""
    try:
        require(type(snapshot) is dict and set(snapshot) == {
            "repository", "default_branch", "default_head", "observed_at", "pulls"
        }, "invalid snapshot keys")
        repo = _repo(snapshot["repository"])
        default = _ref(snapshot["default_branch"])
        default_head = _sha(snapshot["default_head"])
        _time(snapshot["observed_at"])
        pulls = snapshot["pulls"]
        require(type(pulls) is list and len(pulls) <= 300, "invalid open PR inventory")
        nodes, ref_to_pr = {}, {}
        required = {"number", "state", "draft", "head_repo", "head_ref",
                    "head_sha", "base_repo", "base_ref", "base_sha"}
        for pr in pulls:
            require(type(pr) is dict and set(pr) == required, "invalid PR fields")
            number = _number(pr["number"])
            require(pr["state"] == "open" and type(pr["draft"]) is bool,
                    "unconfirmed open state or draft flag")
            require(_repo(pr["head_repo"]) == repo and
                    _repo(pr["base_repo"]) == repo,
                    "cross-repository PR outside same-repo gate")
            head_ref, base_ref = _ref(pr["head_ref"]), _ref(pr["base_ref"])
            require(head_ref != default and base_ref != head_ref,
                    "invalid self/default branch dependency")
            _sha(pr["head_sha"])
            _sha(pr["base_sha"])
            require(number not in nodes and head_ref not in ref_to_pr,
                    "duplicate PR number or ambiguous head ref")
            nodes[number] = pr
            ref_to_pr[head_ref] = number

        parent = {
            n: (ref_to_pr.get(pr["base_ref"]) if pr["base_ref"] != default else None)
            for n, pr in nodes.items()
        }
        visiting, ordered = {}, []

        def visit(n):
            if visiting.get(n) == 1:
                raise UnsafeSnapshot("dependency cycle in open PR graph")
            if visiting.get(n) == 2:
                return
            visiting[n] = 1
            p = parent[n]
            if p is not None:
                visit(p)
            visiting[n] = 2
            ordered.append(n)

        for n in sorted(nodes):
            visit(n)

        depths, states = {}, {}
        items = []
        for n in ordered:
            pr = nodes[n]
            dep = parent[n]
            if pr["base_ref"] == default:
                depth = 0
                status = ("MAIN_BASE_REVIEW_ONLY" if pr["base_sha"] == default_head
                          else "WAIT_STALE_DEFAULT_BASE")
            elif dep is None:
                depth = None
                status = "WAIT_UNTRACKED_BASE"
            else:
                depth = None if depths[dep] is None else depths[dep] + 1
                if pr["base_sha"] != nodes[dep]["head_sha"]:
                    status = "WAIT_PARENT_HEAD_MISMATCH"
                elif states[dep] not in {"MAIN_BASE_REVIEW_ONLY", "WAIT_OPEN_PARENT"}:
                    status = "WAIT_ANCESTOR_UNRESOLVED"
                else:
                    status = "WAIT_OPEN_PARENT"
            depths[n], states[n] = depth, status
            items.append({"number": n, "head_ref": pr["head_ref"],
                          "head_sha": pr["head_sha"], "base_ref": pr["base_ref"],
                          "depends_on_pr": dep, "depth": depth, "status": status,
                          "draft": pr["draft"], "requires_independent_review": True})
        main_candidates = [x["number"] for x in items
                           if x["status"] == "MAIN_BASE_REVIEW_ONLY"]
        return _result("ADVISORY_READY" if items else "EMPTY_INVENTORY",
                       repository=repo, default_head=default_head,
                       dependency_order=[x["number"] for x in items],
                       main_review_candidates=main_candidates,
                       total_open_prs=len(items), items=items,
                       warning="Branch topology and caller-supplied head/base SHAs are "
                               "not ancestry, CI, rights, safety, or merge approval.")
    except (UnsafeSnapshot, TypeError, KeyError, AttributeError, OverflowError,
            RecursionError) as exc:
        return _result("WAIT_METADATA", reason=str(exc))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as handle:
        snapshot = json.load(handle)
    print(json.dumps(evaluate(snapshot), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
