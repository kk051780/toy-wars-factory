#!/usr/bin/env python3
"""Build independently validated PRIVATE RC86 from native85 loot artifact + verified undead source.

No canonical RC, repository main or Roblox publication is touched.
"""
import copy, difflib, hashlib, io, json, xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
from importlib.util import spec_from_file_location, module_from_spec
HERE=Path(__file__).resolve().parent
PARENT=HERE/'stage_loot_parent85.zip'
PARENT_SHA='501688966820ae80833a7cae1d5a8b4fc908b9b30062dd1c3f727a356cc15387'
NEW_MODULE='server/UndeadSquad.luau'; GAME='server/Game.server.luau'
OUT='P0D_RC86_SIEGE_V3_STAGE_WEAPONS_UNDEAD_PRIVATE.rbxlx'
spec=spec_from_file_location('undead_patch_v3',HERE/'undead_patch_v3.py')
up=module_from_spec(spec);spec.loader.exec_module(up)
blob=up.blob;digest=up.digest;sources=up.sources

def build():
    with ZipFile(PARENT) as outer:
        members=outer.namelist()
        if len(members)!=1 or not members[0].endswith('.zip'):raise ValueError('WRONG_PARENT_ARCHIVE')
        with ZipFile(io.BytesIO(outer.read(members[0]))) as inner:
            loc=[x for x in inner.namelist() if x.endswith('.rbxlx')]
            if len(loc)!=1:raise ValueError('WRONG_PARENT_PLACE_COUNT')
            parent=inner.read(loc[0]);sl=json.loads(inner.read('SOURCE_LOCK.json'));fl=json.loads(inner.read('RC_FEATURE_LOCK.json'))
    if len(parent)!=832695 or digest(parent)!=PARENT_SHA:raise ValueError('SOURCE_DRIFT_PARENT_LOOT85')
    if sl['total_scripts']!=85 or fl['total_sources']!=85 or sl['blobs']!=fl['source_gitblobs']:raise ValueError('SOURCE_DRIFT_LOCK')
    root=ET.fromstring(parent);found=sources(root);before={k:s.text for k,(_,_,s) in found.items()}
    if len(before)!=85 or len(sl['blobs'])!=85:
        raise ValueError('SOURCE_DRIFT_85_SCRIPT_NAMES')
    if blob(before['Game'])!=sl['blobs'][GAME]:raise ValueError('SOURCE_DRIFT_GAME_BLOB')
    if blob(before['StagePickupLoot'])!=sl['blobs']['server/StagePickupLoot.luau']:
        raise ValueError('SOURCE_DRIFT_LOOT_BLOB')
    if 'SevenJobs.StageLoot.start(map.model' not in before['Game'] or 'SevenJobs.StageLoot.damageMultiplier' not in before['Game']:
        raise ValueError('SOURCE_DRIFT_LOOT_GAME')
    if 'UndeadSquad' in before:raise ValueError('DUPLICATE_UNDEAD')
    mod=(HERE/'UndeadSquad.luau').read_text(encoding='utf-8')
    after_game=up.patch_game(before['Game'])
    if not after_game.count('SevenJobs.StageLoot.damageMultiplier')==1:raise ValueError('LOOT_LOST_IN_COMPOSITE')
    if not after_game.count('SevenJobs.Undead.cast')==1:raise ValueError('UNDEAD_LOST_IN_COMPOSITE')
    if not after_game.count('SevenJobs.StageLoot.endRound()')==2:raise ValueError('LOOT_CLEANUP_LOST')
    found['Game'][2].text=after_game
    parent_element,template,_=found['SevenJobsRules']
    new=copy.deepcopy(template)
    refs=[int(x.attrib['referent']) for x in root.iter('Item') if x.attrib.get('referent','').isdigit()]
    new.set('referent',str(max(refs)+1))
    props=new.find('Properties');props.find("string[@name='Name']").text='UndeadSquad';props.find("string[@name='Source']").text=mod
    parent_element.append(new)
    sl['blobs'][GAME]=fl['source_gitblobs'][GAME]=blob(after_game)
    sl['blobs'][NEW_MODULE]=fl['source_gitblobs'][NEW_MODULE]=blob(mod)
    sl['total_scripts']=fl['total_sources']=86
    out=ET.tostring(root,encoding='utf-8');actual={k:s.text for k,(_,_,s) in sources(ET.fromstring(out)).items()}
    if len(actual)!=86:raise ValueError('SCRIPT_COUNT_BAD')
    for k,v in before.items():
        if k!='Game' and actual[k]!=v:raise ValueError('PREEXISTING_SCRIPT_CHANGED_'+k)
    if actual['Game']!=after_game or actual['UndeadSquad']!=mod:raise ValueError('NEW_SOURCE_MISMATCH')
    if sorted(blob(x) for x in actual.values())!=sorted(sl['blobs'].values()):raise ValueError('LOCK_MISMATCH')
    (HERE/OUT).write_bytes(out)
    (HERE/'SOURCE_LOCK.json').write_text(json.dumps(sl,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'RC_FEATURE_LOCK.json').write_text(json.dumps(fl,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'Game_combined_only.diff').write_text(''.join(difflib.unified_diff(before['Game'].splitlines(True),after_game.splitlines(True),fromfile='game_usable_stage_weapons85',tofile='game_stage_loot_plus_undead86')),encoding='utf-8')
    receipt={'schema':'P0D_RC86_SIEGE_V3_STAGE_LOOT_AND_UNDEAD','parent_sha256':PARENT_SHA,'place_sha256':digest(out),'place_bytes':len(out),'script_count':86,'unchanged_existing_scripts':84,'changed_paths':[GAME,NEW_MODULE],'game_gitblob':blob(after_game),'loot_gitblob':blob(before['StagePickupLoot']),'undead_gitblob':blob(mod),'source_lock':True,'official_rc_write':False,'native_luau':'NOT_RUN','rojo':'NOT_RUN','studio':'NOT_RUN','android':'NOT_RUN','owner_accepted':False,'product':'NO_GO','art':'NO_GO'}
    (HERE/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt
if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
