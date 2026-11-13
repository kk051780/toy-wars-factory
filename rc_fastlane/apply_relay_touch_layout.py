#!/usr/bin/env python3
"""Private RC61 portrait relay touchscreen overlap fix. HUD-only and fail closed.

The original WCS+SevenJobs+ClassicRelay+Starfall 61 source bodies are immutable
except one localized button layout function inserted into the EXISTING HUD.
No new Remote, DataStore, score or state authority. No canonical RC writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HUD="client/HUD.client.luau"
FEATURE="RC61_RELAY_TOUCH_LAYOUT"
ORIGINAL="relayButton.Visible=false"
INSERT="""relayButton.Visible=false
-- RC61 TOUCH: narrow portrait controls must not overlap rescue/net or SevenJobs.
-- The existing button() uses AnchorPoint=(0,1). Source geometry:
-- default centered slot overlaps rescue at width 375-600; use the quiet
-- left-middle slot on <=650px while retaining the proven landscape slot.
local relayViewportConnection: RBXScriptConnection?=nil
local function layoutRelayTouch()
    local camera=workspace.CurrentCamera
    local viewWidth=if camera then camera.ViewportSize.X else 800
    if viewWidth<=650 then
        relayButton.Position=UDim2.new(0,10,1,-127)
    else
        relayButton.Position=UDim2.new(.5,-56,1,-164)
    end
end
local function bindRelayViewport()
    if relayViewportConnection then
        relayViewportConnection:Disconnect()
        relayViewportConnection=nil
    end
    local camera=workspace.CurrentCamera
    if camera then
        relayViewportConnection=camera:GetPropertyChangedSignal("ViewportSize"):Connect(layoutRelayTouch)
    end
    layoutRelayTouch()
end
workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(bindRelayViewport)
bindRelayViewport()"""


def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def inventory(dist:Path)->dict[str,bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}


def run(dist:Path,enabled:bool)->None:
    before=inventory(dist)
    assert len(before)==61,("NEED_REAL_FULL_RC61",len(before))
    assert HUD in before
    for p in ("server/Game.server.luau","server/WCS_CrystalCanyon.server.luau",
              "server/SevenJobsRules.luau","server/EggRelayPolicy.luau",
              "server/StarfallPath.server.luau"):
        assert p in before,("MISSING_FOUR_FEATURE_GAMEROOT",p)

    pins={k:gitblob(v) for k,v in before.items()}
    original_lock=dist/"SOURCE_LOCK.json"
    feature_lock=dist/"RC_FEATURE_LOCK.json"
    lock=json.loads(original_lock.read_text("utf8"))
    assert lock["total_scripts"]==61 and lock["blobs"]==pins,"RC61_SOURCE_PIN_DRIFT"
    feature=json.loads(feature_lock.read_text("utf8"))
    assert feature["total_sources"]==61 and feature["source_gitblobs"]==pins,"RC61_FEATURE_PIN_DRIFT"
    flags=feature.get("feature_flags",{})
    assert all(flags.get(name)==True for name in
               ("WCS_F01_C01","SEVEN_JOBS_PVE_V1",
                "EGG_RELAY_CLASSIC_V1","STARRY_PATH_V1")), "INCOMPATIBLE_BOOT_FLAGS"

    text=before[HUD].decode("utf8")
    assert "local function layoutRelayTouch()" not in text, "DUPLICATE_TOUCH_PATCH"
    assert text.count(ORIGINAL)==1,"RELAY_BUTTON_ANCHOR_DRIFT"
    assert "b.AnchorPoint = Vector2.new(0, 1)" in text
    assert text.count("UDim2.fromOffset(112,58),UDim2.new(.5,-56,1,-164)")==1
    assert text.count("UDim2.fromOffset(115,62),UDim2.new(1,-265,1,-185)")==1
    assert "SevenJobsPvEAbility" in text
    assert 'action("JOB_SKILL",nil)' in text
    assert 'KeyCode.H' in text
    if not enabled:
        print("P0D_MOBILE_TOUCH_OFF_PRESERVES_ALL61_SOURCES_AND_LOCKS")
        return
    changed=text.replace(ORIGINAL,INSERT,1)
    assert changed.count("local function layoutRelayTouch()")==1
    assert changed.count('relayButton.Position=UDim2.new(0,10,1,-127)')==1
    assert changed.count('relayButton.Position=UDim2.new(.5,-56,1,-164)')==1
    assert changed.count('workspace:GetPropertyChangedSignal("CurrentCamera")')==1
    after=dict(before)
    after[HUD]=changed.encode("utf8")
    assert sorted(k for k in before if after[k]!=before[k])==[HUD]
    assert all(before[k]==after[k] for k in before if k!=HUD)
    newpins={k:gitblob(v) for k,v in after.items()}
    lock["blobs"]=newpins
    lock["rc_touch_layout_private61"]={
        "feature":FEATURE,
        "stage":"ISOLATED_SOURCE_QA_NO_CANONICAL_ADOPTION",
        "only_changed":[HUD],
        "original_other60_byte_identical":True,
        "narrow_viewport_width_max":650,
        "mobile_relay_slot":"x=10..122 px; y=height-185..height-127",
        "wide_relay_slot":"original center layout",
        "engine_Studio":"NOT_TESTED",
        "rollback":"do not run the overlay; exact original 61 scripts/project/locks",
    }
    feature["source_gitblobs"]=newpins
    feature["rc61_touch_layout_private"]=True
    # All predictable input errors rejected before writes.
    (dist/"src"/HUD).write_bytes(after[HUD])
    original_lock.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    feature_lock.write_text(json.dumps(feature,ensure_ascii=False,indent=2)+"\n","utf8")
    assert inventory(dist)==after
    print("P0D_RC61_TOUCH_RELAY_FIX_HUD_ONLY_60_OTHERS_IDENTICAL_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--enabled",choices=("on","off"),required=True)
    args=p.parse_args()
    run(args.dist,args.enabled=="on")
