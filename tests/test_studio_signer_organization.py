"""PR149 Authenticode signer organization policy (mocked, never runs Windows Studio).

The real Windows Authenticode cryptographic verification is deliberately not
simulated as proof; these tests inspect the PowerShell command assembled by
the actual Studio gate and its companion launcher.
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import studio_host_gate as gate

EXPECTED=r'(^|,\s*)O=Roblox Corporation(\s*,|$)'


def pattern_in(script):
    found=re.findall(r"-notmatch '([^']+)'",script)
    if len(found)!=1:
        raise AssertionError('one signer Subject -notmatch rule expected')
    return found[0]


class SignerOrganizationGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as name:
            exe=Path(name)/'RobloxStudioBeta.exe'
            exe.write_bytes(b'untrusted_test_only')
            commands=[]
            def fake_runner(argv, **kwargs):
                commands.append(argv)
                return SimpleNamespace(stdout=gate.SIGNATURE_SENTINEL+'\n',returncode=0,stderr='')
            cls.assert_called=gate.verify_windows_studio_signature(
                exe,runner=fake_runner,system='Windows')
            cls.command=commands[0][-1]
        cls.subject_rule=pattern_in(cls.command)

    def matches(self,subject):
        return bool(re.search(self.subject_rule,subject,re.IGNORECASE))

    def test_python_requires_exact_organization_field(self):
        self.assertEqual(self.subject_rule,EXPECTED)

    def test_powershell_launcher_uses_same_field_policy(self):
        text=(ROOT/'tools/launch_trusted_studio_probe.ps1').read_text(encoding='utf-8')
        self.assertEqual(pattern_in(text),EXPECTED)

    def test_authenticode_status_and_certificate_still_required(self):
        self.assertIn("$s.Status -ne 'Valid'",self.command)
        self.assertIn("$null -eq $s.SignerCertificate",self.command)
        launcher=(ROOT/'tools/launch_trusted_studio_probe.ps1').read_text(encoding='utf-8')
        self.assertIn("$signature.Status -ne 'Valid'",launcher)
        self.assertIn("$null -eq $signature.SignerCertificate",launcher)

    def test_accept_organization_alone(self):
        self.assertTrue(self.matches('O=Roblox Corporation'))

    def test_accept_organization_first_with_country(self):
        self.assertTrue(self.matches('O=Roblox Corporation, C=US'))

    def test_accept_organization_between_other_fields(self):
        self.assertTrue(self.matches('CN=Roblox Studio, O=Roblox Corporation, C=US'))

    def test_reject_common_name_containing_roblox(self):
        self.assertFalse(self.matches('CN=Roblox Studio LLC, O=Other Vendor, C=US'))

    def test_reject_only_organizational_unit_roblox(self):
        self.assertFalse(self.matches('OU=Roblox Corporation, O=Other Vendor'))

    def test_reject_fake_organization_prefix(self):
        self.assertFalse(self.matches('O=Fake Roblox Corporation, C=US'))

    def test_reject_fake_organization_suffix(self):
        self.assertFalse(self.matches('O=Roblox Corporation Fake, C=US'))

    def test_reject_organization_substring(self):
        self.assertFalse(self.matches('O=Fictional Roblox Corporation Unit'))

    def test_reject_roblox_only_common_name(self):
        self.assertFalse(self.matches('CN=Roblox Corporation'))

    def test_reject_missing_organization(self):
        self.assertFalse(self.matches('CN=Generic Studio, OU=Apps, C=US'))

    def test_reject_empty_certificate_subject(self):
        self.assertFalse(self.matches(''))

    def test_reject_wrong_company_with_roblox_ou(self):
        self.assertFalse(self.matches('CN=Game Tool, OU=Roblox Studio, O=Thirdparty'))


if __name__=='__main__':
    unittest.main()
