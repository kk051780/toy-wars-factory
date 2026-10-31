"""Pure untrusted C-history reservation CAS proposal, NOT an execution capability.

Every returned plan is advice, never a live ref mutation or authenticated lease.
A future trusted host must bind actual source read, lock, clock, full active PR
head set, main tree and follow the one-parent expected-SHA coordinator CAS.
"""
from __future__ import annotations
import copy
from collections import Counter
from datetime import datetime, timezone
import re

SHA = re.compile(r'[0-9a-f]{40}\Z')
CID = re.compile(r'C[0-9]{5}\Z')
TASK_ID = re.compile(r'[0-9a-f]{32}\Z')
UUID = re.compile(r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z')
WORK = re.compile(r'[A-Za-z0-9_-]{8,100}\Z')
BRANCH = re.compile(r'(?:auto/twf-game-repair-[0-9a-f-]+|auto/twf-system-review-[0-9a-f-]+|controller/[A-Za-z0-9_/-]+)\Z')
MAX_CLAIMS = 10000

class InvalidState(ValueError): pass

def fail(code): raise InvalidState(code)
def stamp(v):
    if type(v) is not str: fail('INVALID_TIME')
    try:
        d=datetime.fromisoformat(v.replace('Z','+00:00'))
        if d.tzinfo is None: fail('INVALID_TIME')
        return d.astimezone(timezone.utc)
    except (ValueError, OverflowError): fail('INVALID_TIME')

def _id(k):
    return type(k) is str and bool(CID.fullmatch(k)) and k!='C00000'

def advise(coordinator, *, expected_ref, owner_id, work_branch, work_id,
           occupied_ids, main_sha, amount, now):
    """Strict deterministic reducer. It assumes nothing about provider origin.

    Does NOT grant permission even when all fields are mutually consistent.
    """
    base={'schema':1,'authority':'UNTRUSTED_ADVISORY','may_claim':False,
          'may_write':False,'may_merge':False,'may_create_pr':False,
          'cas_performed':False,'provider_attested':False,'may_retry':False}
    def decision(status,**kw):return dict(base,status=status,**kw)
    if type(coordinator) is not dict or type(coordinator.get('schema')) is not int or coordinator.get('schema')!=1 or type(coordinator.get('epoch')) is not int or coordinator['epoch']<0: return decision('BLOCK_BAD_COORD')
    if type(expected_ref) is not str or not SHA.fullmatch(expected_ref) or type(main_sha) is not str or not SHA.fullmatch(main_sha):return decision('BLOCK_BAD_SHA')
    if type(owner_id) is not str or not UUID.fullmatch(owner_id) or type(work_branch) is not str or not BRANCH.fullmatch(work_branch) or type(work_id) is not str or not WORK.fullmatch(work_id):return decision('BLOCK_BAD_WORK')
    if type(amount) is not int or not 1<=amount<=4:return decision('BLOCK_BAD_AMOUNT')
    try: t=stamp(now)
    except InvalidState: return decision('BLOCK_TIME')
    holder=coordinator.get('holder')
    if type(holder) is not dict or holder.get('kind') not in ('WORKER','META','CONTROLLER'):return decision('BLOCK_NO_AUTHOR_LEASE')
    if (holder.get('owner_id')!=owner_id or holder.get('work_branch')!=work_branch or
        type(holder.get('epoch')) is not int or holder['epoch']!=coordinator['epoch'] or
        holder.get('base_main_sha')!=main_sha): return decision('BLOCK_OWNER_OR_MAIN_CHANGED')
    try: acquired,expires=stamp(holder.get('acquired_at')),stamp(holder.get('expires_at'))
    except InvalidState:return decision('BLOCK_TIME')
    if not acquired<=t<expires:return decision('BLOCK_EXPIRED_OR_TIME_TRAVEL')
    if holder.get('kind') in ('WORKER','META'):
        registered=coordinator.get('authorized_tasks')
        if (type(registered) is not dict or type(registered.get(holder['kind'])) is not str
            or not TASK_ID.fullmatch(registered[holder['kind']])
            or holder.get('task_id')!=registered[holder['kind']]):
            return decision('BLOCK_UNREGISTERED_AUTHOR')
    if holder.get('kind')=='CONTROLLER' and not work_branch.startswith('controller/'):
        return decision('BLOCK_WRONG_ROLE_BRANCH')
    if holder.get('kind')=='WORKER' and not work_branch.startswith('auto/twf-game-repair-'):
        return decision('BLOCK_WRONG_ROLE_BRANCH')
    if holder.get('kind')=='META' and not work_branch.startswith('auto/twf-system-review-'):
        return decision('BLOCK_WRONG_ROLE_BRANCH')
    if type(occupied_ids) is not list or len(occupied_ids)>MAX_CLAIMS or any(not _id(x) for x in occupied_ids):return decision('BLOCK_OCCUPIED_SET')
    observed_collisions=sorted(k for k,v in Counter(occupied_ids).items() if v>1)
    ledger=coordinator.get('history_id_reservations')
    if ledger is None:return decision('WAIT_VERIFIED_BOOTSTRAP')
    if type(ledger) is not dict or set(ledger)!={'schema','high_watermark','entries'} or type(ledger['schema']) is not int or ledger['schema']!=1 or type(ledger['high_watermark']) is not int or not 1<=ledger['high_watermark']<=99999 or type(ledger['entries']) is not list or len(ledger['entries'])>MAX_CLAIMS:return decision('BLOCK_LEDGER_SCHEMA')
    existing=set(); owned=[]
    for rec in ledger['entries']:
        if (type(rec) is not dict or set(rec)!={'id','owner_id','epoch','work_branch','work_id','main_sha'}
            or not _id(rec['id']) or type(rec['owner_id']) is not str or not UUID.fullmatch(rec['owner_id'])
            or type(rec['epoch']) is not int or rec['epoch']<1
            or type(rec['work_id']) is not str or not WORK.fullmatch(rec['work_id'])
            or type(rec['work_branch']) is not str or not BRANCH.fullmatch(rec['work_branch'])
            or type(rec['main_sha']) is not str or not SHA.fullmatch(rec['main_sha'])):
            return decision('BLOCK_LEDGER_SCHEMA')
        if rec['epoch']>coordinator['epoch']:
            return decision('BLOCK_FUTURE_RESERVATION_EPOCH')
        if rec['id'] in existing:return decision('BLOCK_DUPLICATE_LEDGER_ID')
        existing.add(rec['id'])
        if rec['work_branch']==work_branch and rec['work_id']==work_id:owned.append(rec['id'])
        if rec['work_id']==work_id and rec['work_branch']!=work_branch:return decision('BLOCK_CROSS_BRANCH_WORK_ID')
    high=max([ledger['high_watermark']]+[int(v[1:]) for v in existing])
    if existing and max(int(v[1:]) for v in existing)>ledger['high_watermark']:return decision('BLOCK_LEDGER_WATERMARK')
    if set(occupied_ids)&existing:
        # Legal after already-authorized publication, but cannot prove which; require review.
        return decision('WAIT_RECONCILE_EXISTING_IDS',conflicts=sorted(set(occupied_ids)&existing))
    if owned:
        claims=[r for r in ledger['entries'] if r['work_branch']==work_branch and r['work_id']==work_id]
        origins={(r['owner_id'],r['epoch'],r['main_sha']) for r in claims}
        if len(origins)>1:
            return decision('BLOCK_MIXED_RESERVATION_ORIGINS')
        if origins!={(owner_id,coordinator['epoch'],main_sha)}:
            return decision('WAIT_AUTHENTICATED_RESERVATION_REBIND',reserved_ids=sorted(owned))
        if len(owned)!=amount:return decision('BLOCK_REPLAY_AMOUNT_DRIFT',reserved_ids=sorted(owned))
        return decision('JOIN_RESERVED_NO_REISSUE',reserved_ids=sorted(owned),expected_ref=expected_ref,legacy_collision_ids=observed_collisions)
    universe_hi=max([high]+[int(v[1:]) for v in occupied_ids])
    if universe_hi+amount>99999:return decision('BLOCK_EXHAUSTED')
    ids=[f'C{v:05d}' for v in range(universe_hi+1,universe_hi+amount+1)]
    proposed=copy.deepcopy(coordinator)
    records=[{'id':x,'owner_id':owner_id,'epoch':coordinator['epoch'],'work_branch':work_branch,'work_id':work_id,'main_sha':main_sha} for x in ids]
    proposed['history_id_reservations']['entries'].extend(records)
    proposed['history_id_reservations']['high_watermark']=universe_hi+amount
    return decision('PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED',suggested_ids=ids,expected_ref=expected_ref,proposed_state=proposed,legacy_collision_ids=observed_collisions,legacy_collisions_unresolved=bool(observed_collisions),trust_requirements=['complete authenticated source','single-parent GitHub coordinator CAS','exact ref postwrite readback','fresh owner+epoch clock check','independent protected review'])
