"""Reuse the existing ACTIVE touch layout against the selected HUD."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_touch_attack"
HUD = "client/HUD.client.luau"
FEATURE = "ACTIVE_TOUCH_ATTACK_LAYOUT_V2"


def mounted_layout():
    geometry = (PACKAGE / "touch-layout.luau").read_text(encoding="utf-8")
    bridge = (PACKAGE / "touch-ui.luau").read_text(encoding="utf-8")
    bridge = patch(bridge, [
        {"anchor": "local attackDesktopSize, attackDesktopPosition, attackDesktopText = attack.Size, attack.Position, attack.Text\nlocal touchActive = false",
         "replace": "local attackDesktopSize, attackDesktopPosition = attack.Size, attack.Position"},
        {"anchor": "        attack.Size, attack.Position, attack.Text = attackDesktopSize, attackDesktopPosition, attackDesktopText\n        touchActive = false",
         "replace": "        attack.Size, attack.Position = attackDesktopSize, attackDesktopPosition\n        touchAttackActive = false\n        refreshAttackCaption()"},
        {"anchor": "    if not UserInputService.TouchEnabled and not touchActive then return end",
         "replace": "    if not UserInputService.TouchEnabled and not touchAttackActive then\n"
                    "        attack.Visible = attackInBattle\n        return\n    end"},
        {"anchor": '    if not attackInBattle or not jump or not jump:IsA("GuiButton") then return end',
         "replace": '    if not attackInBattle or not jump or not jump:IsA("GuiButton") then\n'
                    '        attack.Visible = false\n        return\n    end'},
        {"anchor": '        attack.Text = "攻撃"', "replace": '        refreshAttackCaption()'},
    ]).replace("touchActive", "touchAttackActive")
    return geometry + "\n" + bridge


def apply(dist,profile="rich51",enabled_override=None):
    if profile!="rich51":
        return False
    pins = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = pins["enabled"] if enabled_override is None else enabled_override
    assert type(enabled) is bool and pins["profile"]==profile and pins["feature"]==FEATURE
    if not enabled:
        return False
    before = sources(dist)
    identities = {name: gitblob(raw) for name, raw in before.items()}
    source_path, feature_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, features = (json.loads(path.read_bytes()) for path in (source_path, feature_path))
    assert len(before) == lock["total_scripts"] == features["total_sources"] == 69
    assert identities == lock["blobs"] == features["source_gitblobs"]
    route = pins["routes"][HUD]
    assert identities[HUD] == route["before"] == lock["rc_active_assassin_wind"]["routes"][HUD]["after"]
    assert all(hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest()==pins["original"][name]
               for name in ("touch-layout.luau","touch-ui.luau"))
    hud = before[HUD].decode("utf-8")
    updated = patch(hud, [
        {"anchor": "local attackFeedbackVersion = 0\nlocal function flashConfirmedAttack",
         "replace": "local attackFeedbackVersion = 0\n"
                    "local touchAttackActive = false\nlocal attackCueFlashing = false\n"
                    "local function refreshAttackCaption()\n"
                    '    if not attackCueFlashing then attack.Text = if touchAttackActive then "攻撃" else originalAttackText end\n'
                    "end\nlocal function flashConfirmedAttack"},
        {"anchor": "    local version = attackFeedbackVersion\n    attack.Text = message",
         "replace": "    local version = attackFeedbackVersion\n    attackCueFlashing = true\n    attack.Text = message"},
        {"anchor": "            attack.Text = originalAttackText\n            attack.BackgroundColor3 = originalAttackColor",
         "replace": "            attackCueFlashing = false\n            refreshAttackCaption()\n"
                    "            attack.BackgroundColor3 = originalAttackColor"},
        {"anchor": "remote.OnClientEvent:Connect(function(s)\n",
         "replace": mounted_layout() + "\nremote.OnClientEvent:Connect(function(s)\n"},
        {"anchor": '    attack.Visible = s.phase == "ACTIVE"',
         "replace": '    attackInBattle = s.phase == "ACTIVE"'},
        {"anchor": '        else "🌪 風走り\\nRキー"\nend)',
         "replace": '        else "🌪 風走り\\nRキー"\n    layoutTouchAttack()\nend)'},
    ]).encode("utf-8")
    assert updated.count(b'attack.Activated:Connect(function() action("ATTACK", nil) end)')==1
    assert updated.count(b'jobCast.MouseButton1Click:Connect(function() action("JOB_SKILL",nil) end)')==1
    assert gitblob(updated)==route["after"]
    (dist / "src" / HUD).write_bytes(updated)
    assert sources(dist) == before | {HUD: updated}
    receipt={"feature":FEATURE,"profile":profile,"source":HUD,"before":route["before"],
             "after":route["after"],"original":pins["original"],"off_place":pins["off_place"],
             "android":"NOT_TESTED"}
    identities[HUD] = receipt["after"]
    lock.update(blobs=identities, rc_active_touch_attack=receipt)
    features.update(source_gitblobs=identities, rc_active_touch_attack=receipt)
    write_json(source_path, lock)
    write_json(feature_path, features)
    print(json.dumps(receipt))
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist",type=Path,required=True)
    parser.add_argument("--profile",choices=("rich51","rich47","legacy21"),required=True)
    parser.add_argument("--off-place",type=Path)
    args=parser.parse_args()
    pins=json.loads((PACKAGE / "source_lock.json").read_bytes())
    if args.profile==pins["profile"] and pins["enabled"] is True:
        if args.off_place is None:
            parser.error("--off-place required for enabled rich51")
        raw=args.off_place.read_bytes()
        assert {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}==pins["off_place"]
        print("ACTIVE_TOUCH_ATTACK_IMMEDIATE_OFF_EXACT")
    apply(args.dist,args.profile)
