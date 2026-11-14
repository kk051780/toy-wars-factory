#!/usr/bin/env python3
"""Execute actual server-authored recent-hit ring under native Luau.

Studio live networking and render are *not* exercised by this source test.
"""
import argparse
from pathlib import Path

SOURCE = Path(__file__).with_name("MusouHordeArtSignal.luau")
START = "-- BEGIN_ACTUAL_RECENT_HIT_RING"
END = "-- END_ACTUAL_RECENT_HIT_RING"

def generate(raw: str) -> str:
    if raw.count(START)!=1 or raw.count(END)!=1:
        raise RuntimeError("HISTORY_RUNTIME_SOURCE_NOT_UNIQUE")
    fragment=raw.split(START,1)[1].split("\n",1)[1].split(END,1)[0]
    for term in ("local function appendRecentHit(", "table.insert(list,hit)",
                 "if now-list[i][12]>2.5", "while #list>12"):
        if term not in fragment: raise RuntimeError("HISTORY_RUNTIME_SEAM_DRIFT "+term)
    return fragment + """
local function hit(i,t)
    return {1,1,2,3,4,5,6,false,i,1,1,t}
end
local list={}
for i=1,3 do appendRecentHit(list,hit(i,100+i/100),100+i/100) end
assert(#list==3 and list[1][9]==1 and list[3][9]==3,
       "HISTORY_DROPPED_STARTUP_HITS")
local first=list[1]
appendRecentHit(list,hit(4,100.5),100.5)
assert(#list==4 and list[1]==first,"HISTORY_INVALID_ORDER")
for i=5,20 do appendRecentHit(list,hit(i,100+i/100),100+i/100) end
assert(#list==12 and list[1][9]==9 and list[12][9]==20,
       "HISTORY_WRONG_MAX12_FIFO")
appendRecentHit(list,hit(21,104),104)
assert(#list==1 and list[1][9]==21,
       "HISTORY_RETAINED_STALE_2_5_SEC_CUES")
print("P0D_FB015_REAL_SERVER_RECENT_HISTORY_NATIVE_PASS")
"""

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.write_text(generate(SOURCE.read_text("utf8")),encoding="utf8")

if __name__=="__main__":
    main()
