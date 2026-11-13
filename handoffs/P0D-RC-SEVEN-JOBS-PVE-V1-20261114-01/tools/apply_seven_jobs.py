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

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL={
 "server/Game.server.luau":"aaa03616ee4aadee32bfeb90a0016ca036919a52a2725e908a0c360adf087739",
 "client/TrapRaidersHUD.client.luau":"3f2654199c2531bea34371a4ea33beecf65d1e306ecd91e86f5164ab3ddca06d",
}
AFTER={
 "server/Game.server.luau":"6308e02c0d6930af2ec4ba0f86bf280be435ca8b7c46f1c8c8ee81b4164269eb",
 "client/TrapRaidersHUD.client.luau":"6d510976b25789a99686fc58ed6ae4c85dbd2b04f9080e2d4e88e09057506f30",
 "server/SevenJobsRules.luau":"cd4de7c232f2303e719000fddc2b52f54b38f461416cb4d33316c8fac24fb3d8",
}
PATCHES=[
 ("Game.patch.zlib.b64","Game.luau","server/Game.server.luau",
  "dace60e6a60a9de0960e2b2f91a39033264e8a7e7ed9b83f5c5ddb014176e39c"),
 ("HUD.patch.zlib.b64","TrapRaidersHUD.luau","client/TrapRaidersHUD.client.luau",
  "ba56402a37e318c9102a15c7217659bf4a0297fb27fd4c71a5ae81c0cc6c05e2"),
]
def hash_bytes(raw):
 return hashlib.sha256(raw).hexdigest()
def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sources(dist):
 return {p.relative_to(dist/"src").as_posix():p.read_bytes()
         for p in (dist/"src").rglob("*.luau")}
def apply(dist):
 assert dist.is_dir() and (dist/"default.project.json").is_file(),"NO_RC_DIST"
 before=sources(dist)
 assert len(before)==57,("NEED_EXACT_RC57_WITH_SCOUT_SPECIES",len(before))
 for key,sha in ORIGINAL.items():
  assert hash_bytes(before[key])==sha,("RC_AUTHOR_DRIFT",key)
 config=json.loads((dist/"default.project.json").read_text("utf8"))
 assert config["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 assert config["tree"]["StarterPlayer"]["StarterPlayerScripts"]["TrapRaidersHUD"]["$path"]=="src/client/TrapRaidersHUD.client.luau"
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
  if key=="client/TrapRaidersHUD.client.luau":
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
 assert len(after)==58 and len(set(after)-set(before))==1
 assert {p for p in before if after[p]!=before[p]}==set(ORIGINAL)
 assert all(after[p]==raw for p,raw in before.items() if p not in ORIGINAL)
 game=after["server/Game.server.luau"].decode()
 client=after["client/TrapRaidersHUD.client.luau"].decode()
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
 assert "SavedBeastPolicy." in game or "SavedBeastEvolutionPolicy" in game
 assert "SavedPvePolicy.mergeWithEarned(" in game
 receipt={
  "status":"P0D_SEVEN_JOBS_PVE_OPTIONAL_UNSELECTED",
  "base_official_sha":"34d6d384d04ba1d4a394331a3e5c74f798e57a22",
  "base_source_count":57,"added_count":1,"changed_existing_count":2,
  "existing_unchanged_count":55,"total_source_count":58,
  "single_Game":True,"single_Remote":True,"Store_byte_identical":True,
  "no_new_DataStore":True,"no_Publication":True,
  "actual_studio_engine":"NOT_TESTED","native_luau":"NOT_TESTED",
  "official_rc_adopted":False,"pvp_job_balance":"NOT_IMPLEMENTED","saved_weapon_mastery_source_preserved":True,"saved_beast_evolution_source_preserved":True,"scout_species_source_preserved":True,
  "source_blobs":{p:blob(s) for p,s in sorted(after.items())}
 }
 (dist/"P0D_SEVEN_JOBS_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
 print("P0D_RICH54_TO_55_SEVEN_JOBS_SOURCE_EXACT_SUCCESS")
 return receipt
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--dist",type=Path,required=True)
 args=p.parse_args()
 apply(args.dist)
