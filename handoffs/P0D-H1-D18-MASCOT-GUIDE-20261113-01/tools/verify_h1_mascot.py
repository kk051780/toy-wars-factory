#!/usr/bin/env python3
"""Strict H1 cloned-game source lock + client-only D18 guide contract. No Studio PASS claim."""
from pathlib import Path
import json,hashlib,subprocess,re
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
ORIGIN="c73f305fb412927aee05b399a4f54a2a16d0579f"
OLD="handoffs/P0D-H1-WORLD-CREATURES-20261113-01/src/"
NEW="handoffs/P0D-H1-D18-MASCOT-GUIDE-20261113-01/src/"
CATALOG_SHA="41079553d2141940fc3fee57b23969e292770614"
NEW_NAMES={"src/client/D18Batch8Catalog.luau","src/client/D18MascotGuideRules.luau","src/client/D18MascotGuide.client.luau"}
def check(ok,msg):
 if not ok:raise ValueError(msg)
def git(*args):
 return subprocess.check_output(["git",*args],cwd=REPO)
def verify_original():
 old=git("ls-tree","-r","--name-only",ORIGIN,OLD).decode().splitlines()
 old=[p for p in old if p.endswith(".luau")]
 check(len(old)==24,"expected original 24 H1 real sources")
 for path in old:
  rel=path[len(OLD):]
  expected=git("show",ORIGIN+":"+path)
  check((ROOT/"src"/rel).read_bytes()==expected,"existing H1 source modified "+rel)
 return old
def verify_manifest():
 lock=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 check(lock["schema"]=="P0D_H1_D18_MASCOT_REAL_GAME_KEYLESS_SOURCE_LOCK_V1","schema")
 check(lock["origin_h1_game_sha"]==ORIGIN,"origin")
 names=set()
 for row in lock["source_files"]:
  path=row["path"]
  check(path.startswith("src/") and ".." not in Path(path).parts and path not in names,"bad manifest path")
  raw=(ROOT/path).read_bytes()
  sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\\0"+raw).hexdigest()
  check(sha==row["git_blob_sha1"] and len(raw)==row["bytes"],"manifest source changed "+path)
  names.add(path)
 check(len(names)==27 and NEW_NAMES<=names,"missing expected 27 exact source")
 check(lock["original_24_source_count"]==24,"wrong origin count")
 check(len([x for x in names if x not in NEW_NAMES])==24,"unexpected source")
 check(git("hash-object",str(ROOT/"src/client/D18Batch8Catalog.luau")).decode().strip()==CATALOG_SHA,"D18 catalog original SHA")
 return names
def verify_contract(client=None,rules=None,project=None):
 client=client if client is not None else (ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")
 rules=rules if rules is not None else (ROOT/"src/client/D18MascotGuideRules.luau").read_text(encoding="utf8")
 project=project if project is not None else json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
 for token in ('RunService:IsStudio()','ProximityPrompt','OnClientEvent','D18Batch8Catalog','SCORE_PAD','EGG','MaxActivationDistance=14','CanCollide=false','CanTouch=false','CanQuery=false','clearHints()','dropMascot()'):
  check(token in client,"missing safety/UI contract "+token)
 for token in ('UPDATE','PRODUCTION','MarketplaceService','DataStore','FireServer(','Instance.new("RemoteEvent")','Player:SetAttribute','ApplyDamage','DamageHumanoid'):
  check(token not in client,"forbidden authority/mutation "+token)
 for token in ('s.kind~="SNAPSHOT"','update<=previousUpdate','s.serial < previousSerial','s.team~="RED" and s.team~="BLUE"','s.carrying~=""','if carrying then s.team else enemy','if carrying then "SCORE_PAD" else "EGG"'):
  check(token in rules,"missing read-only rule gate "+token)
 for token in ("FireServer(","DataStore","Marketplace","RemoteEvent","Humanoid:TakeDamage"):
  check(token not in rules,"forbidden rule authority")
 sp=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
 check(set(sp)>={"TrapRaidersHUD","TrapRaidersCoach","D18MascotGuideRules","D18Batch8Catalog","D18MascotGuide"},"old/new client wiring")
 check(sp["D18MascotGuide"]["$path"]=="src/client/D18MascotGuide.client.luau","local script mapping")
 check(sp["D18Batch8Catalog"]["$path"]=="src/client/D18Batch8Catalog.luau","catalog mapping")
 check(project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server","original S1 server authority mapping")
 return True
if __name__=="__main__":
 verify_original();verify_manifest();verify_contract()
 print("P0D_H1_D18_MASCOT_24_ORIGINAL_EXACT_3_NEW_LOCK_27_SOURCE_PASS")
