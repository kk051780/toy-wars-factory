#!/usr/bin/env python3
"""Regenerate anonymous public synthetic examples. Not gameplay source."""
from pathlib import Path
import json
from copy import deepcopy

ROOT=Path(__file__).resolve().parent.parent
R='ROUND_SYNTH_001'
events=[]
def add(kind,ms,**kw):
    if kind in {'NAV_REQUEST','MOVE_SAMPLE','TELEGRAPH','ATTACK_RESOLVE','HIT','HIT_DENIED','CLEANUP'}:
        kw.setdefault('boss_id','BOSS_SYNTH')
    events.append({'seq':len(events)+1,'ms':ms,'kind':kind,'authority':'SERVER','round_id':R,**kw})
add('ROUND_START',0)
add('TRIGGER',50,mode='SERVER_QA_ONLY',source='SERVER_TEST_COMMAND')
add('SPAWN',100,boss_id='BOSS_SYNTH',server_owned=True,pos=[0.0,0.0,0.0])
add('NAV_REQUEST',150,mechanism='PATHFINDING_MOVETO')
add('MOVE_SAMPLE',350,pos=[0.5,0,0],source='SERVER_HUMANOID_ROOT',server_owned=True,grounded=True,root_anchored=False)
add('MOVE_SAMPLE',700,pos=[1.4,0,0],source='SERVER_HUMANOID_ROOT',server_owned=True,grounded=True,root_anchored=False)
add('TELEGRAPH',1000,attack_id='A_SYNTH_1',visible_blue=True,visible_red=True)
add('ATTACK_RESOLVE',3200,attack_id='A_SYNTH_1',receipt='CORE_STOMP_RESOLVE',fresh_server_snapshot=True)
add('HIT',3201,attack_id='A_SYNTH_1',target_token='ANON_P1',damage=8,server_los=True,safezone=False,invulnerable=False,target_alive=True,server_roster_verified=True,distance_studs=6,max_range_studs=12)
add('HIT_DENIED',3202,attack_id='A_SYNTH_1',reason='SAFEZONE')
add('REMOTE_REJECTED',3203,reason='CLIENT_DAMAGE')
add('ROUND_END',10100)
add('CLEANUP',10110,boss_instances_remaining=0)
trace={
  'schema':'P0D_GOROGAN_STUDIO_TRACE_V1',
  'game_id':'TRAP_RAIDERS','work_id':'p0d-siege-v19','feature_id':'D07','stage':'S1',
  'environment':'UNPUBLISHED_STUDIO','trigger_mode':'SERVER_QA_ONLY',
  'round_id':R,'run_id':'RUN_SYNTH_001','clients':2,'trace_origin':'SYNTHETIC',
  'place_sha256':'a'*64,'source_sha256':'b'*64,'output_sha256':'c'*64,
  'evidence':{'stop_edit_save':True,'owned_studio_pid_exited':True,'saved_place_sha256':'a'*64,'log_sha256':'c'*64,'local_source_sha256':'b'*64},
  'events':events
}
(ROOT/'examples'/'synthetic_pass.json').write_text(json.dumps(trace,indent=2,sort_keys=True)+'\n')
bad=deepcopy(trace)
bad['events'].insert(9,deepcopy(bad['events'][8]))
for i,x in enumerate(bad['events']): x['seq']=i+1
(ROOT/'examples'/'synthetic_duplicate_damage_fail.json').write_text(json.dumps(bad,indent=2,sort_keys=True)+'\n')
