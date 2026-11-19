#!/usr/bin/env python3
"""Generate exact #297-source spectator/Horde correction (private PREP only)."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED

RC='d2f3ed1a47558fdaf07be0181c83c698bdb2ce34'
PARENT='f6cc936a17b10d7cbfb1eb31718025a6fe21346160cacea8d58e8e52d93eb542'
PARENT_GAME='00fab56c721145688a34ba2825babd7bac351fbb'
RESULT='c8fcc131afec42d6c5cf0c58a941d2ee63d0685a99973a11a9fd91a0627ce4b5'
NEW_GAME='a2afadfe31e1a588c531f84890a27df361fc8192'
OUTER='P0D_RC82_ROLE7_FULL_SAFETY_COMPOSITE_PRIVATE.zip'
INNER='COMPOSED_ROLE7_WIND_BUILDERQ_DELAYED_SAFE_RC82.rbxlx'
NAME='P0D_AUTHOR297_ROLE7_FULL_SAFETY_SPECTATOR_PRIVATE.rbxlx'
GAME='server/Game.server.luau'

def sha(x):return hashlib.sha256(x).hexdigest()
def blob(s):
    x=s.encode('utf-8');return hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()
def once(s,old,new,tag):
    n=s.count(old)
    if n!=1:raise ValueError('ANCHOR_DRIFT_'+tag+'_'+str(n))
    return s.replace(old,new,1)

def scripts(root):
    out={};nodes={}
    for node in root.iter('Item'):
        if node.get('class') not in ('Script','ModuleScript','LocalScript'):continue
        p=node.find('Properties')
        if p is None:raise ValueError('MISSING_SCRIPT_PROPS')
        name=p.findtext("string[@name='Name']")
        source=p.find("string[@name='Source']")
        if not name or source is None or source.text is None or name in out:
            raise ValueError('MISSING_OR_DUPLICATE_SCRIPT')
        out[name]=source.text;nodes[name]=source
    if len(out)!=82:raise ValueError('SCRIPT_COUNT_NOT_82')
    return out,nodes

def verify(xml,sl,fl):
    src,_=scripts(ET.fromstring(xml))
    if sl.get('total_scripts')!=82 or fl.get('total_sources')!=82:
        raise ValueError('SOURCE_COUNT_LOCK_DRIFT')
    if sl.get('blobs')!=fl.get('source_gitblobs'):
        raise ValueError('DUAL_LOCK_MISMATCH')
    if Counter(map(blob,src.values()))!=Counter(sl['blobs'].values()):
        raise ValueError('PLACE_SOURCE_LOCK_DRIFT')
    return src

def patch(game):
    game=once(game,
        '    if RunService:IsStudio() and\n'
        '        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then\n',
        '    if (RunService:IsStudio() or privateHordeTrialAllowed()) and\n'
        '        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then\n',
        'LATE_JOIN_OBSERVER')
    game=once(game,
        '        for _,impact in ipairs(horde:tick(now,Players:GetPlayers(),healthy)) do',
        '        for _,impact in ipairs(horde:tick(now,eligibleSoloPlayers(),healthy)) do',
        'LIVE_HORDE_ROSTER')
    game=once(game,
        '            if ok and hum and victimRoot and now>=(invulnUntil[victim] or 0) then',
        '            if ok and hum and victimRoot\n'
        '                and victim:GetAttribute("P0D_LateJoinSpectator")~=true\n'
        '                and (getTeamName(victim)=="RED" or getTeamName(victim)=="BLUE")\n'
        '                and now>=(invulnUntil[victim] or 0) then',
        'DELAYED_HORDE_TARGET_RECHECK')
    game=once(game,
        '    if match.phase == "LOBBY" then\n'
        '        if RunService:IsStudio() then\n'
        '            for _,entrant in ipairs(Players:GetPlayers()) do\n',
        '    if match.phase == "LOBBY" then\n'
        '        if RunService:IsStudio() or privateHordeTrialAllowed()\n'
        '            or #eligibleSoloPlayers()<#Players:GetPlayers() then\n'
        '            for _,entrant in ipairs(Players:GetPlayers()) do\n',
        'RETURN_SPECTATORS_WHEN_PRIVATE_FLAG_OFF')
    for evidence in ('sevenJobPickAckSeq[player]=data.seq',
                     'local castCharacter=player.Character',
                     'root.Parent~=castCharacter',
                     'mobCombo[player]=if hitNow<(mobComboUntil[player] or 0)',
                     'P0D_ADAPTIVE_WIND_FIELD',
                     'workspace:Raycast(root.Position,facing*9,params)'):
        if evidence not in game:raise ValueError('PREVIOUS_QUALITY_FIX_MISSING:'+evidence)
    return game

def build(artifact):
    with ZipFile(io.BytesIO(artifact)) as outer:
        if len(outer.namelist())!=len(set(outer.namelist())):raise ValueError('DUPLICATE_OUTER')
        inner=outer.read(OUTER)
    with ZipFile(io.BytesIO(inner)) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('DUPLICATE_INNER')
        place=z.read(INNER)
        sl=json.loads(z.read('SOURCE_LOCK.json'))
        fl=json.loads(z.read('RC_FEATURE_LOCK.json'))
        receipt=json.loads(z.read('RECEIPT.json'))
    if sha(place)!=PARENT or len(place)!=778612 or receipt.get('official_rc_head')!=RC:
        raise ValueError('AUTHOR_NATIVE82_ROJO_PARENT_CHANGED')
    before=verify(place,sl,fl)
    if sl['blobs'].get(GAME)!=PARENT_GAME:raise ValueError('GAME_BLOB_MISMATCH')
    root=ET.fromstring(place)
    src,nodes=scripts(root)
    changed=patch(before['Game'])
    if blob(changed)!=NEW_GAME:raise ValueError('NEW_GAME_NOT_REPRODUCIBLE')
    nodes['Game'].text=changed
    sl['blobs'][GAME]=fl['source_gitblobs'][GAME]=NEW_GAME
    after=ET.tostring(root,encoding='utf-8')
    if sha(after)!=RESULT or len(after)!=778905:
        raise ValueError('PRIVATE_PLACE_SHA_OR_BYTES_MISMATCH')
    after_src=verify(after,sl,fl)
    if any(before[k]!=after_src[k] for k in before if k!='Game'):
        raise ValueError('OTHER_AUTHOR_SCRIPT_CHANGED')
    return after,sl,fl,after_src

def write(artifact,dest,script_dir):
    place,sl,fl,src=build(artifact)
    with ZipFile(dest,'w',ZIP_DEFLATED) as z:
        z.writestr(NAME,place)
        z.writestr('SOURCE_LOCK.json',json.dumps(sl,ensure_ascii=False,indent=2))
        z.writestr('RC_FEATURE_LOCK.json',json.dumps(fl,ensure_ascii=False,indent=2))
        z.writestr('RECEIPT.json',json.dumps({
            'schema':'P0D_QUALITY_AUTHOR297_B20_SPECTATOR_NATIVE82_V3',
            'official_rc_head':RC,'parent_sha256':PARENT,'place_sha256':RESULT,
            'scripts':82,'unchanged_parent_scripts':81,'game_blob':NEW_GAME,
            'native':'NOT_RUN','rojo':'NOT_RUN','studio':'NOT_RUN',
            'android':'NOT_RUN','owner_accepted':False,'official_rc_write':False,
            'decision':'PRODUCT_NO_GO'},indent=2))
    script_dir.mkdir(parents=True,exist_ok=True)
    root=ET.fromstring(place)
    manifest=[]
    kinds={'Script':'.server.luau','LocalScript':'.client.luau','ModuleScript':'.luau'}
    def walk(item,base=()):
        props=item.find('Properties')
        label=props.findtext("string[@name='Name']") if props is not None else None
        source=props.findtext("string[@name='Source']") if props is not None else None
        path=base+((label,) if label is not None else ())
        if source is not None:
            if item.attrib.get('class') not in kinds or len(path)<3:
                raise ValueError('SOURCE_PATH_OR_CLASS_NOT_ALLOWED')
            if path[0] not in ('ReplicatedStorage','ServerScriptService','StarterPlayer'):
                raise ValueError('SOURCE_SERVICE_NOT_ALLOWED')
            if any(not segment.isidentifier() for segment in path):
                raise ValueError('INVALID_SOURCE_NAME')
            rel=Path(*path).with_suffix(kinds[item.attrib['class']])
            output=script_dir/'src'/rel
            output.parent.mkdir(parents=True,exist_ok=True)
            if output.exists():raise ValueError('DUPLICATE_PHYSICAL_SOURCE_PATH')
            output.write_text(source,encoding='utf-8')
            manifest.append(dict(path='/'.join(path),kind=item.attrib['class'],blob=blob(source)))
        for child in item.findall('Item'):walk(child,path)
    for item in root.findall('Item'):walk(item)
    if len(manifest)!=82:raise ValueError('SOURCE_TREE_NOT_82')
    (script_dir/'manifest.json').write_text(json.dumps(manifest,indent=2))
    project={'name':'P0DNativeSpectator82','tree':{'$className':'DataModel',
        'ReplicatedStorage':{'$className':'ReplicatedStorage',
            'TrapRaidersShared':{'$path':'src/ReplicatedStorage/TrapRaidersShared'}},
        'ServerScriptService':{'$className':'ServerScriptService',
            'TrapRaidersS1':{'$path':'src/ServerScriptService/TrapRaidersS1'}},
        'StarterPlayer':{'$className':'StarterPlayer',
            'StarterPlayerScripts':{'$path':'src/StarterPlayer/StarterPlayerScripts'}}}}
    (script_dir/'default.project.json').write_text(json.dumps(project,indent=2))
    return len(src),sha(place)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--author-artifact',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--scripts',type=Path,required=True)
    a=parser.parse_args()
    print('P0D_SPECTATOR_SOURCE_PREP',write(a.author_artifact.read_bytes(),a.out,a.scripts))
