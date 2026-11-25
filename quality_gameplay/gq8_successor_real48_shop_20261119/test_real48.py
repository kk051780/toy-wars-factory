#!/usr/bin/env python3
"""Negative mutation checks on actual 48-source crosslane selected artifact."""
import argparse,copy,json,tempfile
from pathlib import Path
from compose_real48 import BLOBS,CANDIDATE,flatten,blob,compose,klass
p=argparse.ArgumentParser()
for name in ("original44","receipt44","server","client","catalog","view","selected48"):p.add_argument("--"+name,required=True,type=Path)
a=p.parse_args()
_,before=flatten(a.original44);_,after=flatten(a.selected48)
assert len(before)==44 and len(after)==48
assert set(after)==set(before)|set(CANDIDATE)
assert all(before[r].read_bytes()==after[r].read_bytes() and klass(before[r])==klass(after[r]) for r in before)
for route,(name,ext) in CANDIDATE.items():
 assert after[route].read_bytes()==getattr(a,name).read_bytes()
 assert blob(after[route].read_bytes())==BLOBS[name]
assert klass(after[("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopView")])=="ModuleScript"
assert klass(after[("StarterPlayer","StarterPlayerScripts","GQ805_ShopKioskClient")])=="LocalScript"
assert sum(r[-1]=="EGGRUMBLE_SwarmCombat" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_LobbyCastleModesPreview" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_CurseConversionPolicy" for r in after)==1
with tempfile.TemporaryDirectory() as d:
 temp=Path(d)
 mutated=temp/"client.luau"
 mutated.write_bytes(a.client.read_bytes()+b"\n-- altered\n")
 try:
  compose(a.original44,a.receipt44,{"server":a.server,"client":mutated,"catalog":a.catalog,"view":a.view},temp/"rejected48")
  raise AssertionError("RED_SHOP_SOURCE_MUTATION_NOT_REJECTED")
 except ValueError as e:
  assert "RED_ORIGINAL_808_OR_816_SOURCE_DRIFT_client" in str(e),str(e)
 try:
  compose(a.original44,a.receipt44,{"server":a.server,"client":a.client,"catalog":a.catalog,"view":a.view},a.selected48.parent)
  raise AssertionError("RED_OVERWRITE_NOT_REJECTED")
 except ValueError as e:
  assert "RED_REFUSE_OVERWRITE" in str(e)
print("GQ8_REAL48_ACTUAL_SOURCE_LOCK_CLASS_ROUTES_MUTATION_PASS")
