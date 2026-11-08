"""P0-B: integrated four-toy Studio preview builds a canonical, source-exact installer.

This is offline artifact integrity evidence, not actual Roblox Studio execution.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "balance": "ToyWarsBalance.lua",
    "server": "ToyWarsServer.server.lua",
    "hud": "ToyWarsHUD.client.lua",
    "smoke": "ToyWarsSmokeTest.server.lua",
}


class IntegratedPreviewInstallerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "tools").mkdir()
        (self.root / "src").mkdir()
        shutil.copyfile(ROOT / "tools/build_installer.py",
                        self.root / "tools/build_installer.py")
        for filename in SOURCES.values():
            shutil.copyfile(ROOT / "src" / filename,
                            self.root / "src" / filename)

    def build(self):
        subprocess.run([sys.executable, str(self.root / "tools/build_installer.py")],
                       check=True, capture_output=True, text=True, encoding="utf-8")
        installer = (self.root / "studio/TOY_WARS_v1_2_ONE_CLICK_INSTALLER.lua").read_bytes()
        manifest_bytes = (self.root / "evidence/SOURCE_MANIFEST.json").read_bytes()
        return installer, manifest_bytes, json.loads(manifest_bytes.decode("utf-8"))

    def test_actual_integrated_sources_match_every_manifest_hash(self):
        installer, manifest_bytes, manifest = self.build()
        self.assertEqual(set(manifest), set(SOURCES) | {"installer_sha256"})
        self.assertEqual(hashlib.sha256(installer).hexdigest(), manifest["installer_sha256"])
        self.assertNotIn(b"\r\n", installer)
        self.assertNotIn(b"\r\n", manifest_bytes)
        for key, filename in SOURCES.items():
            # Python text reading uses universal newlines on both Windows and Linux.
            text = (self.root / "src" / filename).read_text(encoding="utf-8")
            source_bytes = text.encode("utf-8")
            self.assertEqual(hashlib.sha256(source_bytes).hexdigest(), manifest[key])
            self.assertIn(source_bytes, installer)

    def test_real_four_toy_preview_and_unsaved_notice_are_embedded(self):
        installer, _, _ = self.build()
        for marker in (
            b"PLAYABLE_IDS", b"curebo", b"STUDIO_PREVIEW_UNSAVED",
            b"PROGRESS STATUS PENDING - SAVE UNVERIFIED",
            b"STUDIO PREVIEW - PROGRESS NOT SAVED",
            b"TWF_INSTALL_OK v1.2", b"ToyWarsSelectUnit",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, installer)

    def test_integrated_installer_rebuild_is_byte_deterministic(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
