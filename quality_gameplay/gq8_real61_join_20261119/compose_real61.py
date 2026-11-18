#!/usr/bin/env python3
"""Compose exact official Real55 + upstream HUD4 + trade2. Never touches game authority."""
import argparse,copy,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"quality_gameplay/gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten,klass
PINS={
"handoffs/EGGRUMBLE-HUD-INTEL-20261119/EGGRUMBLE_HudIntelRuntime.client.luau":"99e5a58d3d2622643f6a4e74817fa0cfbd8c59d2",
"handoffs/EGGRUMBLE-HUD-INTEL-20261119/EGGRUMBLE_MapIntelBridge.server.luau":"4899bd52518815630a49954a1adc36151a5c1eea",
"handoffs/EGGRUMBLE-HUD-INTEL-20261119/HudPresentationPolicy.luau":"9358eff6c71bdc2b860b00d98f20d13db6ce3571",
"handoffs/EGGRUMBLE-HUD-INTEL-20261119/MapVisibilityPolicy.luau":"9fbb08a86c555a9bfbb7c63b064fdb87ff8ab8bc",
"quality_gameplay/gq8_trade_ux_journal_20261119/GQ8_TradeJournalContract.luau":"c3d6ca4ebc518592bddefbb5942f4d60ab5179a9",
"quality_gameplay/gq8_trade_ux_journal_20261119/GQ8_TradeReview.client.luau":"a96d9bde201c6bdbb8fe185c81650f99368a9544"}
T=ROOT/"quality_gameplay/gq8_trade_ux_journal_20261119"
ROUTES={
("ServerScriptService","GQ8_TradeJournalContract"):("GQ8_TradeJournalContract.luau","ModuleScript"),
("StarterPlayer","StarterPlayerScripts","GQ8_TradeReview"):("GQ8_TradeReview.client.luau","LocalScript")}
def sha(b):return hashlib.sha256(b).hexdigest()
def run(base,receipt,off,out):
 if out.exists():raise ValueError("RED_OVERWRITE")
 for path,expected in PINS.items():
  got=subprocess.check_output(["git","hash-object",path],text=True).strip()
  assert got==expected,("RED_IMMUTABLE_AUTHOR_BLOB",path,got)
 p,old=flatten(base);_,off_sources=flatten(off)
 r=json.loads(receipt.read_text())
 assert len(old)==59 and len(off_sources)==55
 assert r.get("official_rc_head")=="a6020867fac80fa3b2ca47478625873fc6f3678e"
 assert r.get("baseline55_exact_sources_unchanged") is True
 for k,f in off_sources.items():
  assert k in old and f.read_bytes()==old[k].read_bytes(),("RED_ORIGINAL55_CHANGED",k)
 assert not set(old)&set(ROUTES)
 needed={("ServerScriptService","EGGRUMBLE_SevenRoleCombat"),
 ("ServerScriptService","EGGRUMBLE_SwarmCombat"),
 ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview"),
 ("ServerScriptService","GQ8_LobbySocialPlaza"),
 ("ServerScriptService","EGGRUMBLE_MapIntelBridge"),
 ("ReplicatedStorage","GQ8Trade","GQ8_TradePolicy")}
 assert needed.issubset(old)
 out.mkdir(parents=True);(out/"sources").mkdir()
 project=copy.deepcopy(p);project["name"]="EGGRUMBLE_PRIVATE_REAL61_HUD_FOG_TRADE"
 def rewrite(node):
  if not isinstance(node,dict):return
  if "$path" in node:
   original=Path(node["$path"])
   assert not original.is_absolute() and ".." not in original.parts
   node["$path"]="../on59/"+original.as_posix()
  for k,v in node.items():
   if k!="$path":rewrite(v)
 rewrite(project["tree"])
 added=[]
 for route,(name,cl) in ROUTES.items():
  b=(T/name).read_bytes();(out/"sources"/name).write_bytes(b)
  node=project["tree"]
  for k in route[:-1]:
   assert k in node
   node=node[k]
  assert route[-1] not in node
  node[route[-1]]={"$path":"sources/"+name}
  added.append({"route":"/".join(route),"class":cl,"sha256":sha(b),"bytes":len(b)})
 target=out/"GQ8_REAL61_COMPOSITE.project.json"
 target.write_text(json.dumps(project,indent=2,ensure_ascii=False)+"\n")
 _,all61=flatten(target)
 assert len(all61)==61 and set(all61)==set(old)|set(ROUTES)
 for k,f in old.items():
  assert klass(all61[k])==klass(f) and all61[k].read_bytes()==f.read_bytes()
 for k in ROUTES:assert klass(all61[k])==ROUTES[k][1]
 assert set(all61)-set(off_sources)=={
 ("ReplicatedStorage","EGGRUMBLE_HudPresentationPolicy"),
 ("ServerScriptService","EGGRUMBLE_MapVisibilityPolicy"),
 ("ServerScriptService","EGGRUMBLE_MapIntelBridge"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime"),
 *ROUTES}
 for path in PINS:
  if "gq8_trade_ux" in path:
   s=(ROOT/path).read_text()
   for bad in ("DataStoreService","MarketplaceService","ProcessReceipt","FireServer(","UpdateAsync("):
    assert bad not in s,("RED_TRADE_PAID_OWNER",path,bad)
 data={"official_rc_base":"a6020867fac80fa3b2ca47478625873fc6f3678e",
 "origin_hud":{"pr":829,"sha":"5eebda8d8365bde3f9e9c8c989b2906ddd412ad3"},
 "origin_trade":{"pr":838,"sha":"9f6ac8aebb7467d1249e9b36a5463b7ca0065c9b"},
 "on_source_count":61,"off_source_count":55,"original55_mutations":0,
 "hud_additions":4,"trade_additions":2,"new_routes":added,"source_pins":PINS,
 "areas_preserved":["characters","field","combat","castles","neutrals","items","lobby","ui","balance"],
 "payment":False,"trade_settlement":False,"publish":False,"official_rc_integrated":False,
 "studio_solo":"NOT_TESTED","studio_2client":"NOT_TESTED","android15":"NOT_TESTED",
 "fun":"PRODUCT_NO_GO","rollback":"select exact OFF55 project"}
 (out/"GQ8_REAL61_RECEIPT.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
 print("GQ8_REAL61_PARENT55_UNCHANGED_HUD4_TRADE2_CLASS_SOURCE_LOCK_PASS")
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--parent59",type=Path,required=True)
 a.add_argument("--receipt59",type=Path,required=True)
 a.add_argument("--off55",type=Path,required=True)
 a.add_argument("--out",type=Path,required=True)
 z=a.parse_args();run(z.parent59,z.receipt59,z.off55,z.out)
