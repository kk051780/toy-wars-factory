#!/usr/bin/env python3
"""Read-only selection of authentic ART input, never a visual approval.

PRs use the latest exact PR-head RC80 producer, including its merge-SHA receipt.
Manual dispatch requires an explicit run and name. No historical/latest fallback.
The existing source, image, mobile and FUN auditors remain separate and unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time
from datetime import datetime, timezone
from typing import Callable
import zipfile

REPO = "kk051780/toy-wars-factory"
REPO_ID = 1431683395
RC = "rc/p0d-s1-kids-rc01"
WORKFLOW = ".github/workflows/p0d-rc-fastlane.yml"
WORKFLOW_ID = 417604004
PLACE_ARTIFACT = "P0D-FB015-FOREST-BIOMES-FB019V2-PRIVATE80"
REPORT_ARTIFACT = "P0D-ART-GATE-RC80-SAMEHEAD-NO-OWNER-APPROVAL"
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
MAX_BYTES = 64 * 1024 * 1024
PREFIX = f"/repos/{REPO}"


class RedGate(ValueError):
    pass


class Pending(RedGate):
    """Only missing/running exact inputs may be waited for, with a deadline."""


def need(condition, reason):
    if not condition:
        raise RedGate(reason)


def integer(value):
    return type(value) is int and value > 0


def moment(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        raise RedGate("INVALID_TIMESTAMP") from None
    need(result.tzinfo is not None, "NAIVE_TIMESTAMP")
    return result


def load_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def trusted_repo(value):
    return (isinstance(value, dict) and value.get("full_name") == REPO
            and value.get("id") == REPO_ID and value.get("fork") is False)


def context(event_name, payload, check_head, requested_run="", requested_name=""):
    need(isinstance(payload, dict), "INVALID_EVENT_PAYLOAD")
    need(bool(SHA.fullmatch(check_head)), "INVALID_CHECK_HEAD")
    if event_name == "pull_request":
        pr = payload.get("pull_request", {})
        head, base = pr.get("head", {}), pr.get("base", {})
        number = payload.get("number")
        need(integer(number) and pr.get("number") == number, "INVALID_PR_NUMBER")
        need(trusted_repo(head.get("repo")) and trusted_repo(base.get("repo")),
             "FOREIGN_PR_REPOSITORY")
        need(base.get("ref") == RC, "WRONG_PR_BASE_BRANCH")
        need(bool(SHA.fullmatch(head.get("sha", ""))) and
             bool(SHA.fullmatch(base.get("sha", ""))), "INVALID_PR_SHA")
        need(isinstance(head.get("ref"), str) and bool(head["ref"]), "MISSING_PR_BRANCH")
        return {"kind": "PR", "pr": number, "head": head["sha"],
                "base": base["sha"], "branch": head["ref"], "check_head": check_head}
    need(event_name == "workflow_dispatch", "UNSUPPORTED_EVENT")
    need(re.fullmatch(r"[1-9][0-9]*", requested_run) is not None,
         "EXPLICIT_MANUAL_RUN_REQUIRED")
    need(isinstance(requested_name, str) and 0 < len(requested_name) <= 255
         and all(ord(char) >= 32 for char in requested_name), "EXPLICIT_MANUAL_NAME_REQUIRED")
    return {"kind": "MANUAL_EXPLICIT", "run_id": int(requested_run),
            "artifact_name": requested_name, "check_head": check_head}


def rows(response, key):
    data = response.get(key)
    need(isinstance(data, list) and type(response.get("total_count")) is int
         and response["total_count"] == len(data) and len(data) <= 100,
         "INCOMPLETE_OR_INVALID_API_LIST")
    return data


def live_pr(api, ctx):
    pr = api(f"{PREFIX}/pulls/{ctx['pr']}")
    current = context("pull_request", {"number": ctx["pr"], "pull_request": pr},
                      ctx["check_head"])
    need(current == ctx and pr.get("state") == "open", "PR_HEAD_OR_BASE_MOVED")
    if pr.get("merge_commit_sha") is None:
        raise Pending("PR_MERGE_NOT_READY")
    need(pr["merge_commit_sha"] == ctx["check_head"], "PR_MERGE_SHA_MISMATCH")
    ref = api(f"{PREFIX}/git/ref/heads/{RC}")
    need(ref.get("object", {}).get("sha") == ctx["base"], "OFFICIAL_RC_BASE_MOVED")


def validate_run(run, ctx, now):
    need(integer(run.get("id")) and integer(run.get("run_attempt")), "INVALID_RUN_ID")
    need(trusted_repo(run.get("repository")) and trusted_repo(run.get("head_repository")),
         "FOREIGN_RUN_REPOSITORY")
    need(bool(SHA.fullmatch(run.get("head_sha", ""))), "INVALID_RUN_HEAD")
    if ctx["kind"] == "PR":
        need(run.get("workflow_id") == WORKFLOW_ID and run.get("path") == WORKFLOW,
             "WRONG_PRODUCER_WORKFLOW")
        need(run.get("event") == "pull_request" and run.get("head_sha") == ctx["head"]
             and run.get("head_branch") == ctx["branch"], "WRONG_PRODUCER_HEAD_OR_EVENT")
        bindings = run.get("pull_requests")
        need(isinstance(bindings, list) and len(bindings) == 1, "AMBIGUOUS_PR_BINDING")
        binding = bindings[0]
        need(binding.get("number") == ctx["pr"]
             and binding.get("head", {}).get("sha") == ctx["head"]
             and binding.get("head", {}).get("ref") == ctx["branch"]
             and binding.get("base", {}).get("sha") == ctx["base"]
             and binding.get("base", {}).get("ref") == RC
             and binding.get("head", {}).get("repo", {}).get("id") == REPO_ID
             and binding.get("base", {}).get("repo", {}).get("id") == REPO_ID,
             "WRONG_PRODUCER_PR_OR_BASE")
    if run.get("status") in ("queued", "in_progress", "waiting", "pending", "requested"):
        raise Pending("LATEST_PRODUCER_NOT_COMPLETE")
    need(run.get("status") == "completed" and run.get("conclusion") == "success",
         "LATEST_PRODUCER_FAILED")
    need(moment(run.get("created_at")) <= moment(run.get("run_started_at"))
         <= moment(run.get("updated_at")) <= now, "INVALID_RUN_CHRONOLOGY")


def artifact(items, name, run, now):
    matches = [item for item in items if item.get("name") == name]
    if not matches:
        raise Pending("EXACT_ARTIFACT_NOT_READY:" + name)
    need(len(matches) == 1, "DUPLICATE_EXACT_ARTIFACT")
    item = matches[0]
    need(integer(item.get("id")) and integer(item.get("size_in_bytes"))
         and item["size_in_bytes"] <= MAX_BYTES, "EMPTY_OR_INVALID_ARTIFACT")
    need(item.get("expired") is False and moment(item.get("expires_at")) > now,
         "EXPIRED_ARTIFACT")
    need(moment(run["run_started_at"]) <= moment(item.get("created_at")) <= now,
         "ARTIFACT_FROM_OLD_ATTEMPT")
    need(bool(DIGEST.fullmatch(item.get("digest", ""))), "ARTIFACT_DIGEST_REQUIRED")
    origin = item.get("workflow_run", {})
    need(origin.get("id") == run["id"] and origin.get("head_sha") == run["head_sha"]
         and origin.get("head_branch") == run.get("head_branch")
         and origin.get("repository_id") == REPO_ID
         and origin.get("head_repository_id") == REPO_ID, "ARTIFACT_RUN_BINDING_MISMATCH")
    return {key: item[key] for key in ("id", "name", "size_in_bytes", "digest",
                                      "created_at", "expires_at")}


def select(api: Callable, ctx, now):
    if ctx["kind"] == "PR":
        live_pr(api, ctx)
        found = rows(api(f"{PREFIX}/actions/runs?head_sha={ctx['head']}&event=pull_request&per_page=100"),
                     "workflow_runs")
        matching = [run for run in found if run.get("workflow_id") == WORKFLOW_ID
                    or run.get("path") == WORKFLOW]
        if not matching:
            raise Pending("EXACT_PRODUCER_NOT_STARTED")
        need(all(integer(run.get("id")) for run in matching)
             and len({run["id"] for run in matching}) == len(matching), "DUPLICATE_RUN_ID")
        # Choose the newest run before considering success. Never use an older green run.
        latest = max(matching, key=lambda run: (moment(run.get("created_at")), run["id"]))
        run_id = latest["id"]
    else:
        run_id = ctx["run_id"]
    run = api(f"{PREFIX}/actions/runs/{run_id}")
    need(run.get("id") == run_id, "RUN_ID_MISMATCH")
    # Live callers pass a UTC clock: a run may complete during these GETs.
    # Offline snapshots retain their explicit fixed observation time.
    run_observed_at = now() if callable(now) else now
    validate_run(run, ctx, run_observed_at)
    items = rows(api(f"{PREFIX}/actions/runs/{run_id}/artifacts?per_page=100"), "artifacts")
    artifacts_observed_at = now() if callable(now) else now
    names = {"place": PLACE_ARTIFACT, "report": REPORT_ARTIFACT} if ctx["kind"] == "PR" else {
        "place": ctx["artifact_name"]}
    selected = {kind: artifact(items, name, run, artifacts_observed_at) for kind, name in names.items()}
    return {"schema": "P0D_ART_ARTIFACT_SELECTION_V1", "context": ctx,
            "run_id": run_id, "run_attempt": run["run_attempt"],
            "producer_head": run["head_sha"], "producer_path": run.get("path"),
            "artifacts": selected, "selected_at": artifacts_observed_at.isoformat(),
            "art_decision": "ART_NO_GO", "owner_accepted": False}


def same_selection(first, second):
    fields = ("context", "run_id", "run_attempt", "producer_head", "producer_path", "artifacts")
    need(all(first.get(key) == second.get(key) for key in fields), "SELECTION_CHANGED_DURING_DOWNLOAD")


def read_zip(path, meta):
    data = path.read_bytes()
    need(len(data) == meta["size_in_bytes"] and len(data) <= MAX_BYTES,
         "ARTIFACT_ZIP_SIZE_MISMATCH")
    need("sha256:" + hashlib.sha256(data).hexdigest() == meta["digest"],
         "ARTIFACT_ZIP_DIGEST_MISMATCH")
    result = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        need(sum(item.file_size for item in archive.infolist()) <= MAX_BYTES,
             "ARTIFACT_EXPANDED_SIZE_LIMIT")
        for item in archive.infolist():
            name = PurePosixPath(item.filename)
            need(not name.is_absolute() and ".." not in name.parts and "\\" not in item.filename
                 and not stat.S_ISLNK(item.external_attr >> 16), "UNSAFE_ARTIFACT_MEMBER")
            if item.is_dir():
                continue
            need(item.filename not in result, "DUPLICATE_ARTIFACT_MEMBER")
            result[item.filename] = archive.read(item)
    return result


def verify_downloads(selection, place_zip, report_zip=None):
    files = read_zip(place_zip, selection["artifacts"]["place"])
    places = [name for name in files if name.lower().endswith(".rbxlx")]
    need(len(places) == 1, "ART_REAL_PLACE_NOT_UNIQUE")
    place = files[places[0]]
    size, digest = len(place), hashlib.sha256(place).hexdigest()
    need(size > 0, "EMPTY_PLACE")
    if selection["context"]["kind"] == "PR":
        need(report_zip is not None, "SAME_RUN_REPORT_REQUIRED")
        reports = read_zip(report_zip, selection["artifacts"]["report"])
        need("RECEIPT.json" in files and "ART_RC_INTAKE_RECEIPT.json" in reports
             and "ART_CHECK_FOREST_PRIVATE80.json" in reports, "PROVENANCE_RECEIPT_MISSING")
        receipt = load_json(files["RECEIPT.json"])
        provenance = load_json(reports["ART_RC_INTAKE_RECEIPT.json"])
        audit = load_json(reports["ART_CHECK_FOREST_PRIVATE80.json"])
        ctx = selection["context"]
        need(provenance.get("schema") == "P0D_ART_QUALITY_SAMEHEAD_RC80_RECEIPT_V1"
             and provenance.get("github_head") == ctx["check_head"]
             and provenance.get("github_run_id") == str(selection["run_id"])
             and provenance.get("github_ref") == f"refs/pull/{ctx['pr']}/merge",
             "PROVENANCE_MERGE_RUN_OR_REF_MISMATCH")
        need(provenance.get("forest_candidate_source_gate") == "PASS"
             and provenance.get("official_script_count") == 80
             and provenance.get("owner_accepted") is False
             and provenance.get("official_art_adoption_by_this_gate") is False
             and provenance.get("art_decision") == "ART_NO_GO", "PROVENANCE_GATE_MISMATCH")
        need(receipt.get("status") == "PRIVATE_SOURCE_QA_NOT_OFFICIAL"
             and receipt.get("lua_sources") == 80 and receipt.get("rojo_sources_exact") == 80
             and receipt.get("one_game") is True and receipt.get("other79_byte_exact") is True
             and receipt.get("official_rc_adopted") is False
             and receipt.get("owner_art") == "ART_NO_GO", "PLACE_RECEIPT_CONTRACT_MISMATCH")
        source = audit.get("source", {})
        need(receipt.get("place_bytes") == source.get("place_bytes") == size
             and receipt.get("place_sha256") == source.get("place_sha256") == digest,
             "PLACE_RECEIPT_HASH_OR_SIZE_MISMATCH")
        need(source.get("source_gate") == "PASS" and source.get("script_count") == 80
             and audit.get("art_decision") == "ART_NO_GO"
             and audit.get("owner_accepted") is False, "DOWNLOADED_SOURCE_REPORT_MISMATCH")
    return place, {"place_bytes": size, "place_sha256": digest,
                   "original_place_member": places[0],
                   "verification": "AUTHENTIC_INPUT_ONLY_SOURCE_AND_EVIDENCE_AUDITS_STILL_REQUIRED"}


class GitHubReadOnly:
    """Use the runner's existing gh client; no token in command arguments or output."""
    def __call__(self, path):
        need(path.startswith(PREFIX + "/"), "FOREIGN_API_PATH")
        data = subprocess.check_output(["gh", "api", "--method", "GET", path], timeout=30)
        return load_json(data)

    def download(self, artifact_id, destination):
        need(integer(artifact_id), "INVALID_DOWNLOAD_ARTIFACT_ID")
        with destination.open("wb") as output:
            subprocess.run(["gh", "api", "--method", "GET",
                            f"{PREFIX}/actions/artifacts/{artifact_id}/zip"],
                           stdout=output, check=True, timeout=120)


def wait_for_selection(api, ctx, seconds, interval=10, *, clock=time.monotonic,
                       sleep=time.sleep, utcnow=lambda: datetime.now(timezone.utc)):
    need(0 <= seconds <= 600 and 0 < interval <= 30, "INVALID_WAIT_BOUND")
    deadline = clock() + seconds
    while True:
        try:
            return select(api, ctx, utcnow)
        except Pending as error:
            remaining = deadline - clock()
            if remaining <= 0:
                raise RedGate("ART_INPUT_WAIT_TIMEOUT:" + str(error)) from None
            print("ART_INPUT_WAIT", str(error), flush=True)
            sleep(min(interval, remaining))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--event-file", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--run", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--wait-seconds", type=int, default=600)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    try:
        need(os.environ.get("GITHUB_REPOSITORY") == REPO, "WRONG_EXECUTION_REPOSITORY")
        ctx = context(args.event, load_json(args.event_file.read_bytes()), args.head, args.run, args.name)
        api = GitHubReadOnly()
        selection = wait_for_selection(api, ctx, args.wait_seconds)
        args.directory.mkdir(parents=True, exist_ok=True)
        need(not any(args.directory.iterdir()), "INPUT_DIRECTORY_NOT_EMPTY")
        archives = {}
        for kind, meta in selection["artifacts"].items():
            archive = args.directory / (kind + ".zip")
            api.download(meta["id"], archive)
            archives[kind] = archive
        same_selection(selection, select(api, ctx, lambda: datetime.now(timezone.utc)))
        place, verified = verify_downloads(selection, archives["place"], archives.get("report"))
        (args.directory / "SELECTED_AUTHENTIC_ART_INPUT.rbxlx").write_bytes(place)
        selection.update(verified)
        selection["status"] = "VERIFIED_INPUT_NOT_ART_APPROVAL"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + "\n", "utf8")
        if args.github_output:
            with args.github_output.open("a", encoding="utf8") as output:
                output.write(f"run_id={selection['run_id']}\n")
                output.write(f"artifact_name={selection['artifacts']['place']['name']}\n")
                output.write(f"mode={ctx['kind']}\n")
        print("ART_AUTHENTIC_INPUT_VERIFIED", selection["run_id"], verified["place_sha256"])
        return 0
    except (RedGate, KeyError, TypeError, OSError, ValueError, zipfile.BadZipFile,
            subprocess.SubprocessError) as error:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({"status": "FAIL", "reason": str(error),
                                         "art_decision": "ART_NO_GO", "owner_accepted": False},
                                        indent=2) + "\n", "utf8")
        print("ART_AUTHENTIC_INPUT_FAIL", str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
