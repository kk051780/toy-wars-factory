#!/usr/bin/env python3
"""Deterministic and strict original D18 gallery story beat generator."""
import json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/'data/story_beats.json').read_text('utf-8'))
ids=[x['id'] for x in raw['steps']]
assert raw['schema']=='P0D_D18_STORY_BEATS_V1' and len(ids)==10 and len(set(ids))==10
assert raw['pose_for_chapter']==['idle','loss','win']
lines=['-- GENERATED from data/story_beats.json. Pure client-only narrative data.', '-- No server awards, inventory, timers, networking or paid elements.', 'local BEATS = {']
for row in raw['steps']:
    assert len(row['beats'])==3
    for s in row['beats']:
        assert isinstance(s,str) and 6<=len(s)<=64 and '\n' not in s
    name=json.dumps(row['id'],ensure_ascii=False)
    beats=', '.join(json.dumps(s,ensure_ascii=False) for s in row['beats'])
    lines.append('    ['+name+'] = {'+beats+'},')
lines += ['}', 'local POSES = {"idle", "loss", "win"}', 'local Story = {}',
'function Story.get(id, chapter)',
'    if type(id) ~= "string" or type(chapter) ~= "number" or chapter % 1 ~= 0 or chapter < 1 or chapter > 3 then return nil end',
'    local lines = BEATS[id]',
'    if not lines then return nil end',
'    return { id = id, chapter = chapter, total = 3, text = lines[chapter], pose = POSES[chapter] }',
'end',
'function Story.next(chapter)',
'    if type(chapter) ~= "number" or chapter % 1 ~= 0 or chapter < 1 or chapter > 3 then return nil end',
'    return chapter % 3 + 1',
'end',
'function Story.count()',
'    local count = 0',
'    for _ in pairs(BEATS) do count += 1 end',
'    return count',
'end',
'return Story','']
result='\n'.join(lines)
p=ROOT/'src/D18StoryBeats.luau'
if '--check' in sys.argv:
    if not p.is_file() or p.read_text('utf-8')!=result:
        sys.exit('STORY_GENERATION_MISMATCH')
    print('STORY_GENERATION_EXACT_10x3_PASS')
else:
    p.write_text(result,encoding='utf-8')
    print('STORY_GENERATED_10x3')
