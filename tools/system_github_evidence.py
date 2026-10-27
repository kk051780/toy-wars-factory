"""Scoped GitHub GET collection. No credentials, network client or write capability.

The host supplies its connected read-only GET capability. Response validation is
NOT authentication of that capability: fixtures and the stdio bridge remain
NOT_VERIFIED. Only an external host trace of actual connector calls can attest
LIVE_PROVIDER_VERIFIED, for that execution, never for a replayed JSON document.
"""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from studio_autopilot import core, scheduler
from tools import system_host_write_triage as triage

SHA = re.compile(r"[0-9a-f]{40}\Z")
UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
BINDING = {"game_id", "manifest_path", "main_sha", "coordinator_sha",
           "coordinator_blob_sha", "coordinator_epoch", "pr_number",
           "pr_head_sha", "pr_base_sha", "author_role", "author_run_id",
           "ci_run_id", "ci_attempt", "workflow_file", "workflow_id"}
DENIED = {k: False for k in ("write_allowed", "dispatch_allowed", "merge_allowed",
                            "publish_allowed", "external_spend_allowed")}


class EvidenceError(ValueError):
    """Contains a fixed safe code, never a provider body or exception message."""


def need(condition, code):
    if not condition:
        raise EvidenceError(code)


def integer(value, minimum=1):
    return type(value) is int and minimum <= value <= 2**63 - 1


def unique(pairs):
    out = {}
    for key, value in pairs:
        need(key not in out, "DUPLICATE_JSON_FIELD")
        out[key] = value
    return out


def loads(text):
    need(type(text) is str and len(text.encode()) <= 2_000_000, "INVALID_RESPONSE")
    try:
        return json.loads(text, object_pairs_hook=unique,
                          parse_constant=lambda _: need(False, "NONFINITE_JSON"))
    except (ValueError, TypeError, RecursionError) as exc:
        if isinstance(exc, EvidenceError):
            raise
        raise EvidenceError("INVALID_JSON") from None


def moment(value):
    try:
        need(type(value) is str, "INVALID_TIMESTAMP")
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        need(dt.tzinfo is not None, "INVALID_TIMESTAMP")
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        raise EvidenceError("INVALID_TIMESTAMP") from None


def sha(value):
    need(type(value) is str and SHA.fullmatch(value), "INVALID_SHA")
    return value


@dataclass(frozen=True)
class Response:
    status: int
    text: str


class Reader:
    def __init__(self, repository, get, clock):
        self.prefix = "https://api.github.com/repos/" + repository
        self.get, self.clock, self.trace = get, clock, []
        self.started = moment(clock())

    def read(self, path, *, raw=False):
        # All paths originate in this module, never in a response URL or PR body.
        compare = re.fullmatch(r"/compare/[0-9a-f]{40}[.]{3}[0-9a-f]{40}", path)
        need((path == "" or path.startswith("/")) and
             (".." not in path or compare) and "\\" not in path,
             "UNSCOPED_GET")
        url = self.prefix + path
        at = moment(self.clock())
        need(self.started <= at and (at - self.started).total_seconds() <= 120,
             "OBSERVATION_WINDOW_EXCEEDED")
        try:
            response = self.get(url)
        except Exception:
            raise EvidenceError("GET_UNAVAILABLE") from None
        finished = moment(self.clock())
        need(at <= finished and (finished-self.started).total_seconds() <= 120,
             "OBSERVATION_WINDOW_EXCEEDED")
        need(type(response) is Response and type(response.status) is int and
             response.status == 200, "GET_REJECTED")
        body = response.text
        need(type(body) is str and len(body.encode()) <= 2_000_000, "INVALID_RESPONSE")
        self.trace.append({"method": "GET", "url": url, "observed_at": at.isoformat(),
                           "body_sha256": hashlib.sha256(body.encode()).hexdigest()})
        return body if raw else loads(body)

    def ref(self, branch, expected):
        value = self.read("/git/ref/heads/" + branch)
        need(value.get("ref") == "refs/heads/" + branch and
             value.get("object", {}).get("type") == "commit" and
             value["object"].get("sha") == expected, "REF_MOVED_OR_FOREIGN")
        return expected

    def tree(self, commit):
        obj = self.read("/git/commits/" + sha(commit))
        need(obj.get("sha") == commit, "WRONG_COMMIT")
        tree_sha = sha(obj.get("tree", {}).get("sha"))
        tree = self.read("/git/trees/" + tree_sha + "?recursive=1")
        need(tree.get("sha") == tree_sha and tree.get("truncated") is False and
             type(tree.get("tree")) is list, "INCOMPLETE_TREE")
        paths = {}
        for entry in tree["tree"]:
            path = entry.get("path")
            need(type(path) is str and path not in paths, "DUPLICATE_TREE_PATH")
            paths[path] = entry
        return paths

    def blob(self, tree, path, expected=None):
        item = tree.get(path, {})
        need(item.get("mode") == "100644" and item.get("type") == "blob",
             "NOT_ORDINARY_BLOB")
        digest = sha(item.get("sha"))
        need(expected is None or digest == expected, "WRONG_BLOB")
        raw = self.read("/git/blobs/" + digest, raw=True)
        data = raw.encode()
        # The connected GitHub fetch tool decodes blobs. Standard REST clients
        # may instead return the documented base64 envelope. Verify either by
        # the immutable Git object ID, never by a provider label.
        def git_hash(b):
            return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        if git_hash(data) != digest:
            envelope = loads(raw)
            need(type(envelope) is dict and envelope.get("sha") == digest and
                 envelope.get("encoding") == "base64", "BLOB_HASH_MISMATCH")
            try:
                data = base64.b64decode("".join(envelope["content"].split()), validate=True)
            except (ValueError, KeyError, TypeError):
                raise EvidenceError("BLOB_HASH_MISMATCH") from None
        need(git_hash(data) == digest, "BLOB_HASH_MISMATCH")
        try:
            return loads(data.decode("utf-8"))
        except UnicodeError:
            raise EvidenceError("INVALID_BLOB_ENCODING") from None


def _run(reader, run, workflow_id, head, branch, now, *, pr=None, base=None):
    repo = reader.prefix.rsplit("/repos/", 1)[1]
    need(type(run) is dict and integer(run.get("id")) and integer(run.get("run_attempt")),
         "INVALID_RUN")
    need(type(run.get("workflow_id")) is int and run.get("workflow_id") == workflow_id and run.get("head_sha") == head and
         run.get("head_branch") == branch and
         run.get("repository", {}).get("full_name") == repo and
         run.get("head_repository", {}).get("full_name") == repo and
         run["head_repository"].get("fork") is False, "FOREIGN_OR_STALE_RUN")
    need(moment(run["created_at"]) <= moment(run["updated_at"]) <= now,
         "OUT_OF_ORDER_RUN")
    need(run.get("status") in ("queued", "in_progress", "completed"), "INVALID_RUN_STATUS")
    conclusions = ("success", "failure", "neutral", "cancelled", "skipped", "timed_out",
                   "action_required", "stale", "startup_failure")
    need((run["status"] == "completed" and run.get("conclusion") in conclusions) or
         (run["status"] != "completed" and run.get("conclusion") is None), "INVALID_RUN_CONCLUSION")
    if pr is not None:
        matches = run.get("pull_requests")
        need(run.get("event") == "pull_request" and type(matches) is list and len(matches) == 1,
             "PR_RUN_BINDING_MISSING")
        binding = matches[0]
        need(type(binding.get("number")) is int and binding.get("number") == pr and binding.get("head", {}).get("sha") == head and
             binding.get("base", {}).get("sha") == base, "WRONG_PR_RUN_BASE")
    else:
        need(run.get("event") == "push", "WRONG_MAIN_EVENT")
    jobs = reader.read(f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs?per_page=100")
    need(type(jobs) is dict and jobs.get("total_count") == 2 and
         type(jobs.get("jobs")) is list and len(jobs["jobs"]) == 2, "MISSING_OR_EXTRA_JOB")
    seen, names = set(), set()
    for job in jobs["jobs"]:
        need(integer(job.get("id")) and job["id"] not in seen and
             job.get("name") in ("offline", "compile_hold") and job["name"] not in names,
             "DUPLICATE_OR_WRONG_JOB")
        seen.add(job["id"])
        names.add(job["name"])
        need(type(job.get("run_id")) is int and type(job.get("run_attempt")) is int and
             job.get("run_id") == run["id"] and job.get("run_attempt") == run["run_attempt"] and
             job.get("head_sha") == head, "WRONG_JOB_BINDING")
        need(job.get("status") in ("queued", "in_progress", "completed") and
             ((job["status"] == "completed" and job.get("conclusion") in conclusions) or
              (job["status"] != "completed" and job.get("conclusion") is None)), "INVALID_JOB_STATUS")
        if job.get("status") == "completed":
            need(moment(run["created_at"]) <= moment(job["started_at"]) <=
                 moment(job["completed_at"]) <= moment(run["updated_at"]) <= now, "OUT_OF_ORDER_JOB")
    if run["status"] != "completed":
        verdict = "PENDING"
    else:
        verdict = "PASS" if run.get("conclusion") == "success" and all(
            j.get("status") == "completed" and j.get("conclusion") == "success"
            for j in jobs["jobs"]) else "FAIL"
    return {"id": run["id"], "attempt": run["run_attempt"], "head": head,
            "created_at": run["created_at"], "updated_at": run["updated_at"],
            "status": run["status"], "conclusion": run.get("conclusion"), "qa": verdict,
            "jobs": [{k: j.get(k) for k in ("id", "name", "run_id", "run_attempt",
                       "head_sha", "status", "conclusion")} for j in jobs["jobs"]]}


def _latest(reader, workflow_file, workflow_id, query):
    rows = reader.read("/actions/runs?" + query + "&per_page=100")
    need(type(rows) is dict and type(rows.get("workflow_runs")) is list and
         integer(rows.get("total_count")) and 1 <= len(rows["workflow_runs"]) <= 100,
         "MISSING_RUN")
    runs = rows["workflow_runs"]
    need(len({r.get("id") for r in runs}) == len(runs), "DUPLICATE_RUN")
    need(all(moment(runs[i]["created_at"]) >= moment(runs[i+1]["created_at"])
             for i in range(len(runs)-1)), "OUT_OF_ORDER_RUN_LIST")
    selected = [r for r in runs if r.get("path") == ".github/workflows/" + workflow_file]
    need(selected and selected[0].get("workflow_id") == workflow_id, "WRONG_WORKFLOW")
    return selected[0]


def collect(projects, binding, get, clock):
    """Run scoped GETs; output is advisory and never a portable origin receipt.

    `projects` and pins come from the trusted host's selection. The manifest is
    reloaded from the pinned real main and matched against that selection. A
    malicious transport can forge even a self-consistent Git DAG: no boolean,
    stdout JSON, callback class name or caller assertion upgrades authentication.
    """
    try:
        return _collect(projects, binding, get, clock)
    except EvidenceError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, IndexError, OverflowError):
        raise EvidenceError("MALFORMED_EVIDENCE") from None


def _collect(projects, b, get, clock):
    need(type(b) is dict and set(b) == BINDING, "INVALID_BINDING")
    games = scheduler._validated_games(deepcopy(projects))
    chosen = [g for g in games if g["game_id"] == b["game_id"]]
    need(len(chosen) == 1, "UNKNOWN_PROJECT")
    project = chosen[0]
    for key in ("main_sha", "coordinator_sha", "coordinator_blob_sha", "pr_head_sha", "pr_base_sha"):
        sha(b[key])
    need(all(integer(b[k]) for k in ("pr_number", "ci_run_id", "ci_attempt", "workflow_id")) and
         integer(b["coordinator_epoch"], 0), "INVALID_NUMERIC_BINDING")
    need(b["author_role"] in ("author", "meta") and type(b["author_run_id"]) is str and
         UUID.fullmatch(b["author_run_id"]), "INVALID_AUTHOR_BINDING")
    need(type(b["manifest_path"]) is str and re.fullmatch(
        r"studio_autopilot/projects/[A-Za-z0-9_]+[.]json", b["manifest_path"]), "INVALID_MANIFEST_PATH")
    need(type(b["workflow_file"]) is str and re.fullmatch(
        r"[A-Za-z0-9_-]+[.]yml", b["workflow_file"]), "INVALID_WORKFLOW_PATH")
    reader = Reader(project["repository"], get, clock)
    now = reader.started
    repo = reader.read("")
    need(repo.get("full_name") == project["repository"] and repo.get("fork") is False,
         "FOREIGN_REPOSITORY")
    reader.ref("main", b["main_sha"])
    reader.ref(project["coordination_ref"], b["coordinator_sha"])
    main_tree = reader.tree(b["main_sha"])
    need(reader.blob(main_tree, b["manifest_path"]) == project, "MANIFEST_NOT_BOUND_TO_MAIN")
    policy = reader.blob(main_tree, "config/autonomous_repair.json")
    expected_roles = {"WORKER": project["roles"]["author"], "META": project["roles"]["meta"],
                      "REVIEWER": project["roles"]["reviewer"]}
    need(policy.get("repository") == project["repository"] and policy.get("queue_version", 0) >= 4 and
         policy.get("task_id") == expected_roles["WORKER"] and
         policy.get("system_review", {}).get("task_id") == expected_roles["META"] and
         policy.get("integration", {}).get("task_id") == expected_roles["REVIEWER"], "ROLE_POLICY_MISMATCH")
    coord_tree = reader.tree(b["coordinator_sha"])
    state = reader.blob(coord_tree, "ops/REPAIR_COORDINATOR.json", b["coordinator_blob_sha"])
    need(state.get("schema") == 1 and state.get("authorized_tasks") == expected_roles and
         state.get("task_id") == expected_roles["WORKER"] and
         type(state.get("epoch")) is int and state["epoch"] == b["coordinator_epoch"], "WRONG_EPOCH_OR_ROLE")
    holder = state.get("holder")
    if holder is not None:
        need(type(holder) is dict and holder.get("epoch") == state["epoch"] and
             type(holder.get("owner_id")) is str and UUID.fullmatch(holder["owner_id"]) and
             holder.get("kind") in ("META", "WORKER", "REVIEWER", "DISPATCH", "CONTROLLER") and
             moment(holder["acquired_at"]) < moment(holder["expires_at"]), "INVALID_HOLDER")
        if holder["kind"] in expected_roles:
            need(holder.get("task_id") == expected_roles[holder["kind"]], "HOLDER_WRONG_TASK")
    pr = reader.read(f"/pulls/{b['pr_number']}")
    def pr_identity(p):
        return {"number": p.get("number"), "state": p.get("state"), "merged": p.get("merged"),
                "head": p.get("head"), "base": p.get("base")}
    need(type(pr.get("number")) is int and pr.get("number") == b["pr_number"] and pr.get("state") == "open" and
         pr.get("merged") is False, "CLOSED_OR_WRONG_PR")
    for side, expected in (("head", b["pr_head_sha"]), ("base", b["pr_base_sha"])):
        obj = pr.get(side, {})
        need(obj.get("sha") == expected and obj.get("repo", {}).get("full_name") ==
             project["repository"] and obj["repo"].get("fork") is False, "FOREIGN_OR_STALE_PR")
    need(pr["base"].get("ref") == "main" and b["pr_base_sha"] == b["main_sha"], "STALE_PR_BASE")
    prefix = (policy["system_review"]["branch_prefix"] if b["author_role"] == "meta"
              else policy["branch_prefix"])
    need(type(prefix) is str and pr["head"].get("ref") == prefix + b["author_run_id"], "WRONG_AUTHOR_RUN")
    workflow = main_tree.get(".github/workflows/" + b["workflow_file"], {})
    need(workflow.get("mode") == "100644" and workflow.get("type") == "blob",
         "WRONG_WORKFLOW")
    workflow_blob = sha(workflow.get("sha"))
    query = "head_sha=" + b["pr_head_sha"] + "&event=pull_request"
    run = _latest(reader, b["workflow_file"], b["workflow_id"], query)
    need(run.get("id") == b["ci_run_id"] and run.get("run_attempt") == b["ci_attempt"], "STALE_RUN_OR_ATTEMPT")
    exact = reader.read(f"/actions/runs/{b['ci_run_id']}")
    need(exact == run, "RUN_CHANGED_DURING_READ")
    pr_ci = _run(reader, run, b["workflow_id"], b["pr_head_sha"], pr["head"]["ref"], now,
                 pr=b["pr_number"], base=b["pr_base_sha"])
    main_run = _latest(reader, b["workflow_file"], b["workflow_id"], "branch=main&event=push")
    main_sha = sha(main_run.get("head_sha"))
    main_ci = _run(reader, main_run, b["workflow_id"], main_sha, "main", now)
    status_only = []
    if main_sha != b["main_sha"]:
        cmp = reader.read("/compare/" + main_sha + "..." + b["main_sha"])
        files = cmp.get("files")
        need(cmp.get("status") == "ahead" and cmp.get("behind_by") == 0 and
             type(files) is list and 1 <= len(files) <= 2 and
             cmp.get("base_commit", {}).get("sha") == main_sha and
             cmp.get("merge_base_commit", {}).get("sha") == main_sha, "UNPROVEN_MAIN_DESCENDANT")
        status_only = [f.get("filename") for f in files]
        need(len(set(status_only)) == len(status_only) and set(status_only) <=
             {"status/CHAT_HANDOFF.md", "status/LATEST_STATE.json"} and
             all(f.get("status") == "modified" for f in files), "MAIN_CHANGED_AFTER_QA")
    # A consistent first read is insufficient: reject drift, retries or PR closure.
    reader.ref("main", b["main_sha"])
    reader.ref(project["coordination_ref"], b["coordinator_sha"])
    need(pr_identity(reader.read(f"/pulls/{b['pr_number']}")) == pr_identity(pr), "PR_MOVED_DURING_READ")
    need(reader.read(f"/actions/runs/{b['ci_run_id']}") == exact and
         _latest(reader, b["workflow_file"], b["workflow_id"], query) == run and
         _latest(reader, b["workflow_file"], b["workflow_id"], "branch=main&event=push") == main_run, "CI_MOVED_DURING_READ")
    return {"schema": 1, "mode": "ADVISORY_ONLY", "verification": "NOT_VERIFIED",
            "origin": "GET_CAPABILITY_REQUIRES_EXTERNAL_HOST_ATTESTATION",
            "integrity": "SCOPED_GETS_AND_BINDINGS_CHECKED", "game_id": project["game_id"],
            "repository": project["repository"], "observed_at": now.isoformat(),
            "main_sha": b["main_sha"], "main_ci": main_ci, "status_only": status_only,
            "workflow": {"id": b["workflow_id"], "path": ".github/workflows/"+b["workflow_file"],
                         "trusted_main_blob": workflow_blob},
            "coordinator": {"ref_sha": b["coordinator_sha"], "blob_sha": b["coordinator_blob_sha"],
                            "epoch": state["epoch"], "holder": holder},
            "pr": {"number": b["pr_number"], "head": b["pr_head_sha"], "base": b["pr_base_sha"],
                   "branch": pr["head"]["ref"], "state": pr["state"], "ci": pr_ci},
            "trace": reader.trace, "authority": deepcopy(DENIED),
            "service_run_verification": "NOT_COLLECTED"}


def advisory(projects, report, *, cycle=0):
    """Existing real planners consume the observation; all grants remain false."""
    project = next(p for p in projects if p["game_id"] == report["game_id"])
    need(project["repository"] == report["repository"], "FOREIGN_ADVISORY")
    h = report["coordinator"]["holder"]
    obs = {"repository": project["repository"], "main_head": report["main_sha"],
           "main_qa_head": report["main_sha"] if report["status_only"] else report["main_ci"]["head"],
           "main_qa": {"PASS": "success", "FAIL": "failure"}.get(report["main_ci"]["qa"], "pending"),
           "lease": None if h is None else {"kind": h["kind"], "owner_run_id": h["owner_id"], "epoch": h["epoch"]},
           "open_prs": [{"head_sha": report["pr"]["head"], "ci_head_sha": report["pr"]["ci"]["head"],
                         "ci": {"PASS": "success", "FAIL": "failure"}.get(report["pr"]["ci"]["qa"], "pending")}]}
    row = {"repository": project["repository"], "main_sha": obs["main_head"], "qa_sha": obs["main_qa_head"],
           "qa": report["main_ci"]["qa"], "lease_epoch": report["coordinator"]["epoch"],
           "holder": None if h is None else h["owner_id"], "open_prs": 1,
           "last_served_cycle": -1, "live_read_claim": False}
    return {"core": core.evaluate(project, obs), "scheduler": scheduler.propose(
        [project], {project["game_id"]: row}, [{"game_id": project["game_id"],
        "trigger": "repair", "occurrence_key": "github-observation"}], cycle=cycle),
        "triage": triage.result("INDETERMINATE", "SERVICE_AND_OPERATION_EVIDENCE_NOT_COLLECTED"),
        "authority": deepcopy(DENIED)}


def main():
    """Host bridge protocol, NOT a credential or live-origin authentication API."""
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--request", required=True)
        args = parser.parse_args()
        request = loads(Path(args.request).read_text(encoding="utf-8"))
        need(type(request) is dict and set(request) == {"projects", "binding"}, "INVALID_REQUEST")
        def get(url):
            print(json.dumps({"method": "GET", "url": url}), flush=True)
            row = loads(sys.stdin.readline())
            need(type(row) is dict and set(row) == {"status", "body"}, "INVALID_TRANSPORT_RESPONSE")
            return Response(row["status"], row["body"])
        report = collect(request["projects"], request["binding"], get,
                         lambda: datetime.now(timezone.utc).isoformat())
        report["advisory"] = advisory(request["projects"], report)
        print(json.dumps({"result": report}, sort_keys=True), flush=True)
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, EvidenceError) else "INVALID_OR_UNAVAILABLE_EVIDENCE"
        print(json.dumps({"verification": "NOT_VERIFIED", "reason": code,
                          "authority": DENIED}), flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
