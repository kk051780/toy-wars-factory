"""Reviewed workflow SHA and accepted game-source SHA are separate identities.
Synthetic test IDs and source versions only. No provider calls or secrets.
"""
from dataclasses import replace
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import roblox_private_xml_saved as x
SOURCE=x.MAIN_BASE
WORKFLOW='f'*40
OTHER='a'*40

def cfg(workflow=WORKFLOW,source=SOURCE):
    return x.XmlStageConfig('2020','3030','4040','5050',source,'a'*64,54753,workflow)

def env(workflow=WORKFLOW,source=SOURCE):
    return {'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':x.REPOSITORY,
            'GITHUB_REF':'refs/heads/main','GITHUB_SHA':workflow,
            'GITHUB_EVENT_NAME':'workflow_dispatch',
            'TWF_ACCEPTED_GAME_SOURCE_SHA':source,
            'TWF_REVIEWED_MAIN_SHA':workflow,
            'TWF_PRIVATE_STAGE_APPROVED':'true','TWF_PROTECTED_ENVIRONMENT':'roblox-private-test',
            'TWF_TEST_UNIVERSE_ID':'2020','TWF_TEST_PLACE_ID':'3030',
            'TWF_PROD_UNIVERSE_ID':'4040','TWF_PROD_PLACE_ID':'5050'}

class ShaIdentitySeparation(unittest.TestCase):
    def test_future_workflow_sha_with_original_source_allowed_as_syntax(self):
        x.check_host_environment(cfg(),env())
        self.assertNotEqual(cfg().reviewed_workflow_sha,cfg().source_main_sha)
    def test_wrong_actions_run_sha_rejected(self):
        e=env();e['GITHUB_SHA']=OTHER
        with self.assertRaises(x.XmlStageError):x.check_host_environment(cfg(),e)
    def test_reviewed_sha_claim_mismatch_rejected(self):
        e=env();e['TWF_REVIEWED_MAIN_SHA']=OTHER
        with self.assertRaises(x.XmlStageError):x.check_host_environment(cfg(),e)
    def test_changed_accepted_source_claim_rejected(self):
        e=env();e['TWF_ACCEPTED_GAME_SOURCE_SHA']=OTHER
        with self.assertRaises(x.XmlStageError):x.check_host_environment(cfg(),e)
    def test_changed_source_sha_rejected_even_with_matching_env(self):
        with self.assertRaises(x.XmlStageError):x.check_host_environment(cfg(source=OTHER),env(source=OTHER))
    def test_malformed_reviewed_workflow_sha_rejected(self):
        with self.assertRaises(x.XmlStageError):cfg(workflow='bad').check()
    def test_missing_reviewed_workflow_sha_rejected(self):
        with self.assertRaises(x.XmlStageError):cfg(workflow='').check()
    def test_untrusted_pr_ref_rejected(self):
        e=env();e['GITHUB_REF']='refs/pull/145/merge'
        with self.assertRaises(x.XmlStageError):x.check_host_environment(cfg(),e)
    def test_foreign_repo_rejected(self):
        e=env();e['GITHUB_REPOSITORY']='other/private'
        with self.assertRaises(x.XmlStageError):x.check_host_environment(cfg(),e)
    def test_production_place_collision_rejected(self):
        with self.assertRaises(x.XmlStageError):replace(cfg(),production_place_id='3030').check()
