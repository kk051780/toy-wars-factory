"""A14: verify Windows host reconnaissance is isolated from Roblox execution.

This is a *contract* check for an explicitly non-attesting discovery job;
passing these tests does not mean Roblox Studio is installed or launched.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / '.github/workflows/twf-windows-studio-availability.yml'

class WindowsStudioHostContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FLOW.read_text(encoding='utf-8')

    def test_dedicated_windows_runner(self):
        self.assertIn('runs-on: windows-latest', self.source)

    def test_explicitly_unprivileged(self):
        self.assertRegex(self.source, r'(?m)^permissions:\s*\{\s*\}\s*$')
        self.assertNotIn('secrets.', self.source)
        self.assertNotIn('GH_TOKEN', self.source)

    def test_pull_request_scoped_and_manual_only(self):
        self.assertIn('pull_request:', self.source)
        self.assertIn('workflow_dispatch:', self.source)
        self.assertIn('.github/workflows/twf-windows-studio-availability.yml', self.source)
        self.assertNotIn('schedule:', self.source)
        self.assertNotIn('push:', self.source)

    def test_job_never_installs_studio(self):
        for command in ('Invoke-WebRequest', 'Start-Process', 'Install-Module', 'winget', 'choco install', 'Install-Package', 'Invoke-RestMethod'):
            self.assertNotIn(command.lower(), self.source.lower())

    def test_job_does_not_run_arbitrary_repository_code(self):
        self.assertNotIn('actions/checkout', self.source)
        self.assertNotIn('runScriptFile', self.source)
        self.assertNotIn('RunScript', self.source)
        self.assertNotIn('python ', self.source.lower())

    def test_studio_detection_is_restricted(self):
        self.assertIn('Roblox\\Versions', self.source)
        self.assertIn('RobloxStudioBeta.exe', self.source)
        self.assertIn('Get-ChildItem', self.source)

    def test_signer_is_verified(self):
        self.assertIn('Get-AuthenticodeSignature', self.source)
        self.assertIn('SignerCertificate', self.source)
        self.assertIn("'Valid'", self.source)

    def test_reports_all_three_discovery_outcomes(self):
        for status in ('STUDIO_NOT_INSTALLED', 'STUDIO_PRESENT_SIGNED', 'STUDIO_PRESENT_UNTRUSTED'):
            self.assertIn(status, self.source)

    def test_explicitly_denies_any_engine_claim(self):
        for key in ('studio_executed', 'xml_loaded', 'play_mode_verified', 'roblox_engine_verified', 'public_publish_authorized'):
            self.assertIn(key, self.source)

    def test_immutable_execution_budget(self):
        self.assertIn('timeout-minutes: 5', self.source)
        self.assertNotIn('continue-on-error:', self.source)

    def test_retain_machine_readable_result(self):
        self.assertIn('ConvertTo-Json', self.source)
        self.assertIn('studio-host-availability.json', self.source)
        self.assertIn('actions/upload-artifact@v4', self.source)
        self.assertIn('twf-windows-studio-availability-not-engine', self.source)

    def test_never_echo_all_environment(self):
        for phrase in ('Get-ChildItem Env:', 'printenv', 'set |', '$env:PATH', 'env: *toJSON('):
            self.assertNotIn(phrase.lower(), self.source.lower())

if __name__ == '__main__':
    unittest.main()
