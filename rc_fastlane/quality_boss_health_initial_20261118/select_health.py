#!/usr/bin/env python3
"""GQ8: initialize the existing Stone Giant's replicated health before its first hit.

Source-only selection of ORIGINAL #482 + immutable #518 wall-occlusion patch.
No new Boss, Host, combat authority, RemoteEvent, GUI, or extra game script.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from pathlib import Path

ORIGINAL_BLOB = "2670618cba320c51936c750a10e43c194cada0f0"
PARENT_AUTHOR_SHA = "f31081d5cb2bea86d01c76c53bb60cd2f9a8355d"
ANCHOR = b" local health=900\n local active=true\n"
REPLACEMENT = (
    b" local health=900\n"
    b" -- A boss has a real, replicated health value even before the first hit.\n"
    b' model:SetAttribute("EGGRUMBLE_BossHealth",health)\n'
    b" local active=true\n"
)

def blob_sha(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\x00" + content).hexdigest()

def load_author(path: Path):
    spec = importlib.util.spec_from_file_location("gq518_original_boss_patch", path)
    if spec is None or spec.loader is None:
        raise ValueError("missing pinned original GQ518 patch")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.ORIGINAL_BLOB != ORIGINAL_BLOB:
        raise ValueError("GQ518 parent source lock changed")
    return module

def base_518(original: bytes, author_path: Path) -> bytes:
    if blob_sha(original) != ORIGINAL_BLOB:
        raise ValueError("RED: original #482 boss source blob drift")
    return load_author(author_path).patch_bytes(original)

def apply(parent_518: bytes) -> bytes:
    if parent_518.count(ANCHOR) != 1:
        raise ValueError("RED: unique boss-health anchor changed")
    if parent_518.count(b'model:SetAttribute("EGGRUMBLE_BossHealth",health)') != 1:
        raise ValueError("RED: duplicate boss spawn initialization")
    patched = parent_518.replace(ANCHOR, REPLACEMENT, 1)
    if undo(patched) != parent_518:
        raise ValueError("RED: non-reversible patch")
    return patched

def undo(on: bytes) -> bytes:
    if on.count(REPLACEMENT) != 1:
        raise ValueError("RED: cannot reverse boss health patch")
    return on.replace(REPLACEMENT, ANCHOR, 1)

def verify(base: bytes, on: bytes) -> None:
    if undo(on) != base or apply(base) != on:
        raise ValueError("RED: source inverse mismatch")
    for marker in (b"function Boss.spawn(", b"local function damageFrom(", b"h:TakeDamage(28)",
                   b"shockwaveClear(c,root)", b"MIN_HIT_INTERVAL=.22"):
        if base.count(marker) != on.count(marker):
            raise ValueError("RED: gameplay authority drift: " + marker.decode())
    for forbidden in (b"RemoteEvent", b"DataStore", b"MarketplaceService", b"PromptProductPurchase"):
        if forbidden in REPLACEMENT:
            raise ValueError("RED: new authority in health initialization")

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",required=True,type=Path)
    parser.add_argument("--gq518-author",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--off",action="store_true")
    args=parser.parse_args()
    base=base_518(args.original.read_bytes(),args.gq518_author)
    result=base if args.off else apply(base)
    if not args.off: verify(base,result)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(result)
    print("GQ8_BOSS_HEALTH", "OFF_GQ518_EXACT" if args.off else "ON", "sha256="+hashlib.sha256(result).hexdigest())

if __name__=="__main__":
    main()
