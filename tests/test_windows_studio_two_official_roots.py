"""PR150 official two-path Roblox Studio host inventory regression.

Only source-contract tests; they do NOT prove a Windows binary was installed,
signed, launched or executed in a real Roblox engine.
"""
from pathlib import Path
import unittest

FLOW = (Path(__file__).resolve().parents[1] /
        ".github/workflows/twf-windows-studio-availability.yml")


class OfficialStudioInstallRoots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FLOW.read_text(encoding="utf-8")

    def test_scans_localappdata_location(self):
        self.assertIn("Join-Path $env:LOCALAPPDATA 'Roblox\\Versions'", self.source)

    def test_scans_official_programfiles_x86_location(self):
        self.assertIn("[Environment]::GetEnvironmentVariable('ProgramFiles(x86)')", self.source)
        self.assertIn("Join-Path $programFilesX86 'Roblox\\Versions'", self.source)

    def test_iterates_over_all_configured_roots(self):
        self.assertIn("foreach ($root in $roots)", self.source)
        self.assertIn("Get-ChildItem -LiteralPath $root", self.source)

    def test_signature_checked_for_each_candidate(self):
        self.assertIn("foreach ($candidate in $found)", self.source)
        self.assertIn("Get-AuthenticodeSignature -LiteralPath $candidate.FullName", self.source)

    def test_does_not_report_absence_for_incomplete_root_configuration(self):
        self.assertIn("'HOST_INVENTORY_INCOMPLETE'", self.source)
        self.assertIn("if ($scanRootsChecked -ne 2)", self.source)

    def test_receipt_records_limited_search_scope(self):
        self.assertIn("scan_scope = 'TWO_OFFICIAL_WINDOWS_LOCATIONS_ONLY'", self.source)
        self.assertIn("scan_roots_checked = $scanRootsChecked", self.source)
        self.assertIn("scan_roots_present = $scanRootsPresent", self.source)

    def test_preserves_read_only_and_no_engine_claim(self):
        self.assertIn("permissions: {}", self.source)
        for blocked in ("actions/checkout", "Start-Process", "Invoke-WebRequest",
                        "Install-Module", "RobloxStudioInstaller", "--task RunScript",
                        "secrets.", "GH_TOKEN"):
            self.assertNotIn(blocked, self.source)
        for marker in ("studio_executed = $false", "xml_loaded = $false",
                       "roblox_engine_verified = $false", "public_publish_authorized = $false"):
            self.assertIn(marker, self.source)


if __name__ == "__main__":
    unittest.main()
