from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from manual_controller_run_origin_gate import *

MAIN = 'a'*40
CLAIM = 'b'*40
OWNER = '5f8c2be1-5a5a-4e11-aa0e-cb4714315abb'
BRANCH = 'controller/protected-system-' + OWNER
RUN_ID = 44112233
JOB_ID = 145670001


def fixture():
    origin = {
        'repository': REPO, 'repository_id': str(REPO_ID),
        'workflow_ref': WORKFLOW_REF, 'workflow_sha': MAIN,
        'source_main_sha': MAIN, 'job_id': 'witness',
        'run_id': RUN_ID, 'run_attempt': 1,
        'claim_sha': CLAIM, 'source_branch': BRANCH, 'epoch': 412,
        'provider_authenticated': False, 'job_log_attested': False,
        'may_review_or_merge': False, 'may_write_or_publish': False,
    }
    candidate = {
        'status':'CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY',
        'claim_sha':CLAIM, 'source_branch':BRANCH, 'main_sha':MAIN, 'epoch':412,
        'provider_witness_id':'MUST_BIND_TO_AUTHENTICATED_WORKFLOW_RUN_AND_JOB',
        'provider_authenticated':False, 'independent_review_authorized':False,
        'merge_authorized':False, 'roblox_post_authorized':False,
        'reported_actions_origin_untrusted':origin,
    }
    run = {
        'repository':{'id':REPO_ID,'full_name':REPO},'id':RUN_ID,
        'run_attempt':1,'event':'workflow_dispatch',
        'path':WORKFLOW, 'head_sha':MAIN,'head_branch':'main',
        'status':'completed','conclusion':'success',
        'actor':{'login':ACTOR},'triggering_actor':{'login':ACTOR},
    }
    job_page = {'total_count':1,'jobs':[{
        'id':JOB_ID,'run_id':RUN_ID,'run_attempt':1,
        'name':'witness','head_sha':MAIN,'status':'completed',
        'conclusion':'success','steps':[
            {'name':'Set up job','conclusion':'success','status':'completed'},
            {'name':TEST_STEP,'conclusion':'success','status':'completed'},
            {'name':'Preserve non-authorizing outcome classification','conclusion':'success','status':'completed'},
            {'name':'Complete job','conclusion':'success','status':'completed'},
        ]} ]}
    return candidate,run,job_page


SENTINEL = object()

def invoke(candidate=SENTINEL,run=SENTINEL,page=SENTINEL,**opts):
    c,r,p=fixture()
    return verify_original_run_job_metadata(
        c if candidate is SENTINEL else candidate,
        accepted_main_sha=opts.get('accepted_main_sha',MAIN),
        expected_run_id=opts.get('expected_run_id',RUN_ID),
        expected_job_id=opts.get('expected_job_id',JOB_ID),
        original_run=r if run is SENTINEL else run,
        original_job_page=p if page is SENTINEL else page)


class OriginalRunTests(unittest.TestCase):
    def test_positive_non_authorizing(self):
        x=invoke()
        self.assertEqual(x['status'],'ORIGINAL_RUN_JOB_METADATA_CONSISTENT_CANDIDATE_ONLY')
        self.assertTrue(x['metadata_fields_consistent'])
        for name in ('trusted_provider_transport_authenticated','witness_log_line_authenticated',
                     'claim_before_source_push_proven','independent_review_authorized',
                     'merge_authorized','source_write_authorized','roblox_publish_authorized'):
            self.assertIs(x[name],False)

    def test_wrong_event_rejected(self):
        c,r,p=fixture();r['event']='pull_request'
        with self.assertRaises(OriginHold):invoke(c,r,p)

    def test_wrong_workflow_rejected(self):
        c,r,p=fixture();r['path']='.github/workflows/bootstrap-quality.yml'
        with self.assertRaises(OriginHold):invoke(c,r,p)

    def test_wrong_repo_id_or_full_name(self):
        for key,value in [('id',432),('id',True),('full_name','foreign/repo')]:
            c,r,p=fixture();r['repository'][key]=value
            with self.subTest(key=key),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_wrong_main_sha(self):
        c,r,p=fixture();r['head_sha']='f'*40
        with self.assertRaises(OriginHold):invoke(c,r,p)

    def test_wrong_actor_and_triggering_actor(self):
        for key in ('actor','triggering_actor'):
            c,r,p=fixture();r[key]['login']='other'
            with self.subTest(key=key),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_wrong_attempt_or_replayed_run_id(self):
        for field,value in [('run_attempt',2),('run_attempt',True),('id',RUN_ID+1)]:
            c,r,p=fixture();r[field]=value
            with self.subTest(field=field),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_non_successful_run_rejected(self):
        for field,val in [('status','in_progress'),('conclusion','failure'),('conclusion','cancelled')]:
            c,r,p=fixture();r[field]=val
            with self.subTest(field=field),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_foreign_run_label_rejected(self):
        c,r,p=fixture();c['reported_actions_origin_untrusted']['run_id']=RUN_ID+1
        with self.assertRaises(OriginHold):invoke(c,r,p)

    def test_candidate_invented_approval_rejected(self):
        for key in ('provider_authenticated','merge_authorized','independent_review_authorized','roblox_post_authorized'):
            c,r,p=fixture();c[key]=True
            with self.subTest(key=key),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_origin_report_invented_approval_rejected(self):
        for key in ('provider_authenticated','job_log_attested','may_review_or_merge','may_write_or_publish'):
            c,r,p=fixture();c['reported_actions_origin_untrusted'][key]=True
            with self.subTest(key=key),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_unverified_branch_and_claim_rejected(self):
        for key,value in [('source_branch','controller/unscoped'),('claim_sha','bad'),('epoch',True)]:
            c,r,p=fixture();c[key]=value
            with self.subTest(key=key),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_forged_provider_witness_id_rejected(self):
        c,r,p=fixture();c['provider_witness_id']='VERIFIED_SIGNATURE'
        with self.assertRaises(OriginHold):invoke(c,r,p)

    def test_wrong_job_run_id_or_attempt(self):
        for key,value in [('run_id',RUN_ID+1),('run_attempt',2),('run_attempt',True)]:
            c,r,p=fixture();p['jobs'][0][key]=value
            with self.subTest(key=key),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_wrong_job_identity(self):
        for key,value in [('id',JOB_ID+1),('name','offline'),('head_sha','f'*40)]:
            c,r,p=fixture();p['jobs'][0][key]=value
            with self.subTest(key=key),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_job_page_extra_or_missing(self):
        for op in ('extra','none','wrongcount'):
            c,r,p=fixture()
            if op=='extra':p['jobs'].append(deepcopy(p['jobs'][0]));p['total_count']=2
            if op=='none':p['jobs']=[];p['total_count']=0
            if op=='wrongcount':p['total_count']=True
            with self.subTest(op=op),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_failed_or_skipped_witness_step(self):
        for status,conclusion in [('completed','failure'),('completed','skipped'),('in_progress','success')]:
            c,r,p=fixture();p['jobs'][0]['steps'][1].update(status=status,conclusion=conclusion)
            with self.subTest(status=status,conclusion=conclusion),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_witness_step_missing_or_duplicated(self):
        for op in ('absent','dup'):
            c,r,p=fixture()
            if op=='absent':p['jobs'][0]['steps'][1]['name']='not witness'
            if op=='dup':p['jobs'][0]['steps'].append(deepcopy(p['jobs'][0]['steps'][1]))
            with self.subTest(op=op),self.assertRaises(OriginHold):invoke(c,r,p)

    def test_non_witness_failed_step_rejected(self):
        c,r,p=fixture();p['jobs'][0]['steps'][0]['conclusion']='failure'
        with self.assertRaises(OriginHold):invoke(c,r,p)

    def test_source_main_mismatch_from_independent_sha(self):
        with self.assertRaises(OriginHold):invoke(accepted_main_sha='f'*40)

    def test_bool_external_ids_rejected(self):
        for opts in ({'expected_run_id':True},{'expected_job_id':True}):
            with self.subTest(opts=opts),self.assertRaises(OriginHold):invoke(**opts)

    def test_report_origin_source_branch_mismatch(self):
        c,r,p=fixture();c['reported_actions_origin_untrusted']['source_branch']='controller/protected-system-'+str(__import__('uuid').uuid4())
        with self.assertRaises(OriginHold):invoke(c,r,p)

    def test_run_job_page_malformed_types(self):
        for replacement in (None,[],{},'success',True):
            c,r,p=fixture()
            with self.subTest(v=replacement),self.assertRaises(OriginHold):invoke(c,replacement,p)
            with self.subTest(j=replacement),self.assertRaises(OriginHold):invoke(c,r,replacement)

if __name__=='__main__': unittest.main()
