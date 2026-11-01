"""Original PR163 CAS post-write readback regression (no network, fake REST only)."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import system_actions_write_probe as probe

OLD = "1" * 40
CREATED = "2" * 40
FOREIGN = "3" * 40
TARGET = {"schema": 1, "epoch": 356, "holder": None}


class FakeGit:
    def __init__(self):
        self.requests = []

    def call(self, method, path, body=None):
        self.requests.append((method, path, deepcopy(body)))
        if (method, path) == ("GET", f"/git/commits/{OLD}"):
            return {"tree": {"sha": "4" * 40}}
        if (method, path) == ("POST", "/git/blobs"):
            return {"sha": "5" * 40}
        if (method, path) == ("POST", "/git/trees"):
            return {"sha": "6" * 40}
        if (method, path) == ("POST", "/git/commits"):
            return {"sha": CREATED}
        if (method, path) == ("PATCH", f"/git/refs/heads/{probe.CONTROL_REF}"):
            return {"object": {"sha": CREATED}}
        raise AssertionError(f"unplanned REST request: {method} {path}")


class LateCoordinatorRefDrift(unittest.TestCase):
    def test_verified_after_two_matching_live_ref_reads(self):
        api = FakeGit()
        observed = []
        def get_ref(actual, branch):
            self.assertIs(actual, api)
            self.assertEqual(branch, probe.CONTROL_REF)
            observed.append(CREATED)
            return CREATED
        with patch.object(probe, "sha_ref", side_effect=get_ref) as ref, patch.object(
                probe, "state_at", return_value=TARGET) as state:
            self.assertEqual(probe.cas_state(api, OLD, TARGET), CREATED)
        self.assertEqual(observed, [CREATED, CREATED])
        self.assertEqual(state.call_count, 1)
        self.assertEqual(api.requests[-1], ("PATCH", f"/git/refs/heads/{probe.CONTROL_REF}",
                                            {"sha": CREATED, "force": False}))

    def test_ref_moves_after_first_get_and_before_state_completes(self):
        api = FakeGit()
        observed = []
        def get_ref(actual, branch):
            self.assertIs(actual, api)
            self.assertEqual(branch, probe.CONTROL_REF)
            value = CREATED if not observed else FOREIGN
            observed.append(value)
            return value
        with patch.object(probe, "sha_ref", side_effect=get_ref), patch.object(
                probe, "state_at", return_value=TARGET) as state:
            with self.assertRaisesRegex(probe.ProbeError, "CONTROL_CAS_READBACK_UNCONFIRMED"):
                probe.cas_state(api, OLD, TARGET)
        self.assertEqual(observed, [CREATED, FOREIGN])
        self.assertEqual(state.call_count, 1)

    def test_foreign_first_ref_denied_without_state_read(self):
        api = FakeGit()
        with patch.object(probe, "sha_ref", return_value=FOREIGN) as ref, patch.object(
                probe, "state_at") as state:
            with self.assertRaisesRegex(probe.ProbeError, "CONTROL_CAS_READBACK_UNCONFIRMED"):
                probe.cas_state(api, OLD, TARGET)
        self.assertEqual(ref.call_count, 1)
        state.assert_not_called()

    def test_wrong_state_denied_without_second_ref_get(self):
        api = FakeGit()
        other = {"schema": 1, "epoch": 357, "holder": None}
        with patch.object(probe, "sha_ref", return_value=CREATED) as ref, patch.object(
                probe, "state_at", return_value=other) as state:
            with self.assertRaisesRegex(probe.ProbeError, "CONTROL_CAS_READBACK_UNCONFIRMED"):
                probe.cas_state(api, OLD, TARGET)
        self.assertEqual(ref.call_count, 1)
        self.assertEqual(state.call_count, 1)


if __name__ == "__main__":
    unittest.main()
