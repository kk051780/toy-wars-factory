"""Offline, non-authorizing Gemini/Antigravity provider handoff preflight.

This tool neither contacts Google/GitHub nor reads environment credentials. It cannot
authenticate observations, grant a lease, enable inference, merge, or publish.
"""
import json
import re
import sys

WORK_ID = "TWF-PROVIDER-BRIDGE-ANTIGRAVITY-GEMINI-20261031"
REPOSITORY = "kk051780/toy-wars-factory"
ROUTES = {
    "antigravity_account_interactive": ("antigravity-cli", "owner_local"),
    "gemini_api_headless": ("antigravity-cli", "github_actions"),
}
FIELDS = frozenset({
    "schema", "work_id", "project_id", "repository", "main_sha",
    "route", "tool", "runner", "planned_write_set",
    "gemini_severe_hold", "request_inference", "request_write",
    "owner_approved_new_inference", "provider_hard_budget_cap_verified",
    "provider_auth_status", "subscription_pays_api_calls",
})
SAFE_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\/-]{0,199}$")
SHA = re.compile(r"^[a-f0-9]{40}$")


class BridgeError(ValueError):
    """Invalid or falsely authorizing handoff intent."""


def _required(value, expected, name):
    if type(value) is not type(expected) or value != expected:
        raise BridgeError("unexpected " + name)


def _check_paths(paths):
    if not isinstance(paths, list) or len(paths) > 20:
        raise BridgeError("invalid planned_write_set")
    seen = set()
    for path in paths:
        if not isinstance(path, str) or not SAFE_PATH.fullmatch(path):
            raise BridgeError("invalid planned path")
        parts = path.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise BridgeError("unsafe planned path")
        identity = path.casefold()
        if identity in seen:
            raise BridgeError("duplicate case-insensitive planned path")
        seen.add(identity)


def inspect(contract):
    """Validate an untrusted *proposal* and return an advisory, never authority."""
    if not isinstance(contract, dict) or set(contract) != FIELDS:
        raise BridgeError("missing or unknown contract fields")
    _required(contract["schema"], 1, "schema")
    _required(contract["work_id"], WORK_ID, "work_id")
    _required(contract["project_id"], "toy-wars-factory", "project_id")
    _required(contract["repository"], REPOSITORY, "repository")
    main_sha = contract["main_sha"]
    if not isinstance(main_sha, str) or not SHA.fullmatch(main_sha):
        raise BridgeError("invalid main SHA")
    route = contract["route"]
    if not isinstance(route, str) or route not in ROUTES:
        raise BridgeError("unsupported auth route (legacy Gemini CLI consumer login is retired)")
    tool, runner = ROUTES[route]
    _required(contract["tool"], tool, "tool")
    _required(contract["runner"], runner, "runner")
    _check_paths(contract["planned_write_set"])
    _required(contract["gemini_severe_hold"], True, "gemini_severe_hold")
    for field in ("request_inference", "request_write",
                  "owner_approved_new_inference", "provider_hard_budget_cap_verified",
                  "subscription_pays_api_calls"):
        _required(contract[field], False, field)
    _required(contract["provider_auth_status"], "NOT_CONFIGURED", "provider_auth_status")

    return {
        "schema": 1,
        "work_id": WORK_ID,
        "route": route,
        "status": "PREPARED_HOLD",
        "evidence_trust": "UNAUTHENTICATED_CALLER_INPUT",
        "main_sha_verified_from_github": False,
        "subscription_or_key_authenticated": False,
        "lease_granted": False,
        "inference_permitted": False,
        "write_permitted": False,
        "merge_permitted": False,
        "roblox_publish_permitted": False,
        "next": [
            "Independently confirm current GitHub main/issue/PR and exclusive CAS lease",
            "Use owner-controlled sign-in for interactive Antigravity only",
            "Treat headless Gemini API key quota/billing separately from subscription",
            "Keep Gemini severe hold until separately resolved and reapproved",
            "Require exact-head QA and independent review before any integration",
        ],
    }


def main():
    try:
        payload = json.load(sys.stdin)
        result = inspect(payload)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (BridgeError, ValueError, TypeError, OSError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc),
                          "inference_permitted": False, "write_permitted": False},
                         sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
