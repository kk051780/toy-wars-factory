"""Scoped read-only transport and service-metadata minimization.

This is an in-process input adapter, NOT a sandbox, credential proxy or origin
attestation. A separately trusted host supplies read-only GET/PEEK callbacks and
selects reviewed code/pins. No tokens, writes, task controls or network client.
"""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from tools import system_github_evidence as github
from tools import system_service_observer as service
from tools import system_incident_observer as incident

EvidenceError, need = github.EvidenceError, github.need
DENIED = deepcopy(service.DENIED)


class ReadOnlyTransport:
    """A new instance for one selected project and bounded observation only.

    The underlying host connection remains the actual permission boundary.
    An adversarial in-process caller can bypass a Python object; this class
    deliberately never claims OS isolation or PR55 credential isolation.
    """
    def __init__(self, projects, binding, get, peek, clock):
        need(type(binding) is dict and set(binding) == {"github", "max_record_age_seconds", "max_window_seconds"}, "INVALID_BINDING")
        self.binding = deepcopy(binding)
        b = self.binding["github"]
        need(type(b) is dict and set(b) == github.BINDING, "INVALID_BINDING")
        games = service.scheduler._validated_games(deepcopy(projects))
        selected = [p for p in games if p["game_id"] == b["game_id"]]
        need(len(selected) == 1, "UNKNOWN_PROJECT")
        self.project = selected[0]
        for key in ("main_sha", "coordinator_sha", "coordinator_blob_sha", "pr_head_sha", "pr_base_sha"):
            github.sha(b[key])
        need(all(github.integer(b[k]) for k in ("pr_number", "ci_run_id", "ci_attempt", "workflow_id")) and
             github.integer(b["coordinator_epoch"], 0), "INVALID_BINDING")
        need(b["author_role"] in ("author", "meta") and type(b["author_run_id"]) is str and
             github.UUID.fullmatch(b["author_run_id"]), "INVALID_BINDING")
        need(type(b["manifest_path"]) is str and re.fullmatch(r"studio_autopilot/projects/[A-Za-z0-9_]+[.]json", b["manifest_path"]) and
             type(b["workflow_file"]) is str and re.fullmatch(r"[A-Za-z0-9_-]+[.]yml", b["workflow_file"]), "INVALID_BINDING")
        need(github.integer(binding["max_record_age_seconds"]) and binding["max_record_age_seconds"] <= 172800 and
             github.integer(binding["max_window_seconds"]) and binding["max_window_seconds"] <= 120, "INVALID_BINDING")
        self.prefix = "https://api.github.com/repos/" + self.project["repository"]
        self._get, self._peek, self._clock = get, peek, clock
        self.started = self.previous = github.moment(clock())
        self.closed, self.roles_bound = False, False
        self.calls, self.raw_bytes = 0, 0
        self.trace, self._rules, self._documents, self._seen_refs = [], {}, {}, set()
        self._allow("", ("repository",))
        self._allow("/git/ref/heads/main", ("ref", b["main_sha"]))
        self._allow("/git/ref/heads/" + self.project["coordination_ref"], ("ref", b["coordinator_sha"]))
        for role, sha in (("main", b["main_sha"]), ("coordinator", b["coordinator_sha"])):
            self._allow("/git/commits/" + sha, ("commit", sha, role))
        self._allow("/pulls/" + str(b["pr_number"]), ("pr",))
        self._allow("/actions/runs?head_sha=" + b["pr_head_sha"] + "&event=pull_request&per_page=100", ("pr_runs",))
        self._allow("/actions/runs?branch=main&event=push&per_page=100", ("main_runs",))
        self._allow("/actions/runs/" + str(b["ci_run_id"]), ("run", b["ci_run_id"], b["ci_attempt"], b["pr_head_sha"]))
        self._jobs(b["ci_run_id"], b["ci_attempt"])

    def _allow(self, path, rule):
        need(path not in self._rules or self._rules[path] == rule, "CONTRADICTORY_RESOURCE_GRAPH")
        self._rules[path] = rule

    def _jobs(self, run, attempt):
        self._allow(f"/actions/runs/{run}/attempts/{attempt}/jobs?per_page=100", ("jobs",))

    def clock(self):
        try:
            now = github.moment(self._clock())
            need(not self.closed and self.previous <= now and
                 (now-self.started).total_seconds() <= self.binding["max_window_seconds"], "TRANSPORT_WINDOW_CLOSED")
            self.previous = now
            return now.isoformat()
        except Exception:
            self.closed = True
            raise EvidenceError("READONLY_TRANSPORT_REJECTED") from None

    def _begin(self):
        self.clock()
        need(self.calls < 64, "TRANSPORT_CALL_LIMIT")
        self.calls += 1

    def _consume(self, raw):
        need(type(raw) is str, "INVALID_RESPONSE")
        size = len(raw.encode())
        need(size <= 2_000_000 and self.raw_bytes + size <= 16_000_000, "TRANSPORT_BYTE_LIMIT")
        self.raw_bytes += size
        self.clock()

    def _blob(self, raw, sha):
        data = raw.encode()
        def digest(value):
            return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()
        if digest(data) != sha:
            row = github.loads(raw)
            need(type(row) is dict and row.get("sha") == sha and row.get("encoding") == "base64", "WRONG_BLOB")
            data = base64.b64decode("".join(row["content"].split()), validate=True)
        need(digest(data) == sha, "WRONG_BLOB")
        return github.loads(data.decode("utf-8"))

    def _bind_roles(self):
        if (set(self._documents) != {"manifest", "policy", "coordinator"} or
                self._seen_refs != {"/git/ref/heads/main", "/git/ref/heads/" + self.project["coordination_ref"]}):
            return
        p, policy, state = (self._documents[k] for k in ("manifest", "policy", "coordinator"))
        roles = {kind: self.project["roles"][role] for role, kind in service.ROLES.items()}
        need(p == self.project and policy.get("repository") == self.project["repository"] and
             type(policy.get("queue_version")) is int and policy["queue_version"] >= 4 and
             policy.get("task_id") == roles["WORKER"] and
             policy.get("system_review", {}).get("task_id") == roles["META"] and
             policy.get("integration", {}).get("task_id") == roles["REVIEWER"] and
             type(state.get("schema")) is int and state["schema"] == 1 and
             state.get("task_id") == roles["WORKER"] and state.get("authorized_tasks") == roles and
             type(state.get("epoch")) is int and state["epoch"] == self.binding["github"]["coordinator_epoch"], "UNBOUND_SERVICE_ROLES")
        self.roles_bound = True

    def _learn(self, path, rule, raw):
        b = self.binding["github"]
        if rule[0] == "blob":
            self._documents[rule[2]] = self._blob(raw, rule[1])
            self._bind_roles()
            return
        row = github.loads(raw)
        need(type(row) is dict, "INVALID_RESPONSE")
        kind = rule[0]
        if kind == "repository":
            need(row.get("full_name") == self.project["repository"] and row.get("fork") is False, "FOREIGN_REPOSITORY")
        elif kind == "ref":
            need(row.get("ref") == "refs/heads/" + path.rsplit("/", 1)[1] and
                 row.get("object", {}).get("type") == "commit" and row["object"].get("sha") == rule[1], "REF_MOVED")
            self._seen_refs.add(path)
            self._bind_roles()
        elif kind == "commit":
            need(row.get("sha") == rule[1], "WRONG_COMMIT")
            tree = github.sha(row.get("tree", {}).get("sha"))
            self._allow("/git/trees/" + tree + "?recursive=1", ("tree", tree, rule[2]))
        elif kind == "tree":
            need(row.get("sha") == rule[1] and row.get("truncated") is False and type(row.get("tree")) is list, "INCOMPLETE_TREE")
            entries = {}
            for entry in row["tree"]:
                name = entry.get("path")
                need(type(name) is str and name not in entries, "DUPLICATE_TREE_PATH")
                entries[name] = entry
            wanted = ({b["manifest_path"]: "manifest", "config/autonomous_repair.json": "policy"}
                      if rule[2] == "main" else {"ops/REPAIR_COORDINATOR.json": "coordinator"})
            for name, tag in wanted.items():
                entry = entries.get(name, {})
                need(entry.get("mode") == "100644" and entry.get("type") == "blob", "NOT_ORDINARY_BLOB")
                sha = github.sha(entry.get("sha"))
                need(tag != "coordinator" or sha == b["coordinator_blob_sha"], "WRONG_COORDINATOR_BLOB")
                self._allow("/git/blobs/" + sha, ("blob", sha, tag))
        elif kind == "main_runs":
            rows = row.get("workflow_runs")
            need(type(rows) is list, "INVALID_RUNS")
            chosen = [r for r in rows if r.get("path") == ".github/workflows/" + b["workflow_file"]]
            need(chosen, "MISSING_RUN")
            run = chosen[0]
            need(github.integer(run.get("id")) and github.integer(run.get("run_attempt")) and
                 type(run.get("workflow_id")) is int and run["workflow_id"] == b["workflow_id"] and
                 run.get("event") == "push" and run.get("head_branch") == "main" and
                 run.get("repository", {}).get("full_name") == self.project["repository"] and
                 run.get("head_repository", {}).get("full_name") == self.project["repository"] and
                 run["head_repository"].get("fork") is False, "FOREIGN_MAIN_RUN")
            head = github.sha(run.get("head_sha"))
            self._allow("/actions/runs/" + str(run["id"]), ("run", run["id"], run["run_attempt"], head))
            self._jobs(run["id"], run["run_attempt"])
            if head != b["main_sha"]:
                self._allow("/compare/" + head + "..." + b["main_sha"], ("compare",))
        elif kind == "run":
            need(type(row.get("id")) is int and row["id"] == rule[1] and
                 type(row.get("run_attempt")) is int and row["run_attempt"] == rule[2] and
                 row.get("head_sha") == rule[3], "WRONG_RUN")
        # PR/list/job/compare behavioral validation stays in the unchanged
        # accepted collectors. No response-provided URL ever becomes a request.

    def get(self, url):
        try:
            self._begin()
            need(type(url) is str and url.startswith(self.prefix), "FOREIGN_GET")
            path = url[len(self.prefix):]
            need(path in self._rules and url == self.prefix + path, "UNSCOPED_GET")
            response = self._get(url)
            need(type(response) is github.Response and type(response.status) is int and response.status == 200, "GET_REJECTED")
            self._consume(response.text)
            self._learn(path, self._rules[path], response.text)
            self.trace.append({"method": "GET", "url": url, "observed_at": self.clock(),
                               "response_sha256": hashlib.sha256(response.text.encode()).hexdigest()})
            return response
        except Exception:
            self.closed = True
            raise EvidenceError("READONLY_TRANSPORT_REJECTED") from None

    def peek(self, task):
        try:
            self._begin()
            need(self.roles_bound and type(task) is str and task in self.project["roles"].values(), "UNSCOPED_PEEK")
            response = self._peek(task)
            need(type(response) is service.PeekResponse and response.ok is True, "PEEK_REJECTED")
            self._consume(response.text)
            envelope = github.loads(response.text)
            need(type(envelope) is dict, "INVALID_PEEK_ENVELOPE")
            layers = [envelope]
            if "structuredContent" in envelope:
                need("automations" not in envelope and type(envelope["structuredContent"]) is dict, "AMBIGUOUS_PEEK_ENVELOPE")
                layers.append(envelope["structuredContent"])
            for layer in layers:
                need(layer.get("isError", False) is False and layer.get("status") != "ERROR" and
                     layer.get("error_code") is None, "PEEK_ERROR_ENVELOPE")
            safe = service.snapshot(response.text, task, github.moment(self.clock()), self.binding["max_record_age_seconds"])
            projected = {"automations": [{"id": safe["task_id"], "is_enabled": safe["is_enabled"],
                "run_details": {"last_run": safe["last_run"], "latest_result": safe["latest_result_metadata"]}}]}
            text = json.dumps(projected, sort_keys=True)
            self.trace.append({"method": "PEEK", "task_id": task, "observed_at": self.clock(),
                               "forwarded_metadata_sha256": hashlib.sha256(text.encode()).hexdigest(),
                               "projection": "ALLOWLISTED_LIFECYCLE_METADATA_ONLY"})
            return service.PeekResponse(True, text)
        except Exception:
            self.closed = True
            raise EvidenceError("READONLY_TRANSPORT_REJECTED") from None

    def audit(self):
        return {"verification": "NOT_VERIFIED", "mode": "READ_ONLY_INPUT_ADAPTER",
                "repository": self.project["repository"], "roles_bound_to_pinned_blobs": self.roles_bound,
                "calls": self.calls, "received_bytes": self.raw_bytes, "closed": self.closed,
                "trace": deepcopy(self.trace), "authority": deepcopy(DENIED),
                "limitations": "NO_SANDBOX_CREDENTIAL_ISOLATION_OR_PORTABLE_ORIGIN_PROOF"}


def observe(projects, binding, get, peek, clock, *, collector="incident"):
    need(collector in ("incident", "service"), "UNKNOWN_COLLECTOR")
    transport = ReadOnlyTransport(projects, binding, get, peek, clock)
    if collector == "incident":
        report = incident.observe(projects, binding, transport.get, transport.peek, transport.clock)
    else:
        pins = {k: binding["github"][k] for k in service.FIELDS if k != "max_record_age_seconds"}
        pins["max_record_age_seconds"] = binding["max_record_age_seconds"]
        report = service.observe(projects, pins, transport.get, transport.peek, transport.clock)
    return {"observation": report, "transport": transport.audit(), "verification": "NOT_VERIFIED",
            "authority": deepcopy(DENIED)}


def main():
    try:
        class SafeParser(argparse.ArgumentParser):
            def error(self, message):
                raise EvidenceError("INVALID_REQUEST")
        parser = SafeParser(description=__doc__)
        parser.add_argument("--request", required=True)
        request = github.loads(Path(parser.parse_args().request).read_text(encoding="utf-8"))
        need(type(request) is dict and set(request) == {"projects", "binding", "collector"}, "INVALID_REQUEST")
        def call(method, key, value):
            print(json.dumps({"method": method, key: value}), flush=True)
            row = github.loads(sys.stdin.readline())
            need(type(row) is dict and set(row) == ({"status", "body"} if method == "GET" else {"ok", "body"}), "INVALID_RESPONSE")
            return github.Response(row["status"], row["body"]) if method == "GET" else service.PeekResponse(row["ok"], row["body"])
        result = observe(request["projects"], request["binding"], lambda url: call("GET", "url", url),
                         lambda task: call("PEEK", "task_id", task), lambda: datetime.now(timezone.utc).isoformat(), collector=request["collector"])
        print(json.dumps({"result": result}, sort_keys=True), flush=True)
        return 0
    except Exception:
        print(json.dumps({"verification": "NOT_VERIFIED", "reason": "READONLY_TRANSPORT_REJECTED", "authority": DENIED}), flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
