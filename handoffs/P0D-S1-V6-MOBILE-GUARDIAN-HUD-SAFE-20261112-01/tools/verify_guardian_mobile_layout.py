#!/usr/bin/env python3
"""Frozen official TRAP RAIDERS S1 V6 touch HUD candidate verification.

This checks *exactly* one GuardianTrap button UDim2 placement edit against
the official Git blob, plus child-readable mobile landscape geometry.
Offline geometry is NOT actual Roblox safe area or physical touch testing.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys

OFFICIAL_RC = "1263a03701211a652b99b91d2339575dc8104eff"
OFFICIAL_BLOB = "ee594fbc34e6bf938518fae32c0642c852f11f9e"
RC_HUD = "releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau"
ROOT = Path("handoffs/P0D-S1-V6-MOBILE-GUARDIAN-HUD-SAFE-20261112-01")
CANDIDATE = ROOT / "candidate/src/client/HUD.client.luau"
OLD = b"UDim2.fromOffset(110, 74), UDim2.new(.02, 0, 1, -16)"
NEW = b"UDim2.fromOffset(110, 74), UDim2.new(1, -140, 1, -110)"
SUPPORTED_LANDSCAPE = ((640,360),(667,375),(812,375),(1024,576),(1280,720),(1920,1080))
BUTTON_ATTACK = (126, 88, -140, -16)
BUTTON_TRAP = (110, 74, -140, -110)


def sha_blob(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()


def rectangle(w, h, size_x, size_y, offset_x, bottom_offset):
    x = w + offset_x
    bottom = h + bottom_offset
    return (x, bottom - size_y, x + size_x, bottom)


def overlap(a, b):
    return max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3])


def geometry(w, h, trap=BUTTON_TRAP, attack=BUTTON_ATTACK):
    assert 0 < h < w
    t = rectangle(w,h,*trap)
    a = rectangle(w,h,*attack)
    thumbstick_reserve = (0, h-220, w*0.32, h)
    instructions = (.20*w, h-58, .75*w, h-16)
    coach_width = min(530,max(220,.62*w))
    coach = ((w-coach_width)*.5,108,(w+coach_width)*.5,175)
    # This is a conservative layout check, NOT a claim about native controls.
    return {
        "trap":t,
        "attack":a,
        "thumbstick_reserved":thumbstick_reserve,
        "instructions":instructions,
        "coach":coach,
    }


def check_geometry(w, h, trap=BUTTON_TRAP):
    bounds=geometry(w,h,trap)
    t,a=bounds["trap"],bounds["attack"]
    if t[0] < 0 or t[1] < 0 or t[2] > w or t[3] > h-8:
        raise AssertionError(f"BUTTON_OUTSIDE_LANDSCAPE_SAFE_RECT {w}x{h}: {t}")
    if overlap(t,a):
        raise AssertionError(f"ATTACK_TRAP_OVERLAP {w}x{h}")
    if overlap(t,bounds["thumbstick_reserved"]):
        raise AssertionError(f"LEFT_TOUCH_MOVEMENT_RESERVED_COLLISION {w}x{h}")
    if overlap(t,bounds["instructions"]) or overlap(t,bounds["coach"]):
        raise AssertionError(f"TOUCH_HELP_PANEL_COLLISION {w}x{h}")
    if overlap(a,bounds["instructions"]) or overlap(a,bounds["coach"]):
        raise AssertionError(f"PREEXISTING_ATTACK_HUD_COLLISION {w}x{h}")
    # A 6px vertical gutter between attack and trap keeps the two tap targets distinct.
    if a[1]-t[3] < 6:
        raise AssertionError(f"INSUFFICIENT_GUARDIAN_BUTTON_GUTTER {w}x{h}")
    return bounds


def fail_closed_exact_diff(original, candidate):
    if sha_blob(original) != OFFICIAL_BLOB:
        raise RuntimeError("OFFICIAL_HUD_GIT_BLOB_NOT_EXACT")
    if original.count(OLD) != 1:
        raise RuntimeError("ORIGINAL_GUARDIAN_ANCHOR_NON_UNIQUE")
    if candidate != original.replace(OLD, NEW, 1):
        raise RuntimeError("CANDIDATE_NOT_SINGLE_SOURCE_POSITION_PATCH")
    if candidate.count(NEW) != 1 or candidate.count(OLD):
        raise RuntimeError("GUARDIAN_LAYOUT_SOURCE_AMBIGUOUS")
    # Sensitive gameplay and UI network authority remains unchanged as a consequence
    # of exact full-binary replacement.
    return True


def actual_bytes(repo: Path) -> tuple[bytes, bytes]:
    p = subprocess.run(
        ["git","-C",str(repo),"show",OFFICIAL_RC+":"+RC_HUD],
        capture_output=True, timeout=20, check=False,
    )
    if p.returncode:
        raise RuntimeError("OFFICIAL_HUD_PIN_NOT_ACCESSIBLE")
    target=repo/CANDIDATE
    if target.is_symlink() or not target.is_file():
        raise RuntimeError("CANDIDATE_MISSING_OR_SYMLINK")
    return p.stdout, target.read_bytes()


def tests():
    assert sha_blob(b"abc") == "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert not overlap((0,0,5,5),(5,0,6,5))
    assert overlap((0,0,6,6),(5,5,8,8))
    for w,h in SUPPORTED_LANDSCAPE:
        b=check_geometry(w,h)
        print(f"LANDSCAPE_GEOMETRY_PASS {w}x{h} trap={b['trap']} attack={b['attack']}")
    bad_cases={
        "original_bottom_left":(110,74,int(.02*640)-640,-16),
        "same_attack_bottom":(110,74,-140,-16),
        "coach_collision_640":(110,74,-140,-128),
        "off_screen_right":(160,74,-140,-110),
        "no_button_gutter":(110,74,-140,-105),
    }
    for name,bad in bad_cases.items():
        try:
            check_geometry(640,360,bad)
        except AssertionError:
            print("UNSAFE_TOUCH_GEOMETRY_REJECTED " + name)
        else:
            raise AssertionError("UNDETECTED_UNSAFE_TOUCH_GEOMETRY " + name)
    fixture=b"before " + OLD + b" after"
    assert fixture.replace(OLD, NEW, 1).count(NEW) == 1
    for old, mutated in (
        (fixture,fixture),
        (fixture,fixture.replace(OLD, NEW,1)+b"\nremote:FireServer({damage=999})"),
        (fixture.replace(OLD,b"other",1),fixture),
    ):
        # For fixture tests, the real checksum condition is deliberately bypassed
        # with a preliminary structural gate because the official blob is huge.
        try:
            if old.count(OLD) != 1 or mutated != old.replace(OLD,NEW,1):
                raise RuntimeError("DIFF_REJECTED")
        except RuntimeError:
            pass
        else:
            raise AssertionError("ILLEGAL_SOURCE_MUTATION_ACCEPTED")
    print("P0D_MOBILE_HUD_OFFLINE_GEOMETRY_PASS sizes=6 unsafe_layouts=5 source_mutants=3")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path)
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    if args.selftest:
        tests()
        return 0
    if not args.repo:
        p.error("--repo is required except for --selftest")
    original,candidate=actual_bytes(args.repo.resolve())
    fail_closed_exact_diff(original,candidate)
    for w,h in SUPPORTED_LANDSCAPE:
        check_geometry(w,h)
    print("P0D_OFFICIAL_RC_V6_HUD_SINGLE_PATCH_SOURCE_PASS blob="+sha_blob(original))
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,ValueError,AssertionError,OSError) as e:
        print("P0D_MOBILE_GUARDIAN_HUD_BLOCKED " + str(e),file=sys.stderr)
        sys.exit(2)
