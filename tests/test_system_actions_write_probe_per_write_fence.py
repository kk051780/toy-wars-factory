"""PR163 P0: per-write ownership fencing; all transports synthetic, no real GitHub calls."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import inspect
import base64
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import system_actions_write_probe as p

MAIN = "a" * 40
CLAIM = "b" * 40
FOREIGN = "c" * 40
OWNER = "473ba135-4cdb-4e5c-8f96-08e734c698da"
EPOCH = 340
SCOPE = {
    "owner": OWNER, "main": MAIN,
    "branch": "controller/gha-write-probe-41199998877-a1",
    "run_id": 41199998877, "attempt": 1,
}
TARGET = "/contents/ops/probes/gha-write-41199998877-a1.json"
OPS = [("POST", "/git/refs"), ("PUT", TARGET), ("POST", "/pulls")]


def approved_bodies():
    """Known public test-only bytes, identical to the production caller."""
    info = {"schema": 1, "kind": "OWNER_MANUAL_GHA_CAPABILITY_PROBE_ONLY",
            "source_main_sha": MAIN, "github_run_id": SCOPE["run_id"],
            "run_attempt": SCOPE["attempt"], "status": "NO_AI_NO_GAME_CHANGE"}
    return [
        {"ref": "refs/heads/" + SCOPE["branch"], "sha": MAIN},
        {"message": "probe: isolated owner-manual write only",
         "branch": SCOPE["branch"],
         "content": base64.b64encode(
             (json.dumps(info, sort_keys=True) + "\n").encode()).decode()},
        {"title": "[PROBE ONLY] Owner-manual GitHub Actions branch/PR permission",
         "head": SCOPE["branch"], "base": "main", "draft": True,
         "body": "Non-production, no game files, no AI inference, no merge authorization. "
                 "Confirm separate reviewer and delete only by authorized owner after audit."},
    ]


def holder():
    return {
        "kind": "CONTROLLER", "owner_id": OWNER, "epoch": EPOCH,
        "task_id": None, "work_branch": SCOPE["branch"],
        "base_main_sha": MAIN,
    }


class FakeAPI:
    def __init__(self):
        self.main = MAIN
        self.ref = CLAIM
        self.state = {"holder": holder(), "epoch": EPOCH}
        self.calls = []
        self.after_write = None

    def call(self, method, path, body=None):
        self.calls.append((method, path))
        if self.after_write:
            self.after_write(self)
        return {"ok": True}


class FenceTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.sha = patch.object(p, "sha_ref", side_effect=self.ref_sha)
        self.state = patch.object(p, "state_at", side_effect=self.get_state)
        self.owns = patch.object(p, "owns", side_effect=self._owns)
        self.clock = patch.object(p, "now", return_value="2026-10-31T09:25:00+00:00")
        for m in (self.sha, self.state, self.owns, self.clock):
            m.start()
            self.addCleanup(m.stop)

    def ref_sha(self, api, branch):
        return api.main if branch == "main" else api.ref

    def get_state(self, api, ref):
        return deepcopy(api.state)

    @staticmethod
    def _owns(state, kind, owner, epoch, at):
        h = state.get("holder")
        return bool(h and (h.get("kind"), h.get("owner_id"), h.get("epoch")) ==
                    (kind, owner, epoch))

    def fence(self):
        return p._PerWriteLeaseFence(self.api, SCOPE, EPOCH, CLAIM)

    def first(self, fence):
        return fence.call(*OPS[0], approved_bodies()[0])

    def test_branch_only_fence_rejects_pr_creation_even_with_canonical_body(self):
        # If the host later grants broader token rights, BRANCH_ONLY must still
        # forbid /pulls in source, rather than relying on OAuth permissions.
        branch_scope = {**SCOPE, "branch_only": True}
        x = p._PerWriteLeaseFence(self.api, branch_scope, EPOCH, CLAIM)
        for i, (method, path) in enumerate(OPS[:2]):
            x.call(method, path, approved_bodies()[i])
        with self.assertRaisesRegex(p.ProbeError, "SOURCE_WRITE_NOT_IN_ALLOWED_ORDER"):
            x.call(*OPS[2], approved_bodies()[2])
        self.assertEqual(self.api.calls, OPS[:2])

    def test_branch_only_fence_gets_do_not_unlock_third_write(self):
        branch_scope = {**SCOPE, "branch_only": True}
        x = p._PerWriteLeaseFence(self.api, branch_scope, EPOCH, CLAIM)
        for i, (method, path) in enumerate(OPS[:2]):
            x.call(method, path, approved_bodies()[i])
        x.call("GET", "/git/ref/heads/main")
        with self.assertRaisesRegex(p.ProbeError, "SOURCE_WRITE_NOT_IN_ALLOWED_ORDER"):
            x.call(*OPS[2], approved_bodies()[2])
        self.assertEqual(self.api.calls[:2], OPS[:2])
        self.assertEqual(self.api.calls[-1], ("GET", "/git/ref/heads/main"))

    def test_positive_three_exact_writes(self):
        x = self.fence()
        for i, (method, path) in enumerate(OPS):
            x.call(method, path, approved_bodies()[i])
        self.assertEqual(self.api.calls, OPS)

    def test_read_does_not_consume_mutation_budget(self):
        x = self.fence()
        x.call("GET", "/git/ref/heads/main")
        self.first(x)
        self.assertEqual(len(self.api.calls), 2)

    def test_changed_coordinator_head_blocks_next_write(self):
        x = self.fence()
        self.first(x)
        self.api.ref = FOREIGN
        with self.assertRaises(p.ProbeError):
            x.call(*OPS[1], approved_bodies()[1])
        self.assertEqual(self.api.calls, OPS[:1])

    def test_changed_owner_blocks_next_write(self):
        x = self.fence()
        self.first(x)
        self.api.state["holder"]["owner_id"] = "581c9d84-436e-422c-bc44-d06ff57f5924"
        with self.assertRaises(p.ProbeError):
            x.call(*OPS[1], approved_bodies()[1])
        self.assertEqual(self.api.calls, OPS[:1])

    def test_wrong_epoch_refused_before_first_write(self):
        self.api.state["holder"]["epoch"] = EPOCH + 1
        with self.assertRaises(p.ProbeError):
            self.first(self.fence())
        self.assertEqual(self.api.calls, [])

    def test_wrong_branch_refused(self):
        self.api.state["holder"]["work_branch"] = "controller/foreign"
        with self.assertRaises(p.ProbeError):
            self.first(self.fence())
        self.assertEqual(self.api.calls, [])

    def test_wrong_source_sha_refused(self):
        self.api.state["holder"]["base_main_sha"] = FOREIGN
        with self.assertRaises(p.ProbeError):
            self.first(self.fence())
        self.assertEqual(self.api.calls, [])

    def test_registered_worker_task_id_refused(self):
        self.api.state["holder"]["task_id"] = "registered-task"
        with self.assertRaises(p.ProbeError):
            self.first(self.fence())
        self.assertEqual(self.api.calls, [])

    def test_main_movement_between_mutations_stops(self):
        x = self.fence()
        self.first(x)
        self.api.main = FOREIGN
        with self.assertRaises(p.ProbeError):
            x.call(*OPS[1], approved_bodies()[1])
        self.assertEqual(self.api.calls, OPS[:1])

    def test_wrong_operation_order_stops_without_write(self):
        x = self.fence()
        with self.assertRaises(p.ProbeError):
            x.call(*OPS[1], approved_bodies()[1])
        self.assertEqual(self.api.calls, [])

    def test_unknown_write_ack_cannot_retry(self):
        x = self.fence()
        def fail(*args, **kwargs):
            raise p.ProbeError("ACK_UNAVAILABLE")
        self.api.call = fail
        with self.assertRaisesRegex(p.ProbeError, "ACK_UNAVAILABLE"):
            self.first(x)
        self.api.call = FakeAPI.call.__get__(self.api, FakeAPI)
        with self.assertRaises(p.ProbeError):
            self.first(x)
        self.assertEqual(self.api.calls, [])

    def test_extra_write_not_allowed(self):
        x = self.fence()
        for i, (method, path) in enumerate(OPS):
            x.call(method, path, approved_bodies()[i])
        with self.assertRaises(p.ProbeError):
            x.call("POST", "/pulls", {})
        self.assertEqual(self.api.calls, OPS)

    def test_arbitrary_mutation_denied(self):
        x = self.fence()
        for method, path in (("PATCH", "/git/refs/heads/main"),
                             ("DELETE", "/git/refs"),
                             ("PUT", "/contents/src/ToyWarsServer.server.lua")):
            with self.subTest(method=method), self.assertRaises(p.ProbeError):
                x.call(method, path, {})
        self.assertEqual(self.api.calls, [])

    def test_source_run_wraps_only_create_and_retains_postwrite_check(self):
        body = inspect.getsource(p.run)
        self.assertIn("_PerWriteLeaseFence(", body)
        self.assertIn("pr=create_branch_probe(api,scope)", body)
        self.assertIn("verify_created_probe(api,scope,pr)", body)
        self.assertLess(body.index("pr=create_branch_probe(api,scope)"),
                        body.index("verify_created_probe(api,scope,pr)"))


if __name__ == "__main__":
    unittest.main()
