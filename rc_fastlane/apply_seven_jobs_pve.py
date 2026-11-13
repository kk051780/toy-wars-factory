#!/usr/bin/env python3
"""Build exact P0D 54->55 SevenJobs PvE source slice, without touching official RC."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zlib

ROOT=Path(__file__).resolve().parent/"features/seven_jobs"
ORIGINAL={
 "server/Game.server.luau":"aaa03616ee4aadee32bfeb90a0016ca036919a52a2725e908a0c360adf087739",
 "client/HUD.client.luau":"3f2654199c2531bea34371a4ea33beecf65d1e306ecd91e86f5164ab3ddca06d",
}
AFTER={
 "server/Game.server.luau":"6308e02c0d6930af2ec4ba0f86bf280be435ca8b7c46f1c8c8ee81b4164269eb",
 "client/HUD.client.luau":"6d510976b25789a99686fc58ed6ae4c85dbd2b04f9080e2d4e88e09057506f30",
 "server/SevenJobsRules.luau":"cd4de7c232f2303e719000fddc2b52f54b38f461416cb4d33316c8fac24fb3d8",
}
PATCHES=[
 ("Game.patch.zlib.b64","Game.luau","server/Game.server.luau",
  "8b067b88eed38050e2f71119c83d06c9f3fef67578478024e3b0b1c27b8952ef"),
 ("HUD.patch.zlib.b64","TrapRaidersHUD.luau","client/HUD.client.luau",
  "ba56402a37e318c9102a15c7217659bf4a0297fb27fd4c71a5ae81c0cc6c05e2"),
]
def hash_bytes(raw):
 return hashlib.sha256(raw).hexdigest()
def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sources(dist):
 return {p.relative_to(dist/"src").as_posix():p.read_bytes()
         for p in (dist/"src").rglob("*.luau")}
def apply(dist, enabled_override=None):
 assert dist.is_dir() and (dist/"default.project.json").is_file(),"NO_RC_DIST"
 before=sources(dist)
 flags=json.loads((Path(__file__).resolve().parent/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
 enabled=flags["SEVEN_JOBS_PVE_V1"]["enabled"] if enabled_override is None else enabled_override
 assert type(enabled) is bool,"SEVEN_JOBS_ENABLE_INVALID"
 if not enabled:
  print("SEVEN_JOBS_OFF_PRESERVES_EXISTING_SOURCE")
  return {"enabled":False,"source_count":len(before)}
 want=57+int(flags["WCS_F01_C01"]["enabled"])
 assert len(before)==want,("NEED_EXACT_LATEST_RC_WCS_BASE",len(before),want)
 lockpath=dist/"SOURCE_LOCK.json"
 lock=json.loads(lockpath.read_text("utf8"))
 assert lock["total_scripts"]==want and lock["blobs"]=={p:blob(v) for p,v in sorted(before.items())},"SEVEN_JOBS_PREVIOUS_SOURCE_LOCK_DRIFT"
 assert lock["rc_scout_species_overlay"]["id"]=="SCOUT_SPECIES_V1"
 if flags["WCS_F01_C01"]["enabled"]:
  assert lock["rc_wcs_f01_c01_overlay"]["id"]=="WCS_F01_C01"
  assert "server/WCS_CrystalCanyon.server.luau" in before
 for key,sha in ORIGINAL.items():
  assert hash_bytes(before[key])==sha,("RC_AUTHOR_DRIFT",key)
 config=json.loads((dist/"default.project.json").read_text("utf8"))
 assert config["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 assert config["tree"]["StarterPlayer"]["StarterPlayerScripts"]["TrapRaidersHUD"]["$path"]=="src/client/HUD.client.luau"
 for encoded,filename,key,expected_sha in PATCHES:
  data=(ROOT/"patches"/encoded).read_text("ascii").strip()
  unpacked=zlib.decompress(base64.b64decode(data,validate=True))
  assert hash_bytes(unpacked)==expected_sha,("CORRUPT_AUTHOR_PATCH",encoded)
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/filename
   f.write_bytes(before[key])
   patch=Path(td)/"change.patch"
   patch.write_bytes(unpacked)
   subprocess.run(["patch","--fuzz=0","--batch","--forward","-p1","-i",
                   str(patch)],cwd=td,check=True,capture_output=True,text=True)
   after=f.read_bytes()
  if key=="server/Game.server.luau":
   # Required safety fix after author patch: turret never occludes LOS raycasts.
   old=b"wall.Anchored=true;wall.CanCollide=false;wall.CanTouch=false"
   assert after.count(old)==1,"TURRET_GUARD_DRIFT"
   after=after.replace(old,old+b";wall.CanQuery=false")
  if key=="client/HUD.client.luau":
   # CRITICAL: author HUD diff has a literal LF inside a double-quoted Luau string.
   # Roblox XML is parseable while native Luau compilation would fail. Fix fail-closed.
   old_title='jobTitle.Text="7職業: まずは中立モンスター戦'+chr(10)+'1チーム同職1人 / ロビーで選ぶ"'
   new_title=old_title.replace(chr(10),chr(92)+'n')
   raw=after.decode("utf8")
   assert raw.count(old_title)==1,("LUAU_MULTILINE_QUOTED_STRING_DRIFT",raw.count(old_title))
   after=raw.replace(old_title,new_title).encode("utf8")
  assert hash_bytes(after)==AFTER[key],("WRONG_PATCH_RESULT",key)
  (dist/"src"/key).write_bytes(after)
 new_src=(ROOT/"src/SevenJobsRules.luau").read_bytes()
 assert blob(new_src)=="a7253d36cb67df47d4ba65d35af212ed1eb7b5b2"
 assert hash_bytes(new_src)==AFTER["server/SevenJobsRules.luau"]
 dest=dist/"src/server/SevenJobsRules.luau"
 assert not dest.exists(),"DUPLICATE_JOBS"
 dest.write_bytes(new_src)
 after=sources(dist)
 assert len(after)==want+1 and len(set(after)-set(before))==1
 assert {p for p in before if after[p]!=before[p]}==set(ORIGINAL)
 assert all(after[p]==raw for p,raw in before.items() if p not in ORIGINAL)
 if flags["WCS_F01_C01"]["enabled"]:
  assert after["server/WCS_CrystalCanyon.server.luau"]==before["server/WCS_CrystalCanyon.server.luau"],"WCS_SCRIPT_CHANGED"
 game=after["server/Game.server.luau"].decode()
 client=after["client/HUD.client.luau"].decode()
 assert game.count("remote.OnServerEvent:Connect(")==1
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert 'ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")' in game
 assert 'horde:hit(source,dir,damage,serverNow(),player.Character)' in game
 assert 'UserInputService.InputBegan:Connect' in client
 assert 'action("JOB_PICK",entry[1])' in client
 assert 'action("JOB_SKILL",nil)' in client
 assert 'SaveStatus' in game and 'settleSixSkill' in game
 assert after["server/PersistentHatchStore.luau"]==before["server/PersistentHatchStore.luau"]
 assert after["server/SavedPveMasteryPolicy.luau"]==before["server/SavedPveMasteryPolicy.luau"]
 assert after["server/SavedBeastEvolutionPolicy.luau"]==before["server/SavedBeastEvolutionPolicy.luau"]
 assert after["server/ScoutSpeciesPolicy.luau"]==before["server/ScoutSpeciesPolicy.luau"]
 assert "ScoutSpeciesPolicy" in game
 assert "P0D_RC_ENABLE_SEVEN_JOBS_PVE" in game
 assert "SavedBeastPolicy." in game or "SavedBeastEvolutionPolicy" in game
 assert "SavedPvePolicy.mergeWithEarned(" in game
 # The additive change preserves original Game/Remote/Store instances.
 # A private WCS+7jobs project explicitly sets the boot opt-in on ServerStorage.
 server_storage=config["tree"].setdefault("ServerStorage",{"$className":"ServerStorage"})
 attributes=server_storage.setdefault("$attributes",{})
 assert "P0D_RC_ENABLE_SEVEN_JOBS_PVE" not in attributes
 attributes["P0D_RC_ENABLE_SEVEN_JOBS_PVE"]=True
 (dist/"default.project.json").write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 lock["total_scripts"]=len(after)
 lock["blobs"]={p:blob(v) for p,v in sorted(after.items())}
 lock["rc_seven_jobs_pve_overlay"]={"id":"SEVEN_JOBS_PVE_V1",
   "original_game_hud_sha256":ORIGINAL,"after_sha256":AFTER,
   "author_policy_blob":"a7253d36cb67df47d4ba65d35af212ed1eb7b5b2",
   "source_count":len(after),"previous_script_count":want,
   "unchanged_original_count":want-2,"new_module_only":True,
   "one_Game_Remote_Store":True,"real_engine":"NOT_TESTED",
   "rollback":"disable SEVEN_JOBS_PVE_V1 switch"}
 lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 featurelock=dist/"RC_FEATURE_LOCK.json"
 if featurelock.exists():
  f=json.loads(featurelock.read_text("utf8"))
  assert f["total_sources"]==want
  f["total_sources"]=len(after)
  f["source_gitblobs"]={p:blob(v) for p,v in sorted(after.items())}
  f["feature_flags"]["SEVEN_JOBS_PVE_V1"]=True
  featurelock.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 receipt={
  "status":"P0D_SEVEN_JOBS_PVE_RC59_COMBINED_CANDIDATE_NOT_OFFICIAL",
  "base_official_sha":"34d6d384d04ba1d4a394331a3e5c74f798e57a22",
  "base_source_count":want,"added_count":1,"changed_existing_count":2,
  "existing_unchanged_count":want-2,"total_source_count":len(after),
  "single_Game":True,"single_Remote":True,"Store_byte_identical":True,
  "no_new_DataStore":True,"no_Publication":True,
  "actual_studio_engine":"NOT_TESTED","native_luau":"NOT_TESTED",
  "official_rc_adopted":False,"pvp_job_balance":"NOT_IMPLEMENTED","saved_weapon_mastery_source_preserved":True,"saved_beast_evolution_source_preserved":True,"scout_species_source_preserved":True,
  "source_blobs":{p:blob(s) for p,s in sorted(after.items())}
 }
 (dist/"P0D_SEVEN_JOBS_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
 print("P0D_WCS_SEVEN_JOBS_RC59_SOURCE_LOCK_PASS",len(after))
 return receipt
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--dist",type=Path,required=True)
 args=p.parse_args()
 apply(args.dist)
