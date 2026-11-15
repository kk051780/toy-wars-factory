"""Real local Git nonforce push race, no network/repository writes."""
from pathlib import Path
import subprocess
import tempfile
import unittest

BRANCH = 'rc/p0d-s1-kids-rc01'


def git(cwd, *args, ok=True):
    result = subprocess.run(['git', '-C', str(cwd), *args], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ok and result.returncode:
        raise AssertionError(f'git {args} failed: {result.stderr}')
    return result


class TestGitNonforceRace(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.remote = root / 'origin.git'
        self.seed = root / 'seed'
        self.w1 = root / 'writer1'
        self.w2 = root / 'writer2'
        git(root, 'init', '--bare', str(self.remote))
        git(root, 'init', '-b', BRANCH, str(self.seed))
        git(self.seed, 'config', 'user.email', 'p0d-test@example.invalid')
        git(self.seed, 'config', 'user.name', 'P0D Test')
        (self.seed / 'common.txt').write_text('base\n')
        git(self.seed, 'add', '.')
        git(self.seed, 'commit', '-m', 'original approved RC')
        git(self.seed, 'remote', 'add', 'origin', str(self.remote))
        git(self.seed, 'push', 'origin', 'HEAD:refs/heads/'+BRANCH)
        for work in (self.w1,self.w2):
            git(root, 'clone', '-b', BRANCH, str(self.remote), str(work))
            git(work, 'config', 'user.email', 'p0d-test@example.invalid')
            git(work, 'config', 'user.name', 'P0D Test')

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, wd, fname, content):
        (wd / fname).write_text(content)
        git(wd, 'add', fname)
        git(wd, 'commit', '-m', fname)

    def publish(self, wd):
        return git(wd,'push','origin','HEAD:refs/heads/'+BRANCH,ok=False)

    def test_disjoint_writers_one_loses_then_retests_and_succeeds(self):
        self.edit(self.w1, 'castle.txt', 'castle art\n')
        self.edit(self.w2, 'forest.txt', 'forest art\n')
        self.assertEqual(self.publish(self.w1).returncode,0)
        self.assertNotEqual(self.publish(self.w2).returncode,0)
        stale = git(self.w2,'rev-parse','HEAD').stdout.strip()
        git(self.w2,'fetch','origin',BRANCH)
        git(self.w2,'rebase','FETCH_HEAD')
        updated = git(self.w2,'rev-parse','HEAD').stdout.strip()
        self.assertNotEqual(stale,updated,'A stale commit may not reuse old sameHEAD CI')
        self.assertEqual(self.publish(self.w2).returncode,0)
        git(self.w1,'fetch','origin',BRANCH)
        tree = git(self.w1,'ls-tree','-r','--name-only','FETCH_HEAD').stdout
        self.assertIn('castle.txt',tree)
        self.assertIn('forest.txt',tree)

    def test_same_file_never_overwrites_without_conflict_resolution(self):
        self.edit(self.w1,'common.txt','one\n')
        self.edit(self.w2,'common.txt','two\n')
        self.assertEqual(self.publish(self.w1).returncode,0)
        self.assertNotEqual(self.publish(self.w2).returncode,0)
        git(self.w2,'fetch','origin',BRANCH)
        self.assertNotEqual(git(self.w2,'rebase','FETCH_HEAD',ok=False).returncode,0)
        current = git(self.w2,'show','FETCH_HEAD:common.txt').stdout
        self.assertEqual(current,'one\n')

if __name__ == '__main__':
    unittest.main(verbosity=2)
