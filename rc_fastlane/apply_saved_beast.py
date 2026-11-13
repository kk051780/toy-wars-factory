#!/usr/bin/env python3
"""P0D official RC: additive source-exact saved BEAST -> evolved scout PvE.

After rich55 policy, modify original sole Game and add one pure ModuleScript.
Owner's existing evolution upgrades, short-session Dojo and only Horde damage
authority remain intact. NO Store, Remote, HP, score, XP, or paid modifications.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MOD=ROOT/"features/saved_beast/SavedBeastEvolutionPolicy.luau"
SHA="24d23ef4bf815bd42122b8a9604622cf46eff453"
def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
def allsrc(dist):
    return {p.relative_to(dist/"src").as_posix():p.read_bytes()
            for p in (dist/"src").rglob("*.luau")}
def one(s,old,new):
    assert s.count(old)==1,("BEAST_SOURCE_ANCHOR_DRIFT",old,s.count(old))
    return s.replace(old,new,1)
def apply(dist,profile):
    if profile!="rich51":
        print("P0D_BEAST_NOT_IN_FALLBACK",profile)
        return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    if not flags["SAVED_BEAST_EVOLUTION"]["enabled"]:
        print("P0D_BEAST_DISABLED_KEEP_RICH55")
        return False
    assert flags["SIX_SKILL_DURABLE"]["enabled"] is True
    assert flags["SAVED_PVE_MASTERY"]["enabled"] is True
    assert blob(MOD.read_bytes())==SHA, "PINNED_BEAST_MODULE_DRIFT"
    before=allsrc(dist)
    assert len(before)==55,("REQUIRES_SAVED_WEAPON_55",len(before))
    lockfile=dist/"SOURCE_LOCK.json"
    lock=json.loads(lockfile.read_text("utf8"))
    assert lock["total_scripts"]==55
    assert lock["rc_saved_pve_mastery_overlay"]["id"]=="SAVED_PVE_MASTERY"
    assert lock["blobs"]=={p:blob(v) for p,v in before.items()}
    original=before["server/Game.server.luau"].decode("utf8")
    assert original.count('remote.OnServerEvent:Connect(')==1
    assert original.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert original.count("PersistentHatch.settleSixSkill(")==1
    assert original.count("SavedPvePolicy.mergeWithEarned(")==1
    assert "P0D_SAVED_BEAST_EVOLUTION_V1" not in original

    game=one(original,
        'local SavedPvePolicy = require(script.Parent:WaitForChild("SavedPveMasteryPolicy"))',
        'local SavedPvePolicy = require(script.Parent:WaitForChild("SavedPveMasteryPolicy"))\n'
        'local SavedBeastEvolution = require(script.Parent:WaitForChild("SavedBeastEvolutionPolicy"))')

    # Only server-verified same-key DEV record. No player attribute is a trusted input.
    provider=(
        '-- P0D_SAVED_BEAST_EVOLUTION_V1: existing Game only, no extra PvE writer.\n'
        'local function savedBeastLevel(player: Player): (number,number,string)\n'
        '    if not RunService:IsStudio() or player.UserId<=0\n'
        '        or persistenceState[player]~="SAVED" then return 1,1,"NONE" end\n'
        '    local raw=persistentProfiles[player]\n'
        '    if not raw or not PersistentHatch.validate(raw) then return 1,1,"NONE" end\n'
        '    return SavedBeastEvolution.saved(raw.trainingV4)\n'
        'end\n'
    )
    game=one(game,
        '-- Free Hatch -> actual BEAST scout thin authoritative server-only adapter.',
        provider+'-- Free Hatch -> actual BEAST scout thin authoritative server-only adapter.')

    # The existing free hatch scout actually uses stage 2-3 evolution forms,
    # colored/size-changed source geometry. Never invent a second creature model.
    visualization=(
        '    if stage>=2 then\n'
        '        local savedPower,savedLevel,savedTier=savedBeastLevel(player)\n'
        '        if savedPower>1 and savedLevel>=5 then\n'
        '            -- Server-side label on the ACTUAL evolved model, same short scout lifetime.\n'
        '            local plate=Instance.new("BillboardGui")\n'
        '            plate.Name="SavedBeastEvolutionTier"\n'
        '            plate.Adornee=body\n'
        '            plate.AlwaysOnTop=true\n'
        '            plate.Size=UDim2.fromOffset(162,35)\n'
        '            plate.StudsOffsetWorldSpace=Vector3.new(0,3.1*scale,0)\n'
        '            plate.Parent=body\n'
        '            local txt=Instance.new("TextLabel")\n'
        '            txt.BackgroundTransparency=.28\n'
        '            txt.BackgroundColor3=Color3.fromRGB(33,24,62)\n'
        '            txt.TextColor3=Color3.fromRGB(255,224,108)\n'
        '            txt.Font=Enum.Font.GothamBold\n'
        '            txt.TextScaled=true\n'
        '            txt.Size=UDim2.fromScale(1,1)\n'
        '            txt.Text=string.format("魔獣 Lv%d | %s",savedLevel,savedTier)\n'
        '            txt.Parent=plate\n'
        '        end\n'
        '    end\n'
    )
    game=one(game,
        '    model.Parent=map.model -- server-created and replicated to BOTH clients, never local gallery\n'
        '    scoutModels[player]=model',
        '    model.Parent=map.model -- server-created and replicated to BOTH clients, never local gallery\n'
        +visualization+
        '    scoutModels[player]=model')

    # Original code's damage: evolution tier 26/40 * SESSION BEAST Dojo.
    # New saved BEAST strength compares against session dojo; it is NOT multiplied.
    game=one(game,
        '                    *Dojo.pveDamageMultiplier(dojoStates[player],"BEAST"),\n'
        '                    serverNow(),player.Character)',
        '                    *SavedBeastEvolution.choose(\n'
        '                        Dojo.pveDamageMultiplier(dojoStates[player],"BEAST"),\n'
        '                        savedBeastLevel(player)),\n'
        '                    serverNow(),player.Character)')

    assert game.count('Dojo.pveDamageMultiplier(dojoStates[player],"BEAST")')==1
    assert game.count('Dojo.pveDamageMultiplier(dojoStates[player],"WEAPON")')==1
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('SavedPvePolicy.mergeWithEarned(')==1
    assert game.count('PersistentHatch.settleSixSkill(')==1
    assert game.count('SavedBeastEvolution.choose(')==1
    assert 'hum:TakeDamage(' in game # unchanged PvP attack
    assert 'local function v4TickCanonical()' in game
    path=dist/"src/server/Game.server.luau"
    path.write_text(game,encoding="utf8")
    new=dist/"src/server/SavedBeastEvolutionPolicy.luau"
    assert not new.exists()
    new.write_bytes(MOD.read_bytes())
    final=allsrc(dist)
    assert len(final)==56
    assert sorted(p for p in before if final[p]!=before[p])==["server/Game.server.luau"]
    assert sorted(set(final)-set(before))==["server/SavedBeastEvolutionPolicy.luau"]
    assert all(final[p]==v for p,v in before.items() if p!="server/Game.server.luau")
    lock["total_scripts"]=56
    lock["blobs"]={p:blob(v) for p,v in sorted(final.items())}
    lock["rc_saved_beast_evolution_overlay"]={
        "id":"SAVED_BEAST_EVOLUTION",
        "modified":["server/Game.server.luau"],
        "added":["server/SavedBeastEvolutionPolicy.luau"],
        "old_54_source_bodies_unchanged":True,
        "short_session_dojo_preserved":True,
        "saved_bonus_nonstacking_max":1.20,
        "existing_evolution_stage_2_or_3_required_for_strike":True,
        "evolved_scout_actual_model_label":True,
        "no_new_Store_Remote_or_Game":True,
        "real_Studio":"NOT_TESTED",
        "rollback":"set SAVED_BEAST_EVOLUTION.enabled=false, rebuild existing rich55"
    }
    lockfile.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    extra=dist/"RC_FEATURE_LOCK.json"
    if extra.exists():
        e=json.loads(extra.read_text("utf8"))
        assert e["total_sources"]==55
        e["total_sources"]=56
        e["source_gitblobs"]={p:blob(v) for p,v in sorted(final.items())}
        e["feature_flags"]["SAVED_BEAST_EVOLUTION"]=True
        e["base55_unchanged_except_original_Game"]=True
        extra.write_text(json.dumps(e,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_SAVED_BEAST_EVOLUTION_RICH56_EXACT_54_UNCHANGED_ONE_GAME_PASS")
    return True
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--profile",required=True,choices=["rich51","rich47","legacy21"])
    a.add_argument("--dist",required=True,type=Path)
    p=a.parse_args()
    apply(p.dist,p.profile)
