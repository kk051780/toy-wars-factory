"""Host preflight fails before any credential or GitHub callback is used."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import manual_controller_claim_witness as m

BASE={"GITHUB_REPOSITORY":m.REPO,"GITHUB_REPOSITORY_ID":m.REPO_ID,
      "GITHUB_WORKFLOW_REF":m.WORKFLOW_REF,"GITHUB_WORKFLOW_SHA":"a"*40,
      "GITHUB_ACTIONS":"true","GITHUB_JOB":"witness",
      "GITHUB_EVENT_NAME":"workflow_dispatch",
      "GITHUB_REF":"refs/heads/main","GITHUB_SHA":"a"*40,
      "GITHUB_RUN_ID":"41199999999","GITHUB_RUN_ATTEMPT":"1"}

class HostTests(unittest.TestCase):
    def test_good_shape_non_authorizing(self):
        self.assertTrue(m.validate_host_context(dict(BASE)))
    def test_every_required_field_refused_when_absent(self):
        for key in BASE:
            with self.subTest(key=key), self.assertRaisesRegex(m.WitnessHold,'UNTRUSTED_HOST_CONTEXT'):
                x=BASE.copy();del x[key];m.validate_host_context(x)
    def test_every_foreign_identity_refused(self):
        for k,v in [("GITHUB_REPOSITORY","other/repo"),("GITHUB_REPOSITORY_ID","1"),
                    ("GITHUB_WORKFLOW_REF",m.WORKFLOW_REF+'-evil'),
                    ("GITHUB_EVENT_NAME","pull_request"),("GITHUB_REF","refs/heads/feature"),
                    ("GITHUB_SHA","bad"),("GITHUB_RUN_ID","0"),("GITHUB_RUN_ATTEMPT","2")]:
            with self.subTest(k=k),self.assertRaisesRegex(m.WitnessHold,'UNTRUSTED_HOST_CONTEXT'):
                m.validate_host_context({**BASE,k:v})
    def test_wrong_type_denied_without_throwing_unexpected(self):
        for k in BASE:
            with self.subTest(k=k), self.assertRaises(m.WitnessHold):
                m.validate_host_context({**BASE,k:None})

if __name__ == '__main__':unittest.main()
