#!/usr/bin/env python3
"""Cumulative P0 private77: fixed-source core70 + seven original visual scripts.
This does not alter main, official RC66, or the source70 candidate.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ART=HERE/"features"/"p0_playable_art77"
BASE_RC="43543378f976374e2cac2d68b3136ac355d3191b"
SPECS=[
 ("CASTLE_DETAIL","CastleDetailArt.server.luau","server/CastleDetailArt.server.luau","da2bf0544682f72ee02280374a27ce2f4fadb5c2","FB015_FORTRESS_DETAIL_ART_V2"),
 ("WORLD","FantasyWorldArt.server.luau","server/FantasyWorldArt.server.luau","dc741ec6d0506cfebf82631cf3583dd4037fbea9","FB015_ART_WORLD_LIGHT_FOLIAGE_V1"),
 ("SEA","H1CoastalSeascape.server.luau","server/H1CoastalSeascape.server.luau","44b39c3d8b0df9290c86a139318ca1bf68356814","FB011_H1_COASTAL_SEASCAPE_V1"),
 ("SEA_CHANNEL","H1SeaGroundRepair.server.luau","server/H1SeaGroundRepair.server.luau","652bbcb31d91810a8d5d65d25e769c18ddd1f20f","FB015_REAL_SEA_GROUND_V2"),
 ("MINION","MinionArtSilhouette.server.luau","server/ArtMinionSilhouette.server.luau","ed5cd56789abc4a7bc8ee3a44b8982aae4f3ff62","ART_MINION_THREE_SILHOUETTES_V1"),
 ("BEAST","FB015CharacterArt.client.luau","client/FB015CharacterArt.client.luau","2ff10db1a4171be9abdc276a43dd21b2401da2d8","FB015_GOROGAN_BEAST_VISUAL_V2"),
 ("COMBAT","ConfirmedSlashFX.client.luau","client/ConfirmedSlashFX.client.luau","4b1dce5635b709d349ab3f00bba7a7cf9d9883bd","FB008_CONFIRMED_HIT_SLASH_VFX_V1")]
CLIENTS={"FB015GoroganVisual":"src/client/FB015CharacterArt.client.luau",
         "P0DConfirmedCombatFX":"src/client/ConfirmedSlashFX.client.luau"}
def blob(x):
 return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def read(root):
 assert root.is_dir() and not root.is_symlink(),"MISSING_OR_SYMLINK"
 for p in root.rglob("*"):
  assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("SYMLINK_ESCAPE",p)
 src=root/"src"
 assert src.is_dir()
 return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}
def additions():
 out={}
 for k,name,dest,pin,feature in SPECS:
  data=(ART/name).read_bytes()
  assert blob(data)==pin,("PIN_DRIFT",k)
  assert b"RunService:IsStudio()" in data,("ART_NON_STUDIO",k)
  for banned in (b"MarketplaceService",b"DataStoreService",b"UpdateAsync(",b"FireServer(",b"OnServerEvent:Connect(",b"TakeDamage("):
   assert banned not in data,("SECOND_AUTHORITY",k)
  assert dest not in out
  out[dest]=data
 assert len(out)==7
 assert b"MUSOU_MINION_" not in out["client/FB015CharacterArt.client.luau"]
 assert b"Gorogan_ServerRig" not in out["server/ArtMinionSilhouette.server.luau"]
 assert b"ForestPlacedAfterCastleExpanded" in out["server/FantasyWorldArt.server.luau"]
 return out
def apply(base,out,enabled):
 if not enabled:
  print("P0_PRIVATE77_OFF_ZERO_WRITE")
  return False
 base=base.absolute();out=out.absolute()
 assert out.parent.is_dir() and not out.exists() and not out.is_relative_to(base),"BAD_OUTPUT"
 before=read(base)
 required={"server/Game.server.luau","server/SoloTeamBots.luau","server/LobbyDojoIsland.luau","server/CastleBattlefield.server.luau","client/BattleHUDGovernor.client.luau"}
 assert len(before)==70 and required.issubset(before),"NOT_CORE70"
 game=before["server/Game.server.luau"]
 assert game.count(b"remote.OnServerEvent:Connect(")==1
 assert b"everybodyReady()" in game and b"SoloTeamBots.tick" in game
 assert b"math.abs(position.X) > 182" in game
 assert b"grass.Size = Vector3.new(370, 4, 294)" in before["server/CastleBattlefield.server.luau"]
 pins={p:blob(v) for p,v in sorted(before.items())}
 sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
 fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
 project=json.loads((base/"default.project.json").read_text("utf8"))
 assert sl["total_scripts"]==fl["total_sources"]==70
 assert sl["blobs"]==fl["source_gitblobs"]==pins
 parent=fl["owner361_p0_composite_private70"]
 assert parent["base_rc"]==BASE_RC and not parent["formal_rc_adoption"]
 assert len(parent["feature_ids"])==5
 add=additions()
 assert not set(add).intersection(before)
 starter=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
 assert starter["BattleHUDGovernor"]["$path"]=="src/client/BattleHUDGovernor.client.luau"
 for k,v in CLIENTS.items():
  assert k not in starter
  starter[k]={"$path":v}
 features=[row[4] for row in SPECS]
 assert set(features).isdisjoint(fl["feature_flags"])
 for f in features: fl["feature_flags"][f]=True
 after=dict(before);after.update(add)
 assert len(after)==77 and all(after[k]==v for k,v in before.items())
 newpins={p:blob(v) for p,v in sorted(after.items())}
 receipt={"status":"PRIVATE77_NOT_OFFICIAL","official_base":BASE_RC,
 "parent70_feature_ids":parent["feature_ids"],"added_art_feature_ids":features,
 "source_count":77,"parent70_all_byte_identical":True,
 "sole_game_authority":True,"engine_studio":"NOT_TESTED",
 "android":"NOT_TESTED","owner_art":"ART_NO_GO","owner_fun":"FUN_NO_GO",
 "water_castle_collision":"NOT_TESTED","rollback":"omit this additive step",
 "source_blobs":{row[2]:row[3] for row in SPECS}}
 sl["total_scripts"]=77;sl["blobs"]=newpins;sl["p0_private77"]=receipt
 fl["total_sources"]=77;fl["source_gitblobs"]=newpins;fl["p0_private77"]=receipt
 scratch=Path(tempfile.mkdtemp(prefix=".p0_art77_",dir=str(out.parent)))
 staged=scratch/"dist"
 try:
  shutil.copytree(base,staged,symlinks=False)
  for dest,data in add.items():
   f=staged/"src"/dest;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
  (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
  (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
  (staged/"default.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n","utf8")
  assert read(staged)==after
  assert json.loads((staged/"SOURCE_LOCK.json").read_text())["blobs"]==newpins
  assert json.loads((staged/"RC_FEATURE_LOCK.json").read_text())["source_gitblobs"]==newpins
  assert not out.exists()
  os.replace(staged,out)
 finally: shutil.rmtree(scratch,ignore_errors=True)
 assert read(base)==before,"PARENT70_CHANGED"
 print("P0_CORE70_PLUS_7ART_PRIVATE77_SOURCE_LOCK_PASS")
 return True
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--base",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--enabled",required=True,choices=["true","false"])
 a=p.parse_args()
 apply(a.base,a.out,a.enabled=="true")
