"""PR150 Windows-only inventory signer policy. No Studio launch/download/Roblox calls."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FLOW=ROOT/'.github/workflows/twf-windows-studio-availability.yml'
EXPECTED=r'(^|,\s*)O=Roblox Corporation(\s*,|$)'

class HostInventorySignerOrganization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=FLOW.read_text(encoding='utf-8')
        match=re.search(r"\$sig\.SignerCertificate\.Subject\s+-match\s+'([^']+)'",cls.source)
        if match is None:
            raise AssertionError('required signer organization condition missing')
        cls.rule=match.group(1)

    def matches(self,subject):
        return bool(re.search(self.rule,subject,re.IGNORECASE))

    def test_exact_organization_rule(self):
        self.assertEqual(self.rule,EXPECTED)

    def test_preserves_valid_and_certificate_gate(self):
        self.assertIn("$sig.Status -eq 'Valid'",self.source)
        self.assertIn("$null -ne $sig.SignerCertificate",self.source)

    def test_accepted_organization_bare(self):
        self.assertTrue(self.matches('O=Roblox Corporation'))

    def test_accepted_organization_in_full_dn(self):
        self.assertTrue(self.matches('CN=Roblox Studio, O=Roblox Corporation, C=US'))

    def test_accepted_organization_first(self):
        self.assertTrue(self.matches('O=Roblox Corporation, C=US'))

    def test_reject_cn_only(self):
        self.assertFalse(self.matches('CN=Roblox Corporation, O=Third Party, C=US'))

    def test_reject_ou_only(self):
        self.assertFalse(self.matches('OU=Roblox Corporation, O=Unrelated Vendor'))

    def test_reject_fake_organization_prefix(self):
        self.assertFalse(self.matches('O=Fake Roblox Corporation'))

    def test_reject_fake_organization_suffix(self):
        self.assertFalse(self.matches('O=Roblox Corporation Fake'))

    def test_reject_unrelated_org_containing_roblox(self):
        self.assertFalse(self.matches('O=Thirdparty Roblox Services'))

    def test_reject_roblox_cn_when_no_organization(self):
        self.assertFalse(self.matches('CN=Roblox Studio'))

    def test_reject_organization_substring(self):
        self.assertFalse(self.matches('O=Roblox Corporation International'))

    def test_reject_empty_subject(self):
        self.assertFalse(self.matches(''))

    def test_inventory_cannot_launch_or_install_studio(self):
        self.assertIn('runs-on: windows-latest',self.source)
        self.assertNotIn('Start-Process',self.source)
        self.assertNotIn('Invoke-WebRequest',self.source)
        self.assertNotIn('actions/checkout',self.source)
        self.assertNotIn('--task RunScript',self.source)

    def test_no_inference_that_studio_was_executed(self):
        for field in ('studio_executed = $false','xml_loaded = $false',
                      'play_mode_verified = $false','roblox_engine_verified = $false',
                      'public_publish_authorized = $false'):
            self.assertIn(field,self.source)


if __name__=='__main__':
    unittest.main()
