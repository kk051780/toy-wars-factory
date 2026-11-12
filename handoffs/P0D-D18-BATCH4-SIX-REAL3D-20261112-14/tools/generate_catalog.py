#!/usr/bin/env python3
"""Fail-closed D18 6-category original source-only model catalog generator."""
import argparse
import json
import math
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/six_pilot_geometry.json'
RULES=ROOT/'data/archetype_rules.json'
REGISTRY=ROOT/'data/flagship72_registry.json'
QUEUE=ROOT/'data/next54_source_queue.json'
CLAIMS=ROOT/'data/batch_claims.json'
OUT=ROOT/'src/D18BatchCatalog.luau'
CATEGORIES={'BE','SP','VE','WE','ZO','TR'}
POSES={'idle','tap','win','loss'}
SHAPES={'Ball','Block','Cylinder'}
def error(msg):raise ValueError(msg)
def numeric(v,low,high):
    return type(v) in (int,float) and math.isfinite(v) and low<=v<=high

def validate(data,rules,registry,queue,claims):
    if data.get('schema')!='P0D_D18_SIX_ARCHETYPE_SOURCE_V1':error('schema')
    if claims.get('schema')!='P0D_D18_BATCH_CLAIM_V1':error('claims schema')
    if data.get('game_id')!='TRAP_RAIDERS':error('game id')
    if rules.get('schema')!='P0D_D18_ARCHETYPE_RULES_V1':error('rules schema')
    if registry.get('schema')!='P0D_D18_FLAGSHIP72_SOURCE_REGISTRY_V1':error('registry schema')
    if queue.get('schema')!='P0D_D18_NEXT54_SOFT_CLAIM_QUEUE_V1':error('queue schema')
    sha=registry['source_atlas_sha256']
    if any(v.get('source_atlas_sha256')!=sha for v in (data,queue,claims)):error('source sha mismatch')
    chars=data['characters']
    prior=set(claims['previous_3d_source_ids'])
    new=set(claims['new_3d_source_ids'])
    if not 1<=len(new)<=6 or not prior.isdisjoint(new) or set(chars)!=new:error('claim ids must be 1..6 new canon IDs')
    if not isinstance(claims.get('soft_claim_issue_url'),str) or '#issuecomment-' not in claims['soft_claim_issue_url']:error('missing soft claim receipt')
    if len(registry['entries'])!=72 or len({x['id'] for x in registry['entries']})!=72:error('canonical 72')
    canon={x['id']:x for x in registry['entries']}
    if len({x['category'] for x in registry['entries']})!=6:error('canonical 6 categories')
    if any(sum(x['category']==cat for x in registry['entries'])!=12 for cat in CATEGORIES):error('canonical class 12 count')
    if set(rules['archetypes'])!={c['archetype'] for c in chars.values()}:error('archetypes/claims mismatch')
    if set(queue['previous_3d_source_ids'])!=prior or set(queue['current_batch_ids'])!=new:error('queue/claim receipts mismatch')
    if not prior<=set(canon) or not new<=set(canon):error('claim not canonical')
    if claims.get('estimated_total_source_after_batch')!=len(prior)+len(new):error('inconsistent source count')
    q=[x for v in queue['groups'].values() for x in v]
    expected_unclaimed=set(canon)-prior-new
    if len(q)!=len(expected_unclaimed) or len({x['id'] for x in q})!=len(q) or {x['id'] for x in q}!=expected_unclaimed:error('full remaining queue')
    if queue.get('remaining_source_not_started_count')!=len(q):error('remaining count')
    if set(queue['groups'])!=CATEGORIES or any(x['category']!=group for group,rows in queue['groups'].items() for x in rows):error('queue grouping')
    if any(x['status']!='NOT_STARTED_3D_SOURCE' or x['soft_claim']!='NONE' for x in q):error('queue unclaimed')
    for item in q:
        o=canon[item['id']]
        if any(item[k]!=o[k] for k in ('name','world','category','rarity')):error('queue canon metadata')
    for rid,c in chars.items():
        if not re.fullmatch(r'TRCA-(BE|SP|VE|WE|ZO|TR)-\d{3}',rid) or c.get('id')!=rid:error('ID format')
        original=canon[rid]
        if any(c.get(k)!=original[k] for k in ('name','category','world','rarity')):error('canonical identity '+rid)
        if c.get('category')!=rid[5:7]:error('id category conflict')
        if c.get('provenance',{}).get('atlas_sha256')!=sha:error('source pin '+rid)
        rule=rules['archetypes'][c['archetype']]
        if rule['category']!=c['category'] or rule['signature_tags']!=c['signature_tags']:error('archetype signature mismatch '+rid)
        if len(c['signature_tags'])!=3 or len(set(c['signature_tags']))!=3:error('three unique signature roles '+rid)
        if not isinstance(c.get('story'),str) or len(c['story'])<5:error('story hook '+rid)
        if not isinstance(c.get('signature_silhouette'),str) or len(c['signature_silhouette'])<15:error('original silhouette '+rid)
        palette=c.get('palette',{})
        if not isinstance(palette,dict) or not 3<=len(palette)<=6:error('palette limit')
        for rgb in palette.values():
            if not isinstance(rgb,list) or len(rgb)!=3 or any(type(x)!=int or not 0<=x<=255 for x in rgb):error('rgb out of bounds '+rid)
        parts=c.get('parts',[])
        if not isinstance(parts,list) or not 8<=len(parts)<=min(30,rule['near_max']):error('near part budget '+rid)
        far=[p for p in parts if p.get('far') is True]
        if not 6<=len(far)<=min(18,rule['far_max']):error('far part budget '+rid)
        seen=set()
        for p in parts:
            if set(p)!=set(rules['required_field_per_part']):error('unexpected part fields')
            if not isinstance(p['name'],str) or p['name'] in seen or len(p['name'])>32:error('duplicate/oversize part names')
            seen.add(p['name'])
            if p['shape'] not in SHAPES or p['color'] not in palette or type(p['far'])!=bool:error('part shape/color/far invalid')
            if not isinstance(p['signature_tag'],str) or not isinstance(p['group'],str):error('part tag/group')
            for key,lo,hi in [('size',.06,6),('position',-8,8),('rotation',-180,180)]:
                v=p[key]
                if not isinstance(v,list) or len(v)!=3 or any(not numeric(x,lo,hi) for x in v):error('part '+key+' bounds')
        kept={p['signature_tag'] for p in far}
        if not set(c['signature_tags'])<=kept:error('far 3 silhouette role loss '+rid)
        if set(c['pose_offsets'])!=POSES:error('missing poses')
        groups={p['group'] for p in parts}
        for pose,offsets in c['pose_offsets'].items():
            if not isinstance(offsets,dict):error('pose group')
            for group,vec in offsets.items():
                if group not in groups or set(vec)-{'dx','dy','dz','rz'}:error('unknown pose group/vector')
                if any(not numeric(value,-30 if key=='rz' else -.5,30 if key=='rz' else .5) for key,value in vec.items()):error('pose bounds')
    return True

def lua(obj,indent=0):
    pad=' '*indent
    if obj is None:return 'nil'
    if type(obj)==bool:return 'true' if obj else 'false'
    if type(obj) in (int,float):return str(obj)
    if isinstance(obj,str):return json.dumps(obj,ensure_ascii=False)
    if isinstance(obj,list):return '{\n'+''.join(' '*(indent+4)+lua(v,indent+4)+',\n' for v in obj)+pad+'}'
    if isinstance(obj,dict):return '{\n'+''.join(' '*(indent+4)+'['+lua(str(k))+'] = '+lua(obj[k],indent+4)+',\n' for k in sorted(obj))+pad+'}'
    raise TypeError(type(obj))

def generate():
    data=json.loads(DATA.read_text(encoding='utf8'))
    rules=json.loads(RULES.read_text(encoding='utf8'))
    registry=json.loads(REGISTRY.read_text(encoding='utf8'))
    queue=json.loads(QUEUE.read_text(encoding='utf8'))
    claims=json.loads(CLAIMS.read_text(encoding='utf8'))
    validate(data,rules,registry,queue,claims)
    return ('-- P0D D18: six distinct manually-authored V4 tactical archetype flagship source-only previews.\n'
      '-- GENERATED, DO NOT EDIT. python tools/generate_catalog.py --check\n'
      '-- No Roblox entitlement, combat, spawning, persistent inventory or reward logic.\n'
      'local C = {}\nlocal DEFINITIONS = '+lua(data['characters'])+'\n'
      'function C.get(id)\n    if type(id) ~= "string" then return nil end\n    return DEFINITIONS[id]\nend\n'
      'function C.ids()\n    return '+lua(sorted(data['characters']))+'\nend\n'
      'return C\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    v=generate()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding='utf8')!=v:raise SystemExit('CATALOG_MISMATCH')
        print('CATALOG_EXACT_PASS ids='+str(len(json.loads(DATA.read_text(encoding='utf8'))['characters']))+' source_only=true')
    else:
        OUT.write_text(v,encoding='utf8');print('CATALOG_GENERATED',OUT)
