"""PR-less actual service-observer path; all fixtures SYNTHETIC_TEST_ONLY."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'tests')]
from tools import system_idle_health as target
from test_system_service_observer import fixtures,Provider,NOW,IDS
from test_system_github_evidence import mutate
from test_system_runtime_alerts import rules


class IdleHealthTests(unittest.TestCase):
    def run_fixture(self,f=None,*,now=NOW,previous=None,projects=None):
        p,b,d,s=f or fixtures();v=Provider(p,d,s)
        return target.observe(projects or [p],b,rules(),v.get,v.peek,lambda:now,previous),v

    def report(self):
        p,b,d,s=fixtures();v=Provider(p,d,s)
        return p,b,target.service.observe([p],b,v.get,v.peek,lambda:NOW)

    def kinds(self,r):return {a['identity']['kind'] for a in r['frame']['alerts']}

    def no_update(self):
        p,b,d,s=fixtures();s[p['roles']['author']]['run_details']['last_run']['recorded_status']='no_update'
        return p,b,d,s

    def test_no_pr_two_games_no_ci_or_authority_claim(self):
        one,two=fixtures(),fixtures(True)
        for f in (one,two):
            p,b,d,s=f
            # There is deliberately no PR/run/job API in this provider.
            for path in list(d):
                if path.startswith(('/pulls/','/actions/')):del d[path]
            out,v=self.run_fixture(f,projects=[one[0],two[0]])
            self.assertEqual(out['state'],'OBSERVED_HEALTHY')
            self.assertEqual(out['main_qa'],'MAIN_QA_NOT_CHECKED')
            self.assertEqual(out['frame']['ci'],[])
            self.assertEqual(len(v.peek_calls),6)
            self.assertFalse(any(out['authority'].values()))
            self.assertFalse(out['a12_verified'])
            self.assertFalse(any('/pulls/' in x or '/actions/' in x for x in v.raw_get.calls))

    def test_actual_accepted_observer_called_not_copied(self):
        with patch.object(target.service,'observe',wraps=target.service.observe) as call:self.run_fixture()
        self.assertEqual(call.call_count,1)

    def test_failed_and_no_update_ignore_green_previous_prose(self):
        for status in ('failed','no_update'):
            p,b,d,s=fixtures();s[p['roles']['author']]['run_details']['last_run']['recorded_status']=status
            s[p['roles']['author']]['run_details']['latest_result']['content_text']='HOST_WRITE_DENIED token=DO_NOT_ECHO SUCCESS'
            out,_=self.run_fixture((p,b,d,s))
            self.assertIn('OBSERVED_'+status.upper(),self.kinds(out))
            self.assertEqual(out['operation_cause'],'INDETERMINATE')
            self.assertNotIn('DO_NOT_ECHO',json.dumps(out))

    def test_previous_result_cannot_complete_active_run(self):
        out,_=self.run_fixture();row=next(x for x in out['frame']['services'] if x['role']=='meta')
        self.assertEqual(row['latest_result_binding'],'PREVIOUS_RUN')
        self.assertEqual(row['state'],'IN_PROGRESS_NOT_YET_STALE')

    def test_terminal_missing_current_result_not_success(self):
        p,b,d,s=fixtures();s[p['roles']['author']]['run_details']['latest_result']=None
        out,_=self.run_fixture((p,b,d,s));self.assertIn('STALE_OR_NO_RESULT',self.kinds(out))

    def test_timeout_distinct_from_in_window(self):
        p,b,r=self.report();limit=rules();limit['service_timeout_seconds']['meta']=600
        out=target.classify([p],b,r,limit,NOW);self.assertIn('STALE_OR_NO_RESULT',self.kinds(out))
        limit['service_timeout_seconds']['meta']=1200
        out=target.classify([p],b,r,limit,NOW);self.assertNotIn('STALE_OR_NO_RESULT',self.kinds(out))

    def test_disabled_and_attention_are_not_healthy(self):
        for state in ('disabled','attention'):
            p,b,d,s=fixtures()
            if state=='disabled':s[p['roles']['author']]['is_enabled']=False
            else:s[p['roles']['author']]['run_details']['latest_result']['requires_user_action']=True
            out,_=self.run_fixture((p,b,d,s));self.assertEqual(out['state'],'ATTENTION_REQUIRED')

    def holder(self,role='meta',expired=False):
        p,b,d,s=fixtures();state=json.loads(d['/git/blobs/'+b['coordinator_blob_sha']].text)
        state['holder']={'kind':target.service.ROLES[role],'owner_id':IDS[role],'task_id':p['roles'][role],'epoch':7,
                         'acquired_at':'2026-10-27T12:00:00Z' if expired else '2026-10-27T12:10:00Z',
                         'expires_at':'2026-10-27T12:20:00Z' if expired else '2026-10-27T12:40:00Z'}
        raw=json.dumps(state,sort_keys=True);sha=hashlib.sha1(b'blob '+str(len(raw.encode())).encode()+b'\0'+raw.encode()).hexdigest()
        d['/git/blobs/'+sha]=target.github.Response(200,raw);b['coordinator_blob_sha']=sha
        mutate(d,'/git/trees/'+'e'*40+'?recursive=1',lambda x:x['tree'][0].update(sha=sha))
        return p,b,d,s

    def test_active_lease_no_false_alarm_or_takeover(self):
        out,_=self.run_fixture(self.holder());self.assertEqual(out['frame']['lease']['state'],'ACTIVE_LEASE')
        self.assertEqual(self.kinds(out),set());self.assertFalse(out['authority']['takeover_allowed'])

    def test_terminal_owner_unreleased_is_attention(self):
        out,_=self.run_fixture(self.holder('author'));self.assertIn('STALE_OR_NO_RESULT',self.kinds(out))

    def test_expired_lease_never_recovered(self):
        out,_=self.run_fixture(self.holder(expired=True));self.assertIn('EXPIRED_LEASE_UNRELEASED',self.kinds(out))
        self.assertFalse(any(out['authority'].values()))

    def test_detector_403_404_and_unknown_exception_are_indeterminate(self):
        for status in (403,404):
            p,b,d,s=fixtures();d['']=target.github.Response(status,'token=NO_ECHO')
            out,_=self.run_fixture((p,b,d,s));self.assertEqual(out['state'],'INDETERMINATE');self.assertNotIn('NO_ECHO',json.dumps(out))
        p,b,d,s=fixtures()
        def fail(*args):raise RuntimeError('secret=NO_ECHO')
        out=target.observe([p],b,rules(),fail,fail,lambda:NOW)
        self.assertEqual(self.kinds(out),{'CONNECTOR_UNAVAILABLE'})

    def test_wrong_task_repo_epoch_and_duplicate_run_fail_closed(self):
        for change in (lambda p,b,d,s:s[p['roles']['author']].update(id='f'*32),
                       lambda p,b,d,s:mutate(d,'',lambda x:x.update(full_name='other/repo')),
                       lambda p,b,d,s:b.update(coordinator_epoch=9),
                       lambda p,b,d,s:s[p['roles']['reviewer']]['run_details']['last_run'].update(id=IDS['author'])):
            f=fixtures();change(*f);out,_=self.run_fixture(f);self.assertEqual(out['state'],'INDETERMINATE')

    def test_forged_pr_provider_and_false_authentication_rejected(self):
        for key in ('pr','provider_verified','host_receipt'):
            p,b,r=self.report();r[key]=True
            with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)
        p,b,r=self.report();r['verification']='LIVE_PROVIDER_VERIFIED'
        with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)

    def test_contradictory_status_and_trace_digest_rejected(self):
        for change in (lambda r:r['services']['meta'].update(observation_state='COMPLETED_WITH_CURRENT_RESULT'),
                       lambda r:r['peek_trace'][0].update(metadata_sha256='f'*64),lambda r:r.update(peek_trace=[]),
                       lambda r:r.update(get_trace=[])):
            p,b,r=self.report();change(r)
            with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)

    def test_future_and_stale_clock_rejected(self):
        for now in ('2026-10-27T12:29:59Z','2026-10-27T12:32:01Z'):
            p,b,r=self.report()
            with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),now)

    def test_cross_game_task_reuse_rejected(self):
        p,b,d,s=fixtures();q,_,_,_=fixtures(True);q['roles']['meta']=p['roles']['meta']
        with self.assertRaises(Exception):self.run_fixture((p,b,d,s),projects=[p,q])

    def test_dedup_and_unverified_recovery(self):
        first,_=self.run_fixture(self.no_update())
        second,_=self.run_fixture(self.no_update(),now='2026-10-27T12:30:01Z',previous=first)
        self.assertEqual(second['frame']['alerts'][0]['repeats'],2)
        third,_=self.run_fixture(now='2026-10-27T12:30:02Z',previous=second)
        candidate=third['frame']['recovery_candidates'][0]
        self.assertEqual(candidate['status'],'UNVERIFIED_RECOVERY_CANDIDATE');self.assertFalse(candidate['recovered'])

    def test_forged_duplicate_or_replayed_prior_rejected(self):
        first,_=self.run_fixture(self.no_update())
        for change in (lambda x:x.update(delivery='ALERT_DELIVERED'),lambda x:x.update(a12_verified=True),
                       lambda x:x['frame']['alerts'].append(deepcopy(x['frame']['alerts'][0])),
                       lambda x:x['authority'].update(write_allowed=True)):
            bad=deepcopy(first);change(bad)
            with self.assertRaises(target.EvidenceError):self.run_fixture(now='2026-10-27T12:30:01Z',previous=bad)
        with self.assertRaises(target.EvidenceError):self.run_fixture(self.no_update(),previous=first)

    def test_invalid_threshold_and_binding_not_authority(self):
        p,b,r=self.report();limit=rules();limit['service_timeout_seconds']['meta']=True
        with self.assertRaises(target.EvidenceError):target.classify([p],b,r,limit,NOW)
        b['pr_number']=9
        with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)

    def test_error_envelope_not_healthy_and_clock_backwards_indeterminate(self):
        p,b,d,s=fixtures();v=Provider(p,d,s)
        def peek(task):
            row=json.loads(v.peek(task).text);row['isError']=True
            return target.service.PeekResponse(True,json.dumps(row))
        out=target.observe([p],b,rules(),v.get,peek,lambda:NOW)
        self.assertEqual(out['state'],'INDETERMINATE')
        times=iter([NOW,'2026-10-27T12:29:59Z']+['2026-10-27T12:29:58Z']*100)
        out=target.observe([p],b,rules(),v.get,v.peek,lambda:next(times))
        self.assertEqual(out['state'],'INDETERMINATE')


if __name__=='__main__':unittest.main()
