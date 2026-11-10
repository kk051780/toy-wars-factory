import hashlib
import importlib.util
import io
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "legacy_zip_locator.py"
spec = importlib.util.spec_from_file_location("locator", SOURCE)
locator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locator)


class OriginalZipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.name = "ORIGINAL.zip"
        self.path = self.root / self.name

    def make(self, members=None):
        members = members or {"luau/Hello.luau": "return true\n", "tests/test.py": "assert True\n"}
        with zipfile.ZipFile(self.path, "w") as z:
            for name, contents in members.items():
                z.writestr(name, contents)
        payload = self.path.read_bytes()
        return {"demo": {"file": self.name, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}}

    def check(self, members=None):
        return locator.inspect_zip(self.path, "demo", self.make(members))

    def reject(self, members, reason=None):
        with self.assertRaises(locator.Rejected) as ex:
            self.check(members)
        if reason:
            self.assertIn(reason, str(ex.exception))

    def test_catalog_has_four_pinned_hashes(self):
        self.assertEqual(len(locator.PACKETS), 4)
        self.assertEqual(len({x["file"] for x in locator.PACKETS.values()}), 4)
        for item in locator.PACKETS.values():
            self.assertEqual(len(item["sha256"]), 64)
            self.assertTrue(item["bytes"] > 0)

    def test_v42_supersession_is_explicit(self):
        ids = [k for k, v in locator.PACKETS.items() if v["lineage"] == "progression"]
        self.assertEqual(len(ids), 3)
        self.assertEqual(locator.PACKETS["v42.2-progress-ui"]["priority"], "latest_archive_reference")

    def test_positive(self):
        self.assertEqual(set(self.check()), {"luau/Hello.luau", "tests/test.py"})

    def test_allowed_subfolder(self):
        self.assertEqual(len(self.check({"deep/a/b/t.py": "x=1", "z.md": "Hi"})), 2)

    def test_sha_tampering(self):
        idx = self.make()
        self.path.write_bytes(self.path.read_bytes() + b"!")
        with self.assertRaisesRegex(locator.Rejected, "size mismatch"):
            locator.inspect_zip(self.path, "demo", idx)

    def test_exact_sha_not_just_size(self):
        idx = self.make()
        b = bytearray(self.path.read_bytes())
        b[-4] ^= 1
        self.path.write_bytes(b)
        with self.assertRaisesRegex(locator.Rejected, "SHA-256 mismatch"):
            locator.inspect_zip(self.path, "demo", idx)

    def test_unknown_id(self):
        idx = self.make()
        with self.assertRaisesRegex(locator.Rejected, "not in pinned"):
            locator.inspect_zip(self.path, "unknown", idx)

    def test_wrong_filename(self):
        idx = self.make()
        idx["demo"]["file"] = "WRONG.zip"
        with self.assertRaisesRegex(locator.Rejected, "wrong original filename"):
            locator.inspect_zip(self.path, "demo", idx)

    def test_traversal(self):
        self.reject({"../escape.py": "bad", "ok.py": "ok"}, "traversal")

    def test_absolute(self):
        self.reject({"/tmp/secrets.py": "bad", "ok.py": "ok"}, "absolute")

    def test_windows_separators(self):
        self.reject({"evil\\data.py": "bad", "ok.py": "ok"}, "windows")

    def test_colon_drive(self):
        self.reject({"C:evil.py": "bad", "ok.py": "ok"}, "windows")

    def test_hidden_file(self):
        self.reject({".env": "no", "ok.py": "ok"}, "hidden")

    def test_forbid_exe(self):
        self.reject({"run.exe": "no", "ok.py": "ok"}, "non-source")

    def test_case_insensitive_duplicate(self):
        self.reject({"a.py": "x=1", "A.PY": "x=2"}, "case-colliding")

    def test_non_utf8(self):
        self.reject({"bad.py": bytes([0xff, 0xfe]), "ok.py": "ok"}, "non-UTF8")

    def test_oversize_member(self):
        self.reject({"a.py": "a" * (locator.MAX_FILE_BYTES+1), "ok.py": "ok"}, "oversize")

    def test_invalid_zip(self):
        idx = self.make()
        self.path.write_bytes(b"!" * idx["demo"]["bytes"])
        idx["demo"]["sha256"] = locator.sha(self.path.read_bytes())
        with self.assertRaisesRegex(locator.Rejected, "corrupt"):
            locator.inspect_zip(self.path, "demo", idx)

    def test_scan_does_not_recurse(self):
        self.assertEqual(len(locator.scan(self.root)), 4)
        self.assertTrue(all(x["state"] == "MISSING_ORIGINAL" for x in locator.scan(self.root)))
        (self.root / "sub").mkdir()
        self.assertEqual(len(locator.scan(self.root)), 4)

    def test_existing_output_refusal(self):
        idx = self.make()
        original = locator.PACKETS
        try:
            locator.PACKETS = idx
            out = self.root / "out"
            out.mkdir()
            with self.assertRaisesRegex(locator.Rejected, "already exist"):
                locator.stage(self.path, "demo", out)
        finally:
            locator.PACKETS = original

    def test_safe_stage(self):
        idx = self.make()
        original = locator.PACKETS
        try:
            locator.PACKETS = idx
            out = self.root / "out"
            obj = locator.stage(self.path, "demo", out)
            self.assertEqual(obj["source_count"], 2)
            self.assertEqual((out/"luau/Hello.luau").read_text(), "return true\n")
            self.assertIn("NOT_GITHUB", obj["staging"])
        finally:
            locator.PACKETS = original

    def test_symlink_member(self):
        with zipfile.ZipFile(self.path, "w") as z:
            v = zipfile.ZipInfo("linked.py")
            v.create_system = 3
            v.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(v, "secret")
            z.writestr("ok.py", "x=1")
        b = self.path.read_bytes()
        idx = {"demo": {"file": self.name, "sha256": locator.sha(b), "bytes": len(b)}}
        with self.assertRaisesRegex(locator.Rejected, "symlink"):
            locator.inspect_zip(self.path, "demo", idx)


if __name__ == "__main__":
    unittest.main()
