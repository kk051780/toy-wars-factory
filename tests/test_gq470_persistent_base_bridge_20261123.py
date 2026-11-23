"""Real-artifact preparation and refusal tests; discovery without inputs is NOT_RUN."""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[1]
PACKAGE = ROOT / "quality_gameplay/gq470_persistent_base_bridge_20261123"
SPEC = importlib.util.spec_from_file_location("p0d033_persistent_base_prepare", PACKAGE / "prepare_bridge.py")
PREP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREP)
ENV_KEYS = ("P0D033_OFFICIAL_ZIP", "P0D033_DONOR_ZIP")


def input_paths(direct=False):
    values = [os.environ.get(key) for key in ENV_KEYS]
    if all(value is None for value in values) and not direct:
        raise unittest.SkipTest("NOT_RUN: exact H72 and H84 artifacts are required by the dedicated gate")
    if any(value is None or not value.strip() for value in values):
        raise ValueError("BOTH_EXACT_ARTIFACT_INPUTS_REQUIRED")
    return [PREP.safe_path(value) for value in values]


class PersistentBasePreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.official, cls.donor = input_paths()
        cls.identities = [PREP.identity(PREP.read_file(path)) for path in (cls.official, cls.donor)]
        PREP.verify_inputs(cls.official, cls.donor)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p0d033-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / "prepared"

    def tearDown(self):
        self.assertEqual([PREP.identity(PREP.read_file(path)) for path in (self.official, self.donor)],
                         self.identities, "original artifact input changed")

    def test_prepare_has_seven_unattached_exact_modules(self):
        receipt = PREP.prepare(self.official, self.donor, self.out)
        files = {p.relative_to(self.out).as_posix() for p in self.out.rglob("*") if p.is_file()}
        expected = {PREP.NAMESPACE + "/" + name + ".luau" for name in receipt["modules"]}
        self.assertEqual(files, expected | {"PREPARE_RECEIPT.json"})
        self.assertEqual(len(expected), 7)
        for name, pin in receipt["modules"].items():
            self.assertEqual(PREP.identity((self.out / PREP.NAMESPACE / (name + ".luau")).read_bytes()), pin)
        self.assertEqual(receipt["selected_sources_preserved"], 69)
        self.assertFalse(receipt["created_place"])
        self.assertFalse(receipt["installed_in_runtime"])

    def test_existing_output_is_not_overwritten(self):
        self.out.mkdir(); sentinel = self.out / "keep.txt"; sentinel.write_bytes(b"existing user data")
        with self.assertRaisesRegex(ValueError, "OUTPUT_MUST_BE_NEW"):
            PREP.prepare(self.official, self.donor, self.out)
        self.assertEqual(sentinel.read_bytes(), b"existing user data")
        self.assertEqual(list(self.out.iterdir()), [sentinel])

    def test_input_symlink_and_ancestor_are_rejected_before_output(self):
        link = self.root / "linked.zip"; link.symlink_to(self.official)
        parent = self.root / "linked-parent"; parent.symlink_to(self.official.parent, target_is_directory=True)
        for source in (link, parent / self.official.name):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SYMLINK"):
                    PREP.prepare(source, self.donor, self.out)
                self.assertFalse(self.out.exists())

    def test_output_symlink_ancestor_is_rejected(self):
        actual = self.root / "actual"; actual.mkdir()
        link = self.root / "linked"; link.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "SYMLINK"):
            PREP.prepare(self.official, self.donor, link / "prepared")
        self.assertEqual(list(actual.iterdir()), [])

    def test_changed_zip_is_rejected_before_output(self):
        for index, original in enumerate((self.official, self.donor)):
            changed = self.root / (str(index) + ".zip")
            raw = bytearray(original.read_bytes()); raw[-1] ^= 1; changed.write_bytes(raw)
            args = [self.official, self.donor]; args[index] = changed
            with self.subTest(index=index):
                with self.assertRaisesRegex(ValueError, "EXACT_.*_ZIP"):
                    PREP.prepare(*args, self.out)
                self.assertFalse(self.out.exists())

    def test_input_alias_and_empty_input_cannot_be_output(self):
        with self.assertRaises(ValueError):
            PREP.prepare(self.official, self.donor, self.official)
        with self.assertRaisesRegex(ValueError, "EMPTY_PATH"):
            PREP.prepare("", self.donor, self.out)
        with self.assertRaisesRegex(ValueError, "PARENT_TRAVERSAL"):
            PREP.prepare(self.official, self.donor, self.root / "x" / ".." / "escaped")
        self.assertFalse(self.out.exists())

    def test_strict_json_rejects_duplicates_and_nonfinite(self):
        for raw in ('{"x":1,"x":2}', '{"x":1,"\\u0078":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                PREP.strict_json(raw)

    def test_zip_parser_rejects_escape_duplicates_and_symlinks(self):
        cases = [("../escape.luau",), ("/absolute.luau",), ("A.luau", "a.luau"), ("link.luau",)]
        for names in cases:
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as archive:
                for name in names:
                    info = zipfile.ZipInfo(name)
                    if name == "link.luau": info.create_system = 3; info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    archive.writestr(info, b"return {}\n")
            with self.subTest(names=names), self.assertRaises(ValueError):
                PREP.zip_members(stream.getvalue())

    def test_xml_parser_rejects_duplicate_concrete_routes_and_entities(self):
        item = '<Item class="ModuleScript"><Properties><string name="Name">same</string><string name="Source">return {}</string></Properties></Item>'
        with self.assertRaisesRegex(ValueError, "DUPLICATE_INSTANCE_ROUTE"):
            PREP.place_sources(('<roblox version="4">' + item + item + '</roblox>').encode())
        with self.assertRaisesRegex(ValueError, "XML_DECLARATION"):
            PREP.place_sources(b'<!DOCTYPE roblox><roblox version="4"/>')

    def test_changed_adapter_copy_is_rejected_before_output(self):
        capsule = self.root / "capsule"; capsule.mkdir()
        for name in ("prepare_bridge.py", "source_lock.json", PREP.MODULE + ".luau"):
            shutil.copyfile(PACKAGE / name, capsule / name)
        with (capsule / (PREP.MODULE + ".luau")).open("ab") as stream: stream.write(b"\n-- changed\n")
        run = subprocess.run([sys.executable, "-B", str(capsule / "prepare_bridge.py"), "--official-zip",
                              str(self.official), "--donor-zip", str(self.donor), "--output", str(self.out)],
                             capture_output=True, timeout=30)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn(b"ADAPTER_CHANGED", run.stdout)
        self.assertFalse(self.out.exists())

    def test_direct_test_entry_rejects_absent_empty_and_partial_inputs(self):
        combinations = ((None, None), ("", ""), (str(self.official), None), (" ", str(self.donor)))
        for values in combinations:
            env = dict(os.environ)
            for key in ENV_KEYS: env.pop(key, None)
            for key, value in zip(ENV_KEYS, values):
                if value is not None: env[key] = value
            run = subprocess.run([sys.executable, "-B", str(Path(__file__).absolute())], env=env,
                                 capture_output=True, timeout=30)
            with self.subTest(values=values):
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b"BOTH_EXACT_ARTIFACT_INPUTS_REQUIRED", run.stderr)


if __name__ == "__main__":
    try:
        input_paths(direct=True)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
    unittest.main()
