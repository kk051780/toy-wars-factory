"""Prevent unreviewed PR test code from inheriting GitHub read credentials."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF = ROOT / '.github/workflows/bootstrap-quality.yml'

class BootstrapTokenIsolationTests(unittest.TestCase):
    def setUp(self):
        self.content = WF.read_text(encoding='utf-8')

    def steps(self):
        matches = list(re.finditer(r'^      - (?:name|uses): ', self.content, re.MULTILINE))
        return [self.content[m.start():matches[i + 1].start() if i + 1 < len(matches)
                else len(self.content)] for i, m in enumerate(matches)]

    def test_every_checkout_discards_persisted_credentials(self):
        checkout = [s for s in self.steps() if "uses: actions/checkout@v4" in s]
        self.assertEqual(len(checkout), 3)
        for step in checkout:
            with self.subTest(step=step.splitlines()[0]):
                self.assertRegex(step, r'(?m)^          persist-credentials: false$')

    def test_tokened_steps_are_explicit_allowlisted_native_commands_only(self):
        tokened = [s for s in self.steps() if 'GH_TOKEN: ${{ github.token }}' in s]
        self.assertEqual(len(tokened), 2)
        self.assertIn('Install the same pinned official compiler', tokened[0])
        self.assertIn('gh extension install github/gh-aw --pin v0.93.2', tokened[0])
        self.assertIn('Fetch shared coordinator with isolated read token', tokened[1])
        self.assertIn('git -c "http.extraheader=AUTHORIZATION: bearer ${GH_TOKEN}" fetch', tokened[1])
        for step in tokened:
            with self.subTest(step=step.splitlines()[0]):
                self.assertNotIn('python3 ', step)
                self.assertNotIn('gh aw compile', step)
                self.assertNotIn('lua5.4', step)

    def test_untrusted_compiler_and_hold_script_have_no_repo_token(self):
        steps = [s for s in self.steps() if 'Recompile the literal incident hold' in s]
        self.assertEqual(len(steps), 1)
        self.assertIn('gh aw compile', steps[0])
        self.assertIn('python3 tools/verify_gemini_hold.py', steps[0])
        self.assertNotIn('GH_TOKEN:', steps[0])
        self.assertNotIn('github.token', steps[0])

    def test_untrusted_python_and_lua_test_steps_receive_no_token(self):
        for step in self.steps():
            if ('python3 -m unittest discover' in step or 'lua5.4 tests/' in step
                    or 'python3 tools/build_installer.py' in step):
                with self.subTest(step=step.splitlines()[0]):
                    self.assertNotIn('GH_TOKEN:', step)
                    self.assertNotIn('GITHUB_TOKEN:', step)
                    self.assertNotIn('github.token', step)

    def test_original_lease_scope_and_compiler_hold_not_relaxed(self):
        self.assertIn('python3 /tmp/twf-trusted/repair_control.py verify-pr', self.content)
        self.assertIn('git show-ref --verify --quiet refs/remotes/origin/twf-repair-coordinator', self.content)
        self.assertIn('git show "$TWF_BASE_SHA:tools/repair_control.py"', self.content)
        self.assertIn('git diff --exit-code -- .github/workflows/twf-gemini-free-trial.lock.yml', self.content)
        self.assertIn('permissions:\n  contents: read', self.content)
        self.assertNotIn('contents: write', self.content)

if __name__ == '__main__':
    unittest.main()
