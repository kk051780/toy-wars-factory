#!/usr/bin/env python3
"""P0D FB020 private Studio playable fix: Assassin R wind + guarded 3-route movement.

Input is the genuine native RC82 .rbxlx. Apply only Game+HUD source within XML,
checking exact source anchors and 82-script inventory. Never touches official RC.
"""
from __future__ import annotations
import hashlib
from lxml import etree
from pathlib import Path

GAME = 'Game'
HUD = 'TrapRaidersHUD'

def gitblob(s: str) -> str:
    data = s.encode('utf8')
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def replace_once(s: str, a: str, b: str) -> str:
    found = s.count(a)
    if found != 1: raise AssertionError(f'ANCHOR_DRIFT: {a[:80]} COUNT={found}')
    return s.replace(a, b, 1)

def patched_sources(sources: dict[str, str]) -> dict[str, str]:
    g, h = sources[GAME], sources[HUD]
    g = replace_once(g, 'local windInput:any = {\n        phase = match.phase, team = team, role = roles[player] or "RAIDER",',
      '''local windInput:any = {
        phase = match.phase, team = team,
        role = ((RunService:IsStudio() or privateHordeTrialAllowed())
            and sevenJobSelected[player] == true and sevenJobs[player] == "NINJA")
            and "RAIDER" or (roles[player] or "RAIDER"),''')
    g = replace_once(g, 'if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true then',
      'if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true or RunService:IsStudio() then')
    g = replace_once(g, '''        windInput.arenaMaxZ=math.min(140,grass.Size.Z*.5-6)
    end
    if not WindRules.canActivate(windInput) then return end''',
      '''        windInput.arenaMaxZ=math.min(140,grass.Size.Z*.5-6)
        if RunService:IsStudio() then
            -- Physical floor proof is server-only; no client-provided movement area.
            local params=RaycastParams.new()
            params.FilterType=Enum.RaycastFilterType.Exclude
            params.FilterDescendantsInstances={player.Character}
            local ground=workspace:Raycast(root.Position+Vector3.new(0,1,0),
                Vector3.new(0,-8,0),params)
            if not ground or ground.Normal.Y<0.65
                or not ground.Instance:IsA("BasePart")
                or not ground.Instance.Anchored or not ground.Instance.CanCollide then return end
            -- Use only server recovery's established inner X/Z boundaries.
            windInput.arenaX=root.Position.X
            windInput.arenaZ=root.Position.Z
            windInput.arenaMaxX=178
            windInput.arenaMaxZ=140
        end
    end
    if not WindRules.canActivate(windInput) then return end''')
    cond='(s.role == "RAIDER" or (s.jobStudioPvE==true and s.jobSelected==true and s.job=="NINJA"))'
    h = replace_once(h, 'windButton.Visible = s.phase == "ACTIVE" and s.role == "RAIDER"',
      'windButton.Visible = s.phase == "ACTIVE" and '+cond)
    h = replace_once(h, 'windButton.Active = s.phase == "ACTIVE" and s.role == "RAIDER"',
      'windButton.Active = s.phase == "ACTIVE" and '+cond)
    assert g.count('remote.OnServerEvent:Connect(')==1, 'SECOND_REMOTE_OWNER'
    assert 'WindRules.canActivate(windInput)' in g
    assert 'windInput.arenaMaxX=178' in g
    assert g.count('lastWind[player] = now')==1
    assert h.count('action("WIND_BURST", nil)')==2
    return {GAME: g, HUD: h}

def run(input_path: Path, output_path: Path) -> dict:
    if output_path.exists(): raise FileExistsError(output_path)
    tree=etree.parse(str(input_path),etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True))
    entries=[]
    for item in tree.xpath('//Item'):
        properties=item.find('Properties')
        if properties is None: continue
        name=properties.find('string[@name="Name"]')
        source=next((x for x in properties if x.get('name')=='Source'),None)
        if name is not None and source is not None:
            entries.append((name.text or '',source))
    assert len(entries)==82, f'RC82_EXPECTED: {len(entries)}'
    target={name:source for name,source in entries if name in (GAME,HUD)}
    assert len(target)==2,'EXACT_ONE_GAME_HUD'
    original={name:src.text or '' for name,src in target.items()}
    fixed=patched_sources(original)
    before=[(name, gitblob(el.text or '')) for name,el in entries]
    for name,text in fixed.items(): target[name].text=text
    after=[(name,gitblob(el.text or '')) for name,el in entries]
    changed=[(before[i][0],before[i][1],after[i][1]) for i in range(len(before)) if before[i]!=after[i]]
    assert len(changed)==2 and sorted(x[0] for x in changed)==[GAME,HUD], changed
    etree.ElementTree(tree.getroot()).write(str(output_path),encoding='utf-8',xml_declaration=False,pretty_print=True)
    check=etree.parse(str(output_path),etree.XMLParser(resolve_entities=False,no_network=True))
    stored=[]
    for item in check.xpath('//Item'):
        properties=item.find('Properties')
        if properties is None: continue
        name=properties.find('string[@name="Name"]')
        source=next((x for x in properties if x.get('name')=='Source'),None)
        if name is not None and source is not None: stored.append((name.text or '',gitblob(source.text or '')))
    assert stored==after,'WRITTEN_SCRIPT_SOURCE_DRIFT'
    return {'script_count':82,'unchanged_scripts':80,'changed':changed,
            'output_sha256':hashlib.sha256(output_path.read_bytes()).hexdigest(),
            'bytes':output_path.stat().st_size,'studio_native':'NOT_RUN','publish':False}

if __name__=='__main__':
    import json,sys
    if len(sys.argv)!=3:raise SystemExit('usage: script.py ORIGINAL.rbxlx OUT.rbxlx')
    print(json.dumps(run(Path(sys.argv[1]),Path(sys.argv[2])),ensure_ascii=False,indent=2))
