"""Scoped host-capability bridge for the accepted idle observer and ledger.

No credential, HTTP client, scheduler, notification or recovery API. A separately
trusted host binds GET/PEEK and, optionally, three already-authorized Git tool
callbacks. Callbacks are a trust boundary, not portable provider authentication.
Without writer capabilities the result is a prepared operation, NOT_PERSISTED.
Only ops/alerts/<selected game>.json on its coordinator may change. No retry,
force, takeover, main/PR write or permission upgrade exists. An uncertain CAS
receipt/readback may mean a write occurred: never assert rollback or delivery.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from tools import system_alert_ledger as ledger
from tools import system_idle_health as idle

github, need, EvidenceError = idle.github, idle.need, idle.EvidenceError
WRITES = {"create_tree", "create_commit", "update_ref"}
SAFE_ERRORS = {"REF_MOVED_OR_FOREIGN", "FENCE_NOT_OWNED", "EXPIRED_OR_STALE_LEDGER_FENCE",
               "WRONG_EPOCH_OR_ROLE", "BLOB_HASH_MISMATCH", "WRONG_BLOB", "GET_REJECTED",
               "PREVIOUS_LEDGER_DIGEST_MISMATCH", "OBSERVER_UNASSESSABLE", "ACTOR_NOT_CURRENT",
               "ANCHOR_CHANGED", "WRONG_PREPARED_TREE", "WRONG_PREPARED_COMMIT",
               "WRITE_RECEIPT_REJECTED", "INVALID_WRITE_CAPABILITIES", "CLOCK_INVALID"}


def _result(state, stage, receipts, **extra):
    return {"schema": 1, "mode": "HOST_CAPABILITY_LEDGER_BRIDGE", "verification": "NOT_VERIFIED",
            "state": state, "stage": stage, "persisted": state == "PERSISTED_READBACK",
            "cas_attempted": any(r["operation"] == "update_ref" for r in receipts),
            "operation_receipts": deepcopy(receipts), "delivery": "NOT_ATTEMPTED",
            "recovery_verification": "NOT_VERIFIED", "a12_verified": False,
            "main_qa": "MAIN_QA_NOT_CHECKED", "authority": deepcopy(idle.service.DENIED), **extra}


def _snapshot(project, binding, actor, reader, peek, clock):
    reader.ref("main", binding["main_sha"])
    reader.ref(project["coordination_ref"], binding["coordinator_sha"])
    commit = reader.read("/git/commits/" + binding["coordinator_sha"])
    tree_sha = github.sha(commit.get("tree", {}).get("sha"))
    tree = reader.tree(binding["coordinator_sha"])
    state = reader.blob(tree, "ops/REPAIR_COORDINATOR.json", binding["coordinator_blob_sha"])
    roles = {kind: project["roles"][role] for role, kind in idle.service.ROLES.items()}
    need(type(state) is dict and type(state.get("schema")) is int and state["schema"] == 1 and
         state.get("task_id") == roles["WORKER"] and state.get("authorized_tasks") == roles and
         type(state.get("epoch")) is int and state["epoch"] == binding["coordinator_epoch"], "WRONG_EPOCH_OR_ROLE")
    path = "ops/alerts/" + project["game_id"] + ".json"
    previous = reader.blob(tree, path) if path in tree else None
    prior_blob = tree[path]["sha"] if path in tree else None
    now = clock()
    fence = {"repository": project["repository"], "coordination_ref": project["coordination_ref"],
             "expected_ref_sha": binding["coordinator_sha"], "observed_at": now, "epoch": state["epoch"],
             "actor_role": actor["role"], "actor_task_id": actor["task_id"], "actor_run_id": actor["run_id"],
             "holder": state.get("holder"), "previous_digest": None if previous is None else ledger.digest(previous)}
    ledger._fence(project, fence, idle.moment(now))
    need(state["holder"]["base_main_sha"] == binding["main_sha"] and
         (idle.moment(state["holder"]["expires_at"])-idle.moment(now)).total_seconds() >= 30, "FENCE_NOT_OWNED")
    try:
        response = peek(actor["task_id"])
    except Exception:
        raise EvidenceError("ACTOR_NOT_CURRENT") from None
    need(type(response) is idle.service.PeekResponse and response.ok is True, "ACTOR_NOT_CURRENT")
    envelope = github.loads(response.text)
    layers = [envelope]
    if type(envelope) is dict and "structuredContent" in envelope:
        need("automations" not in envelope, "ACTOR_NOT_CURRENT")
        layers.append(envelope["structuredContent"])
    need(all(type(x) is dict and x.get("isError", False) is False and x.get("status") != "ERROR" and
         x.get("error_code") is None for x in layers), "ACTOR_NOT_CURRENT")
    row = idle.service.snapshot(response.text, actor["task_id"], idle.moment(clock()), binding["max_record_age_seconds"])
    need(row["is_enabled"] is True and row["last_run"]["id"] == actor["run_id"] and
         row["last_run"]["recorded_status"] == "in_progress" and
         idle.moment(row["last_run"]["started_at"]) <= idle.moment(state["holder"]["acquired_at"]), "ACTOR_NOT_CURRENT")
    # Recheck expiry after PEEK, not just before a possibly slow callback.
    ledger._fence(project, fence, idle.moment(clock()))
    return {"tree_sha": tree_sha, "tree": tree, "path": path, "previous": previous,
            "prior_blob": prior_blob, "fence": fence}


def _same(first, second):
    need(all(first[k] == second[k] for k in ("tree_sha", "tree", "path", "previous", "prior_blob")) and
         all(first["fence"][k] == second["fence"][k] for k in ledger.FENCE - {"observed_at"}), "ANCHOR_CHANGED")


def persist(projects, binding, actor, thresholds, get, peek, clock, *, writer=None):
    """Observe first; reduce pinned prior; prepare or use explicit host callbacks.

    writer keys match the connected create_tree/create_commit/update_ref tools;
    each callable accepts keyword arguments and returns github.Response (201 for
    object creation,200 with {success:true} for a CAS-checked ref update). The
    host must implement expected_sha itself; bare REST force=false is not that
    parameter. Never pass a credential to this module or bind automatic retries.
    """
    stage, receipts, prepared = "INPUT", [], None
    previous_time = None
    def tick():
        nonlocal previous_time
        try:
            now = idle.moment(clock())
            need(previous_time is None or previous_time <= now, "CLOCK_INVALID")
            previous_time = now
            return now.isoformat()
        except Exception:
            raise EvidenceError("CLOCK_INVALID") from None
    try:
        projects, binding, actor = deepcopy(projects), deepcopy(binding), deepcopy(actor)
        project = idle._project(projects, binding)
        need(type(actor) is dict and set(actor) == {"role", "task_id", "run_id"} and
             actor["role"] in ("meta", "reviewer") and actor["task_id"] == project["roles"][actor["role"]], "ACTOR_NOT_CURRENT")
        idle.service.run_id(actor["run_id"])
        need(writer is None or (type(writer) is dict and set(writer) == WRITES and
             all(callable(fn) for fn in writer.values())), "INVALID_WRITE_CAPABILITIES")
        stage = "OBSERVE"
        report = idle.observe(projects, binding, thresholds, get, peek, tick)
        need(report["state"] != "INDETERMINATE", "OBSERVER_UNASSESSABLE")
        stage = "IMMUTABLE_ANCHOR"
        reader = github.Reader(project["repository"], get, tick)
        first = _snapshot(project, binding, actor, reader, peek, tick)
        reduced = ledger.reduce(projects, first["previous"], report["frame"], first["fence"], tick())
        if not reduced["changed"]:
            return _result("NOT_PERSISTED", "NO_CHANGE", receipts, reason=reduced["reason"])
        content = json.dumps(reduced["ledger"], sort_keys=True, separators=(",", ":")) + "\n"
        raw = content.encode()
        blob_sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        prepared = {"repository": project["repository"], "branch": project["coordination_ref"],
                    "parent_sha": binding["coordinator_sha"], "expected_sha": binding["coordinator_sha"], "force": False,
                    "base_tree_sha": first["tree_sha"], "path": first["path"], "content": content,
                    "content_blob_sha": blob_sha, "previous_blob_sha": first["prior_blob"],
                    "coordinator_blob_sha": binding["coordinator_blob_sha"], "epoch": binding["coordinator_epoch"],
                    "actor": actor, "live_host_reread_required": True}
        stage = "SECOND_ANCHOR"
        _same(first, _snapshot(project, binding, actor, reader, peek, tick))
        if writer is None:
            return _result("NOT_PERSISTED", "PREPARED_ONLY", receipts, reason="WRITE_CAPABILITY_NOT_BOUND", prepared=prepared)
        def write(name, **args):
            ledger._fence(project, first["fence"], idle.moment(tick()))
            need((idle.moment(first["fence"]["holder"]["expires_at"])-idle.moment(tick())).total_seconds() >= 30,
                 "FENCE_NOT_OWNED")
            receipt = {"operation": name, "status": "MISSING"}; receipts.append(receipt)
            try:
                response = writer[name](**args)
            except Exception:
                raise EvidenceError("WRITE_RECEIPT_REJECTED") from None
            need(type(response) is github.Response and type(response.status) is int, "WRITE_RECEIPT_REJECTED")
            receipt["status"] = response.status
            need(response.status == (200 if name == "update_ref" else 201), "WRITE_RECEIPT_REJECTED")
            row = github.loads(response.text)
            need(type(row) is dict and set(row) == ({"success"} if name == "update_ref" else {"sha"}), "WRITE_RECEIPT_REJECTED")
            if name == "update_ref": need(row["success"] is True, "WRITE_RECEIPT_REJECTED")
            else: github.sha(row["sha"])
            return row
        stage = "CREATE_TREE"
        tree_sha = write("create_tree", repository_full_name=project["repository"], base_tree_sha=first["tree_sha"],
                         tree_elements=[{"path": first["path"], "mode": "100644", "type": "blob", "content": content}])["sha"]
        stage = "CREATE_COMMIT"
        commit_sha = write("create_commit", repository_full_name=project["repository"], parent_sha=binding["coordinator_sha"],
                           tree_sha=tree_sha, message="Record scoped A12 alert ledger proposal")["sha"]
        obj = reader.read("/git/commits/" + commit_sha)
        need(obj.get("sha") == commit_sha and obj.get("tree", {}).get("sha") == tree_sha and
             [r.get("sha") for r in obj.get("parents", [])] == [binding["coordinator_sha"]], "WRONG_PREPARED_COMMIT")
        tree = reader.tree(commit_sha)
        def leaves(entries):return {k:v for k,v in entries.items() if v["type"] != "tree"}
        expected = leaves(first["tree"])
        expected[first["path"]] = {"path": first["path"], "mode": "100644", "type": "blob", "sha": blob_sha}
        # Ignore provider-only size/url fields, but compare every leaf/path/mode.
        clean = lambda entries: {k:{f:v.get(f) for f in ("path", "mode", "type", "sha")} for k,v in leaves(entries).items()}
        need(clean(tree) == clean(expected), "WRONG_PREPARED_TREE")
        need(reader.blob(tree, first["path"], blob_sha) == reduced["ledger"], "WRONG_PREPARED_TREE")
        stage = "FINAL_FENCE"
        _same(first, _snapshot(project, binding, actor, reader, peek, tick))
        stage = "CAS"
        write("update_ref", repository_full_name=project["repository"], branch_name=project["coordination_ref"],
              expected_sha=binding["coordinator_sha"], sha=commit_sha, force=False)
        stage = "READBACK"
        after = dict(binding, coordinator_sha=commit_sha)
        final = _snapshot(project, after, actor, reader, peek, tick)
        need(final["prior_blob"] == blob_sha and final["previous"] == reduced["ledger"] and
             final["fence"]["holder"] == first["fence"]["holder"], "ANCHOR_CHANGED")
        return _result("PERSISTED_READBACK", stage, receipts, commit_sha=commit_sha, ledger_blob_sha=blob_sha,
                       incident_count=len(reduced["ledger"]["frame"]["alerts"]), ref_outcome="OBSERVED_COMMIT_AND_BLOB")
    except Exception as error:
        reason = str(error) if type(error) is EvidenceError and str(error) in SAFE_ERRORS else "INDETERMINATE_REJECTION"
        attempted = any(r["operation"] == "update_ref" for r in receipts)
        return _result("NOT_PERSISTED", stage, receipts, reason=reason,
                       ref_outcome="UNCONFIRMED_POSSIBLE_WRITE" if attempted else "NO_REF_UPDATE_ATTEMPTED",
                       limitation="NOT_PERSISTED means no confirmed persistence; no rollback or notification claim")
