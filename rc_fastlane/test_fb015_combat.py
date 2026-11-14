#!/usr/bin/env python3
"""Actual FB-008/015 source-locked overlay / transactional rollback tests.

The native Luau generator separately runs the REAL client cue policy;
these Python tests do NOT claim Roblox Studio, networking or visuals.
"""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("p0d_art_combat", ROOT / "apply_fb015_combat.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def original_horde() -> bytes:
    s = mod.HORDE_AUTHOR.read_text("utf8")
    header='''-- No RemoteEvent, no task scheduler, no XP/egg/score/damage-player authority.
local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))'''
    new_header='''-- In Studio only: one outbound cosmetic RemoteEvent + visual-only spark cue.
-- No OnServerEvent listener, scheduler, XP/egg/score/damage-player authority.
local RunService=game:GetService("RunService")
local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))'''
    old_ctor='''    folder.Parent=world
    return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0},Horde)'''
    new_ctor='''    folder.Parent=world
    -- Studio-only outbound visuals; live servers create/send no unused packet.
    local visualCue=nil
    if RunService:IsStudio() then
        visualCue=Instance.new("RemoteEvent")
        visualCue.Name="P0D_ART_COMBAT_SIGNAL_V1"
        visualCue.Parent=folder
    end
    return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0,artCue=visualCue},Horde)'''
    seam='                    m.body.Color=Color3.fromRGB(253,231,111)'
    hit='''
                    -- Every confirmed hit produces BOTH a reliable Studio client
                    -- arc packet and a synchronous server-only 3D spark cue.
                    -- Never allow the cosmetic Remote to accept client traffic.
                    if self.artCue then
                        m.artHitSeq=(m.artHitSeq or 0)+1
                        self.artCue:FireAllClients(m.id,m.pos,origin,m.hp<=0,m.artHitSeq,self.round)
                        m.body:SetAttribute("P0D_ART_SPARK_V1",
                            tostring(m.artHitSeq).."|"..(if m.hp<=0 then "K" else "H"))
                    end'''
    raw = s.replace(new_header,header).replace(new_ctor,old_ctor).replace(seam+hit,seam).encode("utf8")
    if raw == s.encode("utf8") or mod.blob(raw) != mod.ORIGINAL_HORDE_PIN:
        raise RuntimeError("BAD_HORDE_TEST_FIXTURE_EXACT_RECONSTRUCTION")
    return raw

def snapshot(base: Path):
    return {p.relative_to(base).as_posix(): p.read_bytes()
            for p in base.rglob("*") if p.is_file()}

def fixture(root: Path):
    dist=root/"dist"
    items={
        "server/MusouHorde.luau":original_horde(),
        "server/Game.server.luau":b'remote.OnServerEvent:Connect(function() end)',
    }
    items.update({f"shared/MOCK_{i:02d}.luau":f"return {i}\n".encode() for i in range(64)})
    assert len(items)==66
    for name,raw in items.items():
        p=dist/"src"/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(raw)
    pins={name:mod.blob(raw) for name,raw in sorted(items.items())}
    (dist/"SOURCE_LOCK.json").write_text(json.dumps({
        "total_scripts":66,"blobs":pins,"unchanged":"keep"}))
    (dist/"RC_FEATURE_LOCK.json").write_text(json.dumps({
        "total_sources":66,"source_gitblobs":pins,"feature_flags":{}}))
    (dist/"default.project.json").write_text(json.dumps({"tree":{
        "StarterPlayer":{"StarterPlayerScripts":{
            "ResultNextStep":{"$path":"src/client/ResultNextStep.client.luau"}}},
        "ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}}
    }}))
    return dist

class ArtCombatQA(unittest.TestCase):
    def test_exact_sources_and_server_outbound_only(self):
        self.assertEqual(mod.blob(mod.AUTHOR.read_bytes()),mod.PIN)
        self.assertEqual(mod.blob(mod.HORDE_AUTHOR.read_bytes()),mod.HORDE_PATCH_PIN)
        mod.validate_visual(mod.AUTHOR.read_bytes())
        mod.validate_horde_patch(original_horde(),mod.HORDE_AUTHOR.read_bytes())
        h=mod.HORDE_AUTHOR.read_text()
        self.assertIn('self.artCue:FireAllClients(m.id,m.pos,origin,m.hp<=0,m.artHitSeq,self.round)',h)
        self.assertNotIn("OnServerEvent:Connect(",h)
        self.assertEqual(h.count('Instance.new("RemoteEvent")'),1)
        self.assertIn("if RunService:IsStudio() then",h)
        self.assertIn('m.body:SetAttribute("P0D_ART_SPARK_V1"',h)
        self.assertIn("if self.artCue then",h)

    def test_client_only_observes_outbound_hit_and_limit(self):
        s=mod.AUTHOR.read_text()
        self.assertIn('cue.OnClientEvent:Connect(onConfirmedHit)',s)
        self.assertIn('if not acceptVisualCue(id,serial,round) then return end',s)
        self.assertIn('makeArc(hitPos,fromPos,isKO)',s)
        self.assertIn('if UserInputService.TouchEnabled then 1 else 2',s)
        self.assertIn("MAX_BURSTS_PER_SECOND = 9",s)
        self.assertIn("MAX_LIVE = 8",s)
        self.assertNotIn("FireServer(",s)
        self.assertNotIn("GetAttributeChangedSignal(",s)
        self.assertNotIn("OnServerEvent:Connect(",s)

    def test_clean_off_then_on_then_exact_off_and_locks(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            before=snapshot(d)
            self.assertFalse(mod.apply(d,False))
            self.assertEqual(snapshot(d),before)
            self.assertTrue(mod.apply(d,True))
            self.assertEqual(len(mod.sources(d)),67)
            self.assertTrue(mod.backup_dir(d).is_dir())
            feature=json.loads((d/"RC_FEATURE_LOCK.json").read_text())
            self.assertTrue(feature["feature_flags"][mod.FEATURE])
            self.assertEqual(mod.sources(d)["server/Game.server.luau"],
                             before["src/server/Game.server.luau"])
            self.assertTrue(mod.apply(d,False))
            self.assertEqual(snapshot(d),before)
            self.assertFalse(mod.backup_dir(d).exists())

    def test_bad_backup_does_not_destroy_known_good_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            mod.apply(d,True)
            candidate=snapshot(d)
            original=mod.backup_dir(d)
            h=original/"src/server/MusouHorde.luau"
            h.write_bytes(h.read_bytes()+b"CORRUPT")
            with self.assertRaisesRegex(RuntimeError,"ORIGINAL_HORDE_DRIFT"):
                mod.apply(d,False)
            self.assertEqual(snapshot(d),candidate)
            self.assertTrue(original.exists())

    def test_interrupted_off_state_can_recover(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            before=snapshot(d)
            mod.apply(d,True)
            interrupted=d.with_name(d.name+".art_combat_disabling")
            os.rename(d,interrupted)  # crash after disabled rename
            self.assertTrue(mod.apply(d,False))
            self.assertEqual(snapshot(d),before)
            self.assertFalse(interrupted.exists())
            self.assertFalse(mod.backup_dir(d).exists())

    def test_interrupted_off_cleanup_can_recover(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            before=snapshot(d)
            mod.apply(d,True)
            interrupted=d.with_name(d.name+".art_combat_disabling")
            os.rename(d,interrupted)
            os.rename(mod.backup_dir(d),d)  # crash before removing disabled
            self.assertTrue(mod.apply(d,False))
            self.assertEqual(snapshot(d),before)
            self.assertFalse(interrupted.exists())

    def test_optimized_python_still_rejects_bad_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            original=d/"src/server/MusouHorde.luau"
            original.write_bytes(original.read_bytes()+b"DRIFT")
            before=snapshot(d)
            env=os.environ.copy()
            env["PYTHONOPTIMIZE"]="1"
            p=subprocess.run([sys.executable,"-O",str(ROOT/"apply_fb015_combat.py"),
                 "--dist",str(d),"--enabled","true"],
                 env=env,text=True,capture_output=True)
            self.assertNotEqual(p.returncode,0,p.stdout)
            self.assertIn("ORIGINAL_HORDE_DRIFT",p.stderr)
            self.assertEqual(snapshot(d),before)

    def test_uninstalled_off_is_true_zero_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/"missing"
            self.assertFalse(mod.apply(d,False))
            self.assertFalse(d.exists())

    def test_source_drift_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"ART_COMBAT_SOURCE_DRIFT"):
            mod.validate_visual(mod.AUTHOR.read_bytes()+b"MALFORMED")

if __name__=="__main__":
    unittest.main()
