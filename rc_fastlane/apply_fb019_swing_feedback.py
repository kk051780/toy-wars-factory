#!/usr/bin/env python3
"""FB-019 P0 source-locked visual feedback for ATTACK intent on RC80.
This is a limited symptom fix: never interpret client swing as confirmed damage.
Only B #220 may approve official RC admission; this builds PRIVATE candidate.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path

TARGET = "client/HUD.client.luau"
FEATURE = "FB019_ATTACK_INPUT_SWING_FEEDBACK_V1"
SOURCE_COUNT = 80
BASE_RC = "a47abf05b1d8b5463ee5f5ad3073492e17c03746"
ACTION = "local function action(kind: string, role: string?)"
FIRE = "    remote:FireServer({action = kind, role = role, seq = seq})"
SNAP = "    lastSerial = s.serial"
HELPER = '''-- FB019_ATTACK_SWING_INTENT_ONLY: visual input acknowledgement, NOT a hit.
-- No new attack authority, damage, targets, Remote, HUD labels or persistent guides.
local fb019TweenService = game:GetService("TweenService")
local fb019Debris = game:GetService("Debris")
local fb019InBattle = false
local fb019LastSwingAt = -100
local function fb019ShowSwing()
    if not fb019InBattle or not game:GetService("RunService"):IsStudio() then return end
    local now = os.clock()
    if now - fb019LastSwingAt < .20 then return end
    fb019LastSwingAt = now
    -- A short pulse of the existing attack button; no additional ScreenGui.
    local normal = attack.BackgroundColor3
    attack.BackgroundColor3 = Color3.fromRGB(255, 164, 114)
    fb019TweenService:Create(attack, TweenInfo.new(.16),
        {BackgroundColor3 = normal}):Play()
    local avatar = player.Character
    local root = if avatar then avatar:FindFirstChild("HumanoidRootPart") else nil
    if not root or not root:IsA("BasePart") then return end
    -- Light-weight client-local blade sweep follows the player's own avatar.
    -- This means "input received", not "enemy was damaged".
    local a0 = Instance.new("Attachment")
    a0.Position = Vector3.new(-.95, 1.10, -1.85)
    a0.Parent = root
    local a1 = Instance.new("Attachment")
    a1.Position = Vector3.new(1.18, 1.50, -2.20)
    a1.Parent = root
    local beam = Instance.new("Beam")
    beam.Attachment0 = a0
    beam.Attachment1 = a1
    beam.FaceCamera = true
    beam.Width0 = .24
    beam.Width1 = .08
    beam.CurveSize0 = 1.35
    beam.CurveSize1 = -.45
    beam.LightEmission = .30
    beam.Color = ColorSequence.new(Color3.fromRGB(234, 241, 255))
    beam.Transparency = NumberSequence.new(.18)
    beam.Parent = root
    fb019TweenService:Create(a0, TweenInfo.new(.15, Enum.EasingStyle.Quad,
        Enum.EasingDirection.Out), {Position = Vector3.new(1.10, 1.26, -2.10)}):Play()
    fb019TweenService:Create(beam, TweenInfo.new(.18),
        {Width0 = 0, Width1 = 0}):Play()
    fb019Debris:AddItem(a0, .22)
    fb019Debris:AddItem(a1, .22)
    fb019Debris:AddItem(beam, .22)
end

'''

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def read(root: Path) -> dict[str, bytes]:
    assert root.is_dir() and not root.is_symlink()
    for path in root.rglob("*"):
        assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), ("UNSAFE_PATH", path)
    src = root / "src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def once(src: str, old: str, new: str) -> str:
    assert src.count(old) == 1, ("FB019_SOURCE_DRIFT", old, src.count(old))
    return src.replace(old, new, 1)

def patch(raw: bytes) -> bytes:
    code = raw.decode("utf8")
    assert FEATURE not in code and "FB019_ATTACK_SWING_INTENT_ONLY" not in code
    assert 'b.Text = text' in code, "FB018_NOT_PRESENT"
    assert 'attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)' in code
    assert 'if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil)' in code
    code = once(code, ACTION, HELPER + ACTION)
    code = once(code, FIRE, '    if kind == "ATTACK" then fb019ShowSwing() end\n' + FIRE)
    code = once(code, SNAP, SNAP + '\n    fb019InBattle = s.phase == "ACTIVE"')
    assert code.count(FIRE)==1 and code.count("fb019ShowSwing()")==2
    assert code.count('action("ATTACK", nil)')>=2
    assert code.count('remote:FireServer({action = kind, role = role, seq = seq})') == 1
    assert "TakeDamage(" not in HELPER and "FireServer(" not in HELPER
    assert "ScreenGui" not in HELPER and "TextLabel" not in HELPER
    return code.encode("utf8")

def apply(base: Path, out: Path, enabled: bool) -> bool:
    if not enabled:
        assert not out.exists(), "FB019_OFF_ZERO_WRITES"
        print("FB019_OFF_ZERO_WRITES_PASS")
        return False
    base = base.resolve()
    out = out.absolute()
    assert out.parent.is_dir() and not out.exists() and not out.is_relative_to(base)
    original = read(base)
    assert len(original)==SOURCE_COUNT and TARGET in original
    assert "server/Game.server.luau" in original
    original_pins = {p:blob(data) for p,data in sorted(original.items())}
    sl = json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl = json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==SOURCE_COUNT
    assert sl["blobs"]==fl["source_gitblobs"]==original_pins, "SOURCE_LOCK_DRIFT"
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"] is True
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"] is True
    assert fl["feature_flags"]["FB018_ACTION_BUTTON_TEXT_INIT"] is True
    assert fl["fb018_button_label"]["new_hud_blob"]==original_pins[TARGET], "FB018_VERIFIED_PIN_DRIFT"
    assert FEATURE not in fl["feature_flags"]
    replacement = patch(original[TARGET])
    after = dict(original)
    after[TARGET] = replacement
    assert len(after)==SOURCE_COUNT
    assert {p for p in original if original[p]!=after[p]}=={TARGET}
    new_pins = {p:blob(raw) for p,raw in sorted(after.items())}
    receipt = {
        "feature":FEATURE,"feedback":"FB-019","base_rc":BASE_RC,
        "stage":"A_PREP_PRIVATE_ONLY","script_count":80,
        "changed_sources":[TARGET],"other_79_byte_exact":True,
        "old_source_blob":original_pins[TARGET],"new_source_blob":new_pins[TARGET],
        "only_visual_input_feedback":True,"attack_server_damaging_behavior_changed":False,
        "only_one_remote_fire":True,"no_persistent_guide":True,
        "source_lock_checked":True,"rollback":"omit overlay to recover original RC80 FB018 HUD",
        "studio_pc":"NOT_TESTED","android_touch":"NOT_TESTED",
        "attack_damage_end_to_end":"NOT_TESTED","owner_fun":"FUN_NO_GO",
        "formal_rc_adoption":False,
    }
    sl["blobs"]=new_pins
    sl["fb019_attack_swing_feedback"]=receipt
    fl["source_gitblobs"]=new_pins
    fl["feature_flags"][FEATURE]=True
    fl["fb019_attack_swing_feedback"]=receipt
    temporary=Path(tempfile.mkdtemp(prefix=".fb019_",dir=str(out.parent)))
    staged=temporary/"dist"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/TARGET).write_bytes(replacement)
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==original
        os.replace(staged,out)
    finally:
        shutil.rmtree(temporary,ignore_errors=True)
    print("FB019_PRIVATE_RC80_ONE_HUD_PATCH_79_BYTE_EXACT_PASS")
    return True

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--enabled",required=True,choices=("true","false"))
    a=ap.parse_args()
    apply(a.base,a.out,a.enabled=="true")
