#!/usr/bin/env python3
"""FB019 negative and source-preservation tests; engine gameplay is not simulated."""
import json,tempfile,unittest
from pathlib import Path
from apply_fb019_swing_feedback import TARGET,FEATURE,read,blob,patch,apply

HUD_ORIGINAL='''--!strict
local b = Instance.new("TextButton")
b.Text = text
local attack = button(gui, "Attack", "攻撃", UDim2.fromOffset(126, 88), UDim2.new(1, -140, 1, -16), Color3.new(1,1,1))
local seq = 0
local function action(kind: string, role: string?)
    seq += 1
    remote:FireServer({action = kind, role = role, seq = seq})
end
attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)
UserInputService.InputBegan:Connect(function(input, processed)
    if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil)
    end
end)
remote.OnClientEvent:Connect(function(s)
    if s.kind ~= "SNAPSHOT" then return end
    lastSerial = s.serial
end)
'''
class TestFeedback(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        folder=Path(self.temp.name)
        self.base=folder/"base";self.out=folder/"out"
        src=self.base/"src";(src/"client").mkdir(parents=True)
        (src/"server").mkdir(parents=True)
        (src/TARGET).write_text(HUD_ORIGINAL,"utf8")
        (src/"server/Game.server.luau").write_text("--original game\n")
        for i in range(78):
            (src/"server"/f"INERT_{i:02d}.luau").write_text(f"--{i}\n")
        pins={p:blob(x) for p,x in read(self.base).items()}
        assert len(pins)==80
        sl={"total_scripts":80,"blobs":pins}
        fl={"total_sources":80,"source_gitblobs":pins,
            "feature_flags":{
                "FB016_FOLIAGE_PASSAGE_20261114":True,
                "FB017_NO_PERSISTENT_BATTLE_GUIDES":True,
                "FB018_ACTION_BUTTON_TEXT_INIT":True,
            },
            "fb018_button_label":{"new_hud_blob":pins[TARGET]}}
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps(sl))
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl))
    def tearDown(self):self.temp.cleanup()
    def test_input_and_server_authority_untouched(self):
        out=patch(HUD_ORIGINAL.encode()).decode()
        self.assertEqual(out.count('remote:FireServer({action = kind, role = role, seq = seq})'),1)
        self.assertEqual(out.count('action("ATTACK", nil)'),2)
        self.assertIn('fb019InBattle = s.phase == "ACTIVE"',out)
        self.assertIn('fb019ShowSwing()',out)
        self.assertNotIn("TakeDamage(",out)
        self.assertNotIn('Instance.new("RemoteEvent")',out)
    def test_no_new_gui_remote_or_fake_damage(self):
        output=patch(HUD_ORIGINAL.encode()).decode()
        self.assertEqual(output.count('Instance.new("Beam")'),1)
        self.assertIn('if not fb019InBattle',output)
        self.assertIn('fb019Debris:AddItem(beam, .22)',output)
        self.assertNotIn('Instance.new("RemoteEvent")',output)
        self.assertNotIn('Instance.new("ScreenGui")',output)
        self.assertEqual(output.count('remote:FireServer({action = kind, role = role, seq = seq})'),1)
    def test_disable_zero_write(self):
        before=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(before,read(self.base))
    def test_only_one_hud_replacement(self):
        before=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read(self.out)
        self.assertEqual({p for p in before if before[p]!=after[p]},{TARGET})
        self.assertEqual(before["server/Game.server.luau"],after["server/Game.server.luau"])
        self.assertTrue(json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())["feature_flags"][FEATURE])
        self.assertEqual(before,read(self.base))
    def test_source_drift_fails_closed(self):
        p=self.base/"src"/TARGET
        p.write_text(p.read_text()+"-- break the required input marker\n")
        p.write_text(p.read_text().replace("attack.MouseButton1Click:Connect","attack.NotARealClick:Connect"))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_old_lock_mismatch_fails_closed(self):
        p=self.base/"RC_FEATURE_LOCK.json"
        obj=json.loads(p.read_text())
        obj["fb018_button_label"]["new_hud_blob"]="0"*40
        p.write_text(json.dumps(obj))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_duplicate_action_marker_fails_closed(self):
        mock=HUD_ORIGINAL.replace("local function action(kind: string, role: string?)",
                                  "local function action(kind: string, role: string?)\nlocal function action(kind: string, role: string?)")
        with self.assertRaises(AssertionError):patch(mock.encode())
if __name__=="__main__":unittest.main()
