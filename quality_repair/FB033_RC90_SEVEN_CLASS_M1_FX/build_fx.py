#!/usr/bin/env python3
"""Source-exact FB033 real RC89 -> private RC90: distinct 7-role, 3-stage animated M1 impact.

The ONLY changed Luau is SevenJobArmamentM1. All original Game damage/score/Remote
and the other 85 script bodies are preserved byte-for-byte. No Roblox publish.
"""
import hashlib, json, difflib, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent
PARENT=ROOT/'parent_rc89.zip'
PARENT_NAME='P0D_RC89_WIDEFIELD_WARP_STAGE_LOOT_WALL_SAFE_PRIVATE.rbxlx'
PARENT_SHA='03bba976334b188897f4e771d04473229bd82a81db8f6a6fdc44a99d26a14bc9'
OUT=ROOT/'P0D_RC90_SEVEN_JOB_ATTACK_FX_WARP_LOOT_UNDEAD_PRIVATE.rbxlx'
TARGET='ServerScriptService/TrapRaidersS1/SevenJobArmamentM1'

def sha(b):return hashlib.sha256(b).hexdigest()
def blob(s):
 b=s.encode('utf-8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def once(s,before,after,label):
 count=s.count(before)
 if count!=1: raise ValueError('ANCHOR_DRIFT_'+label+'_'+str(count))
 return s.replace(before,after,1)

def read_scripts(root):
 d={}
 def walk(node,parents=()):
  p=node.find('Properties')
  name=p.findtext("string[@name='Name']") if p is not None else None
  chain=parents+((name,) if name else ())
  source=next((x for x in p if x.attrib.get('name')=='Source'),None) if p is not None else None
  if source is not None:
   key='/'.join(chain)
   if key in d:raise ValueError('DUPLICATE_SOURCE_'+key)
   d[key]={'element':source,'body':source.text or '','class':node.attrib.get('class')}
  for child in node.findall('Item'):walk(child,chain)
 for node in root.findall('Item'):walk(node)
 return d

# Minimal-authority change: all code below is server-created, noncolliding VFX.
FX_HELPER='''local TweenService=game:GetService("TweenService")
-- FB033 role-specific 3D strike presentation; NO new combat owner or hitbox.
-- All animated parts are server-made, noncolliding, nonqueryable, auto-Debris.
local function transientFx(name:string,at:CFrame,size:Vector3,color:Color3,
        lifetime:number,goalSize:Vector3,shift:Vector3,
        shape:Enum.PartType?):()
    local p=Instance.new("Part")
    p.Name="P0D_JOB_M1_FX_"..name
    p.Shape=shape or Enum.PartType.Block
    p.Size=size
    p.CFrame=at
    p.Material=Enum.Material.Neon
    p.Color=color
    p.Transparency=.14
    p.Anchored=true
    p.CanCollide=false
    p.CanTouch=false
    p.CanQuery=false
    p.CastShadow=false
    p.Parent=workspace
    -- Spatial bursts contract rapidly as they travel; 0.33s maximum work.
    local tween=TweenService:Create(p,TweenInfo.new(lifetime,
        Enum.EasingStyle.Quad,Enum.EasingDirection.Out),{
            Size=goalSize,Transparency=1,CFrame=at+shift,
        })
    tween:Play()
    Debris:AddItem(p,lifetime+.08)
end
local function roleImpact(job:string,stage:number,where:Vector3,
        direction:Vector3,shotAngle:number):()
    local rgb=JOBS[job].rgb
    local accent=Color3.fromRGB(rgb[1],rgb[2],rgb[3])
    local face=CFrame.lookAt(where,where+direction)
    local heavy=stage==3
    local t=if heavy then .32 else .23
    -- At most 3 animated shapes per hit, 9 per attack. No frame loop.
    if job=="WARRIOR" then
        -- A broad double-edged advancing greatsword sweep.
        for _,sign in ipairs({-1,1}) do
            local at=face*CFrame.new(sign*.60,0,-.8)*CFrame.Angles(0,0,math.rad(sign*32))
            transientFx("GREATSLASH",at,Vector3.new(.23,4.4,.18),
                if sign==1 then GOLD else accent,t,Vector3.new(.04,5.4,.08),
                direction*2.1+Vector3.new(0,.4,0))
        end
    elseif job=="MAGE" then
        -- A moving spell orb + expanding spell halo, distinct from a sword.
        transientFx("SPELL_ORB",face*CFrame.new(0,.8,-.6),
            Vector3.new(1.1,1.1,1.1),accent,t,Vector3.new(2,2,2),
            direction*2.4,Enum.PartType.Ball)
        transientFx("SPELL_HALO",face*CFrame.Angles(0,0,math.rad(90)),
            Vector3.new(.12,2.4,2.4),GOLD,t,Vector3.new(.04,4.8,4.8),
            direction*.6,Enum.PartType.Cylinder)
    elseif job=="NINJA" then
        -- Twin cross-cut blades at opposing angles, a rapid purple X.
        for _,sign in ipairs({-1,1}) do
            local at=face*CFrame.new(sign*.42,.55,-.35)
                *CFrame.Angles(0,0,math.rad(sign*48))
            transientFx("SHADOW_X",at,Vector3.new(.13,3.5,.18),accent,
                .16,Vector3.new(.06,4.2,.12),direction*2.1)
        end
    elseif job=="TRAPPER" then
        -- Three intersecting radiant snare bars: short net cage.
        for i=-1,1 do
            local at=face*CFrame.new(i*1.0,.4,-.25)
                *CFrame.Angles(0,0,math.rad(i*23))
            transientFx("PSY_SNARE",at,Vector3.new(.13,2.6,.15),accent,
                t,Vector3.new(.07,3.8,.08),direction*1.1)
        end
    elseif job=="BUILDER" then
        -- A low gold impact shock disc and falling hammer strike.
        transientFx("HAMMER_RIPPLE",face*CFrame.new(0,-1.3,-.5)
            *CFrame.Angles(0,0,math.rad(90)),Vector3.new(.12,2.8,2.8),
            GOLD,t,Vector3.new(.05,6,6),Vector3.new(0,-.08,0),Enum.PartType.Cylinder)
        transientFx("HAMMER_STRIKE",face*CFrame.new(0,1.1,-.3),
            Vector3.new(2.1,.45,.55),accent,t,Vector3.new(3,.07,.6),
            Vector3.new(0,-1.7,0))
    elseif job=="BEAST_TAMER" then
        -- Long green spear thrust and a trailing tame-beast spark.
        transientFx("SPEAR_LANCE",face*CFrame.new(0,.5,-1.5),
            Vector3.new(.24,.26,4.2),accent,t,Vector3.new(.08,.1,7.1),
            direction*2.1)
        transientFx("BEAST_SPARK",face*CFrame.new(0,.6,-.6),
            Vector3.new(.8,.8,.8),GOLD,t,Vector3.new(1.6,1.6,1.6),
            direction*1.4,Enum.PartType.Ball)
    else
        -- Necromancer: two cursed scythe streaks around a death orb.
        for _,sign in ipairs({-1,1}) do
            transientFx("CURSED_SCYTHE",face*CFrame.new(sign*.7,.4,-.5)
                *CFrame.Angles(0,0,math.rad(sign*58)),
                Vector3.new(.15,2.6,.22),accent,t,Vector3.new(.06,4.3,.1),
                direction*1.7+Vector3.new(0,.5,0))
        end
        transientFx("SOUL_ORB",face*CFrame.new(0,.6,-.5),
            Vector3.new(.9,.9,.9),Color3.fromRGB(143,77,200),t,
            Vector3.new(1.75,1.75,1.75),direction*1.1,Enum.PartType.Ball)
    end
end
'''

ORIG='''        -- Distinct visible short attack arc at the SAME server-owned hit direction.
        -- No hitboxes or damage authority; real Horde:hit is still called below.
        local arc=Instance.new("Part")
        arc.Name="P0D_M1_HIT_ARC_"..job
        arc.Size=Vector3.new(if job=="WARRIOR" then 6 elseif job=="NINJA" then 2.5 else 4,
            .18, if job=="BEAST_TAMER" then 5 else 2.3)
        arc.Anchored=true;arc.CanCollide=false;arc.CanTouch=false;arc.CanQuery=false
        arc.CastShadow=false
        arc.Material=Enum.Material.Neon
        local color=JOBS[job].rgb
        arc.Color=Color3.fromRGB(color[1],color[2],color[3])
        arc.Transparency=.38
        local impact=origin+dir*(shot.s+2)
        arc.CFrame=CFrame.lookAt(impact,impact+dir)
        arc.Parent=workspace
        Debris:AddItem(arc,.20)
'''
NEW='''        -- Three-stage class-specific attack FX at the same authorized hit direction.
        -- Cosmetic only; below hitCallback is the original sole damage owner.
        local impact=origin+dir*(shot.s+.65)
        roleImpact(job,stage,impact,dir,shot.a)
'''

def patch(source):
 out=once(source,'local Debris=game:GetService("Debris")\n',
            'local Debris=game:GetService("Debris")\n'+FX_HELPER,'FX_SERVICE')
 out=once(out,ORIG,NEW,'VFX_REPLACE')
 if out.count('hitCallback(origin+dir*shot.s,dir,math.clamp(baseDamage*shot.m,1,40))')!=1:
  raise ValueError('ATTACK_AUTH_CHANGED')
 if 'RunService.Heartbeat' in out or 'remote:' in out or 'Players:' in out:
  raise ValueError('NEW_AUTHORITY_REJECTED')
 return out

def build(parent=None, write=True):
 if parent is None:
  with ZipFile(PARENT) as z:
   assert sorted(z.namelist())==[PARENT_NAME,'RC_FEATURE_LOCK.json','RECEIPT.json','SOURCE_LOCK.json'] or set(z.namelist())=={PARENT_NAME,'RC_FEATURE_LOCK.json','RECEIPT.json','SOURCE_LOCK.json'},z.namelist()
   parent=z.read(PARENT_NAME)
 if sha(parent)!=PARENT_SHA or len(parent)!=847767:raise ValueError('WRONG_PARENT_SHA_OR_BYTES')
 root=ET.fromstring(parent);before=read_scripts(root)
 if len(before)!=86:raise ValueError('WRONG_PARENT_SCRIPT_COUNT')
 src=before[TARGET]['body'];other=patch(src)
 before[TARGET]['element'].text=other
 result=ET.tostring(root,encoding='utf-8')
 after=read_scripts(ET.fromstring(result))
 if set(before)!=set(after) or len(after)!=86:raise ValueError('SCRIPT_INVENTORY_CHANGED')
 changes=[k for k in before if before[k]['body']!=after[k]['body']]
 if changes!=[TARGET]:raise ValueError('WRONG_CHANGED_SOURCES_'+repr(changes))
 for k in before:
  if before[k]['class']!=after[k]['class'] or (k!=TARGET and before[k]['body']!=after[k]['body']):
   raise ValueError('PARENT_SOURCE_DRIFT_'+k)
 if sum(k.endswith('/Game') for k in after)!=1:raise ValueError('DUPLICATE_GAME')
 game=after['ServerScriptService/TrapRaidersS1/Game']['body']
 if game.count('remote.OnServerEvent:Connect(')!=1:raise ValueError('DUPLICATE_REMOTE')
 manifests={k:{'class':v['class'],'blob':blob(v['body'])} for k,v in sorted(after.items())}
 receipt={'feature':'FB033_RC90_SEVEN_DISTINCT_ANIMATED_M1','parent_sha256':PARENT_SHA,
  'place_bytes':len(result),'place_sha256':sha(result),'scripts':86,
  'changed_scripts':changes,'unchanged_scripts':85,'original_blob':blob(src),
  'new_blob':blob(other),'native_luau':'NOT_RUN','rojo':'NOT_RUN',
  'studio':'NOT_RUN','android':'NOT_RUN','owner_accepted':False,
  'official_rc_write':False,'product':'NO_GO'}
 if write:
  OUT.write_bytes(result)
  (ROOT/'SOURCE_LOCK.json').write_text(json.dumps({'total_scripts':86,'scripts':manifests},indent=2,ensure_ascii=False)+'\n')
  (ROOT/'RC_FEATURE_LOCK.json').write_text(json.dumps({'total_sources':86,'source_gitblobs':{'/'.join(k.split('/')[2:]):v['blob'] for k,v in sorted(manifests.items())}},indent=2)+'\n')
  (ROOT/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
  (ROOT/'M1_FX_ONLY.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),other.splitlines(True),fromfile='rc89/SevenJobArmamentM1',tofile='rc90/SevenJobArmamentM1')))
 return receipt

if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
