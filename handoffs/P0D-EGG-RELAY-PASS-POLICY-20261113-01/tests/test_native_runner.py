"""Pure Python integrity unit tests; not native Luau nor Roblox Studio."""
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "native_builder", ROOT / "tools" / "generate_native_runner.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class NativeHarnessIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "src" / "EggRelayPolicy.luau").read_bytes()
        self.cases = (ROOT / "tests" / "native_policy_cases.luau").read_bytes()
        self.manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text("utf-8"))

    def test_original_39_cases_expand_into_luau(self):
        expanded = builder.render(self.source, self.cases, self.manifest)
        self.assertIn("local Relay = (function()", expanded)
        self.assertIn("function Relay.evaluate(world, request)", expanded)
        self.assertIn("P0D_EGG_RELAY_NATIVE_POLICY_39_CASES_PASS", expanded)

    def test_detect_original_luau_mutation(self):
        with self.assertRaisesRegex(AssertionError, "SOURCE_SHA256_MISMATCH"):
            builder.render(self.source + b"\n-- unauthorized", self.cases, self.manifest)

    def test_detect_native_spec_shrink(self):
        with self.assertRaisesRegex(AssertionError, "NATIVE_CASES_DRIFT"):
            builder.render(self.source, self.cases.replace(
                b'check("blocking wall"', b'--check("blocking wall"'), self.manifest)

    def test_detect_manifest_fake_official_rc(self):
        self.manifest["official_rc_adopted"] = True
        with self.assertRaisesRegex(AssertionError, "FORBIDDEN_OFFICIAL_RC_CLAIM"):
            builder.render(self.source, self.cases, self.manifest)

    def test_detect_manifest_fake_studio_pass(self):
        self.manifest["roblox_studio"] = "PASS"
        with self.assertRaisesRegex(AssertionError, "FORBIDDEN_STUDIO_PASS_CLAIM"):
            builder.render(self.source, self.cases, self.manifest)

    def test_detect_manifest_fake_product_selection(self):
        self.manifest["product_selected"] = True
        with self.assertRaisesRegex(AssertionError, "FORBIDDEN_PRODUCT_SELECTED_CLAIM"):
            builder.render(self.source, self.cases, self.manifest)

    def test_git_blob_original_source_locked(self):
        self.assertEqual(builder.blob_sha(self.source),
                         "dd5e5e19fb16c79bc54bfdef04c941cde418b0b4")

    def test_all_native_case_source_pinned(self):
        self.assertEqual(builder.blob_sha(self.cases),
                         "fc827f4f16f4745f85faef867596f208b76ee0dc")


if __name__ == "__main__":
    unittest.main()
