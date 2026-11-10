"""Independent Python reference oracle for D14 server-visual outbound policy.
No actual Roblox/Luau runtime is exercised. Fail closed; synthetic only.
"""
import copy
import math
from pathlib import Path
import random
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'luau'/'D14VisualPublisherCore.luau'
ADAPTER=ROOT/'luau'/'D14ServerVisualOutboundAdapter.luau'


class PolicyError(Exception):
    pass


def valid_id(x):
    return isinstance(x,str) and 1 <= len(x) <= 48 and re.fullmatch(r'[A-Za-z0-9_-]+',x) is not None


def finite(x):
    return type(x) in (float,int) and math.isfinite(x)


def valid_pose(p):
    return isinstance(p,dict) and set(('x','y','z')) <= p.keys() and all(finite(p[k]) and abs(p[k])<=2048 for k in ('x','y','z'))


def valid_dir(d):
    return isinstance(d,dict) and all(k in d and finite(d[k]) for k in ('x','z')) and .90 <= d['x']**2+d['z']**2 <= 1.10


def distance(a,b):
    return math.dist([a[k] for k in ('x','y','z')],[b[k] for k in ('x','y','z')])


class Publisher:
    def __init__(self):
        self.started=False
        self.round=None
        self.last_clock=None
        self.slots={}

    def begin(self,round_id,now):
        if not valid_id(round_id) or not finite(now) or now<0:
            raise PolicyError('BAD_ROUND')
        if self.last_clock is not None and now<self.last_clock:
            raise PolicyError('CLOCK_REWIND')
        self.started=True;self.round=round_id;self.slots={};self.last_clock=now

    def stop(self):
        self.started=False;self.round=None;self.slots={}

    def publish(self, s):
        if not self.started:raise PolicyError('NOT_STARTED')
        if not isinstance(s,dict):raise PolicyError('BAD_SNAPSHOT')
        now=s.get('now')
        if not finite(now) or now<0 or (self.last_clock is not None and now<self.last_clock):
            raise PolicyError('STALE_CLOCK')
        if s.get('roundId')!=self.round or s.get('roundActive') is not True:raise PolicyError('STALE_ROUND')
        if s.get('authorizedServer') is not True or s.get('seatVerified') is not True:
            raise PolicyError('NO_AUTHORITY')
        if not valid_id(s.get('vehicleId')) or not valid_id(s.get('teamId')):raise PolicyError('BAD_ID')
        if s.get('kind') not in ('CART','RAFT'):raise PolicyError('BAD_KIND')
        if s.get('stage') not in ('S1','S2'):raise PolicyError('BAD_STAGE')
        epoch=s.get('seatEpoch');seq=s.get('sourceSeq')
        if type(epoch) is not int or not 0<=epoch<=10**9:raise PolicyError('BAD_EPOCH')
        if type(seq) is not int or not 1<=seq<=10**9:raise PolicyError('BAD_SOURCE_SEQ')
        if not all(type(s.get(k)) is bool for k in ('driverPresent','passengerPresent','moving')):raise PolicyError('BAD_SEATS')
        if (not s['driverPresent'] and (s['passengerPresent'] or s['moving'])):
            raise PolicyError('UNAUTHORIZED_OCCUPANCY')
        if not valid_pose(s.get('position')) or not valid_dir(s.get('direction')):
            raise PolicyError('BAD_GEOMETRY')
        slot=self.slots.get(s['vehicleId'])
        if slot is None and len(self.slots)>=4:raise PolicyError('TOO_MANY_VEHICLES')
        if slot:
            if any(slot[k]!=s[k] for k in ('kind','teamId','stage')):raise PolicyError('VEHICLE_ID_REUSED')
            if epoch<slot['seatEpoch']:raise PolicyError('STALE_SEAT_EPOCH')
            if seq<=slot['sourceSeq']:raise PolicyError('REPLAY_SOURCE_SEQ')
            if now<slot['at']:raise PolicyError('STALE_VEHICLE_CLOCK')
            if epoch==slot['seatEpoch'] and not slot['driverPresent'] and s['driverPresent']:
                raise PolicyError('DRIVER_REAUTH_REQUIRED')
            delta=now-slot['at']
            traveled=distance(s['position'],slot['position'])
            if traveled>(16 if s['kind']=='CART' else 8)*delta + 0.15+1e-12:
                raise PolicyError('POSE_TELEPORT')
            if not s['driverPresent'] and traveled>0.15+1e-12:
                raise PolicyError('MOTION_AFTER_DRIVER_EXIT')
            if delta<.1 and slot['driverPresent']==s['driverPresent'] and slot['passengerPresent']==s['passengerPresent']:
                raise PolicyError('RATE_LIMIT')
        outseq=slot['outSeq']+1 if slot else 1
        frame={
            'schema':'TR_D14_VISUAL_V1', 'roundId':self.round,
            'teamId':s['teamId'],'vehicleId':s['vehicleId'],
            'stage':s['stage'],'kind':s['kind'],'seq':outseq,'serverTime':now,'expiresAt':now+1.5,
            'position':{k:s['position'][k] for k in ('x','y','z')},
            'direction':{k:s['direction'][k] for k in ('x','z')},
            'moving':s['moving'],'driverPresent':s['driverPresent'],'passengerPresent':s['passengerPresent']}
        self.slots[s['vehicleId']]=dict(outSeq=outseq,sourceSeq=seq,at=now,position=frame['position'],seatEpoch=epoch,
            kind=s['kind'],stage=s['stage'],teamId=s['teamId'],driverPresent=s['driverPresent'],passengerPresent=s['passengerPresent'])
        self.last_clock=now
        return frame


def baseline(**overrides):
    obj=dict(roundId='round_A',roundActive=True,authorizedServer=True,seatVerified=True,
        vehicleId='cart_1',teamId='blue',kind='CART',stage='S1',seatEpoch=1,sourceSeq=1,now=10.,
        driverPresent=True,passengerPresent=False,moving=True,position=dict(x=0.,y=0.,z=0.),direction=dict(x=1.,z=0.))
    obj.update(overrides);return obj


class TestPolicy(unittest.TestCase):
    def setUp(self):self.p=Publisher();self.p.begin('round_A',10.)
    def push(self,**kw):return self.p.publish(baseline(**kw))
    def mustblock(self,expected,**kw):
        with self.assertRaisesRegex(PolicyError,expected):self.push(**kw)

    def test_valid_first_frame(self):
        f=self.push();self.assertEqual(f['seq'],1);self.assertEqual(f['expiresAt'],11.5)
    def test_allowlist_never_leaks_identifiers(self):
        f=self.push(userId=123,playerName='private',accountId='100');self.assertNotIn('userId',f);self.assertNotIn('playerName',f)
    def test_outbound_schema(self):
        self.assertEqual(set(self.push()),{'schema','roundId','teamId','vehicleId','stage','kind','seq','serverTime','expiresAt','position','direction','moving','driverPresent','passengerPresent'})
    def test_no_start(self):self.p.stop();self.mustblock('NOT_STARTED')
    def test_invalid_round_ids(self):
        for val in ('../unsafe','A!','',123):
            with self.subTest(val=val),self.assertRaises(PolicyError):Publisher().begin(val,10.)
    def test_round_rewind(self):self.push();self.p.begin('round_B',11.);self.assertEqual(self.p.publish(baseline(roundId='round_B',now=11.2))['seq'],1)
    def test_begin_clock_rewind(self):
        with self.assertRaisesRegex(PolicyError,'CLOCK_REWIND'):self.p.begin('round_B',9.)
    def test_stale_round(self):self.mustblock('STALE_ROUND',roundId='round_old')
    def test_round_closed(self):self.mustblock('STALE_ROUND',roundActive=False)
    def test_missing_authorized_server(self):self.mustblock('NO_AUTHORITY',authorizedServer=False)
    def test_missing_seat_receipt(self):self.mustblock('NO_AUTHORITY',seatVerified=False)
    def test_untrusted_boolean_numeric(self):self.mustblock('NO_AUTHORITY',authorizedServer=1)
    def test_invalid_vehicle_id(self):self.mustblock('BAD_ID',vehicleId='cart/../evil')
    def test_invalid_team_id(self):self.mustblock('BAD_ID',teamId='')
    def test_invalid_kind(self):self.mustblock('BAD_KIND',kind='AIRSHIP')
    def test_invalid_stage(self):self.mustblock('BAD_STAGE',stage='S4')
    def test_invalid_epoch(self):self.mustblock('BAD_EPOCH',seatEpoch=-1)
    def test_boolean_epoch_rejected(self):self.mustblock('BAD_EPOCH',seatEpoch=True)
    def test_invalid_seq(self):self.mustblock('BAD_SOURCE_SEQ',sourceSeq=0)
    def test_seat_fields_not_accepted_as_integers(self):self.mustblock('BAD_SEATS',driverPresent=1)
    def test_passenger_without_driver(self):self.mustblock('UNAUTHORIZED_OCCUPANCY',driverPresent=False,passengerPresent=True,moving=False)
    def test_moving_without_driver(self):self.mustblock('UNAUTHORIZED_OCCUPANCY',driverPresent=False,passengerPresent=False,moving=True)
    def test_nan(self):self.mustblock('BAD_GEOMETRY',position=dict(x=math.nan,y=0,z=0))
    def test_inf(self):self.mustblock('BAD_GEOMETRY',position=dict(x=math.inf,y=0,z=0))
    def test_out_of_bounds(self):self.mustblock('BAD_GEOMETRY',position=dict(x=2050,y=0,z=0))
    def test_zero_dir(self):self.mustblock('BAD_GEOMETRY',direction=dict(x=0,y=0,z=0))
    def test_invalid_dir(self):self.mustblock('BAD_GEOMETRY',direction=dict(x=7,z=4))
    def test_stale_global_clock(self):self.push();self.mustblock('STALE_CLOCK',now=9.9,sourceSeq=2)
    def test_replay_seq(self):self.push();self.mustblock('REPLAY_SOURCE_SEQ',now=10.2)
    def test_duplicate_rate_limited(self):self.push();self.mustblock('RATE_LIMIT',now=10.05,sourceSeq=2)
    def test_seq_increments(self):self.push();self.assertEqual(self.push(now=10.2,sourceSeq=2,position=dict(x=2,y=0,z=0))['seq'],2)
    def test_moving_teleport(self):self.push();self.mustblock('POSE_TELEPORT',now=10.2,sourceSeq=2,position=dict(x=100,y=0,z=0))
    def test_exact_speed_allowed(self):self.push();self.assertEqual(self.push(now=10.2,sourceSeq=2,position=dict(x=3.2,y=0,z=0))['seq'],2)
    def test_raft_speed_limit(self):
        self.push(kind='RAFT');self.mustblock('POSE_TELEPORT',kind='RAFT',now=10.2,sourceSeq=2,position=dict(x=3,y=0,z=0))
    def test_vehicle_team_swap(self):self.push();self.mustblock('VEHICLE_ID_REUSED',now=10.2,sourceSeq=2,teamId='red')
    def test_vehicle_kind_swap(self):self.push();self.mustblock('VEHICLE_ID_REUSED',now=10.2,sourceSeq=2,kind='RAFT')
    def test_vehicle_stage_swap(self):self.push();self.mustblock('VEHICLE_ID_REUSED',now=10.2,sourceSeq=2,stage='S2')
    def test_seat_epoch_rewind(self):self.push(seatEpoch=2);self.mustblock('STALE_SEAT_EPOCH',now=10.2,sourceSeq=2,seatEpoch=1)
    def test_seat_presence_stop_immediate(self):
        self.push();f=self.push(now=10.01,sourceSeq=2,driverPresent=False,moving=False)
        self.assertFalse(f['moving']);self.assertEqual(f['seq'],2)
    def test_driver_loss_position_frozen(self):
        self.push();self.mustblock('MOTION_AFTER_DRIVER_EXIT',now=10.2,sourceSeq=2,driverPresent=False,moving=False,position=dict(x=.3,y=0,z=0))
    def test_driver_return_requires_new_epoch(self):
        self.push();self.push(now=10.15,sourceSeq=2,driverPresent=False,moving=False)
        self.mustblock('DRIVER_REAUTH_REQUIRED',now=10.3,sourceSeq=3,driverPresent=True,moving=True)
    def test_driver_return_new_epoch(self):
        self.push();self.push(now=10.15,sourceSeq=2,driverPresent=False,moving=False)
        self.assertEqual(self.push(now=10.3,sourceSeq=3,seatEpoch=2)['seq'],3)
    def test_client_spoof_no_pose_leak(self):
        self.push();withheld=self.p.slots['cart_1'].copy()
        with self.assertRaises(PolicyError):self.push(now=10.2,sourceSeq=2,authorizedServer=False)
        self.assertEqual(self.p.slots['cart_1'],withheld)
    def test_four_vehicle_limit(self):
        for i in range(4):self.push(vehicleId='cart_'+str(i),now=10.,sourceSeq=1)
        self.mustblock('TOO_MANY_VEHICLES',vehicleId='cart_5')
    def test_seat_transition_bypass_rate_limit(self):
        self.push();f=self.push(now=10.01,sourceSeq=2,passengerPresent=True)
        self.assertEqual(f['seq'],2)
    def test_round_reset_clears_vehicles(self):
        self.push();self.p.begin('round_B',11.)
        self.assertEqual(self.push(roundId='round_B',now=11.0)['seq'],1)
    def test_many_seeded_bounded_poses(self):
        self.push();r=random.Random(17)
        x=0.;seq=1
        for i in range(3000):
            dt=.2;x += r.uniform(-1,1);seq+=1
            f=self.push(now=10.+.2*i+.2,sourceSeq=seq,position=dict(x=x,y=0,z=0))
            self.assertEqual(f['seq'],seq)
    def test_static_core_no_network_api(self):
        source=CORE.read_text();self.assertNotIn('OnServerEvent',source);self.assertNotIn('FireClient',source)
    def test_static_adapter_outbound_only(self):
        source=ADAPTER.read_text();self.assertIn(':FireClient(',source)
        self.assertNotIn('OnServerEvent',source);self.assertNotIn('FireServer',source)
        self.assertIn('enabled ~= true',source)
    def test_static_no_client_player_ids(self):
        core=CORE.read_text();self.assertNotIn('UserId',core);self.assertNotIn('Name = player',core)
    def test_static_anti_motion_loss(self):
        core=CORE.read_text();self.assertIn('if not snapshot.driverPresent and dist',core)
    def test_static_server_only_runtime(self):self.assertIn('RunService:IsServer()',ADAPTER.read_text())
    def test_static_existing_server_receipts(self):self.assertIn('snapshot.seatVerified ~= true',ADAPTER.read_text())
    def test_static_no_new_scheduler(self):self.assertNotIn('Heartbeat:Connect',ADAPTER.read_text())
    def test_static_no_instance_builder(self):self.assertNotIn('Instance.new',ADAPTER.read_text())


if __name__=='__main__':unittest.main()
