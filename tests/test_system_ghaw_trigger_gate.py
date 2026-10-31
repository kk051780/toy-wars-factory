"""Protected source-side tests: a compiled AI workflow cannot auto-start."""
import unittest
from pathlib import Path
from tools.ghaw_trigger_gate import check, get_frontmatter, event_names, secure_network

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.github/workflows/twf-autonomous-developer.md'
SYNTHETIC_LOCK='''name: compilation fixture only
"on":
  workflow_dispatch:
    inputs:
      reason:
        required: false
jobs:
  probe:
    runs-on: ubuntu-latest
'''

class ProtectedManualTriggerTests(unittest.TestCase):
    def test_source_checked_in_not_scheduled(self):
        self.assertEqual(event_names(get_frontmatter(SOURCE.read_text())),{'workflow_dispatch'})
    def test_local_manual_lock_not_authorization(self):
        report=check(SOURCE.read_text(),SYNTHETIC_LOCK)
        self.assertEqual(report['status'],'MANUAL_ONLY_EVENT_SHAPE_OBSERVED_NOT_ENGINE_APPROVAL')
        for field in ('may_activate','may_run_model','may_write_repo','may_spend','may_publish','may_release_any_lease'):
            self.assertFalse(report[field])
    def test_explicit_strict_minimum_network(self):
        self.assertTrue(secure_network(SOURCE.read_text()))
    def test_live_source_original_cron_rejected(self):
        body=SOURCE.read_text().replace('  workflow_dispatch:',
            "  schedule:\n    - cron: '8,28,48 * * * *'\n  workflow_dispatch:",1)
        self.assertEqual(check(body,SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_compiled_cron_rejected(self):
        lock=SYNTHETIC_LOCK.replace('  workflow_dispatch:',
            "  schedule:\n    - cron: '8,28,48 * * * *'\n  workflow_dispatch:",1)
        self.assertEqual(check(SOURCE.read_text(),lock)['status'],'FAIL_CLOSED')
    def test_push_rejected(self):
        self.assertEqual(check(SOURCE.read_text(),SYNTHETIC_LOCK.replace('  workflow_dispatch:', '  push:\n  workflow_dispatch:'))['status'],'FAIL_CLOSED')
    def test_pr_rejected(self):
        self.assertEqual(check(SOURCE.read_text(),SYNTHETIC_LOCK.replace('  workflow_dispatch:', '  pull_request:\n  workflow_dispatch:'))['status'],'FAIL_CLOSED')
    def test_workflow_call_rejected(self):
        self.assertEqual(check(SOURCE.read_text(),SYNTHETIC_LOCK.replace('  workflow_dispatch:', '  workflow_call:\n  workflow_dispatch:'))['status'],'FAIL_CLOSED')
    def test_duplicate_on_rejected(self):
        self.assertEqual(check(SOURCE.read_text(),SYNTHETIC_LOCK+'\non:\n  schedule:\n')['status'],'FAIL_CLOSED')
    def test_flow_on_rejected(self):
        self.assertEqual(check(SOURCE.read_text(),"on: {workflow_dispatch: {}}\njobs:\n")['status'],'FAIL_CLOSED')
    def test_inline_schedule_rejected(self):
        self.assertEqual(check(SOURCE.read_text(),"on: schedule\njobs:\n")['status'],'FAIL_CLOSED')
    def test_empty_lock_rejected(self):
        self.assertEqual(check(SOURCE.read_text(),"")['status'],'FAIL_CLOSED')
    def test_false_external_entitlement_rejected(self):
        x=check(SOURCE.read_text(),SYNTHETIC_LOCK)
        self.assertFalse(x['model_entitlement_proven'])
        self.assertFalse(x['model_spending_cap_proven'])
        self.assertFalse(x['independent_review_proven'])
    def test_compiled_marker_not_engine_proof(self):
        x=check(SOURCE.read_text(),SYNTHETIC_LOCK)
        self.assertFalse(x['actual_gh_aw_compiled_here'])
    def test_no_yaml_alias_triggers(self):
        self.assertEqual(check(SOURCE.read_text(),"on: *other\njobs:\n")['status'],'FAIL_CLOSED')
    def test_only_expected_current_source(self):
        text=SOURCE.read_text()
        self.assertIn('protected-files: blocked',text)
        self.assertNotIn('  schedule:',get_frontmatter(text))

    def test_source_missing_network_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults\n',''),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_wildcard_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: {allowed: ["*"]}'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_custom_domain_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: {allowed: ["example.org"]}'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_blocked_all_denied_for_this_pin(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: {}'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_extra_network_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: defaults\nnetwork: defaults'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_strict_disabled_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: defaults\nstrict: false'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_strict_disabled_true_also_denied_for_fixed_policy(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: defaults\nstrict: true'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_uppercase_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','NETWORK: defaults'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_alias_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: *external'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_quoted_key_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','"network": defaults'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_not_in_frontmatter_denied(self):
        body=SOURCE.read_text().replace('network: defaults\n','').replace('---\n\n# TOY', '---\n\nnetwork: defaults\n# TOY')
        self.assertEqual(check(body,SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_lax_line_comment_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: defaults # allowed'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_source_network_merge_key_denied(self):
        self.assertEqual(check(SOURCE.read_text().replace('network: defaults','network: defaults\nfoo: &anchor anything\nbar: *anchor'),SYNTHETIC_LOCK)['status'],'FAIL_CLOSED')
    def test_src_network_keeps_no_grants(self):
        p=check(SOURCE.read_text(),SYNTHETIC_LOCK)
        self.assertEqual(p['status'],'MANUAL_ONLY_EVENT_SHAPE_OBSERVED_NOT_ENGINE_APPROVAL')
        self.assertFalse(p['may_activate'])
        self.assertFalse(p['may_run_model'])
        self.assertFalse(p['may_spend'])

if __name__=='__main__': unittest.main()
