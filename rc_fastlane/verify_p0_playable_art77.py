#!/usr/bin/env python3
"""Private77 real Rojo XML source-exact audit. Studio engine is NOT tested."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_p0_playable_art77 import read,blob
def verify(dist,place,receipt):
 scripts=read(dist);assert len(scripts)==77
 expected=collections.Counter(b.decode("utf8") for b in scripts.values())
 actual=collections.Counter();names=collections.Counter()
 for item in ET.parse(place).iter("Item"):
  if item.get("class") not in ("Script","ModuleScript","LocalScript"):continue
  source=item.find("./Properties/string[@name='Source']")
  if source is not None:actual[source.text or ""]+=1
  name=item.find("./Properties/string[@name='Name']")
  if name is not None:names[(item.get("class"),name.text)]+=1
 assert actual==expected and sum(actual.values())==77,"SOURCE_NOT_EXACT"
 for typ,name in [("Script","Game"),("Script","Owner361CastleBattlefield"),("Script","CastleDetailArt"),("Script","H1SeaGroundRepair"),("Script","ArtMinionSilhouette"),("LocalScript","BattleHUDGovernor"),("LocalScript","FB015GoroganVisual"),("LocalScript","P0DConfirmedCombatFX"),("ModuleScript","SoloTeamBots"),("ModuleScript","LobbyDojoIsland")]:
  assert names[(typ,name)]==1,(typ,name,names[(typ,name)])
 pins={p:blob(v) for p,v in sorted(scripts.items())}
 sl=json.loads((dist/"SOURCE_LOCK.json").read_text())
 fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text())
 assert sl["total_scripts"]==fl["total_sources"]==77
 assert sl["blobs"]==fl["source_gitblobs"]==pins
 data={"source_count":77,"native_and_rojo_source_exact":True,
 "private_place_bytes":place.stat().st_size,
 "private_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
 "official_rc_adoption":0,"owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
 "studio_solo":"NOT_TESTED","studio_2client":"NOT_TESTED","android":"NOT_TESTED"}
 receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
 print("P0_PRIVATE77_REAL_ROJO_77_77_SOURCE_EXACT_PASS",data["private_place_bytes"],data["private_place_sha256"])
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--dist",type=Path,required=True)
 p.add_argument("--place",type=Path,required=True)
 p.add_argument("--receipt",type=Path,required=True)
 a=p.parse_args();verify(a.dist,a.place,a.receipt)
