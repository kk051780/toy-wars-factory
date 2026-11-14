#!/usr/bin/env python3
"""OWNER #340/#341: source-exact, reversible HUD+Studio debug cleanup on RC65.

Does not alter Game, Store, Remote, score, XP, egg or match authority.
Actual rich65 Game ALREADY supports one-player Studio Solo practice.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ID = "OWNER_FIRSTPLAY_UX_V1"
BLOBS = {
    "client/HUD.client.luau": "4a75ee2310652f064f89c760629c26df28f69cc5",
    "client/V4TrialOverlay.client.luau": "fd5f93f982e353b22eed1a5eb29ad965bb73da5b",
    "client/P0DStudioTrialAudit.client.luau": "ee96518a7eeaaaba98d2a8e2aff6dad780fae8c7",
}

def blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*.luau"))}

def sub(s: str, old: str, new: str) -> str:
    assert s.count(old) == 1, ("OWNER_UX_SOURCE_DRIFT", old[:70], s.count(old))
    return s.replace(old, new, 1)

def patch_hud(s: str) -> str:
    s = sub(s, '"Score", UDim2.new(.76, 0, 0, 58), UDim2.new(.12, 0, 0, 4)',
            '"Score", UDim2.new(.76, 0, 0, 39), UDim2.new(.12, 0, 0, 4)')
    s = sub(s, '"Status", UDim2.new(.76, 0, 0, 34), UDim2.new(.12, 0, 0, 65)',
            '"Status", UDim2.new(.76, 0, 0, 29), UDim2.new(.12, 0, 0, 47)')
    s = sub(s, '"RealH1ServerLevel",UDim2.new(.76,0,0,35),\n    UDim2.new(.12,0,0,105)',
            '"RealH1ServerLevel",UDim2.new(.42,0,0,26),\n    UDim2.new(.015,0,0,82)')
    s = sub(s, '"First90RealObjectiveGuide",UDim2.new(.62,0,0,44),\n    UDim2.new(.19,0,.61,0)',
            '"First90RealObjectiveGuide",UDim2.new(.48,0,0,29),\n    UDim2.new(.26,0,.19,0)')
    s = sub(s, 'UDim2.fromOffset(260,33),UDim2.fromOffset(17,178)',
            'UDim2.fromOffset(190,28),UDim2.fromOffset(12,94)')
    s = sub(s, '    if s.phase == "LOBBY" then return "準備中：役職と次の試合モードを選ぼう！" end',
            '''    if s.phase == "LOBBY" then
        local total=(if type(s.redPlayers)=="number" then s.redPlayers else 0)
            +(if type(s.bluePlayers)=="number" then s.bluePlayers else 0)
        if RunService:IsStudio() and total==1 then
            return "▶ 1人練習は自動開始！ 役職を選ぼう"
        end
        return "▶ 赤・青がそろうと自動開始。役職を選ぼう"
    end''')
    s = sub(s, '    if s.phase == "COUNTDOWN" then return "開始まで " .. tostring(s.time) .. " 秒！" end',
            '    if s.phase == "COUNTDOWN" then return "▶ 開始まで " .. tostring(s.time) .. " 秒" end')
    s = sub(s, '    top.Text = string.format("🔴 %d / 🏰 %d       🔵 %d / 🏰 %d\\n自分:%s・%s  |  %d対%d人",\n        s.scores.RED or 0, s.hp.RED or 0, s.scores.BLUE or 0,\n        s.hp.BLUE or 0, s.team or "?", displayRole(s.role),\n        s.redPlayers or 0, s.bluePlayers or 0)',
            '    top.Text = string.format("🔴%d   🔵%d   🏰%d/%d",\n        s.scores.RED or 0, s.scores.BLUE or 0, s.hp.RED or 0, s.hp.BLUE or 0)')
    s = sub(s, '    dojoBadge.Visible=valid and s.hatchEnabled==true',
            '    dojoBadge.Visible=valid and s.hatchEnabled==true and s.phase=="LOBBY"')
    s = sub(s, '    progressBadge.Visible=s.phase=="ACTIVE"',
            '    progressBadge.Visible=false -- XP stays server-owned; hide bulky text')
    s = sub(s, '    instructions.Visible=s.phase=="ACTIVE"',
            '    instructions.Visible=false -- redundant multiline help, keep controls')
    s = sub(s, '    top.Text=string.format("🏆 🔴 %d 点    🔵 %d 点\\n自分:%s・%s　|　卵5こ得点戦",\n            s.scores.RED or 0,s.scores.BLUE or 0,s.team or "?",displayRole(s.role))',
            '    top.Text=string.format("🏆 🔴%d   🔵%d", s.scores.RED or 0,s.scores.BLUE or 0)')
    assert 'if s.kind ~= "SNAPSHOT" then return end' in s
    assert 'action("MODE_VOTE","CLASSIC")' in s
    return s

def patch_v4(s: str) -> str:
    return sub(s, 'local folded=false\ntoggle.MouseButton1Click:Connect(function()',
        'local folded=true -- DEV panel starts collapsed for OWNER first play\nbox.Visible=false\ntoggle.Text="修行詳細"\ntoggle.MouseButton1Click:Connect(function()')

def patch_audit(s: str) -> str:
    s = sub(s, '    screen.DisplayOrder=110\n',
        '    screen.DisplayOrder=110\n    screen.Enabled=false -- F9 logs retain private QA\n')
    assert 'remote.OnClientEvent:Connect(function(msg:any)' in s
    return s

def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("P0D_OWNER_UX_OFF_BYTE_IDENTICAL_PREVIOUS65_PASS")
        return False
    before=sources(dist)
    assert len(before)==65, ("REQUIRE_CANONICAL65", len(before))
    assert all(p in before and blob(before[p])==b for p,b in BLOBS.items()), "OLD_HUD_BLOBS_DRIFT"
    assert "server/Game.server.luau" in before
    previous={p:blob(b) for p,b in sorted(before.items())}
    lp=dist/"SOURCE_LOCK.json"
    fp=dist/"RC_FEATURE_LOCK.json"
    lock=json.loads(lp.read_text("utf8"))
    feature=json.loads(fp.read_text("utf8"))
    assert lock["total_scripts"]==65 and lock["blobs"]==previous
    assert feature["total_sources"]==65 and feature["source_gitblobs"]==previous
    assert ID not in feature["feature_flags"]
    updated={
        "client/HUD.client.luau":patch_hud(before["client/HUD.client.luau"].decode("utf8")).encode("utf8"),
        "client/V4TrialOverlay.client.luau":patch_v4(before["client/V4TrialOverlay.client.luau"].decode("utf8")).encode("utf8"),
        "client/P0DStudioTrialAudit.client.luau":patch_audit(before["client/P0DStudioTrialAudit.client.luau"].decode("utf8")).encode("utf8"),
    }
    after={**before,**updated}
    assert {p for p in before if before[p]!=after[p]}==set(BLOBS)
    pins={p:blob(b) for p,b in sorted(after.items())}
    lock["blobs"]=pins
    lock["rc_owner_firstplay_ux"]={
        "id":ID,"owner_issues":[340,341],"modified":sorted(updated),
        "unchanged_other_sources":62,"game_remote_store_unchanged":True,
        "solo_authority_unchanged":True,"studio_fun":"NOT_TESTED",
        "rollback":"omit overlay to restore exact prior65"
    }
    feature["source_gitblobs"]=pins
    feature["feature_flags"][ID]=True
    for path,raw in updated.items():
        (dist/"src"/path).write_bytes(raw)
    lp.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    fp.write_text(json.dumps(feature,ensure_ascii=False,indent=2)+"\n","utf8")
    assert sources(dist)==after
    print("P0D_OWNER_UX_65_3_CLIENT_MODIFIED_62_OTHER_IDENTICAL_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    args=p.parse_args()
    apply(args.dist,args.enabled=="true")
