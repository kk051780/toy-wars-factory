#!/usr/bin/env python3
"""FB030: source-exact anti-wall-bypass repair of real PRIVATE RC86 StagePickupLoot.

Keep the original Game/HUD, castle, egg, horde and 85 other script bodies byte exact;
only replace one existing ModuleScript. Private preview; not official adoption.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, difflib, xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
PARENT = HERE / 'parent_rc86_ci.zip'
PARENT_SHA = 'b614def362c7dad77341e75b568ab153e3001b9a146defe93ff2e9fa94f0dc6d'
OUTPUT = HERE / 'P0D_RC86_STAGE_WEAPONS_UNDEAD_WIND_WALL_SAFE_PRIVATE.rbxlx'
TARGET = 'StagePickupLoot'
TARGET_PATH = 'server/StagePickupLoot.luau'

def sha(data):return hashlib.sha256(data).hexdigest()
def blob(source):
    data=source.encode('utf8')
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def replace_once(source,old,new,label):
    count=source.count(old)
    if count!=1:raise ValueError(f'SOURCE_DRIFT_{label}_COUNT_{count}')
    return source.replace(old,new,1)

def source_nodes(root):
    nodes={}
    for item in root.iter('Item'):
        props=item.find('Properties')
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        src=props.find("ProtectedString[@name='Source']")
        if src is None:src=props.find("string[@name='Source']")
        if name and src is not None:
            if name in nodes:raise ValueError('SOURCE_DRIFT_DUPLICATE_'+name)
            nodes[name]=src
    return nodes

GUARD = '''-- FB030 wall/gate safety: server-only line of sight, not a client claim.
-- Ignore the caster's body and noncollidable decoration, but never castle solids.
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

def patch(src):
    src=replace_once(src,'local function spawnPickup(parent,index,x,z,kind)',
         GUARD+'local function spawnPickup(parent,index,x,z,kind)',
         'NEW_SHARED_SERVER_LOS_HELPER')
    src=replace_once(src,
       '        if (root.Position-base.Position).Magnitude>10 then return end\n        local now=workspace:GetServerTimeNow()',
       '''        if (root.Position-base.Position).Magnitude>10 then return end
        -- No grabbing a weapon through closed castle doors or solid cover.
        if not unobstructed(player,root.Position,
            base.Position+Vector3.new(0,1.3,0),model) then return end
        local now=workspace:GetServerTimeNow()''',
       'WORLD_PICKUP_BLOCKED_WALL')
    src=replace_once(src,
       '    return if v.Magnitude>.01 then origin+v.Unit*buff.reach else origin\nend',
       '''    if v.Magnitude<=.01 then return origin end
    local projected=origin+v.Unit*buff.reach
    -- A spear cannot move the melee attack origin through a closed portcullis.
    -- If projected reach crosses solid geometry, retain the original origin;
    -- the existing Horde:hit LOS check then remains authoritative.
    if not unobstructed(player,origin,projected,nil) then return origin end
    return projected
end''',
       'WEAPON_REACH_BLOCKED_WALL')
    if src.count('local function unobstructed(')!=1:raise ValueError('DUPLICATE_LOS')
    if src.count('workspace:Raycast(')!=1:raise ValueError('SECOND_RAYCAST_OWNER')
    return src

def build():
    with ZipFile(PARENT) as z:
        places=[p for p in z.namelist() if p.endswith('.rbxlx')]
        if len(places)!=1:raise ValueError('SOURCE_DRIFT_PARENT_PLACE_COUNT')
        parent=z.read(places[0]);lock=json.loads(z.read('SOURCE_LOCK.json'))
        feature=json.loads(z.read('RC_FEATURE_LOCK.json'))
    if sha(parent)!=PARENT_SHA or len(parent)!=844814:raise ValueError('SOURCE_DRIFT_PARENT86')
    if lock['total_scripts']!=86 or feature['total_sources']!=86 or lock['blobs']!=feature['source_gitblobs']:
        raise ValueError('SOURCE_DRIFT_PARENT_LOCK')
    root=ET.fromstring(parent)
    nodes=source_nodes(root)
    originals={n:s.text or '' for n,s in nodes.items()}
    if len(originals)!=86:raise ValueError('SOURCE_DRIFT_86_EXPECTED')
    if blob(originals[TARGET])!=lock['blobs'][TARGET_PATH]:raise ValueError('SOURCE_DRIFT_LOOT')
    new=patch(originals[TARGET])
    nodes[TARGET].text=new
    lock['blobs'][TARGET_PATH]=feature['source_gitblobs'][TARGET_PATH]=blob(new)
    result=ET.tostring(root,encoding='utf-8')
    output_nodes=source_nodes(ET.fromstring(result))
    updated={n:s.text or '' for n,s in output_nodes.items()}
    if len(updated)!=86 or any(updated[n]!=orig for n,orig in originals.items() if n!=TARGET):
        raise ValueError('SOURCE_DRIFT_UNEXPECTED_MODIFICATION')
    if sorted(blob(s) for s in updated.values())!=sorted(lock['blobs'].values()):
        raise ValueError('SOURCE_DRIFT_LOCK_MISMATCH')
    OUTPUT.write_bytes(result)
    (HERE/'SOURCE_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (HERE/'RC_FEATURE_LOCK.json').write_text(json.dumps(feature,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    diff=''.join(difflib.unified_diff(originals[TARGET].splitlines(True),new.splitlines(True),
        fromfile='original_stage_loot',tofile='wall_safe_stage_loot'))
    (HERE/'FB030_StageLoot_only.diff').write_text(diff,encoding='utf8')
    receipt={'feature':'FB030_STAGE_LOOT_WALL_AND_CASTLE_GATE_SAFETY',
        'parent_sha256':PARENT_SHA,'place_sha256':sha(result),'bytes':len(result),
        'source_count':86,'changed':['server/StagePickupLoot.luau'],
        'unchanged_sources':85,'stage_loot_old_blob':blob(originals[TARGET]),
        'stage_loot_new_blob':blob(new),
        'native_luau':'NOT_RUN','rojo':'NOT_RUN','studio':'NOT_RUN','android':'NOT_RUN',
        'official_rc_write':False,'owner_accepted':False,'product':'NO_GO'}
    (HERE/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return receipt
if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
