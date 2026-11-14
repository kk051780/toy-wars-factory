#!/usr/bin/env python3
"""P0 #444: complete existing *official* private Horde source-only combat lifecycle.

Parent is the official RC81 with server-private Horde reset already source-staged
by sole B writer. Patch only original Game ATTACK + Horde 0.5s tick; never patch
reset a second time. Keep Studio-only SoloTeamBots tick in Studio.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path

GAME="server/Game.server.luau"
HORDE="server/MusouHorde.luau"
GAME_OFFICIAL_BLOB="77738212e5c9dd3d75b0d3e750ca5ba5584ab95b"
HORDE_OFFICIAL_BLOB="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
PARENT="0287c696bd2467177236c46a1b2b39646d5aa2b9"
PARENT_FEATURE="P0D_PRIVATE_LIVE_HORDE_NINE_V1"
FEATURE="P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2"
PRIVATE_ATTR="P0D_PRIVATE_LIVE_HORDE_NINE"
RESET_AUTH=('if RunService:IsStudio() or (game.PrivateServerId ~= "" '
    'and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true) '
    'then horde:reset(match.serial,serverNow()) end')
HIT_OLD=('    -- Original ATTACK cooldown/seq/phase also gates PvE. No second Remote or damage event.\n'
         '    if RunService:IsStudio() then\n')
HIT_NEW=('    -- Original ATTACK cooldown/seq/phase also gates PvE. No second Remote or damage event.\n'
         '    if RunService:IsStudio() or (game.PrivateServerId ~= "" '
         'and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true) then\n')
TICK_OLD=('    -- Existing server tick is the sole PvE attack authority; no extra game loop.\n'
          '    if RunService:IsStudio() and match.phase=="ACTIVE" then\n')
TICK_NEW=('    -- Existing server tick is the sole PvE attack authority; no extra game loop.\n'
          '    if (RunService:IsStudio() or (game.PrivateServerId ~= "" '
          'and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true)) '
          'and match.phase=="ACTIVE" then\n')
BOT_OLD=('        -- The same ORIGINAL Game tick drives Studio bots. No second match loop.\n'
         '        if not EXPERIMENTAL_FIVE_EGG_MODE then\n')
BOT_NEW=('        -- The same ORIGINAL Game tick drives Studio bots. No second match loop.\n'
         '        if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then\n')

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("SOURCE_LINK_REFUSED",p)
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def one(text:str,old:str,new:str)->str:
    assert text.count(old)==1,("STUDIO_HORDE_AUTHOR_ANCHOR_DRIFT",old[:90],text.count(old))
    return text.replace(old,new,1)

def patch(raw:bytes)->bytes:
    assert blob(raw)==GAME_OFFICIAL_BLOB,("PARENT_GAME_SHA_CHANGED",blob(raw))
    g=raw.decode("utf8")
    assert g.count(RESET_AUTH)==1,"B_PRIVATE_HORDE_RESET_MUST_ALREADY_BE_ADOPTED"
    assert g.count("horde:reset(")==1 and g.count("remote.OnServerEvent:Connect(")==1
    assert g.count('local touched,defeated = horde:hit(')==1
    assert g.count('horde:tick(now,Players:GetPlayers(),healthy)')==1
    assert "local startupSerial=match.serial" in g
    assert 'if match.phase~="ACTIVE" or match.serial~=startupSerial then return end' in g
    assert FEATURE not in g
    g=one(g,HIT_OLD,HIT_NEW)
    g=one(g,TICK_OLD,TICK_NEW)
    g=one(g,BOT_OLD,BOT_NEW)
    assert g.count(RESET_AUTH)==1,"SINGLE_ORIGINAL_RESET_CHANGED"
    assert g.count(HIT_NEW)==1 and g.count(TICK_NEW)==1 and g.count(BOT_NEW)==1
    assert g.count("horde:reset(")==1 and g.count('horde:tick(')==1
    assert g.count("remote.OnServerEvent:Connect(")==1
    assert g.count('game.PrivateServerId ~= ""')==3
    assert g.count('workspace:GetAttribute("'+PRIVATE_ATTR+'") == true')==3
    assert 'workspace:SetAttribute("'+PRIVATE_ATTR not in g
    return g.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    assert not out.exists(),"OUTPUT_ALREADY_EXISTS"
    if not enabled:
        print("P0D_HORDE_LIFECYCLE_V2_OFF_ZERO_WRITE")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and not base.is_symlink() and out.parent.is_dir()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==81 and GAME in before and HORDE in before
    pins={p:blob(v) for p,v in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==pins,"OFFICIAL_SOURCE_LOCK_DRIFT"
    assert pins[GAME]==GAME_OFFICIAL_BLOB and pins[HORDE]==HORDE_OFFICIAL_BLOB
    assert fl["feature_flags"].get(PARENT_FEATURE) is True,"B_RESET_MUST_ALREADY_EXIST"
    assert not fl["feature_flags"].get(FEATURE,False)
    horde=before[HORDE].decode("utf8")
    for a in ("local MINIONS = 8","local MAX_ACTIVE = 9",
              "for i=1,MAX_ACTIVE do","function Horde:reset(",
              "function Horde:hit(","function Horde:tick(",
              "RealDamagePopup","if self.round<0 then return 0,0 end"):
        assert a in horde,("HORDE_NINE_AUTHOR_PIN_DRIFT",a)
    after=dict(before);after[GAME]=patch(before[GAME])
    assert len(after)==81 and {k for k in before if before[k]!=after[k]}=={GAME}
    newpins={p:blob(v) for p,v in sorted(after.items())}
    receipt={
      "schema":"P0D_HORDE_PRIVATE_ATTACK_TICK_SOURCE_V2",
      "official_parent":PARENT,"feature":FEATURE,"source_count":81,
      "original_reset_from_B_unchanged":True,
      "changed_source":[GAME],"other80_byte_identical":True,
      "original_horde_gitblob":HORDE_OFFICIAL_BLOB,"game_before":GAME_OFFICIAL_BLOB,
      "game_after":newpins[GAME],"private_server_and_owner_attr_required":True,
      "private_attr":PRIVATE_ATTR,"public_default":"OFF",
      "studio_bot_tick_stays_studio_only":True,
      "game_authority_count":1,"remote_authority_count":1,
      "real_neutral9":"NOT_TESTED","real_hit_hp_popup":"NOT_TESTED",
      "live_horde_decision":"LIVE_HORDE_NO_GO",
      "art_decision":"ART_NO_GO","mobile_decision":"MOBILE_NO_GO",
      "fun_decision":"FUN_NO_GO","owner_accepted":False,"official_rc_adopted":False,
      "rollback":"omit only V2 source overlay; B official Game reset canary retained"}
    sl["blobs"]=newpins;fl["source_gitblobs"]=newpins
    sl["live_horde_attack_tick_v2"]=fl["live_horde_attack_tick_v2"]=receipt
    fl["feature_flags"][FEATURE]=True
    scratch=Path(tempfile.mkdtemp(prefix=".p0d_horde_attacktick_",dir=str(out.parent)))
    stage=scratch/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(after[GAME])
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after and read(base)==before
        os.replace(stage,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("P0D_ISSUE444_LIFECYCLE_GAME_ONLY81_OTHER80_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args();apply(a.base,a.out,a.enabled=="true")
