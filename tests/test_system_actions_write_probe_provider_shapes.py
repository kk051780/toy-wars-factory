"""PR163: malformed GitHub REST data must fail closed, including lease cleanup.

Synthetic GitHub GET responses only; NOT provider authority, token access,
actual scheduled writing, native approval, or Roblox engine proof.
"""
import base64
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import system_actions_write_probe as probe
from repair_control import initial_state
from test_system_actions_write_probe import BASE_ENV, BASE_RUN, SHA


class StubAPI:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def call(self, method, path, body=None):
        self.calls.append((method, path, body))
        return deepcopy(self.response)


class MalformedProviderFailClosed(unittest.TestCase):
    def test_live_run_nested_objects_are_required_mappings(self):
        for key in ("actor", "triggering_actor", "head_repository"):
            for invalid in (None, [], "not-an-object"):
                with self.subTest(key=key, invalid=invalid):
                    payload = deepcopy(BASE_RUN)
                    payload[key] = invalid
                    with self.assertRaisesRegex(probe.ProbeError,
                                                "^LIVE_RUN_LINEAGE_MISMATCH$"):
                        probe.checked_context(BASE_ENV, payload, SHA)

    def test_git_ref_sha_must_have_an_object_mapping(self):
        for bad in (None, [], "incorrect", True):
            with self.subTest(bad=bad):
                api = StubAPI({"object": bad})
                with self.assertRaisesRegex(probe.ProbeError, "^REF_INVALID$"):
                    probe.sha_ref(api, "twf-repair-coordinator")
                self.assertEqual(len(api.calls), 1)

    def test_corrupt_coordinator_content_rejected_as_probe_error(self):
        for invalid in ("%%%bad-base64%%%", None, ["abc"]):
            with self.subTest(invalid=invalid):
                api = StubAPI({"type": "file", "encoding": "base64",
                               "content": invalid})
                with self.assertRaisesRegex(probe.ProbeError, "^STATE_INVALID$"):
                    probe.state_at(api, SHA)
                self.assertEqual(len(api.calls), 1)

    def test_duplicate_top_level_or_nested_github_json_is_rejected(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size):
                return self.payload[:size]

        for payload in (b'{"status":"completed","status":"in_progress"}',
                        b'{"object":{"sha":"aaaa","sha":"bbbb"}}'):
            with self.subTest(payload=payload):
                api = probe.GitHubAPI('test-token-not-real',
                        transport=lambda req, timeout: FakeResponse(payload))
                with self.assertRaisesRegex(probe.ProbeError, '^RESPONSE_INVALID
        for invalid in (None, [], "bad-tree"):
            with self.subTest(invalid=invalid):
                class CommitAPI:
                    def __init__(self):
                        self.calls = []
                    def call(self, method, path, body=None):
                        self.calls.append((method, path))
                        return {"tree": invalid}
                api = CommitAPI()
                with self.assertRaisesRegex(probe.ProbeError,
                                            "^CONTROL_TREE_INVALID$"):
                    probe.cas_state(api, SHA, {"schema": 1})
                self.assertEqual(api.calls, [("GET", "/git/commits/" + SHA)])

    def test_valid_authenticated_context_fixture_still_classifies(self):
        scope = probe.checked_context(BASE_ENV, BASE_RUN, SHA)
        self.assertEqual(scope["main"], SHA)
        self.assertEqual(scope["run_id"], int(BASE_ENV["GITHUB_RUN_ID"]))


if __name__ == "__main__":
    unittest.main()
):
                    api.call('GET', '/git/ref/heads/main')

    def test_duplicate_coordinator_epoch_is_rejected_before_claim(self):
        # initial_state() is otherwise valid. Last-key-wins would silently
        # change its epoch and still pass validate(); never trust that parse.
        state = initial_state()
        raw = json.dumps(state, separators=(',', ':'))
        duplicate_epoch = raw[:-1] + ',"epoch":99}'
        api = StubAPI({'type': 'file', 'encoding': 'base64',
                       'content': base64.b64encode(
                           duplicate_epoch.encode()).decode()})
        with self.assertRaisesRegex(probe.ProbeError, '^STATE_INVALID
        for invalid in (None, [], "bad-tree"):
            with self.subTest(invalid=invalid):
                class CommitAPI:
                    def __init__(self):
                        self.calls = []
                    def call(self, method, path, body=None):
                        self.calls.append((method, path))
                        return {"tree": invalid}
                api = CommitAPI()
                with self.assertRaisesRegex(probe.ProbeError,
                                            "^CONTROL_TREE_INVALID$"):
                    probe.cas_state(api, SHA, {"schema": 1})
                self.assertEqual(api.calls, [("GET", "/git/commits/" + SHA)])

    def test_valid_authenticated_context_fixture_still_classifies(self):
        scope = probe.checked_context(BASE_ENV, BASE_RUN, SHA)
        self.assertEqual(scope["main"], SHA)
        self.assertEqual(scope["run_id"], int(BASE_ENV["GITHUB_RUN_ID"]))


if __name__ == "__main__":
    unittest.main()
):
            probe.state_at(api, SHA)
        self.assertEqual(len(api.calls), 1)

    def test_null_commit_tree_is_rejected_before_any_cas_write(self):
        for invalid in (None, [], "bad-tree"):
            with self.subTest(invalid=invalid):
                class CommitAPI:
                    def __init__(self):
                        self.calls = []
                    def call(self, method, path, body=None):
                        self.calls.append((method, path))
                        return {"tree": invalid}
                api = CommitAPI()
                with self.assertRaisesRegex(probe.ProbeError,
                                            "^CONTROL_TREE_INVALID$"):
                    probe.cas_state(api, SHA, {"schema": 1})
                self.assertEqual(api.calls, [("GET", "/git/commits/" + SHA)])

    def test_valid_authenticated_context_fixture_still_classifies(self):
        scope = probe.checked_context(BASE_ENV, BASE_RUN, SHA)
        self.assertEqual(scope["main"], SHA)
        self.assertEqual(scope["run_id"], int(BASE_ENV["GITHUB_RUN_ID"]))


if __name__ == "__main__":
    unittest.main()
