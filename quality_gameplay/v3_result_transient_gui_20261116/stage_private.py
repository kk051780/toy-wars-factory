#!/usr/bin/env python3
"""Private original #487 V3 22 OFF / 23 ON real Rojo source staging; no formal RC changes."""
import argparse, hashlib, json
from pathlib import Path
from compose_result import patch, AUTHOR_PATH, AUTHOR_BLOB, git_blob
BASE=Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")
PROJECT=BASE/"EGGRUMBLE_V3_STUDIO.project.json"
PROJECT_BLOB="4f85b8313ad93744ac13d0480c3460643f96212e"
SCORE_BLOB="4de4b8068203ce93bba9c0810d54ab22367e5f35"
ROOT=Path(__file__).resolve().parent

def stage(out:Path,on:bool):
 if git_blob(PROJECT.read_bytes())!=PROJECT_BLOB: raise ValueError("SOURCE_PROJECT_DRIFT")
 if git_blob((BASE/"EGGRUMBLE_ScoreBalance.luau").read_bytes())!=SCORE_BLOB:
  raise ValueError("SOURCE_SCORE_DRIFT")
 project=json.loads(PROJECT.read_text())
 out.mkdir(parents=True,exist_ok=False)
 src=out/"src"
 src.mkdir()
 mapped={}
 def visit(node):
  for name,value in node.items():
   if not isinstance(value,dict):continue
   if "$path" in value:
    rel=value["$path"];file=BASE/rel
    raw=file.read_bytes()
    if file==AUTHOR_PATH:
     raw=patch(raw,on)
    (src/rel).write_bytes(raw)
    value["$path"]="src/"+rel
    mapped[name]={"file":rel,"sha256":hashlib.sha256(raw).hexdigest(),
                  "author_blob":git_blob(file.read_bytes())}
   else:visit(value)
 visit(project["tree"])
 if len(mapped)!=22:raise AssertionError(("expected original 22",len(mapped)))
 if on:
  rel="EGGRUMBLE_ResultRetry.luau"
  content=(ROOT/rel).read_bytes()
  (src/rel).write_bytes(content)
  project["tree"]["ServerScriptService"]["EGGRUMBLE_ResultRetry"]={"$path":"src/"+rel}
  mapped["EGGRUMBLE_ResultRetry"]={"file":rel,"sha256":hashlib.sha256(content).hexdigest(),"author_blob":None}
 if len(mapped)!=(23 if on else 22):raise AssertionError("incorrect source count")
 (out/"private.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n")
 receipt={"mode":"ON" if on else "OFF","author_head":"438a406ccfda5563053d783d7561797ccd364361",
          "result_blob":AUTHOR_BLOB,"project_blob":PROJECT_BLOB,"scripts":mapped,"count":len(mapped),
          "official_rc":False,"studio_tested":False}
 (out/"receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
 print(f"GQ_RESULT_PRIVATE_{receipt['mode']}_SOURCE_STAGE_PASS {len(mapped)}")
 return receipt

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--on",action="store_true")
 a=p.parse_args();stage(a.out,a.on)
