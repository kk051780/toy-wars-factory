#!/usr/bin/env python3
"""Read-only trusted-main GitHub Actions claim+branch-absence witness candidate.

This tool is designed to run ONLY from a separately reviewed/pinned main Actions
workflow. Its output is a candidate observation, not a provider-signed certificate,
a Reviewer approval, or permission to push, dispatch Roblox, or merge code.
"""
from __future__ import annotations
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid

REPO = "kk051780/toy-wars-factory"
REPO_ID = "1431683395"
WORKFLOW_REF = REPO + "/.github/workflows/twf-controller-claim-witness.yml@refs/heads/main"
API = f"https://api.github.com/repos/{REPO}"
REF = "refs/heads/twf-repair-coordinator"
SRC = re.compile(r"controller/protected-system-([0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
API_PATH = re.compile(r"/(?:git/ref/heads/[a-z0-9\-_/]+|git/commits/[0-9a-f]{40}|git/trees/[0-9a-f]{40}\?recursive=1|contents/ops/REPAIR_COORDINATOR\.json\?ref=[0-9a-f]{40})\Z")
MAX_BODY = 262144


class WitnessHold(ValueError):
    pass


def need(value, code):
    if not value:
        raise WitnessHold(code)


def sha(value):
    return type(value) is str and SHA.fullmatch(value) is not None


def uuid_ok(value):
    try:
        return type(value) is str and str(uuid.UUID(value)) == value
    except (TypeError, AttributeError, ValueError):
        return False


def date(value):
    need(type(value) is str and value.endswith("Z"), "INVALID_TIME")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        raise WitnessHold("INVALID_TIME") from None
    need(d.utcoffset() is not None, "INVALID_TIME")
    return d.astimezone(timezone.utc)


def parse_json(data):
    need(type(data) is bytes and len(data) <= MAX_BODY, "INVALID_PROVIDER_PAYLOAD")
    def pairs(items):
        o = {}
        for k, v in items:
            need(k not in o, "DUPLICATE_JSON_KEY")
            o[k] = v
        return o
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda token: (_ for _ in ()).throw(WitnessHold("INVALID_PROVIDER_JSON")))
    except (UnicodeError, ValueError):
        raise WitnessHold("INVALID_PROVIDER_JSON") from None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise WitnessHold("REDIRECT_REFUSED")


class ProviderReadOnly:
    """Authenticated API read transport. No POST or token output."""
    def __init__(self, token, opener=None):
        need(type(token) is str and len(token) >= 12 and "\n" not in token and "\r" not in token, "CREDENTIAL_MISSING")
        self.__token = token
        self.__opener = opener or build_opener(NoRedirect()).open
        self.queries = 0

    def get(self, path, *, allow_missing=False):
        need(type(path) is str and API_PATH.fullmatch(path), "INVALID_API_ROUTE")
        if allow_missing:
            need(path.startswith('/git/ref/heads/controller/protected-system-') and
                 SRC.fullmatch(path.removeprefix('/git/ref/heads/')) is not None,
                 'MISSING_ONLY_ALLOWED_FOR_UNCREATED_SOURCE_REF')
        self.queries += 1
        need(self.queries <= 12, "QUERY_BOUND")
        req = Request(API + path, method="GET", headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.__token,
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with self.__opener(req, timeout=9) as response:
                need(getattr(response, "status", None) == 200, "PROVIDER_NON_200_HOLD")
                b = response.read(MAX_BODY + 1)
                return parse_json(b)
        except HTTPError as e:
            # A GitHub branch ref 404 is allowed ONLY for the source ref query.
            if allow_missing and e.code == 404:
                return None
            raise WitnessHold("PROVIDER_API_UNAVAILABLE_HOLD") from None
        except WitnessHold:
            raise
        except (URLError, OSError, ValueError, TimeoutError, TypeError):
            raise WitnessHold("PROVIDER_API_UNAVAILABLE_HOLD") from None


def decode_file(obj):
    need(type(obj) is dict and obj.get("encoding") == "base64" and
         type(obj.get("content")) is str and obj.get("type") == "file", "FILE_ENVELOPE_MISMATCH")
    try:
        raw = base64.b64decode("".join(obj["content"].split()), validate=True)
    except (ValueError, TypeError):
        raise WitnessHold("FILE_ENVELOPE_MISMATCH") from None
    need(len(raw) <= MAX_BODY, "FILE_TOO_LARGE")
    git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    need(type(obj.get("size")) is int and obj["size"] == len(raw) and
         sha(obj.get("sha")) and obj["sha"] == git_blob,
         "FILE_BLOB_HASH_MISMATCH")
    payload = parse_json(raw)
    need(type(payload) is dict, "STATE_NOT_DICT")
    return payload


def verify_single_coordinator_change(before_tree, after_tree, before_blob_sha,
                                     after_blob_sha, parent_tree_sha, claim_tree_sha):
    """Check the immutable Git tree diff, not just one file's JSON content.

    A valid coordinator claim modifies exactly ops/REPAIR_COORDINATOR.json.
    Its ancestor `ops` TREE SHA naturally changes too. No unrelated blob,
    symlink, submodule, mode, or tree may change or disappear.
    This remains non-authorizing evidence with caller-supplied provider data.
    """
    target = 'ops/REPAIR_COORDINATOR.json'

    def canonical(snapshot, expected_sha):
        need(type(snapshot) is dict and snapshot.get('sha') == expected_sha and
             snapshot.get('truncated') is False and
             type(snapshot.get('tree')) is list and
             1 <= len(snapshot['tree']) <= 2000,
             'GIT_TREE_INCOMPLETE_OR_WRONG_SHA')
        rows = {}
        for item in snapshot['tree']:
            need(type(item) is dict and type(item.get('path')) is str and
                 item['path'] not in rows and type(item.get('mode')) is str and
                 type(item.get('type')) is str and sha(item.get('sha')),
                 'GIT_TREE_MALFORMED_OR_DUPLICATE')
            rows[item['path']] = (item['type'], item['mode'], item['sha'])
        need(rows.get('ops', (None,))[0:2] == ('tree', '040000') and
             rows.get(target, (None,))[0:2] == ('blob', '100644'),
             'COORDINATOR_FILE_PATH_OR_MODE_CHANGED')
        return rows

    before = canonical(before_tree, parent_tree_sha)
    after = canonical(after_tree, claim_tree_sha)
    need(before.keys() == after.keys(), 'CLAIM_CHANGED_OTHER_PATHS')
    need(before[target][2] == before_blob_sha and
         after[target][2] == after_blob_sha and before_blob_sha != after_blob_sha,
         'CLAIM_TREE_BLOB_NOT_BOUND_TO_CONTENT')
    need(before['ops'][2] != after['ops'][2], 'CLAIM_ANCESTOR_TREE_UNCHANGED')
    for key in before:
        if key in ('ops', target):
            continue
        need(before[key] == after[key], 'CLAIM_CHANGED_OTHER_PATHS')
    return True


def first_party_witness(provider, *, claim_sha, owner_id, epoch, source_branch,
                        main_sha, event_name, event_ref, event_sha, observed_at=None):
    """Purely evaluate connected GitHub GET observations, no authorizing return."""
    need(all(sha(s) for s in (claim_sha, main_sha, event_sha)), "INVALID_SHA")
    need(uuid_ok(owner_id) and type(epoch) is int and epoch > 0, "INVALID_ACTOR")
    match = SRC.fullmatch(source_branch) if type(source_branch) is str else None
    need(match and match.group(1) == owner_id, "UNIQUE_SOURCE_BRANCH_REQUIRED")
    need(event_name == "workflow_dispatch" and event_ref == "refs/heads/main" and
         event_sha == main_sha, "NOT_TRUSTED_MAIN_WORKFLOW")
    current = provider.get("/git/ref/heads/twf-repair-coordinator")
    need(type(current) is dict and current.get("ref") == REF and
         type(current.get("object")) is dict and
         current["object"].get("sha") == claim_sha, "CLAIM_NOT_LIVE_CURRENT_REF")
    commit = provider.get("/git/commits/" + claim_sha)
    need(type(commit) is dict and commit.get("sha") == claim_sha and
         type(commit.get("parents")) is list and len(commit["parents"]) == 1 and
         type(commit["parents"][0]) is dict and sha(commit["parents"][0].get("sha")),
         "CLAIM_PARENT_UNPROVEN")
    parent_sha = commit["parents"][0]["sha"]
    parent = provider.get('/git/commits/' + parent_sha)
    need(type(parent) is dict and parent.get('sha') == parent_sha and
         type(parent.get('tree')) is dict and sha(parent['tree'].get('sha')) and
         type(commit.get('tree')) is dict and sha(commit['tree'].get('sha')),
         'CLAIM_GIT_COMMIT_TREE_UNPROVEN')
    before_file = provider.get("/contents/ops/REPAIR_COORDINATOR.json?ref=" + parent_sha)
    after_file = provider.get("/contents/ops/REPAIR_COORDINATOR.json?ref=" + claim_sha)
    before = decode_file(before_file)
    after = decode_file(after_file)
    need(before.get("holder") is None and
         type(before.get("epoch")) is int and before["epoch"] == epoch - 1,
         "CLAIM_PARENT_BUSY")
    expected = dict(before)
    expected["epoch"] = epoch
    expected["holder"] = after.get("holder")
    need(after == expected, "CLAIM_MUTATED_UNRELATED_STATE")
    h = after.get("holder")
    need(type(h) is dict and h.get("kind") == "CONTROLLER" and
         h.get("owner_id") == owner_id and type(h.get("epoch")) is int and
         h["epoch"] == epoch and h.get("task_id") is None and
         h.get("work_branch") == source_branch and
         h.get("base_main_sha") == main_sha and h.get("origin") == "controller",
         "CLAIM_OWNER_BINDING_FAIL")
    start, stop = date(h.get("acquired_at")), date(h.get("expires_at"))
    need(start < stop and (stop - start).total_seconds() <= 1800,
         "CLAIM_LEASE_INVALID")
    # Runner time is a bounded freshness check, NOT a GitHub-signed time proof.
    check_time = observed_at if observed_at is not None else datetime.now(timezone.utc)
    need(type(check_time) is datetime and check_time.tzinfo is not None and
         check_time.utcoffset() is not None, "INVALID_OBSERVATION_TIME")
    need(start <= check_time.astimezone(timezone.utc) < stop,
         "LEASE_NOT_LIVE_AT_OBSERVATION")
    parent_tree_sha = parent['tree']['sha']
    claim_tree_sha = commit['tree']['sha']
    verify_single_coordinator_change(
        provider.get('/git/trees/' + parent_tree_sha + '?recursive=1'),
        provider.get('/git/trees/' + claim_tree_sha + '?recursive=1'),
        before_file['sha'], after_file['sha'], parent_tree_sha, claim_tree_sha)
    real_main = provider.get("/git/ref/heads/main")
    need(type(real_main) is dict and real_main.get("ref") == "refs/heads/main" and
         type(real_main.get("object")) is dict and
         real_main["object"].get("sha") == main_sha,
         "BASE_MAIN_MOVED")
    # Recheck both mutable refs close to the final source-branch observation.
    # The immutable commit and tree checks above remain authoritative for content.
    # This is not atomic across refs: it narrows a check-then-act window; a future
    # independently authorized writer still requires a fresh own lease and check.
    live_again = provider.get("/git/ref/heads/twf-repair-coordinator")
    need(type(live_again) is dict and live_again.get("ref") == REF and
         type(live_again.get("object")) is dict and
         live_again["object"].get("sha") == claim_sha,
         "CLAIM_MOVED_DURING_WITNESS")
    main_again = provider.get("/git/ref/heads/main")
    need(type(main_again) is dict and main_again.get("ref") == "refs/heads/main" and
         type(main_again.get("object")) is dict and
         main_again["object"].get("sha") == main_sha,
         "MAIN_MOVED_DURING_WITNESS")
    # A 404 is meaningful only after both mutable refs were revalidated.
    # In the Actions host (observed_at=None), also check the original lease
    # remains live at the END, rather than merely before the network roundtrips.
    if observed_at is None:
        need(datetime.now(timezone.utc) < stop, "LEASE_EXPIRED_DURING_WITNESS")
    branch = provider.get("/git/ref/heads/" + source_branch, allow_missing=True)
    need(branch is None, "SOURCE_BRANCH_ALREADY_EXISTS")
    return {
        "status": "CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY",
        "claim_sha": claim_sha, "claim_parent_sha": parent_sha,
        "source_branch": source_branch, "main_sha": main_sha,
        "epoch": epoch,
        "source_branch_not_found_at_checked_time": True,
        "provider_witness_id": "MUST_BIND_TO_AUTHENTICATED_WORKFLOW_RUN_AND_JOB",
        "provider_authenticated": False,
        "independent_review_authorized": False,
        "merge_authorized": False,
        "roblox_post_authorized": False,
    }


def validate_host_context(env):
    """Validate original Actions environment BEFORE any token or provider read.

    Caller-provided env can be spoofed in offline tests. This is a shape/host
    precondition, not an independent provider attestation.
    """
    need(type(env) is dict and
         env.get("GITHUB_REPOSITORY") == REPO and
         env.get("GITHUB_REPOSITORY_ID") == REPO_ID and
         env.get("GITHUB_WORKFLOW_REF") == WORKFLOW_REF and
         env.get("GITHUB_ACTIONS") == "true" and
         env.get("GITHUB_JOB") == "witness" and
         sha(env.get("GITHUB_WORKFLOW_SHA")) and
         env.get("GITHUB_WORKFLOW_SHA") == env.get("GITHUB_SHA") and
         env.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and
         env.get("GITHUB_REF") == "refs/heads/main" and
         sha(env.get("GITHUB_SHA")) and
         type(env.get("GITHUB_RUN_ID")) is str and
         re.fullmatch(r"[1-9][0-9]{0,17}", env["GITHUB_RUN_ID"]) is not None and
         env.get("GITHUB_RUN_ATTEMPT") == "1", "UNTRUSTED_HOST_CONTEXT")
    return True


def bind_actions_run_observation(observation, env):
    """Attach *untrusted* runner labels to a successful candidate observation.

    This is a REVIEWER JOIN KEY, not proof of the label's origin. The
    independent reviewer MUST fetch the real GitHub workflow run and job by
    ID from the original provider, cross-check exact main/job/attempt/head,
    and treat the printed log itself as untrusted without that fetch.
    """
    validate_host_context(env)
    need(type(observation) is dict and
         observation.get('status') == 'CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY' and
         sha(observation.get('claim_sha')) and
         observation.get('main_sha') == env['GITHUB_SHA'] and
         type(observation.get('epoch')) is int and observation['epoch'] > 0 and
         type(observation.get('source_branch')) is str and
         SRC.fullmatch(observation['source_branch']) is not None and
         observation.get('provider_authenticated') is False and
         observation.get('independent_review_authorized') is False and
         observation.get('merge_authorized') is False and
         observation.get('roblox_post_authorized') is False,
         'UNTRUSTED_WITNESS_OBSERVATION')
    result = dict(observation)
    result['reported_actions_origin_untrusted'] = {
        'repository': REPO, 'repository_id': REPO_ID,
        'workflow_ref': WORKFLOW_REF,
        'workflow_sha': env['GITHUB_WORKFLOW_SHA'],
        'job_id': 'witness',
        'run_id': int(env['GITHUB_RUN_ID']),
        'run_attempt': 1,
        'source_main_sha': env['GITHUB_SHA'],
        'claim_sha': observation['claim_sha'],
        'source_branch': observation['source_branch'],
        'epoch': observation['epoch'],
        'provider_authenticated': False,
        'job_log_attested': False,
        'may_review_or_merge': False,
        'may_write_or_publish': False,
    }
    return result


def from_actions_env():
    e = os.environ
    validate_host_context(dict(e))
    return bind_actions_run_observation(first_party_witness(
        ProviderReadOnly(e.get("GH_TOKEN")),
        claim_sha=e.get("TWF_CLAIM_SHA"),
        owner_id=e.get("TWF_OWNER_ID"),
        epoch=int(e.get("TWF_EPOCH", "0")) if re.fullmatch(r"[0-9]{1,8}", e.get("TWF_EPOCH", "")) else -1,
        source_branch=e.get("TWF_SOURCE_BRANCH"),
        main_sha=e.get("TWF_MAIN_SHA"),
        event_name=e.get("GITHUB_EVENT_NAME"),
        event_ref=e.get("GITHUB_REF"),
        event_sha=e.get("GITHUB_SHA"),
    ), dict(e))


if __name__ == "__main__":
    try:
        result = from_actions_env()
        print("CLAIM_WITNESS_READ_ONLY " + json.dumps(result, sort_keys=True))
    except WitnessHold as e:
        print("CLAIM_WITNESS_HOLD " + str(e))
        sys.exit(1)
