#!/usr/bin/env python3
"""Actual FB-008/015 source-locked overlay / transactional rollback tests.

The native Luau generator separately runs the REAL client cue policy;
these Python tests do NOT claim Roblox Studio, networking or visuals.
"""
from __future__ import annotations
import importlib.util
import ast
import inspect
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
    # Extract authored exact seam literals from the real adapter, then verify
    # the reconstructed original against the independent original Git blob.
    source = ast.parse(inspect.getsource(mod.validate_horde_patch)).body[0]
    keys = {"header","new_header","old_ctor","new_ctor","old_reset","new_reset","helper","seam","extra"}
    vals = {}
    for line in source.body:
        if isinstance(line, ast.Assign) and len(line.targets)==1:
            t=line.targets[0]
            if isinstance(t,ast.Name) and t.id in keys:
                vals[t.id]=ast.literal_eval(line.value)
    if vals.keys()!=keys:
        raise RuntimeError("INCOMPLETE_ORIGINAL_HORDE_SEAMS")
    patched=mod.HORDE_AUTHOR.read_text("utf8")
    restored=(patched.replace(vals["new_header"], vals["header"])
                    .replace(vals["helper"],"")
                    .replace(vals["new_ctor"], vals["old_ctor"])
                    .replace(vals["new_reset"], vals["old_reset"])
                    .replace(vals["seam"]+vals["extra"], vals["seam"])).encode("utf8")
    if restored==patched.encode("utf8") or mod.blob(restored)!=mod.ORIGINAL_HORDE_PIN:
        raise RuntimeError("BAD_HORDE_TEST_FIXTURE_EXACT_RECONSTRUCTION")
    return restored

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
        self.assertIn('self.artCue:FireAllClients(',h)
        self.assertIn('self.artEpoch',h)
        self.assertIn('P0D_ART_VISUAL_CUE_NON_BLOCKING',h)
        self.assertIn('P0D_ART_RECENT_HISTORY_NON_BLOCKING',h)
        self.assertIn('pcall(function()',h)
        self.assertIn('P0D_ART_RECENT_V1',h)
        self.assertIn('HttpService:JSONEncode(self.artRecent)',h)
        self.assertIn('self.artEpoch+=1',h)
        self.assertNotIn("OnServerEvent:Connect(",h)
        self.assertEqual(h.count('Instance.new("RemoteEvent")'),1)
        self.assertIn("if RunService:IsStudio() then",h)
        self.assertIn('self.artHitBus:Fire(m.body,m.artHitSeq,m.hp<=0,self.round)',h)
        self.assertIn('Instance.new("BindableEvent")',h)
        self.assertNotIn('P0D_ART_SPARK_V1',h)
        self.assertIn("if self.artCue and self.artHitBus then",h)

    def test_client_only_observes_outbound_hit_and_limit(self):
        s=mod.AUTHOR.read_text()
        self.assertIn('cue.OnClientEvent:Connect(onConfirmedHit)',s)
        self.assertIn('if not acceptVisualCue(id,serial,round,epoch) then return end',s)
        self.assertIn('if isEpochStale(authoritativeEpoch,epoch) then return end',s)
        self.assertIn('if not admitPacketEpoch(epoch) then return end',s)
        self.assertIn('if pending[i][7]<highestPacketEpoch then table.remove(pending,i) end',s)
        self.assertIn('historyConnection=cue:GetAttributeChangedSignal("P0D_ART_RECENT_V1")',s)
        self.assertIn('HttpService:JSONDecode(encoded)',s)
        self.assertIn("syncServerEpoch()",s)
        self.assertIn("characterConnection=localPlayer.CharacterAdded:Connect(",s)
        self.assertIn("sparks:Emit(if isKO then 10 else 4)",s)
        self.assertIn("state.seen[serial]",s)
        self.assertIn("if not root then",s)
        self.assertIn('if lastEpoch~=nil and epoch<lastEpoch then return false end',s)
        self.assertIn('makeArc(hitPos,fromPos,isKO)',s)
        self.assertIn('if UserInputService.TouchEnabled then 1 else 2',s)
        self.assertIn("MAX_BURSTS_PER_SECOND = 9",s)
        self.assertIn("MAX_LIVE = 8",s)
        self.assertNotIn("FireServer(",s)
        self.assertIn('GetAttributeChangedSignal("P0D_ART_RECENT_V1")',s)
        self.assertNotIn('GetAttributeChangedSignal("P0D_ART_SPARK_V1")',s)
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
            with self.assertRaisesRegex(RuntimeError,"ART_COMBAT_SAVED_ORIGINAL_EXTRA_OR_CHANGED_FILE"):
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

    def test_candidate_added_file_refuses_off_and_retains_user_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            mod.apply(d,True)
            added=d/"IMPORTANT_UNRELATED.txt"
            added.write_text("KEEP_THIS",encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,
                "ART_COMBAT_CANDIDATE_EXTRA_OR_CHANGED_FILE"):
                mod.apply(d,False)
            self.assertEqual(added.read_text("utf8"),"KEEP_THIS")
            added.unlink()
            self.assertTrue(mod.apply(d,False))

    def test_saved_original_added_file_refuses_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            mod.apply(d,True)
            user_file=mod.backup_dir(d)/"IMPORTANT_ORIGINAL.txt"
            user_file.write_text("DO_NOT_DELETE",encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,
                "ART_COMBAT_SAVED_ORIGINAL_EXTRA_OR_CHANGED_FILE"):
                mod.apply(d,False)
            self.assertEqual(user_file.read_text("utf8"),"DO_NOT_DELETE")
            user_file.unlink()
            self.assertTrue(mod.apply(d,False))

    def test_empty_user_directory_is_not_deleted_by_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            mod.apply(d,True)
            user_dir=d/"IMPORTANT_EMPTY_FOLDER"
            user_dir.mkdir()
            with self.assertRaisesRegex(RuntimeError,
                "ART_COMBAT_CANDIDATE_EXTRA_OR_CHANGED_FILE"):
                mod.apply(d,False)
            self.assertTrue(user_dir.is_dir())
            user_dir.rmdir()
            self.assertTrue(mod.apply(d,False))

    def test_mode_changes_are_not_deleted_by_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            mod.apply(d,True)
            f=d/"src/client/ArtCombatSlash.client.luau"
            initial=f.stat().st_mode & 0o777
            f.chmod(0o600 if initial != 0o600 else 0o644)
            with self.assertRaisesRegex(RuntimeError,
                "ART_COMBAT_CANDIDATE_EXTRA_OR_CHANGED_FILE"):
                mod.apply(d,False)
            f.chmod(initial)
            self.assertTrue(mod.apply(d,False))

    def test_preflight_symlink_refused_before_copying(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            escape=root/"EXTERNAL"
            escape.mkdir()
            (escape/"secret.txt").write_text("not part of game")
            link=d/"DANGEROUS_LINK"
            link.symlink_to(escape, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,"FB015_SYMLINK_ENTRY_REFUSED"):
                mod.apply(d,True)
            self.assertFalse(mod.backup_dir(d).exists())
            self.assertTrue(link.is_symlink())
            self.assertEqual((escape/"secret.txt").read_text(),"not part of game")

    def test_coedited_in_tree_manifest_cannot_authorize_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            mod.apply(d,True)
            user=d/"OWNER_UNRELATED_NOT_FOR_DELETE.txt"
            user.write_text("preserve",encoding="utf8")
            manifest=d/mod.TRANSACTION
            original=manifest.read_bytes()
            hacked=json.loads(manifest.read_text("utf8"))
            hacked["candidate"]=mod.whole_tree(d,exclude=mod.TRANSACTION)
            manifest.write_text(json.dumps(hacked),encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,"ART_COMBAT_CANDIDATE_EXTRA_OR_CHANGED_FILE"):
                mod.apply(d,False)
            self.assertEqual(user.read_text("utf8"),"preserve")
            user.unlink()
            manifest.write_bytes(original)
            self.assertTrue(mod.apply(d,False))

    def test_reserved_manifest_in_original_must_restore_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            reserved=d/mod.TRANSACTION
            reserved.write_text("ORIGINAL_OWNER_BYTES",encoding="utf8")
            mod.apply(d,True)
            backup=mod.backup_dir(d)
            original=backup/mod.TRANSACTION
            original.write_text("ALTERED_ORIGINAL_OWNER_BYTES",encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,"ART_COMBAT_SAVED_ORIGINAL_EXTRA_OR_CHANGED_FILE"):
                mod.apply(d,False)
            original.write_text("ORIGINAL_OWNER_BYTES",encoding="utf8")
            self.assertTrue(mod.apply(d,False))
            self.assertEqual(reserved.read_text("utf8"),"ORIGINAL_OWNER_BYTES")

    def test_partial_disabled_cleanup_recovers_without_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fixture(Path(tmp))
            mod.apply(d,True)
            disabled=d.with_name(d.name+".art_combat_disabling")
            os.rename(d,disabled)
            os.rename(mod.backup_dir(d),d)
            (disabled/mod.TRANSACTION).unlink()
            (disabled/"src/client/ArtCombatSlash.client.luau").unlink()
            self.assertTrue(mod.apply(d,False))
            self.assertFalse(disabled.exists())
            self.assertFalse(mod.receipt_path(d).exists())
            self.assertEqual(len(mod.sources(d)),66)

    def test_symlinked_parent_is_refused_before_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            dist=fixture(root)
            alias=root/"ALIAS"
            alias.symlink_to(root,target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,"FB015_SYMLINK_PARENT_COMPONENT_REFUSED"):
                mod.apply(alias/dist.name,True)
            self.assertTrue(dist.is_dir())
            self.assertFalse(mod.backup_dir(dist).exists())

    def test_atomic_external_receipt_never_overwrites_symlink_or_file(self):
        from fb015_fs_guard import atomic_json
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=root/"owner_data"
            original.write_text("DO_NOT_OVERWRITE",encoding="utf8")
            journal=root/"journal.json"
            journal.symlink_to(original)
            with self.assertRaisesRegex((RuntimeError,FileExistsError),
                    "FB015_ATOMIC_JSON_DESTINATION_ALREADY_EXISTS|File exists"):
                atomic_json(journal,{"id":"not_user_data"})
            self.assertEqual(original.read_text("utf8"),"DO_NOT_OVERWRITE")
            journal.unlink()
            journal.symlink_to(root/"missing-external-target")
            with self.assertRaises((RuntimeError,FileExistsError)):
                atomic_json(journal,{"id":"not_user_data"})
            self.assertFalse((root/"missing-external-target").exists())
            journal.unlink()
            atomic_json(journal,{"id":"first"})
            self.assertEqual(json.loads(journal.read_text("utf8"))["id"],"first")
            with self.assertRaises((RuntimeError,FileExistsError)):
                atomic_json(journal,{"id":"second"})
            self.assertEqual(json.loads(journal.read_text("utf8"))["id"],"first")

    def test_copy_rejects_symlink_inserted_after_preflight(self):
        from unittest import mock
        original_copy=mod.shutil.copytree
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            external=root/"OWNER_EXTERNAL"
            external.mkdir()
            (external/"secret.txt").write_text("PRESERVE")
            def racing_copy(source,target,*args,**kwargs):
                result=original_copy(source,target,*args,**kwargs)
                (Path(target)/"SNEAKED_LINK").symlink_to(external,target_is_directory=True)
                return result
            with mock.patch.object(mod.shutil,"copytree",side_effect=racing_copy):
                with self.assertRaisesRegex(RuntimeError,"FB015_SYMLINK_ENTRY_REFUSED"):
                    mod.apply(d,True)
            self.assertTrue(d.is_dir())
            self.assertFalse(mod.backup_dir(d).exists())
            self.assertEqual((external/"secret.txt").read_text("utf8"),"PRESERVE")

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
