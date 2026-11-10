"""Negative/fail-closed validation of the D14 rider-mount decision contract."""
import copy
from dataclasses import replace
import random
import unittest
from reference.rider_mount_model import Actor,RiderModel,snapshot

DRIVER=Actor('DRIVER',100,1,1,'BLUE')
PASSENGER=Actor('PASSENGER',101,2,1,'BLUE')

class RiderMountTests(unittest.TestCase):
    def setUp(self):self.r=RiderModel()
    def start(self,driver=DRIVER,passenger=PASSENGER):
        return self.r.update(snapshot(driver=driver,passenger=passenger),1000)
    def test_initial_two_mounts(self):
        out=self.start();self.assertTrue(out['ok']);self.assertEqual([x['role'] for x in out['mounts']],['DRIVER','PASSENGER'])
    def test_one_driver(self):self.assertEqual(len(self.start(passenger=None)['mounts']),1)
    def test_empty_seats(self):self.assertEqual(self.start(driver=None,passenger=None)['mounts'],[])
    def test_fresh_sync_does_not_remount(self):
        self.start();o=self.r.update(snapshot(seq=2,now=1100,passenger=PASSENGER),1100);self.assertEqual(o['mounts'],[]);self.assertEqual(o['unmounts'],[])
    def test_old_seq(self):self.start();self.assertEqual(self.r.update(snapshot(seq=1,now=1100),1100)['reason'],'REPLAY_OR_OLD_EPOCH')
    def test_regressed_epoch(self):
        self.start();self.assertTrue(self.r.update(snapshot(epoch=2,seq=1,now=1200,driver=replace(DRIVER,seatEpoch=2),passenger=replace(PASSENGER,seatEpoch=2)),1200)['ok']);self.assertEqual(self.r.update(snapshot(seq=3,now=1250),1250)['reason'],'REPLAY_OR_OLD_EPOCH')
    def test_new_epoch_forces_release_and_mount(self):
        self.start();out=self.r.update(snapshot(epoch=2,seq=2,now=1200,driver=replace(DRIVER,seatEpoch=2),passenger=replace(PASSENGER,seatEpoch=2)),1200);self.assertEqual(len(out['unmounts']),2);self.assertEqual(len(out['mounts']),2)
    def test_driver_change_but_same_epoch(self):
        self.start();out=self.r.update(snapshot(seq=2,now=1200,driver=replace(DRIVER,userId=102),passenger=PASSENGER),1200);self.assertEqual([x['role'] for x in out['unmounts']],['DRIVER'])
    def test_passenger_left(self):self.start();self.assertEqual(len(self.r.update(snapshot(seq=2,now=1200,passenger=None),1200)['unmounts']),1)
    def test_driver_left_requires_no_passenger(self):
        self.start();self.assertEqual(self.r.update(snapshot(seq=2,now=1200,driver=None,passenger=PASSENGER),1200)['reason'],'INVALID_ROSTER')
    def test_full_unseat_explicit(self):self.start();self.assertEqual(len(self.r.update(snapshot(seq=2,now=1200,driver=None,passenger=None),1200)['unmounts']),2)
    def test_duplicate_actor_rejected(self):
        self.assertEqual(self.start(passenger=replace(PASSENGER,userId=100))['reason'],'INVALID_ROSTER')
    def test_dead_driver_rejected(self):
        self.assertEqual(self.start(driver=replace(DRIVER,alive=False))['reason'],'INVALID_ROSTER')
    def test_dead_passenger_rejected(self):
        self.assertEqual(self.start(passenger=replace(PASSENGER,alive=False))['reason'],'INVALID_ROSTER')
    def test_changed_team(self):
        self.assertEqual(self.start(passenger=replace(PASSENGER,team='RED'))['reason'],'INVALID_ROSTER')
    def test_too_far(self):
        self.assertEqual(self.start(driver=replace(DRIVER,distanceStuds=8.01))['reason'],'INVALID_ROSTER')
    def test_negative_distance(self):self.assertEqual(self.start(driver=replace(DRIVER,distanceStuds=-1))['reason'],'INVALID_ROSTER')
    def test_nan_distance(self):self.assertEqual(self.start(driver=replace(DRIVER,distanceStuds=float('nan')))['reason'],'INVALID_ROSTER')
    def test_has_egg(self):self.assertEqual(self.start(driver=replace(DRIVER,hasEgg=True))['reason'],'INVALID_ROSTER')
    def test_snared(self):self.assertEqual(self.start(driver=replace(DRIVER,isSnared=True))['reason'],'INVALID_ROSTER')
    def test_rewinding(self):self.assertEqual(self.start(driver=replace(DRIVER,isRewinding=True))['reason'],'INVALID_ROSTER')
    def test_gliding(self):self.assertEqual(self.start(driver=replace(DRIVER,isGliding=True))['reason'],'INVALID_ROSTER')
    def test_not_seated(self):self.assertEqual(self.start(driver=replace(DRIVER,isSeated=False))['reason'],'INVALID_ROSTER')
    def test_missing_driver_character_epoch(self):self.assertEqual(self.start(driver=replace(DRIVER,characterEpoch=0))['reason'],'INVALID_ROSTER')
    def test_wrong_seat_epoch(self):self.assertEqual(self.start(passenger=replace(PASSENGER,seatEpoch=2))['reason'],'INVALID_ROSTER')
    def test_stage_s3_rejected(self):self.assertEqual(self.r.update(snapshot(stage='S3'),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_cart_supported(self):
        r=RiderModel(vehicle_type='CART');self.assertTrue(r.update(snapshot(vehicle_type='CART'),1000)['ok'])
    def test_wrong_vehicle_type(self):self.assertEqual(self.r.update(snapshot(vehicle_type='CART'),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_wrong_vehicle_id(self):self.assertEqual(self.r.update(snapshot(vehicle_id='other'),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_wrong_round_stops(self):
        self.start();o=self.r.update(snapshot(round_id='newround',seq=2),1200);self.assertEqual(o['reason'],'ROUND_CHANGED');self.assertEqual(len(o['unmounts']),2);self.assertTrue(self.r.closed)
    def test_closed_rejects_new_updates(self):
        self.r.close();self.assertEqual(self.r.update(snapshot(),1000)['reason'],'CLOSED')
    def test_nonpositive_time(self):self.assertEqual(self.r.update(snapshot(),-1)['reason'],'INVALID_OR_REWOUND_CLOCK')
    def test_clock_rollback(self):self.start();self.assertEqual(self.r.update(snapshot(seq=2,now=900),900)['reason'],'INVALID_OR_REWOUND_CLOCK')
    def test_timestamp_future(self):self.assertEqual(self.r.update(snapshot(now=1100),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_stale_timestamp(self):self.assertEqual(self.r.update(snapshot(now=100),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_age_boundary(self):self.assertTrue(self.r.update(snapshot(now=650),1000)['ok'])
    def test_age_over(self):self.assertEqual(self.r.update(snapshot(now=649),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_timestamp_not_int(self):self.assertEqual(self.r.update(snapshot(now=1000.5),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_seq_boolean_invalid(self):self.assertEqual(self.r.update(snapshot(seq=True),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_epoch_boolean_invalid(self):self.assertEqual(self.r.update(snapshot(epoch=True),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_bad_team(self):self.assertEqual(self.r.update(snapshot(team='RED/BLUE'),1000)['reason'],'INVALID_AUTHORITY_SNAPSHOT')
    def test_round_closed_reject(self):self.assertEqual(self.r.update(snapshot(round_open=False),1000)['reason'],'ROUND_CLOSED')
    def test_expire_watchdog(self):
        self.start();self.assertEqual(len(self.r.watchdog(2499)['unmounts']),0);self.assertEqual(len(self.r.watchdog(2500)['unmounts']),2)
    def test_expire_one_time(self):self.start();self.r.watchdog(2500);self.assertEqual(self.r.watchdog(2501)['unmounts'],[])
    def test_watchdog_time_rollback(self):self.start();self.assertEqual(self.r.watchdog(900)['reason'],'TIME_ROLLBACK')
    def test_watchdog_closed(self):self.r.close();self.assertEqual(self.r.watchdog(1000)['reason'],'CLOSED')
    def test_invalid_snapshot_does_not_mount(self):self.assertEqual(self.r.update(None,1000)['mounts'],[])
    def test_invalid_snapshot_still_leases_out(self):
        self.start();self.r.update(None,1100);self.assertEqual(len(self.r.watchdog(2500)['unmounts']),2)
    def test_same_identity_new_character_mount(self):
        self.start();o=self.r.update(snapshot(seq=2,now=1100,driver=replace(DRIVER,characterEpoch=3),passenger=PASSENGER),1100);self.assertEqual(len(o['mounts']),1);self.assertEqual(len(o['unmounts']),1)
    def test_one_character_cannot_occupy_both_even_role_change(self):self.assertEqual(self.start(passenger=replace(PASSENGER,userId=100,characterEpoch=2))['reason'],'INVALID_ROSTER')
    def test_round_closed_immediate_unmount(self):
        self.start()
        o=self.r.update(snapshot(seq=2,now=1150,round_open=False,passenger=PASSENGER),1150)
        self.assertEqual(o['reason'],'ROUND_CLOSED')
        self.assertEqual(len(o['unmounts']),2)
        self.assertTrue(self.r.closed)
    def test_dead_driver_immediate_unmount(self):
        self.start()
        o=self.r.update(snapshot(seq=2,now=1200,driver=replace(DRIVER,alive=False),passenger=PASSENGER),1200)
        self.assertEqual(o['reason'],'INVALID_ROSTER')
        self.assertEqual(len(o['unmounts']),2)
    def test_team_change_immediate_unmount(self):
        self.start()
        o=self.r.update(snapshot(seq=2,now=1200,driver=DRIVER,passenger=replace(PASSENGER,team='RED')),1200)
        self.assertEqual(len(o['unmounts']),2)
    def test_invalid_roster_cannot_replay_immediately(self):
        self.start()
        self.r.update(snapshot(seq=2,now=1200,driver=replace(DRIVER,alive=False),passenger=PASSENGER),1200)
        self.assertEqual(self.r.update(snapshot(seq=2,now=1220,passenger=PASSENGER),1220)['reason'],'REPLAY_OR_OLD_EPOCH')
    def test_fresh_revocation_then_renewal(self):
        self.start()
        self.r.update(snapshot(seq=2,now=1200,driver=replace(DRIVER,alive=False),passenger=PASSENGER),1200)
        o=self.r.update(snapshot(seq=3,now=1250,passenger=PASSENGER),1250)
        self.assertEqual(len(o['mounts']),2)
    def test_closed_release_idempotent(self):
        self.start();self.assertEqual(len(self.r.close()['unmounts']),2);self.assertEqual(self.r.close()['unmounts'],[])
    def test_same_round_wrong_vehicle_id_does_not_close(self):
        self.start();self.r.update(snapshot(vehicle_id='other',seq=2,now=1200),1200);self.assertFalse(self.r.closed)
    def test_new_seq_releases_occupancy_lost(self):
        self.start();o=self.r.update(snapshot(seq=2,now=1200,driver=DRIVER,passenger=None),1200);self.assertEqual(o['unmounts'][0]['userId'],101)
    def test_fuzz_stable_authority(self):
        rng=random.Random(15042);self.start();seq=1;now=1000
        for _ in range(2500):
            now+=rng.randint(1,5);seq+=1
            passenger=PASSENGER if rng.random()>.05 else None
            driver=DRIVER if rng.random()>.05 else None
            if driver is None:passenger=None
            o=self.r.update(snapshot(seq=seq,now=now,driver=driver,passenger=passenger),now)
            self.assertTrue(o['ok'])
            self.assertLessEqual(len([a for a in self.r.slots.values() if a]),2)
            self.assertTrue(self.r.slots['DRIVER'] or not self.r.slots['PASSENGER'])
    def test_fuzz_replay_cannot_duplicate(self):
        rng=random.Random(999);self.start();seq=1
        for _ in range(300):
            now=1000+rng.randint(1,200)
            o=self.r.update(snapshot(seq=seq,now=now),now)
            self.assertFalse(o['ok']);self.assertEqual(o['mounts'],[])

if __name__=='__main__':unittest.main()
