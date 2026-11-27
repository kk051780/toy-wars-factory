#!/usr/bin/env python3
"""FB030 native86 PR479 parent -> one authoritative Game/HUD Assassin wind patch.

Pinned real parent: PR479 Actions artifact 14161823401; no source overwrite.
"""
from pathlib import Path
from lxml import etree
import argparse, hashlib, json

PARENT_SHA = "11fa894c4ebfa2303e3f7cef8590d14a6a26f359699b6eda3d2e692bc161c707"
PARENT_SIZE = 843641

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def gitblob(src):
    b = src.encode("utf8")
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

def once(src, before, after):
    if src.count(before) != 1:
        raise AssertionError(f"SOURCE_ANCHOR_DRIFT count={src.count(before)}: {before[:120]!r}")
    return src.replace(before, after, 1)

def game_patch(src):
    src = once(src,
'''    local now = serverNow()
    local windInput:any = {
        phase = match.phase, team = team, role = roles[player] or "RAIDER",''',
'''    local now = serverNow()
    -- FB030: In Studio the chosen Assassin can use the ORIGINAL server wind.
    -- Other seven-job roles cannot impersonate RAIDER to get this move.
    -- This is a server-owned selected job; no client job/position/speed authority.
    local selectedJob = RunService:IsStudio() and sevenJobSelected[player] == true
    if selectedJob and sevenJobs[player] ~= "NINJA" then return end
    local windRole = if selectedJob then "RAIDER" else (roles[player] or "RAIDER")
    local windInput:any = {
        phase = match.phase, team = team, role = windRole,''')
    src = once(src,
'''    if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true then
        local grass=map.model:FindFirstChild("GrassArena")''',
'''    if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true
        or RunService:IsStudio() then
        local grass=map.model:FindFirstChild("GrassArena")''')
    src = once(src,
'''        local localPosition=grass.CFrame:PointToObjectSpace(root.Position)
        windInput.adaptiveField=true''',
'''        if RunService:IsStudio() then
            -- Ground proof in real server geometry, not a client-sent coordinate.
            -- Reject airborne exploits and noncolliding visual scenery.
            local rayParams = RaycastParams.new()
            rayParams.FilterType = Enum.RaycastFilterType.Exclude
            rayParams.FilterDescendantsInstances = {player.Character}
            local floorHit = workspace:Raycast(root.Position + Vector3.new(0, 1, 0),
                Vector3.new(0, -8, 0), rayParams)
            if not floorHit or not floorHit.Instance:IsA("BasePart")
                or not floorHit.Instance.Anchored or not floorHit.Instance.CanCollide
                or floorHit.Normal.Y < 0.65 then return end
        end
        local localPosition=grass.CFrame:PointToObjectSpace(root.Position)
        windInput.adaptiveField=true''')
    return src

def hud_patch(src):
    src = once(src,
'''    windButton.Visible = s.phase == "ACTIVE" and s.role == "RAIDER"''',
'''    -- Show the wind button only to the selected Assassin or legacy RAIDER.
    -- Other chosen seven-job roles must not see an unusable wind action.
    local selectedSevenJob = s.jobStudioPvE==true and s.jobSelected==true
    local canWind = (selectedSevenJob and s.job=="NINJA")
        or (not selectedSevenJob and s.role=="RAIDER")
    windButton.Visible = s.phase == "ACTIVE" and canWind''')
    src = once(src,
'''    windButton.Active = s.phase == "ACTIVE" and s.role == "RAIDER"
        and not carryingEgg and windCooldown == 0 and s.windActive ~= true''',
'''    windButton.Active = windButton.Visible
        and not carryingEgg and windCooldown == 0 and s.windActive ~= true''')
    return src

def sources(tree):
    out = {}
    for item in tree.xpath("//Item"):
        props = item.find("Properties")
        if props is None: continue
        name = props.find('string[@name="Name"]')
        src = next((e for e in props if e.get("name") == "Source"), None)
        if name is not None and src is not None:
            if name.text in out: raise AssertionError("DUPLICATE_SCRIPT")
            out[name.text] = src
    return out

def make(parent, output, receipt=None):
    parent, output = Path(parent), Path(output)
    if sha(parent) != PARENT_SHA or parent.stat().st_size != PARENT_SIZE:
        raise AssertionError("PINNED_RC86_PARENT_FAILED")
    tree = etree.parse(str(parent), etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True))
    src = sources(tree)
    if len(src) != 86 or "Game" not in src or "TrapRaidersHUD" not in src:
        raise AssertionError("EXACT_86_SCRIPT_PARENT_REQUIRED")
    before = {n:gitblob(e.text or "") for n,e in src.items()}
    if before["Game"] != "9affc8697c55c1b6d0158216bfa75c4e9fa7e36d":
        raise AssertionError("WRONG_GAME")
    if before["StagePickupLoot"] != "3fb954f4bcc9d5728b55cc284e6519c304bd61c2":
        raise AssertionError("WRONG_STAGE_LOOT")
    if before["UndeadSquad"] != "4d1e7012e8ab2cd5c40ba6e51db1d52bb2812341":
        raise AssertionError("WRONG_UNDEAD")
    if "if s.adaptiveField == true then" not in (src["S1RaiderWindRules"].text or ""):
        raise AssertionError("NATIVE86_WIND_POLICY_MISSING")
    src["Game"].text = game_patch(src["Game"].text or "")
    src["TrapRaidersHUD"].text = hud_patch(src["TrapRaidersHUD"].text or "")
    after = {n:gitblob(e.text or "") for n,e in src.items()}
    changed = [n for n in before if before[n] != after[n]]
    if sorted(changed) != ["Game", "TrapRaidersHUD"]:
        raise AssertionError(f"UNAUTHORIZED_CHANGE {changed}")
    if (src["Game"].text or "").count("remote.OnServerEvent:Connect(") != 1:
        raise AssertionError("SECOND_GAME_AUTHORITY")
    etree.ElementTree(tree.getroot()).write(str(output), encoding="utf-8", xml_declaration=False, pretty_print=True)
    check = sources(etree.parse(str(output), etree.XMLParser(resolve_entities=False,no_network=True)))
    if {n:gitblob(e.text or "") for n,e in check.items()} != after:
        raise AssertionError("WRITTEN_XML_SOURCE_CHANGED")
    result = {"schema":"FB030_RC86_ASSASSIN_WIND", "parent_sha256":PARENT_SHA,
              "output_sha256":sha(output), "output_bytes":output.stat().st_size,
              "source_count":86, "changed":changed, "unchanged":84, "old":before,"new":after,
              "official_rc_write":False, "native_current":"NOT_RUN",
              "studio":"NOT_RUN", "android":"NOT_RUN", "owner":"NOT_APPROVED"}
    if receipt: Path(receipt).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("parent")
    p.add_argument("output")
    p.add_argument("--receipt")
    a = p.parse_args()
    print(json.dumps(make(a.parent,a.output,a.receipt),ensure_ascii=False,indent=2))
