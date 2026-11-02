"""Minimal notification preparation/receipt matching, NEVER a send API.

Reuse an accepted ledger and persistence readback. A GitHub commit is not a
notification receipt. The current host offers no authenticated incident-bound
delivery receipt; even matching supplied JSON stays UNVERIFIED. Hashes and a
source label only check consistency. A future trusted host must independently
read immutable anchors/receiver authorization; this module supplies neither.
No callbacks, network, credentials, scheduler, spend, automatic resend or recovery.
"""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from tools import system_alert_ledger as ledger
from tools import system_alert_persistence as persistence

runtime,need,moment,EvidenceError=ledger.runtime,ledger.need,ledger.moment,ledger.EvidenceError
DIGEST=runtime.github.re.compile(r'[0-9a-f]{64}\Z')
CONTEXT={'game_id','repository','actor_role','actor_task_id','actor_run_id','epoch',
         'coordinator_sha','recorded_at','previous_notice_digest'}
NOTICE={'schema','mode','verification','notification_id','attempt_id','game_id','repository','incident_id',
        'kind','role','actor_role','actor_task_id','actor_run_id','epoch','coordinator_sha','ledger_blob_sha',
        'receiver_digest','created_at','expires_at','body','evidence_url','delivery_status',
        'send_allowed','recovery_verification','a12_verified','authority'}
READBACK={'schema','mode','verification','state','stage','persisted','cas_attempted','operation_receipts',
          'delivery','recovery_verification','a12_verified','main_qa','authority','commit_sha',
          'ledger_blob_sha','incident_count','ref_outcome'}
RECEIPT={'schema','source','game_id','repository','notification_id','attempt_id','incident_id',
         'receiver_digest','actor_task_id','actor_run_id','epoch','coordinator_sha','ledger_blob_sha',
         'sent_at','recorded_at','delivery_status','http_status'}


def _project(projects,game):
    games=runtime.service.scheduler._validated_games(deepcopy(projects))
    chosen=[p for p in games if p['game_id']==game]
    need(len(chosen)==1,'UNKNOWN_NOTIFICATION_PROJECT')
    return chosen[0]


def _hash(value):
    need(type(value) is str and DIGEST.fullmatch(value),'INVALID_NOTIFICATION_DIGEST')
    return value


def _id(n):return ledger.digest({k:n[k] for k in ('game_id','repository','incident_id','receiver_digest')})


def _attempt(n):
    return ledger.digest({k:n[k] for k in ('notification_id','actor_task_id','actor_run_id','epoch','coordinator_sha','ledger_blob_sha')})


def _body(n):return 'A12 '+n['kind']+' / '+n['role']+'; independent review required.'


def _url(n):
    return 'https://github.com/'+n['repository']+'/blob/'+n['coordinator_sha']+'/ops/alerts/'+n['game_id']+'.json'


def _notice(project,n):
    need(type(n) is dict and set(n)==NOTICE and type(n['schema']) is int and n['schema']==1 and
         n['mode']=='PREPARED_NOTIFICATION_ONLY' and n['verification']=='NOT_VERIFIED' and
         n['delivery_status']=='UNVERIFIED' and n['send_allowed'] is False and
         n['recovery_verification']=='NOT_VERIFIED' and n['a12_verified'] is False and
         all(n[k]==project[k] for k in ('game_id','repository')),'INVALID_PREPARED_NOTIFICATION')
    runtime._denied(n['authority'])
    for key in ('notification_id','attempt_id','incident_id','receiver_digest'):_hash(n[key])
    need(n['actor_role'] in ('meta','reviewer') and n['actor_task_id']==project['roles'][n['actor_role']] and
         n['kind'] in runtime.KINDS and n['role'] in set(project['roles'])|{'system'} and
         runtime.github.integer(n['epoch'],0),'INVALID_NOTIFICATION_BINDING')
    runtime.service.run_id(n['actor_run_id'])
    for key in ('coordinator_sha','ledger_blob_sha'):runtime.github.sha(n[key])
    need(n['notification_id']==_id(n) and n['attempt_id']==_attempt(n) and n['body']==_body(n) and
         n['evidence_url']==_url(n) and
         (moment(n['expires_at'])-moment(n['created_at'])).total_seconds()==120,'FORGED_NOTIFICATION')


def _output(notice,reason,*,duplicate=False,matched=False):
    return {'schema':1,'state':'PREPARED_NOTIFICATION_ONLY','verification':'NOT_VERIFIED',
            'notice':deepcopy(notice),'reason':reason,'duplicate_suppressed':duplicate,
            'receipt_binding_matched':matched,'receipt_origin':'NOT_AUTHENTICATED',
            'delivery_status':'UNVERIFIED','send_allowed':False,'resend_allowed':False,
            'a12_verified':False,'authority':deepcopy(runtime.DENIED)}


def prepare(projects,document,readback,context,receiver,incident_id,observed_at,previous=None):
    """Return a minimal intent only for one open, readback-bound incident.

    previous_notice_digest must come from an independently retrieved immutable
    prior record. Caller control of both record/digest cannot prove its origin.
    An existing incident+receiver intent suppresses new attempts even after TTL;
    expiration/lost ACK never becomes permission to retry.
    """
    try:
        return _prepare(projects,deepcopy(document),deepcopy(readback),deepcopy(context),
                        deepcopy(receiver),incident_id,moment(observed_at),deepcopy(previous))
    except EvidenceError:raise
    except Exception:raise EvidenceError('INVALID_NOTIFICATION_INPUT') from None


def _prepare(projects,doc,r,c,receiver,incident,now,previous):
    need(type(c) is dict and set(c)==CONTEXT,'INVALID_NOTIFICATION_CONTEXT')
    p=_project(projects,c['game_id'])
    need(c['repository']==p['repository'] and c['actor_role'] in ('meta','reviewer') and
         c['actor_task_id']==p['roles'][c['actor_role']] and runtime.github.integer(c['epoch'],0),
         'FOREIGN_NOTIFICATION_ACTOR')
    runtime.service.run_id(c['actor_run_id']);runtime.github.sha(c['coordinator_sha'])
    need(type(receiver) is dict and set(receiver)=={'game_id','repository','receiver_digest'} and
         all(receiver[k]==p[k] for k in ('game_id','repository')),'FOREIGN_NOTIFICATION_RECEIVER')
    _hash(receiver['receiver_digest']);_hash(incident)
    ledger._prior(p,doc,ledger.digest(doc),now)
    need(type(r) is dict and set(r)==READBACK and type(r['schema']) is int and r['schema']==1 and
         r['mode']=='HOST_CAPABILITY_LEDGER_BRIDGE' and r['verification']=='NOT_VERIFIED' and
         r['state']=='PERSISTED_READBACK' and r['stage']=='READBACK' and r['persisted'] is True and
         r['cas_attempted'] is True and r['delivery']=='NOT_ATTEMPTED' and r['recovery_verification']=='NOT_VERIFIED' and
         r['a12_verified'] is False and r['main_qa']=='MAIN_QA_NOT_CHECKED' and
         r['ref_outcome']=='OBSERVED_COMMIT_AND_BLOB','PERSISTENCE_NOT_READBACK_CONFIRMED')
    runtime._denied(r['authority'])
    need(r['operation_receipts']==[{'operation':k,'status':s} for k,s in
         (('create_tree',201),('create_commit',201),('update_ref',200))], 'INVALID_PERSISTENCE_RECEIPTS')
    raw=(json.dumps(doc,sort_keys=True,separators=(',',':'))+'\n').encode()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    need(r['commit_sha']==c['coordinator_sha'] and r['ledger_blob_sha']==blob and
         type(r['incident_count']) is int and r['incident_count']==len(doc['frame']['alerts']), 'UNBOUND_PERSISTENCE_ANCHOR')
    at=moment(doc['frame']['observed_at']);recorded=moment(c['recorded_at'])
    need(at<=recorded<=now and (now-at).total_seconds()<=120,'STALE_NOTIFICATION_SOURCE')
    lease=doc['frame']['lease']
    need(type(lease) is dict and lease['state']=='ACTIVE_LEASE' and type(lease['epoch']) is int and
         lease['epoch']==c['epoch'] and lease['owner_run_id']==c['actor_run_id'] and any(
         row['role']==c['actor_role'] and row['task_id']==c['actor_task_id'] and row['run_id']==c['actor_run_id'] and
         row['state']=='IN_PROGRESS_NOT_YET_STALE' for row in doc['frame']['services']), 'UNBOUND_NOTIFICATION_RUN')
    alerts=[x for x in doc['frame']['alerts'] if x['id']==incident and x['status']=='OPEN']
    need(len(alerts)==1,'NO_CURRENT_OPEN_INCIDENT')
    a=alerts[0]
    n={'schema':1,'mode':'PREPARED_NOTIFICATION_ONLY','verification':'NOT_VERIFIED',
       'game_id':p['game_id'],'repository':p['repository'],'incident_id':incident,'kind':a['identity']['kind'],
       'role':a['identity']['subject'].get('role','system'),'actor_role':c['actor_role'],
       'actor_task_id':c['actor_task_id'],'actor_run_id':c['actor_run_id'],'epoch':c['epoch'],
       'coordinator_sha':c['coordinator_sha'],'ledger_blob_sha':blob,'receiver_digest':receiver['receiver_digest'],
       'created_at':now.isoformat(),'expires_at':(now+timedelta(seconds=120)).isoformat(),
       'delivery_status':'UNVERIFIED','send_allowed':False,'recovery_verification':'NOT_VERIFIED',
       'a12_verified':False,'authority':deepcopy(runtime.DENIED)}
    n['notification_id']=_id(n);n['attempt_id']=_attempt(n);n['body']=_body(n);n['evidence_url']=_url(n)
    _notice(p,n)
    if previous is not None:
        need(type(c['previous_notice_digest']) is str and ledger.digest(previous)==_hash(c['previous_notice_digest']),
             'PREVIOUS_NOTIFICATION_ANCHOR_MISMATCH')
        _notice(p,previous)
        need(previous['notification_id']==n['notification_id'] and moment(previous['created_at'])<=now,
             'FOREIGN_PREVIOUS_NOTIFICATION')
        return _output(previous,'DUPLICATE_NO_NEW_ATTEMPT',duplicate=True)
    need(c['previous_notice_digest'] is None,'MISSING_PREVIOUS_NOTIFICATION')
    return _output(n,'HOST_DELIVERY_CAPABILITY_NOT_CONNECTED')


def assess(projects,notice,receipt,observed_at,expected_notice_digest):
    """Match supplied receipt; even a matched delivered label is NOT authenticated."""
    try:
        now=moment(observed_at);p=_project(projects,notice['game_id']);_notice(p,notice)
        need(ledger.digest(notice)==_hash(expected_notice_digest),'NOTICE_ANCHOR_MISMATCH')
        need(moment(notice['created_at'])<=now,'BACKWARD_NOTIFICATION_CLOCK')
        if receipt is None:return _output(notice,'HOST_RECEIPT_NOT_AVAILABLE')
        need(type(receipt) is dict and set(receipt)==RECEIPT and type(receipt['schema']) is int and
             receipt['schema']==1 and receipt['source']=='HOST_DELIVERY_RECEIPT','INVALID_HOST_RECEIPT')
        for k in ('game_id','repository','notification_id','attempt_id','incident_id','receiver_digest',
                  'actor_task_id','actor_run_id','coordinator_sha','ledger_blob_sha'):
            need(receipt[k]==notice[k],'FOREIGN_OR_REPLAYED_RECEIPT')
        need(type(receipt['epoch']) is int and receipt['epoch']==notice['epoch'],'FOREIGN_OR_REPLAYED_RECEIPT')
        sent,at=moment(receipt['sent_at']),moment(receipt['recorded_at'])
        need(moment(notice['created_at'])<=sent<=at<=now<=moment(notice['expires_at']) and
             (now-at).total_seconds()<=120,'STALE_OR_FUTURE_RECEIPT')
        need(receipt['delivery_status'] in ('unknown','accepted','delivered','failed') and
             (receipt['http_status'] is None or type(receipt['http_status']) is int),'INVALID_HOST_RECEIPT')
        need(receipt['delivery_status']!='failed' and receipt['http_status'] in (None,200,202),'DELIVERY_NOT_CONFIRMED')
        if receipt['delivery_status']=='unknown':return _output(notice,'DELIVERY_STATUS_UNKNOWN')
        need(receipt['http_status'] in (200,202),'RECEIPT_STATUS_UNAVAILABLE')
        return _output(notice,'MATCHED_RECEIPT_NOT_AUTHENTICATED',matched=True)
    except EvidenceError:raise
    except Exception:raise EvidenceError('INVALID_HOST_RECEIPT') from None
