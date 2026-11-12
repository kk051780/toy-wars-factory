"""P0-D S1 Open Cloud read-only Luau probe runner; offline preview by default.

No Roblox place upload/publish, no SavePlaceAsync, no automatic CI trigger.
The exact private staging place/version -> RC source mapping is an OWNER attestation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)

EXPECTED_RC = "1263a03701211a652b99b91d2339575dc8104eff"
BASE = "https://apis.roblox.com/cloud/v2/"
PROBE_PATH = Path(__file__).with_name("OpenCloudS1Probe.luau")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_receipt(receipt, script_bytes):
    """Fail closed: no latest-place tests and no production/live targets."""
    required = {"environment", "rc_commit_sha", "universe_id", "place_id",
                "version_id", "probe_sha256", "owner_approved_for_readonly_cloud_qa"}
    if set(receipt) != required:
        raise ValueError("invalid receipt schema")
    if receipt["environment"] != "PRIVATE_STAGING":
        raise ValueError("only PRIVATE_STAGING is supported")
    if receipt["rc_commit_sha"] != EXPECTED_RC:
        raise ValueError("stale or incorrect RC pin")
    if receipt["owner_approved_for_readonly_cloud_qa"] is not True:
        raise ValueError("explicit OWNER approval missing")
    for field in ("universe_id", "place_id", "version_id"):
        value = receipt[field]
        if type(value) is not int or value <= 0:
            raise ValueError("invalid " + field)
    if not re.fullmatch(r"[0-9a-f]{64}", receipt["probe_sha256"]):
        raise ValueError("invalid probe digest")
    if receipt["probe_sha256"] != sha256(script_bytes):
        raise ValueError("probe source SHA256 mismatch")
    return receipt


def task_endpoint(receipt):
    return (BASE + "universes/{}/places/{}/versions/{}/luau-execution-session-tasks"
            .format(receipt["universe_id"], receipt["place_id"], receipt["version_id"]))


def safe_task_url(name, receipt):
    """Never follow a server-supplied arbitrary URL/path."""
    prefix = "universes/{}/places/{}/versions/{}/luau-execution-sessions/".format(
        receipt["universe_id"], receipt["place_id"], receipt["version_id"])
    if not isinstance(name, str) or not name.startswith(prefix):
        raise ValueError("task path is not in the expected staging place/version")
    suffix = name[len(prefix):]
    if not re.fullmatch(r"[A-Za-z0-9_-]+/tasks/[A-Za-z0-9_-]+", suffix):
        raise ValueError("invalid task path")
    return BASE + name


def request_json(url, key, body=None):
    headers = {"x-api-key": key, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if body is not None else "GET")
    # No redirects to arbitrary hosts, token printed nowhere.
    with _OPENER.open(req, timeout=20) as resp:
        if resp.url != url:
            raise ValueError("unexpected API redirect")
        return json.load(resp)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--receipt", help="Local owner-approved PRIVATE_STAGING receipt JSON")
    ap.add_argument("--execute", action="store_true", help="Submit ONE read-only engine task")
    ap.add_argument("--owner-approved", action="store_true", help="Owner confirms task in staging")
    args = ap.parse_args(argv)
    script_bytes = PROBE_PATH.read_bytes()
    print(json.dumps({"mode": "EXECUTE" if args.execute else "OFFLINE_PREVIEW",
                      "probe_sha256": sha256(script_bytes), "expected_rc": EXPECTED_RC}, sort_keys=True))
    if not args.execute:
        return 0
    if not args.owner_approved or not args.receipt:
        raise ValueError("--execute requires --owner-approved and --receipt")
    receipt = validate_receipt(json.loads(Path(args.receipt).read_text(encoding="utf-8")), script_bytes)
    key = os.environ.get("RBLX_OC_API_KEY", "")
    if not key:
        raise ValueError("RBLX_OC_API_KEY is not configured")
    url = task_endpoint(receipt)
    result = request_json(url, key, {"script": script_bytes.decode("utf-8")})
    task_url = safe_task_url(result.get("path"), receipt)
    end = time.monotonic() + 270
    while time.monotonic() < end:
        task = request_json(task_url, key)
        if task.get("state") not in ("PROCESSING", "PENDING", "QUEUED", "CREATED"):
            break
        time.sleep(3)
    else:
        raise TimeoutError("cloud task did not complete")
    if task.get("state") != "COMPLETE":
        raise RuntimeError("cloud task not complete: " + str(task.get("state")))
    logs = request_json(task_url + "/logs", key)
    entries = logs.get("luauExecutionSessionTaskLogs", [])
    messages = "\n".join(m for ent in entries for m in ent.get("messages", []) if isinstance(m, str))
    if "P0D_CLOUD_GATE_PASS checked=" not in messages or "P0D_CLOUD_GATE_FAIL" in messages:
        raise RuntimeError("missing positive gate evidence or reported failed probe")
    print(json.dumps({"status": "CLOUD_HEADLESS_SOURCE_GATE_ONLY",
                      "task": result["path"], "place_version": receipt["version_id"],
                      "probe_sha256": sha256(script_bytes), "two_client_mobile": "NOT_TESTED",
                      "human_playtest": "NOT_TESTED", "publish_authorized": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, TimeoutError, OSError, urllib.error.URLError) as e:
        print("CLOUD_GATE_BLOCKED " + str(e), file=sys.stderr)
        sys.exit(2)
