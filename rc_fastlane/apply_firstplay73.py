#!/usr/bin/env python3
"""P0D P0 cumulative first-play: ART71 + original READY/LOBBY/SOLO -> private73.

Reuses byte-exact original AUTHORS of #363, #376, #378 (QA #380 adopted).
The actual original 66 official sources must be reconstructed in the source-
locked ART71 input, and only Game/Config/HUD/V4 may be changed. Everything else
in 71 is byte-identical, notably all five ART scripts. The original server Game
stays the ONLY match/HP/score/egg/Remote authority.

B #220 sole official authenticated CAS writer; this is an ISOLATED PRIVATE
candidate and MUST NOT be merged wholesale to RC or main. Studio not tested.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUTH = ROOT / "features/firstplay73"
FEATURE = "P0D_FIRSTPLAY_READY_LOBBY_SOLO_ON_ART71_PRIVATE_V1"
BEFORE = 71
AFTER = 73

AUTHORS = (
    ("ready", "author_ready.py", "52f0fa1dbdc09de3ca9bebbec1c8768d4eba4c92",
     "P0_GAMECORE_READY_15M_HUD_V1"),
    ("lobby", "author_lobby.py", "9fcf93b03efd5567f6c5197453fc1817a5105928",
     "FB007_LOBBY_DOJO_PHYSICAL_V1"),
    ("solo", "author_solo.py", "2d0a7a36100b562d6baa9670bc5da0a1deae24bc",
     "FB005_STUDIO_SOLO_TEAM_BOTS_CLASSIC_V1"),
)
MODULES = (
    ("server/LobbyDojoIsland.luau", "LobbyDojoIsland.luau",
     "0ea8a0957841bcbd92def235726cc9a21be1231f"),
    ("server/SoloTeamBots.luau", "SoloTeamBots.luau",
     "b62c267a352c4037eb71acbb0e440b64011c2a00"),
)
GAME = "server/Game.server.luau"
CONFIG = "shared/Config.luau"
HUD = "client/HUD.client.luau"
V4 = "server/V4TrainingBridge.server.luau"
MODIFIED = {GAME, CONFIG, HUD, V4}


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def all_sources(dist: Path) -> dict[str, bytes]:
    root = dist/"src"
    assert root.is_dir(), "FIRSTPLAY_SOURCE_MISSING"
    return {p.relative_to(root).as_posix():p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}


def load_authors():
    mods = {}
    for name,filename,expected,_ in AUTHORS:
        path=AUTH/filename
        assert gitblob(path.read_bytes())==expected, ("FIRSTPLAY_AUTHOR_DRIFT",name)
        spec=importlib.util.spec_from_file_location("firstplay_auth_"+name,path)
        assert spec and spec.loader
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        mods[name]=module
    return mods


def modules():
    out={}
    for dest,filename,pin in MODULES:
        content=(AUTH/filename).read_bytes()
        assert gitblob(content)==pin,("FIRSTPLAY_MODULE_DRIFT",dest)
        text=content.decode("utf8")
        if "Lobby" in dest:
            assert "function Lobby.padPosition(" in text and "function Lobby.build(" in text
        else:
            assert "PathfindingService" in text and "Bot.tryHumanHit" in text
            assert "Bot.start" in text and "Bot.tick" in text
        for forbidden in ("Instance.new(\"RemoteEvent\")","OnServerEvent:Connect(",
                          "DataStoreService","MarketplaceService","UpdateAsync("):
            assert forbidden not in text,("FIRSTPLAY_MODULE_AUTHORITY",dest,forbidden)
        out[dest]=content
    return out


def compose(previous: dict[str, bytes]) -> tuple[dict[str,bytes], dict]:
    assert len(previous)==BEFORE,("FIRSTPLAY_EXPECT_ART71",len(previous))
    for required in (*MODIFIED,"server/MusouHorde.luau",
                     "server/CastleBattlefield.server.luau",
                     "server/H1CoastalSeascape.server.luau",
                     "server/FantasyWorldArt.server.luau",
                     "server/ArtMinionSilhouette.server.luau",
                     "client/ConfirmedSlashFX.client.luau"):
        assert required in previous,("FIRSTPLAY_MISSING",required)
    assert previous[GAME].count(b"remote.OnServerEvent:Connect(")==1
    old_mod=modules()
    assert not(set(old_mod)&set(previous))
    author=load_authors()
    source=previous[GAME].decode("utf8")
    # Author original context anchors: all source patches are fail-closed
    # against the final single 71-source Game in ONE controlled order.
    source=author["ready"].patch_game(source)
    source=author["lobby"].patch_game(source)
    source=author["solo"].patch_game(source)
    assert source.count("remote.OnServerEvent:Connect(")==1
    assert source.count("local function tickRound()")==1
    assert source.count("local function stopRound(")==1
    for marker in ("READY_TOGGLE","allPlayersReadyForRound()",
                   "LobbyIsland.spawn(team)",
                   "pcall(SoloTeamBots.start,map,","SoloTeamBots.tick",
                   "SOLO_BOTS_NOT_READY"):
        assert marker in source,("FIRSTPLAY_MISSING_GAME_BEHAVIOR",marker)
    updated=dict(previous)
    updated[GAME]=source.encode("utf8")
    updated[CONFIG]=author["ready"].patch_config(previous[CONFIG].decode("utf8")).encode("utf8")
    updated[HUD]=author["ready"].patch_hud(previous[HUD].decode("utf8")).encode("utf8")
    updated[V4]=author["lobby"].patch_v4(previous[V4].decode("utf8")).encode("utf8")
    updated.update(old_mod)
    assert len(updated)==AFTER
    assert {p for p in previous if previous[p]!=updated[p]}==MODIFIED
    assert all(previous[p]==updated[p] for p in previous if p not in MODIFIED)
    assert all(updated[p]==v for p,v in old_mod.items())
    assert b"MatchSeconds = 900" in updated[CONFIG]
    assert b"READY_TOGGLE" in updated[HUD]
    assert updated[GAME].count(b"remote.OnServerEvent:Connect(")==1
    receipt={
        "id":FEATURE,"input_count":BEFORE,"output_count":AFTER,
        "original_art5_sources_byte_identical":True,
        "old71_modified_only":sorted(MODIFIED),
        "new_modules":list(old_mod),
        "source_authors":[{"owner":n,"file":f,"blob":h,"feature":feat}
                          for n,f,h,feat in AUTHORS],
        "parent_art70plus":"FB015_FIVE_ART_CUMULATIVE_PREVIEW_V1",
        "game_authority":"ONLY_OLD_SINGLE_GAME",
        "solo_bot_teams":"2_ally_3_enemy",
        "solo_classic_egg_only":True,"five_egg_ai":"NOT_SUPPORTED",
        "owner_approved":False,"real_studio":"NOT_TESTED",
        "two_client":"NOT_TESTED","android_fps":"NOT_TESTED",
        "studio_overlap_castle_sea_lobby":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
        "rollback":"omit firstplay adapter; --enabled false ZERO WRITE / art71 unchanged",
    }
    return updated,receipt


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("FIRSTPLAY73_OFF_NO_WRITE_ART71_PRESERVED")
        return False
    previous=all_sources(dist)
    assert len(previous)==BEFORE,("FIRSTPLAY_REQUIRES_ART71",len(previous))
    sp=dist/"SOURCE_LOCK.json"
    fp=dist/"RC_FEATURE_LOCK.json"
    pj=dist/"default.project.json"
    sl=json.loads(sp.read_text("utf8"))
    fl=json.loads(fp.read_text("utf8"))
    project=json.loads(pj.read_text("utf8"))
    old_pin={p:gitblob(v) for p,v in sorted(previous.items())}
    assert sl["total_scripts"]==BEFORE and sl["blobs"]==old_pin
    assert fl["total_sources"]==BEFORE and fl["source_gitblobs"]==old_pin
    assert fl["feature_flags"]["FB015_FIVE_ART_CUMULATIVE_PREVIEW_V1"] is True
    assert FEATURE not in fl["feature_flags"]
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    after,receipt=compose(previous)
    pins={p:gitblob(v) for p,v in sorted(after.items())}
    sl["total_scripts"]=AFTER
    sl["blobs"]=pins
    sl["rc_firstplay73"]=receipt
    fl["total_sources"]=AFTER
    fl["source_gitblobs"]=pins
    fl["feature_flags"][FEATURE]=True
    fl["rc_firstplay73"]=receipt
    # No source/project write until ALL author/source locks and compositions pass.
    for path in sorted(MODIFIED | {x[0] for x in MODULES}):
        (dist/"src"/path).write_bytes(after[path])
    sp.write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
    fp.write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
    assert all_sources(dist)==after
    print("P0D_FIRSTPLAY73_READY_LOBBY_SOLO_ART71_SOURCE_EXACT_GAME_SINGLE_PASS")
    return True


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    args=p.parse_args()
    apply(args.dist,args.enabled=="true")
