#!/usr/bin/env python3
"""Fail-closed source-only D18 Batch10 geometry and Git blob verification (no Studio claim)."""
import hashlib,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
ATLAS="cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01"
CANON={
"TRCA-BE-108":("七鈴の王獣","暁鐘の王城","レジェンド"),
"TRCA-SP-063":("一番星の火輪","火輪の熔炉","レジェンド"),
"TRCA-VE-081":("祭りの大荷車","黄金麦の丘","レジェンド"),
"TRCA-WE-063":("炉鈴ホルン","火輪の熔炉","レジェンド"),
"TRCA-ZO-081":("収穫の旗振り兵","黄金麦の丘","レジェンド"),
"TRCA-TR-090":("時砂跳ね台","砂時計の迷宮","レジェンド"),
}
CATS={"BE","SP","VE","WE","ZO","TR"}
PART_KEYS={"name","position","size","rotation","shape","color","far","signature_tag","group"}
def fail(reason):raise ValueError(reason)
def num(x,a,b):return type(x) in (int,float) and math.isfinite(x) and a<=x<=b
def validate_models(d):
 if d.get("schema")!="P0D_D18_BATCH10_SOURCE_ONLY_V1" or d.get("game_id")!="TRAP_RAIDERS" or d.get("source_atlas_sha256")!=ATLAS:fail("metadata")
 cs=d.get("characters")
 if not isinstance(cs,list) or len(cs)!=6 or {x.get("id") for x in cs}!=set(CANON):fail("six IDs")
 if {x.get("category") for x in cs}!=CATS:fail("categories")
 for c in cs:
  rid=c["id"];name,world,rarity=CANON[rid]
  if (c.get("name"),c.get("world"),c.get("rarity"))!=(name,world,rarity):fail("canonical identity")
  if c.get("category")!=rid.split("-")[1]:fail("category mismatch")
  tags=c.get("signature_tags")
  if not isinstance(tags,list) or len(tags)!=3 or len(set(tags))!=3:fail("tags")
  if not isinstance(c.get("signature_silhouette"),str) or len(c["signature_silhouette"])<12:fail("silhouette")
  pal=c.get("palette")
  if not isinstance(pal,dict) or not 3<=len(pal)<=6:fail("palette")
  for rgb in pal.values():
   if not isinstance(rgb,list) or len(rgb)!=3 or any(type(v)!=int or not 0<=v<=255 for v in rgb):fail("RGB")
  parts=c.get("parts")
  if not isinstance(parts,list) or not 8<=len(parts)<=24:fail("part budget")
  far=[p for p in parts if p.get("far") is True]
  if not 6<=len(far)<=18 or not set(tags)<={p.get("signature_tag") for p in far}:fail("far silhouette lost")
  if len({p["name"] for p in parts})!=len(parts):fail("duplicate part")
  groups=set()
  for p in parts:
   if set(p)!=PART_KEYS or not isinstance(p["name"],str) or len(p["name"])>32:fail("part fields")
   if p["shape"] not in ("Block","Ball","Cylinder") or p["color"] not in pal or type(p["far"]) is not bool:fail("invalid shape/color")
   if not all(isinstance(p[k],list) and len(p[k])==3 for k in ("size","position","rotation")):fail("vectors")
   if any(not num(v,.06,6) for v in p["size"]):fail("size")
   if any(not num(v,-8,8) for v in p["position"]):fail("position")
   if any(not num(v,-180,180) for v in p["rotation"]):fail("rotation")
   if not isinstance(p["group"],str) or not isinstance(p["signature_tag"],str):fail("tag")
   groups.add(p["group"])
  pose=c.get("pose_offsets")
  if set(pose)!={"idle","tap","win","loss"}:fail("poses")
  for offsets in pose.values():
   if not isinstance(offsets,dict):fail("pose offsets")
   for group,amount in offsets.items():
    if group not in groups or not isinstance(amount,dict) or set(amount)-{"dy","rz"}:fail("pose group")
    if any(not num(v,-30 if k=="rz" else -.5,30 if k=="rz" else .5) for k,v in amount.items()):fail("pose value")
 return True
def verify_manifest():
 manifest=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 if manifest.get("source_files") is None or len(manifest["source_files"])!=11:fail("manifest file count")
 if manifest.get("atlas_sha256")!=ATLAS:fail("manifest atlas")
 for item in manifest["source_files"]:
  path=item["path"]
  if path.startswith("/") or ".." in pathlib.PurePosixPath(path).parts:fail("unsafe path")
  raw=(ROOT/path).read_bytes()
  h=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
  if h!=item["git_blob_sha1"]:fail("source modified "+path)
 return True
if __name__=="__main__":
 d=json.loads((ROOT/"data/models.json").read_text(encoding="utf8"))
 validate_models(d);verify_manifest();print("BATCH10_CANON_AND_SOURCE_MANIFEST_PASS models=6 files=11")
