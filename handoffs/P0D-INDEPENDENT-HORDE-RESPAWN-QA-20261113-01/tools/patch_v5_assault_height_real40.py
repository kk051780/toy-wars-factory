#!/usr/bin/env python3
"""Independent source-only trial: exact original #288 40+v5 compiled Game -> one assault Y fix.
Run after frozen original #288 builder in its OWN isolated checkout. NEVER change upstream.
"""
from pathlib import Path
from hashlib import sha1,sha256
import json,argparse
ORIGINAL_BLOB="c118a3ff17397ea69360cd7481a2db51d2c32756"
HORDE_BLOB="8c147c801e7fa1ff362922d66c9a6fd432fc8b6e"
BEFORE="                local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,\n"
AFTER=("                local sweepOrigin=Vector3.new(anchor.X,currentRoot.Position.Y,anchor.Z)\n"
       "                local hits=horde:hit(sweepOrigin,currentRoot.CFrame.LookVector,\n")
def blob(data:bytes)->str:return sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def convert(dist:Path)->dict:
 src=dist/"src"
 paths=sorted(src.rglob("*.luau"))
 assert len(paths)==40,("EXPECTED_FROZEN_40",len(paths))
 before={str(p.relative_to(src)):p.read_bytes() for p in paths}
 key="server/Game.server.luau"
 assert key in before and "server/MusouHorde.luau" in before
 assert blob(before[key])==ORIGINAL_BLOB,("NO_UPSTREAM_DRIFT",blob(before[key]))
 assert blob(before["server/MusouHorde.luau"])==HORDE_BLOB
 game=before[key].decode("utf8")
 assert game.count(BEFORE)==1 and AFTER not in game
 for gate in ("local SCOUT_DURATION=5","local scoutExpiresAt=serverNow()+SCOUT_DURATION",
              "evolutionGuards[player]={untilAt=scoutExpiresAt,",
              "evolvedStrikes<2 and serverNow()>=nextEvolvedStrike",
              "nextEvolvedStrike=serverNow()+2.5",
              "musouEliteWarningSeconds","if mobHits>0 then return end"):
  assert gate in game,("BASELINE_SAFETY_MISSING",gate)
 fixed=game.replace(BEFORE,AFTER,1)
 assert fixed.replace(AFTER,BEFORE,1)==game
 for gate in ("remote.OnServerEvent:Connect(","PersistentHatch.evolve(","Power.beginAwaken("):
  assert fixed.count(gate)==game.count(gate),("NEW_SERVER_AUTHORITY",gate)
 (src/key).write_bytes(fixed.encode("utf8"))
 after={str(p.relative_to(src)):p.read_bytes() for p in paths}
 assert set(after)==set(before)
 assert [k for k in before if before[k]!=after[k]]==[key]
 assert len(after)==40
 assert after["server/MusouHorde.luau"]==before["server/MusouHorde.luau"]
 result={"change_count":1,"unchanged_script_count":39,"full_source_count":40,
 "before_game_blob":ORIGINAL_BLOB,"after_game_blob":blob(after[key]),
 "unchanged_v5_horde_blob":HORDE_BLOB,
 "reconstructed_orig_sha256":{k:sha256(v).hexdigest() for k,v in before.items()},
 "patched_source_sha256":{k:sha256(v).hexdigest() for k,v in after.items()},
 "source_trial_only":True,"official_RC_adopted":False,
 "real_Studio_playtested":False,"Android_playtested":False,
 "source_remedy":"Root-attached Y for authoritative assault sweep; floating scout stays at visual anchor."}
 (dist/"ASSAULT_HEIGHT_QA_SOURCE_LOCK.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
 print("P0D_ASSAULT_HEIGHT_40V5_ONE_SOURCE_EXACT_PATCH_PASS")
 return result
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--dist",required=True,type=Path)
 a=ap.parse_args();print(json.dumps(convert(a.dist),indent=2)[:1800])
