"""Synthetic ledger adversaries; never live persistence/delivery/recovery proof."""
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'tools'), str(ROOT/'tests')]
from tools import system_alert_ledger as target
from tools import system_idle_health as idle
from test_system_service_observer import fixtures, Provider, NOW, IDS
from test_system_runtime_alerts import rules


def later(seconds):
    return (datetime.fromisoformat(NOW.replace('Z','+00:00'))+timedelta(seconds=seconds)).isoformat()


def frame(second=False, *, failure=True, at=NOW, outage=None):
    p,b,d,s=fixtures(second)
    if failure:s[p['roles']['author']]['run_details']['last_run']['recorded_status']='no_update'
    provider=Provider(p,d,s)
    def get(url):return idle.github.Response(outage,'{}') if outage else provider.get(url)
    return p,idle.observe([p],b,rules(),get,provider.peek,lambda:at)['frame']


def fence(p,previous=None,*,at=NOW,role='meta'):
    return {'repository':p['repository'],'coordination_ref':p['coordination_ref'],'expected_ref_sha':'e'*40,
            'observed_at':at,'epoch':7,'actor_role':role,'actor_task_id':p['roles'][role],
            'actor_run_id':IDS[role], 'previous_digest':None if previous is None else target.digest(previous),
            'holder':{'kind':idle.service.ROLES[role],'owner_id':IDS[role],'task_id':p['roles'][role],
                      'epoch':7,'acquired_at':later(-30),'expires_at':later(1700),
                      'base_main_sha':'a'*40,'work_branch':'main' if role=='reviewer' else 'auto/meta-'+IDS[role],
                      'origin':role}}


class LedgerTests(unittest.TestCase):
    def first(self):
        p,f=frame();out=target.reduce([p],None,f,fence(p),NOW)
        return p,f,out['ledger']

    def bad(self,p,old,f,lease):
        with self.assertRaises(target.EvidenceError):target.reduce([p],old,f,lease,f['observed_at'])

    def test_two_games_real_accepted_path_single_canonical_incident(self):
        one,two=frame(),frame(True)
        for p,f in (one,two):
            out=target.reduce([one[0],two[0]],None,f,fence(p),NOW)
            alert=out['ledger']['frame']['alerts'][0]
            raw=json.dumps(alert['identity'],sort_keys=True,separators=(',',':')).encode()
            self.assertEqual(alert['id'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(alert['identity']['subject']['task_id'],p['roles']['author'])
            self.assertEqual(alert['repeats'],1)
            self.assertEqual(alert['first_seen'],alert['last_seen'])
            self.assertEqual(out['proposal']['expected_sha'],'e'*40)
            self.assertIs(out['proposal']['force'],False)

    def test_no_alert_no_ledger_or_write_proposal(self):
        p,f=frame(failure=False);out=target.reduce([p],None,f,fence(p),NOW)
        self.assertIsNone(out['ledger']);self.assertIsNone(out['proposal']);self.assertFalse(out['changed'])

    def test_duplicate_replay_is_idempotent_and_no_rewrite(self):
        p,f,old=self.first()
        out=target.reduce([p],old,f,fence(p,old,at=later(1)),later(1))
        self.assertFalse(out['changed']);self.assertIsNone(out['proposal']);self.assertEqual(out['ledger'],old)
        self.assertEqual(out['ledger']['frame']['alerts'][0]['repeats'],1)

    def test_distinct_observation_updates_one_record_once(self):
        p,_,old=self.first();_,f=frame(at=later(10))
        with patch.object(target.runtime,'reconcile',wraps=target.runtime.reconcile) as call:
            out=target.reduce([p],old,f,fence(p,old,at=later(10)),later(10))
        call.assert_called_once();new=out['ledger'];a=new['frame']['alerts']
        self.assertEqual(len(a),1);self.assertEqual(a[0]['repeats'],2)
        self.assertEqual(a[0]['first_seen'],old['frame']['alerts'][0]['first_seen'])
        self.assertEqual(a[0]['last_seen'],f['observed_at'])
        again=target.reduce([p],new,f,fence(p,new,at=later(11)),later(11))
        self.assertFalse(again['changed']);self.assertEqual(again['ledger'],new)

    def test_disappearance_is_only_unverified_candidate(self):
        p,_,old=self.first();_,f=frame(at=later(10),failure=False)
        out=target.reduce([p],old,f,fence(p,old,at=later(10)),later(10));c=out['ledger']['frame']['recovery_candidates']
        self.assertEqual(c[0]['status'],'UNVERIFIED_RECOVERY_CANDIDATE');self.assertIs(c[0]['recovered'],False)
        self.assertEqual(out['delivery'],'NOT_ATTEMPTED');self.assertEqual(out['recovery_verification'],'NOT_VERIFIED')

    def test_403_404_observation_unassessable_never_confirmed_recovery(self):
        p,_,old=self.first()
        for status in (403,404):
            _,f=frame(at=later(10),outage=status)
            out=target.reduce([p],old,f,fence(p,old,at=later(10)),later(10))
            self.assertEqual(out['observation'],'UNASSESSABLE')
            self.assertEqual(out['ledger']['frame']['recovery_candidates'][0]['status'],'RECOVERY_UNASSESSABLE')
            self.assertFalse(out['ledger']['frame']['recovery_candidates'][0]['recovered'])

    def test_observation_same_time_conflict_and_backward_clock(self):
        p,_,old=self.first();_,f=frame(failure=False)
        self.bad(p,old,f,fence(p,old))
        _,f=frame(at=later(-1));self.bad(p,old,f,fence(p,old,at=later(-1)))

    def test_foreign_repository_project_roles_and_task_reuse(self):
        p,f,old=self.first();other,_=frame(True)
        for key in ('repository','game_id','roles'):
            changed=deepcopy(f);changed[key]=deepcopy(other[key]);self.bad(p,None,changed,fence(p))
        other['roles']=deepcopy(p['roles'])
        with self.assertRaises(target.EvidenceError):target.reduce([p,other],None,f,fence(p),NOW)
        lease=fence(p);lease['actor_task_id']='f'*32;self.bad(p,None,f,lease)

    def test_forged_previous_data_rejected_by_independent_digest(self):
        p,f,old=self.first();lease=fence(p,old)
        for key,value in (('repeats',9),('first_seen',later(-20)),('evidence',[])):
            bad=deepcopy(old);bad['frame']['alerts'][0][key]=value;self.bad(p,bad,f,lease)

    def test_forged_authenticated_delivery_or_recovery_rejected_even_with_new_hash(self):
        p,f,old=self.first()
        for key,value in (('verification','LIVE_PROVIDER_VERIFIED'),('delivery','DELIVERED'),
                          ('recovery_verification','CONFIRMED'),('a12_verified',True),('schema',True)):
            bad=deepcopy(old);bad[key]=value;self.bad(p,bad,f,fence(p,bad))
        bad=deepcopy(old);bad['frame']['alerts'][0]['recovered']=True;self.bad(p,bad,f,fence(p,bad))

    def test_forged_prior_counter_and_created_time(self):
        p,f,old=self.first()
        bad=deepcopy(old);bad['frame']['alerts'][0]['repeats']=2;self.bad(p,bad,f,fence(p,bad))
        bad=deepcopy(old);bad['created_at']=later(1);self.bad(p,bad,f,fence(p,bad))

    def test_active_foreign_owner_and_expired_lease_not_takeover(self):
        p,f,_=self.first()
        changes=[('owner_id',IDS['author']),('task_id',p['roles']['reviewer']),('kind','WORKER'),
                 ('epoch',8),('expires_at',NOW),('acquired_at',later(1)),('expires_at',later(2000))]
        for k,v in changes:
            lease=fence(p);lease['holder'][k]=v;self.bad(p,None,f,lease)
        lease=fence(p);lease['holder']=None;self.bad(p,None,f,lease)

    def test_stale_fence_bad_ref_and_missing_prior_anchor(self):
        p,f,old=self.first()
        for k,v in (('observed_at',later(-121)),('expected_ref_sha','main'),('epoch',True),
                    ('coordination_ref','another'),('repository','foreign/repo'),('previous_digest','0'*64)):
            lease=fence(p);lease[k]=v;self.bad(p,None,f,lease)
        self.bad(p,old,f,fence(p))

    def test_worker_cannot_be_ledger_writer_reviewer_can_propose(self):
        p,f,_=self.first();out=target.reduce([p],None,f,fence(p,role='reviewer'),NOW)
        self.assertTrue(out['changed']);self.assertFalse(any(out['authority'].values()))
        self.bad(p,None,f,fence(p,role='author'))

    def test_all_forged_authority_flags_and_provider_label_rejected(self):
        p,f,old=self.first()
        for k in target.runtime.DENIED:
            bad=deepcopy(f);bad['authority'][k]=True;self.bad(p,None,bad,fence(p))
            bad=deepcopy(old);bad['authority'][k]=True;self.bad(p,bad,f,fence(p,bad))
        lease=fence(p);lease['provider_verified']=True;self.bad(p,None,f,lease)

    def test_missing_duplicate_and_rebound_alerts_rejected(self):
        p,f,_=self.first()
        bad=deepcopy(f);bad['alerts']=[];self.bad(p,None,bad,fence(p))
        bad=deepcopy(f);bad['alerts']*=2;self.bad(p,None,bad,fence(p))
        bad=deepcopy(f);a=bad['alerts'][0];a['identity']['subject']['run_id']=IDS['meta']
        a['id']=target.digest(a['identity']);self.bad(p,None,bad,fence(p))

    def test_previous_result_never_current_success_or_empty_observation(self):
        p,f=frame(failure=False)
        bad=deepcopy(f);bad['services'][0]['latest_result_binding']='PREVIOUS_RUN';self.bad(p,None,bad,fence(p))
        bad=deepcopy(f);bad['services']=[];self.bad(p,None,bad,fence(p))

    def test_invalid_types_secrets_not_echoed(self):
        p,f,_=self.first()
        for bad in (None,[],{'token':'DO_NOT_ECHO'},dict(f,unknown='DO_NOT_ECHO')):
            with self.assertRaises(target.EvidenceError) as e:target.reduce([p],None,bad,fence(p),NOW)
            self.assertNotIn('DO_NOT_ECHO',str(e.exception))

    def test_inputs_immutable_and_json_roundtrip_exact(self):
        p,f,old=self.first();_,new=frame(at=later(10));lease=fence(p,old,at=later(10))
        args=([p],old,new,lease,later(10));saved=deepcopy(args)
        out=target.reduce(*args);self.assertEqual(args,saved);self.assertEqual(json.loads(json.dumps(out)),out)
        self.assertEqual(out['verification'],'NOT_VERIFIED');self.assertFalse(out['a12_verified'])

    def test_reconciled_input_and_stale_fresh_observation_rejected(self):
        p,f,old=self.first();_,fresh=frame(at=later(10))
        reconciled=target.runtime.reconcile(f,fresh)
        self.bad(p,old,reconciled,fence(p,old,at=later(10)))
        with self.assertRaises(target.EvidenceError):target.reduce([p],None,f,fence(p,at=later(121)),later(121))


if __name__=='__main__':unittest.main()
