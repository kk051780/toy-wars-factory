"""GQ508 existing-author neutral post-round KO source selection fail-closed tests."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
import json

sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_original508_neutral_ko import (
    git_blob,mapping,author_policy,overlay,prepare,SWARM,OWNER508_POLICY_BLOB,BEFORE,AFTER
)


class Neutral508SingleOwner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=Path(os.environ["GQ508_AUTHOR_POLICY"]) if os.environ.get("GQ508_AUTHOR_POLICY") else None
        cls.base=Path(os.environ["GQ508_BASE31"]) if os.environ.get("GQ508_BASE31") else None

    def test_git_sha_known_blob(self):
        self.assertEqual(git_blob(b"hello\n"),"ce013625030ba8dba906f756967f9e9ca394464a")

    def test_fails_wrong_author_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"wrong.luau";p.write_text("return False")
            with self.assertRaisesRegex(ValueError,"ORIGINAL508_GIT_BLOB_DRIFT"):
                author_policy(p)

    def test_refuses_non31_map(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"p.json";p.write_text(json.dumps({"tree":{"ServerScriptService":{}}}))
            with self.assertRaisesRegex(ValueError,"NOT_EXACT_SINGLE_SWARM_31"):
                mapping(p)

    def test_refuse_inplace_current_game(self):
        if not self.policy or not self.base:self.skipTest("CI provides original author and actual31")
        with self.assertRaisesRegex(ValueError,"NOT_INPLACE"):
            prepare(self.base,self.policy,self.base)

    def test_exact_existing_author_policy_pinned(self):
        if not self.policy:self.skipTest("CI checks out #508 immutable author")
        self.assertEqual(git_blob(self.policy.read_bytes()),OWNER508_POLICY_BLOB)
        p=author_policy(self.policy)
        self.assertIn('function Fence.mayCredit(',p)
        self.assertIn('model:IsDescendantOf(hordeFolder)',p)
        self.assertIn('session.rules.winner',p)
        self.assertEqual(p.count("local KoFence=(function()"),1)

    def test_only_single_died_callback_and_source_reversible(self):
        if not self.policy or not self.base:self.skipTest("CI actual31")
        _,current=mapping(self.base)
        old=current[SWARM].read_text(encoding="utf-8")
        p=author_policy(self.policy)
        changed=overlay(old,p)
        self.assertEqual(changed.count("h.Died:Connect("),1)
        self.assertEqual(changed.count("KoFence.mayCredit("),1)
        self.assertEqual(changed.replace("local KoFence=(function()\n"+p.split("local KoFence=(function()\n",1)[1],"",1).replace(AFTER,BEFORE,1),old)

    def test_reject_double_author_source_apply(self):
        if not self.policy or not self.base:self.skipTest("CI actual31")
        _,current=mapping(self.base)
        original=current[SWARM].read_text(encoding="utf-8")
        p=author_policy(self.policy)
        with self.assertRaisesRegex(ValueError,"ALREADY_SELECTED"):
            overlay(overlay(original,p),p)

    def test_only_swarm_changed_other30_exact(self):
        if not self.policy or not self.base:self.skipTest("CI actual31")
        _,previous=mapping(self.base)
        out=self.base.parent/"UNIT_GQ508_SELECTED31.project.json"
        prepare(self.base,self.policy,out)
        _,new=mapping(out)
        self.assertEqual([k for k in previous if previous[k].read_bytes()!=new[k].read_bytes()],[SWARM])
        prepare(self.base,self.policy,out)
        _,again=mapping(out)
        self.assertEqual(new[SWARM].read_bytes(),again[SWARM].read_bytes())


if __name__=="__main__":unittest.main()
