import copy
import json
import pathlib
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools'))
import verify_gorogan_trace as gate
GOOD=json.loads((ROOT/'examples'/'synthetic_pass.json').read_text())


def ev(doc, kind):
    return next(v for v in doc['events'] if v['kind']==kind)


def remove(doc, kind):
    doc['events']=[e for e in doc['events'] if e['kind']!=kind]
    for i,e in enumerate(doc['events']): e['seq']=i+1


class TraceTests(unittest.TestCase):
    def setUp(self): self.d=copy.deepcopy(GOOD)
    def assertBad(self,code):
        errors=gate.validate(self.d)
        self.assertTrue(any(x.startswith(code) for x in errors),(code,errors))

    def test_good(self): self.assertEqual([],gate.validate(self.d))
    def test_one_client(self): self.d['clients']=1;self.assertBad('CLIENTS_REQUIRE')
    def test_boolean_client(self): self.d['clients']=True;self.assertBad('CLIENTS_REQUIRE')
    def test_s2_disallowed(self): self.d['stage']='S2';self.assertBad('INVALID_STAGE')
    def test_published_disallowed(self): self.d['environment']='PUBLISHED';self.assertBad('INVALID_ENVIRONMENT')
    def test_auto_scheduler_disallowed(self): self.d['trigger_mode']='CLIENT_EVENT';self.assertBad('INVALID_TRIGGER_MODE')
    def test_invalid_run_id(self): self.d['run_id']='name of real player';self.assertBad('INVALID_RUN_ID')
    def test_source_hash(self): self.d['source_sha256']='AAAA';self.assertBad('INVALID_SOURCE_SHA256')
    def test_local_source_mismatch(self): self.d['evidence']['local_source_sha256']='d'*64;self.assertBad('LOCAL_SOURCE_SHA_MISMATCH')
    def test_local_place_mismatch(self): self.d['evidence']['saved_place_sha256']='f'*64;self.assertBad('SAVED_PLACE_SHA_MISMATCH')
    def test_log_sha_mismatch(self): self.d['evidence']['log_sha256']='f'*64;self.assertBad('LOG_SHA_MISMATCH')
    def test_exit_missing(self): self.d['evidence']['owned_studio_pid_exited']=False;self.assertBad('MISSING_OWNED_STUDIO')
    def test_save_missing(self): self.d['evidence']['stop_edit_save']=False;self.assertBad('MISSING_STOP_EDIT_SAVE')
    def test_seq_duplicate(self): ev(self.d,'HIT')['seq']=8;self.assertBad('INVALID_SEQ')
    def test_time_regression(self): ev(self.d,'HIT')['ms']=200;self.assertBad('INVALID_TIME')
    def test_authority_client(self): ev(self.d,'HIT')['authority']='CLIENT';self.assertBad('UNTRUSTED_AUTHORITY')
    def test_round_replay(self): ev(self.d,'HIT')['round_id']='OLD';self.assertBad('ROUND_MISMATCH')
    def test_trigger_not_server(self): ev(self.d,'TRIGGER')['source']='CLIENT';self.assertBad('INVALID_TRIGGER')
    def test_spawn_non_server_owned(self): ev(self.d,'SPAWN')['server_owned']=False;self.assertBad('INVALID_SPAWN')
    def test_root_anchored(self): ev(self.d,'MOVE_SAMPLE')['root_anchored']=True;self.assertBad('NOT_REAL_SERVER_MOVEMENT')
    def test_fake_client_pos(self): ev(self.d,'MOVE_SAMPLE')['source']='CLIENT_SENT_CFRAME';self.assertBad('NOT_REAL_SERVER_MOVEMENT')
    def test_teleport(self): ev(self.d,'MOVE_SAMPLE')['pos']=[999,0,0];self.assertBad('IMPLAUSIBLE_MOVEMENT_SPEED')
    def test_no_movement(self):
        for x in self.d['events']:
            if x['kind']=='MOVE_SAMPLE': x['pos']=[0,0,0]
        self.assertBad('NO_OBSERVED_PATHFINDING_MOVEMENT')
    def test_no_nav(self): remove(self.d,'NAV_REQUEST');self.assertBad('NO_OBSERVED_PATHFINDING_MOVEMENT')
    def test_boss_wrong_id(self): ev(self.d,'HIT')['boss_id']='OTHER_BOSS';self.assertBad('BOSS_ID_MISMATCH')
    def test_telegraph_blue_missing(self): ev(self.d,'TELEGRAPH')['visible_blue']=False;self.assertBad('TELEGRAPH_NOT_VISIBLE_BOTH_TEAMS')
    def test_telegraph_red_missing(self): ev(self.d,'TELEGRAPH')['visible_red']=False;self.assertBad('TELEGRAPH_NOT_VISIBLE_BOTH_TEAMS')
    def test_telegraph_under_2s(self): ev(self.d,'TELEGRAPH')['ms']=1500;self.assertBad('TELEGRAPH_NOT_2S')
    def test_fake_receipt(self): ev(self.d,'ATTACK_RESOLVE')['receipt']='CLIENT_FAKE';self.assertBad('NONCANONICAL_ATTACK_RECEIPT')
    def test_stale_roster(self): ev(self.d,'HIT')['server_roster_verified']=False;self.assertBad('UNAUTHORIZED_HIT')
    def test_wall_damage(self): ev(self.d,'HIT')['server_los']=False;self.assertBad('UNAUTHORIZED_HIT')
    def test_safezone_damage(self): ev(self.d,'HIT')['safezone']=True;self.assertBad('UNAUTHORIZED_HIT')
    def test_invulnerable_damage(self): ev(self.d,'HIT')['invulnerable']=True;self.assertBad('UNAUTHORIZED_HIT')
    def test_dead_damage(self): ev(self.d,'HIT')['target_alive']=False;self.assertBad('UNAUTHORIZED_HIT')
    def test_over_8_damage(self): ev(self.d,'HIT')['damage']=9;self.assertBad('INVALID_DAMAGE')
    def test_float_damage(self): ev(self.d,'HIT')['damage']=4.5;self.assertBad('INVALID_DAMAGE')
    def test_range_damage(self): ev(self.d,'HIT')['distance_studs']=15;self.assertBad('INVALID_HIT_DISTANCE')
    def test_duplicate_damage(self):
        self.d=json.loads((ROOT/'examples'/'synthetic_duplicate_damage_fail.json').read_text())
        self.assertBad('DUPLICATE_OR_INVALID_HIT_TARGET')
    def test_hit_without_resolve(self): remove(self.d,'ATTACK_RESOLVE');self.assertBad('HIT_WITHOUT_RECENT_RESOLVE')
    def test_no_hit(self): remove(self.d,'HIT');self.assertBad('NO_OBSERVED_TELEGRAPH_AND_HIT')
    def test_no_denied(self): remove(self.d,'HIT_DENIED');self.assertBad('MISSING_NEGATIVE_ATTACK_OR_REMOTE_TEST')
    def test_no_fake_remote_rejected(self): remove(self.d,'REMOTE_REJECTED');self.assertBad('MISSING_NEGATIVE_ATTACK_OR_REMOTE_TEST')
    def test_cleanup_ghost(self): ev(self.d,'CLEANUP')['boss_instances_remaining']=1;self.assertBad('INVALID_CLEANUP')
    def test_no_cleanup(self): remove(self.d,'CLEANUP');self.assertBad('MISSING_FINAL_CLEANUP')
    def test_exceed_14s(self): ev(self.d,'CLEANUP')['ms']=15000;self.assertBad('BOSS_TTL_EXCEEDED')
    def test_attack_too_late(self): ev(self.d,'ATTACK_RESOLVE')['ms']=9000;self.assertBad('TELEGRAPH_NOT_2S')
    def test_early_event(self):
        self.d['events'][0]['kind']='REMOTE_REJECTED'
        self.d['events'][0]['reason']='CLIENT_DAMAGE'
        self.assertBad('EVENT_BEFORE_ROUND_START')
    def test_kind_as_dict_no_crash(self): self.d['events'][0]['kind']={};self.assertBad('UNKNOWN_KIND')
    def test_seq_as_dict_no_crash(self): self.d['events'][0]['seq']={};self.assertBad('INVALID_SEQ')
    def test_attack_id_as_list_no_crash(self): ev(self.d,'ATTACK_RESOLVE')['attack_id']=[];self.assertBad('INVALID_OR_DUPLICATE_RESOLVE')
    def test_target_as_list_no_crash(self): ev(self.d,'HIT')['target_token']=[];self.assertBad('DUPLICATE_OR_INVALID_HIT_TARGET')
    def test_nonfinite_input_not_allowed(self): ev(self.d,'HIT')['distance_studs']=float('nan');self.assertBad('INVALID_HIT_DISTANCE')
    def test_no_source(self): self.d.pop('schema');self.assertBad('INVALID_SCHEMA')
    def test_event_limit(self): self.d['events']=[];self.assertBad('INVALID_EVENTS_COUNT')
    def test_no_round_start(self): remove(self.d,'ROUND_START');self.assertBad('MISSING_ROUND_START')
    def test_no_immutable_damage_id(self): ev(self.d,'HIT')['attack_id']='made-up';self.assertBad('HIT_WITHOUT_RECENT_RESOLVE')
    def test_second_spawn(self):
        x=copy.deepcopy(ev(self.d,'SPAWN'))
        self.d['events'].insert(3,x)
        for i,y in enumerate(self.d['events']):y['seq']=i+1
        self.assertBad('INVALID_SPAWN')
    def test_schema_unexpected_list(self): self.assertEqual(['ROOT_NOT_OBJECT'],gate.validate([]))
    def test_synthetic_fixture_is_not_studio(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'trace.json';p.write_text(json.dumps(self.d))
            code=gate.main([str(p),'--format','json'])
            self.assertEqual(0,code)

class ReadSafetyTests(unittest.TestCase):
    def test_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'x.json';p.write_text('{"a":1,"a":2}')
            with self.assertRaises(gate.InvalidTrace): gate.read_trace(p)
    def test_nan_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'x.json';p.write_text('{"a":NaN}')
            with self.assertRaises(gate.InvalidTrace): gate.read_trace(p)
    def test_too_large(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'x.json';p.write_bytes(b'x'*(gate.MAX_FILE+1))
            with self.assertRaises(gate.InvalidTrace): gate.read_trace(p)
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            t=pathlib.Path(td)/'true.json';t.write_text('{}')
            p=pathlib.Path(td)/'link.json'
            p.symlink_to(t)
            with self.assertRaises(gate.InvalidTrace): gate.read_trace(p)
    def test_fail_duplicate_damage_example(self):
        self.assertIn('DUPLICATE_OR_INVALID_HIT_TARGET',gate.validate(json.loads((ROOT/'examples'/'synthetic_duplicate_damage_fail.json').read_text())))
    def test_cli_fail_exit(self):
        p=ROOT/'examples'/'synthetic_duplicate_damage_fail.json'
        x=subprocess.run([sys.executable,str(ROOT/'tools'/'verify_gorogan_trace.py'),str(p),'--format','json'],capture_output=True,text=True,check=False)
        self.assertEqual(1,x.returncode)
        self.assertFalse(json.loads(x.stdout)['pass'])
    def test_cli_pass_exact_status(self):
        p=ROOT/'examples'/'synthetic_pass.json'
        x=subprocess.run([sys.executable,str(ROOT/'tools'/'verify_gorogan_trace.py'),str(p),'--format','json'],capture_output=True,text=True,check=False)
        self.assertEqual(0,x.returncode)
        self.assertEqual('SYNTHETIC_PASS_NOT_STUDIO_QA',json.loads(x.stdout)['status'])
    def test_studio_origin_not_proof(self):
        x=copy.deepcopy(GOOD);x['trace_origin']='STUDIO_SERVER_OUTPUT'
        self.assertEqual([],gate.validate(x))
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'x.json';p.write_text(json.dumps(x))
            s=subprocess.run([sys.executable,str(ROOT/'tools'/'verify_gorogan_trace.py'),str(p),'--format','json'],capture_output=True,text=True)
            self.assertEqual('TRACE_CONTRACT_PASS_NOT_STUDIO_QA',json.loads(s.stdout)['status'])
    def test_random_malicious_shapes_do_not_throw(self):
        rng=random.Random(22488)
        choices=[{}, [], 0, True, False, None, 'A', 'A'*300, -1, 99.3, float('nan')]
        for _ in range(900):
            d=copy.deepcopy(GOOD)
            i=rng.randrange(len(d['events']))
            key=rng.choice(['kind','seq','ms','attack_id','target_token','authority','round_id','boss_id','damage','pos'])
            d['events'][i][key]=rng.choice(choices)
            try: result=gate.validate(d)
            except Exception as exc: self.fail(f'malicious shape caused {exc}: index={i} key={key}')
            self.assertIsInstance(result,list)

if __name__=='__main__': unittest.main()
