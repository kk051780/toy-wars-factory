#!/usr/bin/env python3
"""Source-selective 26->27 private Place instrumentation.

Consumes the OTHER authors' original 26-source output without overwriting
character, combat, score, art, world or inventory sources. Adds one read-only
observer ModuleScript + one guarded call in generated host only. No RC publish.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

REQUIRE_ANCHOR='local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))\n'
REQUIRE_INJECT='local IntegrityObserver=require(script.Parent:WaitForChild("EGGRUMBLE_IntegrityObserver"))\n'
START_ANCHOR=' SwarmCombat.start(session)\n'
START_INJECT='''  -- Optional GQ observer: report first fault, changed fault set and recovery.
  -- Never alter the session. Deduplicate recurrent warnings for low-end devices.
  task.spawn(function()
   local lastSignature:string?=nil
   local lastSnapshot:any?=nil
   while sessions[mode]==session and session.rules.phase=="ACTIVE" do
    task.wait(5)
    if sessions[mode]==session and session.rules.phase=="ACTIVE" then
     local ok,result,nextSnapshot=pcall(IntegrityObserver.inspectAndTrack,session,Rules,lastSnapshot)
     if not ok then
      if lastSignature~="OBSERVER_SCRIPT_ERROR" then
       warn("[EGGRUMBLE GQ OBSERVER] SCRIPT_ERROR")
      end
      lastSignature="OBSERVER_SCRIPT_ERROR"
     else
      lastSnapshot=nextSnapshot
      local current,emit,recovered=IntegrityObserver.warningDelta(lastSignature,result)
      lastSignature=current
      if emit then
       if recovered then
        print("[EGGRUMBLE GQ OBSERVER]",mode,"RECOVERED")
       else
        warn("[EGGRUMBLE GQ OBSERVER]",mode,
         "RED",table.concat(result.red,","),
         "YELLOW",table.concat(result.yellow,","))
       end
      end
     end
    end
   end
  end)
'''

def patch(source: str) -> str:
    if source.count(REQUIRE_ANCHOR)!=1 or source.count(START_ANCHOR)!=1:
        raise ValueError("author/GQ source drift; manually reconcile before any build")
    if "EGGRUMBLE_IntegrityObserver" in source:
        raise ValueError("observer already integrated; do not duplicate")
    result=source.replace(REQUIRE_ANCHOR,REQUIRE_ANCHOR+REQUIRE_INJECT,1)
    result=result.replace(START_ANCHOR,START_ANCHOR+START_INJECT,1)
    if result.replace(REQUIRE_INJECT,"",1).replace(START_INJECT,"",1)!=source:
        raise ValueError("unexpected script rewrite")
    if "scene.closeRound(true)" not in result or "session.rules.phase" not in result:
        raise ValueError("lost vital game lifecycle")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    p.add_argument("--observer",required=True,type=Path)
    a=p.parse_args()
    project=a.project.resolve(strict=True)
    observer=a.observer.resolve(strict=True)
    config=json.loads(project.read_text(encoding="utf-8"))
    server=config["tree"]["ServerScriptService"]
    assert server["$className"]=="ServerScriptService"
    assert len(server)-1==23,(len(server)-1)
    assert "EGGRUMBLE_IntegrityObserver" not in server
    host_rel=server["EGGRUMBLE_LobbyCastleModesPreview"]["$path"]
    host=(project.parent/host_rel).resolve(strict=True)
    assert host.name=="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    original=host.read_text(encoding="utf-8")
    rec=json.loads(a.receipt.read_text(encoding="utf-8"))
    assert rec["status"]=="SOURCE_ONLY_NOT_OFFICIAL_RC"
    assert rec["script_count"]==26
    name="EGGRUMBLE_LobbyCastleModesPreview"
    original_sha=hashlib.sha256(host.read_bytes()).hexdigest()
    assert rec["source_sha256"][name]==original_sha,"host source-lock mismatch"
    patched=patch(original)
    host.write_text(patched,encoding="utf-8")
    server["EGGRUMBLE_IntegrityObserver"]={
      "$path":os.path.relpath(observer,project.parent).replace(os.sep,"/"),
    }
    rec["source_sha256"][name]=hashlib.sha256(host.read_bytes()).hexdigest()
    rec["source_sha256"]["EGGRUMBLE_IntegrityObserver"]=hashlib.sha256(observer.read_bytes()).hexdigest()
    rec["script_count"]=27
    rec["server_count"]=24
    rec["source_only_shadow_observer"]={
      "host_original_sha256":original_sha,
      "host_shadow_sha256":rec["source_sha256"][name],
      "observer_sha256":rec["source_sha256"]["EGGRUMBLE_IntegrityObserver"],
      "no_mutations":True,
      "studio_run":"NOT_TESTED",
      "android_run":"NOT_TESTED",
      "official_rc":"NOT_ADOPTED",
      "rollback":"remove observer mapping and two injected call sites",
    }
    a.receipt.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    project.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_SHADOW_27_SOURCE_ONLY_PASS")
if __name__=="__main__":
    main()
