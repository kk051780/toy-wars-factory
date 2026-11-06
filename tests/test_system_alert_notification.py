"""Notification boundary adversaries; no live send/delivery evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'tests')]
from tools import system_alert_notification as target
from test_system_alert_persistence import Host
from test_system_alert_ledger import later
from test_system_service_observer import NOW,IDS


def fixtures(second=False,seconds=0):
    host=Host(second);host.time=later(seconds);r=host.run()
    assert r['persisted'] is True
    doc=json.loads(host.d['/git/blobs/'+r['ledger_blob_sha']].text)
    context={'game_id':host.p['game_id'],'repository':host.p['repository'],'actor_role':'meta',
             'actor_task_id':host.p['roles']['meta'],'actor_run_id':IDS['meta'],'epoch':host.b['coordinator_epoch'],
             'coordinator_sha':r['commit_sha'],'recorded_at':host.time,'previous_notice_digest':None}
    receiver={'game_id':host.p['game_id'],'repository':host.p['repository'],'receiver_digest':'f'*64}
    incident=doc['frame']['alerts'][0]['id']
    return host.p,doc,r,context,receiver,incident


def prepare(f,at=NOW,previous=None,projects=None):
    p,d,r,c,dest,i=f
    return target.prepare(projects or [p],d,r,c,dest,i,at,previous)


def receipt(n,status='delivered',http=200):
    fields=('game_id','repository','notification_id','attempt_id','incident_id','receiver_digest',
            'actor_task_id','actor_run_id','epoch','coordinator_sha','ledger_blob_sha')
    return {**{k:n[k] for k in fields},'schema':1,'source':'HOST_DELIVERY_RECEIPT','sent_at':n['created_at'],
            'recorded_at':n['created_at'],'delivery_status':status,'http_status':http}


class NotificationTests(unittest.TestCase):
    def first(self):
        f=fixtures();return f,prepare(f)['notice']

    def assess(self,f,n,r,at=NOW,anchor=None):
        return target.assess([f[0]],n,r,at,anchor or target.ledger.digest(n))

    def test_two_games_reuse_actual_accepted_persistence_and_ledger(self):
        one,two=fixtures(),fixtures(True)
        for f in (one,two):
            out=prepare(f,projects=[one[0],two[0]]);n=out['notice']
            self.assertEqual(n['notification_id'],target._id(n));self.assertEqual(n['attempt_id'],target._attempt(n))
            self.assertEqual(n['game_id'],f[0]['game_id']);self.assertIn(f[3]['coordinator_sha'],n['evidence_url'])
            self.assertEqual(out['state'],'PREPARED_NOTIFICATION_ONLY');self.assertEqual(out['delivery_status'],'UNVERIFIED')
            self.assertFalse(out['send_allowed']);self.assertFalse(out['resend_allowed']);self.assertFalse(any(out['authority'].values()))

    def test_body_minimizes_identifiers_and_private_prose(self):
        _,n=self.first()
        self.assertLess(len(n['body']),120)
        self.assertNotIn(n['receiver_digest'],n['body']);self.assertNotIn(n['actor_run_id'],n['body'])
        self.assertNotIn('NEVER_EMIT',json.dumps(n));self.assertNotIn('content_text',json.dumps(n))

    def test_not_persisted_or_lost_cas_receipt_cannot_prepare(self):
        for key,value in (('state','NOT_PERSISTED'),('persisted',False),('cas_attempted',False),
                          ('stage','CREATE_COMMIT'),('ref_outcome','UNCONFIRMED_POSSIBLE_WRITE')):
            f=fixtures();f[2][key]=value
            with self.assertRaises(target.EvidenceError):prepare(f)

    def test_wrong_commit_blob_counter_or_receipts_rejected(self):
        for key,value in (('commit_sha','1'*40),('ledger_blob_sha','1'*40),('incident_count',2),('operation_receipts',[])):
            f=fixtures();f[2][key]=value
            with self.assertRaises(target.EvidenceError):prepare(f)

    def test_foreign_actor_epoch_and_run_rejected(self):
        for key,value in (('epoch',8),('epoch',True),('actor_task_id','9'*32),('actor_run_id',IDS['author']),
                          ('repository','foreign/repo'),('actor_role','author')):
            f=fixtures();f[3][key]=value
            with self.assertRaises(target.EvidenceError):prepare(f)

    def test_foreign_or_raw_receiver_is_not_authorization(self):
        for change in ('repo','game','raw','extra'):
            f=fixtures()
            if change=='repo':f[4]['repository']='foreign/repo'
            elif change=='game':f[4]['game_id']='foreign'
            elif change=='raw':f[4]['receiver_digest']='person@example.test'
            else:f[4]['provider_verified']=True
            with self.assertRaises(target.EvidenceError):prepare(f)

    def test_missing_receipt_lost_ack_never_becomes_delivered(self):
        f,n=self.first();out=self.assess(f,n,None)
        self.assertEqual(out['delivery_status'],'UNVERIFIED');self.assertFalse(out['receipt_binding_matched'])
        self.assertFalse(out['resend_allowed']);self.assertEqual(out['reason'],'HOST_RECEIPT_NOT_AVAILABLE')

    def test_matching_delivered_label_still_not_authenticated(self):
        f,n=self.first();out=self.assess(f,n,receipt(n))
        self.assertTrue(out['receipt_binding_matched']);self.assertEqual(out['delivery_status'],'UNVERIFIED')
        self.assertEqual(out['receipt_origin'],'NOT_AUTHENTICATED');self.assertFalse(out['a12_verified'])

    def test_transport_accepted_is_not_recipient_delivery(self):
        f,n=self.first();out=self.assess(f,n,receipt(n,'accepted',202))
        self.assertEqual(out['delivery_status'],'UNVERIFIED');self.assertFalse(out['send_allowed'])

    def test_delivery_status_unknown_never_upgraded(self):
        f,n=self.first();out=self.assess(f,n,receipt(n,'unknown',None))
        self.assertEqual(out['reason'],'DELIVERY_STATUS_UNKNOWN');self.assertFalse(out['receipt_binding_matched'])

    def test_403_429_and_transport_permission_failure_fail_closed(self):
        f,n=self.first()
        for code in (403,404,429,500):
            with self.assertRaises(target.EvidenceError):self.assess(f,n,receipt(n,'failed',code))
        with self.assertRaises(target.EvidenceError):self.assess(f,n,receipt(n,'delivered',403))

    def test_different_incident_run_receiver_epoch_and_attempt_rejected(self):
        f,n=self.first()
        for key,value in (('incident_id','1'*64),('notification_id','1'*64),('attempt_id','1'*64),
                          ('receiver_digest','1'*64),('actor_run_id',IDS['author']),('actor_task_id','1'*32),
                          ('epoch',8),('repository','foreign/repo'),('game_id','other'),
                          ('coordinator_sha','1'*40),('ledger_blob_sha','1'*40)):
            r=receipt(n);r[key]=value
            with self.assertRaises(target.EvidenceError):self.assess(f,n,r)

    def test_future_backwards_and_stale_receipt_rejected(self):
        f,n=self.first()
        for key,value in (('sent_at',later(-1)),('recorded_at',later(-1)),('recorded_at',later(1))):
            r=receipt(n);r[key]=value
            with self.assertRaises(target.EvidenceError):self.assess(f,n,r)
        with self.assertRaises(target.EvidenceError):self.assess(f,n,receipt(n),later(121))
        with self.assertRaises(target.EvidenceError):self.assess(f,n,None,later(-1))

    def test_stale_source_and_context_time_rejected(self):
        for at in (later(-1),later(121)):
            with self.assertRaises(target.EvidenceError):prepare(fixtures(),at)
        f=fixtures();f[3]['recorded_at']=later(1)
        with self.assertRaises(target.EvidenceError):prepare(f)

    def test_duplicate_prepare_returns_original_attempt_no_resend(self):
        f,n=self.first();f[3]['previous_notice_digest']=target.ledger.digest(n)
        out=prepare(f,later(1),n)
        self.assertTrue(out['duplicate_suppressed']);self.assertEqual(out['notice'],n);self.assertFalse(out['send_allowed'])

    def test_expired_or_lost_ack_notice_does_not_authorize_new_attempt(self):
        _,n=self.first();f=fixtures(seconds=130);f[3]['previous_notice_digest']=target.ledger.digest(n)
        out=prepare(f,later(130),n)
        self.assertTrue(out['duplicate_suppressed']);self.assertEqual(out['notice']['attempt_id'],n['attempt_id'])
        self.assertFalse(out['resend_allowed'])

    def test_previous_anchor_tamper_missing_and_foreign_notice_rejected(self):
        f,n=self.first();f[3]['previous_notice_digest']=target.ledger.digest(n)
        bad=deepcopy(n);bad['body']='changed'
        with self.assertRaises(target.EvidenceError):prepare(f,NOW,bad)
        with self.assertRaises(target.EvidenceError):prepare(f)
        other=fixtures(True);other_notice=prepare(other)['notice'];f[3]['previous_notice_digest']=target.ledger.digest(other_notice)
        with self.assertRaises(target.EvidenceError):prepare(f,NOW,other_notice)

    def test_notice_anchor_cannot_be_replaced_by_github_save(self):
        f,n=self.first()
        with self.assertRaises(target.EvidenceError):self.assess(f,n,receipt(n),anchor='0'*64)
        with self.assertRaises(target.EvidenceError):self.assess(f,n,{'source':'GITHUB_COMMIT','delivery_status':'delivered'})

    def test_forged_provider_permissions_and_delivery_flags_rejected(self):
        f,n=self.first()
        for key in n['authority']:
            bad=deepcopy(n);bad['authority'][key]=True
            with self.assertRaises(target.EvidenceError):self.assess(f,bad,receipt(n))
        r=receipt(n);r['provider_verified']=True
        with self.assertRaises(target.EvidenceError):self.assess(f,n,r)
        bad=deepcopy(n);bad['send_allowed']=True
        with self.assertRaises(target.EvidenceError):self.assess(f,bad,receipt(n))

    def test_recovery_candidate_is_not_a_new_open_notification(self):
        h=Host();h.seed();h.time=later(10);h.s[h.p['roles']['author']]['run_details']['last_run']['recorded_status']='completed'
        r=h.run();doc=json.loads(h.d['/git/blobs/'+r['ledger_blob_sha']].text)
        f=list(fixtures());f[0]=h.p;f[1]=doc;f[2]=r;f[3]['coordinator_sha']=r['commit_sha'];f[3]['recorded_at']=later(10)
        f[5]=doc['frame']['recovery_candidates'][0]['id']
        with self.assertRaises(target.EvidenceError):prepare(f,later(10))

    def test_cross_game_role_reuse_rejected(self):
        f=fixtures();other=fixtures(True);other[0]['roles']=deepcopy(f[0]['roles'])
        with self.assertRaises(target.EvidenceError):prepare(f,projects=[f[0],other[0]])

    def test_bool_or_incomplete_receipt_and_raw_error_do_not_echo(self):
        f,n=self.first()
        for bad in ([],{'token':'NEVER_ECHO'},RuntimeError('NEVER_ECHO'),dict(receipt(n),schema=True),
                    dict(receipt(n),epoch=True),dict(receipt(n),delivery_status='delivered',http_status=None)):
            with self.assertRaises(target.EvidenceError) as e:self.assess(f,n,bad)
            self.assertNotIn('NEVER_ECHO',str(e.exception))

    def test_repeat_receipt_assessment_is_idempotent_not_double_send(self):
        f,n=self.first();one=self.assess(f,n,receipt(n));two=self.assess(f,n,receipt(n))
        self.assertEqual(one,two);self.assertFalse(one['send_allowed']);self.assertFalse(one['resend_allowed'])

    def test_inputs_immutable_and_output_json_roundtrip(self):
        f=fixtures();old=deepcopy(f);out=prepare(f)
        self.assertEqual(f,old);self.assertEqual(json.loads(json.dumps(out)),out)
        n=out['notice'];r=receipt(n);saved=deepcopy((n,r));self.assess(f,n,r)
        self.assertEqual((n,r),saved)


if __name__=='__main__':unittest.main()
