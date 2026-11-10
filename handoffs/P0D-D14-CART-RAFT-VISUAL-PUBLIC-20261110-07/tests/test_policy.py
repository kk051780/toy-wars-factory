import math
import random
import unittest
from reference.vehicle_visual import Policy


def packet(seq=0, kind='START', vehicleId='CART_1', vehicleType='CART', team='BLUE',
           driverOccupied=True, passengerOccupied=False, x=1.0,y=0.5,z=2.0,yawDeg=90.0,remainingMs=2000,roundId='R1'):
    return locals().copy()

class PolicyTest(unittest.TestCase):
    def setUp(self):
        self.s=Policy('R1')

    def test_create(self):
        a=self.s.ingest(packet())
        self.assertEqual(a[0]['op'], 'SPAWN')
        self.assertEqual(self.s.seq,0)

    def test_update(self):
        self.s.ingest(packet())
        self.assertEqual(self.s.ingest(packet(seq=1,kind='UPDATE', x=3))[0]['op'],'MOVE')
        self.assertEqual(self.s.items['CART_1']['x'],3)

    def test_stop(self):
        self.s.ingest(packet())
        self.assertEqual(self.s.ingest(packet(seq=1,kind='STOP'))[0]['op'],'REMOVE')
        self.assertFalse(self.s.items)

    def test_stop_unknown_advances(self):
        self.assertEqual(self.s.ingest(packet(seq=4,kind='STOP')),[])
        self.assertEqual(self.s.seq,4)

    def test_round_end(self):
        self.s.ingest(packet())
        self.assertEqual(self.s.ingest(packet(seq=2,kind='ROUND_END')),[{'op':'CLEAR'}])
        self.assertFalse(self.s.items)
        self.assertTrue(self.s.closed)
        self.assertEqual(self.s.ingest(packet(seq=3)),[])

    def test_client_close(self):
        self.s.ingest(packet())
        self.assertEqual(self.s.close(),[{'op':'CLEAR'}])
        self.assertEqual(self.s.close(),[])

    def test_start_raft_red(self):
        a=self.s.ingest(packet(vehicleType='RAFT',team='RED',driverOccupied=False,passengerOccupied=True))
        self.assertEqual(a[0]['presentation']['vehicleType'],'RAFT')

    def test_no_replay(self):
        self.s.ingest(packet(seq=11))
        self.assertEqual(self.s.ingest(packet(seq=10)),[])
        self.assertEqual(self.s.ingest(packet(seq=11)),[])

    def test_no_other_round(self):
        self.assertEqual(self.s.ingest(packet(roundId='R2')),[])
        self.assertEqual(self.s.seq,-1)

    def test_no_update_without_spawn(self):
        self.assertEqual(self.s.ingest(packet(kind='UPDATE')),[])
        self.assertEqual(self.s.seq,-1)

    def test_type_immutable(self):
        self.s.ingest(packet())
        self.assertEqual(self.s.ingest(packet(seq=1,vehicleType='RAFT')),[])
        self.assertEqual(self.s.seq,0)

    def test_team_immutable(self):
        self.s.ingest(packet())
        self.assertEqual(self.s.ingest(packet(seq=1,team='RED')),[])

    def test_max_instances(self):
        for i in range(4):
            self.assertTrue(self.s.ingest(packet(seq=i,vehicleId=f'V{i}')))
        self.assertEqual(self.s.ingest(packet(seq=4,vehicleId='V4')),[])
        self.assertEqual(self.s.seq,3)

    def test_after_stop_start_again(self):
        self.s.ingest(packet(seq=0))
        self.s.ingest(packet(seq=1,kind='STOP'))
        self.assertEqual(self.s.ingest(packet(seq=2))[0]['op'],'SPAWN')

    def test_round_id_constructor(self):
        for x in ('', 'bad/slash', 'not space', 3, None, 'a'*33):
            with self.subTest(x=x),self.assertRaises(ValueError): Policy(x)

    def test_bad_type(self):
        for val in ('BOAT','TANK','raft',''):
            with self.subTest(val=val):self.assertEqual(self.s.ingest(packet(vehicleType=val)),[])

    def test_bad_team(self):
        for val in ('GREEN','blue',None):
            with self.subTest(val=val):self.assertEqual(self.s.ingest(packet(team=val)),[])

    def test_bad_occupied(self):
        for key in ('driverOccupied','passengerOccupied'):
            for val in (0,1,None,'true'):
                with self.subTest(key=key,val=val):
                    p=packet();p[key]=val;self.assertEqual(self.s.ingest(p),[])

    def test_bad_vehicle_id(self):
        for val in ('', 'bad/ID', '../x', 'with space', 'x'*33, None,3):
            with self.subTest(val=val):self.assertEqual(self.s.ingest(packet(vehicleId=val)),[])

    def test_bad_sequence(self):
        for val in (-1,True,1.1,math.nan,math.inf,'2',2147483648):
            with self.subTest(val=val):self.assertEqual(self.s.ingest(packet(seq=val)),[])

    def test_bad_ttl(self):
        for val in (0,20001,1.0,True,math.inf,math.nan,None):
            with self.subTest(val=val):self.assertEqual(self.s.ingest(packet(remainingMs=val)),[])

    def test_bad_position(self):
        for k in ('x','y','z','yawDeg'):
            for val in (math.inf,math.nan,8193,-8193,'a',None):
                with self.subTest(key=k,val=val):
                    p=packet();p[k]=val;self.assertEqual(self.s.ingest(p),[])

    def test_yaw_limit(self):
        for x in (-361,361):self.assertEqual(self.s.ingest(packet(yawDeg=x)),[])
        self.assertTrue(self.s.ingest(packet(yawDeg=360)))

    def test_bad_kind(self):
        for kind in ('TELEPORT','OWN','',None):self.assertEqual(self.s.ingest(packet(kind=kind)),[])

    def test_no_mutation_from_return(self):
        output=self.s.ingest(packet())[0]
        output['presentation']['vehicleType']='RAFT'
        self.assertEqual(self.s.items['CART_1']['vehicleType'],'CART')

    def test_no_leak_after_stop(self):
        self.s.ingest(packet())
        self.s.ingest(packet(seq=2,kind='STOP'))
        self.assertFalse(self.s.items)

    def test_random_1500(self):
        rng=random.Random(23014)
        for i in range(1500):
            p=packet(seq=i,vehicleId='V'+str(rng.randrange(7)),kind=rng.choice(['START','STOP','UPDATE']),
                     vehicleType=rng.choice(['CART','RAFT']), team=rng.choice(['BLUE','RED']))
            self.s.ingest(p)
            self.assertLessEqual(len(self.s.items),4)
            self.assertLessEqual(self.s.seq,i)
            self.assertTrue(all(x in ('CART','RAFT') for x in (v['vehicleType'] for v in self.s.items.values())))
        self.assertEqual(len(self.s.ingest(packet(seq=2000,kind='ROUND_END'))),1)
        self.assertFalse(self.s.items)

if __name__=='__main__':unittest.main()
