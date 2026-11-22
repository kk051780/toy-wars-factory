#!/usr/bin/env python3
"""REAL69 Studio candidate: human-readable Roblox Tool hotbar, preserved IDs.

Requires the immutable official source artifact for 6c2338b4. Produces only
2 existing-source changes; all gameplay server authority and 67 other scripts
remain byte-identical. This is PREP, never a new formal RC/Studio approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = '6c2338b44db1c772bab0d688b2aece2e3aa8aae2'
MARK = 'GQ470_HUD_TOOL_DISPLAY_IDS_REAL69_20261120'
COMBAT = 'ServerScriptService/EGGRUMBLE_SevenRoleCombat'
HUD = 'StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime'
PROJECT = 'EGGRUMBLE_REAL69.project.json'
RECEIPT = 'REAL69_LEGACY_INTAKE_RECEIPT.json'

def require(x: bool, msg: str) -> None:
    if not x:
        raise ValueError('RED_HUD_DISPLAY_' + msg)

def replace_once(src: str, old: str, new: str, label: str) -> str:
    require(src.count(old) == 1, label + '_ANCHOR_DRIFT')
    return src.replace(old, new, 1)

def patch_combat(src: str) -> str:
    require(MARK not in src, 'COMBAT_ALREADY_PATCHED')
    require('player.UserId' in src, 'COMBAT_P0_REPAIR_MISSING')
    src = replace_once(src, 'function HeroCombat.equip(session:any,p:Player,role:string):()', '''-- ''' + MARK + ''': external display labels only, internal Tool identity kept.
local function isRoleOwnedTool(item:Instance):boolean
 if not item:IsA("Tool") then return false end
 local identity=item:GetAttribute("EGGRUMBLE_InternalToolId")
 if type(identity)=="string" then
  return string.sub(identity,1,16)=="EGGRUMBLE_SKILL_"
   or identity=="EGGRUMBLE_MUSOU_AWAKEN"
   or identity=="EGGRUMBLE_BASIC_ATTACK"
   or identity=="EGGRUMBLE_DODGE_STEP"
 end
 -- Backwards compatibility: old Tool names from earlier respawns.
 return string.sub(item.Name,1,16)=="EGGRUMBLE_SKILL_"
  or item.Name=="EGGRUMBLE_MUSOU_AWAKEN"
  or item.Name=="EGGRUMBLE_BASIC_ATTACK"
  or item.Name=="EGGRUMBLE_DODGE_STEP"
end
function HeroCombat.equip(session:any,p:Player,role:string):()''', 'COMBAT_HELPER')
    old_cleanup='if instance:IsA("Tool") and (string.sub(instance.Name,1,16)=="EGGRUMBLE_SKILL_" or instance.Name=="EGGRUMBLE_MUSOU_AWAKEN" or instance.Name=="EGGRUMBLE_BASIC_ATTACK" or instance.Name=="EGGRUMBLE_DODGE_STEP") then instance:Destroy() end'
    src=replace_once(src,old_cleanup,'if isRoleOwnedTool(instance) then instance:Destroy() end','EQUIP_CLEANUP')
    old_clear='if item:IsA("Tool") and (string.sub(item.Name,1,16)=="EGGRUMBLE_SKILL_" or item.Name=="EGGRUMBLE_MUSOU_AWAKEN" or item.Name=="EGGRUMBLE_BASIC_ATTACK" or item.Name=="EGGRUMBLE_DODGE_STEP") then item:Destroy() end'
    src=replace_once(src,old_clear,'if isRoleOwnedTool(item) then item:Destroy() end','CLEAR_CLEANUP')
    src=replace_once(src, 'tool.Name="EGGRUMBLE_SKILL_"..slot.."_"..data.skills[index]', '''tool:SetAttribute("EGGRUMBLE_InternalToolId", "EGGRUMBLE_SKILL_"..slot.."_"..data.skills[index])
  tool.Name="技"..slot.."・"..data.skills[index]''','SKILL_NAME')
    src=replace_once(src,'musouTool.Name="EGGRUMBLE_MUSOU_AWAKEN"','''musouTool:SetAttribute("EGGRUMBLE_InternalToolId","EGGRUMBLE_MUSOU_AWAKEN")
 musouTool.Name="無双覚醒"''','MUSOU_NAME')
    src=replace_once(src,'''core.Name=if action=="BASIC" then "EGGRUMBLE_BASIC_ATTACK"
    else "EGGRUMBLE_DODGE_STEP"''','''core:SetAttribute("EGGRUMBLE_InternalToolId",if action=="BASIC" then "EGGRUMBLE_BASIC_ATTACK" else "EGGRUMBLE_DODGE_STEP")
  core.Name=if action=="BASIC" then "通常攻撃" else "回避"''','CORE_NAME')
    require(src.count(MARK)==1 and 'player.UserId' in src,'COMBAT_P0_PRESERVATION')
    return src

def patch_hud(src: str) -> str:
    require(MARK not in src, 'HUD_ALREADY_PATCHED')
    src=replace_once(src,'local function toolWith(prefix)','''-- '''+MARK+''': never trust a display label as a gameplay identifier.
local function toolIdentity(t:Tool):string
 local internal=t:GetAttribute("EGGRUMBLE_InternalToolId")
 return if type(internal)=="string" then internal else t.Name
end
local function toolWith(prefix)''','HUD_HELPER')
    src=replace_once(src, 'if child:IsA("Tool") and string.sub(child.Name,1,#prefix)==prefix then', 'if child:IsA("Tool") and string.sub(toolIdentity(child),1,#prefix)==prefix then','HUD_FILTER')
    src=replace_once(src, 'if tool.Name==name then return tool end','if toolIdentity(tool)==name then return tool end','HUD_EXACT')
    src=replace_once(src, 'if string.match(tool.Name,"^EGGRUMBLE_SKILL_"..slot.."_") then return tool end', 'if string.match(toolIdentity(tool),"^EGGRUMBLE_SKILL_"..slot.."_") then return tool end','HUD_SLOT')
    src=replace_once(src, 'if t then table.insert(options,{id=slot,name=slot.." "..t.Name:sub(19),tool=t}) end', '''if t then
    local label=t.Name
    if string.sub(label,1,16)=="EGGRUMBLE_SKILL_" then
     label="技"..slot.."・"..label:sub(19)
    end
    table.insert(options,{id=slot,name=label,tool=t})
   end''','HUD_DRAWER')
    require(src.count(MARK)==1 and 'GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120' in src,
            'HUD_FB019_PRESERVATION')
    src=replace_once(src, ' if mode~="TEAM" and mode~="BR" then hideLegacyToast();return end', ' if mode~="TEAM" and mode~="BR" and mode~="BATTLE_ROYALE" then hideLegacyToast();return end', 'HUD_DISCOVERY_CANONICAL_BR')
    return src

def selected_map(root: Path) -> dict[str,Path]:
    data=json.loads((root/PROJECT).read_text(encoding='utf-8'))
    result={}
    def walk(node,path):
        if isinstance(node,dict):
            if '$path' in node: result[path]=root/node['$path']
            for key,val in node.items():
                if not key.startswith('$'): walk(val, path+'/'+key if path else key)
    walk(data['tree'],'')
    return result

def apply(root:Path, official_ci_head:str|None=None)->None:
    paths=selected_map(root)
    receipt=json.loads((root/RECEIPT).read_text())
    require(len(paths)==69 and COMBAT in paths and HUD in paths,'69_SELECTED_ROUTES')
    require(receipt.get('build_head')==(official_ci_head or BASE) and len(receipt.get('source_hashes',{}))==69,'BASE_RECEIPT')
    old={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
    require(old==receipt['source_hashes'],'RECEIPT_HASH_DRIFT')
    rollback=root/'off69_hud_labels'
    require(not rollback.exists(),'ROLLBACK_COLLISION')
    for k in (COMBAT,HUD):
        target=rollback / paths[k].relative_to(root)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(paths[k],target)
    for k,fn in ((COMBAT,patch_combat),(HUD,patch_hud)):
        paths[k].write_text(fn(paths[k].read_text(encoding='utf-8')),encoding='utf-8')
    after={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
    require({k for k in old if old[k]!=after[k]}=={COMBAT,HUD},'EXACT_2_SOURCES')
    require(all(old[k]==after[k] for k in old if k not in (COMBAT,HUD)),'OTHER_67_EXACT')
    receipt['source_hashes'].update({COMBAT:after[COMBAT],HUD:after[HUD]})
    receipt['build_head']=official_ci_head or 'PREP_HUD_LABELS_FROM_'+BASE
    receipt['gq470_fb015_hud_tool_labels']={
      'feature_id':MARK,'base_official_head':BASE,'only_modified':[COMBAT,HUD],
      'source_count':69,'unchanged_selected_sources':67,
      'engine_authority_changed':False,'server_tool_activation_preserved':True,
      'internal_tool_ids_retained_as_attributes':True,
      'fallback_legacy_names':True,'rollback':'off69_hud_labels',
      'native_rojo_off69':'NOT_TESTED','studio_android_fun':'NOT_TESTED',
      'owner_accepted':False}
    (root/RECEIPT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('GQ470_REAL69_HUD_LABELS_TWO_SOURCES_67_UNCHANGED_SOURCE_PASS')

def selftest()->None:
    root=Path(__file__).resolve().parent
    # A CI environment must separately extract immutable official source artifact.
    assert MARK and BASE
    for func in (patch_combat,patch_hud):
        try: func('unrelated nonmatching source')
        except ValueError: pass
        else: raise AssertionError('source drift accepted')
    print('GQ470_HUD_PATCH_DRIFT_NEGATIVE_PASS')

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--base',type=Path)
    a.add_argument('--head',type=str,default=None,
                   help='same-run official/PR source-composite head; only certified B may adopt')
    a.add_argument('--self-test',action='store_true')
    opts=a.parse_args()
    if opts.self_test: selftest()
    else:
        require(opts.base is not None,'MISSING_OFFICIAL_ARTIFACT')
        apply(opts.base,opts.head)
