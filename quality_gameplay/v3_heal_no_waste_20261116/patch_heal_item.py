#!/usr/bin/env python3
"""Source-select one HEAL zero-effect guard onto original #489 item (no duplicate ITEM)."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ORIGINAL_ITEM_GIT_BLOB = "107046cb0bf81fed9e3cba1699ada31571e44a22"
HELPER_BEGIN = "-- GQ_HEAL_NO_WASTE_BEGIN\n"
HELPER_END = "-- GQ_HEAL_NO_WASTE_END\n"
HELPER = (
    HELPER_BEGIN
    + "local function healUseful(kind:string,health:number,maxHealth:number):boolean\n"
    + ' if kind~="HEAL" then return true end\n'
    + " return health==health and maxHealth==maxHealth\n"
    + "  and health>0 and maxHealth>0 and health<maxHealth\n"
    + "end\n"
    + HELPER_END
)
CALL = (
    "   -- Full-HP HEAL has no effect: preserve the 35-second shared pickup and cooldown.\n"
    "   if not healUseful(kind,hum.Health,hum.MaxHealth) then return end\n"
)
HELPER_ANCHOR = "function Items.start(session:any,positions:{Vector3}):()\n"
CALL_ANCHOR = "   if (root.Position-part.Position).Magnitude>10 then return end\n"

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def patch(original: str) -> str:
    assert original.count(HELPER_ANCHOR)==1, "source author changed Items.start"
    assert original.count(CALL_ANCHOR)==1, "item claim point moved; stop and rebase"
    assert "healUseful(" not in original, "feature already exists; avoid duplicate"
    assert original.count("   consumed[id]=true;lastUse[key]=now") == 1
    assert 'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end' in original
    assert 'interactionGuard.allow(player,part,"拾う",part.Name)' in original
    assert "if not matchActive() or player.Character~=buffCharacter then return end" in original
    changed=original.replace(HELPER_ANCHOR,HELPER+HELPER_ANCHOR,1)
    changed=changed.replace(CALL_ANCHOR,CALL_ANCHOR+CALL,1)
    assert changed.replace(HELPER,"",1).replace(CALL,"",1)==original, "not an additive patch"
    return changed

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    raw=args.source.read_bytes()
    assert git_blob_sha(raw)==ORIGINAL_ITEM_GIT_BLOB, "original #489 item drift, re-pin author SHA"
    content=raw.decode("utf-8")
    output=patch(content)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    assert args.out.name=="EGGRUMBLE_FieldItemPickups.luau"
    assert args.out.resolve()!=args.source.resolve()
    args.out.write_text(output,encoding="utf-8")
    print("GQ_HEAL_ONLY_ADD_HUNK_PASS",git_blob_sha(raw),hashlib.sha256(output.encode()).hexdigest())

if __name__=="__main__":
    main()
