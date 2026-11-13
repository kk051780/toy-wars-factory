#!/usr/bin/env python3
"""D18 extension #278 source-only validation, zero live-game assertions."""
import hashlib,json,math,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
DATA=ROOT/"data/models.json"
CATS=("BE","SP","VE","WE","ZO","TR")
WORLDS=("虹雲の漂流庭園","珊瑚の月光港")
PART_FIELDS={"name","group","position","size","rotation","shape","color","far","signature_tag"}
def fail(msg):raise ValueError(msg)
def num(x,lo,hi):
 return type(x) in (int,float) and math.isfinite(x) and lo<=x<=hi
def load_legacy():
 atlas=json.loads((REPO/"handoffs/P0D-D18-BATCH6-SIX-WORLDS-20261113-01/data/flagship72_registry.json").read_text(encoding="utf8"))
 arr=atlas["entries"]
 if len(arr)!=72 or len({x["id"] for x in arr})!=72:fail("original atlas72 bad")
 names={x["name"] for x in arr}
 ids={x["id"] for x in arr}
 c6=json.loads((REPO/"handoffs/P0D-D18-BATCH6-SIX-WORLDS-20261113-01/data/batch_claims.json").read_text(encoding="utf8"))
 sources=set(c6["previous_3d_source_ids"]+c6["new_3d_source_ids"])
 for batch,dir in [
  (7,"P0D-D18-BATCH7-SIX-CHILD-EXPLORE-20261113-01"),
  (8,"P0D-D18-BATCH8-SIX-ORIGINAL-DISPLAY-20261113-01"),
  (9,"P0D-D18-BATCH9-SIX-ORIGINAL-20261113-01"),
  (10,"P0D-D18-BATCH10-FINAL-SIX-20261113-01")]:
  path=REPO/"handoffs"/dir/"data/models.json"
  obj=json.loads(path.read_text(encoding="utf8"))
  for x in obj["characters"]:
   if x["id"] in sources:fail("legacy duplicate")
   sources.add(x["id"])
 if sources!=ids or len(sources)!=72:fail("legacy72 incomplete")
 return ids,names
def validate(d):
 if d.get("schema")!="P0D_D18_EXTENSION1_SKY_SEA_12_SOURCE_ONLY_V1":fail("schema")
 if d.get("game_id")!="TRAP_RAIDERS" or d.get("display_brand")!="EGG RAID RUMBLE":fail("identity")
 cs=d.get("characters")
 if type(cs)!=list or len(cs)!=12:fail("12 source models required")
 legacy_ids,legacy_names=load_legacy()
 ids=[c.get("id") for c in cs]
 names=[c.get("name") for c in cs]
 if len(set(ids))!=12 or len(set(names))!=12:fail("duplicate new IDs/names")
 if set(ids)&legacy_ids or set(names)&legacy_names:fail("old72 collision")
 expected={f"TRCX-{cat}-{n:03d}" for cat in CATS for n in (1,2)}
 if set(ids)!=expected:fail("extension reserved 12 IDs only")
 if {c["category"] for c in cs}!=set(CATS):fail("categories")
 n_parts=0
 for c in cs:
  rid=c["id"];cat=c["category"];idx=int(rid[-3:])
  if cat!=rid.split("-")[1]:fail("category mismatch")
  if c["world"]!=WORLDS[idx-1]:fail("world ID mismatch")
  if c["rarity"] not in {"レア","エピック","レジェンド","ミシック"}:fail("rarity invalid")
  if type(c["name"])!=str or not 3<=len(c["name"])<=22:fail("name invalid")
  if type(c.get("signature_silhouette"))!=str or len(c["signature_silhouette"])<14:fail("silhouette")
  tags=c.get("signature_tags")
  if type(tags)!=list or len(tags)!=3 or len(set(tags))!=3 or any(not re.fullmatch("[a-z0-9_]{4,32}",t) for t in tags):fail("three original shape anchors")
  palette=c.get("palette")
  if type(palette)!=dict or not 3<=len(palette)<=7:fail("palette")
  for rgb in palette.values():
   if type(rgb)!=list or len(rgb)!=3 or any(type(x)!=int or not 0<=x<=255 for x in rgb):fail("bad RGB")
  ps=c.get("parts")
  if type(ps)!=list or not 10<=len(ps)<=24:fail("Part cost")
  n_parts+=len(ps)
  if len({p.get("name") for p in ps})!=len(ps):fail("Part duplicate names")
  far=[p for p in ps if p.get("far") is True]
  if not 8<=len(far)<=18 or not set(tags)<={p.get("signature_tag") for p in far}:fail("3 visual signs must survive LOD")
  groups=set()
  for p in ps:
   if set(p)!=PART_FIELDS or type(p["name"])!=str or len(p["name"])>32:fail("source Part fields")
   if p["shape"] not in ("Block","Ball","Cylinder") or p["color"] not in palette or type(p["far"])!=bool:fail("unsafe visual fields")
   for key,lo,hi in [("position",-8,8),("size",.06,6),("rotation",-180,180)]:
    a=p[key]
    if type(a)!=list or len(a)!=3 or any(not num(x,lo,hi) for x in a):fail("geometry "+key)
   groups.add(p["group"])
  poses=c.get("pose_offsets")
  if type(poses)!=dict or set(poses)!={"idle","tap","win","loss"}:fail("poses")
  for offs in poses.values():
   if type(offs)!=dict:fail("pose changes")
   for group,amount in offs.items():
    if group not in groups or type(amount)!=dict or not set(amount)<={"dy","rz"}:fail("pose group")
    for k,v in amount.items():
     if not num(v,-.5 if k=="dy" else -30,.5 if k=="dy" else 30):fail("pose offset")
 if n_parts>200:fail("12 item studio viewport budget exceeded")
 return {"new":12,"legacy":72,"total":84,"parts":n_parts}
def validate_contract(c,models):
 if c.get("schema")!="P0D_COLLECTION_EXTENSION1_DESIGN_CONTRACT_V1" or c.get("sourcePrototypeRosterTotal")!=84:fail("collection contract schema")
 if any(c.get(k)!=v for k,v in [("extensionCount",12),("existingCanonicalAtlasCount",72),("implementedOwnedItems",0),("equippingImplemented",False),("realGameHatchingImplemented",False),("noPayToWin",True),("probabilityTablePresent",False)]):fail("false live-collection status")
 items=c.get("items",[])
 if len(items)!=12 or {x.get("itemId") for x in items}!={x["id"] for x in models["characters"]}:fail("collection IDs")
 classes={"BE":"BEAST","SP":"SPELL","VE":"MOUNT","WE":"ITEM","ZO":"ZOMBIE","TR":"TRAP"}
 for it in items:
  if it.get("category")!=classes[it["itemId"].split("-")[1]]:fail("classification")
  for k,v in (("sourceItemOnly",True),("playerOwned",False),("availableInLiveGame",False),("actualAbilityImplemented",False),("freeHatchCandidate",True),("raritySidegradeOnly",True),("freeStarterEquivalentRequired",True)):
   if it.get(k)!=v:fail("fake entitlement "+k)
  for k in ("abilityConcept","counterplay","firstVisibleTell"):
   if type(it.get(k))!=str or len(it[k])<8:fail("insufficient real gameplay contract")
 return True
def gitblob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def verify_manifest():
 mf=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 if mf.get("new_source_count")!=12 or mf.get("source_roster_total")!=84:fail("manifest count")
 fs=mf.get("source_files")
 if type(fs)!=list or len(fs)!=12 or len({x["path"] for x in fs})!=12:fail("manifest12")
 for x in fs:
  p=x["path"]
  if p.startswith("/") or ".." in pathlib.PurePosixPath(p).parts:fail("unsafe path")
  if gitblob((ROOT/p).read_bytes())!=x["git_blob_sha1"]:fail("changed original source "+p)
 return True
if __name__=="__main__":
 m=json.loads(DATA.read_text(encoding="utf8"))
 c=json.loads((ROOT/"data/collection_contract.json").read_text(encoding="utf8"))
 print("D18_EXT1_72_IMMUTABLE_PLUS_12_NEW_SOURCE_PASS",validate(m))
 validate_contract(c,m)
 assert verify_manifest()
 print("D18_EXT1_12_SOURCE_FILE_SHA_AND_FREE_OWN_EQUIP_NOT_IMPLEMENTED_GATE_PASS")
