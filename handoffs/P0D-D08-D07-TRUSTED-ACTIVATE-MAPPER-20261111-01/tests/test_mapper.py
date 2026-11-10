import copy
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from oracle import Mapper

ROOT=pathlib.Path(__file__).resolve().parents[1]
class MapperTests(unittest.TestCase):
    def setUp(self):
        self.r = dict(matchId='rnd1',stage='S1',epoch=9,now=30,deadline=60,active=True)
        self.e = dict(matchId='rnd1',stage='S1',epoch=9,kind='BOSS',subtype='GOROGAN',phase='ACTIVATE',validUntil=44)
        self.calls=[];self.aborts=[]
        def start(a):
            self.calls.append(a)
            self.assertTrue(self.m.is_canonical(a))
            self.assertFalse(self.m.is_canonical(dict(a)))
            return True,'STARTED'
        self.start=start
        self.m=Mapper(lambda:self.r,self.start,lambda rid:self.aborts.append(rid) or True,enabled=True,approved=True)

    def test_happy(self):
        self.assertEqual(self.m.handle(self.e),(True,'DELIVERED_ONCE'))
        self.assertEqual(self.calls[0],dict(event='ACTIVATE',kind='BOSS',subtype='GOROGAN',matchId='rnd1',untilAt=44))
        self.assertFalse(self.m.is_canonical(self.calls[0]))
    def test_off_default(self):
        m=Mapper(lambda:self.r,self.start,lambda _:True,approved=True)
        self.assertEqual(m.handle(self.e)[1],'DISABLED_DEFAULT')
    def test_off_approval(self):
        m=Mapper(lambda:self.r,self.start,lambda _:True,enabled=True)
        self.assertEqual(m.handle(self.e)[1],'DISABLED_DEFAULT')
    def test_replay(self):
        self.m.handle(self.e)
        self.assertEqual(self.m.handle(self.e)[1],'EVENT_REPLAY')
    def test_reentrant(self):
        self.m.in_callback=True
        self.assertEqual(self.m.handle(self.e)[1],'REENTRANT_CALLBACK')
    def test_start_fail_abort(self):
        self.m.start_combined=lambda a:(False,'REJECTED')
        self.assertEqual(self.m.handle(self.e)[1],'START_FAILED_OR_STALE')
        self.assertEqual(self.aborts,['rnd1'])
        self.assertFalse(self.m.enabled)
    def test_start_throws_abort(self):
        self.m.start_combined=lambda a:(_ for _ in ()).throw(RuntimeError('boom'))
        self.assertEqual(self.m.handle(self.e)[1],'START_FAILED_OR_STALE')
    def test_abort_fails_critical(self):
        self.m.start_combined=lambda a:(False,'REJECTED')
        self.m.abort_combined=lambda rid:False
        self.assertEqual(self.m.handle(self.e)[1],'CRITICAL_ABORT_NOT_CONFIRMED')
    def test_round_changed_during_callback(self):
        def switch(a):
            self.r['epoch']+=1
            return True,'STARTED'
        self.m.start_combined=switch
        self.assertEqual(self.m.handle(self.e)[1],'START_FAILED_OR_STALE')
        self.assertEqual(self.aborts,['rnd1'])
    def test_round_time_reversed_during_callback(self):
        def switch(a):
            self.r['now']-=1
            return True,'STARTED'
        self.m.start_combined=switch
        self.assertEqual(self.m.handle(self.e)[1],'START_FAILED_OR_STALE')
    def test_expired_during_yield_abort(self):
        def fast_forward(a):
            self.r['now'] = 44
            return True, 'STARTED'
        self.m.start_combined=fast_forward
        self.assertEqual(self.m.handle(self.e)[1], 'START_FAILED_OR_STALE')
        self.assertEqual(self.aborts,['rnd1'])
    def test_observed_post_callback_clock_is_monotonic_base(self):
        def fast_forward(a):
            self.r['now'] = 40
            return True,'STARTED'
        self.m.start_combined=fast_forward
        self.assertEqual(self.m.handle(self.e)[0], True)
        self.r.update(matchId='rnd2',epoch=10,now=39,deadline=60)
        self.e.update(matchId='rnd2',epoch=10,validUntil=50)
        self.assertEqual(self.m.handle(self.e)[1], 'SERVER_CLOCK_REVERSED')
    def test_round_deadline_changed_during_callback(self):
        def switch(a):
            self.r['deadline']+=1
            return True,'STARTED'
        self.m.start_combined=switch
        self.assertEqual(self.m.handle(self.e)[1],'START_FAILED_OR_STALE')
    def test_round_unavailable(self):
        self.m.read_round=lambda:None
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_read_round_exception(self):
        self.m.read_round=lambda:(_ for _ in ()).throw(RuntimeError())
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_invalid_clock(self):
        self.r['now']=float('nan')
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_boolean_clock(self):
        self.r['now']=True
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_just_two_seconds(self):
        self.e['validUntil']=32
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_valid_until_beyond_round(self):
        self.e['validUntil']=61
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_clock_reversed_after_valid_round(self):
        self.m.handle(self.e)
        self.r.update(matchId='rnd2',epoch=10,now=29)
        self.e.update(matchId='rnd2',epoch=10)
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_CLOCK_REVERSED')
        self.assertFalse(self.m.enabled)
    def test_round_replace_accepted(self):
        self.m.handle(self.e)
        self.r.update(matchId='rnd2',epoch=10,now=45,deadline=75)
        self.e.update(matchId='rnd2',epoch=10,validUntil=59)
        self.assertEqual(self.m.handle(self.e)[0],True)
    def test_old_round_replay(self):
        self.m.handle(self.e)
        self.r.update(matchId='rnd2',epoch=10,now=45,deadline=75)
        self.e.update(matchId='rnd2',epoch=10,validUntil=59)
        self.m.handle(self.e)
        self.r.update(matchId='rnd1',epoch=9,now=47,deadline=70)
        self.e.update(matchId='rnd1',epoch=9,validUntil=60)
        self.assertEqual(self.m.handle(self.e)[1],'EVENT_REPLAY')
    def test_invalid_envelopes(self):
        cases=[('phase','WARNING'),('phase','CLEANUP'),('kind','WEATHER'),('kind',None),('subtype','LIGARDO'),('subtype',''),('matchId',''),('matchId','!foo'),('stage','S2'),('epoch',-1),('epoch',1.5),('epoch',True),('epoch',float('inf')),('validUntil',None),('validUntil',float('nan')),('validUntil',True)]
        for k,v in cases:
            with self.subTest(k=k,v=v):
                e=dict(self.e);e[k]=v
                self.assertEqual(self.m.handle(e)[1],'INVALID_D08_ENVELOPE')
    def test_mismatches(self):
        cases=[('matchId','rnd2'),('stage','S3'),('epoch',10)]
        for k,v in cases:
            with self.subTest(k=k):
                e=dict(self.e);e[k]=v
                self.assertEqual(self.m.handle(e)[1],'SERVER_ROUND_MISMATCH')
    def test_invalid_roster_status(self):
        self.r['active']=False
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_attempt_budget(self):
        self.m.attempted={(f'r{i}',i) for i in range(128)}
        self.assertEqual(self.m.handle(self.e)[1],'ATTEMPT_CAP_REACHED')
    def test_plain_table_cannot_attest(self):
        self.assertFalse(self.m.is_canonical(dict(event='ACTIVATE',matchId='rnd1')))
    def test_no_duplicate_start_after_failure(self):
        self.m.start_combined=lambda a:(False,'ERROR')
        self.m.handle(self.e)
        self.assertEqual(len(self.calls),0)
        self.assertEqual(self.m.handle(self.e)[1],'START_FAILED_OR_STALE')
    def test_static_adapter_contract(self):
        s=(ROOT/'luau/TrustedGoroganActivationMapper.luau').read_text(encoding='utf-8')
        for must in ['function Mapper.new','function Mapper:isCanonicalActivation','function Mapper:handle','function Mapper:disable','self.attestedActivation == activation','self.attestedActivation = nil','phase ~= "ACTIVATE"','activation = {','untilAt = envelope.validUntil','pcall(self.deps.startCombined','pcall(self.deps.abortCombined','self.attempted[key] = true']:
            with self.subTest(must=must): self.assertIn(must,s)
    def test_static_no_effects(self):
        s=(ROOT/'luau/TrustedGoroganActivationMapper.luau').read_text(encoding='utf-8')
        executable='\n'.join(line for line in s.splitlines() if not line.lstrip().startswith('--'))
        for forbidden in ['FireServer','OnServerEvent','RemoteEvent','Instance.new','TakeDamage','GetService','PathfindingService','Random.new','NextInteger','SetNetworkOwner','AssemblyLinearVelocity','CFrame.new','DataStore']:
            with self.subTest(forbidden=forbidden):self.assertNotIn(forbidden,executable)
    def test_epoch_integral(self):
        self.r['epoch']=9.5
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_timeout_if_now_equal_deadline(self):
        self.r['now']=60
        self.assertEqual(self.m.handle(self.e)[1],'SERVER_ROUND_MISMATCH')
    def test_start_returns_truthy_string_is_failure(self):
        self.m.start_combined=lambda a:('true','STARTED')
        self.assertEqual(self.m.handle(self.e)[1],'START_FAILED_OR_STALE')
    def test_bad_abort_exception_critical(self):
        self.m.start_combined=lambda a:(False,'BAD')
        self.m.abort_combined=lambda rid:(_ for _ in ()).throw(RuntimeError())
        self.assertEqual(self.m.handle(self.e)[1],'CRITICAL_ABORT_NOT_CONFIRMED')
    def test_replay_does_not_invoke_callback_twice(self):
        self.m.handle(self.e);self.m.handle(self.e)
        self.assertEqual(len(self.calls),1)

if __name__=='__main__':unittest.main()
