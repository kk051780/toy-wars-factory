#!/usr/bin/env python3
"""Source-exact OFF/ON overlay for existing #487 ResultService. Original authors untouched."""
import argparse
import hashlib
from pathlib import Path

AUTHOR_PATH = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_MatchResultService.luau")
AUTHOR_BLOB = "b5ef844cff98173e3b2499b8aceca099f315adc4"
REQUIRES = 'local ScoreBalance=require(script.Parent:WaitForChild("EGGRUMBLE_ScoreBalance"))\n'
MAKE_HEADER = '''local function makeResultGui(player:Player,title:string,stats:string,won:boolean)
 local container=player:FindFirstChildOfClass("PlayerGui")
 if not container then return end'''
MAKE_HEADER_ON = '''local function makeResultGui(player:Player,title:string,stats:string,won:boolean):boolean
 local container=player:FindFirstChildOfClass("PlayerGui")
 if not container then return false end'''
MAKE_TAIL = ''' task.delay(DISPLAY_SECONDS,function()
  if gui.Parent then gui:Destroy() end
 end)
end

function ResultService.showIfFinished'''
MAKE_TAIL_ON = ''' task.delay(DISPLAY_SECONDS,function()
  if gui.Parent then gui:Destroy() end
 end)
 return true
end

function ResultService.showIfFinished'''
CALL = '    makeResultGui(player,title,stats,won)\n'
CALL_ON = '''    -- Preserve the exact existing SCORE/result payload. Only transient GUI absence retries.
    ResultRetry.deliver(function()
     return player.Parent==Players and player:GetAttribute("EGGRUMBLE_QueuedMode")==mode
      and session.mode==mode and session.rules.phase=="FINISHED" and session.rules.winner~=nil
      and session.world~=nil and session.world.Parent~=nil
    end,function()
     return makeResultGui(player,title,stats,won)
    end,task.delay)
'''

def git_blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def patch(src:bytes, enabled:bool)->bytes:
    if git_blob(src)!=AUTHOR_BLOB:
        raise ValueError("GQ_RESULT_AUTHOR_BLOB_DRIFT")
    if not enabled:
        return src
    text=src.decode("utf-8")
    for old,new,name in [
        (REQUIRES,REQUIRES+'local ResultRetry=require(script.Parent:WaitForChild("EGGRUMBLE_ResultRetry"))\n',"REQUIRE"),
        (MAKE_HEADER,MAKE_HEADER_ON,"GUI_BOOLEANS"),
        (MAKE_TAIL,MAKE_TAIL_ON,"TRUE_ON_PARENT"),
        (CALL,CALL_ON,"ONLY_ONE_DELIVERY_HOOK"),
    ]:
        if text.count(old)!=1:
            raise ValueError(f"GQ_RESULT_STALE_OR_MULTI_{name}:{text.count(old)}")
        text=text.replace(old,new,1)
    assert text.count("ScoreBalance.build(")==1
    assert text.count("session.resultsDelivered=true")==1
    assert text.count("ResultRetry.deliver(")==1
    return text.encode("utf-8")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",action="store_true")
    args=p.parse_args()
    data=patch(AUTHOR_PATH.read_bytes(),args.enabled)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(data)
    print(f"GQ_RESULT_SOURCE_LOCK_PASS enabled={args.enabled} bytes={len(data)}")
