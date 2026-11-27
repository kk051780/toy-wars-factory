#!/usr/bin/env python3
"""FB034: ONE truthful combat hit-confirm per authoritative 7-job M1 tap.
Read immutable prior GitHub-native-pass RC90; change only SevenJobArmamentM1.
Never publish, merge, modify canonical game authorities, or weaken SHA locks.
"""
from __future__ import annotations
import difflib, hashlib, json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
PARENT=ROOT/'parent_rc90.zip'
PARENT_FILE='P0D_RC90_SEVEN_JOB_ATTACK_FX_WARP_LOOT_UNDEAD_PRIVATE.rbxlx'
PARENT_SHA='723d0ea4fd7b5d8ae02c9e585dfa2eaafce09e62602c1548d0dc380076de2cd5'
PARENT_BYTES=851781
TARGET='ServerScriptService/TrapRaidersS1/SevenJobArmamentM1'
OUT=ROOT/'P0D_RC91_7JOBS_TRUE_HIT_KO_FEEDBACK_PRIVATE.rbxlx'

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def gitblob(s:str)->str:
 b=s.encode('utf8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def once(src:str,old:str,new:str,tag:str)->str:
 n=src.count(old)
 if n!=1:raise ValueError(f'ANCHOR_DRIFT_{tag}_{n}')
 return src.replace(old,new,1)
def scripts(root:ET.Element)->dict:
 found={}
 def visit(item:ET.Element,base:tuple=()):
  p=item.find('Properties');name=p.findtext("string[@name='Name']") if p is not None else None
  path=base+((name,) if name else ())
  source=next((c for c in p if c.get('name')=='Source'),None) if p is not None else None
  if source is not None:
   key='/'.join(path)
   if key in found:raise ValueError('DOUBLE_SCRIPT_'+key)
   found[key]={'class':item.get('class'),'text':source.text or '', 'element':source}
  for child in item.findall('Item'):visit(child,path)
 for child in root.findall('Item'):visit(child)
 return found

HIT_HELPER='''-- FB034: ONE compact server-confirmed hit receipt after the REAL Horde callback.
-- No hit = no receipt. No permanent HUD; short world-space feedback by attacker.
local function realHitReceipt(job:string,stage:number,origin:Vector3,
        touched:number,defeated:number):()
    if touched<=0 then return end
    local marker=Instance.new("Part")
    marker.Name="P0D_REAL_M1_HIT_RECEIPT"
    marker.Size=Vector3.new(.15,.15,.15)
    marker.Position=origin+Vector3.new(0,3.1,0)
    marker.Anchored=true
    marker.Transparency=1
    marker.CanCollide=false
    marker.CanTouch=false
    marker.CanQuery=false
    marker.CastShadow=false
    marker.Parent=workspace
    local bubble=Instance.new("BillboardGui")
    bubble.Name="RealHitOnly"
    bubble.Size=UDim2.fromOffset(154,42)
    bubble.StudsOffsetWorldSpace=Vector3.new(0,.5,0)
    bubble.MaxDistance=48
    bubble.AlwaysOnTop=false
    bubble.Parent=marker
    local caption=Instance.new("TextLabel")
    caption.Name="RealHordeReceipt"
    caption.Size=UDim2.fromScale(1,1)
    caption.BackgroundTransparency=1
    caption.TextScaled=true
    caption.Font=Enum.Font.GothamBold
    caption.TextColor3=if defeated>0 then GOLD
        else Color3.fromRGB(JOBS[job].rgb[1],JOBS[job].rgb[2],JOBS[job].rgb[3])
    caption.TextStrokeColor3=Color3.fromRGB(22,22,33)
    caption.TextStrokeTransparency=.15
    caption.Text=if defeated>0 then "命中 "..tostring(touched).." / 撃破 "..tostring(defeated)
        else "命中 ×"..tostring(touched)
    caption.Parent=bubble
    -- One receipt per genuine M1 attack, not per enemy/per VFX shape.
    TweenService:Create(caption,TweenInfo.new(.39,Enum.EasingStyle.Quad,
        Enum.EasingDirection.In),{TextTransparency=1,TextStrokeTransparency=1}):Play()
    Debris:AddItem(marker,.48)
    if defeated>0 and stage==3 then
        -- One finisher flash only on server-confirmed actual KO in third combo.
        transientFx("REAL_KO_FINISH",CFrame.new(origin+Vector3.new(0,2.0,0)),
            Vector3.new(1,1,1),GOLD,.30,Vector3.new(3.4,3.4,3.4),
            Vector3.new(0,.45,0),Enum.PartType.Ball)
    end
end
'''
BEFORE='''    return touched,kos
end
return R'''
AFTER='''    -- Only the original authorized hitCallback (MusouHorde:hit) supplies these.
    -- Misses have a swing but NEVER display fake HIT/KO; no score changes.
    if touched>0 then
        realHitReceipt(job,stage,origin,touched,kos)
    end
    return touched,kos
end
return R'''

def patch(source:str)->str:
 result=once(source,'local function unitFacing(direction:Vector3):Vector3',
     HIT_HELPER+'local function unitFacing(direction:Vector3):Vector3','INSERT_RECEIPT')
 result=once(result,BEFORE,AFTER,'CALL_REAL_RECEIPT')
 expected='hitCallback(origin+dir*shot.s,dir,math.clamp(baseDamage*shot.m,1,40))'
 if result.count(expected)!=1:raise ValueError('HIT_AUTH_CHANGED')
 if result.count('realHitReceipt(job,stage,origin,touched,kos)')!=1:raise ValueError('DUPLICATE_FX')
 if result.count('local function roleImpact(')!=1:raise ValueError('VISUAL_PARENT_DRIFT')
 if result.count('local function realHitReceipt(')!=1:raise ValueError('DUPLICATE_RECEIPT')
 return result

def build(parent:bytes|None=None,write:bool=True)->dict:
 if parent is None:
  with ZipFile(PARENT) as z:
   assert set(z.namelist())=={PARENT_FILE,'SOURCE_LOCK.json','RC_FEATURE_LOCK.json','RECEIPT.json'}
   parent=z.read(PARENT_FILE)
 if len(parent)!=PARENT_BYTES or sha(parent)!=PARENT_SHA:raise ValueError('WRONG_PARENT_SHA_OR_BYTES')
 root=ET.fromstring(parent)
 before=scripts(root)
 if len(before)!=86:raise ValueError('PARENT_SOURCE_COUNT_NOT_86')
 with ZipFile(PARENT) as z:
  pinned=json.loads(z.read('SOURCE_LOCK.json'))['scripts']
 if len(pinned)!=86 or set(before)!=set(pinned):raise ValueError('PARENT_LOCK_MISMATCH')
 for k,entry in before.items():
  if pinned[k]!={'class':entry['class'],'blob':gitblob(entry['text'])}:
   raise ValueError('PARENT_SOURCE_BLOB_DRIFT_'+k)
 old=before[TARGET]['text'];new=patch(old)
 before[TARGET]['element'].text=new
 result=ET.tostring(root,encoding='utf-8')
 after=scripts(ET.fromstring(result))
 if set(before)!=set(after) or len(after)!=86:raise ValueError('SCRIPT_INVENTORY_CHANGED')
 changed=[k for k in sorted(before) if before[k]['text']!=after[k]['text']]
 if changed!=[TARGET]:raise ValueError('WRONG_MUTATED_SCRIPTS_'+str(changed))
 for k in before:
  if before[k]['class']!=after[k]['class'] or (k!=TARGET and before[k]['text']!=after[k]['text']):
   raise ValueError('SOURCE_CLOBBER_'+k)
 game=after['ServerScriptService/TrapRaidersS1/Game']['text']
 if game.count('remote.OnServerEvent:Connect(')!=1:raise ValueError('AUTHORITY_DUPLICATE')
 locks={k:{'class':v['class'],'blob':gitblob(v['text'])} for k,v in sorted(after.items())}
 receipt={'feature':'FB034_RC91_GENUINE_HIT_KO_CONFIRM','parent_sha256':PARENT_SHA,
  'place_bytes':len(result),'place_sha256':sha(result),'scripts':86,
  'changed_scripts':changed,'unchanged_scripts':85,
  'original_blob':gitblob(old),'new_blob':gitblob(new),
  'native_luau':'NOT_RUN','rojo':'NOT_RUN','studio':'NOT_RUN','android':'NOT_RUN',
  'owner_accepted':False,'official_rc_write':False,'product':'NO_GO'}
 if write:
  OUT.write_bytes(result)
  (ROOT/'SOURCE_LOCK.json').write_text(json.dumps({'total_scripts':86,'scripts':locks},ensure_ascii=False,indent=2)+'\n')
  (ROOT/'RC_FEATURE_LOCK.json').write_text(json.dumps({'total_sources':86,'source_gitblobs':{'/'.join(k.split('/')[2:]):v['blob'] for k,v in locks.items()}},ensure_ascii=False,indent=2)+'\n')
  (ROOT/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
  (ROOT/'M1_REAL_HIT_ONLY.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='rc90/SevenJobArmamentM1',tofile='rc91/SevenJobArmamentM1')))
 return receipt

if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
