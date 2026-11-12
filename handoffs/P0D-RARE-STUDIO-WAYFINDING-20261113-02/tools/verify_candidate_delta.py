"""Exactly five ADDITIVE source hooks from SHA-pinned #243 original server.
Fail closed on changes to child book, chance, proximity, status or production guards.
"""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
PARENT=R.parent/"P0D-RARE-CHILD-CLUE-COMPASS-20261113-01"
ORIGINAL=PARENT/"src/RareDiscoveryCluePreview.server.luau"
CANDIDATE=R/"src/RareDiscoveryWayfindingPreview.server.luau"
CHANGES=[
 ('local ClueHUD=require(script.Parent.RareClueHUD)',
  'local ClueHUD=require(script.Parent.RareClueHUD)\nlocal Guides=require(script.Parent.RareStudioGuides)'),
 ('local goodClue,clueWhy=Clue.validate()\nassert(goodBook and goodPlan and goodClue,bookWhy.." / "..planWhy.." / "..clueWhy)',
  'local goodClue,clueWhy=Clue.validate()\nlocal goodGuides,guideWhy=Guides.validate()\nassert(goodBook and goodPlan and goodClue and goodGuides,\n    bookWhy.." / "..planWhy.." / "..clueWhy.." / "..guideWhy)'),
 ('layer.Parent=map.folder\n\nlocal books={}',
  'layer.Parent=map.folder\nlocal guides=Guides.mount(map.folder)\n\nlocal books={}'),
 ('local function clearActive()\n    if promptConn then',
  'local function clearActive()\n    guides:clear()\n    if promptConn then'),
 ('Models.update(visual,p,0)\n    promptConn=visual.prompt.Triggered:Connect',
  'Models.update(visual,p,0)\n    assert(guides:show(id),"GUIDE_MUST_MATCH_CURRENT_NEUTRAL")\n    promptConn=visual.prompt.Triggered:Connect'),
]
def verify():
    origin=ORIGINAL.read_text(encoding="utf-8")
    import json
    m=json.loads((PARENT/"BUILD_MANIFEST.json").read_text("utf-8"))
    line=next((v for v in m["files"] if v["path"]=="src/RareDiscoveryCluePreview.server.luau"),None)
    raw=ORIGINAL.read_bytes()
    if not line or line["size"]!=len(raw) or line["sha256"]!=hashlib.sha256(raw).hexdigest():
        raise ValueError("frozen original full server source not exact")
    for before,after in CHANGES:
        if origin.count(before)!=1:raise ValueError("expected original server hunk not unique")
        origin=origin.replace(before,after,1)
    candidate=CANDIDATE.read_text(encoding="utf-8")
    if candidate!=origin:raise ValueError("unapproved full server mutation")
    for guard in ("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false",
                  "RunService:IsStudio()","RunService:IsServer()",
                  "TRAP_RAIDERS_S1","Policy.MIN_INTERACTION_DISTANCE"):
        if guard not in candidate:raise ValueError("missing original safety "+guard)
    print("P0D_WAYFINDING_EXACT_FIVE_SAFE_HUNKS_PASS")
    return len(CHANGES)
if __name__=="__main__":
    verify()
