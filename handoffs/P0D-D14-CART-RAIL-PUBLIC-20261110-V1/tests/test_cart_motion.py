from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import cart_motion_oracle as m
import copy, math, random, unittest

BASE={'id':'S1_North_Gate','speed':10,'nodes':[{'x':0,'y':3,'z':0},{'x':10,'y':3,'z':0},{'x':20,'y':3,'z':0}]}
BASE_DRIVER={'roundId':'round-1','teamId':'BLUE','isCurrentDriver':True,'alive':True,'carrier':False,'mounted':True,'isTrapped':False,'sequence':1}
BASE_TICK={'roundId':'round-1','teamId':'BLUE','active':True,'driverStillValid':True,'alive':True,'mounted':True,'carrier':False,'isTrapped':False}

class TestCart(unittest.TestCase):
    def new(self,route=None):return m.Cart(copy.deepcopy(route if route is not None else BASE),'round-1','BLUE')
    def request(self, c, **kw):return c.request({**BASE_DRIVER,**kw})
    def tick(self, c, dt=.1, **kw):return c.step(dt,{**BASE_TICK,**kw})
    def test_constructor(self):self.assertEqual(self.new().position,BASE['nodes'][0])
    def test_empty_id(self):
        r=copy.deepcopy(BASE);r['id']=''
        with self.assertRaises(m.PolicyError):self.new(r)
    def test_bad_route_id(self):
        for name in ['a/b','a b','../','á','z'*49]:
            with self.subTest(name=name):
                r=copy.deepcopy(BASE);r['id']=name
                with self.assertRaises(m.PolicyError):self.new(r)
    def test_bad_node_count(self):
        for n in (0,1,25,50):
            r=copy.deepcopy(BASE);r['nodes']=([BASE['nodes'][0]]*n)
            with self.subTest(n=n),self.assertRaises(m.PolicyError):self.new(r)
    def test_route_edge_too_short(self):
        r=copy.deepcopy(BASE);r['nodes'][1]['x']=5
        with self.assertRaises(m.PolicyError):self.new(r)
    def test_route_edge_too_long(self):
        r=copy.deepcopy(BASE);r['nodes'][1]['x']=81
        with self.assertRaises(m.PolicyError):self.new(r)
    def test_invalid_coordinate(self):
        for v in (-2001,2001,float('nan'),float('inf'),'foo',True):
            r=copy.deepcopy(BASE);r['nodes'][1]['x']=v
            with self.subTest(v=str(v)),self.assertRaises(m.PolicyError):self.new(r)
    def test_route_speed(self):
        for s in (0,1.9,16.1,math.nan,math.inf,'10',True):
            r=copy.deepcopy(BASE);r['speed']=s
            with self.subTest(s=str(s)),self.assertRaises(m.PolicyError):self.new(r)
    def test_bad_team(self):
        with self.assertRaises(m.PolicyError):m.Cart(BASE,'round-1','GREEN')
    def test_bad_round(self):
        with self.assertRaises(m.PolicyError):m.Cart(BASE,'','BLUE')
    def test_driver_advances_one_leg(self):
        c=self.new();self.assertEqual(self.request(c),(True,'OK'))
        statuses=[self.tick(c) for _ in range(10)]
        self.assertIn('LEG_COMPLETE',statuses)
        self.assertEqual(c.leg,1);self.assertFalse(c.moving)
        self.assertAlmostEqual(c.position['x'],10)
    def test_two_legs_require_two_commands(self):
        c=self.new();self.request(c)
        for _ in range(11):self.tick(c)
        self.assertEqual(self.request(c,sequence=2),(True,'OK'))
        for _ in range(11):self.tick(c)
        self.assertEqual(c.leg,2)
        self.assertEqual(self.request(c,sequence=3),(False,'ROUTE_END'))
    def test_replay_blocks(self):
        c=self.new();self.request(c)
        for _ in range(11):self.tick(c)
        self.assertEqual(self.request(c,sequence=1),(False,'REPLAY'))
    def test_sequence_fraction_blocks(self):self.assertEqual(self.request(self.new(),sequence=1.5),(False,'REPLAY'))
    def test_sequence_nan_blocks(self):self.assertEqual(self.request(self.new(),sequence=math.nan),(False,'REPLAY'))
    def test_sequence_bool_blocks(self):self.assertEqual(self.request(self.new(),sequence=True),(False,'REPLAY'))
    def test_wrong_round_blocks(self):self.assertEqual(self.request(self.new(),roundId='old')[1],'WRONG_ROUND_TEAM')
    def test_wrong_team_blocks(self):self.assertEqual(self.request(self.new(),teamId='RED')[1],'WRONG_ROUND_TEAM')
    def test_passenger_blocks(self):self.assertEqual(self.request(self.new(),isCurrentDriver=False)[1],'DRIVER_AUTH')
    def test_dead_blocks(self):self.assertEqual(self.request(self.new(),alive=False)[1],'DRIVER_AUTH')
    def test_unmounted_blocks(self):self.assertEqual(self.request(self.new(),mounted=False)[1],'DRIVER_AUTH')
    def test_egg_carrier_blocks(self):self.assertEqual(self.request(self.new(),carrier=True)[1],'DRIVER_AUTH')
    def test_snare_blocks(self):self.assertEqual(self.request(self.new(),isTrapped=True)[1],'DRIVER_AUTH')
    def test_while_moving_blocks(self):
        c=self.new();self.request(c)
        self.assertEqual(self.request(c,sequence=2)[1],'ALREADY_MOVING')
    def test_large_dt_stops(self):
        c=self.new();self.request(c)
        self.assertEqual(self.tick(c,dt=.101),'BAD_DT_STOP');self.assertEqual(c.position['x'],0)
    def test_bad_dt_stops(self):
        for dt in (math.nan,math.inf,-.1,'0.1',True):
            c=self.new();self.request(c)
            self.assertEqual(self.tick(c,dt=dt),'BAD_DT_STOP')
    def test_auth_revoked_mid_leg(self):
        for changes in ({'active':False},{'driverStillValid':False},{'alive':False},{'mounted':False},{'carrier':True},{'isTrapped':True},{'roundId':'old'},{'teamId':'RED'}):
            c=self.new();self.request(c);self.tick(c)
            before=c.position.copy();self.assertEqual(self.tick(c,**changes),'AUTH_STOP');self.assertEqual(c.position,before)
    def test_end_round(self):
        c=self.new();self.request(c);c.end()
        self.assertEqual(self.tick(c),'ENDED');self.assertEqual(self.request(c,sequence=2)[1],'ENDED')
    def test_stop_requires_new_sequence(self):
        c=self.new();self.request(c);self.tick(c);c.stop()
        self.assertEqual(self.request(c,sequence=1)[1],'REPLAY')
        self.assertEqual(self.request(c,sequence=2)[1],'OK')
    def test_movement_never_teleports(self):
        c=self.new();self.request(c)
        last=0.0
        for _ in range(14):
            self.tick(c)
            self.assertLessEqual(c.position['x']-last,1.000001)
            last=c.position['x']
    def test_randomized_events_5k(self):
        random.seed(1508)
        for _ in range(25):
            c=self.new();seq=1;prev=c.position['x']
            for __ in range(200):
                op=random.randrange(5)
                if op==0:
                    self.request(c,sequence=seq);seq+=1
                elif op==1:
                    self.tick(c,dt=random.random()*.1)
                elif op==2:
                    self.tick(c,carrier=True)
                elif op==3:
                    self.tick(c,active=False)
                else:c.stop()
                self.assertGreaterEqual(c.position['x']+.00001,prev)
                self.assertLessEqual(c.position['x'],20.00001)
                prev=c.position['x']
    def test_static_luau_authority(self):
        root=Path(__file__).resolve().parents[1]
        core=(root/'luau'/'CartMotionCore.luau').read_text()
        adapter=(root/'luau'/'CartServerAdapter.luau').read_text()
        self.assertIn('facts.isCurrentDriver ~= true',core)
        self.assertIn('facts.carrier == true',core)
        self.assertIn('state.moving = false',core)
        self.assertIn('callbacks.driverFacts(actorFromServerEvent',adapter)
        self.assertNotIn('OnServerEvent:Connect',adapter)
        self.assertNotIn('TweenService',adapter)
    def test_adapter_pose_only_no_model_ownership(self):
        source=(Path(__file__).resolve().parents[1]/'luau'/'CartServerAdapter.luau').read_text()
        self.assertIn('position=position,direction=self.state.direction',source)
        self.assertNotIn('Instance.new',source)
        self.assertNotIn('PivotTo',source)
        core=(Path(__file__).resolve().parents[1]/'luau'/'CartMotionCore.luau').read_text()
        self.assertIn('state.direction = {x=b.x-a.x, y=b.y-a.y, z=b.z-a.z}',core)

    def test_visual_claim_separation(self):
        root=Path(__file__).resolve().parents[1]
        self.assertFalse((root/'luau'/'CartVisualPrefab.luau').exists())
        code=(root/'luau'/'CartServerAdapter.luau').read_text()
        self.assertNotIn('CanCollide',code)
        self.assertNotIn('Instance.new',code)
        self.assertNotIn('self.model',code)

if __name__ == '__main__':unittest.main()
