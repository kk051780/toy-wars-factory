"""Security regression for a trusted, no-inference GH-AW compiler smoke workflow.

Checking only event-shape AFTER gh-aw compile is too late; verify source policy
BEFORE installing the compiler and never run PR-head Python during preflight.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / '.github/workflows/agent-compile-probe.yml'
SOURCE = ROOT / '.github/workflows/twf-autonomous-developer.md'
APPROVED = '2d82661d394cf9e9422becc924b8edcc4ca2628e8bc243b076b39dfd8798202c'


def step_span(workflow: str, label: str) -> str:
    marker = '      - name: ' + label + '\n'
    assert workflow.count(marker) == 1, ('missing or duplicate step', label)
    start = workflow.index(marker)
    end = workflow.find('\n      - name:', start+len(marker))
    return workflow[start:end if end >= 0 else len(workflow)]


def inline_preflight(workflow: str) -> str:
    step = step_span(workflow, 'Verify approved agent policy before compiling')
    marker = '        run: |\n'
    assert step.count(marker) == 1
    lines = step.split(marker, 1)[1].splitlines()
    assert all(x.startswith('          ') for x in lines if x.strip())
    return '\n'.join(x[10:] for x in lines)+'\n'


def run_fixture(script: str, candidate: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as td:
        here=Path(td)
        (here/'.github/workflows').mkdir(parents=True)
        (here/'.github/workflows/twf-autonomous-developer.md').write_text(candidate,encoding='utf-8')
        return subprocess.run(['bash','-e','-c',script],cwd=here,capture_output=True,text=True,timeout=8)


class PreCompilerFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow=FLOW.read_text(encoding='utf-8')
        cls.md=SOURCE.read_text(encoding='utf-8')

    def test_branch_limited_push(self):
        self.assertRegex(self.workflow, r'(?m)^  push:\n    branches: \[main\]\n    paths:')

    def test_manual_dispatch_preserved(self):
        self.assertRegex(self.workflow, r'(?m)^  workflow_dispatch:\s*$')

    def test_global_repo_read_only(self):
        self.assertIn('permissions:\n  contents: read\n',self.workflow)
        self.assertNotIn('contents: write',self.workflow)

    def test_checkout_credential_persistence_disabled(self):
        self.assertIn('      - uses: actions/checkout@v4\n        with:\n          persist-credentials: false\n',self.workflow)

    def test_compile_job_foreign_repo_denied(self):
        self.assertRegex(self.workflow, r"(?m)^    if: github.repository == 'kk051780/toy-wars-factory'$" )

    def test_preflight_exists_once(self):
        self.assertEqual(self.workflow.count('      - name: Verify approved agent policy before compiling\n'),1)

    def test_preflight_before_token_install(self):
        self.assertLess(self.workflow.index('      - name: Verify approved agent policy before compiling'),self.workflow.index('      - name: Install official agentic workflows compiler'))

    def test_preflight_before_compiler_run(self):
        self.assertLess(self.workflow.index('      - name: Verify approved agent policy before compiling'),self.workflow.index('      - name: Compile workflow, without starting an AI job'))

    def test_preflight_is_inline_not_repo_code(self):
        src=inline_preflight(self.workflow)
        self.assertIn("python3 - <<'PY'",src)
        self.assertNotIn('python3 tools/',src)
        self.assertNotIn('curl ',src)
        self.assertNotIn('pip install',src)

    def test_preflight_embeds_exact_digest(self):
        self.assertIn(APPROVED,inline_preflight(self.workflow))
        self.assertEqual(hashlib.sha256((self.md[4:self.md.find('\n---\n',4)]+'\n').encode()).hexdigest(),APPROVED)

    def test_positive_approved_markdown(self):
        result=run_fixture(inline_preflight(self.workflow),self.md)
        self.assertEqual(result.returncode,0,(result.stdout,result.stderr))

    def test_positive_editorial_body_change(self):
        result=run_fixture(inline_preflight(self.workflow),self.md+'\nReadability note.\n')
        self.assertEqual(result.returncode,0,(result.stdout,result.stderr))

    def test_denies_scheduler_reintroduction(self):
        mutated=self.md.replace('  workflow_dispatch:',"  schedule:\n    - cron: '*/20 * * * *'\n  workflow_dispatch:",1)
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),mutated).returncode,0)

    def test_denies_new_ai_engine(self):
        mutated=self.md.replace('network: defaults','engine: gemini\nnetwork: defaults',1)
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),mutated).returncode,0)

    def test_denies_scope_expansion(self):
        mutated=self.md.replace('  contents: read','  contents: write',1)
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),mutated).returncode,0)

    def test_denies_removed_protected_files_rule(self):
        mutated=self.md.replace('    protected-files: blocked\n','',1)
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),mutated).returncode,0)

    def test_denies_yaml_merge_alias(self):
        mutated=self.md.replace('network: defaults','network: defaults\nimports: *unreviewed',1)
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),mutated).returncode,0)

    def test_denies_invalid_frontmatter_missing(self):
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),self.md[4:]).returncode,0)

    def test_denies_invalid_frontmatter_unclosed(self):
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),'---\non:\n  workflow_dispatch:').returncode,0)

    def test_denies_oversize_agent_md(self):
        self.assertNotEqual(run_fixture(inline_preflight(self.workflow),self.md+('x'*40000)).returncode,0)

    def test_compiler_is_version_pinned(self):
        self.assertIn('gh extension install github/gh-aw --pin v0.93.2',self.workflow)

    def test_strict_compile_after_preflight(self):
        self.assertIn('gh aw compile --strict .github/workflows/twf-autonomous-developer.md',self.workflow)

    def test_postcompile_lock_event_check_preserved(self):
        self.assertIn('python3 tools/ghaw_trigger_gate.py \\',self.workflow)

    def test_compiled_lock_not_committed_by_probe(self):
        self.assertIn('include-hidden-files: true',self.workflow)
        self.assertNotIn('git push',self.workflow)
        self.assertNotIn('gh aw run',self.workflow)

if __name__=='__main__': unittest.main()
