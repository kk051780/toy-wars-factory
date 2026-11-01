"""Adversarial static cross-PR compatibility tests, all fixtures are FORGEABLE."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import twf_roblox_task_post_once as sender
import twf_a14_post_cas_contract as bridge

LUA=(ROOT/'fixtures'/'twf_open_cloud_smoke.luau').read_bytes()
T=sender.Target('12345','67890','56')
FIXED=sender.prepare(T,LUA)
MAIN='e5deff4d5681bca4823a3da0f848e01bc089ae6e'
ZIP='2f662dad3e0fd81d71aaa52f34fcf1be56406cf6aecc5637b30f6de8bdac3b7b'
XML='1c9bdc3dc478fe72e51870e478aa15392c47875618b86262aa7dd605e4026b33'
REF='1'*40
NEW='2'*40
OWNER='4c8d111d-2456-4959-aa5b-219fc7d43546'

def context():
    plan={
      'status':'PRIVATE_OPEN_CLOUD_PLAN_NOT_EXECUTED','repository':bridge.REPO,
      'source_main_sha':MAIN,'artifact_id':13015999142,'producer_run_id':41137070161,
      'zip_sha256':ZIP,'xml_sha256':XML,'xml_bytes':54753,
      'script_sha256':sender.SMOKE_SHA256,
      'request':{'method':'POST','api_host':'https://apis.roblox.com',
                 'path':'/cloud/v2/'+T.create_path(),
                 'body_sha256':FIXED.body_sha256,'explicit_version_id':56,
                 'universe_id':12345,'place_id':67890,'timeout':'30s',
                 'content_type':'application/json',
                 'body_contains_exact_reviewed_script':True,
                 'credentials_embedded':False,'body_embedded_in_report':False}
    }
    intent={'repository':bridge.REPO,'source_main_sha':MAIN,'artifact_zip_sha256':ZIP,
       'rbxlx_sha256':XML,'luau_sha256':sender.SMOKE_SHA256,
       'universe_id':12345,'place_id':67890,'version_id':56,
       'intent_type':'HEADLESS_SERVER_SMOKE_V1'}
    f=bridge.digest_intent(intent)
    rec={'fingerprint':f,'resource':'12345/67890/56','source_main_sha':MAIN,
         'owner_id':OWNER,'epoch':306,'claim_ref':REF,
         'reserved_at':'2026-10-31T01:30:00+00:00',
         'phase':'POST_CONSUMED_NEVER_AUTO_RETRY'}
    proposal={'status':'CANDIDATE_ONLY_NO_WRITE','expected_sha':REF,
        'record':rec, 'post_authorized':False,
       'provider_attested':False, 'roblox_engine_verified':False,
       'main_merge_authorized':False, 'next_state':{
         'schema':1,'task_id':'6adbf0d6a7d881918ce181dff2468867','epoch':306,
         'holder':{'owner_id':OWNER,'epoch':306,'kind':'CONTROLLER','origin':'controller',
                   'task_id':None,'work_branch':'controller/roblox-cloud-example',
                   'base_main_sha':MAIN},
         'cloud_execution_intents_v1':[rec],
         'other_state':'PRESERVED'}}
    receipt={'status':'EXACT_PARENT_CAS_READBACK_STRUCTURAL_ONLY',
             'record_fingerprint':f,'source_ref':REF,'observed_ref':NEW,
             'post_authorized':False,'github_provider_authenticated':False,
             'roblox_engine_verified':False,'replay_authorized':False,
             'merge_authorized':False}
    return {'plan':plan,'intent':intent,'proposal':proposal,'readback':receipt,
            'fixed_request':FIXED,'target':T,'smoke_script':LUA}

def check(x): return bridge.verify_alignment(**x)

class IntegrationTests(unittest.TestCase):
    def hold(self,mutate,reason=None):
        x=context();mutate(x)
        with self.assertRaises(bridge.AlignmentHold) as cm: check(x)
        if reason is not None:self.assertEqual(str(cm.exception),reason)

    def test_01_exact_three_contracts_align_without_grant(self):
        out=check(context());self.assertEqual(out['status'],'UNTRUSTED_PR158_PR175_POST_CONTRACTS_ALIGN')
        self.assertEqual(out['intent_fingerprint'],bridge.digest_intent(context()['intent']))
        self.assertEqual(out['post_body_sha256'],FIXED.body_sha256)
        self.assertEqual(out['network_calls'],0)
        self.assertTrue(all(v is False for k,v in out.items() if k.startswith(('may_',)) or k.endswith(('authenticated','verified','authentic')) or k=='post_authorized'))

    def test_02_pin_genuine_pr175_script(self):
        self.assertEqual(hashlib.sha256(LUA).hexdigest(),sender.SMOKE_SHA256)
    def test_03_pr158_canonical_determinism(self):
        x=context()['intent']; a=bridge.digest_intent(x);x=dict(reversed(list(x.items())));
        self.assertEqual(bridge.digest_intent(x),a)
    def test_04_wrong_artifact_zip(self):
        self.hold(lambda x:x['intent'].__setitem__('artifact_zip_sha256','3'*64),'BUILD_OR_SCRIPT_INTENT_MISMATCH')
    def test_05_wrong_xml_digest(self):
        self.hold(lambda x:x['intent'].__setitem__('rbxlx_sha256','3'*64),'BUILD_OR_SCRIPT_INTENT_MISMATCH')
    def test_06_new_script_hash(self):
        self.hold(lambda x:x['intent'].__setitem__('luau_sha256','3'*64),'BUILD_OR_SCRIPT_INTENT_MISMATCH')
    def test_07_target_universe_in_intent(self):
        self.hold(lambda x:x['intent'].__setitem__('universe_id',222),'INTENT_TARGET_MISMATCH')
    def test_08_target_place_in_intent(self):
        self.hold(lambda x:x['intent'].__setitem__('place_id',222),'INTENT_TARGET_MISMATCH')
    def test_09_saved_version_in_intent(self):
        self.hold(lambda x:x['intent'].__setitem__('version_id',57),'INTENT_TARGET_MISMATCH')
    def test_10_preflight_body_hash(self):
        self.hold(lambda x:x['plan']['request'].__setitem__('body_sha256','f'*64),'POST_PLAN_REQUEST_MISMATCH')
    def test_11_preflight_api_host(self):
        self.hold(lambda x:x['plan']['request'].__setitem__('api_host','https://example.com'),'POST_PLAN_REQUEST_MISMATCH')
    def test_12_script_body_mutation(self):
        self.hold(lambda x:x.__setitem__('smoke_script',LUA+b'\n'),'BAD_LOCAL_POST_REQUEST')
    def test_13_modified_fixed_post_request(self):
        self.hold(lambda x:x.__setitem__('fixed_request',sender.FixedRequest('GET',FIXED.url,FIXED.body,FIXED.script_sha256,FIXED.body_sha256)),'MUTATED_POST_REQUEST')
    def test_14_forged_record_fingerprint(self):
        self.hold(lambda x:x['proposal']['record'].__setitem__('fingerprint','f'*64),'RESERVATION_RECORD_MISMATCH')
    def test_15_duplicate_record_not_present(self):
        self.hold(lambda x:x['proposal']['next_state'].__setitem__('cloud_execution_intents_v1',[]),'RESERVATION_LEDGER_MISMATCH')
    def test_16_claim_ref_changed(self):
        self.hold(lambda x:x['proposal']['record'].__setitem__('claim_ref','9'*40),'RESERVATION_RECORD_MISMATCH')
    def test_17_readback_wrong_fingerprint(self):
        self.hold(lambda x:x['readback'].__setitem__('record_fingerprint','9'*64),'READBACK_STRUCTURAL_PROOF_MISMATCH')
    def test_18_readback_wrong_source_ref(self):
        self.hold(lambda x:x['readback'].__setitem__('source_ref','9'*40),'READBACK_STRUCTURAL_PROOF_MISMATCH')
    def test_19_same_ref_not_advance(self):
        self.hold(lambda x:x['readback'].__setitem__('observed_ref',REF),'READBACK_STRUCTURAL_PROOF_MISMATCH')
    def test_20_injected_claim_grants_post_rejected(self):
        self.hold(lambda x:x['readback'].__setitem__('post_authorized',True),'READBACK_STRUCTURAL_PROOF_MISMATCH')
    def test_21_override_production_authority_rejected(self):
        self.hold(lambda x:x['readback'].__setitem__('provider_authenticated',True),'READBACK_STRUCTURAL_PROOF_MISMATCH')
    def test_22_wrong_ledger_phase(self):
        self.hold(lambda x:x['proposal']['record'].__setitem__('phase','POST_REPLAY_OK'),'RESERVATION_RECORD_MISMATCH')
    def test_23_wrong_main(self):
        self.hold(lambda x:x['plan'].__setitem__('source_main_sha','f'*40),'STALE_SOURCE_MAIN')
    def test_24_nonint_version(self):
        self.hold(lambda x:x['intent'].__setitem__('version_id','56'),'INVALID_INTENT_TARGET')
    def test_25_unreviewed_intent_shape(self):
        self.hold(lambda x:x['intent'].__setitem__('may_post',True),'INTENT_SCHEMA_MISMATCH')
    def test_26_no_implicit_credential_or_network_parameters(self):
        import inspect
        p=inspect.signature(bridge.verify_alignment)
        self.assertTrue(all(name not in p.parameters for name in ('api_key','opener','network','post','github_token')))
    def test_27_mutate_source_main_in_intent(self):
        self.hold(lambda x:x['intent'].__setitem__('source_main_sha','f'*40),'BUILD_OR_SCRIPT_INTENT_MISMATCH')
    def test_28_wrong_plan_version(self):
        self.hold(lambda x:x['plan']['request'].__setitem__('explicit_version_id',99),'POST_PLAN_REQUEST_MISMATCH')
    def test_29_false_readback_status(self):
        self.hold(lambda x:x['readback'].__setitem__('status','CANDIDATE_ONLY_NO_WRITE'),'READBACK_STRUCTURAL_PROOF_MISMATCH')
    def test_30_changed_source_plan_xml(self):
        self.hold(lambda x:x['plan'].__setitem__('xml_sha256','8'*64),'ARTIFACT_NOT_PR175_PINNED')
    def test_31_pr158_max_id_matches_2pow63(self):
        self.hold(lambda x:x['intent'].__setitem__('version_id',2**63),'INVALID_INTENT_TARGET')
    def test_32_foreign_holder_branch_rejected(self):
        self.hold(lambda x:x['proposal']['next_state']['holder'].__setitem__(
            'work_branch','controller/other'),'RESERVATION_LEDGER_MISMATCH')
    def test_33_foreign_holder_role_rejected(self):
        self.hold(lambda x:x['proposal']['next_state']['holder'].__setitem__(
            'kind','WORKER'),'RESERVATION_LEDGER_MISMATCH')
    def test_34_proposal_false_authority_required(self):
        self.hold(lambda x:x['proposal'].__setitem__('post_authorized',True),
                  'PROPOSAL_FALSE_AUTHORITY_REQUIRED')
    def test_35_missing_proposal_false_authority_required(self):
        self.hold(lambda x:x['proposal'].pop('provider_attested'),
                  'PROPOSAL_FALSE_AUTHORITY_REQUIRED')
    def test_36_plan_key_embedded_rejected(self):
        self.hold(lambda x:x['plan']['request'].__setitem__('credentials_embedded',True),
                  'POST_PLAN_REQUEST_MISMATCH')
    def test_37_proposal_original_ref_fingerprint_no_authority(self):
        x=context();out=check(x)
        self.assertEqual(out['intent_fingerprint'],x['readback']['record_fingerprint'])
        self.assertFalse(out['global_intent_authentic']);self.assertFalse(out['may_post'])
    def test_38_coordinated_forged_zip_still_rejected(self):
        x=context();x['plan']['zip_sha256']='a'*64
        x['intent']['artifact_zip_sha256']='a'*64
        with self.assertRaisesRegex(bridge.AlignmentHold,'ARTIFACT_NOT_PR175_PINNED'):
            check(x)
    def test_39_coordinated_forged_xml_still_rejected(self):
        x=context();x['plan']['xml_sha256']='a'*64
        x['intent']['rbxlx_sha256']='a'*64
        with self.assertRaisesRegex(bridge.AlignmentHold,'ARTIFACT_NOT_PR175_PINNED'):
            check(x)
    def test_40_wrong_producer_id_still_rejected(self):
        self.hold(lambda x:x['plan'].__setitem__('producer_run_id',123),
                  'ARTIFACT_NOT_PR175_PINNED')

if __name__ == '__main__': unittest.main()
