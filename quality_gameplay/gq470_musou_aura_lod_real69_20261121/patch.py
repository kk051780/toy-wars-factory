#!/usr/bin/env python3
"""Exact-source reversible visual patch: REAL69 Musou Aura, no game authority."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

FEATURE = "GQ470_FB015_MUSOU_AURA_COMPACT_LOD_REAL69_20261121"
BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraClient"
TARGET_SHA256 = "b2c279371a8fd986b929883290aae58ed9acdafb7cd48f878eae3785e4acccab"
PAIRS = (
    ("GUI", ' gui.Size=UDim2.fromOffset(195,54)\n gui.StudsOffsetWorldSpace=Vector3.new(0,3.35,0)\n gui.MaxDistance=160',
     ' -- FB-015: a compact, occluded-aware status plate; world labels must not fill mobile views.\n gui.Size=UDim2.fromOffset(150,34)\n gui.StudsOffsetWorldSpace=Vector3.new(0,3.0,0)\n gui.MaxDistance=100'),
    ("TEXT", ' label.TextScaled=true\n label.Font=Enum.Font.GothamBlack',
     ' label.TextScaled=false\n label.TextSize=16\n label.TextTruncate=Enum.TextTruncate.AtEnd\n label.Font=Enum.Font.GothamBlack'),
    ("HIGHLIGHT", ' h.FillTransparency=.7\n h.OutlineTransparency=0',
     ' h.FillTransparency=.84\n h.OutlineTransparency=.22'),
    ("GLOW", ' particles.LightEmission=.7\n particles.Rate=12\n particles.Speed=NumberRange.new(1.2,2.8)',
     ' particles.LightEmission=.28\n particles.Rate=7\n particles.Speed=NumberRange.new(.65,1.6)'),
    ("LIFE", ' particles.Lifetime=NumberRange.new(.35,.7)\n particles.Size=NumberSequence.new({\n  NumberSequenceKeypoint.new(0,.42),\n  NumberSequenceKeypoint.new(.7,.25)',
     ' particles.Lifetime=NumberRange.new(.25,.48)\n particles.Size=NumberSequence.new({\n  NumberSequenceKeypoint.new(0,.34),\n  NumberSequenceKeypoint.new(.7,.18)'),
    ("BURST_START", ' particles:Emit(snapshot.phase=="KAKUHEN" and 18 or 8)',
     ' if localViewDist(head)<=85 then\n  particles:Emit(snapshot.phase=="KAKUHEN" and 12 or 6)\n end'),
    ("UPDATE_VISIBILITY", ''' local h=folder:FindFirstChild("MusouHeroOutline")
 local gui=folder:FindFirstChild("MusouEnemyVisibleNameplate")
 if h then h.FillTransparency=snapshot.phase=="KAKUHEN" and .42 or .7 end
 if gui then''',
     ''' local h=folder:FindFirstChild("MusouHeroOutline")
 local gui=folder:FindFirstChild("MusouEnemyVisibleNameplate")
 local head=character:FindFirstChild("Head")
 local dist=if head and head:IsA("BasePart") then localViewDist(head) else math.huge
 -- Fixed distance LOD: no RenderStepped connection and no new camera loop.
 if h then
  h.Enabled=dist<=115
  h.FillTransparency=snapshot.phase=="KAKUHEN" and .69 or .84
 end
 if gui then
  gui.Enabled=dist<=95'''),
    ("UPDATE_BURST", ''' local head=character:FindFirstChild("Head")
 if head then
  local a=head:FindFirstChild("MusouAuraOrigin")''',
     ''' if head then
  local a=head:FindFirstChild("MusouAuraOrigin")'''),
    ("UPDATE_RATE", '''   if previous~=snapshot.phase then
    particles:Emit(snapshot.phase=="KAKUHEN" and 28 or 12)
   end
   local dist=localViewDist(head)
   local rate=if snapshot.phase=="KAKUHEN" then 24 else 12
   particles.Rate=if dist<=85 then rate elseif dist<=140 then 5 else 0''',
     '''   if previous~=snapshot.phase and dist<=85 then
    particles:Emit(snapshot.phase=="KAKUHEN" and 16 or 8)
   end
   local rate=if snapshot.phase=="KAKUHEN" then 12 else 7
   particles.Rate=if dist<=55 then rate elseif dist<=95 then 3 else 0'''),
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch(source: str) -> str:
    if FEATURE in source:
        raise ValueError("RED_ALREADY_PATCHED")
    if '-- GQ8 #824 OPTIONAL VFX MODULE' not in source:
        raise ValueError("RED_WRONG_SOURCE_OWNER")
    for critical in ('local function validSnapshot(s)', 'function M.start(character,snapshot)',
                     'function M.update(character,snapshot)', 'function M.stop(character)',
                     'RunService:IsClient()', 'ClientCosmeticOnly'):
        if critical not in source:
            raise ValueError("RED_MISSING_" + critical)
    out = source
    for key, old, new in PAIRS:
        if out.count(old) != 1:
            raise ValueError("RED_ANCHOR_" + key)
        out = out.replace(old, new, 1)
    for token in ('Instance.new("Highlight")', 'Instance.new("BillboardGui")',
                  'Instance.new("ParticleEmitter")', 'Instance.new("Attachment")',
                  'Instance.new("Folder")', 'M.stop(character)', 'clean(character)',
                  'validSnapshot(snapshot)', 'GetService("RunService")'):
        if out.count(token) != source.count(token):
            raise ValueError("RED_AUTHORITY_OR_BUDGET_" + token)
    if out.count('local head=character:FindFirstChild("Head")') != source.count('local head=character:FindFirstChild("Head")'):
        raise ValueError("RED_HEAD_LIFETIME")
    if out.count('particles:Emit(') != source.count('particles:Emit('):
        raise ValueError("RED_EMISSION_OWNER")
    if len(out) == len(source):
        raise ValueError("RED_NO_PATCH")
    return out

def negatives(original: str) -> int:
    modified = patch(original)
    bad = [
        modified, original.replace(' gui.Size=UDim2.fromOffset(195,54)', ' gui.Size=UDim2.fromOffset(194,54)', 1),
        original.replace(' particles.LightEmission=.7', ' particles.LightEmission=1', 1),
        original.replace(' particles:Emit(snapshot.phase=="KAKUHEN" and 18 or 8)', ' particles:Emit(100)', 1),
        original.replace('local function validSnapshot(s)', 'local function badSnapshot(s)', 1),
        original.replace('ClientCosmeticOnly', 'ClientCombatAuthoritative', 1),
        original.replace(' h.FillTransparency=.7', ' h.FillTransparency=.2', 1),
        original.replace(' local head=character:FindFirstChild("Head")\n if head then\n  local a=', ' local head=character:FindFirstChild("Torso")\n if head then\n  local a=', 1),
        original.replace('RunService:IsClient()', 'RunService:IsServer()'),
    ]
    for i, candidate in enumerate(bad):
        try:
            patch(candidate)
        except ValueError:
            continue
        raise AssertionError('NEGATIVE_FAILED_' + str(i))
    return len(bad)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--report', required=True, type=Path)
    ns = ap.parse_args()
    raw = ns.source.read_bytes()
    if sha(raw) != TARGET_SHA256:
        raise ValueError("RED_FORMAL_SOURCE_SHA_DRIFT")
    original = raw.decode('utf-8')
    candidate = patch(original)
    num = negatives(original)
    if ns.source.resolve() == ns.output.resolve():
        raise ValueError("RED_NO_INPLACE_SOURCE_WRITE")
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_bytes(candidate.encode('utf-8'))
    proof = dict(feature_id=FEATURE, formal_base=BASE, selected_route=ROUTE,
                 original_sha256=sha(raw), candidate_sha256=sha(candidate.encode()),
                 original_bytes=len(raw), candidate_bytes=len(candidate.encode()),
                 negative_mutations_rejected=num, source_changed=1,
                 adds_game_authority=False, adds_render_loop=False,
                 real_studio='NOT_TESTED', android15='NOT_TESTED',
                 human_art='NOT_TESTED', owner_accepted=False,
                 art_gate='ART_NO_GO')
    ns.report.parent.mkdir(parents=True, exist_ok=True)
    ns.report.write_text(json.dumps(proof, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(proof, ensure_ascii=False))

if __name__ == '__main__':
    main()
