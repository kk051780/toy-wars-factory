#!/usr/bin/env python3
"""Real assembled HUD static geometry: portrait touch-collision regression.

Uses exact Lua GUI source and button() AnchorPoint=(0,1). In addition,
proves the viewport listener used for rotations exists. This is deliberately
*not* claiming Android/Roblox engine UI execution.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

FORM = re.compile(
    r'button\(gui,\s*"([^"]+)"\s*,.*?'
    r'UDim2\.fromOffset\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*,\s*'
    r'UDim2\.new\(\s*([\d.\-]+)\s*,\s*([\d.\-]+)\s*,'
    r'\s*([\d.\-]+)\s*,\s*([\d.\-]+)\s*\)',
    flags=re.S,
)

def buttons_from_hud(source: str):
    result={}
    starts=list(re.finditer(r'button\(gui,\s*"([^"]+)"',source))
    for i,m in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(source)
        match=FORM.search(source[m.start():end])
        if match is None:continue
        assert match.group(1)==m.group(1)
        name=m.group(1)
        assert name not in result,("DUPLICATE_GUI_BUTTON",name)
        result[name]=(int(match.group(2)),int(match.group(3)),
                      *[float(match.group(k)) for k in range(4,8)])
    return result

def rect(button,screen_w,screen_h):
    size_w,size_h,scale_x,offset_x,scale_y,offset_y=button
    # Explicit existing GUI helper b.AnchorPoint=Vector2(0,1), so UDim2
    # pos is bottom LEFT of each control.
    x=scale_x*screen_w+offset_x
    bottom=scale_y*screen_h+offset_y
    return (x,bottom-size_h,x+size_w,bottom)

def intersects(a,b):
    return max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3])

def audit(path):
    text=path.read_text("utf8")
    assert text.count("b.AnchorPoint = Vector2.new(0, 1)")==1
    assert text.count("local function layoutRelayTouch()")==1,"MISSING_RESPONSIVE_RELAY_LAYOUT"
    assert text.count("local function bindRelayViewport()")==1
    assert text.count('workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(bindRelayViewport)')==1
    assert text.count('camera:GetPropertyChangedSignal("ViewportSize"):Connect(layoutRelayTouch)')==1
    assert text.count("if viewWidth<=650 then")==1
    assert text.count('relayButton.Position=UDim2.new(0,10,1,-127)')==1
    assert text.count('relayButton.Position=UDim2.new(.5,-56,1,-164)')==1
    assert text.count('relayButton.MouseButton1Click:Connect(fireClassicEggRelay)')==1
    assert text.count('action("JOB_SKILL",nil)')>=1
    assert text.count("KeyCode.H")==1
    buttons=buttons_from_hud(text)
    needed=("ClassicEggRelay","BreakOrRescue","ShortCaptureNet",
            "SevenJobsMenu","SevenJobsPvEAbility","SummonRealScout",
            "Attack","EarnedAwakening","GuardianTrap","RaiderWind",
            "RaiderRole","GuardianRole","OwnedBeastEvolution")
    assert all(n in buttons for n in needed),("HUD_BUTTON_MISSING",sorted(set(needed)-set(buttons)))
    # Reproduce actual source's pre-fix bug as a deterministic regression.
    assert intersects(rect(buttons["ClassicEggRelay"],393,851),
                      rect(buttons["BreakOrRescue"],393,851)), "ORIGINAL_DEFECT_MISSING"
    assert intersects(rect(buttons["ClassicEggRelay"],375,812),
                      rect(buttons["ShortCaptureNet"],375,812)), "SECOND_ORIGINAL_DEFECT_MISSING"
    screens=((320,568),(360,740),(375,812),(393,851),(414,896),
             (600,960),(650,960),(651,960),(800,360),(851,393),
             (1024,768),(1366,768))
    checked=0
    for width,height in screens:
        current=dict(buttons)
        if width<=650:
            # Exactly matches the real source's camera-viewport layout branch.
            current["ClassicEggRelay"]=(112,58,0.0,10.0,1.0,-127.0)
        relay=rect(current["ClassicEggRelay"],width,height)
        assert relay[0]>=0 and relay[1]>=0 and relay[2]<=width and relay[3]<=height,("RELAY_OFFSCREEN",width,height,relay)
        for other in needed:
            if other=="ClassicEggRelay":continue
            box=rect(current[other],width,height)
            assert not intersects(relay,box),("MOBILE_TOUCH_OVERLAP",width,height,other,relay,box)
            checked+=1
        print("P0D_MOBILE_RELAY_TOUCH_NO_OVERLAP",width,height,relay)
    assert checked==len(screens)*(len(needed)-1)
    print("P0D_RC62_MOBILE_RELAY_TOUCH_12_VIEWPORTS_NO_OVERLAP_PASS",checked)
    print("P0D_RC62_MOBILE_ROTATION_EVENT_LISTENER_SOURCE_PRESENT_PASS")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--hud",required=True,type=Path)
    args=parser.parse_args()
    audit(args.hud)
