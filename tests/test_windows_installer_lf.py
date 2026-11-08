"""P0-B: exact installer bytes independent of Windows text newline conversion."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "build_installer.py"
FILES = {
    "ToyWarsBalance.lua": "-- balance non-ASCII 日本語\nreturn { Price = 1 }\n",
    "ToyWarsServer.server.lua": "-- server\nprint('ready')\n",
    "ToyWarsHUD.client.lua": "-- hud\nprint('hud')\n",
    "ToyWarsSmokeTest.server.lua": "-- smoke\nprint('smoke')\n",
}


class WindowsInstallerLineEndingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tools").mkdir()
        (self.root / "src").mkdir()
        self.script = self.root / "tools" / "build_installer.py"
        shutil.copyfile(SCRIPT, self.script)
        for name, code in FILES.items():
            (self.root / "src" / name).write_bytes(code.encode("utf-8"))
        self.installer = self.root / "studio" / "TOY_WARS_v1_2_ONE_CLICK_INSTALLER.lua"
        self.manifest = self.root / "evidence" / "SOURCE_MANIFEST.json"

    def build(self):
        result = subprocess.run([sys.executable, str(self.script)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", check=True)
        self.assertIn("built", result.stdout)
        self.assertTrue(self.installer.is_file())
        self.assertTrue(self.manifest.is_file())
        return self.installer.read_bytes(), self.manifest.read_bytes()

    def test_canonical_installer_bytes_match_manifest(self):
        raw, record = self.build()
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(digest, json.loads(record.decode("utf-8"))["installer_sha256"])
        self.assertNotIn(b"\r\n", raw)

    def test_all_embedded_source_hashes_match_utf8(self):
        raw, record = self.build()
        manifest = json.loads(record.decode("utf-8"))
        for key, name in (("balance", "ToyWarsBalance.lua"),
                          ("server", "ToyWarsServer.server.lua"),
                          ("hud", "ToyWarsHUD.client.lua"),
                          ("smoke", "ToyWarsSmokeTest.server.lua")):
            expected = FILES[name].encode("utf-8")
            self.assertEqual(manifest[key], hashlib.sha256(expected).hexdigest())
            self.assertIn(expected, raw)

    def test_second_build_is_byte_identical(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)

    def test_windows_crlf_conversion_would_change_digest(self):
        raw, record = self.build()
        converted = raw.replace(b"\n", b"\r\n")
        self.assertNotEqual(hashlib.sha256(converted).hexdigest(),
                            json.loads(record.decode("utf-8"))["installer_sha256"])
        self.assertEqual(converted.replace(b"\r\n", b"\n"), raw)

    def test_script_never_uses_platform_text_writer(self):
        # On Windows Path.write_text may translate LF to CRLF. Fail if it
        # is ever invoked, even on the Linux CI runner.
        with patch.object(Path, "write_text", side_effect=AssertionError(
                "unsafe platform-dependent text output")):
            runpy.run_path(str(self.script), run_name="__main__")
        self.assertEqual(hashlib.sha256(self.installer.read_bytes()).hexdigest(),
                         json.loads(self.manifest.read_bytes())["installer_sha256"])

    def test_manifest_also_uses_canonical_lf(self):
        _, raw_manifest = self.build()
        self.assertTrue(raw_manifest.endswith(b"\n"))
        self.assertNotIn(b"\r\n", raw_manifest)

    def test_source_unicode_preserved_without_locale_guess(self):
        raw, _ = self.build()
        self.assertIn("日本語".encode("utf-8"), raw)
        self.assertIn(b"Price = 1", raw)


if __name__ == "__main__":
    unittest.main()
