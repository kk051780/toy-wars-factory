"""Synthetic chronology controls execute accepted idle.observe; no provider proof."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'tools'), str(ROOT/'tests')]
from tools import system_idle_health as target
from test_system_service_observer import fixtures, Provider, NOW, IDS, PREVIOUS
from test_system_github_evidence import mutate
from test_system_runtime_alerts import rules


def holder_fixture(role='meta', *, acquired='2026-10-27T12:09:00Z',
                   expires='2026-10-27T12:39:00Z', second=False, owner=None):
    p,b,d,s=fixtures(second)
    row=s[p['roles'][role]]
    row['run_details']['last_run'].update(recorded_status='in_progress',
        started_at='2026-10-27T12:10:00Z',completed_at=None)
    row['run_details']['latest_result']=None
    state=json.loads(d['/git/blobs/'+b['coordinator_blob_sha']].text)
    state['holder']={'kind':target.service.ROLES[role],'owner_id':owner or IDS[role],
        'task_id':p['roles'][role],'epoch':7,'acquired_at':acquired,'expires_at':expires}
    raw=json.dumps(state,sort_keys=True)
    sha=hashlib.sha1(b'blob '+str(len(raw.encode())).encode()+b'\0'+raw.encode()).hexdigest()
    d['/git/blobs/'+sha]=target.github.Response(200,raw)
    b['coordinator_blob_sha']=sha
    mutate(d,'/git/trees/'+'e'*40+'?recursive=1',lambda x:x['tree'][0].update(sha=sha))
    return p,b,d,s


class IdleClaimChronologyTests(unittest.TestCase):
    def observe(self,f,*,now=NOW,previous=None,change=None,projects=None):
        p,b,d,s=f;v=Provider(p,d,s,change)
        out=target.observe(projects or [p],b,rules(),v.get,v.peek,lambda:now,previous)
        return out,v
    def kinds(self,out): return {a['identity']['kind'] for a in out['frame']['alerts']}
    def assert_closed(self,out):
        self.assertEqual(out['state'],'INDETERMINATE')
        self.assertFalse(any(out['authority'].values()))
        self.assertEqual(out['verification'],'NOT_VERIFIED')
        self.assertFalse(out['a12_verified'])
        self.assertEqual(out['delivery'],'NOT_ATTEMPTED')
        self.assertEqual(out['operation_cause'],'INDETERMINATE')

    def test_meta_current_uuid_cannot_hide_claim_before_provider_start(self):
        out,v=self.observe(holder_fixture())
        self.assert_closed(out)
        self.assertEqual(out['frame']['lease']['state'],'ACTIVE_LEASE')
        self.assertEqual(len(v.peek_calls),6)
    def test_author_current_uuid_prestart_claim_is_not_healthy(self):
        out,_=self.observe(holder_fixture('author'))
        self.assert_closed(out)
    def test_reviewer_current_uuid_prestart_claim_is_not_healthy(self):
        out,_=self.observe(holder_fixture('reviewer'))
        self.assert_closed(out)
    def test_one_microsecond_prestart_is_not_rounded_away(self):
        out,_=self.observe(holder_fixture(acquired='2026-10-27T12:09:59.999999Z',
                                        expires='2026-10-27T12:39:59.999999Z'))
        self.assert_closed(out)
    def test_equal_and_after_start_remain_healthy_with_no_new_grants(self):
        for acquired,expires in [('2026-10-27T12:10:00Z','2026-10-27T12:40:00Z'),
                                 ('2026-10-27T12:10:01Z','2026-10-27T12:40:01Z')]:
            out,_=self.observe(holder_fixture(acquired=acquired,expires=expires))
            self.assertEqual(out['state'],'OBSERVED_HEALTHY')
            self.assertEqual(self.kinds(out),set())
            self.assertFalse(any(out['authority'].values()))
    def test_offset_equivalent_instants_do_not_raise_false_alarm(self):
        out,_=self.observe(holder_fixture(acquired='2026-10-27T21:10:00+09:00',
                                        expires='2026-10-27T21:40:00+09:00'))
        self.assertEqual(out['state'],'OBSERVED_HEALTHY')
    def test_expired_prestart_keeps_expiry_evidence_and_no_takeover(self):
        out,_=self.observe(holder_fixture(acquired='2026-10-27T12:00:00Z',expires='2026-10-27T12:20:00Z'))
        self.assert_closed(out)
        self.assertIn('EXPIRED_LEASE_UNRELEASED',self.kinds(out))
        self.assertEqual(out['frame']['lease']['state'],'EXPIRED_LEASE_UNRELEASED')
    def test_unmatched_owner_not_falsely_bound_to_newest_different_run(self):
        out,_=self.observe(holder_fixture(owner='eeeeeeee-ffff-4aaa-8bbb-cccccccccccc'))
        self.assertNotIn('CONNECTOR_UNAVAILABLE',self.kinds(out))
        self.assertFalse(any(out['authority'].values()))
        self.assertEqual(out['frame']['lease']['state'],'ACTIVE_LEASE')
    def test_start_mutation_during_second_peek_is_still_indeterminate(self):
        def change(row):
            if row['run_details']['last_run']['id']==IDS['meta']:
                row['run_details']['last_run']['started_at']='2026-10-27T12:11:00Z'
        out,_=self.observe(holder_fixture(acquired='2026-10-27T12:10:00Z',expires='2026-10-27T12:40:00Z'),change=change)
        self.assert_closed(out)
    def test_old_result_and_caller_provider_flags_cannot_repair_bad_order(self):
        f=holder_fixture();p,b,d,s=f
        s[p['roles']['meta']]['run_details']['latest_result']={
            'run_id':PREVIOUS,'created_at':'2026-10-27T11:45:00Z',
            'completed_at':'2026-10-27T11:46:00Z','scheduled_for':'2026-10-27T11:30:00Z',
            'is_failure_message':False,'requires_user_action':False,
            'content_text':'provider_verified token=DO_NOT_ECHO'}
        s[p['roles']['meta']].update(provider_verified=True,original_start_verified=True)
        out,_=self.observe(f);self.assert_closed(out)
        self.assertNotIn('DO_NOT_ECHO',json.dumps(out))
    def test_two_games_keep_separate_subjects_and_no_grants(self):
        one,two=holder_fixture(),holder_fixture(second=True)
        for f in (one,two):
            out,_=self.observe(f,projects=[one[0],two[0]])
            self.assert_closed(out)
            self.assertTrue(all(a['identity']['game_id']==f[0]['game_id'] for a in out['frame']['alerts']))
    def test_dedup_retains_one_chronology_alert_and_independent_recovery_unproven(self):
        f=holder_fixture();first,_=self.observe(f)
        self.assert_closed(first)
        second,_=self.observe(f,now='2026-10-27T12:30:01Z',previous=first)
        unknown=[a for a in second['frame']['alerts'] if a['identity']['kind']=='CONNECTOR_UNAVAILABLE']
        self.assertEqual(len(unknown),1);self.assertEqual(unknown[0]['repeats'],2)
        third,_=self.observe(holder_fixture(acquired='2026-10-27T12:10:00Z',expires='2026-10-27T12:40:00Z'),
            now='2026-10-27T12:30:02Z',previous=second)
        self.assertTrue(third['frame']['recovery_candidates'])
        self.assertTrue(all(not a['recovered'] for a in third['frame']['recovery_candidates']))
        self.assertFalse(third['a12_verified'])
    def test_pure_classifier_and_observe_consistently_close_same_current_holder(self):
        p,b,d,s=holder_fixture();v=Provider(p,d,s)
        report=target.service.observe([p],b,v.get,v.peek,lambda:NOW)
        self.assertEqual(report['coordinator']['holder_service_binding'],'MATCHED_CURRENT_SERVICE_RUN')
        # Identity equality remains an observation, never chronology authorization.
        out=target.classify([p],b,report,rules(),NOW)
        self.assert_closed(out)
        self.assertTrue(any('/git/' in e for a in out['frame']['alerts'] for e in a['evidence']))

if __name__=='__main__': unittest.main()
