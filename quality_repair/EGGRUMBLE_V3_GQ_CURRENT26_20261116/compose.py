#!/usr/bin/env python3
"""Private SOURCE-only EGGRUMBLE V3 composition: original 7-domain game, ART,
SCORE and the quality owner's existing spatial fixes. No RC/main/publish writes.
"""
import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path

GAME="handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
ART="handoffs/EGGRUMBLE-ART-SILHOUETTE-FIELD-20261116"
SERVER_REQUIRED={
 "EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_CastleMatchRules",
 "EGGRUMBLE_BotActors", "EGGRUMBLE_BotPathRouter", "EGGRUMBLE_SevenRoleCombat",
 "EGGRUMBLE_FieldItemPickups", "EGGRUMBLE_RaidItemIntake",
 "EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_BossSessionFence",
 "EGGRUMBLE_DivineMantle", "EGGRUMBLE_MatchResultService",
}
ART_SERVER={"EGGRUMBLE_HeroSilhouetteArt","EGGRUMBLE_FlagshipFieldArt",
            "EGGRUMBLE_EncounterReadabilityArt"}

def path_for(project, item):
    assert isinstance(item,dict) and set(item)=={"$path"},item
    return (project.parent/item["$path"]).resolve(strict=True)

def source_path(out,path):
    return {"$path":os.path.relpath(path,out.parent).replace(os.sep,"/")}

def iter_scripts(project):
    def walk(item, chain):
        if isinstance(item,dict):
            if "$path" in item:
                yield chain,path_for(project,item)
            else:
                for name,child in item.items():
                    if not name.startswith("$"):
                        yield from walk(child,chain+(name,))
    yield from walk(project.tree,())

class Project:
    def __init__(self,path):
        self.path=path.resolve(strict=True)
        self.parent=self.path.parent
        self.data=json.loads(self.path.read_text(encoding="utf-8"))
        self.tree=self.data["tree"]

def apply_ramp(author_source,quality_source):
    # Source-selective quality patch: retain NEWEST original 7-domain host and
    # replace neither its boss logic nor its item/lobby state-machine.
    start=" -- Equal walkable entrance approach to every personal castle;"
    end=" -- Hollow, traversable standard castle shell:"
    assert author_source.count(end)==1,"author changed castle construction"
    assert "CastleAccessRamp" not in author_source,"author already has ramp: reconcile manually"
    assert quality_source.count(start)==1 and quality_source.count(end)==1
    ramp=quality_source[quality_source.index(start):quality_source.index(end)].rstrip("\n")
    assert 'block(model,"CastleAccessRamp"' in ramp and "CFrame.Angles" in ramp
    assert "StandardFoundation" in author_source[:author_source.index(end)]
    assert author_source.count("local function createWorldCastle")==1
    return author_source.replace(end,ramp+"\n"+end)

def main():
    ap=argparse.ArgumentParser()
    for arg in ("author","quality","art","score","art_project","out"):
        ap.add_argument("--"+arg.replace("_","-"),required=True,type=Path)
    args=ap.parse_args()
    author=(args.author/GAME).resolve(strict=True)
    quality=(args.quality/GAME).resolve(strict=True)
    art=(args.art/ART).resolve(strict=True)
    score=(args.score/GAME).resolve(strict=True)
    out=args.out.resolve()
    assert out.parent.is_dir() and out.parent!=author and out.parent!=quality
    author_project=Project(author/"EGGRUMBLE_V3_STUDIO.project.json")
    art_project=Project(args.art_project)
    original=author_project.tree["ServerScriptService"]
    server=art_project.tree["ServerScriptService"]
    client=art_project.tree["StarterPlayer"]["StarterPlayerScripts"]
    assert original["$className"]=="ServerScriptService"
    assert len(original)-1==19 and len(server)-1==22,("author/art server drift",len(original),len(server))
    assert len(client)-1==3,("author/art client drift",len(client))
    assert SERVER_REQUIRED.issubset(original)
    assert ART_SERVER.issubset(server)
    assert "EGGRUMBLE_ProceduralSkills" in client
    assert "EGGRUMBLE_ArtDistanceLOD" in client
    for name,spec in original.items():
        if name=="$className":continue
        assert path_for(author_project,spec)==path_for(art_project,server[name]),name
    # Original artist's output must add only visual art, not rewrite game logic.
    assert set(server)-set(original)==ART_SERVER
    assert set(client)-{"$className"}=={
       "EGGRUMBLE_CombatFeel","EGGRUMBLE_ProceduralSkills","EGGRUMBLE_ArtDistanceLOD"}
    # Two pre-existing GQ AI fixes, owned by PR 484; no duplicate implementation.
    for name in ("EGGRUMBLE_BotActors","EGGRUMBLE_BotPathRouter"):
        src=(quality/(name+".luau")).resolve(strict=True)
        assert src.is_file() and "return " in src.read_text(encoding="utf-8")
        server[name]=source_path(out,src)
    source=path_for(author_project,original["EGGRUMBLE_LobbyCastleModesPreview"]).read_text(encoding="utf-8")
    quality_source=(quality/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
    patched=apply_ramp(source,quality_source)
    patched_path=out.parent/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    patched_path.write_text(patched,encoding="utf-8")
    server["EGGRUMBLE_LobbyCastleModesPreview"]=source_path(out,patched_path)
    # Only SCORE's original result adapter and score math; never duplicate HUD.
    result=(score/"EGGRUMBLE_MatchResultService.luau").resolve(strict=True)
    balance=(score/"EGGRUMBLE_ScoreBalance.luau").resolve(strict=True)
    assert "EGGRUMBLE_ScoreBalance" in result.read_text(encoding="utf-8")
    server["EGGRUMBLE_MatchResultService"]=source_path(out,result)
    assert "EGGRUMBLE_ScoreBalance" not in server
    server["EGGRUMBLE_ScoreBalance"]=source_path(out,balance)
    assert len(server)-1==23 and len(client)-1==3
    art_project.data["name"]="EGGRUMBLE_V3_GQ_AUTHOR_ART_SCORE26_PRIVATE_NO_PUBLISH"
    out.write_text(json.dumps(art_project.data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    manifest=Project(out)
    mapped=list(iter_scripts(manifest))
    assert len(mapped)==26
    sources={nodes[-1]:(nodes, p) for nodes,p in mapped}
    assert len(sources)==26,"two Services have duplicate script names"
    assert all(p.is_file() for _,p in mapped)
    assert sum(1 for nodes,_ in mapped if nodes[-1]=="EGGRUMBLE_LobbyCastleModesPreview")==1
    # All sibling Script imports must resolve to an actual composed module.
    for nodes,p in mapped:
        body=p.read_text(encoding="utf-8")
        if nodes[0]!="ServerScriptService":continue
        for dep in re.findall(r'script\.Parent:WaitForChild\("([^"]+)"\)',body):
            assert dep in server,("unmapped sibling",nodes,dep)
    # Cross-domain guard: actual late-author modules and client skills, not old
    # 16-script content relabeled as complete.
    host=patched_path.read_text(encoding="utf-8")
    for token in ("CastleAccessRamp","EGGRUMBLE_RaidItemIntake",
                  "EGGRUMBLE_NeutralStoneGiant","EGGRUMBLE_BossSessionFence"):
        assert token in host,("new source lost functionality",token)
    player_skills=path_for(manifest,client["EGGRUMBLE_ProceduralSkills"]).read_text(encoding="utf-8")
    server_skills=path_for(manifest,server["EGGRUMBLE_SevenRoleCombat"]).read_text(encoding="utf-8")
    assert "EGGRUMBLE_SkillCastSignature" in player_skills
    assert "EGGRUMBLE_SkillCastSignature" in server_skills
    receipt={
      "status":"SOURCE_ONLY_NOT_OFFICIAL_RC",
      "studio":"NOT_TESTED","android":"NOT_TESTED","owner_accepted":False,
      "script_count":len(mapped),"server_count":23,"client_count":3,
      "author_project":str(author_project.path),"art_project":str(args.art_project),
      "quality_overrides":["EGGRUMBLE_BotActors","EGGRUMBLE_BotPathRouter",
                           "EGGRUMBLE_LobbyCastleModesPreview.castle_ramp_ONLY"],
      "score_overrides":["EGGRUMBLE_MatchResultService","EGGRUMBLE_ScoreBalance"],
      "source_sha256":{name:hashlib.sha256(p.read_bytes()).hexdigest()
                       for name,(_,p) in sorted(sources.items())},
    }
    (out.parent/"SOURCE_RECEIPT.json").write_text(
      json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EGGRUMBLE_GQ_CURRENT26_SOURCE_COMPOSITION_PASS",len(mapped))

if __name__=="__main__":main()
