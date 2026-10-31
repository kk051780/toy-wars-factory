"""Provider-bridge negative tests: offline, zero tokens, zero network calls."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from system_gemini_bridge_preflight import BridgeError, inspect, WORK_ID

BASE = {
    "schema": 1,
    "work_id": WORK_ID,
    "project_id": "toy-wars-factory",
    "repository": "kk051780/toy-wars-factory",
    "main_sha": "e5deff4d5681bca4823a3da0f848e01bc089ae6e",
    "route": "antigravity_account_interactive",
    "tool": "antigravity-cli",
    "runner": "owner_local",
    "planned_write_set": ["tools/system_gemini_bridge_preflight.py"],
    "gemini_severe_hold": True,
    "request_inference": False,
    "request_write": False,
    "owner_approved_new_inference": False,
    "provider_hard_budget_cap_verified": False,
    "provider_auth_status": "NOT_CONFIGURED",
    "subscription_pays_api_calls": False,
}


class PreflightTests(unittest.TestCase):
    def check_rejected(self, **changes):
        payload = copy.deepcopy(BASE)
        payload.update(changes)
        with self.assertRaises(BridgeError):
            inspect(payload)

    def test_interactive_contract_is_advisory_only(self):
        report = inspect(copy.deepcopy(BASE))
        self.assertEqual(report["status"], "PREPARED_HOLD")
        self.assertEqual(report["evidence_trust"], "UNAUTHENTICATED_CALLER_INPUT")
        for field in ("subscription_or_key_authenticated", "lease_granted",
                      "inference_permitted", "write_permitted", "merge_permitted",
                      "roblox_publish_permitted", "main_sha_verified_from_github"):
            self.assertFalse(report[field])

    def test_headless_api_contract_is_advisory_only(self):
        p = copy.deepcopy(BASE)
        p.update(route="gemini_api_headless", runner="github_actions")
        self.assertFalse(inspect(p)["inference_permitted"])

    def test_old_consumer_gemini_cli_google_login_rejected(self):
        self.check_rejected(tool="gemini-cli")

    def test_unsupported_legacy_route_rejected(self):
        self.check_rejected(route="gemini_cli_google_login")

    def test_headless_cannot_claim_owner_local_account_route(self):
        self.check_rejected(route="gemini_api_headless", runner="owner_local")

    def test_subscription_does_not_pay_for_api_key_calls(self):
        self.check_rejected(subscription_pays_api_calls=True)

    def test_no_secret_fields_or_accidental_embedded_config(self):
        self.check_rejected(GEMINI_API_KEY="never-put-credentials-in-repo")

    def test_no_oauth_cookies_or_tokens(self):
        self.check_rejected(refresh_token="prohibited")

    def test_no_running_inference(self):
        self.check_rejected(request_inference=True)

    def test_no_external_write_claim(self):
        self.check_rejected(request_write=True)

    def test_no_unilateral_hold_release(self):
        self.check_rejected(gemini_severe_hold=False)

    def test_no_unverified_budget_or_approval_claim(self):
        self.check_rejected(owner_approved_new_inference=True)
        self.check_rejected(provider_hard_budget_cap_verified=True)

    def test_no_fake_authentication(self):
        self.check_rejected(provider_auth_status="AUTHENTICATED")

    def test_unknown_or_cross_project_identity(self):
        self.check_rejected(repository="attacker/other")
        self.check_rejected(project_id="other-project")
        self.check_rejected(work_id="TWF-FAKE")

    def test_stale_or_malformed_head(self):
        self.check_rejected(main_sha="main")
        self.check_rejected(main_sha="0" * 39)

    def test_unsafe_or_colliding_paths(self):
        for paths in (["../ops/REPAIR_COORDINATOR.json"], ["/etc/passwd"],
                      ["tools/a.py", "TOOLS/A.PY"], ["a//b"], ["a\\b"],
                      [str(i) for i in range(21)]):
            self.check_rejected(planned_write_set=paths)

    def test_boolean_one_cannot_impersonate_schema_one(self):
        self.check_rejected(schema=True)

    def test_cli_stdout_and_exit_code_are_fail_closed(self):
        cmd = [sys.executable, str(ROOT / "tools/system_gemini_bridge_preflight.py")]
        ok = subprocess.run(cmd, input=json.dumps(BASE), capture_output=True,
                            text=True, check=False, timeout=10)
        self.assertEqual(ok.returncode, 0)
        self.assertFalse(json.loads(ok.stdout)["write_permitted"])
        bad = copy.deepcopy(BASE)
        bad["request_inference"] = True
        denied = subprocess.run(cmd, input=json.dumps(bad), capture_output=True,
                                text=True, check=False, timeout=10)
        self.assertEqual(denied.returncode, 2)
        self.assertFalse(json.loads(denied.stdout)["inference_permitted"])


if __name__ == "__main__":
    unittest.main()
