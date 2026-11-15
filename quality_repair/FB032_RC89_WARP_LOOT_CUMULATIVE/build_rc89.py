#!/usr/bin/env python3
"""FB032 cumulative real Roblox Place: preserve exact native-pass RC88 + fix 2 StagePickupLoot wall bypasses.

This is PRIVATE Studio source, never an official RC or public Roblox publish.
"""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import hashlib, json, difflib, xml.etree.ElementTree as ET

HOME=Path(__file__).resolve().parent
PARENT=HOME/'parent_rc88.zip'
PARENT_SHA='e207a79b777d3b0814ec9580bc9f7ffaffeb07581d6b1010ac89b2846c2accd8'
PARENT_FILE='P0D_RC88_FB031_NATIVE86_WARP_PRIVATE.rbxlx'
OUTPUT=HOME/'P0D_RC89_WIDEFIELD_WARP_STAGE_LOOT_WALL_SAFE_PRIVATE.rbxlx'
STAGE_PATH='ServerScriptService/TrapRaidersS1/StagePickupLoot'
ORIGINAL_BLOB='3fb954f4bcc9d5728b55cc284e6519c304bd61c2'
EXPECTED_COUNT=86

def sha256(value):return hashlib.sha256(value).hexdigest()
def gitblob(s):
    b=s.encode('utf8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def repl(s,old,new,key):
    c=s.count(old)
    if c!=1:raise ValueError('SOURCE_DRIFT_'+key+':'+str(c))
    return s.replace(old,new,1)

def scan(root):
    entries={}
    def walk(item,base=()):
        p=item.find('Properties')
        n=p.findtext("string[@name='Name']") if p is not None else None
        parts=base+((n,) if n else ())
        node=next((e for e in p if e.attrib.get('name')=='Source'),None) if p is not None else None
        if node is not None:
            path='/'.join(parts)
            if path in entries:raise ValueError('DUPLICATE_SCRIPT_PATH_'+path)
            entries[path]={'item':item,'source':node,'body':node.text or '','class':item.attrib['class']}
        for sub in item.findall('Item'):walk(sub,parts)
    for obj in root.findall('Item'):walk(obj)
    return entries

GUARD='''-- FB032 original StageLoot wall/gate safety, using existing authoritative Game.
-- Ignore the caster and noncollidable pickup decorations, not solid gates.
local function unobstructed(player, fromPos, toPos, pickupModel)
    local params=RaycastParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    local excluded={}
    if player.Character then table.insert(excluded,player.Character) end
    if pickupModel then table.insert(excluded,pickupModel) end
    params.FilterDescendantsInstances=excluded
    params.RespectCanCollide=true
    return workspace:Raycast(fromPos,toPos-fromPos,params)==nil
end
'''

def patch(s):
    s=repl(s,'local function spawnPickup(parent,index,x,z,kind)',
           GUARD+'local function spawnPickup(parent,index,x,z,kind)','ADD_SERVER_LOS')
    s=repl(s,
           '        if (root.Position-base.Position).Magnitude>10 then return end\n        local now=workspace:GetServerTimeNow()',
           '''        if (root.Position-base.Position).Magnitude>10 then return end
        -- Do not award a weapon through an actual closed portcullis or solid wall.
        if not unobstructed(player,root.Position,
            base.Position+Vector3.new(0,1.3,0),model) then return end
        local now=workspace:GetServerTimeNow()''',
           'PICKUP_NOT_THROUGH_WALL')
    s=repl(s,
           '    return if v.Magnitude>.01 then origin+v.Unit*buff.reach else origin\nend',
           '''    if v.Magnitude<=.01 then return origin end
    local projected=origin+v.Unit*buff.reach
    -- Closed castle door must block the segment from original hit origin.
    if not unobstructed(player,origin,projected,nil) then return origin end
    return projected
end''',
           'HIT_ORIGIN_NOT_THROUGH_GATE')
    if s.count('local function unobstructed(')!=1 or s.count('workspace:Raycast(')!=1:
        raise ValueError('SECOND_LOS_IMPL')
    return s

def build(parent_bytes=None):
    if parent_bytes is None:
        with ZipFile(PARENT) as z:
            if sorted(z.namelist())!=[PARENT_FILE,'RC88_RECEIPT.json','patch_log.json']:
                raise ValueError('PARENT_CONTENT_DRIFT')
            parent_bytes=z.read(PARENT_FILE)
    if sha256(parent_bytes)!=PARENT_SHA or len(parent_bytes)!=846753:raise ValueError('WRONG_NATIVE_RC88_PARENT')
    root=ET.fromstring(parent_bytes);before=scan(root)
    if len(before)!=EXPECTED_COUNT:raise ValueError('WRONG_SCRIPT_COUNT')
    if STAGE_PATH not in before:raise ValueError('STAGE_PATH_NOT_FOUND')
    if gitblob(before[STAGE_PATH]['body'])!=ORIGINAL_BLOB:raise ValueError('STAGE_BLOB_DRIFT')
    source=before[STAGE_PATH]['body']
    after_stage=patch(source)
    before[STAGE_PATH]['source'].text=after_stage
    result=ET.tostring(root,encoding='utf-8')
    after=scan(ET.fromstring(result))
    if len(after)!=EXPECTED_COUNT or set(after)!=set(before):raise ValueError('AFTER_SCRIPTS_DRIFT')
    changed=[p for p in before if before[p]['body']!=after[p]['body']]
    if changed!=[STAGE_PATH]:raise ValueError('ILLEGAL_AUTHOR_CHANGE_'+repr(changed))
    if any(before[p]['class']!=after[p]['class'] for p in before):raise ValueError('SCRIPT_CLASS_DRIFT')
    if sum(p.endswith('/Game') for p in before)!=1 or sum(p.endswith('/TrapRaidersHUD') for p in before)!=1:
        raise ValueError('DOUBLE_GAME_HUD')
    game=before['ServerScriptService/TrapRaidersS1/Game']['body']
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert 'UndeadSquad' in game and 'StagePickupLoot' in game
    assert gitblob(before['ServerScriptService/TrapRaidersS1/TrapperWarpService']['body'])=='ef41f1d00ad418a2afe07cdb4cad2eeb3650290d'
    OUTPUT.write_bytes(result)
    manifest={p:{'class':v['class'],'blob':gitblob(v['body'])} for p,v in sorted(after.items())}
    (HOME/'SOURCE_LOCK.json').write_text(json.dumps({'total_scripts':86,'scripts':manifest},indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    (HOME/'RC_FEATURE_LOCK.json').write_text(json.dumps({'total_sources':86,'source_gitblobs':{'/'.join(p.split('/')[2:]):gitblob(v['body']) for p,v in sorted(after.items())}},indent=2)+'\n',encoding='utf8')
    (HOME/'STAGE_LOOT_ONLY.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),after_stage.splitlines(True),fromfile='rc88/StagePickupLoot',tofile='rc89/StagePickupLoot')),encoding='utf8')
    receipt={'feature':'FB032_RC89_WIDEFIELD_WARP_AND_STAGE_LOOT_WALL_SAFETY','parent_sha256':PARENT_SHA,
      'place_bytes':len(result),'place_sha256':sha256(result), 'scripts':86,
      'changed_scripts':[STAGE_PATH],'unchanged_scripts':85,'stage_orig_blob':ORIGINAL_BLOB,
      'stage_new_blob':gitblob(after_stage),'native_luau':'NOT_RUN','rojo':'NOT_RUN',
      'studio':'NOT_RUN','android':'NOT_RUN','official_rc_write':False,'owner_accepted':False,
      'product':'NO_GO'}
    (HOME/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return receipt

if __name__=='__main__':print(json.dumps(build(),indent=2,ensure_ascii=False))
