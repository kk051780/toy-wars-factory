"""Run the production Actions writer against temporary local Git remotes.

No real token, external GitHub writes, or workflow dispatch is performed.
The 512 maximum is lowered only in a copy of the *extracted* writer shell.
"""
import os
import subprocess
import unittest
from pathlib import Path
from test_handoff_status_writer_git import WriterGitBoundary, actual_writer_shell, command


class RotationOfActualWriter(unittest.TestCase):
    def setUp(self):
        self.fixture = WriterGitBoundary("test_status_only_update_pushes_exactly_two_paths")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.script = actual_writer_shell().replace('max=512', 'max=3')
        self.assertIn('max=3', self.script)
        self.assertIn('prior-snapshot-tip:', self.script)

    def run_writer(self, n):
        f = self.fixture
        f.change_status()
        (f.work / 'status/CHAT_HANDOFF.md').write_text('generation fixture %d\n' % n)
        env = os.environ.copy()
        env.update({
            'PATH': str(f.fake_bin) + os.pathsep + os.environ.get('PATH', ''),
            'GH_TOKEN': 'SYNTHETIC_NO_REAL_TOKEN',
            'TWF_SOURCE_COMMIT': f.source_sha,
            'GITHUB_STEP_SUMMARY': str(f.summary),
            'GIT_TERMINAL_PROMPT': '0'})
        return subprocess.run(['bash','-euo','pipefail','-c', self.script],
            cwd=f.work, env=env, capture_output=True, text=True, timeout=30)

    def ref(self, refname):
        return command('git','--git-dir',str(self.fixture.remote),
                       'rev-parse',refname)

    def test_exact_step_rolls_at_cap_without_rewriting_first_generation(self):
        base = 'refs/heads/twf-handoff-snapshots'
        next_ref = base + '-g0002'
        for n in range(3):
            r = self.run_writer(n)
            self.assertEqual(r.returncode, 0, r.stderr)
        archived = self.ref(base)
        r = self.run_writer(3)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ref(base), archived)
        root = self.ref(next_ref)
        self.assertEqual(len(command('git','--git-dir',str(self.fixture.remote),
                            'rev-list','--parents','-n','1',root).split()), 1)
        message = command('git','--git-dir',str(self.fixture.remote),
                          'show','-s','--format=%B',root)
        self.assertIn('prior-snapshot-tip: '+archived, message)
        self.assertIn('snapshot-generation: 2', message)
        self.assertEqual(self.ref('refs/heads/main'), self.fixture.source_sha)

    def test_no_change_at_cap_is_not_a_new_generation(self):
        base='refs/heads/twf-handoff-snapshots'
        for n in range(3):
            self.assertEqual(self.run_writer(n).returncode, 0)
        old = self.ref(base)
        same = self.run_writer(2)
        self.assertEqual(same.returncode, 0, same.stderr)
        self.assertEqual(self.ref(base), old)
        self.assertIn('NO_CHANGE', self.fixture.summary.read_text())

    def test_retired_generation_tamper_rejects_without_overwrite(self):
        base = 'refs/heads/twf-handoff-snapshots'
        successor = base + '-g0002'
        for n in range(4):
            r = self.run_writer(n)
            self.assertEqual(r.returncode, 0, r.stderr)
        protected = self.ref(successor)
        archived = self.ref(base)
        earlier = command('git', '--git-dir', str(self.fixture.remote),
                          'rev-parse', archived + '^')
        # Force in TEMPORARY bare Git fixture only, simulating outside tampering.
        command('git', 'push','-q','--force','origin', earlier+':'+base,
                cwd=self.fixture.work)
        r = self.run_writer(5)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.ref(successor), protected)
        self.assertEqual(self.ref(base), earlier)

    def test_missing_ancestor_generation_rejected(self):
        base = 'refs/heads/twf-handoff-snapshots'
        self.assertEqual(self.run_writer(0).returncode, 0)
        first = self.ref(base)
        command('git', 'push', '-q', 'origin',
                first+':'+base+'-g0003', cwd=self.fixture.work)
        r = self.run_writer(1)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.ref(base), first)


if __name__ == '__main__':
    unittest.main()
