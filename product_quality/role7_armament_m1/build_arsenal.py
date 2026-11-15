#!/usr/bin/env python3
"""Source-selective PREP: original Game + new isolated SevenJobArmamentM1.
No existing #297 Game/HUD branch writes, original RC CAS, publish, merge or spend.
"""
from __future__ import annotations
import hashlib,zipfile,io,copy,json,difflib,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE=Path(__file__).parent
PARENT=Path('/tmp/P0D_FB005_SOLO_OBSERVER_KICKOFF_NATIVE82_AUTHOR_CI.zip')
PARENT_SHA='b773e1eb52c249b220a04ad3f8b1f9f32a0c03362a315261f9eadecfce537f7f'
TARGET='server/Game.server.luau'
MOD_PATH='server/SevenJobArmamentM1.luau'

def sha(b):return hashlib.sha256(b).hexdigest()
def blob(s):
    b=s.encode('utf-8')
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def once(s,old,new,why):
    n=s.count(old)
    if n!=1:raise ValueError(f'SOURCE_DRIFT_{why}:{n}')
    return s.replace(old,new,1)

def patch_game(game):
    game=once(game,'local SevenJobs = require(script.Parent:WaitForChild("SevenJobsRules"))',
       'local SevenJobs = require(script.Parent:WaitForChild("SevenJobsRules"))\n'
       'local JobArsenal = require(script.Parent:WaitForChild("SevenJobArmamentM1"))', 'IMPORT_SINGLE')
    # Existing original authorized job select; no second JOBCHECK or Remote.
    game=once(game,'    sevenJobPickAckSeq[player]=data.seq -- genuine authorized JOB_PICK only\n',
        '    sevenJobPickAckSeq[player]=data.seq -- genuine authorized JOB_PICK only\n'
        '    JobArsenal.resetPlayer(player)\n'
        '    if player.Character then JobArsenal.equip(player.Character,job) end\n','JOB_EQUIP_AFTER_REAL_ACK')
    game=once(game,'            roundReady[player]=false\n            player.Team = teamInstances[move.to]',
        '            roundReady[player]=false\n'
        '            JobArsenal.resetPlayer(player)\n'
        '            JobArsenal.clear(player.Character) -- clear revoked job on lobby team transfer\n'
        '            player.Team = teamInstances[move.to]','REBALANCE_UNEQUIP')
    game=once(game,'        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability\n',
        '        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability\n'
        '        JobArsenal.resetPlayer(player) -- a respawn never carries a prior 3-hit chain\n'
        '        if sevenJobSelected[player]==true and SevenJobs.valid(sevenJobs[player])\n'
        '            and (RunService:IsStudio() or privateHordeTrialAllowed())\n'
        '            and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false then\n'
        '            JobArsenal.equip(character,sevenJobs[player])\n'
        '        end\n','CHARACTER_REAL_EQUIP')
    old='''        local touched,defeated = horde:hit(root.Position,look,
            Config.CombatDamage[roles[player] or "RAIDER"]
                *SavedPvePolicy.mergeWithEarned(
                    earnedDamageMultiplier(player,"MINION")
                    *Dojo.pveDamageMultiplier(dojoStates[player],"WEAPON"),
                    math.min(3.8,savedPveMinionMultiplier(player)
                    *twinBondOnlyNeutralMobBonus(player))),now,player.Character)'''
    new='''        local originalPveDamage = Config.CombatDamage[roles[player] or "RAIDER"]
                *SavedPvePolicy.mergeWithEarned(
                    earnedDamageMultiplier(player,"MINION")
                    *Dojo.pveDamageMultiplier(dojoStates[player],"WEAPON"),
                    math.min(3.8,savedPveMinionMultiplier(player)
                    *twinBondOnlyNeutralMobBonus(player)))
        local touched,defeated=0,0
        if sevenJobSelected[player]==true and SevenJobs.valid(sevenJobs[player])
            and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false then
            -- Server 3-stage per-class M1; original Horde owns real damage/KOs.
            -- Each strike uses authenticated root/role/seq/cooldown above.
            local job=sevenJobs[player]
            local stage=JobArsenal.comboStage(player,job,now)
            touched,defeated=JobArsenal.strike(job,stage,root.Position,look,
                originalPveDamage,function(pos:Vector3,dir:Vector3,damage:number)
                    return horde:hit(pos,dir,damage,now,player.Character)
                end)
        else
            -- Public/flag OFF or unselected class: byte-equivalent original hit.
            touched,defeated=horde:hit(root.Position,look,
                originalPveDamage,now,player.Character)
        end'''
    game=once(game,old,new,'CLASS_SPECIFIC_M1_AUTH_DAMAGE')
    game=once(game,'    sevenJobSelected[player]=nil\n    sevenJobPickAckSeq[player]=nil',
        '    sevenJobSelected[player]=nil\n    JobArsenal.resetPlayer(player)\n'
        '    JobArsenal.clear(player.Character)\n    sevenJobPickAckSeq[player]=nil','REMOVE_CLEANUP')
    return game

def extract(src):
    root=ET.fromstring(src)
    loc={}
    for parent in root.iter():
        for child in list(parent):
            if child.tag!='Item':continue
            props=child.find('Properties')
            if props is None:continue
            n=props.findtext("string[@name='Name']")
            text=props.find("string[@name='Source']")
            if text is not None and n:
                if n in loc: raise ValueError('DUPLICATE_SCRIPT_'+n)
                loc[n]=(parent,child,text)
    return root,loc

def build():
    with zipfile.ZipFile(PARENT) as outer:
        names=outer.namelist();assert len(names)==1
        with zipfile.ZipFile(io.BytesIO(outer.read(names[0]))) as z:
            p=[x for x in z.namelist() if x.endswith('.rbxlx')]
            assert len(p)==1
            xml=z.read(p[0]);sl=json.loads(z.read('SOURCE_LOCK.json'))
            fl=json.loads(z.read('RC_FEATURE_LOCK.json'))
    assert sha(xml)==PARENT_SHA
    assert sl['total_scripts']==fl['total_sources']==82
    assert sl['blobs']==fl['source_gitblobs']
    root,loc=extract(xml)
    assert len(loc)==82
    before={n:t.text for n,(_,_,t) in loc.items()}
    assert Counter(blob(t) for t in before.values())==Counter(sl['blobs'].values())
    assert blob(before['Game'])==sl['blobs'][TARGET]
    newgame=patch_game(before['Game'])
    assert len([k for k in before if k=='SevenJobsRules'])==1
    mod=(HERE/'SevenJobArmamentM1.luau').read_text()
    # New independent ModuleScript immediately beside original SevenJobsRules;
    # clone Instance schema, replace Name/Source and allocate unique referent.
    parent,original,_=loc['SevenJobsRules']
    new=copy.deepcopy(original)
    refs=[int(x.attrib['referent']) for x in root.iter('Item') if x.attrib.get('referent','').isdigit()]
    new.set('referent',str(max(refs)+1))
    props=new.find('Properties')
    props.find("string[@name='Name']").text='SevenJobArmamentM1'
    props.find("string[@name='Source']").text=mod
    parent.append(new)
    loc['Game'][2].text=newgame
    sl['blobs'][TARGET]=fl['source_gitblobs'][TARGET]=blob(newgame)
    sl['blobs'][MOD_PATH]=fl['source_gitblobs'][MOD_PATH]=blob(mod)
    sl['total_scripts']=83;fl['total_sources']=83
    newxml=ET.tostring(root,encoding='utf-8')
    root2,loc2=extract(newxml)
    after={n:t.text for n,(_,_,t) in loc2.items()}
    assert len(after)==83
    assert Counter(blob(t) for t in after.values())==Counter(sl['blobs'].values())
    assert len(sl['blobs'])==83
    for name in before:
        if name!='Game':assert before[name]==after[name],name
    assert after['SevenJobArmamentM1']==mod
    diff=''.join(difflib.unified_diff(before['Game'].splitlines(keepends=True),newgame.splitlines(keepends=True),fromfile='Game_original_82',tofile='Game_new_83'))
    out=HERE/'P0D_ROLE7_REAL_ARMAMENT_M1_PRIVATE83.rbxlx'
    out.write_bytes(newxml)
    (HERE/'P0D_REAL_GAME_SELECTIVE.diff').write_text(diff)
    (HERE/'SOURCE_LOCK.json').write_text(json.dumps(sl,ensure_ascii=False,indent=2)+'\n')
    (HERE/'RC_FEATURE_LOCK.json').write_text(json.dumps(fl,ensure_ascii=False,indent=2)+'\n')
    receipt={'schema':'P0D_ROLE7_REAL_ARMAMENT_7_M1_3STEP_PRIVATE83','base_official_rc':'d2f3ed1a47558fdaf07be0181c83c698bdb2ce34',
             'parent_prep_sha256':PARENT_SHA,'place_bytes':len(newxml),'place_sha256':sha(newxml),
             'source_count':83,'new_module_gitblob':blob(mod),'game_gitblob':blob(newgame),
             'other_81_original_scripts_unchanged':True,'source_lock':True,
             'seven_weapons_physically_welded':True,'seven_differentiated_server_m1':True,
             'native_luau':'NOT_RUN','rojo':'NOT_RUN','studio':'NOT_RUN','android':'NOT_RUN',
             'official_rc_write':False,'product':'NO_GO','owner_accepted':False}
    (HERE/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    zpath=HERE/'P0D_ROLE7_ARMAMENT_M1_SOURCE_PRIVATE83.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for f in [out,HERE/'P0D_REAL_GAME_SELECTIVE.diff',HERE/'SOURCE_LOCK.json',HERE/'RC_FEATURE_LOCK.json',HERE/'RECEIPT.json',HERE/'SevenJobArmamentM1.luau']:
            z.write(f,f.name)
    return receipt
if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
