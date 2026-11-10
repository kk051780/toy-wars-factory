import unittest
from pathlib import Path
from unittest.mock import patch
import random
from oracle import Producer, Follower

ROOT=Path(__file__).resolve().parents[1]
P1=(ROOT/'luau/GoroganPoseOutboxPolicy.luau').read_text(encoding='utf-8')
P2=(ROOT/'luau/GoroganVisualPoseFollower.luau').read_text(encoding='utf-8')


def maker(**kw):
    defaults={'match_id':'m1','event_id':'e1','stage':'S1','epoch':3,'started_at':10,
              'ends_at':24,'enabled':True,'owner_approved':True}
    defaults.update(kw)
    return Producer(**defaults)


def snap(t=10, **kw):
    s={'matchId':'m1','eventId':'e1','stageId':'S1','epoch':3,'now':t,
       'active':True,'position':{'x':0,'y':0,'z':0}}
    s.update(kw);return s


def follower(**kw):
    s={'match_id':'m1','event_id':'e1','stage':'S1','epoch':3,
       'initial_position':{'x':0,'y':0,'z':0},'start_local_now':10.0}
    s.update(kw);return Follower(**s)


def packet(seq=1, **kw):
    s={'kind':'POSE','bossId':'GOROGAN','matchId':'m1','eventId':'e1','stageId':'S1','epoch':3,
       'poseSeq':seq,'position':{'x':1,'y':0,'z':1}}
    s.update(kw);return s


class ServerPolicy(unittest.TestCase):
    def test_disabled_by_default(self):
        with self.assertRaises(ValueError): maker(enabled=False)
    def test_owner_approval_required(self):
        with self.assertRaises(ValueError): maker(owner_approved=False)
    def test_stage_restrictions(self):
        with self.assertRaises(ValueError): maker(stage='S2')
    def test_bad_event_identity(self):
        with self.assertRaises(ValueError): maker(event_id='bad event')
    def test_bad_epoch(self):
        with self.assertRaises(ValueError): maker(epoch=1.5)
    def test_expiry_cap(self):
        with self.assertRaises(ValueError): maker(ends_at=25)
    def test_first_emit(self):
        p,why=maker().sample(snap());self.assertEqual(why,'EMIT');self.assertEqual(p['poseSeq'],1)
    def test_snapshot_immutable_value(self):
        s=snap();p,_=maker().sample(s);s['position']['x']=777;self.assertEqual(p['position']['x'],0)
    def test_reject_mismatch_match(self):
        o=maker();self.assertEqual(o.sample(snap(matchId='m2'))[1],'AUTHORITY_OR_ROUND_INVALID');self.assertTrue(o.closed)
    def test_reject_mismatch_event(self):
        o=maker();self.assertEqual(o.sample(snap(eventId='e2'))[1],'AUTHORITY_OR_ROUND_INVALID')
    def test_reject_mismatch_epoch(self):
        o=maker();self.assertEqual(o.sample(snap(epoch=4))[1],'AUTHORITY_OR_ROUND_INVALID')
    def test_reject_stopped_round(self):
        o=maker();self.assertEqual(o.sample(snap(active=False))[1],'AUTHORITY_OR_ROUND_INVALID')
    def test_no_nan(self):
        o=maker();self.assertEqual(o.sample(snap(position={'x':float('nan'),'y':0,'z':0}))[1],'AUTHORITY_OR_ROUND_INVALID')
    def test_no_inf(self):
        o=maker();self.assertEqual(o.sample(snap(position={'x':float('inf'),'y':0,'z':0}))[1],'AUTHORITY_OR_ROUND_INVALID')
    def test_no_outside_map(self):
        o=maker();self.assertEqual(o.sample(snap(position={'x':9000,'y':0,'z':0}))[1],'AUTHORITY_OR_ROUND_INVALID')
    def test_rate_limit(self):
        o=maker();self.assertEqual(o.sample(snap(10))[1],'EMIT');self.assertEqual(o.sample(snap(10.1))[1],'RATE_LIMIT');self.assertEqual(o.count,1)
    def test_rate_recover(self):
        o=maker();o.sample(snap(10));self.assertEqual(o.sample(snap(10.25))[1],'EMIT')
    def test_clock_backward_closes(self):
        o=maker();o.sample(snap(10.25));self.assertEqual(o.sample(snap(10.2))[1],'CLOCK_REVERSED');self.assertTrue(o.closed)
    def test_expired(self):
        o=maker();self.assertEqual(o.sample(snap(24))[1],'EXPIRED')
    def test_sample_cap(self):
        o=maker();
        for i in range(64):self.assertEqual(o.sample(snap(10+i*.21))[1],'EMIT')
        self.assertEqual(o.sample(snap(23.45))[1],'SAMPLE_CAP')
    def test_postclose(self):
        o=maker();o.sample(snap(eventId='none'));self.assertEqual(o.sample(snap())[1],'CLOSED')
    def test_sealed_sequence(self):
        o=maker();self.assertEqual([o.sample(snap(10+j*.25))[0]['poseSeq'] for j in range(8)],list(range(1,9)))


class ClientPolicy(unittest.TestCase):
    def test_bad_start_epoch(self):
        with self.assertRaises(ValueError): follower(epoch=-1)
    def test_good_follow(self):
        f=follower();p,why=f.accept(packet(),10.1,True);self.assertEqual(why,'FOLLOW');self.assertEqual(p['x'],1)
    def test_lifecycle_inactive(self):
        f=follower();self.assertEqual(f.accept(packet(),10.1,False)[1],'VISUAL_ENDED');self.assertTrue(f.closed)
    def test_event_replay(self):
        f=follower();f.accept(packet(),10.1,True);self.assertEqual(f.accept(packet(),10.35,True)[1],'POSE_REPLAY')
    def test_wrong_epoch(self):
        f=follower();self.assertEqual(f.accept(packet(epoch=2),10.2,True)[1],'INVALID_POSE')
    def test_wrong_event(self):
        f=follower();self.assertEqual(f.accept(packet(eventId='e2'),10.2,True)[1],'INVALID_POSE')
    def test_wrong_boss(self):
        f=follower();self.assertEqual(f.accept(packet(bossId='LIGARDO'),10.2,True)[1],'INVALID_POSE')
    def test_bad_seq(self):
        f=follower();self.assertEqual(f.accept(packet(seq=3.5),10.2,True)[1],'INVALID_POSE')
    def test_seq_bounded(self):
        f=follower();self.assertEqual(f.accept(packet(seq=65),10.2,True)[1],'INVALID_POSE')
    def test_rate_limit(self):
        f=follower();f.accept(packet(),10.1,True);self.assertEqual(f.accept(packet(2),10.15,True)[1],'RATE_LIMIT')
    def test_rate_recover(self):
        f=follower();f.accept(packet(),10.1,True);self.assertEqual(f.accept(packet(2),10.35,True)[1],'FOLLOW')
    def test_large_jump(self):
        f=follower();f.accept(packet(),10.1,True)
        self.assertEqual(f.accept(packet(2,position={'x':999,'y':0,'z':0}),10.3,True)[1],'IMPOSSIBLE_VISUAL_JUMP')
    def test_large_jump_does_not_advance_sequence(self):
        f=follower();f.accept(packet(),10.1,True);f.accept(packet(2,position={'x':999,'y':0,'z':0}),10.3,True)
        self.assertEqual(f.last_seq,1)
    def test_first_pose_delayed_closes(self):
        f=follower();self.assertEqual(f.accept(packet(),11.7,True)[1],'CLIENT_SUSPENDED_REQUIRES_NEW_AUTH_START')
    def test_first_pose_impossible_jump(self):
        f=follower();self.assertEqual(f.accept(packet(position={'x':999,'y':0,'z':0}),10.1,True)[1],'IMPOSSIBLE_VISUAL_JUMP')
    def test_suspend_closes(self):
        f=follower();f.accept(packet(),10.1,True);self.assertEqual(f.accept(packet(2),11.8,True)[1],'CLIENT_SUSPENDED_REQUIRES_NEW_AUTH_START')
    def test_local_clock_reversed_closes(self):
        f=follower();self.assertEqual(f.accept(packet(),9,True)[1],'LOCAL_CLOCK_REVERSED')
    def test_nonfinite_local_clock(self):
        f=follower();self.assertEqual(f.accept(packet(),float('nan'),True)[1],'LOCAL_CLOCK_REVERSED')
    def test_mutated_snapshot_copies(self):
        p=packet();f=follower();f.accept(p,10.2,True);p['position']['x']=99;self.assertEqual(f.current['x'],1)
    def test_no_double_subscriptions_static(self):
        live='\n'.join(line for line in P2.splitlines() if not line.lstrip().startswith('--'))
        self.assertNotIn('OnClientEvent',live);self.assertNotIn('Heartbeat:Connect',live)
        self.assertNotIn('RemoteEvent',P1.split('local Outbox = {}')[1]);self.assertNotIn('FireAllClients',P1)
    def test_source_payload_and_caps_static(self):
        for key in ('poseSeq','eventId','epoch','matchId','stageId','MAX_SAMPLES = 64'):
            self.assertIn(key,P1)
        self.assertIn('packet.poseSeq,1,64',P2)
    def test_no_player_or_damage_mutation_static(self):
        for s in (P1,P2):
            for dangerous in ('TakeDamage(', 'Humanoid:','SetNetworkOwner(', 'AssemblyLinearVelocity', 'DataStoreService', 'PathfindingService', 'CreatePath('):
                self.assertNotIn(dangerous,s)
    def test_randomized_sequence(self):
        r=random.Random(103);o=maker();f=follower();local=10.0
        px,pz=0.0,0.0
        for i in range(42):
            px+=r.uniform(-1.5,1.5);pz+=r.uniform(-1.5,1.5)
            t=10+i*.25;s=snap(t,position={'x':px,'y':0,'z':pz})
            out,why=o.sample(s);self.assertEqual(why,'EMIT')
            local+=.25;p,why=f.accept(out,local,True)
            self.assertEqual(why,'FOLLOW')
            self.assertLessEqual(abs(p['x']),10)
        self.assertEqual(o.count,42)


if __name__=='__main__':unittest.main()
