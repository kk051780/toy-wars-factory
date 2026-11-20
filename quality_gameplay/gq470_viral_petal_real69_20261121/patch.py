#!/usr/bin/env python3
"""REAL69 Studio-only visual fix: 8 Neon balls -> 4 matte wedges, A candidate."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET="StarterPlayer/StarterPlayerScripts/GQ8_ViralCapture"
ORIGINAL="51f28c53a5a930225e5eba1668b48f0734b762d50cc74ae8528da3867e75c285"
EXPECTED="3f788b67aa1df39fbf6ea28212cfc36b2121ecc1c51e071ede4fe5afcc1959bd"
FEATURE="GQ470_FB015_VIRAL_CAPTURE_MATTE_PETALS_REAL69_20261121"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
START='    for i = 1, 8 do\n'
END='    end\nend\n\nlocal function stopCapture()'
NEW=f'''    -- {FEATURE}
    -- Four matte facets instead of eight glowing balls. Cosmetic client-only
    -- shapes, no collision/physics/gameplay effect; no additional event loop.
    local MAX_MATTE_FACETS_PER_CUE = 4
    for i = 1, MAX_MATTE_FACETS_PER_CUE do
        local theta = (i - .5) * math.pi / 2
        local shard = Instance.new("WedgePart")
        shard.Name = "GQ8_ViralMomentLocalFX"
        shard.Material = Enum.Material.SmoothPlastic
        shard.Color = cfg.tone:Lerp(Color3.fromRGB(225, 224, 213), .22)
        shard.Size = Vector3.new(.48, .8, .15)
        shard.Anchored = true
        shard.CanCollide = false
        shard.CanTouch = false
        shard.CanQuery = false
        shard.CastShadow = false
        shard.Transparency = .13
        shard.CFrame = CFrame.new(center + Vector3.new(2.65*math.cos(theta), 1.65, 2.65*math.sin(theta)))
            * CFrame.Angles(0, theta, math.rad(if i % 2 == 0 then -18 else 18))
        shard.Parent = workspace
        local anim = TweenService:Create(shard, TweenInfo.new(1.55, Enum.EasingStyle.Quad),
            {{Position = shard.Position + Vector3.new(0, 2.7, 0), Transparency = 1}})
        anim:Play()
        task.delay(1.75, function()
            if shard.Parent then shard:Destroy() end
        end)
    end
'''
def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def transform(s:str)->str:
    assert FEATURE not in s,"RED_DUPLICATE_APPLICATION"
    assert s.count(START)==1 and s.count(END)==1,"RED_ORIGINAL_VISUAL_ANCHORS"
    guard=("if not RunService:IsStudio() then return end",
           'local CaptureService = game:GetService("CaptureService")',
           'CaptureService:StartVideoCaptureAsync',
           'CaptureService:PromptSaveCapturesToGallery',
           'toggle.Activated:Connect(function()',
           'if now - lastCueAt < 2 then return end',
           'glint.CanCollide = false','glint.CanTouch = false',
           'glint.CanQuery = false','glint.Material = Enum.Material.Neon')
    assert all(k in s for k in guard),"RED_CONSENT_OR_PHYSICS_GUARD"
    i=s.index(START)
    j=s.index(END,i)+len('    end\n')
    assert s[i:j].count('Instance.new("Part")')==1,"RED_ORIGINAL_LOOP_NOT_PART"
    assert s[i:j].count("glint.Parent = workspace")==1,"RED_ORIGINAL_VISUAL"
    assert NEW.count('Instance.new("WedgePart")')==1 and 'MAX_MATTE_FACETS_PER_CUE = 4' in NEW
    assert all(k in NEW for k in ('shard.CanCollide = false',
        'shard.CanTouch = false','shard.CanQuery = false',
        'shard.CastShadow = false','shard.Material = Enum.Material.SmoothPlastic'))
    assert all(k not in NEW for k in ('RemoteEvent','OnServerEvent','DataStore',
        'Marketplace','TakeDamage','while true','RunService.RenderStepped'))
    result=s[:i]+NEW+s[j:]
    assert result.count(FEATURE)==1,"RED_MARKER"
    assert result[:i]==s[:i] and result[i+len(NEW):]==s[j:],"RED_OTHER_SOURCE_DRIFT"
    return result

def selected(root:pathlib.Path)->dict:
    project=json.loads((root/PROJECT).read_text())
    found={}
    def walk(node,route=""):
        if not isinstance(node,dict):return
        if "$path" in node:
            p=(root/node["$path"]).resolve()
            assert p.is_relative_to(root.resolve()) and p.is_file(),"RED_PATH"
            assert route not in found,"RED_DUPLICATE_ROUTE"
            found[route]=p
        for k,v in node.items():
            if not k.startswith("$"):walk(v,route+"/"+k if route else k)
    walk(project["tree"])
    assert len(found)==69 and TARGET in found and found[TARGET].name.endswith(".client.luau"),"RED_69_CLASS"
    return found

def apply(base:pathlib.Path,dest:pathlib.Path)->dict:
    assert base.is_dir() and not dest.exists(),"RED_BASE_DEST"
    rec=json.loads((base/RECEIPT).read_text())
    assert rec.get("build_head")==BASE and rec.get("canonical_build") is True,"RED_FORMAL"
    assert len(rec.get("source_hashes",{}))==69,"RED_REC69"
    paths=selected(base)
    for name,path in paths.items():
        assert sha(path.read_bytes())==rec["source_hashes"].get(name),"RED_HASH_"+name
    original=paths[TARGET].read_bytes()
    assert sha(original)==ORIGINAL,"RED_OLD_TARGET"
    updated=transform(original.decode("utf-8")).encode("utf-8")
    assert sha(updated)==EXPECTED,"RED_EXACT_CANDIDATE_SHA"
    shutil.copytree(base,dest)
    paths2=selected(dest)
    paths2[TARGET].write_bytes(updated)
    assert [k for k in paths if paths[k].read_bytes()!=paths2[k].read_bytes()]==[TARGET],"RED_68_SCOPE"
    for f in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        assert (base/f).read_bytes()==(dest/f).read_bytes(),"RED_BASE_CHANGED"
    qa={"feature":FEATURE,"formal":BASE,"selected":69,"changed":1,"unchanged":68,
        "target":TARGET,"target_class":"LocalScript",
        "old_sha256":ORIGINAL,"new_sha256":EXPECTED,
        "old_source_bytes":len(original),"new_source_bytes":len(updated),
        "old_parts_per_cue":8,"new_parts_per_cue":4,
        "new_remotes":0,"authority_changed":False,
        "studio":"NOT_TESTED","android":"NOT_TESTED","art_png":"0/32",
        "owner_accepted":False}
    (dest/"GQ470_VIRAL_PETAL_SOURCE_QA.json").write_text(json.dumps(qa,indent=2)+"\n")
    return qa

def self_test():
    source=("if not RunService:IsStudio() then return end\n"
       'local CaptureService = game:GetService("CaptureService")\n'
       'CaptureService:StartVideoCaptureAsync\n'
       'CaptureService:PromptSaveCapturesToGallery\n'
       'toggle.Activated:Connect(function()\n'
       'if now - lastCueAt < 2 then return end\n'
       'local function visual()\n'
       + START +
       '''        local glint = Instance.new("Part")
        glint.Material = Enum.Material.Neon
        glint.CanCollide = false
        glint.CanTouch = false
        glint.CanQuery = false
        glint.Parent = workspace
''' + END)
    good=transform(source)
    assert FEATURE in good and 'MAX_MATTE_FACETS_PER_CUE = 4' in good
    mutants=[good,source.replace(START,""),source.replace(END,""),
             source.replace('glint.CanCollide = false','glint.CanCollide = true'),
             source.replace('glint.CanTouch = false','glint.CanTouch = true'),
             source.replace('glint.CanQuery = false','glint.CanQuery = true'),
             source.replace('glint.Material = Enum.Material.Neon',''),
             source.replace('CaptureService:StartVideoCaptureAsync',''),
             source.replace('toggle.Activated:Connect(function()',''),
             source.replace('if not RunService:IsStudio() then return end','')]
    for m in mutants:
        try:transform(m)
        except AssertionError:continue
        raise AssertionError("RED_ACCEPTED_MUTANT")
    print("GQ470_VIRAL_MATTE_10_NEGATIVE_MUTANTS_PASS")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--source",type=pathlib.Path)
    a.add_argument("--dest",type=pathlib.Path)
    args=a.parse_args()
    if args.self_test:self_test()
    else:
        assert args.source and args.dest
        print(json.dumps(apply(args.source,args.dest),indent=2))
