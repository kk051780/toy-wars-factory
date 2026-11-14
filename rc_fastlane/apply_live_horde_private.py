#!/usr/bin/env python3
"""#444 private-only live Horde initializer, source-locked official RC81 -> RC81.

Replaces ONLY the unique round-start Studio guard around the original
horde:reset(match.serial,serverNow()) call inside the existing Game.
Studio behavior remains identical; public non-Studio defaults OFF.
No new Game, Horde, Remote, HP, hit, score, or spawn authority is introduced.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,tempfile
from pathlib import Path

GAME="server/Game.server.luau"
HORDE="server/MusouHorde.luau"
FEATURE="P0D_PRIVATE_LIVE_HORDE_RESET_V1"
PRIVATE_ATTR="P0D_PRIVATE_LIVE_HORDE"
PARENT="bab8e93bfe0bce0baddfe64ee2898962486058af"
RE_1=re.compile(
    r'(?P<indent>^[ \t]*)if[ \t]+RunService:IsStudio\(\)[ \t]+then[ \t]+'
    r'horde:reset\(match\.serial,[ \t]*serverNow\(\)\)[ \t]+end[ \t]*$',
    re.MULTILINE
)
RE_2=re.compile(
    r'(?P<indent>^[ \t]*)if[ \t]+RunService:IsStudio\(\)[ \t]+then[ \t]*\n'
    r'[ \t]+horde:reset\(match\.serial,[ \t]*serverNow\(\)\)[ \t]*\n'
    r'(?P=indent)end[ \t]*$',re.MULTILINE
)

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink(), "MISSING_SOURCE_DIST"
    for path in root.rglob("*"):
        assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),(
            "SOURCE_LINK_REFUSED",path)
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def parse_guard(source:str)->tuple[str,str,str,str]:
    assert source.count("local function resetRound()")==1
    assert source.count("local function chooseTeam(")==1
    assert source.count("horde:reset(")==1, "SINGLE_HORDE_RESET_REQUIRED"
    assert source.count("local startupSerial=match.serial")==1
    assert 'if match.phase~="ACTIVE" or match.serial~=startupSerial then return end' in source
    first,rest=source.split("local function resetRound()",1)
    assert "local function chooseTeam(" in rest
    body,tail=rest.split("local function chooseTeam(",1)
    found=[]
    for pattern in (RE_1,RE_2):
        found.extend(list(pattern.finditer(body)))
    assert len(found)==1,("PRIVATE_HORDE_RESET_STUDIO_ANCHOR_DRIFT",len(found))
    m=found[0]
    return first,body,tail,m.group(0)

def patch(source:bytes)->bytes:
    raw=source.decode("utf8")
    assert FEATURE not in raw and PRIVATE_ATTR not in raw,"DOUBLE_ADOPTION"
    assert raw.count("remote.OnServerEvent:Connect(")==1,"GAME_AUTHORITY_DRIFT"
    assert "local touched,defeated = horde:hit(" in raw
    assert "FB019" in raw and "RealDamagePopup" in raw
    before,reset,after,old=parse_guard(raw)
    indentation=old[:len(old)-len(old.lstrip())]
    new=(
      indentation+"-- "+FEATURE+": identical Studio path, private server opt-in only.\n"
      + indentation+"-- Only original Game owns Horde reset; no client or public enable.\n"
      + indentation+"if RunService:IsStudio() or (\n"
      + indentation+'    game.PrivateServerId ~= "" and\n'
      + indentation+'    workspace:GetAttribute("'+PRIVATE_ATTR+'") == true\n'
      + indentation+") then\n"
      + indentation+"    horde:reset(match.serial,serverNow())\n"
      + indentation+"end"
    )
    assert reset.count(old)==1
    result=before+"local function resetRound()"+reset.replace(old,new,1)+"local function chooseTeam("+after
    assert result.count("horde:reset(")==1
    assert result.count("remote.OnServerEvent:Connect(")==1
    assert result.count('game.PrivateServerId ~= ""')==1
    assert result.count('workspace:GetAttribute("'+PRIVATE_ATTR+'") == true')==1
    assert len(result)>len(raw)
    return result.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_ZERO_WRITE_REQUIRED"
        print("P0D_LIVE_HORDE_OFF_ZERO_WRITE")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and not base.is_symlink()
    assert out.parent.is_dir() and not out.parent.is_symlink() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==81 and GAME in before and HORDE in before
    orig={p:blob(v) for p,v in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==orig,"OFFICIAL_PARENT_SOURCE_LOCK_DRIFT"
    assert not fl["feature_flags"].get(FEATURE,False)
    for flag in ("FB019_RESPONSIVE_ATTACK_INPUT_SWING",
                 "FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2",
                 "FB015_LIVE_CASTLE_SAFE_PARITY_V1"):
        assert fl["feature_flags"].get(flag) is True,("REQUIRED_81_SOURCE_FEATURE_MISSING",flag)
    horde=before[HORDE].decode("utf8")
    assert "function Horde:reset(" in horde or "function MusouHorde:reset(" in horde, "NO_REAL_HORDE_RESET"
    assert "RealDamagePopup" in horde and "MUSOU_ELITE_TELEGRAPH" in horde
    changed=patch(before[GAME])
    after={**before,GAME:changed}
    assert len(after)==81 and {k for k in before if before[k]!=after[k]}=={GAME}
    pins={p:blob(v) for p,v in sorted(after.items())}
    receipt={
       "schema":"P0D_PRIVATE_LIVE_HORDE_RESET_SOURCE_STAGE_V1",
       "parent_official":PARENT,"feature":FEATURE,"source_count":81,
       "modified_sources":[GAME],"other_80_sources_exact":True,
       "original_game_authority_only":True,"original_horde_source_unchanged":True,
       "old_game_sha":orig[GAME],"new_game_sha":pins[GAME],
       "nonstudio_private_server_id_required":True,
       "nonstudio_server_attribute":PRIVATE_ATTR,"public_default":"OFF",
       "studio_behaviour":"UNCHANGED_SOURCE_ONLY",
       "9_mobs_runtime":"NOT_TESTED","attack_hp_runtime":"NOT_TESTED",
       "source_gate":"PENDING_CI",
       "live_horde_decision":"LIVE_HORDE_NO_GO",
       "art_decision":"ART_NO_GO","mobile_decision":"MOBILE_NO_GO",
       "fun_decision":"FUN_NO_GO","owner_accepted":False,
       "official_rc_adopted":False,
       "rollback":"disable feature, omit Game patch; original official RC81 exact"}
    sl["blobs"]=pins
    fl["source_gitblobs"]=pins
    sl["live_horde_private_canary"]=receipt
    fl["live_horde_private_canary"]=receipt
    fl["feature_flags"][FEATURE]=True
    scratch=Path(tempfile.mkdtemp(prefix=".p0d_live_horde_",dir=str(out.parent)))
    stage=scratch/"src"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(changed)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after and read(base)==before
        os.replace(stage,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("P0D_PRIVATE_HORDE_RC81_GAME_ONLY_SOURCE_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args();apply(a.base,a.out,a.enabled=="true")
