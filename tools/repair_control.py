"""Fenced leases and approval packets; no built-in network or scheduler clients.

Persist returned states on the shared coordinator branch with expected_sha and
force=False. A plan is NOT a lock until that non-fast-forward-protected update
succeeds. All competing commits must use the exact observed head as parent.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

TASK_ID = "6adbf0d6a7d881918ce181dff2468867"
CONTROL_BRANCH = "twf-repair-coordinator"
CONTROL_PATH = "ops/REPAIR_COORDINATOR.json"


def canonical_id(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError("canonical operation/run UUID required")
    return value


def instant(value):
    # Fail closed with a domain error, not an unhandled AttributeError when
    # a remote coordinator contains a malformed timestamp.
    if type(value) is not str or not value or len(value) > 64:
        raise ValueError("invalid coordinator timestamp")
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, OverflowError):
        raise ValueError("invalid coordinator timestamp") from None
    if moment.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return moment.astimezone(timezone.utc)


def validate(state):
    if type(state) is not dict:
        raise ValueError("invalid coordinator object")
    if state.get("schema") != 1 or state.get("task_id") != TASK_ID:
        raise ValueError("wrong coordinator schema/task")
    epoch = state.get("epoch")
    if type(epoch) is not int or epoch < 0:
        raise ValueError("invalid lease generation")
    holder = state.get("holder")
    if holder is not None:
        canonical_id(holder["owner_id"])
        if holder.get("kind") not in ("DISPATCH", "WORKER", "META", "REVIEWER", "CONTROLLER"):
            raise ValueError("invalid owner kind")
        if holder["kind"] in ("WORKER", "META", "REVIEWER") and holder.get("task_id") != state.get("authorized_tasks", {}).get(holder["kind"]):
            raise ValueError("unregistered worker task")
        if type(holder.get("epoch")) is not int or holder["epoch"] != epoch:
            raise ValueError("inconsistent fencing generation")
        if instant(holder["expires_at"]) <= instant(holder["acquired_at"]):
            raise ValueError("invalid lease lifetime")
    return state


def initial_state(packet=None):
    return {"schema": 1, "task_id": TASK_ID, "epoch": 0, "holder": None,
            "authorized_tasks": {"WORKER": TASK_ID},
            "approval_packet": packet, "last_reported_approval_signature": None,
            "last_completed": None}



def scoped_lease_migration_block(state):
    """Stop legacy acquisition while a v2 scoped writer exists.

    This gate must be installed on EVERY legacy runner *before* anyone
    enables parallel leases. A prior checkout of legacy code is not fenced
    by the presence of this function in a newer commit. Do not use this
    advisory shim as permission to turn on live parallel writes.
    """
    if type(state) is not dict or type(state.get("epoch")) is not int:
        raise ValueError("invalid scoped coordinator object")
    blocked = False
    for key in ("shadow_parallel_leases", "parallel_leases"):
        if key not in state:
            continue
        registry = state[key]
        if (type(registry) is not dict or set(registry) != {"schema", "entries"} or
                type(registry["schema"]) is not int or registry["schema"] != 1 or
                type(registry["entries"]) is not list or
                len(registry["entries"]) > 2):
            raise ValueError("unrecognized scoped lease registry")
        seen_work, seen_owner, seen_branch = set(), set(), set()
        for entry in registry["entries"]:
            if (type(entry) is not dict or
                    set(entry) != {"scope", "owner_id", "run_id", "nonce",
                                   "lease_epoch", "acquired_at", "expires_at"}):
                raise ValueError("invalid scoped lease identity")
            scope = entry["scope"]
            if (type(scope) is not dict or
                    type(scope.get("work_id")) is not str or
                    type(scope.get("branch")) is not str or
                    not scope["work_id"] or not scope["branch"]):
                raise ValueError("missing scoped work or branch")
            for id_key in ("owner_id", "run_id", "nonce"):
                canonical_id(entry[id_key])
            work, owner, branch = scope["work_id"], entry["owner_id"], scope["branch"]
            if work in seen_work or owner in seen_owner or branch in seen_branch:
                raise ValueError("duplicate scoped identity")
            seen_work.add(work)
            seen_owner.add(owner)
            seen_branch.add(branch)
            if (type(entry["lease_epoch"]) is not int or
                    entry["lease_epoch"] < 1 or entry["lease_epoch"] > state["epoch"] or
                    instant(entry["expires_at"]) <= instant(entry["acquired_at"])):
                raise ValueError("invalid scoped lease lifetime or epoch")
            # Expired entry is NOT self-revocation; only verified recovery can
            # remove it from this same CAS-controlled registry.
            blocked = True
    # Explicit freeze marker protects early migration even before scoped rows
    # are admitted; unknown values fail closed.
    mode = state.get("parallel_write_migration", "LEGACY_ONLY")
    if type(mode) is not str or mode not in ("LEGACY_ONLY", "SCOPED_ACTIVE"):
        raise ValueError("invalid scoped migration mode")
    return blocked or mode == "SCOPED_ACTIVE"

def acquire(state, kind, owner_id, now, service_status=None, base_main_sha=None, work_branch=None, actor_task_id=None):
    validate(state)
    canonical_id(owner_id)
    at = instant(now)
    if kind not in ("DISPATCH", "WORKER", "META", "REVIEWER", "CONTROLLER"):
        raise ValueError("invalid lease kind")
    if kind in ("WORKER", "META", "REVIEWER"):
        actor_task_id = actor_task_id or (TASK_ID if kind == "WORKER" else None)
        if not actor_task_id or actor_task_id != state.get("authorized_tasks", {}).get(kind):
            raise ValueError("worker task must be registered on the shared coordinator")
    if kind == "REVIEWER" and work_branch != "main":
        raise ValueError("integration reviewer may only own the main integration lane")
    if kind in ("WORKER", "META") and work_branch is not None:
        prefix = "auto/twf-game-repair-" if kind == "WORKER" else "auto/twf-system-review-"
        if kind == "META" or work_branch != "auto/twf-game-repair":
            if not work_branch.startswith(prefix):
                raise ValueError("worker cannot claim an unrelated branch")
            canonical_id(work_branch[len(prefix):])
    if scoped_lease_migration_block(state):
        return {"action": "WAIT_SCOPED_LEASES", "state": state, "write": False}
    holder = state["holder"]
    if kind == "DISPATCH":
        if service_status == "in_progress":
            return {"action": "JOIN_EXISTING", "state": state, "write": False}
        if service_status not in ("completed", "failed", "no_update"):
            return {"action": "WAIT_METADATA", "state": state, "write": False}
    if holder:
        # A dispatcher only requests a worker; the first worker atomically adopts
        # that ticket. Other manual requests cannot enqueue a second request.
        if kind == "WORKER" and holder["kind"] == "DISPATCH":
            pass
        elif holder["kind"] == kind and holder["owner_id"] == owner_id:
            action = "RESUME" if at < instant(holder["expires_at"]) else "WAIT_RECOVERY"
            return {"action": action, "state": state, "write": False}
        else:
            action = "JOIN_EXISTING" if holder["kind"] in ("WORKER", "META", "REVIEWER", "DISPATCH") else "WAIT_LOCK"
            if at >= instant(holder["expires_at"]) and holder["kind"] != "DISPATCH":
                action = "WAIT_RECOVERY"
            return {"action": action, "state": state, "write": False,
                    "holder": deepcopy(holder)}
    next_state = deepcopy(state)
    next_state["epoch"] += 1
    seconds = 120 if kind == "DISPATCH" else 1800
    next_state["holder"] = {"kind": kind, "owner_id": owner_id, "task_id": actor_task_id,
                            "epoch": next_state["epoch"], "acquired_at": at.isoformat(),
                            "expires_at": (at + timedelta(seconds=seconds)).isoformat(),
                            "base_main_sha": base_main_sha,
                            "work_branch": work_branch,
                            "origin": "manual" if holder and holder["kind"] == "DISPATCH" else kind.lower()}
    return {"action": "ACQUIRE", "state": next_state, "write": True}


def _owns_legacy_holder(state, kind, owner_id, epoch, now):
    """Internal holder-only test for releasing the same owner, NEVER write auth."""
    validate(state)
    holder = state["holder"]
    return bool(type(epoch) is int and holder and holder["kind"] == kind and holder["owner_id"] == owner_id
                and holder["epoch"] == epoch and instant(now) < instant(holder["expires_at"]))


def owns(state, kind, owner_id, epoch, now):
    """Legacy WRITE authorization must stop if a scoped writer may exist.

    Mixed generations may still be unwound by release() only for the exact
    current owner. This read-only predicate is never provider authentication.
    """
    validate(state)
    if scoped_lease_migration_block(state):
        return False
    return _owns_legacy_holder(state, kind, owner_id, epoch, now)


def release(state, kind, owner_id, epoch, now, packet=None, reported=False):
    validate(state)
    if type(epoch) is not int:
        raise ValueError("integer fencing generation required")
    holder = state["holder"]
    if not holder or (holder["kind"], holder["owner_id"], holder["epoch"]) != (kind, owner_id, epoch):
        raise ValueError("only the current fenced owner can release")
    if instant(now) < instant(holder["acquired_at"]):
        raise ValueError("release cannot precede acquisition")
    result = deepcopy(state)
    result["holder"] = None
    result["last_completed"] = {"kind": kind, "owner_id": owner_id, "epoch": epoch,
                                "released_at": instant(now).isoformat()}
    if packet is not None:
        result["approval_packet"] = packet
        if reported:
            result["last_reported_approval_signature"] = packet["signature"]
    return result



@contextmanager
def owned_lease(*, repository, kind, owner_id, epoch, task_id, read, cas, peek, clock):
    """Finally release a live exact owner through host-supplied capabilities.

    read(repo, branch, path) returns {repository, branch, ref, state}; cas accepts
    only a new state, expected_sha and force=False and returns its commit SHA.
    peek(task_id) returns {task_id, last_run}. The trusted host must bind these
    callbacks to genuine connections/current run and retain their call evidence.
    Python data/receipts do NOT authenticate providers or prove service exit.
    No acquisition, recovery, retry, scheduler, credentials or network client.
    A killed process or failed host callback cannot be fixed by Python finally.
    """
    if (not isinstance(repository, str) or
            not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or
            kind not in ("WORKER", "META", "REVIEWER") or type(epoch) is not int or epoch < 1):
        raise ValueError("invalid owned lease binding")
    canonical_id(owner_id)
    previous = None

    def tick():
        nonlocal previous
        at = instant(clock())
        if previous is not None and at < previous:
            raise ValueError("clock moved backwards")
        previous = at
        return at

    def snapshot():
        row = deepcopy(read(repository, CONTROL_BRANCH, CONTROL_PATH))
        if (type(row) is not dict or
                set(row) != {"repository", "branch", "ref", "state"} or
                row["repository"] != repository or row["branch"] != CONTROL_BRANCH or
                not isinstance(row["ref"], str) or not re.fullmatch(r"[0-9a-f]{40}", row["ref"])):
            raise ValueError("invalid scoped coordinator snapshot")
        validate(row["state"])
        return row

    def live_owner(row, *, release_only=False):
        state, at = row["state"], tick()
        holder = state["holder"]
        # Cleanup may bypass scoped *occupancy*, never scoped schema validation.
        # A malformed v2 registry is an unresolved incident, not release proof.
        if release_only:
            scoped_lease_migration_block(state)
        owner_check = _owns_legacy_holder if release_only else owns
        if (not task_id or state["authorized_tasks"].get(kind) != task_id or
                not owner_check(state, kind, owner_id, epoch, at.isoformat()) or
                holder["task_id"] != task_id or at < instant(holder["acquired_at"]) or
                (instant(holder["expires_at"])-instant(holder["acquired_at"])).total_seconds() > 1800):
            raise ValueError("not the live registered owner")
        service = peek(task_id)
        run = service.get("last_run", {}) if type(service) is dict else {}
        if (service.get("task_id") != task_id or run.get("id") != owner_id or
                run.get("recorded_status") != "in_progress" or run.get("completed_at") is not None or
                instant(run.get("started_at", "")) > instant(holder["acquired_at"])):
            raise ValueError("current same-run observation required")
        return holder

    try:
        initial = snapshot()
        anchor = deepcopy(live_owner(initial))
    except Exception:
        raise ValueError("owned lease entry not verified") from None
    receipt = {"status": "OWNED", "repository": repository, "kind": kind,
               "task_id": task_id, "owner_run_id": owner_id, "epoch": epoch,
               "provider_verified": False, "provider_terminal": "NOT_ATTESTED"}
    try:
        yield receipt
    finally:
        attempted, stage = False, "PRE_RELEASE"
        receipt.update(status="NOT_RELEASED", provider_verified=False,
                       provider_terminal="NOT_ATTESTED")
        try:
            first = snapshot()
            # A mixed v2 entry must stop NEW work, but must not trap an
            # already verified original owner from legally releasing itself.
            # Keep exact owner/epoch/task/live-run and double GitHub readback.
            if live_owner(first, release_only=True) != anchor:
                raise ValueError("original holder changed")
            second = snapshot()
            if live_owner(second, release_only=True) != anchor or second != first:
                raise ValueError("coordinator moved during final fence")
            at = tick().isoformat()
            if not _owns_legacy_holder(second["state"], kind, owner_id, epoch, at):
                raise ValueError("lease expired before CAS")
            target = release(second["state"], kind, owner_id, epoch, at)
            target["last_completed"]["release_receipt"] = {
                "kind": "OWNER_RELEASE_NOT_PROVIDER_TERMINAL_PROOF",
                "repository": repository, "task_id": task_id, "owner_run_id": owner_id,
                "epoch": epoch, "expected_parent": second["ref"],
                "provider_terminal": "NOT_ATTESTED", "postwrite_readback_required": True}
            stage, attempted = "CAS", True
            new_ref = cas(repository, CONTROL_BRANCH, expected_sha=second["ref"],
                          state=deepcopy(target), force=False)
            if (not isinstance(new_ref, str) or not re.fullmatch(r"[0-9a-f]{40}", new_ref) or
                    new_ref == second["ref"]):
                raise ValueError("invalid CAS acknowledgement")
            stage = "READBACK"
            after = snapshot()
            tick()
            if after["ref"] != new_ref or after["state"] != target:
                raise ValueError("release not confirmed by actual ref/state")
            receipt.update(status="RELEASED_READBACK", from_ref=second["ref"],
                           to_ref=new_ref, released_at=at)
        except Exception:
            receipt.update(status="RELEASE_UNCONFIRMED" if attempted else "NOT_RELEASED",
                           failure_stage=stage)
            raise RuntimeError("owned lease finalization not confirmed: " + stage) from None

def recover_finished_worker(state, observed_run, now):
    validate(state)
    holder = state["holder"]
    if (not holder or holder["kind"] not in ("WORKER", "META", "REVIEWER") or
            observed_run.get("id") != holder["owner_id"] or
            observed_run.get("recorded_status") not in ("completed", "failed", "no_update") or
            not observed_run.get("completed_at") or
            instant(observed_run["completed_at"]) < instant(holder["acquired_at"]) or
            instant(observed_run["completed_at"]) > instant(now)):
        raise ValueError("recovery requires positive completion evidence for the exact worker")
    result = release(state, holder["kind"], holder["owner_id"], holder["epoch"], now)
    result["last_completed"]["recovered_from_service_evidence"] = True
    return result


def approval_packet(pulls, repository, observed_at, delegated=False):
    """Require exact-head successful CI and a concrete diff summary for every item."""
    instant(observed_at)
    entries, seen = [], set()
    prefix = "https://github.com/" + repository
    for pr in sorted(pulls, key=lambda item: item["number"]):
        number = pr.get("number")
        if type(number) is not int or number <= 0 or number in seen:
            raise ValueError("invalid/duplicate approval PR")
        seen.add(number)
        if (pr.get("state") != "open" or pr.get("merged") is not False or
                pr.get("repository") != repository or pr.get("ci") != "success" or
                pr.get("ci_head") != pr.get("head") or
                not re.fullmatch(r"[0-9a-f]{40}", pr.get("head", ""))):
            raise ValueError("approval requires an open same-repository PR and exact-head success")
        if (pr.get("url") != prefix + "/pull/" + str(number) or
                not pr.get("ci_url", "").startswith(prefix + "/actions/runs/") or
                not pr.get("summary") or not pr.get("changed_files")):
            raise ValueError("approval needs concrete contents and evidence URLs")
        entries.append({key: pr[key] for key in (
            "number", "title", "url", "head", "ci_url", "summary", "changed_files")})
        entries[-1]["kind"] = ("ゲーム本体修正" if any(x.startswith("src/") for x in pr["changed_files"])
                               else "開発体制改善" if any(x.startswith(("tools/", "ops/")) for x in pr["changed_files"])
                               else "回帰検査追加")
    content = {"scope": "EXACT_HEAD_MAIN_INTEGRATION_ONLY", "items": entries,
               "decision_owner": "ASSISTANT" if delegated else "OWNER",
               "roblox_publish_authorized": False, "automatic_merge_authorized": bool(delegated)}
    signature = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {**content, "observed_at": observed_at, "signature": signature,
            "approval_text": ("・".join("#" + str(p["number"]) for p in entries) + "のmain取り込みを承認") if entries and not delegated else ""}


def report_needed(state, packet, manual=False):
    # Manual status/GO responses always list approvals. Scheduled runs may only
    # suppress an identical packet AFTER a complete approval request was recorded.
    return bool(packet["items"]) and (manual or state.get("last_reported_approval_signature") != packet["signature"])


def render_approvals(packet):
    delegated = packet.get("decision_owner") == "ASSISTANT"
    title = "自動審査・統合待ち" if delegated else "取り込み承認待ち"
    if not packet["items"]:
        message = "自動統合待ちの項目はありません。所有者への承認返信は不要です。" if delegated else "承認待ちの項目はありません。"
        return "# " + title + "\n\n観測時点: " + packet["observed_at"] + "\n\n" + message + "\n"
    lines = ["# " + title, "", "観測時点: " + packet["observed_at"], "",
             "| PR | 内容 | 区分 | 現在headの検査 |", "| --- | --- | --- | --- |"]
    for item in packet["items"]:
        clean = item["summary"].replace("|", "／").replace("\n", " ")
        lines.append(f'| [#{item["number"]}]({item["url"]}) | {clean} | {item["kind"]} | [合格]({item["ci_url"]}) / `{item["head"][:8]}` |')
    if delegated:
        return "\n".join(lines + ["", "所有者への承認返信は不要。独立審査役が現在headの検査と共有所有権を確認し、1件ずつ統合してmainを検査する。", ""])
    lines += ["", "承認する場合の返信: **" + packet["approval_text"] + "**", "",
              "対象は上記コミットのmain取り込み。Roblox公開・課金・外部モデル再実行の承認は含まない。",
              "承認後にhead・CI・競合を再確認し、変更があれば承認を流用しない。", ""]
    return "\n".join(lines)


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def verify_pr(policy, base, head, branch, control_ref):
    if policy.get("queue_version", 0) < 3:
        return "pre-coordination base policy"
    # This is a non-authorizing CI preflight. The trusted integration host
    # MUST separately bind the eventual merge to a fresh atomic coordinator
    # snapshot; a successful historical CLI decision is NOT a merge permit.
    current = json.loads(git("show", control_ref + ":" + CONTROL_PATH))
    validate(current)
    if scoped_lease_migration_block(current):
        raise ValueError("legacy PR verification blocked by scoped migration")
    head = git("rev-parse", head)
    meta = branch.startswith(policy.get("system_review", {}).get("branch_prefix", "auto/twf-system-review-"))
    kind = "META" if meta else "WORKER"
    expected_task = policy["system_review"]["task_id"] if meta else policy["task_id"]
    for old in ([] if meta else policy["coordination"].get("grandfathered_pr_heads", [])):
        if old["head"] == head and old["branch"] == branch:
            return "exact pre-v3 draft grandfathered; no approval or merge permission granted"
        if old["branch"] == branch:
            subprocess.run(["git", "merge-base", "--is-ancestor", old["head"], head], check=True, capture_output=True)
            base = old["head"]
    prefix = policy["system_review"]["branch_prefix"] if meta else policy["branch_prefix"]
    legacy = None if meta else policy["branch"]
    if branch != legacy and not branch.startswith(prefix):
        raise ValueError("new work requires a UUID lane")
    if branch != legacy:
        canonical_id(branch[len(prefix):])
    raw = subprocess.check_output(["git", "diff", "--name-status", "--no-renames", "-z", base, head, "--"]).decode().split("\0")
    entries = list(zip(raw[::2], raw[1::2]))
    records = [path for status, path in entries if status in ("A", "M") and re.fullmatch(r"history/C[0-9]{5}_[^/]+\.json", path)]
    if not records:
        raise ValueError("new worker PR requires a cycle record with a coordinator claim")
    for path in records:
        history = json.loads(git("show", head + ":" + path))
        proof = history.get("coordination", {})
        claim = proof.get("claim_commit", "")
        owner_id = canonical_id(proof.get("owner_run_id"))
        if (proof.get("branch") != CONTROL_BRANCH or
                not re.fullmatch(r"[0-9a-f]{40}", claim)):
            raise ValueError("missing canonical coordinator proof")
        subprocess.run(["git", "merge-base", "--is-ancestor", claim, control_ref], check=True, capture_output=True)
        state = json.loads(git("show", claim + ":" + CONTROL_PATH))
        validate(state)
        if scoped_lease_migration_block(state):
            raise ValueError("legacy claim contains scoped migration")
        holder = state["holder"]
        if not holder or (holder["kind"], holder["owner_id"], holder["epoch"]) != (kind, owner_id, proof.get("epoch")):
            raise ValueError("claim belongs to another lease owner/generation")
        if holder.get("task_id") != expected_task:
            raise ValueError("claim belongs to another registered task")
        if holder.get("work_branch") != branch:
            raise ValueError("claim does not cover this repair branch")
        if state["epoch"] < 1:
            raise ValueError("invalid claim generation")
        parent = json.loads(git("show", claim + "^:" + CONTROL_PATH))
        validate(parent)
        if scoped_lease_migration_block(parent):
            raise ValueError("legacy claim parent contains scoped migration")
        if state.get("authorized_tasks") != parent.get("authorized_tasks"):
            raise ValueError("a claim cannot change registered tasks")
        if state["epoch"] != parent["epoch"] + 1 or (parent["holder"] and (kind != "WORKER" or parent["holder"]["kind"] != "DISPATCH")):
            raise ValueError("claim must follow idle or a dispatch ticket")
    return f"{len(records)} immutable coordinator claim(s) verified"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # Route before argparse so invalid diagnostic arguments are sanitized by
    # the v2 parser and cannot echo provider errors or secret-bearing strings.
    if argv[:1] == ["triage"]:
        from system_host_write_triage_v2 import main as triage_main
        return triage_main(argv[1:])
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("triage", help="read-only v2 incident diagnosis; no write authority")
    plan = sub.add_parser("plan")
    plan.add_argument("--input", required=True, help="state, kind, owner_id, now, service_status, base_main_sha")
    packet = sub.add_parser("approvals")
    packet.add_argument("--input", required=True, help="pulls, repository, observed_at")
    packet.add_argument("--markdown", action="store_true")
    check = sub.add_parser("verify-pr")
    for arg in ("policy", "base", "head", "branch", "control-ref"):
        check.add_argument("--" + arg, required=True)
    args = parser.parse_args(argv)
    if args.command == "verify-pr":
        policy = json.loads(Path(args.policy).read_text())
        print("PASS: repair coordination; " + verify_pr(policy, args.base, args.head, args.branch, args.control_ref))
        return
    data = json.loads(Path(args.input).read_text())
    if args.command == "plan":
        result = acquire(**data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = approval_packet(**data)
        print(render_approvals(result) if args.markdown else json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
