#!/usr/bin/env python3
"""Private full-game exact-source builder: same DEV Hatch key, optional additive dojo.
Reconstruct immutable prior 44 scripts, apply SHA256-pinned unified delta to ONLY 3 scripts.
No publishing, no official RC, no separate DataStore keys, no extra authoritative Game.
"""
import argparse,base64,hashlib,json,shutil,subprocess,sys,zlib
from pathlib import Path
HERE=Path(__file__).resolve()
OWN=HERE.parents[1]; REPO=HERE.parents[3]
PREV=REPO/"handoffs/P0D-H1-AUTO-DOJO-20261113-01"
OLD=PREV/"dist/EGG_RAID_RUMBLE_B42_V7_SKY_SOLO_AUTO_DOJO_PRIVATE"
NEW=OWN/"dist/EGG_RAID_RUMBLE_H1_DOJO_DURABLE_DEV_PRIVATE"
PATCH_SHA="a1395194b0b5234003156cd53d23a4909292f29a719125e71da88da3f2829bd4"
BASE_SHA={
 "server/Game.server.luau":"1c416e7d67306776d6f9eb47ca5e8256c5ecf456e96f98f0dfb8bacaba5697b9",
 "server/PersistentHatchStore.luau":"2485b6e5c0f14383c03d2ee7f3a6a38eebbd05793630497cf54a34254c57fa8a",
 "client/HUD.client.luau":"3f2654199c2531bea34371a4ea33beecf65d1e306ecd91e86f5164ab3ddca06d"}
NEW_SHA={
 "server/Game.server.luau":"8f258076a9bb9f00cb6f10cf0e9ff2dbd83940689edbdc56ed51c3027d2acfdb",
 "server/PersistentHatchStore.luau":"8698b06c4344209b4b63758c142aa33c14f382b1260b76a9c738893e67190b24",
 "client/HUD.client.luau":"50fb7868b936f5df59f562da790901d31222db1a77ae73cdfe686c2966780cab"}
def sha(data):return hashlib.sha256(data).hexdigest()
def src(root):
 return {p.relative_to(root/"src").as_posix():p.read_bytes() for p in sorted((root/"src").rglob("*.luau"))}
def main():
 assert not OLD.exists() and not NEW.exists(),"FAIL_CLOSED_NEVER_OVERWRITE_EXISTING_BUILD"
 patchstr=(OWN/"inputs/dojo_profile_v1_patch.b64").read_text("ascii").strip()
 raw=zlib.decompress(base64.b64decode(patchstr,validate=True))
 assert sha(raw)==PATCH_SHA,"EXACT_PROFILE_PATCH_SOURCE_LOCK_FAILED"
 subprocess.run([sys.executable,"-B",str(PREV/"tools/assemble.py"),"--assemble"],
                 cwd=REPO,check=True)
 before=src(OLD)
 assert len(before)==44,len(before)
 for path,want in BASE_SHA.items():
  assert sha(before[path])==want,("IMMUTABLE_BASE_SCRIPT_DRIFT",path)
 shutil.copytree(OLD,NEW)
 tmp=OWN/"_source_patch_do_not_commit.diff"
 try:
  tmp.write_bytes(raw)
  subprocess.run(["patch","--fuzz=0","--batch","-p0","-d",str(NEW),"-i",str(tmp)],check=True)
 finally:
  if tmp.exists():tmp.unlink()
 # Luau tuple return annotations must be parenthesized; exact source one-line fix.
 storepath=NEW/"src/server/PersistentHatchStore.luau"
 storetext=storepath.read_text("utf8")
 original_type="token:any,snapshot:any):any?,string"
 assert storetext.count(original_type)==1,"SOURCE_TYPE_DRIFT"
 storepath.write_text(storetext.replace(original_type,"token:any,snapshot:any): (any?, string)"),encoding="utf8")
 now=src(NEW)
 assert len(now)==44 and sorted(now)==sorted(before)
 changes=sorted(k for k in before if before[k]!=now[k])
 assert changes==sorted(BASE_SHA),changes
 assert all(before[k]==now[k] for k in before if k not in changes)
 for path,want in NEW_SHA.items():
  assert sha(now[path])==want,("PATCHED_SOURCE_HASH_MISMATCH",path)
 game=now["server/Game.server.luau"].decode("utf8")
 store=now["server/PersistentHatchStore.luau"].decode("utf8")
 hud=now["client/HUD.client.luau"].decode("utf8")
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count("remote.OnServerEvent:Connect(")==1
 assert game.count("local function tickRound()")==1
 assert game.count("local function resetRound()")==1
 assert game.count("local function flushDojo(")==1
 assert game.count("StudioSolo.canStart(")==2
 assert game.count("Dojo.pveDamageMultiplier(")==2
 assert store.count("store:UpdateAsync(")==5
 assert "dojo=cloneDojo(raw.dojo)" in store
 assert "or not safeDojoRecord(raw.dojo)" in store
 assert "normalized=function(raw:any)" in store
 assert "local normalized:any" in store
 assert "PersistenceSave" not in game
 assert game.count('GetDataStore("EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1")')==1
 assert "dojoSaveStatus" in hud
 assert len([k for k in now if k.endswith(".server.luau")])==2
 assert len([k for k in now if k.endswith(".client.luau")])==5
 project=NEW/"default.project.json"
 spec=json.loads(project.read_text("utf8"))
 assert spec["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 spec["name"]="P0D_B42_V7_SKY_SOLO_AUTO_DOJO_DURABLE_DEV_UNPUBLISHED"
 project.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n","utf8")
 receipt={
  "packet":"P0D-H1-DOJO-SAVE-20261113-01",
  "base_44_SHA":"ce4e1ebcf6d16313c9d144c56129bdfae548e1bf",
  "patch_sha256":PATCH_SHA,"scripts":44,"unchanged":41,"patched":changes,
  "schema_version_unchanged":1,
  "dev_Store_namespace":"EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1",
  "separate_data_store":False,
  "optional_dojo_profile_field":True,
  "optimistic_revision":True,"retry_same_server_token":True,
  "Studio_only_and_real_UserId_required":True,
  "fake_user_id_local_only":True,
  "STUDIO_1_CLIENT":"NOT_TESTED","STUDIO_2_CLIENT":"NOT_TESTED",
  "ANDROID":"NOT_TESTED","FUN":"NOT_TESTED",
  "official_rc_adopted":False,"published":False,"paid":False,
  "sha256_script_sources":{k:sha(v) for k,v in now.items()}
 }
 (NEW/"SOURCE_LOCK.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
 print("P0D_H1_DURABLE_DOJO_44_EXACT_SCRIPT_PATCH_SOURCE_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--assemble",required=True,action="store_true")
 p.parse_args();main()
