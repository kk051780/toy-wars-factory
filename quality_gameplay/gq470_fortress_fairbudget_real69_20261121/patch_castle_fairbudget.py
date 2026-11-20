#!/usr/bin/env python3
"""GQ470 REAL69 castle fair-share art, one original FieldArt Script only.
Source integrity is not Studio/Android/ART approval.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil
from pathlib import Path
BASE='e80973c354f14a0d0088577f3cc1a875454f0f8f'
ROUTE='ServerScriptService/EGGRUMBLE_FlagshipFieldArt'
OLD_SHA='d77fdaf390506f87dfea3064611898320288690f4ef14b97f4e8416eaef40395'
FEATURE='GQ470_FORTRESS_VISUAL_FAIR_BUDGET_REAL69_20261121'
PROJECT='EGGRUMBLE_REAL69.project.json'
RECEIPT='REAL69_LEGACY_INTAKE_RECEIPT.json'
PLACE='EGGRUMBLE_REAL69_PRIVATE.rbxlx'
A='local budgets:{[Instance]:number}={}\n'
A1='''local budgets:{[Instance]:number}={}
-- GQ470_FORTRESS_VISUAL_FAIR_BUDGET_REAL69_20261121
-- Reserve ten existing identity parts per castle, without increasing the
-- existing per-arena 320-Part limit or 19-Part optional castle detail limit.
local MIN_CASTLE_ESSENTIAL_PARTS = 10
-- Keep only this art author's instances; do not count gameplay geometry.
-- Old castles/other art can be removed during a match: prune stale references
-- before every new castle, so the counter never prevents later roofs/crests.
local trackedArt:{[Instance]:{BasePart}}={}
local function recountArenaArt(arena:Instance):{BasePart}
 local active:{BasePart}={}
 for _,p in ipairs(trackedArt[arena] or {}) do
  if p.Parent and p:IsDescendantOf(arena) then table.insert(active,p) end
 end
 trackedArt[arena]=active
 budgets[arena]=#active
 return active
end
local function reserveCastleIdentity(arena:Instance):boolean
 local active=recountArenaArt(arena)
 while #active+MIN_CASTLE_ESSENTIAL_PARTS>MAX_VISUAL_PARTS_PER_ARENA do
  -- Reclaim only expendable decorations, NEVER a roof/keystone/crest.
  local optionalIndex:number?=nil
  for index=#active,1,-1 do
   if active[index]:GetAttribute("GQ470CastleOptional")==true then
    optionalIndex=index
    break
   end
  end
  if not optionalIndex then return false end
  local old=table.remove(active,optionalIndex)
  if old then old:Destroy() end
  budgets[arena]=#active
 end
 return true
end
'''
B=''' builtCastles[castle]=true
 local at=core.Position-Vector3.new(0,14,0)
'''
B1=''' -- Recount live owned decorations and reclaim optional trim, never base art.
 if not reserveCastleIdentity(arena) then return end
 builtCastles[castle]=true
 castle.Destroying:Connect(function() builtCastles[castle]=nil end)
 local at=core.Position-Vector3.new(0,14,0)
'''
C='  if p then used+=1 end\n  return p\n'
C1='''  if p then
   used+=1
   if used>MIN_CASTLE_ESSENTIAL_PARTS then
    p:SetAttribute("GQ470CastleOptional",true)
   end
  end
  return p
'''

D=''' budgets[arena]=(budgets[arena] or 0)+1
 return p
'''
D1=''' budgets[arena]=(budgets[arena] or 0)+1
 local tracked=trackedArt[arena]
 if not tracked then tracked={} trackedArt[arena]=tracked end
 table.insert(tracked,p)
 return p
'''
E=''' builtArenas[arena]=true
 budgets[arena]=budgets[arena] or 0
'''
E1=''' builtArenas[arena]=true
 budgets[arena]=budgets[arena] or 0
 -- Match world replacement must release per-arena accounting references.
 arena.Destroying:Connect(function()
  builtArenas[arena]=nil
  budgets[arena]=nil
  trackedArt[arena]=nil
 end)
'''

def need(ok,code):
    if not ok: raise ValueError('RED_GQ470_CASTLE_FAIRBUDGET_'+code)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def transform(src):
    need(FEATURE not in src,'DOUBLE_APPLY')
    for marker,original in [('BUDGET',A),('CASTLE',B),('ADD',C),('TRACK',D),('ARENA_LIFECYCLE',E)]:
        need(src.count(original)==1,marker+'_ANCHOR')
    for key,expected in [('MAX_VISUAL_PARTS_PER_ARENA',320),('MAX_CASTLE_PARTS',19)]:
        need(re.search(r'(?m)^local '+key+r' = '+str(expected)+r'$',src) is not None,key)
    for key in ('local function drawLaneIdentityVista(','local function drawRouteMarker(',
                'GQ8_RC86_FB015_FORTRESS_DETAIL_VISUAL_PORT_REAL69_20261120',
                'createVisual(arena,deco,name,kind,size,cf,color,material)'):
        need(key in src,'PRIOR_ART_'+key[:14])
    out=(src.replace(A,A1,1).replace(B,B1,1).replace(C,C1,1)
         .replace(D,D1,1).replace(E,E1,1))
    need(out.count(FEATURE)==1 and 'local MAX_CASTLE_PARTS = 19' in out,'ADOPTION')
    need(src.split('local function drawTree(',1)[1]==out.split('local function drawTree(',1)[1],'TERRAIN_DRIFT')
    return out

def selected(root):
    tree=json.loads((root/PROJECT).read_text())['tree']
    result={}
    def visit(node,route=''):
        if '$path' in node:
            p=(root/node['$path']).resolve()
            need(p.is_relative_to(root.resolve()) and p.is_file(),'SOURCE_PATH')
            need(route not in result,'DUP_ROUTE')
            result[route]=p
        else:
            for k,v in node.items():
                if not k.startswith('$') and isinstance(v,dict):
                    visit(v,(route+'/' if route else '')+k)
    visit(tree)
    return result

def apply(root):
    root=root.resolve()
    meta=json.loads((root/RECEIPT).read_text())
    scripts=selected(root)
    need(meta.get('official_branch')=='rc/p0d-s1-kids-rc01' and meta.get('build_head')==BASE,'PARENT')
    need(len(scripts)==len(meta['source_hashes'])==meta['selected_source_count']==69,'SOURCES_69')
    need(set(scripts)==set(meta['source_hashes']) and ROUTE in scripts,'PATH_SET')
    need(meta['source_classes'][ROUTE]=='Script','SOURCE_CLASS')
    before={k:sha(p.read_bytes()) for k,p in scripts.items()}
    need(before==meta['source_hashes'] and before[ROUTE]==OLD_SHA,'SOURCE_LOCK')
    off=root/'OFF69_CASTLE_BUDGET'
    need(not off.exists(),'DOUBLE_APPLY_OFF')
    old=scripts[ROUTE].read_bytes()
    changed=transform(old.decode('utf-8')).encode('utf-8')
    shutil.copytree(root/'sources',off/'sources')
    for fn in (PROJECT,RECEIPT,PLACE): shutil.copy2(root/fn,off/fn)
    scripts[ROUTE].write_bytes(changed)
    after={k:sha(p.read_bytes()) for k,p in selected(root).items()}
    need({k for k in after if after[k]!=before[k]}=={ROUTE},'EXACT_ONE_SOURCE')
    need(all(after[k]==before[k] for k in before if k!=ROUTE),'OTHER_68_EXACT')
    need(selected(off)[ROUTE].read_bytes()==old and set(selected(off))==set(scripts),'EXACT_ROLLBACK')
    meta['source_hashes'][ROUTE]=sha(changed)
    meta['build_head']='PREP_FROM_'+BASE
    meta['gq470_castle_fairbudget']={
       'feature_id':FEATURE,'parent':BASE,'selected_source':ROUTE,
       'other_68_exact':True,'new_runtime_scripts':0,'new_parts':0,
       'visual_budget':320,'per_castle_cap_unchanged':19,
       'reserved_identity_per_castle':10,'max_hero_slots':16,
       'current_landscape_parts':140,'max_16_castle_base_plus_landscape':300,
       'with_pr916_12_ridges':312,'gameplay_authority_changed':False,
       'recounts_alive_visuals_after_castle_deletion':True,
       'castle_and_arena_cleanup_handlers':True,
       'optional_only_reclaimed_for_late_castles':True,
       'rollback':'OFF69_CASTLE_BUDGET','studio':'NOT_TESTED',
       'android15':'NOT_TESTED','human_art':'NOT_TESTED','owner_accepted':False}
    (root/RECEIPT).write_text(json.dumps(meta,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('CASTLE_FAIRBUDGET_REAL69_ONE_SOURCE_OFF_PASS',sha(changed))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base',type=Path,required=True)
    apply(p.parse_args().base)
