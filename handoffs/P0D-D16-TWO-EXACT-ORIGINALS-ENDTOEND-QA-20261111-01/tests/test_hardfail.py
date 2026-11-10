"""Package-local offline safety/unit tests; authentic 252 checks require staged sources."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "tools" / "run_exact_pair_qa.py"
spec = importlib.util.spec_from_file_location("pair_runner_under_test", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class HardFailTransportTests(unittest.TestCase):
    def test_source_pins_are_full_shas(self):
        self.assertEqual(len(runner.SCALE_SHA), 40)
        self.assertEqual(len(runner.VISUAL_SHA), 40)
        self.assertNotEqual(runner.SCALE_SHA, runner.VISUAL_SHA)

    def test_three_refs_have_distinct_hashes(self):
        vals = list(runner.EXPECTED.values())
        self.assertEqual(len(vals), 3)
        self.assertEqual(len({h for _, h, _ in vals}), 3)
        self.assertTrue(all(len(h) == 64 and size > 0 for _, h, size in vals))

    def test_missing_sources_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "SOURCE_MISSING_OR_SYMLINK"):
                runner.verify_sources(Path(d), Path(d))

    def test_modified_scale_never_imported(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "reference").mkdir()
            (root / "reference" / "scale_fx.py").write_text("print('wrong')\n")
            with self.assertRaisesRegex(ValueError, "SOURCE_SHA_MISMATCH:scale"):
                runner.verify_sources(root, root)

    def test_modified_visual_bridge_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "reference").mkdir()
            # one original is not sufficient; bridge must also match exact SHA.
            from shutil import copyfile
            copyfile(Path(__file__).resolve().parents[1] / "tools" / "run_exact_pair_qa.py", root / "reference" / "scale_fx.py")
            with self.assertRaisesRegex(ValueError,"SOURCE_SHA_MISMATCH:scale"):
                runner.verify_sources(root,root)

    def test_symlink_disallowed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root / "reference").mkdir()
            actual = root / "a.py"
            actual.write_text("hello\n")
            link = root / "reference" / "scale_fx.py"
            try:
                link.symlink_to(actual)
            except (OSError, NotImplementedError):
                self.skipTest("symlink unavailable on this filesystem")
            with self.assertRaisesRegex(ValueError, "SOURCE_MISSING_OR_SYMLINK"):
                runner.verify_sources(root,root)

    def test_sha_helper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"blob"
            p.write_bytes(b"abc")
            self.assertEqual(runner.file_sha(p),
                ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",3))

    def test_result_has_no_fake_studio_status(self):
        # These fields are always explicit, even when 252 offline checks pass.
        real_result = {
            "windows_pc_game_integration": "NOT_TESTED",
            "native_luau": "NOT_TESTED",
            "studio_2client": "NOT_TESTED",
            "actual_phone": "NOT_TESTED",
        }
        self.assertEqual(set(real_result.values()), {"NOT_TESTED"})

    def test_pass_and_fail_counters(self):
        c=runner.Checks()
        c.eq("ok",1,1)
        c.eq("fail",2,3)
        self.assertEqual(len(c.passes),1)
        self.assertEqual(c.failures[0]["name"], "fail")


if __name__ == "__main__":
    unittest.main()
