#!/usr/bin/env python3
"""Source-selective 27 -> 28 private GQ extension (NO game source rewriting).

Reuses the #488 ORIGINAL 27-script compositor, appends one *Script* event probe
from #493. Both observers have independent responsibilities; never invent a
second match loop, touch author Lua files or update the authenticated RC.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

PROBE_NAME = "EGGRUMBLE_StudioLiveObserver"
EXISTING = "EGGRUMBLE_IntegrityObserver"

def compose(project: Path, receipt: Path, observer: Path) -> dict:
    project=project.resolve(strict=True)
    receipt=receipt.resolve(strict=True)
    observer=observer.resolve(strict=True)
    assert observer.name=="EGGRUMBLE_StudioLiveObserver.server.luau"
    config=json.loads(project.read_text(encoding="utf-8"))
    data=json.loads(receipt.read_text(encoding="utf-8"))
    server=config["tree"]["ServerScriptService"]
    assert server["$className"]=="ServerScriptService"
    assert data["script_count"]==27 and data["server_count"]==24, "27 baseline drift"
    assert len(server)-1==24, "server script count drift"
    assert EXISTING in server, "must reuse original #488 integrity observer"
    assert PROBE_NAME not in server, "duplicate temporal sensor prohibited"
    assert "EGGRUMBLE_LobbyCastleModesPreview" in server
    original_host=server["EGGRUMBLE_LobbyCastleModesPreview"]["$path"]
    host_path=(project.parent/original_host).resolve(strict=True)
    before=host_path.read_bytes()
    host_sha=hashlib.sha256(before).hexdigest()
    assert data["source_sha256"]["EGGRUMBLE_LobbyCastleModesPreview"]==host_sha
    assert b"EGGRUMBLE_IntegrityObserver" in before
    # Add exactly one server Script; do not create extra require/local host changes.
    server[PROBE_NAME]={
        "$path":os.path.relpath(observer,project.parent).replace(os.sep,"/")
    }
    new_hash=hashlib.sha256(observer.read_bytes()).hexdigest()
    data["source_sha256"][PROBE_NAME]=new_hash
    data["script_count"]=28
    data["server_count"]=25
    data["temporal_event_sensor"]={
        "name":PROBE_NAME,
        "original_source_sha256":new_hash,
        "unchanged_27_host_sha256":host_sha,
        "source_exact_27_baseline":True,
        "studio_runtime":"NOT_TESTED",
        "android_runtime":"NOT_TESTED",
        "official_rc":"NOT_ADOPTED",
        "rollback":"remove one observer Script mapping; no original 27 source bytes changed"
    }
    assert host_path.read_bytes()==before, "original 27-game host modified"
    project.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_27_PLUS_ONE_EVENT_SENSOR_SOURCE_ONLY_PASS")
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    p.add_argument("--observer",required=True,type=Path)
    a=p.parse_args()
    compose(a.project,a.receipt,a.observer)

if __name__=="__main__":
    main()
