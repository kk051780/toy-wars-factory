"""Fail closed: the 9KB Studio candidate must differ from immutable original
by EXACTLY four additive clue hooks, no hidden gameplay changes, no local enable.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/"P0D-RARE-DISCOVERY-BOOK-20261112-01"
S=OLD/"src/RareDiscoveryStudio.server.luau"
T=ROOT/"src/RareDiscoveryCluePreview.server.luau"
MODIFICATIONS=[
 ('local HUD=require(script.Parent.RareDiscoveryHUD)\nlocal Plan=require(script.Parent.RareDiscoveryQAPlan)',
  'local HUD=require(script.Parent.RareDiscoveryHUD)\nlocal Plan=require(script.Parent.RareDiscoveryQAPlan)\nlocal Clue=require(script.Parent.RareCluePolicy)\nlocal ClueHUD=require(script.Parent.RareClueHUD)'),
 ('local goodPlan,planWhy=Plan.validate()\nassert(goodBook and goodPlan,bookWhy.." / "..planWhy)',
  'local goodPlan,planWhy=Plan.validate()\nlocal goodClue,clueWhy=Clue.validate()\nassert(goodBook and goodPlan and goodClue,bookWhy.." / "..planWhy.." / "..clueWhy)'),
 ('            HUD.update(player,nextBook)\n            current.twoClients[player]=true',
  '            HUD.update(player,nextBook)\n            ClueHUD.update(player,nextBook)\n            current.twoClients[player]=true'),
 ('            HUD.mount(player,books[player])\n            emit("SESSION_HUD_MOUNTED"',
  '            HUD.mount(player,books[player])\n            ClueHUD.mount(player,books[player])\n            emit("SESSION_HUD_MOUNTED"'),
]
def verify():
    m=json.loads((OLD/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
    origin=S.read_bytes()
    entry=next((row for row in m["files"]
        if row["path"]=="src/RareDiscoveryStudio.server.luau"),None)
    if not entry or entry["size"]!=len(origin) or entry["sha256"]!=hashlib.sha256(origin).hexdigest():
        raise ValueError("pinned original full server not exact manifest")
    text=origin.decode("utf-8")
    for old,new in MODIFICATIONS:
        if text.count(old)!=1:raise ValueError("original anchor changed")
        text=text.replace(old,new,1)
    candidate=T.read_text(encoding="utf-8")
    if text!=candidate:
        raise ValueError("candidate full server contains unapproved source changes")
    if 'ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false' not in candidate or 'RunService:IsStudio()' not in candidate:
        raise ValueError("unsafe studio enabling or missing owner guard")
    print("P0D_CLUE_EXACT_ORIGINAL_SERVER_FOUR_BOUNDED_HUNKS_PASS")
    print("P0D_CLUE_FROZEN_SERVER_BLOB_SHA256="+hashlib.sha256(origin).hexdigest())
    print("P0D_CLUE_NEW_CANDIDATE_SERVER_SHA256="+hashlib.sha256(candidate.encode()).hexdigest())
    return 4
if __name__=="__main__":
    verify()
