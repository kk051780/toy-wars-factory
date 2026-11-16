#!/usr/bin/env python3
"""Source-selective dead-caster gate for original EGGRUMBLE V3 Combat.

This is an isolated candidate, not an official RC writer.  OFF reproduces
original source byte-for-byte. ON changes only one unique function anchor.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

AUTHOR_REL = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau"
AUTHOR_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"
ANCHOR = (
    " local char,root,h=characterOf(p)\n"
    " if not char or not root or not h then return end\n"
    " local now=os.clock()"
)
PATCH = (
    " local char,root,h=characterOf(p)\n"
    " if not char or not root or not h then return end\n"
    " -- GQ_DEAD_CASTER_FENCE: reject death/downed before skill cost, heal or damage.\n"
    " if h.Health<=0 or char:GetAttribute(\"EGGRUMBLE_Downed\")==true then return end\n"
    " local now=os.clock()"
)

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()

def compose(source: bytes, enabled: bool = True) -> bytes:
    if git_blob_sha(source) != AUTHOR_BLOB:
        raise ValueError("RED_SOURCE_LOCK: Combat original blob drifted; reconcile author first")
    if not enabled:
        return source
    text = source.decode("utf-8")
    if text.count(ANCHOR) != 1:
        raise ValueError("RED_ANCHOR: expected unique hero execute entry")
    target = text.index("local function execute(session:any,p:Player,role:string,slot:string)")
    anchor = text.index(ANCHOR)
    end = text.index("function HeroCombat.roleOrder()")
    if not (target < anchor < end):
        raise ValueError("RED_SCOPE: caster entry is not inside execute")
    if not (anchor < text.index("perPlayer[key]=now",target) <
            text.index("elseif role==\"MAGE\"",target)):
        raise ValueError("RED_ORDER: skill cost/branch topology changed")
    return text.replace(ANCHOR, PATCH, 1).encode("utf-8")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[3] / AUTHOR_REL)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--off", action="store_true", help="exact original source rollback")
    args = parser.parse_args()
    content = compose(args.source.read_bytes(), enabled=not args.off)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    print("GQ_DEAD_CASTER_FENCE", "OFF_EXACT" if args.off else "ON_PATCHED",
          "bytes", len(content), "sha256", hashlib.sha256(content).hexdigest())

if __name__ == "__main__":
    main()
