#!/usr/bin/env python3
"""Fail-closed, byte-reversible V3 server-cast cue in existing CombatFeel LocalScript.

This is NOT hit confirmation, damage, ability casting, a new server authority, or
a new LocalScript. The prior original author source remains the default OFF.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

FEATURE = "GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117"
AUTHOR_COMMIT = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_GIT_BLOB = "5509326beed0827b020d967cd9562724d8abbd2a"
ANCHOR = 'mark.Parent=gui\n'
START = '-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 BEGIN'
END = '-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 END'
INSERT = '''-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 BEGIN
-- Server-accepted skill activation, intentionally distinct from a confirmed HIT.
-- No input hook, network events or damage; zero always-visible HUD.
local castCue=Instance.new("Frame")
castCue.Name="ServerAcceptedCastCue"
castCue.AnchorPoint=Vector2.new(.5,.5)
castCue.Position=UDim2.fromScale(.5,.56)
castCue.Size=UDim2.fromOffset(20,3)
castCue.BorderSizePixel=0
castCue.BackgroundColor3=Color3.fromRGB(230,230,230)
castCue.BackgroundTransparency=1
castCue.Visible=false
castCue.Parent=gui
local CAST_CUE_MIN_GAP=.12
local lastCastCue=-100
local lastCastSignature=""
local castCueSerial=0
player:GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature"):Connect(function()
 local sig=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 if type(sig)~="string" or sig==lastCastSignature then return end
 local role,slot,seq=string.match(sig,"^([A-Z]+):([ABC]):(%d+)$")
 if not role or not slot or not seq then return end
 if not tones[role] then return end
 lastCastSignature=sig
 if player:GetAttribute("EGGRUMBLE_Eliminated")==true or reduced() then return end
 local char=player.Character
 local hum=char and char:FindFirstChildOfClass("Humanoid")
 if not hum or hum.Health<=0 then return end
 local now=os.clock()
 if now-lastCastCue<CAST_CUE_MIN_GAP then return end
 lastCastCue=now
 castCueSerial+=1
 local current=castCueSerial
 castCue.BackgroundColor3=tones[role]
 castCue.BackgroundTransparency=.24
 castCue.Visible=true
 TweenService:Create(castCue,TweenInfo.new(.18,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
  {BackgroundTransparency=1}):Play()
 task.delay(.19,function()
  if current==castCueSerial and castCue.Parent then castCue.Visible=false end
 end)
end)
-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 END
'''
def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def patch(source: str) -> str:
    if START in source or END in source:
        raise ValueError("RED_ALREADY_SELECTED")
    if source.count(ANCHOR)!=1:
        raise ValueError("RED_ANCHOR_DRIFT")
    # GQ504 appends its own confirmed-hit audio listener at the end.
    # Only the original preceding client section is our insertion authority.
    AUDIO_MARKER="\n-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117"
    if source.count(AUDIO_MARKER)>1: raise ValueError("RED_DUPLICATE_AUDIO_OWNER")
    original=source.split(AUDIO_MARKER,1)[0]
    for required in (
        'local player=Players.LocalPlayer',
        'local TweenService=game:GetService("TweenService")',
        'local function reduced():boolean',
        'player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',
    ):
        if original.count(required)!=1: raise ValueError("RED_SOURCE_CONTRACT_"+required)
    # Original reduced() is declared below mark.Parent=gui, so move the cue
    # to AFTER its declaration by using an independent post-function anchor.
    post='player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(function()\n'
    if original.count(post)!=1: raise ValueError("RED_POST_ANCHOR_DRIFT")
    # Replace the first (original HIT) listener, not GQ504 appended audio.
    selected=original.replace(post,INSERT+post,1)+source[len(original):]
    if undo(selected)!=source: raise ValueError("RED_INVERSE")
    return selected

def undo(selected: str) -> str:
    cue=INSERT
    if selected.count(cue)!=1: raise ValueError("RED_OFF_SOURCE_DRIFT")
    return selected.replace(cue,"",1)

def validate_original(source: str) -> None:
    if git_blob(source.encode("utf-8"))!=ORIGINAL_GIT_BLOB:
        raise ValueError("RED_ORIGINAL_BLOB_DRIFT")
    if not source.startswith("--!strict\n") or not source.endswith("\n"):
        raise ValueError("RED_SOURCE_FORMAT")

def safety_checks(source: str) -> None:
    for forbidden in (
        'Instance.new("RemoteEvent")', 'Instance.new("RemoteFunction")',
        'TakeDamage(', 'DataStoreService', 'MarketplaceService',
        'FireServer(', ':Activate(', 'tool.Activated',
    ):
        if forbidden in INSERT: raise ValueError("RED_NEW_AUTHORITY_"+forbidden)
    for required in (
        'GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature")',
        'EGGRUMBLE_Eliminated', 'lastCastSignature=sig',
        'hum.Health<=0', 'now-lastCastCue<CAST_CUE_MIN_GAP',
        'reduced()', 'BackgroundTransparency=1',
    ):
        if required not in INSERT: raise ValueError("RED_SAFETY_GUARD_"+required)
    if source.split("\n-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117",1)[0].count('player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")')!=1 or undo(source).count("EGGRUMBLE_ImpactSequence")!=source.count("EGGRUMBLE_ImpactSequence"):
        raise ValueError("RED_EXISTING_HIT_FEEDBACK_DRIFT")
    if source.count(START)!=1 or source.count(END)!=1:
        raise ValueError("RED_SELECTED_SCOPE")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--off",action="store_true")
    args=ap.parse_args()
    base=args.source.read_text(encoding="utf-8")
    validate_original(base)
    selected=patch(base)
    safety_checks(selected)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(base if args.off else selected,encoding="utf-8")
    print("GQ8_CAST_CUE_ORIGINAL_BLOB_LOCK_ON_OFF_EXACT_PASS",FEATURE)
if __name__=="__main__": main()
