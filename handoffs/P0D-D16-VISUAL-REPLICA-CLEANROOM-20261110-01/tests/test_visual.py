import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests'))
from reference import ClientPolicy, ServerBridge
SB=(ROOT/'luau'/'ReplicaSnapshotBridge.luau').read_text()
CP=(ROOT/'luau'/'ReplicaDisplayPolicy.luau').read_text()
RE=(ROOT/'luau'/'ReplicaClientRenderer.luau').read_text()

def snapshot(**kw):
    d={'server_authorized':True,'event_approved':True,'event_name':'GIANT_ONE',
       'match_id':'round1','epoch':3,'sequence':1,
       'server_round_elapsed_seconds':10,'expires_at_round_seconds':18,
       'target_user_ids':[321]}
    d.update(kw)
    return d

class BridgeTests(unittest.TestCase):
    def test_01_valid(self):
        self.assertEqual(ServerBridge().project(snapshot())['kind'],'DISPLAY')
    def test_02_untrusted(self):
        self.assertEqual(ServerBridge().project(snapshot(server_authorized=False))['kind'],'REJECTED')
    def test_03_unapproved(self):
        self.assertEqual(ServerBridge().project(snapshot(event_approved=False))['kind'],'REJECTED')
    def test_04_no_new_event_chooser(self):
        self.assertEqual(ServerBridge().project(snapshot(event_name='OTHER'))['kind'],'REJECTED')
    def test_05_expired(self):
        self.assertEqual(ServerBridge().project(snapshot(expires_at_round_seconds=10))['kind'],'REJECTED')
    def test_06_ttl_over8(self):
        self.assertEqual(ServerBridge().project(snapshot(expires_at_round_seconds=20))['kind'],'REJECTED')
    def test_07_ttl_uses_round_elapsed(self):
        self.assertEqual(ServerBridge().project(snapshot(server_round_elapsed_seconds=13,expires_at_round_seconds=18))['remaining_seconds'],5)
    def test_08_single_giant_target(self):
        self.assertEqual(ServerBridge().project(snapshot(target_user_ids=[1,2]))['kind'],'REJECTED')
    def test_09_mini_all_allows8(self):
        self.assertEqual(ServerBridge().project(snapshot(event_name='MINI_ALL',target_user_ids=list(range(1,9))))['scale_factor'],0.7)
    def test_10_over8_denied(self):
        self.assertEqual(ServerBridge().project(snapshot(event_name='MINI_ALL',target_user_ids=list(range(1,10))))['kind'],'REJECTED')
    def test_11_duplicate_targets_denied(self):
        self.assertEqual(ServerBridge().project(snapshot(event_name='MINI_ALL',target_user_ids=[1,1]))['kind'],'REJECTED')
    def test_12_replay_denied(self):
        b=ServerBridge();b.project(snapshot());self.assertEqual(b.project(snapshot())['kind'],'REJECTED')
    def test_13_future_seq_ok(self):
        b=ServerBridge();b.project(snapshot());self.assertEqual(b.project(snapshot(sequence=2))['kind'],'DISPLAY')
    def test_14_negative_epoch(self):
        self.assertEqual(ServerBridge().project(snapshot(epoch=-1))['kind'],'REJECTED')
    def test_15_wrong_id(self):
        self.assertEqual(ServerBridge().project(snapshot(match_id=''))['kind'],'REJECTED')
    def test_16_nan(self):
        self.assertEqual(ServerBridge().project(snapshot(server_round_elapsed_seconds=float('nan')))['kind'],'REJECTED')

class ClientTests(unittest.TestCase):
    def setUp(self):
        self.bridge=ServerBridge();self.p=self.bridge.project(snapshot());self.c=ClientPolicy()
    def test_17_default_off(self):
        self.assertFalse(self.c.active)
    def test_18_begin(self):
        self.assertEqual(self.c.begin(self.p,20,False),'START')
    def test_19_ignore_untrusted(self):
        self.p['from_server_bridge']=False
        self.assertEqual(self.c.begin(self.p,20,False),'REJECTED')
    def test_20_8sec_expiry(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(27.9,'round1',3,(0,0,0),[])[0],'FRAME')
        self.assertEqual(self.c.frame(28,'round1',3,(0,0,0),[])[0],'CLEAR')
    def test_21_clock_reversal(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(19,'round1',3,(0,0,0),[])[0],'CLEAR')
    def test_22_wrong_round(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(21,'other',3,(0,0,0),[])[0],'CLEAR')
    def test_23_wrong_epoch(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(21,'round1',4,(0,0,0),[])[0],'CLEAR')
    def test_24_display_nearby(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(21,'round1',3,(0,0,0),[{'user_id':321,'position':(0,0,90)}]),('FRAME',[321]))
    def test_25_not_far(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(21,'round1',3,(0,0,0),[{'user_id':321,'position':(0,0,90.1)}]),('FRAME',[]))
    def test_26_others_not_in_targets(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(21,'round1',3,(0,0,0),[{'user_id':999,'position':(0,0,0)}]),('FRAME',[]))
    def test_27_duplicate_avatar_not_twice(self):
        self.c.begin(self.p,20,False)
        v=[{'user_id':321,'position':(0,0,0)}]*2
        self.assertEqual(self.c.frame(21,'round1',3,(0,0,0),v),('FRAME',[321]))
    def test_28_reduced_motion_4x6(self):
        self.assertEqual(self.c.begin(self.p,20,True),'START')
        self.assertEqual((self.c.max_avatars,self.c.max_parts),(4,6))
    def test_29_normal_8x18(self):
        self.c.begin(self.p,20,False)
        self.assertEqual((self.c.max_avatars,self.c.max_parts),(8,18))
    def test_30_replay_denied(self):
        self.c.begin(self.p,20,False);self.c.clear()
        self.assertEqual(self.c.begin(self.p,30,False),'REJECTED')
    def test_31_wider_sequence_ok(self):
        self.c.begin(self.p,20,False);self.c.clear()
        new=dict(self.p,sequence=2)
        self.assertEqual(self.c.begin(new,30,False),'START')
    def test_32_wrong_scale(self):
        self.p['scale_factor']=2.5
        self.assertEqual(self.c.begin(self.p,20,False),'REJECTED')
    def test_33_mini_all_display(self):
        p=self.bridge.project(snapshot(event_name='MINI_ALL',sequence=2,target_user_ids=list(range(1,9))))
        self.assertEqual(self.c.begin(p,20,False),'START')
        users=[{'user_id':n,'position':(0,0,0)} for n in range(1,10)]
        self.assertEqual(len(self.c.frame(21,'round1',3,(0,0,0),users)[1]),8)
    def test_34_missing_camera_coordinate(self):
        self.c.begin(self.p,20,False)
        self.assertEqual(self.c.frame(21,'round1',3,None,[])[0],'CLEAR')

class StaticLuau(unittest.TestCase):
    def test_35_no_new_server_rng(self):
        self.assertNotIn('math.random',SB+CP+RE)
        self.assertNotIn('Random.new(',SB+CP+RE)
    def test_36_no_network_connections(self):
        self.assertNotIn('OnServerEvent',SB+CP+RE)
        self.assertNotIn('OnClientEvent',SB+CP+RE)
        self.assertNotIn('FireServer(',SB+CP+RE)
        self.assertNotIn('FireClient(',SB+CP+RE)
    def test_37_no_body_scale_or_damage_write(self):
        self.assertNotIn('Humanoid:TakeDamage',SB+CP+RE)
        self.assertNotIn('Humanoid.Health',SB+CP+RE)
        self.assertNotIn('GetScale(',SB+CP+RE)
        self.assertNotIn('ScaleTo(',SB+CP+RE)
    def test_38_no_physics_interaction(self):
        for x in ('ghost.CanCollide = false','ghost.CanTouch = false','ghost.CanQuery = false','ghost.Anchored = true'):
            self.assertIn(x,RE)
    def test_39_no_automatic_bootstrap(self):
        self.assertNotIn('RenderStepped',RE)
        self.assertNotIn('Heartbeat',RE)
    def test_40_has_cleanup(self):
        self.assertIn('self.model:Destroy()',RE)
        self.assertIn('function Policy:clear()',CP)
    def test_41_capped_parts(self):
        self.assertIn('total >= 144',RE)
        self.assertIn('self.max_parts = reduced_motion and 6 or 18',CP)
    def test_42_same_clock_protocol(self):
        self.assertIn('SERVER_ROUND_ELAPSED',SB)
        self.assertIn('SERVER_ROUND_ELAPSED',CP)
    def test_43_max_range(self):
        self.assertIn('90*90',CP)
    def test_44_server_authority(self):
        self.assertIn('s.server_authorized ~= true',SB)
        self.assertIn('s.event_approved ~= true',SB)
    def test_45_pure_renderer_not_clone_real_char(self):
        self.assertNotIn('source:Clone()',RE)
        self.assertIn('ghost = Instance.new("Part")',RE)

if __name__=='__main__':
    unittest.main()
