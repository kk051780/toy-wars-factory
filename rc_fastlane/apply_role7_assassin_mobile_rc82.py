#!/usr/bin/env python3
"""FB004: original #297 Assassin display alias, private-only 7-job selection.
Source-exact cumulative genuine RC82; no second Game/Remote/HP/score.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
GAME="server/Game.server.luau"
HUD="client/HUD.client.luau"
POLICY="server/SevenJobsRules.luau"
PINS={GAME:"a8248896acea4ede4b191bd22485d77a9da18e12",HUD:"14594676e6c7f798d46bde6614ff715972bd6e19",POLICY:"a7253d36cb67df47d4ba65d35af212ed1eb7b5b2"}
OUTPUT={GAME:"56433ee87b89b0d4c1b1a333b12c8535f8d940d0",HUD:"6e03c43fe4e9fc7f315c0e7f0d8018444019ae98",POLICY:"5e04c1b4b62908ebb0dc21db7ae82653d70e8ef8"}
PARENT="P0D_FB003_FB008_PERSONAL_RESULTS_V1"
FEATURE="P0D_ROLE7_ASSASSIN_PRIVATE_MOBILE_SELECT_V1"

def blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def one(txt,old,new,count=1):
 assert txt.count(old)==count,("SOURCE_ANCHOR_DRIFT",old[:80],txt.count(old))
 return txt.replace(old,new,count)
def patch(before):
 assert all(blob(before[k])==v for k,v in PINS.items()),"AUTHORED_REAL82_SOURCE_BLOB_DRIFT"
 g=before[GAME].decode("utf8")
 h=before[HUD].decode("utf8")
 p=before[POLICY].decode("utf8")
 assert g.count("local function privateHordeTrialAllowed(): boolean")==1
 g=one(g,"local sevenJobs: {[Player]: string} = {}\n",
       "local sevenJobs: {[Player]: string} = {}\nlocal sevenJobSelected: {[Player]: boolean} = {}\n")
 g=one(g,'        job = sevenJobs[player] or "WARRIOR",\n',
       '        job = sevenJobs[player] or "WARRIOR",\n        jobSelected = sevenJobSelected[player] == true,\n')
 g=one(g,"        jobStudioPvE = RunService:IsStudio()\n",
       "        jobStudioPvE = (RunService:IsStudio() or privateHordeTrialAllowed())\n")
 g=one(g,"{studio=RunService:IsStudio()\n",
       "{studio=(RunService:IsStudio() or privateHordeTrialAllowed())\n",2)
 g=one(g,"    sevenJobs[player]=job\n    sevenJobLastChoose[player]=now\n",
       "    sevenJobs[player]=job\n    sevenJobSelected[player]=true\n    sevenJobLastChoose[player]=now\n")
 g=one(g,'    sevenJobs[player] = "WARRIOR"\n',
       '    sevenJobs[player] = "WARRIOR"\n    sevenJobSelected[player] = false\n')
 g=one(g,"    sevenJobs[player]=nil\n",
       "    sevenJobs[player]=nil\n    sevenJobSelected[player]=nil\n")
 assert g.count("remote.OnServerEvent:Connect(")==1
 assert g.count("sevenJobSelected[player]")==4
 assert g.count("horde:hit(")==3
 p=one(p,'NINJA={label="忍者",skill="影刃",',
       'NINJA={label="暗殺者",skill="影刃",')
 assert blob(p.encode())==OUTPUT[POLICY],"ORIGINAL_AUTHOR_297_ASSASSIN_ALIAS_NOT_EXACT"
 h=one(h,'{"NINJA","🥷 忍者","影刃"}','{"NINJA","🗡 暗殺者","影刃"}')
 h=one(h,'local jobPanel=Instance.new("Frame")\n',
       'local jobPickerPresented=false\nlocal pendingJobChoice: string?=nil\nlocal jobPanel=Instance.new("Frame")\n')
 h=one(h,"jobPanel.Size=UDim2.fromOffset(184,322)","jobPanel.Size=UDim2.fromOffset(174,304)")
 h=one(h,"UDim2.new(1,-12,0,34),UDim2.new(0,6,1,-8-(7-i)*37)",
       "UDim2.new(1,-12,0,32),UDim2.new(0,6,1,-8-(7-i)*34)")
 h=one(h,'        action("JOB_PICK",entry[1]); jobPanel.Visible=false',
       '        pendingJobChoice=entry[1]\n        action("JOB_PICK",entry[1]) -- Wait for server jobSelected ACK')
 h=one(h,"    if not jobMenu.Visible then jobPanel.Visible=false end",
       "    if not jobMenu.Visible then jobPanel.Visible=false end\n"
       "    if jobMenu.Visible and not jobPickerPresented and s.jobSelected~=true then\n"
       "        jobPickerPresented=true\n        jobPanel.Visible=true\n    end\n"
       "    if pendingJobChoice~=nil and s.jobSelected==true and s.job==pendingJobChoice then\n"
       "        pendingJobChoice=nil\n        jobPanel.Visible=false -- Server confirmed this exact job\n    end")
 assert h.count("pendingJobChoice")==5
 assert h.count('action("JOB_PICK",entry[1])')==1
 assert h.count("jobPanel.Visible=true")==1
 assert h.count("🗡 暗殺者")==1
 after={GAME:g.encode(),HUD:h.encode(),POLICY:p.encode()}
 assert {k:blob(v) for k,v in after.items()}==OUTPUT,"PATCH_OUTPUT_DRIFT"
 return after

def read(root):
 assert root.is_dir() and not root.is_symlink()
 assert not any(x.is_symlink() for x in root.rglob("*"))
 return {p.relative_to(root/"src").as_posix():p.read_bytes() for p in sorted((root/"src").rglob("*.luau"))}
def apply(base,out,enabled):
 assert not out.exists(),"DEST_EXISTS"
 if not enabled:
  print("P0D_ROLE7_ASSASSIN_DEFAULT_OFF_ZERO_WRITE");return False
 base=base.resolve();out=out.absolute()
 assert base.is_dir() and out.parent.is_dir()
 assert not out.is_relative_to(base) and not base.is_relative_to(out)
 before=read(base);assert len(before)==82
 sl=json.loads((base/"SOURCE_LOCK.json").read_text())
 fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text())
 pins={k:blob(v) for k,v in sorted(before.items())}
 assert sl["total_scripts"]==fl["total_sources"]==82
 assert sl["blobs"]==fl["source_gitblobs"]==pins
 assert fl["feature_flags"].get(PARENT) is True
 assert FEATURE not in fl["feature_flags"]
 fixed=patch(before)
 after={**before,**fixed}
 assert len(after)==82 and {k for k in before if before[k]!=after[k]}==set(PINS)
 newpins={k:blob(v) for k,v in sorted(after.items())}
 receipt={"schema":"P0D_ROLE7_ASSASSIN_MOBILE_PRIVATE_REAL82_V1",
  "feature_id":FEATURE,"changed_sources":list(PINS),
  "unchanged79_sources_byte_exact":True,"original_author_297_alias_blob":OUTPUT[POLICY],
  "internal_ninja_key_unchanged":True,"private_eligibility":"PrivateServerId+P0D_PRIVATE_LIVE_HORDE_NINE",
  "public_server_role7":"DISABLED","studio_role7":"UNCHANGED",
  "server_selection_ack_required_to_hide":True,
  "new_game_remote_damage_egg_store":"NONE",
  "android_engine":"NOT_TESTED","seven_roles_full_powers":"NOT_COMPLETED",
  "quality":"PRODUCT_NO_GO","owner_accepted":False,
  "old_source_gitblobs":PINS,"fixed_source_gitblobs":OUTPUT}
 sl["blobs"]=newpins;fl["source_gitblobs"]=newpins
 sl["assassin_private_role7"]=fl["assassin_private_role7"]=receipt
 fl["feature_flags"][FEATURE]=True
 tmp=Path(tempfile.mkdtemp(prefix=".p0d_role7_",dir=str(out.parent)))
 stage=tmp/"candidate"
 try:
  shutil.copytree(base,stage,symlinks=False)
  for k,v in fixed.items():(stage/"src"/k).write_bytes(v)
  for fn,d in (("SOURCE_LOCK.json",sl),("RC_FEATURE_LOCK.json",fl)):
   (stage/fn).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n","utf8")
  assert read(stage)==after and read(base)==before
  os.replace(stage,out)
 finally:shutil.rmtree(tmp,ignore_errors=True)
 print("P0D_ROLE7_ASSASSIN_82_SOURCE_EXACT_PASS",*[newpins[k] for k in PINS])
 return True
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--base",type=Path,required=True)
 a.add_argument("--out",type=Path,required=True)
 a.add_argument("--enabled",choices=("true","false"),required=True)
 v=a.parse_args();apply(v.base,v.out,v.enabled=="true")
