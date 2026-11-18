#!/usr/bin/env python3
"""Fail-closed local adversarial tests for REAL65 single-owner Combat overlay."""
from compose_real65 import merge_combat,PVP
src="-- SINGLE OWNER\n"+PVP+"\n-- END\n"
basic=src.replace("-- END","-- EGGRUMBLE_BASIC_ATTACK EGGRUMBLE_DODGE_STEP EGGRUMBLE_BasicMobilityPolicy\n-- END")
replacement="if claimPvPCounter( then EGGRUMBLE_VisibleCounterTell end"
counter=src.replace(PVP,replacement)
out=merge_combat(src.encode(),basic.encode(),counter.encode()).decode()
assert "EGGRUMBLE_BASIC_ATTACK" in out
assert "EGGRUMBLE_DODGE_STEP" in out
assert "EGGRUMBLE_VisibleCounterTell" in out
assert PVP not in out
def reject(original,quick,counter_src,reason):
    try:
        merge_combat(original.encode(),quick.encode(),counter_src.encode())
    except ValueError as e:
        assert "RED_" in str(e),(reason,e)
    else:
        raise AssertionError("RED_MUTANT_NOT_REJECTED_"+reason)
reject(src,basic.replace("EGGRUMBLE_DODGE_STEP","MISSING"),counter,"DODGE_LOST")
reject(src+"\n"+PVP,basic,counter,"MULTIPLE_PVP_SITES")
reject(src,basic,src,"COUNTER_NOT_ADDED")
reject(src,basic.replace(PVP,"FAKE_PVP"),counter,"OLD_PVP_ANCHOR_GONE")
print("GQ8_REAL65_SOURCE_COLLISION_MUTATIONS_PASS")
