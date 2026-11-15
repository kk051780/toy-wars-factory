#!/usr/bin/env python3
"""Deterministic source-exact FB026 private 83->84 place overlay; no official RC write."""
import copy
import difflib
import hashlib
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
PARENT=HERE/'parent_rc84.zip'
PARENT_SHA='89b47d4d919a04b4ea72304681749f2b8f01da768698bf5a1838b8bb5c331e7e'
TARGET='server/Game.server.luau'
MODULE_PATH='server/UndeadSquad.luau'


def digest(b): return hashlib.sha256(b).hexdigest()
def blob(s):
    b=s.encode('utf-8')
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()


def replace_once(src,old,new,label):
    n=src.count(old)
    if n!=1:raise ValueError('SOURCE_DRIFT_'+label+'_'+str(n))
    return src.replace(old,new,1)


def patch_game(src):
    src=replace_once(src,
        'SevenJobs.ArmamentM1 = require(script.Parent:WaitForChild("SevenJobArmamentM1"))',
        'SevenJobs.ArmamentM1 = require(script.Parent:WaitForChild("SevenJobArmamentM1"))\n'
        'SevenJobs.Undead = require(script.Parent:WaitForChild("UndeadSquad"))', 'IMPORT')
    src=replace_once(src,
        '            horde:clearSevenBeast(player)\n            sevenJobs[player]="WARRIOR"',
        '            horde:clearSevenBeast(player)\n            SevenJobs.Undead.clear(player)\n            sevenJobs[player]="WARRIOR"', 'REBALANCE_CLEAR')
    src=replace_once(src,
        '    horde:clearSevenBeast(player) -- no old pet survives role re-selection',
        '    horde:clearSevenBeast(player) -- no old pet survives role re-selection\n'
        '    SevenJobs.Undead.clear(player) -- no old squad survives job change', 'JOB_CHANGE_CLEAR')
    src=replace_once(src,
        '        horde:clearSevenBeast(player)\n        dropEgg(player)',
        '        horde:clearSevenBeast(player)\n        SevenJobs.Undead.clear(player)\n        dropEgg(player)', 'RESPAWN_CLEAR')
    src=replace_once(src,
        '    horde:clearSevenBeast(player)\n    lastFreeHatch[player]=nil',
        '    horde:clearSevenBeast(player)\n    SevenJobs.Undead.clear(player)\n    lastFreeHatch[player]=nil', 'LEAVE_CLEAR')
    src=replace_once(src,
        '    for _,p in ipairs(Players:GetPlayers()) do cleanupScout(p) end\n    match.phase = "RESULTS"',
        '    for _,p in ipairs(Players:GetPlayers()) do\n'
        '        cleanupScout(p)\n        SevenJobs.Undead.clear(p)\n    end\n    match.phase = "RESULTS"', 'ROUND_END_CLEAR')
    src=replace_once(src,
        'local function resetRound()\n    SoloTeamBots.stop()',
        'local function resetRound()\n'
        '    for _,p in ipairs(Players:GetPlayers()) do SevenJobs.Undead.clear(p) end\n'
        '    SoloTeamBots.stop()', 'RESET_CLEAR')
    src=replace_once(src,
        '''    elseif job=="NECROMANCER" then
        sevenJobStrike(player,root.Position,facing,14)
        sevenJobDelayedStrike(player,job,match.serial,root.Position,-facing,14,.8)
        sevenJobDelayedStrike(player,job,match.serial,root.Position,facing,14,1.6)''',
        '''    elseif job=="NECROMANCER" then
        -- FB026 three actual follower NPCs with real, owner-credited horde:hit.
        -- A repeated authorized Q cycles ATTACK / GUARD / FOLLOW commands.
        sevenJobStrike(player,root.Position,facing,14)
        local castAvatar=player.Character
        local castTeam=team
        local castSerial=match.serial
        local castAck=sevenJobPickAckSeq[player]
        SevenJobs.Undead.cast(player,{
            parent=map.model,
            root=function()
                local ok,current=healthy(player)
                if ok and player.Character==castAvatar then return current end
                return nil
            end,
            valid=function()
                return player.Parent==Players and castAvatar~=nil
                    and player.Character==castAvatar and match.phase=="ACTIVE"
                    and match.serial==castSerial and getTeamName(player)==castTeam
                    and sevenJobs[player]=="NECROMANCER"
                    and sevenJobSelected[player]==true
                    and sevenJobPickAckSeq[player]==castAck
                    and carry[player]==nil and slowed[player]==nil
                    and (RunService:IsStudio() or privateHordeTrialAllowed())
                    and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false
            end,
            targets=function() return horde.mobs end,
            hit=function(position,dir,dmg)
                return sevenJobStrike(player,position,dir,dmg)
            end,
        })''', 'NECRO_REAL_SQUAD')
    return src


def sources(root):
    found={}
    for parent in root.iter():
        for item in parent.findall('Item'):
            props=item.find('Properties')
            if props is None:continue
            name=props.findtext("string[@name='Name']")
            source=props.find("string[@name='Source']")
            if name and source is not None:
                if name in found: raise ValueError('DUP_SCRIPT_NAME_'+name)
                found[name]=(parent,item,source)
    return found


def build():
    with ZipFile(PARENT) as outer:
        names=outer.namelist()
        assert len(names)==1 and names[0].endswith('.zip')
        with ZipFile(io.BytesIO(outer.read(names[0]))) as inner:
            places=[x for x in inner.namelist() if x.endswith('.rbxlx')]
            assert len(places)==1
            parent=inner.read(places[0])
            sl=json.loads(inner.read('SOURCE_LOCK.json'))
            fl=json.loads(inner.read('RC_FEATURE_LOCK.json'))
    assert digest(parent)==PARENT_SHA and len(parent)==819866
    assert sl['total_scripts']==fl['total_sources']==84
    assert sl['blobs']==fl['source_gitblobs'] and len(sl['blobs'])==84
    root=ET.fromstring(parent)
    found=sources(root)
    assert len(found)==84 and 'Game' in found and 'SevenJobsRules' in found
    before={name:source.text for name,(_,_,source) in found.items()}
    assert blob(before['Game'])==sl['blobs'][TARGET]
    mod=(HERE/'UndeadSquad.luau').read_text(encoding='utf-8')
    new_game=patch_game(before['Game'])
    found['Game'][2].text=new_game
    parent_element,template,_=found['SevenJobsRules']
    new=copy.deepcopy(template)
    refs=[int(x.attrib['referent']) for x in root.iter('Item') if x.attrib.get('referent','').isdigit()]
    new.set('referent',str(max(refs)+1))
    props=new.find('Properties')
    props.find("string[@name='Name']").text='UndeadSquad'
    props.find("string[@name='Source']").text=mod
    parent_element.append(new)
    sl['blobs'][TARGET]=fl['source_gitblobs'][TARGET]=blob(new_game)
    sl['blobs'][MODULE_PATH]=fl['source_gitblobs'][MODULE_PATH]=blob(mod)
    sl['total_scripts']=fl['total_sources']=85
    out=ET.tostring(root,encoding='utf-8')
    parsed=ET.fromstring(out)
    after={name:source.text for name,(_,_,source) in sources(parsed).items()}
    assert len(after)==85 and len(sl['blobs'])==85 and sl['blobs']==fl['source_gitblobs']
    assert after['UndeadSquad']==mod and after['Game']==new_game
    for name,old in before.items():
        if name!='Game':assert after[name]==old,('REGRESSION',name)
    assert sorted(blob(x) for x in after.values())==sorted(sl['blobs'].values())
    base=(HERE/'P0D_FB026_NECROMANCER_SIEGE_CUMULATIVE_PRIVATE85')
    place=base.with_suffix('.rbxlx')
    place.write_bytes(out)
    (HERE/'SOURCE_LOCK.json').write_text(json.dumps(sl,indent=2,ensure_ascii=False)+'\n')
    (HERE/'RC_FEATURE_LOCK.json').write_text(json.dumps(fl,indent=2,ensure_ascii=False)+'\n')
    (HERE/'Game_source_only.diff').write_text(''.join(difflib.unified_diff(
        before['Game'].splitlines(keepends=True),new_game.splitlines(keepends=True),
        fromfile='Game_siege_private84',tofile='Game_undead_private85')))
    receipt=dict(schema='P0D_FB026_UNDEAD_SIEGE_CUMULATIVE_PRIVATE85',
        parent_sha256=PARENT_SHA,place_sha256=digest(out),place_bytes=len(out),
        script_count=85,old_83_scripts_byte_exact=True,
        changed_paths=[TARGET,MODULE_PATH],game_gitblob=blob(new_game),
        module_gitblob=blob(mod),source_lock=True,official_rc_write=False,
        native_luau='NOT_RUN',rojo='NOT_RUN',studio='NOT_RUN',android='NOT_RUN',
        owner_accepted=False,product='NO_GO')
    (HERE/'RECEIPT.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    return receipt

if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))