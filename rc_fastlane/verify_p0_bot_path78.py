#!/usr/bin/env python3
"""Independent full 78-source real Rojo archive witness, sole Bot input."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_p0_motion78 import read,gitblob
from apply_p0_bot_path78 import BOT,GAME,FIX
def audit(dist:Path,place:Path,receipt:Path):
 src=read(dist)
 assert len(src)==78
 sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
 fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
 pins={key:gitblob(blob) for key,blob in sorted(src.items())}
 assert sl["total_scripts"]==fl["total_sources"]==78
 assert sl["blobs"]==fl["source_gitblobs"]==pins
 assert fl["p0_bot_path78"]["id"]==FIX
 assert fl["p0_bot_path78"]["other77_sources_byte_exact"] is True
 script=src[BOT].decode("utf8")
 for phrase in ("MAX_PENDING_PATH_TASKS=10","releasePathLease(bot)",
                "now<bot.detourUntil and gap>2.5","pendingPathTasks+=1"):
  assert phrase in script,phrase
 assert "local function scheduleLobbyRecovery(" in src[GAME].decode("utf8")
 expected=collections.Counter(body.decode("utf8") for body in src.values())
 actual=collections.Counter(); names=collections.Counter()
 for item in ET.parse(place).iter("Item"):
  if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
  code=item.find("./Properties/string[@name='Source']")
  if code is not None:actual[code.text or ""]+=1
  name=item.find("./Properties/string[@name='Name']")
  if name is not None:names[(item.get("class"),name.text)]+=1
 assert actual==expected and sum(actual.values())==78
 assert names[("Script","Game")]==1 and names[("ModuleScript","SoloTeamBots")]==1
 assert names[("LocalScript","P0DNeutralMotion")]==1
 r={
 "candidate":"P0D_PRIVATE78_ROUND_EPOCH_SAFE_LOBBY_AND_UNSTUCK_SOLO_AI",
 "sources":78,"Rojo_source_exact":True,"game_only_one":True,
 "path_original_author_pr":402,"bot_only_patch":True,
 "source_author_pairs":17,
 "new_feature_ids":0,"official_adoption":0,
 "native_luau_Bot_start_move_actor_lease":"TESTED_WITH_ENGINE_MOCKS",
 "Studio_pathfinding":"NOT_TESTED","Android_FPS":"NOT_TESTED",
 "owner_art":"ART_NO_GO","owner_fun":"FUN_NO_GO",
 "place_bytes":place.stat().st_size,
 "sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
 }
 receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n","utf8")
 print("P0_PRIVATE78_SOLO_PATH_NATIVE_AND_ROJO_78_78_SOURCE_EXACT_PASS",
       r["place_bytes"],r["sha256"])
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--dist",type=Path,required=True)
 p.add_argument("--place",type=Path,required=True)
 p.add_argument("--receipt",type=Path,required=True)
 a=p.parse_args()
 audit(a.dist,a.place,a.receipt)
