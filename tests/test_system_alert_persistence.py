"""Synthetic Git/host adversaries; real unattended persistence remains NOT_RUN."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'tests')]
from tools import system_alert_persistence as target
from test_system_service_observer import fixtures,Provider,IDS,NOW
from test_system_alert_ledger import fence,later
from test_system_incident_observer import set_holder
from test_system_runtime_alerts import rules


class Host:
    def __init__(self,second=False,*,failure=True):
        self.p,self.b,self.d,self.s=fixtures(second)
        self.actor={'role':'meta','task_id':self.p['roles']['meta'],'run_id':IDS['meta']}
        h=fence(self.p)['holder'];h['base_main_sha']=self.b['main_sha']
        set_holder(self.p,{'github':self.b},self.d,h)
        if failure:self.s[self.p['roles']['author']]['run_details']['last_run']['recorded_status']='no_update'
        self.provider=Provider(self.p,self.d,self.s);self.calls=[];self.on_get=None;self.on_write=None
        self.reads={};self.time=NOW
        self.writer={name:getattr(self,name) for name in target.WRITES}

    def get(self,url):
        path=url[len(self.provider.raw_get.prefix):];self.reads[path]=self.reads.get(path,0)+1
        if self.on_get:
            changed=self.on_get(path,self.reads[path])
            if changed is not None:return changed
        return self.provider.get(url)

    def put(self,path,row):self.d[path]=target.github.Response(200,json.dumps(row))

    def blob(self,content):
        raw=content.encode();sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        self.d['/git/blobs/'+sha]=target.github.Response(200,content)
        return sha

    def create_tree(self,**kw):
        self.calls.append(('create_tree',deepcopy(kw)))
        if self.on_write:
            r=self.on_write('create_tree',kw)
            if r is not None:return r
        base=json.loads(self.d['/git/trees/'+kw['base_tree_sha']+'?recursive=1'].text)['tree']
        entries={e['path']:e for e in base}
        for e in kw['tree_elements']:
            entries[e['path']]={'path':e['path'],'mode':e['mode'],'type':e['type'],'sha':self.blob(e['content'])}
        rows=list(entries.values());sha=hashlib.sha1(json.dumps(rows,sort_keys=True).encode()).hexdigest()
        self.put('/git/trees/'+sha+'?recursive=1',{'sha':sha,'truncated':False,'tree':rows})
        return target.github.Response(201,json.dumps({'sha':sha}))

    def create_commit(self,**kw):
        self.calls.append(('create_commit',deepcopy(kw)))
        if self.on_write:
            r=self.on_write('create_commit',kw)
            if r is not None:return r
        sha=hashlib.sha1(json.dumps(kw,sort_keys=True).encode()).hexdigest()
        self.put('/git/commits/'+sha,{'sha':sha,'tree':{'sha':kw['tree_sha']},'parents':[{'sha':kw['parent_sha']}]})
        return target.github.Response(201,json.dumps({'sha':sha}))

    def update_ref(self,**kw):
        self.calls.append(('update_ref',deepcopy(kw)))
        if self.on_write:
            r=self.on_write('update_ref',kw)
            if r is not None:return r
        path='/git/ref/heads/'+self.p['coordination_ref'];old=json.loads(self.d[path].text)
        if old['object']['sha']!=kw['expected_sha'] or kw['force'] is not False:
            return target.github.Response(409,'{}')
        old['object']['sha']=kw['sha'];self.put(path,old)
        return target.github.Response(200,'{"success":true}')

    def run(self,*,writer=True,projects=None,peek=None,clock=None):
        return target.persist(projects or [self.p],self.b,self.actor,rules(),self.get,
                              peek or self.provider.peek,clock or (lambda:self.time),
                              writer=self.writer if writer else None)

    def seed(self):
        prepared=self.run(writer=False)['prepared'];path=prepared['path'];sha=self.blob(prepared['content'])
        tree=json.loads(self.d['/git/trees/'+'e'*40+'?recursive=1'].text)
        tree['tree'].append({'path':path,'mode':'100644','type':'blob','sha':sha})
        self.put('/git/trees/'+'e'*40+'?recursive=1',tree)
        return prepared


class PersistenceTests(unittest.TestCase):
    def test_two_games_actual_observer_reducer_and_only_one_scoped_cas(self):
        one,two=Host(),Host(True)
        for h in (one,two):
            out=h.run(projects=[one.p,two.p]);self.assertTrue(out['persisted'])
            self.assertEqual([n for n,_ in h.calls],['create_tree','create_commit','update_ref'])
            self.assertEqual(h.calls[0][1]['tree_elements'][0]['path'],'ops/alerts/'+h.p['game_id']+'.json')
            self.assertEqual(h.calls[-1][1]['expected_sha'],h.b['coordinator_sha'])
            self.assertIs(h.calls[-1][1]['force'],False);self.assertEqual(out['delivery'],'NOT_ATTEMPTED')
            self.assertEqual(out['verification'],'NOT_VERIFIED');self.assertFalse(any(out['authority'].values()))
            self.assertFalse(out['a12_verified']);self.assertEqual(out['main_qa'],'MAIN_QA_NOT_CHECKED')

    def test_no_writer_prepares_double_checked_operation_without_writes(self):
        h=Host();out=h.run(writer=False)
        self.assertEqual(out['stage'],'PREPARED_ONLY');self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])
        self.assertEqual(out['prepared']['previous_blob_sha'],None)
        self.assertGreaterEqual(h.reads['/git/blobs/'+h.b['coordinator_blob_sha']],3)

    def test_healthy_no_fake_incident_or_objects(self):
        h=Host(failure=False);out=h.run();self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])
        self.assertEqual(out['reason'],'NO_INCIDENT_OBSERVED')

    def test_duplicate_observation_skips_rewrite_and_counter_increment(self):
        h=Host();h.seed();out=h.run();self.assertEqual(out['reason'],'DUPLICATE_OBSERVATION');self.assertEqual(h.calls,[])

    def test_distinct_later_observation_updates_one_record_once(self):
        h=Host();h.seed();h.time=later(10);out=h.run();self.assertTrue(out['persisted'])
        row=json.loads(h.d['/git/blobs/'+out['ledger_blob_sha']].text)
        self.assertEqual(len(row['frame']['alerts']),1);self.assertEqual(row['frame']['alerts'][0]['repeats'],2)

    def test_disappearance_never_claims_recovery_or_delivery(self):
        h=Host();h.seed();h.time=later(10)
        h.s[h.p['roles']['author']]['run_details']['last_run']['recorded_status']='completed'
        out=h.run();self.assertTrue(out['persisted'])
        ledger=json.loads(h.d['/git/blobs/'+out['ledger_blob_sha']].text)
        a=ledger['frame']['recovery_candidates'][0]
        self.assertEqual(a['status'],'UNVERIFIED_RECOVERY_CANDIDATE');self.assertIs(a['recovered'],False)
        self.assertEqual(out['recovery_verification'],'NOT_VERIFIED');self.assertEqual(out['delivery'],'NOT_ATTEMPTED')

    def test_read_403_and_404_never_write_or_fake_health(self):
        for status in (403,404):
            h=Host();h.on_get=lambda path,count:target.github.Response(status,'{}')
            out=h.run();self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])
            self.assertEqual(out['reason'],'OBSERVER_UNASSESSABLE')

    def test_cas_conflict_never_retry_force_or_confirm(self):
        h=Host();h.on_write=lambda name,kw:target.github.Response(409,'{}') if name=='update_ref' else None
        out=h.run();self.assertFalse(out['persisted']);self.assertTrue(out['cas_attempted'])
        self.assertEqual(len([n for n,_ in h.calls if n=='update_ref']),1)
        self.assertEqual(out['reason'],'WRITE_RECEIPT_REJECTED')

    def test_ref_movement_at_second_anchor_prevents_all_writes(self):
        h=Host()
        def drift(path,count):
            if path=='/git/ref/heads/'+h.p['coordination_ref'] and count>=4:
                return target.github.Response(200,json.dumps({'ref':'refs/heads/'+h.p['coordination_ref'],
                    'object':{'sha':'9'*40,'type':'commit'}}))
        h.on_get=drift;out=h.run();self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])

    def test_stale_epoch_wrong_run_and_foreign_actor_rejected(self):
        for change in ('epoch','run','task'):
            h=Host()
            if change=='epoch':h.b['coordinator_epoch']+=1
            elif change=='run':h.actor['run_id']=IDS['reviewer']
            else:h.actor['task_id']=h.p['roles']['author']
            self.assertFalse(h.run()['persisted']);self.assertEqual(h.calls,[])

    def test_active_foreign_holder_and_expiry_never_takeover(self):
        for change in ('foreign','expired'):
            h=Host();holder=fence(h.p)['holder'];holder['base_main_sha']=h.b['main_sha']
            if change=='foreign':holder.update(kind='REVIEWER',task_id=h.p['roles']['reviewer'],owner_id=IDS['reviewer'],origin='reviewer',work_branch='main')
            else:holder.update(acquired_at=later(-1800),expires_at=NOW)
            set_holder(h.p,{'github':h.b},h.d,holder)
            out=h.run();self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])

    def test_forged_immutable_prior_blob_rejected(self):
        h=Host();prepared=h.seed();sha=h.blob(prepared['content'])
        h.d['/git/blobs/'+sha]=target.github.Response(200,prepared['content'].replace('NOT_VERIFIED','VERIFIED'))
        self.assertFalse(h.run()['persisted']);self.assertEqual(h.calls,[])

    def test_forged_delivery_and_recovery_in_prior_are_rejected(self):
        for field,value in (('delivery','DELIVERED'),('recovery_verification','CONFIRMED'),('a12_verified',True)):
            h=Host();pr=h.seed();row=json.loads(pr['content']);row[field]=value;sha=h.blob(json.dumps(row))
            tree=json.loads(h.d['/git/trees/'+'e'*40+'?recursive=1'].text);tree['tree'][-1]['sha']=sha
            h.put('/git/trees/'+'e'*40+'?recursive=1',tree)
            self.assertFalse(h.run()['persisted']);self.assertEqual(h.calls,[])

    def test_invalid_writer_and_fake_provider_flag_rejected(self):
        h=Host();h.writer={'provider_verified':True};out=h.run();self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])
        h=Host();h.actor['provider_verified']=True;self.assertFalse(h.run()['persisted']);self.assertEqual(h.calls,[])

    def test_write_error_or_no_receipt_does_not_leak_or_retry(self):
        for response in (None,target.github.Response(403,'{"token":"NEVER_ECHO"}')):
            h=Host()
            def reject(name,kw):
                if name=='create_tree':
                    if response is None:raise RuntimeError('token=NEVER_ECHO')
                    return response
            h.on_write=reject;out=h.run();self.assertFalse(out['persisted']);self.assertEqual(len(h.calls),1)
            self.assertNotIn('NEVER_ECHO',json.dumps(out))

    def test_fake_success_receipt_is_not_persistence_without_readback(self):
        h=Host();h.on_write=lambda name,kw:target.github.Response(200,'{"success":true}') if name=='update_ref' else None
        out=h.run();self.assertFalse(out['persisted']);self.assertEqual(out['stage'],'READBACK')
        self.assertEqual(out['ref_outcome'],'UNCONFIRMED_POSSIBLE_WRITE')

    def test_commit_created_without_cas_is_not_persisted(self):
        h=Host();h.on_write=lambda name,kw:target.github.Response(201,'{"sha":"0000000000000000000000000000000000000000"}') if name=='create_commit' else None
        out=h.run();self.assertFalse(out['persisted']);self.assertFalse(out['cas_attempted'])

    def test_wrong_parent_or_injected_tree_never_cas(self):
        for mode in ('parent','tree'):
            h=Host()
            def tamper(path,count):
                if path.startswith('/git/commits/') and path not in ('/git/commits/'+'a'*40,'/git/commits/'+'b'*40):
                    row=json.loads(h.d[path].text)
                    if mode=='parent':row['parents']=[{'sha':'9'*40}]
                    else:
                        treepath='/git/trees/'+row['tree']['sha']+'?recursive=1'
                        tree=json.loads(h.d[treepath].text);tree['tree'].append({'path':'workflow.yml','mode':'100644','type':'blob','sha':'9'*40});h.put(treepath,tree)
                    return target.github.Response(200,json.dumps(row))
            h.on_get=tamper;out=h.run();self.assertFalse(out['persisted']);self.assertFalse(out['cas_attempted'])

    def test_actor_changes_after_observation_prevents_writes(self):
        h=Host();count=0
        def peek(task):
            nonlocal count
            if task==h.actor['task_id']:
                count+=1
                if count>=3:h.s[task]['run_details']['last_run']['id']=IDS['reviewer']
            return h.provider.peek(task)
        out=h.run(peek=peek);self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])

    def test_clock_reverse_and_budget_of_lease_rejected(self):
        h=Host();counter=0
        def clock():
            nonlocal counter
            counter+=1;return NOW if counter==1 else later(-1)
        self.assertFalse(h.run(clock=clock)['persisted']);self.assertEqual(h.calls,[])
        h=Host();holder=fence(h.p)['holder'];holder.update(base_main_sha=h.b['main_sha'],expires_at=later(29))
        set_holder(h.p,{'github':h.b},h.d,holder);self.assertFalse(h.run()['persisted']);self.assertEqual(h.calls,[])

    def test_foreign_repo_fork_and_reused_cross_game_roles_rejected(self):
        for change in ('repo','fork','roles'):
            h=Host();other=Host(True)
            if change=='repo':h.p['repository']='foreign/repository'
            elif change=='fork':h.put('',{'full_name':h.p['repository'],'fork':True})
            else:other.p['roles']=deepcopy(h.p['roles'])
            out=h.run(projects=[h.p,other.p]);self.assertFalse(out['persisted']);self.assertEqual(h.calls,[])

    def test_expiry_between_object_creation_and_cas_blocks_ref_update(self):
        h=Host()
        def expire(name,kw):
            if name=='create_commit':h.time=later(1801)
        h.on_write=expire;out=h.run();self.assertFalse(out['persisted']);self.assertFalse(out['cas_attempted'])

    def test_lost_cas_ack_never_claims_rollback_or_retries(self):
        h=Host();original=h.writer['update_ref']
        def lose(**kw):
            original(**kw);raise RuntimeError('receipt unavailable')
        h.writer['update_ref']=lose;out=h.run();self.assertFalse(out['persisted'])
        self.assertEqual(out['ref_outcome'],'UNCONFIRMED_POSSIBLE_WRITE')
        ref=json.loads(h.d['/git/ref/heads/'+h.p['coordination_ref']].text)
        self.assertNotEqual(ref['object']['sha'],h.b['coordinator_sha'])
        self.assertEqual(len([n for n,_ in h.calls if n=='update_ref']),1)


if __name__=='__main__':unittest.main()
