#!/usr/bin/env python3
"""Independent Android touch-control collision QA on the FINAL assembled RC61 HUD.

Does not change any game code or Studio project. Prints actual button rectangles
for typical landscape/portrait sizes. Uses exact GUI button creation arguments
and bottom-left button AnchorPoint=(0,1). Source geometry, NOT engine proof.
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

def get_buttons(source: str):
    # Begin each extraction at a fresh actual button call; no cross-item
    # matching if another button call appears before the size and pos.
    buttons={}
    starts=list(re.finditer(r'button\(gui,\s*"([^"]+)"',source))
    for i,m in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(source)
        block=source[m.start():end]
        n=FORM.search(block)
        if not n:
            continue
        assert n.group(1)==m.group(1)
        assert n.group(1) not in buttons,("DUPLICATE_TOUCH_BUTTON",n.group(1))
        buttons[n.group(1)]={
            "size":(int(n.group(2)),int(n.group(3))),
            "pos":tuple(float(n.group(j)) for j in range(4,8)),
            "source":block[:350].replace("\n"," "),
        }
    return buttons

def box(a,width,height):
    sx,sy=a["size"]
    fx,ox,fy,oy=a["pos"]
    # Original GUI function uses AnchorPoint Vector2(0,1), meaning
    # Position is the BOTTOM-LEFT corner of each button.
    x=fx*width+ox
    bottom=fy*height+oy
    return (x,bottom-sy,x+sx,bottom)

def intersect(a,b):
    return (max(a[0],b[0]) < min(a[2],b[2])
            and max(a[1],b[1]) < min(a[3],b[3]))

def audit(path):
    s=path.read_text("utf8")
    assert s.count('b.AnchorPoint = Vector2.new(0, 1)')==1
    for term in ('"ClassicEggRelay"','"BreakOrRescue"','"ShortCaptureNet"',
                 'action("JOB_SKILL",nil)', 'EGG_RELAY','KeyCode.H'):
        assert term in s,("MISSING_FINAL61_UI_COMPONENT",term)
    buttons=get_buttons(s)
    for name in ("ClassicEggRelay","BreakOrRescue","ShortCaptureNet"):
        assert name in buttons,("UNPARSEABLE_TOUCH_BUTTON",name)
    print("P0D_FINAL61_HUD_BUTTON_SLOT_COUNT",len(buttons))
    for name in sorted(buttons):
        print("P0D_FINAL61_TOUCH_SLOT",name,buttons[name]["size"],buttons[name]["pos"])
    hits=[]
    for width,height in ((393,851),(600,960),(851,393),(375,812)):
        relay=box(buttons["ClassicEggRelay"],width,height)
        rescue=box(buttons["BreakOrRescue"],width,height)
        net=box(buttons["ShortCaptureNet"],width,height)
        overlap=intersect(relay,rescue)
        hits.append((width,height,overlap))
        print("P0D_FINAL61_TOUCH_RELAY_RESCUE_OVERLAP",width,height,overlap)
        print("P0D_FINAL61_TOUCH_RELAY_NET_OVERLAP",width,height,intersect(relay,net))
        print("P0D_FINAL61_RELAY_RECT",width,height,relay)
        print("P0D_FINAL61_RESCUE_RECT",width,height,rescue)
    # First diagnostic pass establishes source-level evidence of the current
    # portrait-screen problem without applying speculative UI modifications.
    assert any(x[2] for x in hits), "NO_COLLISION_REPRODUCED_CHECK_ANCHOR"
    assert hits[2][2] is False,"LANDSCAPE_SHOULD_NOT_OVERLAP"
    print("P0D_FINAL61_TOUCH_PORTRAIT_OVERLAP_REPRODUCED")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--hud",required=True,type=Path)
    a=p.parse_args()
    audit(a.hud)
