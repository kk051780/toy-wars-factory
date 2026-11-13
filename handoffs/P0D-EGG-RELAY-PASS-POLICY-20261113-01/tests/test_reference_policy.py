"""Behavioral unit tests for Python reference + safety-oriented source inspections.
Does not execute Luau/Roblox or prove an in-game pass is wired.
"""
import pathlib, re, unittest
from reference_policy import fixture, check
ROOT=pathlib.Path(__file__).resolve().parents[1]

class EggRelayPolicyTests(unittest.TestCase):
    def test_accept_valid_two_teammates(self):
        w,r=fixture();self.assertEqual(check(w,r),'ACCEPT_POLICY_ONLY')
    def test_exact_limit_eight_studs_allowed(self):
        w,r=fixture();self.assertEqual(check(w,r),'ACCEPT_POLICY_ONLY')
    def test_cooldown_at_twelve_seconds_accepted(self):
        w,r=fixture();w['eggs']['E2']['lastRelayAtSec']=88;self.assertEqual(check(w,r),'ACCEPT_POLICY_ONLY')
    def test_classic_or_five_egg_id_independent(self):
        w,r=fixture();e=w['eggs'].pop('E2');e['id']='N1';w['eggs']['N1']=e;w['players'][1]['carriedEggId']='N1';r['eggId']='N1';self.assertEqual(check(w,r),'ACCEPT_POLICY_ONLY')
    def test_stale_round(self):
        w,r=fixture();r['roundEpoch']=6;self.assertEqual(check(w,r),'STALE_ROUND')
    def test_not_playing(self):
        w,r=fixture();w['phase']='RESULT';self.assertEqual(check(w,r),'ROUND_NOT_PLAYING')
    def test_self_transfer(self):
        w,r=fixture();r['targetUserId']=1;self.assertEqual(check(w,r),'INVALID_PARTICIPANTS')
    def test_real_large_user_ids_allowed(self):
        w,r=fixture()
        a,b=5_000_000_123,5_000_000_456
        w['players'][a]=w['players'].pop(1)
        w['players'][b]=w['players'].pop(2)
        w['lastAcceptedSeqByUser'][a]=w['lastAcceptedSeqByUser'].pop(1)
        w['eggs']['E2']['carrierUserId']=a
        r['actorUserId']=a
        r['targetUserId']=b
        self.assertEqual(check(w,r),'ACCEPT_POLICY_ONLY')

    def test_above_exact_integer_range_rejected(self):
        w,r=fixture()
        r['actorUserId']=9007199254740992
        self.assertEqual(check(w,r),'INVALID_PARTICIPANTS')

    def test_wrong_team(self):
        w,r=fixture();w['players'][2]['team']='BLUE';self.assertEqual(check(w,r),'WRONG_TEAM')
    def test_ghost_target(self):
        w,r=fixture();w['players'].pop(2);self.assertEqual(check(w,r),'PLAYER_MISSING')
    def test_target_already_carrying(self):
        w,r=fixture();w['players'][2]['carriedEggId']='X';self.assertEqual(check(w,r),'CARRIER_INVENTORY_CONFLICT')
    def test_carrier_inventory_conflict(self):
        w,r=fixture();w['players'][1]['carriedEggId']='X';self.assertEqual(check(w,r),'CARRIER_INVENTORY_CONFLICT')
    def test_egg_not_carried(self):
        w,r=fixture();w['eggs']['E2']['phase']='DROPPED';self.assertEqual(check(w,r),'NOT_AUTHORIZED_CARRIER')
    def test_egg_relay_blocked(self):
        w,r=fixture();w['eggs']['E2']['relayEligible']=False;self.assertEqual(check(w,r),'NOT_AUTHORIZED_CARRIER')
    def test_wrong_carrier(self):
        w,r=fixture();w['eggs']['E2']['carrierUserId']=42;self.assertEqual(check(w,r),'NOT_AUTHORIZED_CARRIER')
    def test_duplicate_request_sequence(self):
        w,r=fixture();r['seq']=4;self.assertEqual(check(w,r),'REPLAYED_REQUEST')
    def test_wrong_transfer_version(self):
        w,r=fixture();r['expectedTransferSeq']=2;self.assertEqual(check(w,r),'STALE_EGG_VERSION')
    def test_pass_cooldown(self):
        w,r=fixture();w['eggs']['E2']['lastRelayAtSec']=89;self.assertEqual(check(w,r),'EGG_PASS_COOLDOWN')
    def test_future_timestamp_rejected(self):
        w,r=fixture();w['eggs']['E2']['lastRelayAtSec']=101;self.assertEqual(check(w,r),'CLOCK_OR_COOLDOWN_INVALID')
    def test_dead_actor(self):
        w,r=fixture();w['players'][1]['alive']=False;self.assertEqual(check(w,r),'PLAYER_NOT_ELIGIBLE')
    def test_dead_target(self):
        w,r=fixture();w['players'][2]['alive']=False;self.assertEqual(check(w,r),'PLAYER_NOT_ELIGIBLE')
    def test_stunned(self):
        w,r=fixture();w['players'][1]['stunned']=True;self.assertEqual(check(w,r),'PLAYER_NOT_ELIGIBLE')
    def test_restrained(self):
        w,r=fixture();w['players'][2]['restrained']=True;self.assertEqual(check(w,r),'PLAYER_NOT_ELIGIBLE')
    def test_just_beyond_horizontal_limit(self):
        w,r=fixture();w['players'][2]['serverPosition']['x']=8.001;self.assertEqual(check(w,r),'OUT_OF_PASS_RANGE')
    def test_vertical_gap(self):
        w,r=fixture();w['players'][2]['serverPosition']['y']=4.01;self.assertEqual(check(w,r),'OUT_OF_PASS_RANGE')
    def test_wall_blocks_pass(self):
        w,r=fixture();w['serverLineOfSightClear']=False;self.assertEqual(check(w,r),'PASS_LINE_OF_SIGHT_BLOCKED')
    def test_missing_los_blocks_pass(self):
        w,r=fixture();w.pop('serverLineOfSightClear');self.assertEqual(check(w,r),'PASS_LINE_OF_SIGHT_BLOCKED')
    def test_invalid_position(self):
        w,r=fixture();w['players'][1]['serverPosition']={'x':0,'y':float('nan'),'z':0};self.assertEqual(check(w,r),'UNVERIFIED_POSITIONS')
    def test_invalid_clock(self):
        w,r=fixture();w['nowSec']=float('inf');self.assertEqual(check(w,r),'INVALID_SERVER_CLOCK')
    def test_missing_state(self):
        w,r=fixture();w.pop('eggs');self.assertEqual(check(w,r),'MISSING_AUTHORITY_STATE')
    def test_invalid_egg_id(self):
        w,r=fixture();r['eggId']='';self.assertEqual(check(w,r),'INVALID_EGG_ID')
    def test_invalid_seq(self):
        w,r=fixture();r['seq']=True;self.assertEqual(check(w,r),'INVALID_REQUEST_SEQUENCE')
    def test_policy_contains_no_engine_side_effects(self):
        s=(ROOT/'src/EggRelayPolicy.luau').read_text()
        self.assertNotIn('OnServerEvent',s)
        for banned in ['FireServer(', 'GetDataStore(', 'UpdateAsync(', 'Instance.new(', 'RemoteEvent.new(']:
            self.assertNotIn(banned,s)
        self.assertIn('function Relay.evaluate(world, request)',s)
        self.assertIn('serverLineOfSightClear ~= true',s)
    def test_policy_rejects_replay_and_duplicate_carry(self):
        s=(ROOT/'src/EggRelayPolicy.luau').read_text()
        for must in ['REPLAYED_REQUEST','STALE_EGG_VERSION','CARRIER_INVENTORY_CONFLICT','OUT_OF_PASS_RANGE','EGG_PASS_COOLDOWN']:
            self.assertIn(must,s)

if __name__=='__main__':unittest.main()
