#!/usr/bin/env python3
"""Generate actual-Luau native square-overlap tests for REAL63 selected HUD."""
import argparse
from pathlib import Path

TEST = r'''
local H=(function()
__SOURCE__
end)()
local function rect(x,y,w,h) return {x=x,y=y,w=w,h=h} end
local function hit(a,b)
 return a.x < b.x+b.w and b.x < a.x+a.w
   and a.y < b.y+b.h and b.y < a.y+a.h
end
local function square(p)
 return rect(p.x-p.size/2,p.y-p.size/2,p.size,p.size)
end
for _,shape in ipairs({{320,260},{393,851},{375,667},{600,300},{851,393},{1280,720},{1024,768}}) do
 for _,hand in ipairs({"RIGHT","LEFT"}) do
  local w,h=shape[1],shape[2]
  local data=H.layout(w,h,hand)
  local p=data.anchors
  local names={"ATTACK","JUMP","DODGE","INVUL","MUSOU","ITEM","SKILL","CONTEXT","MOVE","MAP"}
  for i=1,#names do
   local a=square(p[names[i]])
   assert(a.x>=0 and a.y>=0 and a.x+a.w<=w and a.y+a.h<=h,
      "RED_OUT_OF_SCREEN_"..names[i])
   for j=i+1,#names do
    assert(not hit(a,square(p[names[j]])),
      "RED_SQUARE_OVERLAP_"..names[i].."_"..names[j].."_"..w.."x"..h.."_"..hand)
   end
  end
  local status=data.chrome.status
  local area=rect(status.x,status.y,status.w,status.h)
  assert(not hit(area,square(p.MAP)),"RED_STATUS_OVER_MAP")
  assert(not hit(area,square(p.ITEM)),"RED_STATUS_OVER_ITEM")
  assert(not hit(area,square(p.SKILL)),"RED_STATUS_OVER_SKILL")
  local bar=data.chrome.musouBar
  assert(not hit(area,rect(bar.x,bar.y,bar.w,bar.h)),
    "RED_BAR_OVER_STATUS")
 end
end
print("GQ8_REAL63_UI_SQUARE_COLLISIONS_14_CASES_PASS")
'''

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    policy=a.sources/"EGGRUMBLE_HudPresentationPolicy.luau"
    hud=a.sources/"EGGRUMBLE_HudIntelRuntime.client.luau"
    assert policy.is_file() and hud.is_file(),"RED_REAL63_SELECTED_HUD_MISSING"
    p=policy.read_text(encoding="utf8")
    h=hud.read_text(encoding="utf8")
    # Test exact selected physical source, not the unselected historical author file.
    assert "local menuY = math.max(62, math.min(133, h * .18))" in p
    assert 'MUSOU = at(x - 55, h - 35, 46, "無双")' in p
    for anchor in (
        "local selecting=drawer.Visible",
        "actions.ATTACK.Visible=actions.ATTACK.Visible and inMatch and not selecting",
        "actions.DODGE.Visible=actions.DODGE.Visible and inMatch and not selecting",
        "actions.INVUL.Visible=inMatch and not drawer.Visible",
        "actions.MUSOU.Visible=inMatch and not drawer.Visible",
        "local moveTop=p.MOVE.y-p.MOVE.size/2",
        'hand=="LEFT" and (w-mw-9) or 9',
        "choices[i].Size=UDim2.new(1,-12,0,31)",
        "choices[i].Position=UDim2.fromOffset(6,5+(i-1)*33)",
    ):
        assert anchor in h,("RED_REAL63_RUNTIME_LAYOUT_GATE",anchor)
    assert "remote:FireServer(" not in h,"RED_FAKE_CLIENT_DAMAGE_AUTHORITY"
    a.out.write_text(TEST.replace("__SOURCE__",p),encoding="utf8")
    print("GQ8_REAL63_SELECTED_SOURCE_MODAL_LAYOUT_PROOFS_PASS")

if __name__=="__main__":
    main()
