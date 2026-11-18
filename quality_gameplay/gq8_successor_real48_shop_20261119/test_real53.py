#!/usr/bin/env python3
"""Actual source and adversarial mutation QA for original Real49 plus original 4 shop scripts."""
import argparse,copy,json,tempfile
from pathlib import Path
from compose_real53 import compose,check_parent
from compose_real48 import BLOBS,CANDIDATE,flatten,klass,blob

p=argparse.ArgumentParser()
for name in ("original49","receipt49","original44","server","client","catalog","view","real53"):
 p.add_argument("--"+name,required=True,type=Path)
a=p.parse_args()
inputs={k:getattr(a,k) for k in BLOBS}
doc,old,base,unchanged=check_parent(a.original49,a.receipt49,a.original44)
_,after=flatten(a.real53)
assert len(old)==49 and len(after)==53 and len(base)==44 and len(unchanged)==37
assert set(after)==set(old)|set(CANDIDATE)
for route,source in old.items():
 assert after[route].read_bytes()==source.read_bytes(),route
 assert klass(after[route])==klass(source),route
for route,(name,ext) in CANDIDATE.items():
 assert after[route].read_bytes()==inputs[name].read_bytes()
 assert blob(after[route].read_bytes())==BLOBS[name]
assert klass(after[("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopView")])=="ModuleScript"
assert klass(after[("StarterPlayer","StarterPlayerScripts","GQ805_ShopKioskClient")])=="LocalScript"
assert sum(r[-1]=="EGGRUMBLE_SwarmCombat" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_SevenRoleCombat" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_LobbyCastleModesPreview" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_MusouFeverPolicy" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_InvulRuntime" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_CurseConversionPolicy" for r in after)==1
assert sum(r[-1]=="EGGRUMBLE_LobbyShopCatalog" for r in after)==1
with tempfile.TemporaryDirectory() as d:
 t=Path(d)
 # An altered upstream author source must be rejected before selection.
 tamper=t/"kiosk.client.luau";tamper.write_bytes(inputs["client"].read_bytes()+b"\n-- HACK\n")
 try:
  compose(a.original49,a.receipt49,a.original44,
          {**inputs,"client":tamper},t/"badshop")
  raise AssertionError("RED_CHANGED_SHOP_SOURCE_ACCEPTED")
 except ValueError as e:
  assert "RED_ORIGINAL_808_816_GIT_BLOB_CHANGED_client" in str(e),str(e)
 receipt=json.loads(a.receipt49.read_text(encoding="utf8"))
 receipt["sources"][0]["sha256"]="0"*64
 tamper_receipt=t/"badreceipt.json"
 tamper_receipt.write_text(json.dumps(receipt))
 try:
  check_parent(a.original49,tamper_receipt,a.original44)
  raise AssertionError("RED_CHANGED_REAL49_SOURCE_LEDGER_ACCEPTED")
 except ValueError as e:
  assert "RED_AUTHOR_REAL49_BYTES_DRIFT" in str(e),str(e)
 # Existing real53 output may not be overwritten, even if validated.
 try:
  compose(a.original49,a.receipt49,a.original44,inputs,a.real53.parent)
  raise AssertionError("RED_OVERWRITE_ACCEPTED")
 except ValueError as e:
  assert "RED_REFUSE_OVERWRITE" in str(e),str(e)
 # Missing immutable author route must be caught, not patched ad hoc.
 receipt=json.loads(a.receipt49.read_text(encoding="utf8"))
 receipt["sources"].pop()
 missing=t/"missing.json";missing.write_text(json.dumps(receipt))
 try:
  check_parent(a.original49,missing,a.original44)
  raise AssertionError("RED_MISSING_SOURCE_LEDGER_ACCEPTED")
 except ValueError as e:
  assert "RED_AUTHOR_SOURCE_LEDGER_MISSING_ROUTE" in str(e),str(e)
print("GQ8_REAL53_TRUE49_PRESERVED_4SHOP_AND_FOUR_HOSTILE_MUTANTS_PASS")
