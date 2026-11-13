#!/usr/bin/env python3
"""Reproducibly build one Studio-only H1 with four independently sourced lanes.

Base: #252 exact full-game H1 role+world composite (25 Luau).
Overlays: #253 wall-clear route code (one Script replacement), #219 D18
mascot Catalog/Rules/LocalScript (three additions). Original owners' trees are
read-only. NEVER alter protected S1 RC or publish this test build.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, shutil, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve().parents[1]
UP = REPO / "handoffs/P0D-H1-COMPOSITE-20261113-01"
DST = OWN / "dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY"
SRC = UP / "src"
IN = OWN / "inputs"

PROVENANCE = {
    "base_composite_git_commit": "3c537a551e173fffaf0e1039c90d04250313c6d8",
    "base_game_GitBlob": "adecfee41a594bdd54393050b4890a5733a536ce",
    "base_HUD_GitBlob": "6d273404800e1d25fb1405bc52249b3ab47c1b41",
    "base_wind_GitBlob": "7d5706774b874759e7ab994dc0654c3ae9a46502",
    "base_original_world_GitBlob": "6de8a8b4f17afd4e11c4be8eb1db556506d9c8df",
    "base_original_map_GitBlob": "94655d019fdf9798fa24a350ebf49f8290465ac0",
    "fixed_world_source_commit": "2494fa855d77e1ef6dd2c5f8b8d21fbef90fc44a",
    "fixed_world_blob": "cc764b9caaa293ff747489e02e607af4502ddca4",
    "D18_source_commit": "bce72bd3b36f5a331afc939ede6a7779fb9545b9",
    "D18_catalog_blob": "41079553d2141940fc3fee57b23969e292770614",
    "D18_rules_blob": "328b8a4d70261e633f163a5e166822a29d7eb1ba",
    "D18_client_blob": "39a2e35e4b2e8635d6d87359cd86f783aedf8756",
}
INPUTS = {
    "server/H1FunWorld.server.luau": "cc764b9caaa293ff747489e02e607af4502ddca4",
    "client/D18Batch8Catalog.luau": "41079553d2141940fc3fee57b23969e292770614",
    "client/D18MascotGuideRules.luau": "328b8a4d70261e633f163a5e166822a29d7eb1ba",
    "client/D18MascotGuide.client.luau": "39a2e35e4b2e8635d6d87359cd86f783aedf8756",
}
BASE = {
    "server/Game.server.luau": PROVENANCE["base_game_GitBlob"],
    "client/HUD.client.luau": PROVENANCE["base_HUD_GitBlob"],
    "server/S1RaiderWindRules.luau": PROVENANCE["base_wind_GitBlob"],
    "server/H1FunWorld.server.luau": PROVENANCE["base_original_world_GitBlob"],
    "server/MapBuilder.luau": PROVENANCE["base_original_map_GitBlob"],
}
ORIGINAL_ROUTES = {"SKY_RAMP_RED", "SKY_WALKWAY", "SKY_RAMP_BLUE", "SEA_LOW_CAUSEWAY"}
CORRECTED_ROUTES = ORIGINAL_ROUTES | {"SEA_ENTRY_RED", "SEA_ENTRY_BLUE"}
ROUTES = re.compile(
    r'path\("([^"]+)",\s*Vector3\.new\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\),\s*'
    r'Vector3\.new\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\),\s*([\d.]+)'
)
def blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
def assert_blob(p: Path, expected: str):
    actual = blob(p.read_bytes())
    assert actual == expected, f"GIT_BLOB_MISMATCH {p} actual={actual} expected={expected}"

def segments(source: str):
    result = {}
    for m in ROUTES.finditer(source):
        k = m.group(1)
        assert k not in result, f"DUPLICATE_ROUTE {k}"
        vals = list(map(float, m.groups()[1:]))
        a,b = tuple(vals[:3]),tuple(vals[3:6])
        result[k] = (a,b,vals[6])
    return result

def centerline_wall_intersections(paths):
    # Original S1 castle-side wall Parts: size=(40,14,5) at
    # position=(+/-103,7,+/-44), CanCollide=true.
    hits = []
    for name,(a,b,width) in paths.items():
        assert width >= 8 and width <= 20
        for team,x in (("RED",-103),("BLUE",103)):
            for z in (-44.,44.):
                bounds = ((x-20.,x+20.),(0.,14.),(z-2.5,z+2.5))
                lower,upper = 0.,1.
                for axis,(lo,hi) in enumerate(bounds):
                    d=b[axis]-a[axis]
                    if abs(d)<1e-12:
                        if not lo<=a[axis]<=hi:
                            lower,upper=1.,0.
                            break
                    else:
                        p0,p1=(lo-a[axis])/d,(hi-a[axis])/d
                        lower=max(lower,min(p0,p1))
                        upper=min(upper,max(p0,p1))
                if lower<=upper:
                    hits.append((name,team,z))
    return hits

def check_geometry(before: str, after: str) -> dict:
    orig=segments(before);good=segments(after)
    assert set(orig)==ORIGINAL_ROUTES,sorted(orig)
    assert set(good)==CORRECTED_ROUTES,sorted(good)
    hits=centerline_wall_intersections(orig)
    assert sorted(hits)==[
        ("SEA_LOW_CAUSEWAY","BLUE",-44.),("SEA_LOW_CAUSEWAY","RED",-44.),
        ("SKY_RAMP_BLUE","BLUE",44.),("SKY_RAMP_RED","RED",44.)],hits
    fixed=centerline_wall_intersections(good)
    assert not fixed, f"PATCH_STILL_WALL_COLLIDES {fixed}"
    def same(a,b):
        return sum((x-y)**2 for x,y in zip(a,b)) < 0.0001
    assert same(good["SKY_RAMP_RED"][1],good["SKY_WALKWAY"][0])
    assert same(good["SKY_WALKWAY"][1],good["SKY_RAMP_BLUE"][0])
    assert same(good["SEA_LOW_CAUSEWAY"][0],good["SEA_ENTRY_RED"][0])
    assert same(good["SEA_LOW_CAUSEWAY"][1],good["SEA_ENTRY_BLUE"][0])
    assert all(all(abs(p[i])<bound for i,bound in enumerate((125,120,71))
                   if i in (0,2)) for a,b,_ in good.values() for p in (a,b))
    assert all(abs(b[1]-a[1])<=0.55*((b[0]-a[0])**2+(b[2]-a[2])**2)**0.5
               for a,b,_ in good.values())
    # Negative mutation: revert sea to original path, must be caught.
    broken=dict(good); broken["SEA_LOW_CAUSEWAY"]=orig["SEA_LOW_CAUSEWAY"]
    assert len(centerline_wall_intersections(broken))>=2
    # Negative mutation: remove sky route must fail exact route contract.
    assert set(k for k in good if k!="SKY_RAMP_RED")!=CORRECTED_ROUTES
    return {"baseline_obstructed_centerlines":hits,
            "patched_centerline_obstructions":fixed,
            "corrected_count":len(good),"Studio_collision_tested":False,
            "geometry_gate":"SOURCE_CENTERLINES_CLEAR_ENGINE_NOT_TESTED"}

def verify_baseline():
    assert SRC.is_dir(),SRC
    old=sorted(SRC.rglob("*.luau"))
    assert len(old)==25,len(old)
    assert len(list(SRC.rglob("Game.server.luau")))==1
    for n,h in BASE.items():
        assert_blob(SRC/n,h)
    source=(SRC/"server/Game.server.luau").read_text()
    overlay=(SRC/"server/H1FunWorld.server.luau").read_text()
    hud=(SRC/"client/HUD.client.luau").read_text()
    assert source.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "WIND_BURST" in source and "WIND_BURST" in hud
    assert "S1RaiderWindRules" in source
    assert "CANONICAL_S1_ENABLED = false" in source
    assert "D07_D08_RELEASE_REVIEW_APPROVED = false" in source
    assert 'Models.create("SPACE"' in overlay
    assert 'Models.create("CELESTIAL"' in overlay
    assert "RemoteEvent" not in overlay and "DataStore" not in overlay
    return overlay

def verify_inputs():
    for name,h in INPUTS.items():
        assert_blob(IN/Path(name).name,h)
    for name in ("H1FunWorld.server.luau","D18MascotGuide.client.luau"):
        assert "RunService:IsStudio()" in (IN/name).read_text()
    guide=(IN/"D18MascotGuide.client.luau").read_text()
    assert "FireServer" not in guide and "DataStore" not in guide
    assert "TRCA-BE-063" in guide
    return (IN/"H1FunWorld.server.luau").read_text()

def assemble():
    original=verify_baseline()
    replacement=verify_inputs()
    geo=check_geometry(original,replacement)
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)
    shutil.copytree(SRC,DST/"src")
    shutil.copyfile(UP/"default.project.json",DST/"default.project.json")
    for name in INPUTS:
        shutil.copyfile(IN/Path(name).name,DST/"src"/name)
    project=json.loads((DST/"default.project.json").read_text())
    project["name"]="TRAP_RAIDERS_H1_WOW_4WAY_STUDIO_ONLY"
    clients=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    for k in ("D18Batch8Catalog","D18MascotGuideRules","D18MascotGuide"):
        assert k not in clients
        file=k+(".client.luau" if k=="D18MascotGuide" else ".luau")
        clients[k]={"$path":"src/client/"+file}
    (DST/"default.project.json").write_text(
        json.dumps(project,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    built=sorted((DST/"src").rglob("*.luau"))
    assert len(built)==28,len(built)
    assert len(list((DST/"src").rglob("Game.server.luau")))==1
    assert len(list((DST/"src").rglob("H1FunWorld.server.luau")))==1
    assert all(blob((DST/"src"/p).read_bytes())==h for p,h in INPUTS.items())
    changed=[]
    for f in sorted(SRC.rglob("*.luau")):
        relative=f.relative_to(SRC)
        if f.read_bytes()!=(DST/"src"/relative).read_bytes():
            changed.append(str(relative))
    assert changed==["server/H1FunWorld.server.luau"],changed
    assert len([p for p in built if p.relative_to(DST/"src").as_posix().startswith("client/")])==7
    receipt={
        "game_id":"TRAP_RAIDERS",
        "stage":"H1_PRIVATE_STUDIO_BUILD_NOT_RELEASE",
        "candidate_id":"P0D-FUN-H1-001",
        "fixed_base_source_sha":PROVENANCE["base_composite_git_commit"],
        "source_pin":PROVENANCE,
        "source_count":28,
        "original_game_source_unchanged_except":["server/H1FunWorld.server.luau"],
        "added_original_D18_client_scripts":3,
        "geometry":geo,
        "not_authorized":{"published":False,"Studio_2client_tested":False,
            "physical_mobile_tested":False,"OWNER_H0_H1_fun_accepted":False,
            "official_RC_adopted":False,"D07_D08_enabled":False},
    }
    (DST/"SOURCE_LOCK.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
        "test":"H1_FOUR_WAY_FULL_SOURCE_28_LUAU_ASSEMBLED",
        "route_source_obstructions":len(geo["patched_centerline_obstructions"]),
        "original_route_obstructions":len(geo["baseline_obstructed_centerlines"]),
        "source_count":28,"owner_Studio_2client":"NOT_TESTED",
        "built_project":str(DST.relative_to(REPO))},ensure_ascii=False))
    return receipt

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--verify",action="store_true")
    parser.add_argument("--assemble",action="store_true")
    args=parser.parse_args()
    if not (args.verify or args.assemble):
        parser.error("--verify or --assemble required")
    if args.verify:
        o=verify_baseline()
        n=verify_inputs()
        print(json.dumps(check_geometry(o,n),indent=2))
    else:
        assemble()
if __name__=="__main__":
    main()
