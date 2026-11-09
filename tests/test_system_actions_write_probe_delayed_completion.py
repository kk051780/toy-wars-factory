"""PR163: source timeout / lease lifetime against one persisted in-memory coordinator.

Exercises the REAL repair_control acquire/owns/release and the REAL
_PerWriteLeaseFence._check_live during probe.run(). The mocked GitHub host is
shared by both contenders: no independent initial_state() lease shortcut.
This is NOT provider attestation or a durable pending_source_action reservation.
"""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import repair_control
import system_actions_write_probe as probe
from test_system_actions_write_probe_partial_dispatch import SCOPE, SHA

NOW = "2026-11-09T00:01:00+00:00"
NEXT_OWNER = "69c043c2-8dfc-470d-91f5-e82a7249d008"
BASE_REF = "b" * 40


class PersistedMockGitHub:
    """One state/ref store for the actual probe and the competing controller."""

    def __init__(self, *, timeout_put=False):
        self.state = repair_control.initial_state()
        self.coord_ref = BASE_REF
        self.cas_count = 0
        self.sent = []
        self.timeout_put = timeout_put
        self.branch_created = False
        self.file_committed = False
        self.delayed_put_in_flight = False

    def call(self, method, path, body=None):
        if method == "GET":
            return {"id": 777}
        self.sent.append((method, path))
        if method == "POST" and path == "/git/refs":
            self.branch_created = True
            return {}
        if method == "PUT" and path.startswith("/contents/ops/probes/"):
            if self.timeout_put:
                self.delayed_put_in_flight = True
                raise probe.ProbeError("GITHUB_TRANSPORT_FAILED")
            self.file_committed = True
            return {}
        raise AssertionError((method, path))

    def sha_ref(self, _api, which):
        if which == "main":
            return SHA
        if which == probe.CONTROL_REF:
            return self.coord_ref
        raise AssertionError(which)

    def state_at(self, _api, sha):
        if sha != self.coord_ref:
            raise probe.ProbeError("MOCK_COORDINATOR_REF_STALE")
        return deepcopy(self.state)

    def cas_state(self, _api, old_ref, new_state):
        if old_ref != self.coord_ref:
            raise probe.ProbeError("MOCK_CAS_CONFLICT")
        self.cas_count += 1
        self.state = deepcopy(new_state)
        self.coord_ref = chr(ord("b") + self.cas_count) * 40
        return self.coord_ref

    def verify_staged(self, _api, _scope):
        if not self.file_committed:
            raise probe.ProbeError("MOCK_SOURCE_NOT_READ_BACK")
        return SHA

    def complete_delayed_put(self):
        if not self.delayed_put_in_flight:
            raise AssertionError("no pending PUT")
        self.file_committed = True
        self.delayed_put_in_flight = False

    def execute(self, *, before_dispatch_failure=False):
        env = {
            "GITHUB_RUN_ID": "777",
            "PROBE_MODE": "BRANCH_ONLY",
            "PROBE_CONSENT": probe.BRANCH_CONSENT,
        }
        scope = {**SCOPE, "branch_only": True}
        with ExitStack() as stack:
            for name, fn in (
                ("checked_context", lambda *_args: dict(scope)),
                ("sha_ref", self.sha_ref),
                ("state_at", self.state_at),
                ("cas_state", self.cas_state),
                ("now", lambda: NOW),
                ("verify_staged_probe", self.verify_staged),
            ):
                stack.enter_context(patch.object(probe, name, fn))
            if before_dispatch_failure:
                def fail_before_write(*_args):
                    raise probe.ProbeError("MAIN_CHANGED")
                stack.enter_context(patch.object(probe, "create_branch_probe",
                                                 fail_before_write))
            # In particular, DO NOT patch probe.acquire, probe.owns,
            # probe.release or _PerWriteLeaseFence._check_live.
            return probe.run(self, env)

    def second_claim(self, at):
        return repair_control.acquire(
            deepcopy(self.state), "CONTROLLER", NEXT_OWNER, at,
            base_main_sha=SHA,
            work_branch="controller/gha-write-probe-778-a1",
        )


class AmbiguousWriteLeaseRegression(unittest.TestCase):
    def test_delayed_put_same_persisted_holder_blocks_next_writer(self):
        host = PersistedMockGitHub(timeout_put=True)
        with self.assertRaisesRegex(
            probe.ProbeError,
            r"^GITHUB_TRANSPORT_FAILED__SOURCE_MUTATIONS_ATTEMPTED_2__PARTIAL_WRITE_POSSIBLE__SOURCE_ACTION_UNRESOLVED_NO_RELEASE$",
        ):
            host.execute()

        self.assertEqual(host.sent[0], ("POST", "/git/refs"))
        self.assertEqual(host.sent[1][0], "PUT")
        self.assertEqual(len(host.sent), 2)  # no automatic retry
        self.assertEqual(host.cas_count, 1)   # claim persisted; release not sent
        self.assertEqual(host.state["holder"]["owner_id"], SCOPE["owner"])
        self.assertEqual(host.state["holder"]["epoch"], 1)

        contender = host.second_claim("2026-11-09T00:01:01+00:00")
        self.assertFalse(contender["write"])
        self.assertEqual(contender["action"], "WAIT_LOCK")

        # The old request can still complete AFTER the unknown-ACK failure.
        host.complete_delayed_put()
        self.assertTrue(host.file_committed)
        after_commit = host.second_claim("2026-11-09T00:01:02+00:00")
        self.assertFalse(after_commit["write"])
        self.assertEqual(after_commit["action"], "WAIT_LOCK")

        # Expiring the lease does not prove that the HTTP request terminated.
        after_expiry = host.second_claim("2026-11-09T00:32:01+00:00")
        self.assertFalse(after_expiry["write"])
        self.assertEqual(after_expiry["action"], "WAIT_RECOVERY")
        self.assertEqual(host.cas_count, 1)
        self.assertEqual(host.state["holder"]["owner_id"], SCOPE["owner"])

    def test_normal_verified_put_releases_persisted_holder(self):
        host = PersistedMockGitHub()
        result = host.execute()
        self.assertEqual(result["status"], "BRANCH_VERIFIED_NO_PR_REQUEST")
        self.assertTrue(host.file_committed)
        self.assertEqual(host.cas_count, 2)  # claim + own release
        self.assertIsNone(host.state["holder"])
        contender = host.second_claim("2026-11-09T00:01:02+00:00")
        self.assertEqual(contender["action"], "ACQUIRE")
        self.assertTrue(contender["write"])
        self.assertEqual(contender["state"]["epoch"], 2)

    def test_before_any_source_dispatch_releases_persisted_holder(self):
        host = PersistedMockGitHub()
        with self.assertRaisesRegex(probe.ProbeError, r"^MAIN_CHANGED$"):
            host.execute(before_dispatch_failure=True)
        self.assertEqual(host.sent, [])
        self.assertEqual(host.cas_count, 2)
        self.assertIsNone(host.state["holder"])
        self.assertTrue(host.second_claim("2026-11-09T00:01:02+00:00")["write"])


if __name__ == "__main__":
    unittest.main()
