"""Red-first guard against policy expansion beyond hand-reviewed frontmatter.

Owner-local tests. They cannot authorize a real model run, grant, merge or action.
"""
import unittest
from pathlib import Path
from tools.ghaw_trigger_gate import check, get_frontmatter

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = (ROOT/'.github/workflows/twf-autonomous-developer.md').read_text()
LOCK = 'name: synthetic only\n"on":\n  workflow_dispatch:\njobs:\n  test:\n    runs-on: ubuntu-latest\n'

class ScopedFrontmatterTests(unittest.TestCase):
    def denied(self, src):
        report=check(src, LOCK)
        self.assertEqual(report['status'], 'FAIL_CLOSED')
        for k in ('may_activate','may_run_model','may_write_repo','may_spend','may_publish','may_release_any_lease'):
            self.assertIs(report[k], False)

    def change(self, original, replacement):
        self.assertEqual(ORIGINAL.count(original), 1)
        return ORIGINAL.replace(original,replacement,1)

    def test_positive_exact_scoped_frontmatter(self):
        self.assertEqual(check(ORIGINAL,LOCK)['status'], 'MANUAL_ONLY_EVENT_SHAPE_OBSERVED_NOT_ENGINE_APPROVAL')

    def test_positive_body_edit_does_not_change_approval(self):
        self.assertEqual(check(ORIGINAL+'\n# editorial body-only note\n',LOCK)['status'], 'MANUAL_ONLY_EVENT_SHAPE_OBSERVED_NOT_ENGINE_APPROVAL')

    def test_frontmatter_digest_field_comes_from_checked_policy(self):
        report=check(ORIGINAL,LOCK)
        self.assertIn('approved_frontmatter_sha256',report)
        self.assertEqual(len(report['approved_frontmatter_sha256']),64)
        self.assertTrue(report['approved_frontmatter_matches'])

    def test_contents_write_denied(self): self.denied(self.change('contents: read','contents: write'))
    def test_issues_write_denied(self): self.denied(self.change('issues: read','issues: write'))
    def test_pull_requests_write_denied(self): self.denied(self.change('pull-requests: read','pull-requests: write'))
    def test_draft_disabled_denied(self): self.denied(self.change('draft: true','draft: false'))
    def test_pr_quantity_increase_denied(self): self.denied(self.change('    draft: true\n    max: 1','    draft: true\n    max: 2'))
    def test_allowed_files_wildcard_denied(self): self.denied(self.change("- 'src/**'","- '**'"))
    def test_allowed_files_extended_denied(self): self.denied(self.change("- 'docs/EXPERIMENT_LOG.md'","- 'docs/EXPERIMENT_LOG.md'\n      - '.github/**'"))
    def test_protected_files_exclusion_removed_denied(self): self.denied(self.change('    protected-files: blocked\n',''))
    def test_pr_prefix_changed_denied(self): self.denied(self.change("title-prefix: '[TWF autonomous] '","title-prefix: '[NOT TWF] '"))
    def test_issue_prefix_changed_denied(self): self.denied(self.change("title-prefix: '[TWF blocked] '","title-prefix: '[SUPPRESS] '"))
    def test_unreviewed_import_rejected(self): self.denied(self.change('network: defaults\n','network: defaults\nimports:\n  - imported-policy.md\n'))
    def test_unreviewed_engine_rejected(self): self.denied(self.change('network: defaults\n','network: defaults\nengine: gemini\n'))
    def test_unreviewed_tools_rejected(self): self.denied(self.change('network: defaults\n','network: defaults\ntools:\n  github:\n    mode: write\n'))
    def test_unreviewed_mcp_server_rejected(self): self.denied(self.change('network: defaults\n','network: defaults\nmcp-servers:\n  unsafe: {}\n'))
    def test_unreviewed_safe_output_rejected(self): self.denied(self.change('safe-outputs:\n','safe-outputs:\n  push-to-pull-request:\n    enabled: true\n'))
    def test_unreviewed_concurrency_rejected(self): self.denied(self.change('network: defaults\n','network: defaults\nconcurrency:\n  group: unsafe\n'))
    def test_unreviewed_permissions_new_key_rejected(self): self.denied(self.change('  contents: read\n','  contents: read\n  actions: write\n'))

if __name__ == '__main__': unittest.main()
