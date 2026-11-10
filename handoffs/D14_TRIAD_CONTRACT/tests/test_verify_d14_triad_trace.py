from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import verify_d14_triad_trace as m


def valid():
    return json.loads((ROOT/'examples'/'synthetic_cart_trace.json').read_text('utf-8'))

class TriadTests(unittest.TestCase):
    def setUp(self):
        self.d=valid()

    def expect(self,code, mutator):
        d=copy.deepcopy(self.d)
        mutator(d)
        with self.assertRaisesRegex(m.TraceError,code):
            m.validate(d)

    def test_sample(self):
        r=m.validate(self.d)
        self.assertEqual(r['events_checked'],14)
        self.assertEqual(r['pose_events'],6)
        self.assertEqual(r['visual_events'],2)
        self.assertEqual(r['studio_qa'],'NOT_ATTESTED_BY_THIS_TOOL')
    def test_valid_no_visual(self):
        self.d['events']=[x for x in self.d['events'] if x['type']!='VISUAL']
        r=m.validate(self.d)
        self.assertEqual(r['visual_events'],0)
    def test_valid_add_passenger(self):
        e=self.d['events'][1].copy()
        e.update(type='BOARD',player='p_guest2',seat='PASSENGER',seq=0,ms=0,alive=True,mounted=True,carrier=False,snared=False)
        self.d['events'].insert(2,e)
        for j,v in enumerate(self.d['events']):v['seq']=j+1
        for v in self.d['events']:
            if v['type']=='VISUAL':v['seat_count']=2;v['pose_seq']=v['pose_seq']+1
        self.assertEqual(m.validate(self.d)['visual_events'],2)
    def test_valid_with_disabled_passenger(self):
        e=self.d['events'][1].copy()
        e.update(type='BOARD',player='p_guest2',seat='PASSENGER',seq=0,ms=0,alive=True,mounted=True,carrier=False,snared=False)
        x={k:v for k,v in self.d['events'][1].items() if k in ('type','seq','ms','round_id','source','cart_id','team','player')}
        x.update(type='DISABLE',player='p_guest2',reason='DIED',seq=0,ms=0)
        self.d['events'].insert(2,e)
        self.d['events'].insert(3,x)
        for j,v in enumerate(self.d['events']):v['seq']=j+1
        for v in self.d['events']:
            if v['type']=='VISUAL':v['pose_seq']+=2
        self.assertEqual(m.validate(self.d)['pose_events'],6)
    def test_reject_wrong_game(self):self.expect('WRONG_PROJECT',lambda d:d.update(game_id='TOY_WARS'))
    def test_reject_wrong_work(self):self.expect('WRONG_PROJECT',lambda d:d.update(work_id='other'))
    def test_reject_wrong_schema(self):self.expect('WRONG_PROJECT',lambda d:d.update(schema='v2'))
    def test_reject_wrong_seat_sha(self):self.expect('WRONG_OR_SUPERSEDED_REFERENCE',lambda d:d['reference_commits'].update(seats='0'*40))
    def test_reject_superseded_motion(self):self.expect('WRONG_OR_SUPERSEDED_REFERENCE',lambda d:d['reference_commits'].update(motion=m.SUPERSEDED))
    def test_reject_bad_provenance(self):self.expect('BAD_PROVENANCE',lambda d:d.update(provenance='STUDIO_QA_PASS'))
    def test_reject_bad_round(self):self.expect('BAD_ROUND_ID',lambda d:d.update(round_id='../x'))
    def test_reject_duplicate_cart(self):self.expect('DUPLICATE_CART_ID',lambda d:d['routes'].append(copy.deepcopy(d['routes'][0])))
    def test_reject_second_same_team(self):
        def f(d):
            other=copy.deepcopy(d['routes'][0]);other['cart_id']='cartB';d['routes'].append(other)
        self.expect('DUPLICATE_OR_BAD_TEAM',f)
    def test_reject_too_many_routes(self):
        def f(d):
            for c in ['cartB','cartC']:
                x=copy.deepcopy(d['routes'][0]);x['cart_id']=c;x['team']='RED';d['routes'].append(x)
        self.expect('BAD_ROUTE_SET',f)
    def test_reject_bad_speed(self):self.expect('BAD_SPEED',lambda d:d['routes'][0].update(speed=19))
    def test_reject_bad_route_edge(self):self.expect('BAD_LEG_DISTANCE',lambda d:d['routes'][0].update(nodes=[[0,0,0],[3,0,0]]))
    def test_reject_nan_position(self):self.expect('BAD_POSITION',lambda d:d['routes'][0].update(nodes=[[0,0,0],[float('nan'),0,0]]))
    def test_reject_unknown_event(self):self.expect('UNKNOWN_EVENT_TYPE',lambda d:d['events'][1].update(type='TELEPORT'))
    def test_reject_client_board(self):self.expect('CLIENT_AUTHORITY_ATTEMPT',lambda d:d['events'][1].update(source='CLIENT_VIEW'))
    def test_reject_client_advance(self):self.expect('CLIENT_AUTHORITY_ATTEMPT',lambda d:d['events'][3].update(source='CLIENT_VIEW'))
    def test_reject_client_pose(self):self.expect('CLIENT_AUTHORITY_ATTEMPT',lambda d:d['events'][4].update(source='CLIENT_VIEW'))
    def test_reject_duplicate_sequence(self):self.expect('NONMONOTONIC_SEQUENCE',lambda d:d['events'][5].update(seq=5))
    def test_reject_time_reversal(self):self.expect('TIME_REGRESSION',lambda d:d['events'][5].update(ms=1))
    def test_reject_round_change(self):self.expect('CROSS_ROUND_EVENT',lambda d:d['events'][4].update(round_id='roundB'))
    def test_reject_egg_board(self):self.expect('INELIGIBLE_BOARD',lambda d:d['events'][1].update(carrier=True))
    def test_reject_snared_board(self):self.expect('INELIGIBLE_BOARD',lambda d:d['events'][1].update(snared=True))
    def test_reject_not_alive_board(self):self.expect('INELIGIBLE_BOARD',lambda d:d['events'][1].update(alive=False))
    def test_reject_double_board(self):
        def f(d):
            x=copy.deepcopy(d['events'][1]); x.update(seq=3);d['events'].insert(2,x)
            for i,v in enumerate(d['events']):v['seq']=i+1
            for v in d['events']:
                if v['type']=='VISUAL':v['pose_seq']+=1
        self.expect('DOUBLE_SEAT',f)
    def test_reject_wrong_team(self):self.expect('CART_TEAM_MISMATCH',lambda d:d['events'][3].update(team='RED'))
    def test_reject_wrong_player(self):self.expect('NON_DRIVER_COMMAND',lambda d:d['events'][3].update(player='p_fake'))
    def test_reject_command_replay(self):self.expect('REPLAY_COMMAND',lambda d:d['events'][7].update(command_seq=1))
    def test_reject_command_wrong_leg(self):self.expect('WRONG_LEG_REQUEST',lambda d:d['events'][3].update(leg=2))
    def test_reject_moving_without_command(self):
        def f(d):d['events'].pop(3);d['events']=[dict(x,seq=i+1) for i,x in enumerate(d['events'])]
        self.expect('MOVING_WITHOUT_SERVER_ADVANCE',f)
    def test_reject_speed_teleport(self):
        def f(d):d['events'][4]['ms']=20
        self.expect('EXCESSIVE_SPEED_OR_TELEPORT',f)
    def test_reject_off_rail(self):self.expect('OFF_RAIL_POSE',lambda d:d['events'][4].update(position=[5,0,10]))
    def test_reject_nonfinite_snapshot(self):self.expect('BAD_POSITION',lambda d:d['events'][4].update(position=[float('inf'),0,0]))
    def test_reject_progress_wrong(self):self.expect('BAD_POSE_PROGRESS',lambda d:d['events'][4].update(progress=1.5))
    def test_reject_initial_pose_wrong(self):self.expect('INVALID_INITIAL_POSE',lambda d:d['events'][2].update(moving=True))
    def test_reject_visual_bad_pose_seq(self):self.expect('STALE_OR_UNAUTHORIZED_VISUAL_POSE',lambda d:d['events'][5].update(pose_seq=3))
    def test_reject_visual_fake_seats(self):self.expect('VISUAL_SEAT_COUNT_MISMATCH',lambda d:d['events'][5].update(seat_count=2))
    def test_reject_raft_on_cart_route(self):self.expect('RAFT_NOT_THIS_CONTRACT',lambda d:d['events'][5].update(visual_kind='RAFT'))
    def test_reject_spoofed_visual_fields(self):self.expect('BAD_VISUAL_FIELDS',lambda d:d['events'][5].update(driver_id='victim'))
    def test_reject_extra_command_client_coords(self):self.expect('BAD_ADVANCE_FIELDS',lambda d:d['events'][3].update(x=1000))
    def test_reject_unboard_non_seat(self):self.expect('UNBOARD_NON_OCCUPANT',lambda d:d['events'][11].update(player='p_fake'))
    def test_reject_event_after_round_end(self):
        def f(d):
            x=copy.deepcopy(d['events'][12]);x['seq']=15;x['ms']=2060;d['events'].append(x)
        self.expect('ROUND_END_NOT_LAST',f)
    def test_reject_no_round_end(self):self.expect('ROUND_NOT_CLOSED',lambda d:d['events'].pop())
    def test_reject_moving_after_driver_removed(self):
        def f(d):
            e={k:v for k,v in d['events'][1].items() if k in ('type','seq','ms','round_id','source','cart_id','team','player')}
            e.update(type='DISABLE',reason='DIED',ms=600)
            d['events'].insert(6,e)
            # First CLIENT_VIEW still references old pose, so remove that visual;
            # the next moving POSE is disallowed after driver invalidation.
            d['events']=[v for v in d['events'] if v['type']!='VISUAL']
            for i,v in enumerate(d['events']):v['seq']=i+1
        self.expect('MOVEMENT_AFTER_DRIVER_INVALIDATION',f)

    def test_reject_driver_disconnect_then_advance(self):
        def f(d):
            d['events'][7]['player']='p_notdriver'
        self.expect('NON_DRIVER_COMMAND',f)

    def test_reject_untrusted_advance_speed(self):
        self.expect('BAD_ADVANCE_FIELDS',lambda d:d['events'][3].update(speed=999))

    def test_reject_wrong_client_cart_id(self):
        self.expect('UNKNOWN_CART',lambda d:d['events'][5].update(cart_id='fakeCart'))

    def test_reject_replay_visual_after_round_end(self):
        def f(d):
            v=copy.deepcopy(d['events'][9]);v.update(seq=15,ms=2060)
            d['events'].append(v)
        self.expect('ROUND_END_NOT_LAST',f)

    def test_reject_route_from_forged_user(self):
        self.expect('BAD_ROUTE_FIELDS',lambda d:d['routes'][0].update(client_points=[[999,0,0]]))

    def test_reject_malformed_duplicates(self):
        with self.assertRaisesRegex(m.TraceError,'DUPLICATE_JSON_KEY'):
            m.strict_loads('{"a":1,"a":2}')
    def test_reject_nonfinite_json(self):
        with self.assertRaisesRegex(m.TraceError,'NON_FINITE_JSON_CONSTANT'):
            m.strict_loads('{"x":NaN}')
    def test_cli_real_fixture(self):
        self.assertEqual(m.main([str(ROOT/'examples'/'synthetic_cart_trace.json')]),0)
    def test_cli_reject_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/'trace.json';x.symlink_to(ROOT/'examples'/'synthetic_cart_trace.json')
            self.assertEqual(m.main([str(x)]),2)
    def test_does_not_launch_studio_or_network(self):
        with patch('subprocess.run',side_effect=AssertionError('subprocess forbidden')):
            with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
                self.assertEqual(m.validate(self.d)['studio_qa'],'NOT_ATTESTED_BY_THIS_TOOL')

if __name__=='__main__':unittest.main()
