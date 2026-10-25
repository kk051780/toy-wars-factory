"""Portable, stdlib-only multi-game control-plane v0: validation and READ-ONLY planning.

Not a scheduler, AI service, Roblox integration, or publishing tool.
All observations supplied on disk are advisory and have no authority.
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import re

ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
TASK_ID = re.compile(r"[0-9a-f]{32}\Z")
RUN_ID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
STATES = {"NOT_RUN", "PASS", "FAIL"}
ROLES = ("author", "reviewer", "meta")
GATES = ("offline", "engine", "two_client", "mobile", "playtest")
PROJECT_FIELDS = {"schema", "game_id", "title", "platform", "phase",
                  "repository", "coordination_ref", "roles", "game_design",
                  "quality", "safety", "source_prefix", "tests_prefix", "ci_provenance"}
SAFETY_FIELDS = {"draft_only", "independent_review", "exact_head_ci",
                 "post_merge_main_qa", "auto_publish", "external_inference",
                 "daily_external_budget_usd", "max_open_prs"}


class InvalidProject(ValueError):
    pass


def _object(value, keys, title):
    if type(value) is not dict or set(value) != set(keys):
        raise InvalidProject(title + ": required/allowed fields differ")
    return value


def _safe_path(root, path):
    if type(path) is not str or not path or "\\" in path:
        raise InvalidProject("invalid relative path")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(x in ("..", ".", ".git") for x in path.split("/")):
        raise InvalidProject("unsafe relative path")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise InvalidProject("path escapes portfolio root")
    return resolved


def _json_at(root, path):
    location = _safe_path(root, path)
    if not location.is_file() or location.stat().st_size > 131072:
        raise InvalidProject("missing or oversized manifest: " + path)
    try:
        return json.loads(location.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidProject("invalid JSON: " + path) from exc


def validate_project(data):
    _object(data, PROJECT_FIELDS, "project")
    if type(data["schema"]) is not int or data["schema"] != 1 or type(data["game_id"]) is not str or not ID.fullmatch(data["game_id"]):
        raise InvalidProject("invalid project schema or game ID")
    if type(data["title"]) is not str or not 2 <= len(data["title"]) <= 100:
        raise InvalidProject("invalid title")
    if data["platform"] != "roblox" or data["phase"] not in ("BOUND_OBSERVE", "UNBOUND_TEMPLATE"):
        raise InvalidProject("unsupported platform or phase")
    _object(data["roles"], ROLES, "roles")
    _object(data["quality"], GATES, "quality")
    if any(type(v) is not str or v not in STATES for v in data["quality"].values()):
        raise InvalidProject("unknown quality evidence state")
    if data["phase"] == "UNBOUND_TEMPLATE":
        if data["ci_provenance"] is not None:
            raise InvalidProject("unbound template cannot declare trusted CI")
    else:
        provenance = _object(data["ci_provenance"], ("workflow_path", "app_slug", "app_id"), "CI provenance")
        if (type(provenance["workflow_path"]) is not str or
                re.fullmatch(r"\.github/workflows/[A-Za-z0-9_.-]+\.yml", provenance["workflow_path"]) is None or
                provenance["app_slug"] != "github-actions" or
                type(provenance["app_id"]) is not int or provenance["app_id"] != 15368):
            raise InvalidProject("invalid trusted GitHub Actions workflow origin")
    _object(data["safety"], SAFETY_FIELDS, "safety")
    guard = data["safety"]
    for required_true in ("draft_only", "independent_review", "exact_head_ci",
                          "post_merge_main_qa"):
        if guard[required_true] is not True:
            raise InvalidProject("a mandatory review gate was weakened: " + required_true)
    for forbidden in ("auto_publish", "external_inference"):
        if guard[forbidden] is not False:
            raise InvalidProject("external execution or public release is not authorized")
    if type(guard["daily_external_budget_usd"]) not in (int, float) or guard["daily_external_budget_usd"] != 0:
        raise InvalidProject("prototype has a zero-external-spend hard cap")
    if type(guard["max_open_prs"]) is not int or not 1 <= guard["max_open_prs"] <= 3:
        raise InvalidProject("invalid bounded PR capacity")
    _object(data["game_design"], ("genre", "core_loop", "audience", "novelty_hypothesis"), "design")
    design = data["game_design"]
    if any(type(design[key]) is not str or not 2 <= len(design[key]) <= 300
           for key in ("genre", "audience", "novelty_hypothesis")):
        raise InvalidProject("missing product intent")
    if type(design["core_loop"]) is not list or not 3 <= len(design["core_loop"]) <= 8 or any(
            type(x) is not str or not 2 <= len(x) <= 120 for x in design["core_loop"]):
        raise InvalidProject("gameplay loop must have 3-8 steps")
    if data["phase"] == "UNBOUND_TEMPLATE":
        if any(data[key] is not None for key in ("repository", "coordination_ref", "source_prefix", "tests_prefix")) or any(
                (value is not None for value in data["roles"].values())) or any(v != "NOT_RUN" for v in data["quality"].values()):
            raise InvalidProject("unbound templates must have no repository, tasks, or evidence")
    else:
        repo = data["repository"]
        if type(repo) is not str or not REPO.fullmatch(repo) or ".." in repo or repo.startswith("-"):
            raise InvalidProject("bound project needs an explicit owner/repository")
        ref = data["coordination_ref"]
        if type(ref) is not str or not ID.fullmatch(ref):
            raise InvalidProject("bound project needs an independent coordination ref")
        for role in ROLES:
            value = data["roles"][role]
            if type(value) is not str or not TASK_ID.fullmatch(value):
                raise InvalidProject("bound project needs canonical task IDs")
        if len(set(data["roles"].values())) != 3:
            raise InvalidProject("an author cannot act as their own reviewer/meta")
        for field in ("source_prefix", "tests_prefix"):
            val = data[field]
            if type(val) is not str or not ID.fullmatch(val):
                raise InvalidProject("unsafe game source/test namespace")
    return data


def load_portfolio(root, portfolio):
    raw = _json_at(root, portfolio)
    _object(raw, ("schema", "projects"), "portfolio")
    if type(raw["schema"]) is not int or raw["schema"] != 1 or type(raw["projects"]) is not list or not 1 <= len(raw["projects"]) <= 100:
        raise InvalidProject("portfolio schema or capacity")
    if any(type(path) is not str for path in raw["projects"]):
        raise InvalidProject("manifest references must be string paths")
    if len(set(raw["projects"])) != len(raw["projects"]):
        raise InvalidProject("duplicate manifest paths")
    projects = []
    seen_ids, seen_repos, seen_tasks, seen_coord_refs = set(), set(), set(), set()
    for path in raw["projects"]:
        project = validate_project(_json_at(root, path))
        identifier = project["game_id"]
        if identifier in seen_ids:
            raise InvalidProject("duplicate game ID " + identifier)
        seen_ids.add(identifier)
        if project["phase"] == "BOUND_OBSERVE":
            repo = project["repository"].casefold()
            if repo in seen_repos:
                raise InvalidProject("multiple projects targeting one repository")
            seen_repos.add(repo)
            coord_key = project["coordination_ref"].casefold()
            if coord_key in seen_coord_refs:
                raise InvalidProject("duplicate coordination ref across games")
            seen_coord_refs.add(coord_key)
            roles = set(project["roles"].values())
            if seen_tasks & roles:
                raise InvalidProject("a task has cross-game authority")
            seen_tasks.update(roles)
        projects.append(project)
    return projects


def evaluate(project, observation=None):
    """Untrusted, READ-ONLY triage: never grants a new task, merge, or publication.

    Future live GitHub evidence adapters must explicitly authorize a *different*
    execution path. A JSON observation can be forged, omitted or stale.
    """
    result = {
        "game_id": project["game_id"], "repository": project["repository"],
        "mode": "ADVISORY_ONLY", "action": "HOLD_UNVERIFIED_INPUT",
        "diagnostic": "NONE", "alerts": [], "dispatch_allowed": False,
        "evidence_authority": "UNTRUSTED_JSON", "release_eligible": False,
        "declared_engine_gate": project["quality"]["engine"],
        "engine_evidence_verified": False,
    }
    if project["phase"] == "UNBOUND_TEMPLATE":
        result["action"] = "UNBOUND_TEMPLATE"
        return result
    if type(observation) is not dict:
        result["action"] = "HOLD_NO_OBSERVATION"
        return result
    if observation.get("repository") != project["repository"]:
        result["action"] = "HOLD_FOREIGN_REPOSITORY"
        return result
    if not all(type(observation.get(k)) is str and SHA.fullmatch(observation[k])
               for k in ("main_head", "main_qa_head")):
        result["action"] = "HOLD_MISSING_HEAD"
        return result
    for role in ("meta", "worker", "reviewer"):
        if observation.get(role + "_run") == "no_update":
            result["alerts"].append(role.upper() + "_NO_UPDATE")
    # A claimed idle lease cannot prove the current real coordinator is idle.
    # A claimed occupied lease can only produce conservative diagnostics.
    if "lease" not in observation:
        result["diagnostic"] = "LEASE_STATUS_MISSING"
        return result
    lease = observation["lease"]
    if lease is not None:
        if (type(lease) is not dict or set(lease) != {"kind", "owner_run_id", "epoch"} or
                lease["kind"] not in ("WORKER", "REVIEWER", "META", "CONTROLLER", "DISPATCH") or
                type(lease["owner_run_id"]) is not str or
                not RUN_ID.fullmatch(lease["owner_run_id"]) or
                type(lease["epoch"]) is not int or lease["epoch"] <= 0):
            result["diagnostic"] = "INVALID_LEASE_CLAIM"
        else:
            result["diagnostic"] = "LEASE_CLAIM_UNVERIFIED"
        return result
    if observation["main_head"] != observation["main_qa_head"]:
        result["diagnostic"] = "WAIT_EXACT_MAIN_QA"
        return result
    if observation.get("main_qa") == "failure":
        result["diagnostic"] = "REPAIR_MAIN_FIRST"
        return result
    if observation.get("main_qa") != "success":
        result["diagnostic"] = "WAIT_MAIN_QA"
        return result
    prs = observation.get("open_prs")
    if type(prs) is not list or any(type(p) is not dict for p in prs):
        result["diagnostic"] = "HOLD_INVALID_PR_QUEUE"
    elif len(prs) > project["safety"]["max_open_prs"]:
        result["diagnostic"] = "HOLD_PR_CAPACITY_BREACH"
    elif prs:
        # An existing draft always gets attention before generating a new one.
        # It is not possible to approve or merge a PR using this JSON alone.
        if any(p.get("ci") == "failure" for p in prs):
            result["diagnostic"] = "REPAIR_EXISTING_PR_CI"
        elif any(not (type(p.get("head_sha")) is str and SHA.fullmatch(p["head_sha"]) and
                        p.get("head_sha") == p.get("ci_head_sha") and p.get("ci") == "success")
                 for p in prs):
            result["diagnostic"] = "WAIT_EXISTING_PR_CI"
        else:
            result["diagnostic"] = "REVIEW_CANDIDATE_UNVERIFIED"
    elif observation.get("worker_run") == "no_update":
        result["diagnostic"] = "DIAGNOSE_WORKER"
    else:
        result["diagnostic"] = "POTENTIAL_DRAFT_UNVERIFIED"
    # action remains HOLD_UNVERIFIED_INPUT regardless of apparent CI success.
    # Neither a field claiming PASS nor an absent lease constitutes authorization.
    return result


def plan(root, portfolio, observations=None):
    projects = load_portfolio(root, portfolio)
    if observations is None:
        data = {}
    else:
        raw = _json_at(root, observations)
        _object(raw, ("schema", "projects"), "observations")
        if type(raw["schema"]) is not int or raw["schema"] != 1 or type(raw["projects"]) is not dict:
            raise InvalidProject("invalid observations file")
        data = raw["projects"]
        known = {p["game_id"] for p in projects}
        if set(data) - known:
            raise InvalidProject("unknown game in observations")
    return [evaluate(p, data.get(p["game_id"])) for p in projects]


def main():
    parser = argparse.ArgumentParser(description="Read-only multi-game plan; NEVER runs agents or deploys.")
    parser.add_argument("command", choices=("validate", "plan"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--portfolio", default="studio_autopilot/portfolio.json")
    parser.add_argument("--observations", default=None)
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve()
        output = ({"validated_projects": [p["game_id"] for p in load_portfolio(root, args.portfolio)],
                   "execution": "DISABLED"} if args.command == "validate"
                  else {"decisions": plan(root, args.portfolio, args.observations),
                        "execution": "DISABLED", "evidence_scope": "ADVISORY_INPUT_NOT_VERIFIED"})
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    except InvalidProject as exc:
        parser.exit(2, "FAIL_CLOSED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
