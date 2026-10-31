"""Rojo build-only toolchain reproducibility: synthetic command proof, no engine."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import rojo_toolchain_gate as gate

WORKFLOW=ROOT/".github/workflows/toy-wars-rojo-build-only.yml"
ROKIT=ROOT/"rokit.toml"

def execute(rokit="rokit 1.2.0\n",rojo="Rojo 7.5.1\n",exitcode=0,stderr=False):
    calls=[]
    def runner(argv, **kwargs):
        calls.append((argv,kwargs))
        value=rokit if argv[0]=="rokit" else rojo
        if isinstance(value, BaseException): raise value
        if stderr:return subprocess.CompletedProcess(argv,exitcode,"",value)
        return subprocess.CompletedProcess(argv,exitcode,value,"")
    return runner,calls

class VersionContractTests(unittest.TestCase):
    def test_exact_versions_pass_as_static_toolchain_receipt_only(self):
        fn,calls=execute()
        report=gate.verify_toolchain(runner=fn)
        self.assertEqual(report["rokit"],"1.2.0")
        self.assertEqual(report["rojo"],"7.5.1")
        self.assertFalse(report["engine_verified"])
        self.assertFalse(report["built_rbxl"])
        self.assertEqual([x[0] for x in calls],[["rokit","--version"],["rojo","--version"]])

    def test_version_prefix_variation_is_accepted(self):
        fn,_=execute(rokit="rokit v1.2.0",rojo="rojo v7.5.1")
        self.assertEqual(gate.verify_toolchain(runner=fn)["rojo"],"7.5.1")

    def test_stderr_only_version_supported(self):
        fn,_=execute(stderr=True)
        self.assertEqual(gate.verify_toolchain(runner=fn)["rokit"],"1.2.0")

    def test_previous_rokit_version_blocked(self):
        fn,_=execute(rokit="rokit 1.1.1")
        with self.assertRaises(ValueError):gate.verify_toolchain(runner=fn)

    def test_wrong_rojo_version_blocked(self):
        fn,_=execute(rojo="Rojo 7.5.0")
        with self.assertRaises(ValueError):gate.verify_toolchain(runner=fn)

    def test_rokit_extra_prefix_not_trusted(self):
        fn,_=execute(rokit="unreviewed-rokit 1.2.0")
        with self.assertRaises(ValueError):gate.verify_toolchain(runner=fn)

    def test_multiline_output_not_trusted(self):
        fn,_=execute(rojo="Rojo 7.5.1\nupgrade ready")
        with self.assertRaises(ValueError):gate.verify_toolchain(runner=fn)

    def test_unexpected_cli_exit_blocked(self):
        fn,_=execute(exitcode=1)
        with self.assertRaises(ValueError):gate.verify_toolchain(runner=fn)

    def test_cli_timeout_blocked(self):
        fn,_=execute(rokit=subprocess.TimeoutExpired(["rokit","--version"],8))
        with self.assertRaises(ValueError):gate.verify_toolchain(runner=fn)

    def test_cli_missing_blocked(self):
        fn,_=execute(rokit=FileNotFoundError("rokit unavailable"))
        with self.assertRaises(ValueError):gate.verify_toolchain(runner=fn)

    def test_no_shell_or_environment_mutation_in_version_queries(self):
        fn,calls=execute()
        gate.verify_toolchain(runner=fn)
        self.assertEqual(len(calls),2)
        for argv,kwargs in calls:
            self.assertEqual(argv[1],"--version")
            self.assertIs(kwargs.get("shell"),False)
            self.assertTrue(kwargs.get("capture_output"))
            self.assertTrue(kwargs.get("text"))
            self.assertEqual(kwargs.get("timeout"),8)
            self.assertNotIn("env",kwargs)

class WorkflowPinTests(unittest.TestCase):
    def test_fixed_toolchain_versions_and_gate_before_build(self):
        workflow=WORKFLOW.read_text()
        self.assertIn("paradoxum-games/setup-rokit@29e6ee09651a3711e3a287a1037671d7b74db6d0",workflow)
        self.assertIn("version: 1.2.0",workflow)
        self.assertIn("python3 tools/rojo_toolchain_gate.py",workflow)
        self.assertLess(workflow.index("python3 tools/rojo_toolchain_gate.py"),workflow.index("rojo build"))
        self.assertIn('rojo = "rojo-rbx/rojo@7.5.1"',ROKIT.read_text())

    def test_legacy_unpinned_rokit_setup_forbidden(self):
        workflow=WORKFLOW.read_text()
        self.assertNotIn("version: latest",workflow)
        self.assertNotIn("cache: true",workflow)
        self.assertIn("persist-credentials: false",workflow)
        self.assertIn("contents: read",workflow)

if __name__=="__main__":
    unittest.main()
