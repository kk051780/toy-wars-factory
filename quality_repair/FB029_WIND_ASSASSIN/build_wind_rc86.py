#!/usr/bin/env python3
"""FB029: source-locked port of original-author #476 FB020 Assassin wind repair.

Independent private 86-script RC86 stage loot + undead source remains unchanged
except for existing Game and HUD. No main/official RC or Publish writes.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, difflib, xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
PARENT_ZIP=HERE/'parent_rc86_ci.zip'
PARENT_SHA='11fa894c4ebfa2303e3f7cef8590d14a6a26f359699b6eda3d2e692bc161c707'
GAME_PATH='server/Game.server.luau'
HUD_PATH='client/HUD.client.luau'
OUTPUT=HERE/'P0D_RC86_STAGE_WEAPONS_UNDEAD_ASSASSIN_WIND_PRIVATE.rbxlx'

def sha(b):return hashlib.sha256(b).hexdigest()
def blob(s):
    b=s.encode('utf8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def replace1(text, old, new, label):
    n=text.count(old)
    if n!=1:raise ValueError(f'SOURCE_DRIFT_{label}_COUNT_{n}')
    return text.replace(old,new,1)

def source_nodes(root):
    found={}
    for p in root.iter():
        for i in p.findall('Item'):
            pr=i.find('Properties')
            if pr is None:continue
            name=pr.findtext("string[@name='Name']")
            s=pr.find("string[@name='Source']")
            if name and s is not None:
                if name in found:raise ValueError('DUPLICATE_SCRIPT_'+name)
                found[name]=s
    return found

def patch(game, hud):
    # Exactly the author-approved #476 FB020 wind role policy. Preserve the
    # physical source GrassArena size and original MapBuilder coordinates.
    game=replace1(game,
      'local windInput:any = {\n        phase = match.phase, team = team, role = roles[player] or "RAIDER",',
      '''local windInput:any = {
        phase = match.phase, team = team,
        role = ((RunService:IsStudio() or privateHordeTrialAllowed())
            and sevenJobSelected[player] == true and sevenJobs[player] == "NINJA")
            and "RAIDER" or (roles[player] or "RAIDER"),''','SERVER_NINJA_ALIAS')
    game=replace1(game,
      'if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true then',
      'if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true or RunService:IsStudio() then',
      'SERVER_STUDIO_ADAPTIVE')
    game=replace1(game,
      '''        windInput.arenaMaxZ=math.min(140,grass.Size.Z*.5-6)
    end
    if not WindRules.canActivate(windInput) then return end''',
      '''        windInput.arenaMaxZ=math.min(140,grass.Size.Z*.5-6)
        if RunService:IsStudio() then
            -- FB029: only an actual anchored collidable walkable floor permits wind.
            -- Use the ORIGINAL live map bounds (no oversized 178x140 expansion).
            local params=RaycastParams.new()
            params.FilterType=Enum.RaycastFilterType.Exclude
            params.FilterDescendantsInstances={player.Character}
            local ground=workspace:Raycast(root.Position+Vector3.new(0,1,0),
                Vector3.new(0,-8,0),params)
            if not ground or ground.Normal.Y<0.65
                or not ground.Instance:IsA("BasePart")
                or not ground.Instance.Anchored or not ground.Instance.CanCollide then return end
        end
    end
    if not WindRules.canActivate(windInput) then return end''',
      'SERVER_WALKABLE_GROUND')
    # Avoid double overlay with Guardian trap on touch. Only the affected
    # character gets the second button: no persistent intrusive UI.
    hud=replace1(hud,
      '    windButton.Visible = s.phase == "ACTIVE" and s.role == "RAIDER"',
      '''    local assassinWind=(s.jobStudioPvE==true and s.jobSelected==true
        and s.job=="NINJA")
    windButton.Visible=s.phase=="ACTIVE" and (s.role=="RAIDER" or assassinWind)
    windButton.Position=if assassinWind and s.role=="GUARDIAN"
        then UDim2.new(1,-260,1,-110) else UDim2.new(1,-140,1,-110)''',
      'HUD_VISIBLE_TOUCH_POSITION')
    hud=replace1(hud,
      '    windButton.Active = s.phase == "ACTIVE" and s.role == "RAIDER"',
      '    windButton.Active = s.phase == "ACTIVE" and (s.role=="RAIDER" or assassinWind)',
      'HUD_ACTIVE')
    if game.count('remote.OnServerEvent:Connect(')!=1:raise ValueError('SECOND_REMOTE_OWNER')
    if hud.count('action("WIND_BURST", nil)')!=2:raise ValueError('SECOND_CLIENT_COMMAND')
    if game.count('lastWind[player] = now')!=1:raise ValueError('WIND_COOLDOWN_DRIFT')
    return game,hud

def build():
    with ZipFile(PARENT_ZIP) as z:
        places=[n for n in z.namelist() if n.endswith('.rbxlx')]
        if len(places)!=1:raise ValueError('PARENT_PLACE_COUNT')
        parent=z.read(places[0]);lock=json.loads(z.read('SOURCE_LOCK.json'))
        feature=json.loads(z.read('RC_FEATURE_LOCK.json'))
    if sha(parent)!=PARENT_SHA or len(parent)!=843641:raise ValueError('SOURCE_DRIFT_PARENT86')
    if lock['total_scripts']!=86 or feature['total_sources']!=86 or lock['blobs']!=feature['source_gitblobs']:
        raise ValueError('SOURCE_DRIFT_PARENT_LOCK')
    root=ET.fromstring(parent)
    nodes=source_nodes(root)
    originals={k:n.text for k,n in nodes.items()}
    if len(originals)!=86 or blob(originals['Game'])!=lock['blobs'][GAME_PATH] or blob(originals['TrapRaidersHUD'])!=lock['blobs'][HUD_PATH]:
        raise ValueError('SOURCE_DRIFT_BASE_SCRIPTS')
    new_game,new_hud=patch(originals['Game'],originals['TrapRaidersHUD'])
    nodes['Game'].text=new_game;nodes['TrapRaidersHUD'].text=new_hud
    lock['blobs'][GAME_PATH]=feature['source_gitblobs'][GAME_PATH]=blob(new_game)
    lock['blobs'][HUD_PATH]=feature['source_gitblobs'][HUD_PATH]=blob(new_hud)
    result=ET.tostring(root,encoding='utf-8')
    actual={k:v.text for k,v in source_nodes(ET.fromstring(result)).items()}
    if len(actual)!=86:raise ValueError('NEW_SOURCE_SCRIPT_COUNT')
    if sorted(blob(s) for s in actual.values())!=sorted(lock['blobs'].values()):raise ValueError('SOURCE_LOCK_MISMATCH')
    for name,old in originals.items():
        if name not in ('Game','TrapRaidersHUD') and actual[name]!=old:
            raise ValueError('SOURCE_REGRESSION_'+name)
    OUTPUT.write_bytes(result)
    (HERE/'SOURCE_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (HERE/'RC_FEATURE_LOCK.json').write_text(json.dumps(feature,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for label,old,new in [('Game',originals['Game'],new_game),('HUD',originals['TrapRaidersHUD'],new_hud)]:
        (HERE/('FB029_'+label+'_only.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original86_'+label,tofile='wind_repaired86_'+label)),encoding='utf8')
    receipt={'feature':'FB029_ASSASSIN_WIND_PORT_REUSE_ORIGINAL_AUTHOR_476',
       'parent_sha256':PARENT_SHA,'place_sha256':sha(result),'bytes':len(result),
       'source_count':86,'unchanged_sources':84,
       'changed':[GAME_PATH,HUD_PATH],
       'original_author_patch':'quality_repair/fb020_wind_assassin_studio_patch.py PR#476',
       'original_undead_gitblob':lock['blobs']['server/UndeadSquad.luau'],
       'original_loot_gitblob':lock['blobs']['server/StagePickupLoot.luau'],
       'native_luau':'NOT_RUN','rojo':'NOT_RUN','studio':'NOT_RUN','android':'NOT_RUN',
       'official_rc_write':False,'owner_accepted':False,'product':'NO_GO'}
    (HERE/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return receipt
if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
