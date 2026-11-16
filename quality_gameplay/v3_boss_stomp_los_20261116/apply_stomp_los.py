#!/usr/bin/env python3
"""Source-select ONE server-side sight check onto #482 original boss; no boss fork."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

AUTHOR_SHA = "2670618cba320c51936c750a10e43c194cada0f0"
AUTHOR_COMMIT = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
HELPER_ANCHOR = "function Boss.spawn(parent:Instance,at:Vector3,options:any?):any\n"
HIT_ANCHOR = (
    "     if d<=11 and math.abs(root.Position.Y-at.Y)<=8 then\n"
    "      -- Server-side radial attack only, no client-trusted damage remotes.\n"
    "      h:TakeDamage(28)\n"
    "     end\n"
)
HELPER = """-- GQ_BOSS_STOMP_LOS_BEGIN: a solid castle gate/wall blocks outgoing boss shockwave.
local function stompVisible(model:Model,center:Vector3,character:Model,root:BasePart):boolean
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={model,character}
 params.RespectCanCollide=true
 local origin=center+Vector3.new(0,3,0)
 local target=root.Position+Vector3.new(0,1,0)
 local delta=target-origin
 if delta.Magnitude<=.01 then return true end
 return workspace:Raycast(origin,delta,params)==nil
end
-- GQ_BOSS_STOMP_LOS_END
"""
HIT_PATCH = HIT_ANCHOR.replace(
    "if d<=11 and math.abs(root.Position.Y-at.Y)<=8 then",
    "if d<=11 and math.abs(root.Position.Y-at.Y)<=8 and stompVisible(model,at,c,root) then",
)


def blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\\0"+raw).hexdigest()


def patch(raw:str)->str:
    assert raw.count(HELPER_ANCHOR)==1, "original boss spawn moved; source drift"
    assert raw.count(HIT_ANCHOR)==1, "stomp attack moved; source drift"
    assert "stompVisible" not in raw, "already patched: do not duplicate"
    assert raw.count("h:TakeDamage(28)")==1, "multiple boss stomp authorities"
    assert 'if not active or not sessionActive() or cooldown then continue end' in raw
    result=raw.replace(HELPER_ANCHOR,HELPER+HELPER_ANCHOR,1)
    result=result.replace(HIT_ANCHOR,HIT_PATCH,1)
    assert result.replace(HELPER,"",1).replace(HIT_PATCH,HIT_ANCHOR,1)==raw
    return result


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    original=args.source.read_bytes()
    assert blob_sha(original)==AUTHOR_SHA, "must explicitly review new original #482 blob"
    assert args.source.resolve()!=args.out.resolve(), "author original must remain byte identical"
    patched=patch(original.decode("utf-8"))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(patched,encoding="utf-8")
    assert args.out.name=="EGGRUMBLE_NeutralStoneGiant.luau"
    print("BOSS_STOMP_ONLY_AUTHOR_OVERLAY_PASS",hashlib.sha256(patched.encode()).hexdigest())


if __name__=="__main__":
    main()
