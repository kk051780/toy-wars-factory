"""PR163 delayed-completion regression against real run() and legacy lease model.

Mock HTTP transport only, NOT an authenticated GitHub-hosted live execution.
"""
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import repair_control
from test_system_actions_write_probe_partial_dispatch import Host, SCOPE, SHA


class AmbiguousWriteLeaseRegression(unittest.TestCase):
    def test_unknown_put_blocks_second_controller(self):
        host = Host(fail_at=2, mode="BRANCH_ONLY")
        with self.assertRaisesRegex(
            Exception,
            r"GITHUB_TRANSPORT_FAILED__SOURCE_MUTATIONS_ATTEMPTED_2__PARTIAL_WRITE_POSSIBLE__SOURCE_ACTION_UNRESOLVED_NO_RELEASE",
        ):
            host.execute()
        self.assertEqual(host.dispatched[1][0], "PUT")
        self.assertEqual(host.release_count, 0)
        self.assertEqual(host.cas_count, 1)
        start = "2026-11-09T00:01:00+00:00"
        first = repair_control.acquire(
            repair_control.initial_state(), "CONTROLLER", SCOPE["owner"], start,
            base_main_sha=SHA, work_branch=SCOPE["branch"],
        )
        self.assertEqual(first["action"], "ACQUIRE")
        second = repair_control.acquire(
            first["state"], "CONTROLLER",
            "69c043c2-8dfc-470d-91f5-e82a7249d008",
            "2026-11-09T00:01:01+00:00",
            base_main_sha=SHA, work_branch="controller/gha-write-probe-778-a1",
        )
        self.assertFalse(second["write"])
        self.assertIn(second["action"], ("WAIT_LOCK", "JOIN_EXISTING", "WAIT_RECOVERY"))

    def test_before_dispatch_releases_own_lease(self):
        host = Host(mode="BRANCH_ONLY")
        with self.assertRaisesRegex(Exception, "MAIN_CHANGED"):
            host.execute(no_source=True)
        self.assertEqual(host.dispatched, [])
        self.assertEqual(host.release_count, 1)


if __name__ == "__main__":
    unittest.main()
