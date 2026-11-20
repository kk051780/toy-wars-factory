#!/usr/bin/env python3
"""Exact-source REAL69 visual-only confirmed-hit matte streak A candidate.

No server authority, world Parts, physics, Remote, screen-filling HUD or
unbounded render loop. Does not claim Studio/Android/human ART approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import shutil

FORMAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel"
OLD_SHA = "d378d6a356b9462c99deddc19b4393d79bf113225047a057658d1782e1e8a32e"
FEATURE = "GQ470_FB015_CONFIRMED_HIT_MATTE_STREAK_REAL69_20261121"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
VISUAL = f'''-- {FEATURE}
-- Two preallocated, noninteractive matte UI strokes. Only actual server-confirmed
-- impact sequence animates them; no new Part, Remote or per-frame connection.
local hitStreaks={{}}
for i,angle in ipairs({{-37,37}}) do
 local streak=Instance.new("Frame")
 streak.Name="ConfirmedMatteStreak_"..i
 streak.AnchorPoint=Vector2.new(.5,.5)
 streak.Position=UDim2.fromScale(.5,.5)
 streak.Size=UDim2.fromOffset(8,2)
 streak.Rotation=angle
 streak.BackgroundColor3=tones.WARRIOR
 streak.BackgroundTransparency=1
 streak.BorderSizePixel=0
 streak.ZIndex=2
 streak.Visible=false
 streak.Parent=mark
 table.insert(hitStreaks,streak)
end
'''
A = 'local function reduced():boolean\n'
B = '''player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(function()
 if reduced() then return end
'''
B_NEW = '''player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(function()
 if reduced() or player:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
'''
C = ''' TweenService:Create(mark,TweenInfo.new(.16,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
  {Size=UDim2.fromOffset(26,26)}):Play()
'''
C_NEW = ''' -- Short dual diagonal strike gives a recognizable confirmed-hit accent.
 -- Fixed two frames, 0.17s fade, small central footprint, no dynamic Instances.
 for i,streak in ipairs(hitStreaks) do
  streak.BackgroundColor3=c
  streak.BackgroundTransparency=.24
  streak.Size=UDim2.fromOffset(8,2)
  streak.Position=UDim2.fromScale(.5,.5)
  streak.Visible=true
  TweenService:Create(streak,TweenInfo.new(.17,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),{
   Size=UDim2.fromOffset(34,2),
   Position=UDim2.new(.5,if i==1 then -4 else 4,.5,if i==1 then -5 else 5),
   BackgroundTransparency=1,
  }):Play()
 end
''' + C
D = '''task.delay(.17,function()
  if thisPulse==pulse and mark.Parent then mark.Visible=false end
 end)
'''
D_NEW = '''task.delay(.17,function()
  if thisPulse==pulse and mark.Parent then
   mark.Visible=false
   for _,streak in ipairs(hitStreaks) do streak.Visible=false end
  end
 end)
'''

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def transform(s: str) -> str:
    assert FEATURE not in s, "RED_ALREADY_APPLIED"
    assert 'if not RunService:IsStudio() then return end' in s, "RED_STUDIO_FENCE"
    assert 'local IMPACT_WINDOW=.115' in s and 'local RECENT_CD=.12' in s, "RED_IMPACT_GUARDS"
    assert 'local fxSecondaryNames={' in s and 'local function pickObjective(' in s, "RED_OTHER_LANES"
    for a in (A, B, C, D):
        assert s.count(a) == 1, "RED_ANCHOR_" + a[:25]
    result = s.replace(A,VISUAL + A,1).replace(B,B_NEW,1).replace(C,C_NEW,1).replace(D,D_NEW,1)
    assert result.count(FEATURE)==1 and result.count('ConfirmedMatteStreak_')==1, "RED_STREAK_MISSING"
    assert result.count('Instance.new("Frame")')==s.count('Instance.new("Frame")')+1, "RED_UI_ONLY"
    for bad in ('RemoteEvent', 'TakeDamage(', 'DataStoreService', 'MarketplaceService', 'Instance.new("Part")', 'RenderStepped:Connect('):
        assert bad not in VISUAL+C_NEW, "RED_AUTHORITY_OR_PART"
    assert 'if reduced() or player:GetAttribute("EGGRUMBLE_Eliminated")==true' in result
    assert result.replace(VISUAL,'',1).replace(B_NEW,B,1).replace(C_NEW,C,1).replace(D_NEW,D,1)==s, "RED_NOT_EXACT_TRANSFORM"
    return result


def selected(root: pathlib.Path) -> dict[str,pathlib.Path]:
    project=json.loads((root/PROJECT).read_text())
    result={}
    def walk(node:dict,route:str=''):
        if not isinstance(node,dict):return
        if '$path' in node:
            p=(root/node['$path']).resolve()
            assert p.is_relative_to(root.resolve()) and p.is_file(),"RED_PROJECT_PATH"
            assert route not in result,"RED_DUPLICATE_ROUTE"
            result[route]=p
        for key,child in node.items():
            if not key.startswith('$'):walk(child,route+'/'+key if route else key)
    walk(project['tree'])
    assert len(result)==69 and TARGET in result,"RED_ROUTE_COUNT"
    assert result[TARGET].name.endswith('.client.luau'),"RED_TARGET_CLASS"
    return result


def apply(source:pathlib.Path,dest:pathlib.Path):
    assert source.is_dir() and not dest.exists(),"RED_INPUT_OR_DEST"
    receipt=json.loads((source/RECEIPT).read_text())
    paths=selected(source)
    assert receipt.get('build_head')==FORMAL and receipt.get('canonical_build') is True, "RED_FORMAL_HEAD"
    assert len(receipt.get('source_hashes',{}))==69,"RED_RECEIPT_69"
    for route,path in paths.items():
        assert sha(path.read_bytes())==receipt['source_hashes'].get(route),"RED_ORIGINAL_SOURCE_"+route
    raw=paths[TARGET].read_bytes()
    assert sha(raw)==OLD_SHA,"RED_WRONG_TARGET_SHA"
    new=transform(raw.decode('utf-8')).encode('utf-8')
    shutil.copytree(source,dest)
    dst=selected(dest)[TARGET]
    dst.write_bytes(new)
    out_paths=selected(dest)
    changes=[k for k in paths if paths[k].read_bytes()!=out_paths[k].read_bytes()]
    assert changes==[TARGET],"RED_1_OF_69_SOURCE_LOCK"
    assert (source/PROJECT).read_bytes()==(dest/PROJECT).read_bytes(),"RED_PROJECT_DRIFT"
    assert (source/'EGGRUMBLE_REAL69_PRIVATE.rbxlx').read_bytes()==(dest/'EGGRUMBLE_REAL69_PRIVATE.rbxlx').read_bytes(),"RED_ORIGINAL_PLACE_DRIFT"
    report={'feature_id':FEATURE,'formal_head':FORMAL,'selected_source_count':69,
            'source_modified':1,'source_byte_exact':68,'route':TARGET,'class':'LocalScript',
            'original_sha256':OLD_SHA,'candidate_sha256':sha(new),
            'original_bytes':len(raw),'candidate_bytes':len(new),
            'added_world_parts':0,'added_ui_frames':2,'new_remotes':0,'engine':'NOT_TESTED',
            'android':'NOT_TESTED','human_art':'NOT_TESTED','owner_accepted':False}
    (dest/'GQ470_HIT_STREAK_SOURCE_QA.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report


def self_test():
    original=(f'--!strict\nif not RunService:IsStudio() then return end\n'
              f'local IMPACT_WINDOW=.115\nlocal RECENT_CD=.12\n'
              f'local fxSecondaryNames={{\nlocal function pickObjective(\n'
              f'{A}{B}{C}{D}')
    good=transform(original)
    assert 'ConfirmedMatteStreak_' in good and 'EGGRUMBLE_Eliminated' in good
    mutants=[good,original.replace(A,''),original.replace(B,'no impact'),
             original.replace(C,'no mark'),original.replace(D,'no cleanup'),
             original.replace('local IMPACT_WINDOW=.115','local IMPACT_WINDOW=.35'),
             original.replace('if not RunService:IsStudio() then return end',''),
             original.replace('local fxSecondaryNames={','')]
    for bad in mutants:
        try:transform(bad)
        except AssertionError:continue
        raise AssertionError('RED_MUTATION_ADMITTED')
    print('GQ470_HIT_STREAK_8_MUTATION_NEGATIVES_PASS')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--source',type=pathlib.Path)
    ap.add_argument('--dest',type=pathlib.Path)
    args=ap.parse_args()
    if args.self_test:self_test();return
    assert args.source and args.dest
    print(json.dumps(apply(args.source,args.dest),indent=2,ensure_ascii=False))
if __name__=='__main__': main()
