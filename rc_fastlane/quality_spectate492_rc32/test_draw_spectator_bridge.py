"""GQ499 deadline and GQ492 original spectator cross-domain source mutants."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location(
    "bridge", Path(__file__).with_name("verify_draw_spectator_bridge.py"))
assert spec and spec.loader
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
HOST="\n".join(bridge.HOST_ANCHORS)
CLIENT="\n".join(bridge.CLIENT_ANCHORS)

class BridgeTests(unittest.TestCase):
    def test_valid_source_hooks(self):
        evidence=bridge.validate(HOST,CLIENT)
        self.assertEqual(evidence["host_deadline_anchors"],8)
        self.assertEqual(evidence["spectator_recovery_anchors"],8)
        self.assertEqual(evidence["actual_studio_2client"],"NOT_TESTED")

    def test_mutate_each_of_eight_server_hooks_must_fail(self):
        for hook in bridge.HOST_ANCHORS:
            with self.subTest(hook=hook):
                with self.assertRaisesRegex(ValueError,"HOST_DEADLINE"):
                    bridge.validate(HOST.replace(hook,"-- mutated",1),CLIENT)

    def test_mutate_each_of_eight_original_client_hooks_must_fail(self):
        for hook in bridge.CLIENT_ANCHORS:
            with self.subTest(hook=hook):
                with self.assertRaisesRegex(ValueError,"SPECTATOR_BRIDGE"):
                    bridge.validate(HOST,CLIENT.replace(hook,"-- mutated",1))

    def test_added_remote_authority_must_fail(self):
        with self.assertRaisesRegex(ValueError,"REMOTE_AUTHORITY"):
            bridge.validate(HOST,CLIENT+"\nFakeRemote:FireServer()")
if __name__=="__main__":
    unittest.main()
