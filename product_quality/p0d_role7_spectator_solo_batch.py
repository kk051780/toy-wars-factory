#!/usr/bin/env python3
"""#470 source-exact private opt-in solo team bots + physical spectator safe staging + lobby reentry.

Apply only selected Game and original SoloTeamBots source changes on the latest
verified spectator-staging Place. Never mutate canonical RC/PR author Game.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from collections import Counter

PARENT_PLACE = "P0D_ROLE7_ACK_WIND_BUILDER_COMBO_RESPAWN_SPECTATOR_RC82.rbxlx"
PARENT_SHA = "233c684371f6211d2d5f385479e8a39e6a22b0504efba96935a740cd99042a5e"
PARENT_GAME = "4986f23e7e0c46595aa489e4576d227945ed8686"
RC = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
GAME = "server/Game.server.luau"
BOTS = "server/SoloTeamBots.luau"
OUTPUT_PLACE = "P0D_ROLE7_SPECTATOR_SAFE_STAGE_SOLO_BOTS_LOBBY_SAFE_RC82.rbxlx"
EXPECTED_PLACE_SHA="c1cfc5f73b219bec5e75f5d9bee6647ab34f08cbaff44dd3bebdf8e5afc14111"
EXPECTED_GAME="9c88bb0b2491943dce12090bc95f27464795ea47"
EXPECTED_BOTS="959289081bdf1f4ae11d48466856cba1bb8b83ce"

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def blob(s:str)->str:
    b=s.encode('utf8'); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
def swap(s:str,old:str,new:str,label:str)->str:
    if s.count(old)!=1 or new in s:raise ValueError('ANCHOR_DRIFT_OR_DUPLICATE_'+label+':'+str(s.count(old)))
    return s.replace(old,new,1)

def source_map(raw:bytes):
    root=ET.fromstring(raw);scripts={}; actual={}
    services={"ServerScriptService":"server","StarterPlayer":"client","ReplicatedStorage":"shared"}
    # Immutable original-author Rojo source filenames are distinct from four
    # Roblox Runtime Instance.Name values. Map them explicitly, never infer by hash.
    aliases={
        'client/FB015GoroganVisual.client.luau':'client/FB015CharacterArt.client.luau',
        'client/P0DConfirmedCombatFX.client.luau':'client/ConfirmedSlashFX.client.luau',
        'client/TrapRaidersCoach.client.luau':'client/FirstMinuteCoach.client.luau',
        'client/TrapRaidersHUD.client.luau':'client/HUD.client.luau',
    }
    def walk(node,chain=()):
        p=node.find('Properties');n=p.findtext('./string[@name="Name"]') if p is not None else None
        if n is None:raise ValueError('NO_NAME')
        path=chain+(n,)
        if node.get('class') in ('Script','LocalScript','ModuleScript'):
            so=p.find('string[@name="Source"]');
            if so is None or so.text is None:raise ValueError('MISSING_SCRIPT_SOURCE')
            if n in scripts:raise ValueError('DUPLICATE_SCRIPT_NAME_'+n)
            scripts[n]=(so,node.get('class'),path)
        for child in node.findall('Item'):walk(child,path)
    for child in root.findall('Item'):walk(child)
    if len(scripts)!=82:raise ValueError('SCRIPT_COUNT_DRIFT')
    for n,(e,cl,path) in scripts.items():
        if not path or path[0] not in services:raise ValueError('UNEXPECTED_SERVICE')
        ext={'Script':'.server.luau','LocalScript':'.client.luau','ModuleScript':'.luau'}[cl]
        path_key=services[path[0]]+'/'+n+ext
        actual[aliases.get(path_key,path_key)]=blob(e.text)
    if len(actual)!=82:raise ValueError('DUPLICATE_SOURCE_PATH')
    return root,scripts,actual

def locked(raw,lock,feature):
    root,scripts,actual=source_map(raw)
    a=lock.get('blobs');b=feature.get('source_gitblobs')
    if lock.get('total_scripts')!=82 or feature.get('total_sources')!=82 or a!=b or actual!=a:
        # Compare path as well as source: a SHA multiset check misses swaps.
        raise ValueError('CLASS_PATH_OR_SOURCE_LOCK_DRIFT')
    return root,scripts

def egg_block(s:str)->str:
    begin='for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
    end='\n-- P0D_SAVED_PVE_MASTERY_V1:'
    if s.count(begin)!=1 or s.count(end)!=1:raise ValueError('EGG_SCORE_ORIGINAL_DRIFT')
    return s[s.index(begin):s.index(end)]

def patch_sources(game:str,bots:str):
    original_egg=egg_block(game)
    gate='local function privateHordeTrialAllowed(): boolean\n    return game.PrivateServerId ~= "" and\n        workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true\nend'
    game=swap(game,gate,gate+'\n-- FB005 separate private-only explicit opt-in; public bots stay disabled.\nlocal function privateSoloBotsTrialAllowed(): boolean\n    return privateHordeTrialAllowed()\n        and workspace:GetAttribute("P0D_PRIVATE_SOLO_TEAM_BOTS") == true\nend','BOT_GATE')
    game=swap(game,
      'if RunService:IsStudio() and studioSoloRoundStarted\n        and not EXPERIMENTAL_FIVE_EGG_MODE then',
      'if (RunService:IsStudio() or privateSoloBotsTrialAllowed())\n        and studioSoloRoundStarted and not EXPERIMENTAL_FIVE_EGG_MODE then','BOT_START')
    attack_gate='if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then'
    if game.count(attack_gate)!=2:raise ValueError('ORIGINAL_BOT_TICK_ATTACK_DRIFT')
    game=game.replace(attack_gate,'if (RunService:IsStudio() or privateSoloBotsTrialAllowed())\n        and not EXPERIMENTAL_FIVE_EGG_MODE then')
    game=swap(game,'    tickTraps(now)\n    -- The ORIGINAL Game clock alone owns auto-training;',
      '    tickTraps(now)\n    -- Stop physical private bots immediately after flag-OFF; avoid abandoned NPCs.\n    if not RunService:IsStudio() and SoloTeamBots.isActive()\n        and not privateSoloBotsTrialAllowed() then\n        SoloTeamBots.stop()\n        if studioSoloRoundStarted and match.phase=="ACTIVE"\n            and #eligibleSoloPlayers()==1 then\n            stopRound("DRAW","PRIVATE_SOLO_BOTS_DISABLED")\n        end\n    end\n    -- The ORIGINAL Game clock alone owns auto-training;','BOT_OFF_ROLLBACK')
    bots=swap(bots,'    if not RunService:IsStudio() then return false end\n    local eligible=0',
      '    -- Original solo AI only under Studio or two independent private-server flags.\n    if not (RunService:IsStudio() or\n        (game.PrivateServerId ~= ""\n         and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE")==true\n         and workspace:GetAttribute("P0D_PRIVATE_SOLO_TEAM_BOTS")==true)) then\n        return false\n    end\n    local eligible=0','BOT_MODULE_PRIVATE')
    bots=swap(bots,'    folder:SetAttribute("StudioBotPreview",true)',
      '    folder:SetAttribute("StudioBotPreview",RunService:IsStudio())','BOT_METADATA')
    # Existing spectator-safe staging remains untouched. Existing lobby fallback
    # missing team is a distinct proven nil-index crash: repair only this branch.
    game=swap(game,
      'root.CFrame=if RunService:IsStudio()\n                            then LobbyIsland.spawn(getTeamName(entrant))\n                            else map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0)',
      'root.CFrame=if RunService:IsStudio()\n                            then LobbyIsland.spawn(getTeamName(entrant))\n                            -- No-team spectators must not dereference map.teams[nil].\n                            else (map.teams[getTeamName(entrant)]\n                                and (map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0))\n                                or root.CFrame)','TEAMLESS_REENTRY')
    for proof in ('horde:tick(now,eligibleSoloPlayers(),healthy)',
      'if map.model:FindFirstChild("P0D_SAFE_LOBBY")==nil then',
      'LobbyIsland.build(map.model)',
      'sevenJobPickAckSeq[player]~=selectedAck',
      'player.Character~=castCharacter',
      'mobCombo[player]=if hitNow<(mobComboUntil[player] or 0)',
      'if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true then',
      'personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1',
      'privateSoloBotsTrialAllowed()',
      'stopRound("DRAW","PRIVATE_SOLO_BOTS_DISABLED")'):
        if proof not in game:raise ValueError('ORIGINAL_CORE_GAMEPLAY_REGRESSION_'+proof)
    if egg_block(game)!=original_egg:raise ValueError('EGG_SCORE_WINNER_AUTHORITY_CHANGED')
    for proof in ('function Bot.tick(now)','function Bot.tryHumanHit(',
      'callbacks.deposit(bot,bot.team,bot.carry)',
      'workspace:GetAttribute("P0D_PRIVATE_SOLO_TEAM_BOTS")==true'):
        if proof not in bots:raise ValueError('ORIGINAL_SOLO_BOT_AUTHORITY_CHANGED')
    return game,bots

def build(outer_zip:bytes,output:Path,extract_dir:Path|None=None):
    import io
    with ZipFile(io.BytesIO(outer_zip)) as outer:
        if len(outer.namelist())!=1:raise ValueError('UNEXPECTED_OUTER_ARTIFACT')
        with ZipFile(io.BytesIO(outer.read(outer.namelist()[0]))) as z:
            if len(z.namelist())!=len(set(z.namelist())):raise ValueError('DUPLICATE_ZIP_MEMBER')
            raw=z.read(PARENT_PLACE)
            lock=json.loads(z.read('SOURCE_LOCK.json'))
            feature=json.loads(z.read('RC_FEATURE_LOCK.json'))
            prior=json.loads(z.read('RECEIPT.json'))
    if sha(raw)!=PARENT_SHA or lock['blobs'].get(GAME)!=PARENT_GAME or prior.get('official_rc_head')!=RC:
        raise ValueError('PARENT_SOURCE_NOT_PINNED')
    root,els=locked(raw,lock,feature)
    old={n:e.text for n,(e,_,_) in els.items()}
    game,bots=patch_sources(old['Game'],old['SoloTeamBots'])
    els['Game'][0].text=game;els['SoloTeamBots'][0].text=bots
    out=ET.tostring(root,encoding='utf-8')
    if sha(out)!=EXPECTED_PLACE_SHA or len(out)!=780590 or blob(game)!=EXPECTED_GAME or blob(bots)!=EXPECTED_BOTS:
        raise ValueError('FINAL_SAME_HEAD_PLACE_OR_BLOBS_CHANGED')
    _,after=locked(out,{**lock,'blobs':{**lock['blobs'],GAME:blob(game),BOTS:blob(bots)}},
                        {**feature,'source_gitblobs':{**feature['source_gitblobs'],GAME:blob(game),BOTS:blob(bots)}})
    for name in old:
        if name not in ('Game','SoloTeamBots') and after[name][0].text!=old[name]:
            raise ValueError('OTHER_80_SCRIPT_SOURCE_CHANGED')
    lock['blobs'][GAME]=feature['source_gitblobs'][GAME]=blob(game)
    lock['blobs'][BOTS]=feature['source_gitblobs'][BOTS]=blob(bots)
    report={"schema":"P0D_SPECTATOR_SAFE_STAGING_SOLO_TEAM_BOTS_BATCH_V1",
        "official_rc_head":RC,"official_rc_write":False,
        "parent_place_sha256":PARENT_SHA,"place_sha256":sha(out),"place_bytes":len(out),
        "source_count":82,"unchanged_parent_scripts":80,
        "changed":[GAME,BOTS],"game_blob":blob(game),"bots_blob":blob(bots),
        "source_lock_exact_paths":True,"egg_score_winner_source_byte_exact":True,
        "physical_observer_island_preserved":True,"teamescape_nil_index_fixed":True,
        "private_ai_default_off":True,"android":"NOT_RUN","studio":"NOT_RUN",
        "native":"NOT_RUN","rojo":"NOT_RUN","product":"NO_GO","owner":False}
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        z.writestr(OUTPUT_PLACE,out)
        z.writestr('SOURCE_LOCK.json',json.dumps(lock,indent=2)+'\n')
        z.writestr('RC_FEATURE_LOCK.json',json.dumps(feature,indent=2)+'\n')
        z.writestr('RECEIPT.json',json.dumps(report,indent=2)+'\n')
    if extract_dir:
        manifest=[]
        for name,(e,cl,path) in after.items():
            ext={'Script':'.server.luau','LocalScript':'.client.luau','ModuleScript':'.luau'}[cl]
            source_file=extract_dir/'src'/Path(*path).with_suffix(ext)
            source_file.parent.mkdir(parents=True,exist_ok=True)
            source_file.write_text(e.text,encoding='utf-8')
            manifest.append({'path':'/'.join(path),'kind':cl,'blob':blob(e.text)})
        if len(manifest)!=82:raise ValueError('ROJO_SOURCE_COUNT_DRIFT')
        project={
          'name':'P0DOriginalAuthorSourceParity82',
          'tree':{'$className':'DataModel',
            'ReplicatedStorage':{'$className':'ReplicatedStorage','TrapRaidersShared':{'$path':'src/ReplicatedStorage/TrapRaidersShared'}},
            'ServerScriptService':{'$className':'ServerScriptService','TrapRaidersS1':{'$path':'src/ServerScriptService/TrapRaidersS1'}},
            'StarterPlayer':{'$className':'StarterPlayer','StarterPlayerScripts':{'$path':'src/StarterPlayer/StarterPlayerScripts'}}}}
        (extract_dir/'default.project.json').write_text(json.dumps(project,indent=2))
        (extract_dir/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--author-artifact',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--extract',type=Path)
    a=ap.parse_args()
    print(json.dumps(build(a.author_artifact.read_bytes(),a.out,a.extract),ensure_ascii=False,indent=2))
if __name__=='__main__':main()