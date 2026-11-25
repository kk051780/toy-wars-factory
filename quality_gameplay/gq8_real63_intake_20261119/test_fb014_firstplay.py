#!/usr/bin/env python3
"""FB-014 source-level fail-closed check, no Roblox Studio pass claimed."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compose_real65 import add_fb014_firstplay

original=b"-- GQ646_LOBBY_SAFE_SPAWN_END\nlocal function block"
patched=add_fb014_firstplay(original)
assert patched.count(b"GQ8_FB014_FIRSTPLAY_GUIDE_BEGIN")==1
assert patched.count(b"GQ8_FB014_FIRSTPLAY_SIGN")==1
assert patched.count(b"CanCollide=false")==1
assert patched.count(b"MaxDistance=44")==1
assert original==b"-- GQ646_LOBBY_SAFE_SPAWN_END\nlocal function block"
assert patched.endswith(b"local function block")
for bad in (original.replace(b"SAFE_SPAWN_END",b"SAFE_SPAWN_OLD"),
            original+original, patched):
    try:
        add_fb014_firstplay(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("RED_FB014_FAIL_OPEN_ON_BAD_SOURCE")
print("GQ8_FB014_FIRSTPLAY_ONE_SIGN_3_NEGATIVES_SOURCE_PASS")
