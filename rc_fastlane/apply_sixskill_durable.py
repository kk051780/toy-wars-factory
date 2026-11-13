#!/usr/bin/env python3
"""P0D V5: source-locked same-key durable six-skill overlay for ONE canonical RC.

This invokes authored minimal patches against the existing Game/Store and
read-only V4 HUD; it adds exactly ONE pure policy module, not a new writer.
All changes are restricted to the unpublished Studio DEV key. No paid/live writes.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE_ROOT = ROOT / "features" / "sixskill"
PINNED = {
    "patches/Game.patch": "5c80b0e3d265fccfc8914b1a0d16cc6418f24d09",
    "patches/PersistentHatchStore.patch": "5b06b6009f223c6054d9973bedc3f1ac24f2864d",
    "SixSkillAtomicProfile.luau": "aeadd5a8e0d367ddfa639df161843f9a74637c87",
}
FILES = ("server/Game.server.luau", "server/PersistentHatchStore.luau",
         "client/V4TrialOverlay.client.luau")
def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
def all_source(dist: Path) -> dict[str, bytes]:
    return {p.relative_to(dist/"src").as_posix():p.read_bytes()
            for p in (dist/"src").rglob("*.luau")}
def exact_replace(text: str, old: str, new: str) -> str:
    assert text.count(old)==1, ("MISSING_OR_DUPLICATE_CONTEXT", old)
    return text.replace(old,new,1)
def patch_file(dist: Path, name: str, original: str, target: str):
    raw=(FEATURE_ROOT/"patches"/name).read_text("utf8")
    assert raw.startswith("--- original/"+original+"\n+++ proposed/"+original+"\n"),name
    rewritten=raw.replace("--- original/"+original+"\n","--- "+target+"\n",1)
    rewritten=rewritten.replace("+++ proposed/"+original+"\n","+++ "+target+"\n",1)
    opts=["patch","-p0","--fuzz=0","--batch","--forward","--reject-file=-",
          "-d",str(dist/"src")]
    for args in (opts+["--dry-run"],opts):
        test=subprocess.run(args,input=rewritten,text=True,capture_output=True)
        assert test.returncode==0,("AUTHOR_PATCH_REJECTED",name,args[-1],test.stdout[-900:],test.stderr[-900:])
def patch_hud(text: str) -> str:
    # Author's V4 new status UI, carefully grafted onto the accepted idle-warning
    # overlay; preserve its event hooks instead of overwriting new safety fixes.
    text=exact_replace(text,'title.Text="6系統 修行（体験版）"',
        'title.Text="6系統 修行（保存検証）"')
    text=exact_replace(text,'footer.Text="保存なし / 対戦強化なし / 課金なし"',
        'footer.Text="DEV保存確認待ち / 対戦強化なし"')
    text=exact_replace(text,'local baseWarning="保存なし / 対戦強化なし / 課金なし"',
        'local baseWarning="DEV保存状態確認中 / 対戦強化なし"')
    text=exact_replace(text,'footer.Text="⚠ 間もなく自動切断・修行XPは保存なし"',
        'footer.Text="⚠ まもなく自動切断・保存状況を確認"')
    text=exact_replace(text,'footer.Text="⚠ 約20分無操作で切断・保存なし"',
        'footer.Text="⚠ 約20分の無操作で切断・保存状況を確認"')
    text=exact_replace(text,"local function render()\n    local active=",
        'local function render()\n'
        '    local saved=player:GetAttribute("P0D_V4_SaveStatus")=="SAVED"\n'
        '    local saveState=tostring(player:GetAttribute("P0D_V4_SaveStatus") or "LOCAL_ONLY")\n'
        '    baseWarning=if saved then "DEV保存確認済 / 対戦強化なし"\n'
        '        else "保存状況:"..saveState.." / 体験XP"\n'
        '    footer.Text=baseWarning\n'
        '    local active=')
    text=exact_replace(text,'local mode=player:GetAttribute("P0D_V4_Mode")',
        'local mode=player:GetAttribute(if saved then "P0D_V4_SavedMode" else "P0D_V4_Mode")')
    text=exact_replace(text,'local left=tonumber(player:GetAttribute("P0D_V4_Remaining")) or 1800',
        'local left=tonumber(player:GetAttribute(if saved then "P0D_V4_SavedRemaining" else "P0D_V4_Remaining")) or 1800')
    text=exact_replace(text,'local current=player:GetAttribute("P0D_V4_Current") or "-"',
        'local current=player:GetAttribute(if saved then "P0D_V4_SavedSkill" else "P0D_V4_Current") or "-"')
    text=exact_replace(text,'local lv=tonumber(player:GetAttribute("P0D_V4_"..skill.."_LV")) or 1',
        'local prefix=if saved then "P0D_V4_SAVED_" else "P0D_V4_"\n'
        '        local lv=tonumber(player:GetAttribute(prefix..skill.."_LV")) or 1')
    text=exact_replace(text,'local xp=tonumber(player:GetAttribute("P0D_V4_"..skill.."_XP")) or 0',
        'local xp=tonumber(player:GetAttribute(prefix..skill.."_XP")) or 0')
    text=exact_replace(text,'local nextXP=tonumber(player:GetAttribute("P0D_V4_"..skill.."_NEXT")) or 100',
        'local nextXP=tonumber(player:GetAttribute(prefix..skill.."_NEXT")) or 100')
    assert 'player.Idled:Connect(' in text
    assert 'UserInputService.InputBegan:Connect(' in text
    assert text.count('local function render()')==1
    return text
def integrate(dist: Path, profile: str) -> bool:
    if profile!="rich51":
        print("P0D_DURABLE_NOT_IN_FALLBACK_PROFILE",profile)
        return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))
    item=flags["features"]["SIX_SKILL_DURABLE"]
    assert item["rollback"]=="DISABLE_54_TO_53"
    assert type(item["enabled"]) is bool
    if not item["enabled"]:
        print("P0D_DURABLE_SWITCH_OFF_KEEP_RICH53")
        return False
    for path,sha in PINNED.items():
        assert blob((FEATURE_ROOT/path).read_bytes())==sha,("SOURCE_LOCK_DRIFT",path)
    before=all_source(dist)
    assert len(before)==53,("BASE_NOT_53",len(before))
    assert all(k in before for k in FILES)
    assert "server/SixSkillAtomicProfile.luau" not in before
    lockpath=dist/"SOURCE_LOCK.json"
    lock=json.loads(lockpath.read_text("utf8"))
    assert lock["total_scripts"]==53
    assert lock["blobs"]=={k:blob(v) for k,v in before.items()},"NOT_BYTE_EXACT_CURRENT_53"
    # Both are authored and pretested with the exact baseline source. Zero fuzz,
    # missing contexts or any alias/schema drift fail the entire RC build.
    patch_file(dist,"Game.patch","Game.luau","server/Game.server.luau")
    patch_file(dist,"PersistentHatchStore.patch","PersistentHatchStore.luau",
               "server/PersistentHatchStore.luau")
    ui=(dist/"src"/"client/V4TrialOverlay.client.luau")
    old=ui.read_text("utf8")
    ui.write_text(patch_hud(old),encoding="utf8")
    newmodule=dist/"src"/"server/SixSkillAtomicProfile.luau"
    newmodule.write_bytes((FEATURE_ROOT/"SixSkillAtomicProfile.luau").read_bytes())
    project=dist/"default.project.json"
    cfg=json.loads(project.read_text("utf8"))
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    post=all_source(dist)
    assert len(post)==54
    changed=sorted(k for k in before if post[k]!=before[k])
    assert changed==sorted(FILES),("UNAUTHORIZED_MODIFICATION",changed)
    assert sorted(set(post)-set(before))==["server/SixSkillAtomicProfile.luau"]
    unchanged=set(before)-set(FILES)
    assert all(before[k]==post[k] for k in unchanged)
    game=post["server/Game.server.luau"].decode("utf8")
    store=post["server/PersistentHatchStore.luau"].decode("utf8")
    hud=post["client/V4TrialOverlay.client.luau"].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count("PersistentHatch.settleSixSkill(")==1
    assert "if v4OnHomePad(player)~=skill" in game
    assert "or utcEnd-utcStart<30" in game
    assert "if not RunService:IsStudio() then return end" not in game  # full original Game
    assert game.count("v4TickCanonical()")==2 # function + tick call
    assert store.count("function Store.settleSixSkill(")==1
    assert store.count("store:UpdateAsync(")>=1
    assert store.count('return "U_"..tostring(uid)')==1
    assert 'raw.dojoV4~=nil' in store and 'raw.dojo~=nil' in store
    assert "GetDataStore(" not in post["server/SixSkillAtomicProfile.luau"].decode("utf8")
    assert "P0D_V4_SaveStatus" in hud and "player.Idled:Connect(" in hud
    lock["total_scripts"]=54
    lock["blobs"]={k:blob(v) for k,v in sorted(post.items())}
    lock["rc_durable_skill_overlay"]={
        "id":"SIX_SKILL_DURABLE",
        "existing53_source_paths":53,"modified":changed,
        "added":["server/SixSkillAtomicProfile.luau"],
        "single_persistent_owner":"server/Game.server.luau + existing PersistentHatchStore",
        "only_studio_dev_key":True,
        "real_data_store_engine":"NOT_TESTED",
        "rollback":"disable SIX_SKILL_DURABLE flag and rebuild rich53",
        "author_patches":PINNED
    }
    lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    extra=dist/"RC_FEATURE_LOCK.json"
    if extra.exists():
        receipt=json.loads(extra.read_text("utf8"))
        assert receipt["total_sources"]==53
        receipt["total_sources"]=54
        receipt["source_gitblobs"]={k:blob(v) for k,v in sorted(post.items())}
        receipt["feature_flags"]["SIX_SKILL_DURABLE"]=True
        receipt["existing_53_preserved_except"]=changed
        extra.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_SIX_SKILL_SAMEKEY_DEV_PROFILE_RICH54_EXACT_50_UNCHANGED_PASS")
    return True

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--profile",choices=["rich51","rich47","legacy21"],required=True)
    cli.add_argument("--dist",type=Path,required=True)
    args=cli.parse_args()
    integrate(args.dist,args.profile)
