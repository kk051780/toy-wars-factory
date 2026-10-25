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
STATES = {"NOT_RUN", "PASS", "FAIL"}
ROLES = ("author", "reviewer", "meta")
GATES = ("offline", "engine", "two_client", "mobile", "playtest")
PROJECT_FIELDS = {"schema", "game_id", "title", "platform", "phase",
                  "repository", "coordination_ref", "roles", "game_design",
                  "quality", "safety", "source_prefix", "tests_prefix"}
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
    if data["schema"] != 1 or type(data["game_id"]) is not str or not ID.fullmatch(data["game_id"]):
        raise InvalidProject("invalid project schema or game ID")
    if type(data["title"]) is not str or not 2 <= len(data["title"]) <= 100:
        raise InvalidProject("invalid title")
    if data["platform"] != "roblox" or data["phase"] not in ("BOUND_OBSERVE", "UNBOUND_TEMPLATE"):
        raise InvalidProject("unsupported platform or phase")
    _object(data["roles"], ROLES, "roles")
    _object(data["quality"], GATES, "quality")
    if any(v not in STATES for v in data["quality"].values()):
        raise InvalidProject("unknown quality evidence state")
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
                data["roles"].values()) or any(v != "NOT_RUN" for v in data["quality"].values()):
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
    if raw["schema"] != 1 or type(raw["projects"]) is not list or not 1 <= len(raw["projects"]) <= 100:
        raise InvalidProject("portfolio schema or capacity")
    if any(type(path) is not str for path in raw["projects"]):
        raise InvalidProject("manifest references must be string paths")
    if len(set(raw["projects"])) != len(raw["projects"]):
        raise InvalidProject("duplicate manifest paths")
    projects = []
    seen_ids, seen_repos, seen_tasks = set(), set(), set()
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
            roles = set(project["roles"].values())
            if seen_tasks & roles:
                raise InvalidProject("a task has cross-game authority")
            seen_tasks.update(roles)
        projects.append(project)
    return projects


def evaluate(project, observation=None):
    """Read-only recommendation. No GitHub writes, provider calls, or dispatch."""
    result = {"game_id": project["game_id"], "repository": project["repository"],
              "mode": "ADVISORY_ONLY", "action": "HOLD", "alerts": [],
              "release_eligible": False, "declared_engine_gate": project["quality"]["engine"], "engine_evidence_verified": False}
    if project["phase"] == "UNBOUND_TEMPLATE":
        result["action"] = "UNBOUND_TEMPLATE"
        return result
    if type(observation) is not dict:
        result["action"] = "HOLD_NO_OBSERVATION"
        return result
    # An observation is untrusted telemetry, never an instruction or proof of success.
    if observation.get("repository") != project["repository"]:
        result["action"] = "HOLD_FOREIGN_REPOSITORY"
        return result
    if not all(type(observation.get(k)) is str and SHA.fullmatch(observation[k])
               for k in ("main_head", "main_qa_head")):
        result["action"] = "HOLD_MISSING_HEAD"
        return result
    if observation.get("meta_run") == "no_update":
        result["alerts"].append("META_NO_UPDATE")
    if observation.get("worker_run") == "no_update":
        result["alerts"].append("WORKER_NO_UPDATE")
    if observation.get("reviewer_run") == "no_update":
        result["alerts"].append("REVIEWER_NO_UPDATE")
    if observation.get("lease") is not None:
        result["action"] = "JOIN_EXISTING_LEASE"
    elif observation["main_head"] != observation["main_qa_head"]:
        result["action"] = "WAIT_EXACT_MAIN_QA"
    elif observation.get("main_qa") == "failure":
        result["action"] = "REPAIR_MAIN_FIRST"
    elif observation.get("main_qa") != "success":
        result["action"] = "WAIT_MAIN_QA"
    else:
        prs = observation.get("open_prs")
        if type(prs) is not list or any(type(p) is not dict for p in prs):
            result["action"] = "HOLD_INVALID_PR_QUEUE"
        elif len(prs) > project["safety"]["max_open_prs"]:
            result["action"] = "HOLD_PR_CAPACITY_BREACH"
        elif any(p.get("ci") == "success" and p.get("head_sha") == p.get("ci_head_sha")
                 and type(p.get("head_sha")) is str and SHA.fullmatch(p["head_sha"])
                 for p in prs):
            result["action"] = "REQUEST_INDEPENDENT_REVIEW"
        elif len(prs) >= project["safety"]["max_open_prs"]:
            result["action"] = "WAIT_PR_CAPACITY"
        elif observation.get("worker_run") == "no_update":
            result["action"] = "DIAGNOSE_WORKER"
        else:
            result["action"] = "CANDIDATE_DRAFT_ONLY"
    # A PASS in a fixture does not override a release prohibition or the lack
    # of engine, actual client-device, and real-player evidence.
    return result


def plan(root, portfolio, observations=None):
    projects = load_portfolio(root, portfolio)
    if observations is None:
        data = {}
    else:
        raw = _json_at(root, observations)
        _object(raw, ("schema", "projects"), "observations")
        if raw["schema"] != 1 or type(raw["projects"]) is not dict:
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
