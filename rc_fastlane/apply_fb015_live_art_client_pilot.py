#!/usr/bin/env python3
"""#431 server-authenticated private opt-in for two client-only art sources."""
from __future__ import annotations
import argparse,json,os,shutil,tempfile
from pathlib import Path
from apply_fb015_gorogan_mobile_lod import read,blob
from apply_live_castle_safe import DEST as LIVE_CASTLE, AUTHOR_BLOB as CASTLE_BLOB
BEAST="client/FB015CharacterArt.client.luau"
FX="client/ConfirmedSlashFX.client.luau"
SERVER="server/CastleDetailArt.server.luau"
CLIENTS=(BEAST,FX)
FILES=(BEAST,FX,SERVER)
OLD="if not RunService:IsStudio() then return end"
FLAG="FB015_LIVE_ART_PRIVATE_CLIENT_PILOT_V1"
ATTR="P0D_LIVE_ART_PILOT_SERVER_ALLOWED"
OWNER_OPTIN="P0D_LIVE_ART_PILOT_OPTIN"
SERVER_OLD='local RunService = game:GetService("RunService")\nif not RunService:IsStudio() then return end'
SERVER_NEW='''local RunService = game:GetService("RunService")
-- Server-only authorization: Roblox PrivateServerId is not client-replicated.
-- Only owner-approved private session may signal the two client cosmetics.
if not RunService:IsStudio() then
    if game.PrivateServerId ~= ""
       and workspace:GetAttribute("P0D_LIVE_ART_PILOT_OPTIN") == true then
        workspace:SetAttribute("P0D_LIVE_ART_PILOT_SERVER_ALLOWED", true)
    end
    return
end'''
NEW='''-- FB015_LIVE_ART_PRIVATE_CLIENT_PILOT_V1: private nonStudio cosmetic trial.
-- Server authorizes only private game plus owner opt-in; public stays OFF.
-- Studio visuals remain unchanged. This creates no gameplay/remote authority.
local function allowPrivateLiveArtPilot(): boolean
    if RunService:IsStudio() then return true end
    -- Server authorization can replicate after this LocalScript's first frame.
    -- Bounded polling prevents a late attribute from permanently hiding art.
    for _ = 1, 40 do
        if workspace:GetAttribute("P0D_LIVE_ART_PILOT_SERVER_ALLOWED") == true then
            return true
        end
        task.wait(.2)
    end
    return false
end
if not allowPrivateLiveArtPilot() then return end'''
def patch(data:bytes)->bytes:
    s=data.decode("utf8")
    assert s.count(OLD)==1 and FLAG not in s and ATTR not in s
    assert "game.PrivateServerId" not in s
    out=s.replace(OLD,NEW,1)
    assert out.replace(NEW,OLD,1)==s
    assert "game.PrivateServerId" not in out
    assert out.count('workspace:GetAttribute("'+ATTR+'") == true')==1
    assert out.count('task.wait(.2)')==1
    assert out.count('for _ = 1, 40 do')==1
    return out.encode("utf8")
def patch_server(data:bytes)->bytes:
    s=data.decode("utf8")
    assert s.count(SERVER_OLD)==1 and OWNER_OPTIN not in s and ATTR not in s
    o=s.replace(SERVER_OLD,SERVER_NEW,1)
    assert o.replace(SERVER_NEW,SERVER_OLD,1)==s
    assert o.count('game.PrivateServerId ~= ""')==1
    assert o.count('workspace:GetAttribute("'+OWNER_OPTIN+'") == true')==1
    assert o.count('workspace:SetAttribute("'+ATTR+'", true)')==1
    return o.encode("utf8")
def apply(base:Path,out:Path,enabled:bool)->bool:
    assert not out.exists()
    if not enabled:
        print("P0_431_DISABLED_ZERO_WRITE");return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.is_relative_to(base)
    before=read(base)
    assert len(before)==81 and all(p in before for p in FILES) and LIVE_CASTLE in before
    pins={p:blob(v) for p,v in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text())
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text())
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==pins,"SOURCE_PIN_DRIFT"
    for flag in ("FB015_FOREST_BIOMES_MONUMENTS_V2",
                 "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
                 "FB016_ART_CAMERA_SIGHTLINE_V2",
                 "FB015_GOROGAN_MOBILE_LOD_V1",
                 "FB015_LIVE_CASTLE_SAFE_PARITY_V1"):
        assert fl["feature_flags"].get(flag) is True,("MISSING_PARENT",flag)
    assert FLAG not in fl["feature_flags"]
    assert pins[FX]=="4b1dce5635b709d349ab3f00bba7a7cf9d9883bd"
    assert pins[LIVE_CASTLE]==CASTLE_BLOB,"OFFICIAL_RC81_CASTLE_DRIFT"
    assert fl["fb015_castle_v3"]["new_blob"]==pins[SERVER]
    assert fl["fb015_beast_mobile_lod"]["new_git_blob"]==pins[BEAST]
    assert fl["fb015_beast_mobile_lod"]["old_git_blob"]=="2ff10db1a4171be9abdc276a43dd21b2401da2d8"
    assert b"MAX_ACTIVE_PARTS = 48" in before[FX]
    assert b"FB015_GOROGAN_MOBILE_LOD_V1" in before[BEAST]
    after=dict(before)
    for p in CLIENTS:after[p]=patch(after[p])
    after[SERVER]=patch_server(before[SERVER])
    assert {p for p in before if before[p]!=after[p]}==set(FILES)
    newpins={p:blob(b) for p,b in sorted(after.items())}
    meta={
      "feature":FLAG,"status":"PRIVATE_ONLY_SOURCE_QA",
      "changed":list(FILES),"unchanged_sources":78,"sources":81,
      "public_nonstudio":"OFF","private_without_optin":"OFF",
      "private_with_optin":"SOURCE_INTENDED_ON_NOT_RUNTIME_TESTED",
      "owner_accepted":False,"official_adopted":False,
      "studio_pc":"NOT_TESTED","android15":"NOT_TESTED","child3":"NOT_TESTED",
      "live_art":"LIVE_ART_NO_GO","art":"ART_NO_GO",
      "rollback":"omit patch; original Rojo is unchanged",
      "old_blobs":{p:pins[p] for p in FILES},
      "new_blobs":{p:newpins[p] for p in FILES}
    }
    sl["blobs"]=newpins;fl["source_gitblobs"]=newpins
    sl["p0_431_client_pilot"]=meta;fl["p0_431_client_pilot"]=meta
    fl["feature_flags"][FLAG]=True
    temp=Path(tempfile.mkdtemp(prefix=".p0_431_",dir=str(out.parent)))
    stage=temp/"dist"
    try:
        shutil.copytree(base,stage,symlinks=False)
        for p in FILES:(stage/"src"/p).write_bytes(after[p])
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n")
        assert read(stage)==after and read(base)==before
        os.replace(stage,out)
    finally:shutil.rmtree(temp,ignore_errors=True)
    print("P0_431_SERVER_AUTHORIZED_CLIENT_ART_RC81_OTHER78_EXACT")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args();apply(a.base,a.out,a.enabled=="true")
