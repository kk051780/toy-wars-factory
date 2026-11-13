#!/usr/bin/env python3
"""P0D official RC, three real existing scout species & evolved class styles.

Only original Game's existing summon model, guard shield and horde:hit are
reused. No new combat owner / Store / Remote / marketplace / XP / egg rules.
Feature flag independently returns byte-identical previous rich56 source.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MOD=ROOT/"features/scout_species/ScoutSpeciesPolicy.luau"
MOD_SHA="67dbf6129673de4be3a8061aebcaa6eafd0462fb"
def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
def allsrc(dist):
    return {p.relative_to(dist/"src").as_posix():p.read_bytes()
            for p in (dist/"src").rglob("*.luau")}
def one(s,old,new):
    assert s.count(old)==1,("SCOUT_SOURCE_ANCHOR_DRIFT",old,s.count(old))
    return s.replace(old,new,1)
def apply(dist,profile):
    if profile!="rich51":return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    if not flags["SCOUT_SPECIES_V1"]["enabled"]:
        print("P0D_SCOUT_SPECIES_V1_DISABLED_RICH56_EXACT")
        return False
    assert flags["SAVED_BEAST_EVOLUTION"]["enabled"] is True
    assert blob(MOD.read_bytes())==MOD_SHA,"PINNED_SCOUT_SPECIES_DRIFT"
    before=allsrc(dist)
    assert len(before)==56,("REQUIRES_RICH56",len(before))
    lockpath=dist/"SOURCE_LOCK.json"
    lock=json.loads(lockpath.read_text("utf8"))
    assert lock["total_scripts"]==56
    assert lock["rc_saved_beast_evolution_overlay"]["id"]=="SAVED_BEAST_EVOLUTION"
    assert lock["blobs"]=={p:blob(raw) for p,raw in before.items()}
    old=before["server/Game.server.luau"].decode("utf8")
    assert old.count("SavedBeastEvolution.choose(")==1
    assert old.count('remote.Name = "TrapRaidersS1Remote"')==1
    # The exact full attack hunk below is the single-authority guard; previous
    # B42 source may contain additional similar commentary or wrapper text.
    assert "horde:hit(" in old, "MISSING_ORIGINAL_HORDE"
    assert "P0D_SCOUT_SPECIES_V1" not in old

    code=one(old,
      'local SavedBeastEvolution = require(script.Parent:WaitForChild("SavedBeastEvolutionPolicy"))',
      'local SavedBeastEvolution = require(script.Parent:WaitForChild("SavedBeastEvolutionPolicy"))\n'
      'local ScoutSpecies = require(script.Parent:WaitForChild("ScoutSpeciesPolicy"))')

    code=one(code,
      '    local branch=if evolutionForm then evolutionForm.branch else "NONE"\n'
      '    local scale=if stage>=3 then 1.65',
      '    local branch=if evolutionForm then evolutionForm.branch else "NONE"\n'
      '    -- P0D_SCOUT_SPECIES_V1. Only the original server-minted scout token.\n'
      '    local species=ScoutSpecies.kind(token.cosmetic)\n'
      '    local scale=if stage>=3 then 1.65')

    # Two distinct on-model solid 3D pieces + an actual species-and-branch
    # Billboard, all inside the old five-second server-owned scout lifecycle.
    visual=(
      '    local crestKind=if species=="forest" then "LEAF_HORNS"\n'
      '        elseif species=="star" then "STAR_WINGS" else "SCOUT_HORNS"\n'
      '    local crestTint=if species=="forest" then Color3.fromRGB(61,255,110)\n'
      '        elseif species=="star" then Color3.fromRGB(255,230,64)\n'
      '        else Color3.fromRGB(124,204,255)\n'
      '    local crestSize=if species=="forest" then Vector3.new(.48,1.7,.5)*scale\n'
      '        elseif species=="star" then Vector3.new(1.7,.42,.65)*scale\n'
      '        else Vector3.new(.52,.85,.5)*scale\n'
      '    local crestLeft=piece(crestKind.."_LEFT",Enum.PartType.Block,crestSize,.08)\n'
      '    local crestRight=piece(crestKind.."_RIGHT",Enum.PartType.Block,crestSize,.08)\n'
      '    crestLeft.Color=crestTint;crestRight.Color=crestTint\n'
      '    local speciesPlate=Instance.new("BillboardGui")\n'
      '    speciesPlate.Name="P0D_ActualScoutSpecies"\n'
      '    speciesPlate.Adornee=body\n'
      '    speciesPlate.AlwaysOnTop=true\n'
      '    speciesPlate.Size=UDim2.fromOffset(200,35)\n'
      '    speciesPlate.StudsOffsetWorldSpace=Vector3.new(0,4.6*scale,0)\n'
      '    speciesPlate.Parent=body\n'
      '    local speciesLabel=Instance.new("TextLabel")\n'
      '    speciesLabel.Size=UDim2.fromScale(1,1)\n'
      '    speciesLabel.BackgroundTransparency=.32\n'
      '    speciesLabel.BackgroundColor3=Color3.fromRGB(24,38,61)\n'
      '    speciesLabel.TextColor3=crestTint\n'
      '    speciesLabel.TextScaled=true\n'
      '    speciesLabel.Font=Enum.Font.GothamBold\n'
      '    speciesLabel.Text=ScoutSpecies.label(species,branch)\n'
      '    speciesLabel.Parent=speciesPlate\n'
    )
    code=one(code,
        '    model.PrimaryPart=body\n'
        '    model.Parent=map.model -- server-created and replicated to BOTH clients, never local gallery',
        visual+
        '    model.PrimaryPart=body\n'
        '    model.Parent=map.model -- server-created and replicated to BOTH clients, never local gallery')

    code=one(code,
       '        evolutionGuards[player]={untilAt=serverNow()+8,\n'
       '            hits=if stage>=3 then 5 else 3}',
       '        local hitsAllowed,activeSeconds=ScoutSpecies.guard(species,stage)\n'
       '        evolutionGuards[player]={untilAt=serverNow()+activeSeconds,\n'
       '            hits=hitsAllowed}')

    code=one(code,
       '        local nextEvolvedStrike=0\n'
       '        local highlighted: Highlight?=nil',
       '        local nextEvolvedStrike=0\n'
       '        local assaultCount=0\n'
       '        local highlighted: Highlight?=nil')

    code=one(code,
       '            if evolvedAura then evolvedAura.CFrame=body.CFrame end\n'
       '            if stage>=2 and branch=="ASSAULT"',
       '            if evolvedAura then evolvedAura.CFrame=body.CFrame end\n'
       '            local spread=if species=="star" then 2.1 elseif species=="forest" then 1.1 else .8\n'
       '            crestLeft.CFrame=body.CFrame*CFrame.new(-spread*scale,1.25*scale,0)\n'
       '                *CFrame.Angles(0,0,if species=="forest" then -.32 else -.17)\n'
       '            crestRight.CFrame=body.CFrame*CFrame.new(spread*scale,1.25*scale,0)\n'
       '                *CFrame.Angles(0,0,if species=="forest" then .32 else .17)\n'
       '            if stage>=2 and branch=="ASSAULT"')

    code=one(code,
       '            if stage>=2 and branch=="ASSAULT"\n'
       '                and serverNow()>=nextEvolvedStrike then',
       '            local speciesStrikeDamage,speciesInterval,maxSpeciesStrikes=\n'
       '                ScoutSpecies.attack(species,stage)\n'
       '            if stage>=2 and branch=="ASSAULT" and speciesStrikeDamage>0\n'
       '                and assaultCount<maxSpeciesStrikes\n'
       '                and serverNow()>=nextEvolvedStrike then')

    code=one(code,
       '                local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,\n'
       '                    (if stage>=3 then 40 else 26)\n'
       '                    *SavedBeastEvolution.choose(',
       '                local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,\n'
       '                    speciesStrikeDamage\n'
       '                    *SavedBeastEvolution.choose(')

    code=one(code,
       '                nextEvolvedStrike=serverNow()+12',
       '                assaultCount+=1\n'
       '                nextEvolvedStrike=serverNow()+speciesInterval')

    assert code.count('remote.OnServerEvent:Connect(')==1
    assert code.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert code.count('horde:hit(anchor,currentRoot.CFrame.LookVector,')==1
    assert code.count('SavedBeastEvolution.choose(')==1
    assert code.count('Dojo.pveDamageMultiplier(dojoStates[player],"BEAST")')==1
    assert code.count('SavedPvePolicy.mergeWithEarned(')==1
    assert code.count('PersistentHatch.settleSixSkill(')==1
    assert code.count("ScoutSpecies.attack(")==1
    assert code.count("ScoutSpecies.guard(")==1
    assert code.count("ScoutSpecies.label(")==1
    assert "function Store." not in MOD.read_text("utf8")
    (dist/"src/server/Game.server.luau").write_text(code,encoding="utf8")
    dest=dist/"src/server/ScoutSpeciesPolicy.luau"
    assert not dest.exists()
    dest.write_bytes(MOD.read_bytes())

    final=allsrc(dist)
    assert len(final)==57
    assert sorted(p for p in before if final[p]!=before[p])==["server/Game.server.luau"]
    assert sorted(set(final)-set(before))==["server/ScoutSpeciesPolicy.luau"]
    assert all(final[p]==data for p,data in before.items() if p!="server/Game.server.luau")
    lock["total_scripts"]=57
    lock["blobs"]={p:blob(v) for p,v in sorted(final.items())}
    lock["rc_scout_species_overlay"]={
        "id":"SCOUT_SPECIES_V1",
        "existing_55_sources_byte_unchanged":True,
        "game_only_modified":True,"new_pure_module":"server/ScoutSpeciesPolicy.luau",
        "server_token_cosmetic":"forest/star/default",
        "assault":"forest 2 light hits in same 5s lifetime, star 1 heavier, default original",
        "guard":"forest +1 hit, star +1 second, default original",
        "original_evolution":"unchanged", "only_one_horde_hit_callsite":True,
        "real_studio":"NOT_TESTED", "rollback":"disable flag to restore rich56"
    }
    lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    f=dist/"RC_FEATURE_LOCK.json"
    if f.exists():
        extra=json.loads(f.read_text("utf8"))
        assert extra["total_sources"]==56
        extra["total_sources"]=57
        extra["source_gitblobs"]={p:blob(v) for p,v in sorted(final.items())}
        extra["feature_flags"]["SCOUT_SPECIES_V1"]=True
        extra["base56_except_original_Game_preserved"]=True
        f.write_text(json.dumps(extra,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_SCOUT_SPECIES_RICH57_SOURCE_LOCK_55_UNCHANGED_SINGLE_GAME_PASS")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile",choices=["rich51","rich47","legacy21"],required=True)
    parser.add_argument("--dist",type=Path,required=True)
    args=parser.parse_args()
    apply(args.dist,args.profile)
