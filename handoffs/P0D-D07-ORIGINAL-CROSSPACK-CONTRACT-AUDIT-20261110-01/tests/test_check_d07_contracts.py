import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit", ROOT / "tools" / "check_d07_contracts.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def synthetic():
    """Fixture strings test detection logic; not a substitute for real source readback."""
    values = {n: "--!strict\n" for ns in audit.MODULES.values() for n in ns}
    values["CanonicalEventBridge.luau"] += "phase = event.event\nvalidUntil = event.untilAt\nstage = cur.stage\n"
    values["GoroganCombinedRuntime.luau"] += '''activation.event~="ACTIVATE"\nactivation.untilAt\nself.deps.getStageId(roundId)\nsendVisual(self,a,"START"\nsendVisual(self,a,"STOMP"\ndriver:requestNavigation(cmd.position,cmd.reason,now)\nCore.new()\nopenFromCoreResult\n'''
    values["GoroganVisualPolicy.luau"] += 'snapshot.kind == "STOMP"\n'
    values["GoroganVisualPrefab.luau"] += "handle.rootPosition\nrootPosition=rootPosition\n"
    values["GoroganDamageBoundary.luau"] += "isCanonicalAttackReceipt\ngetAttackCenter\n"
    values["GoroganAttackReceiptWindow.luau"] += "function Window:attests\nfunction Window:center\n"
    values["GoroganClientAdapter.client.luau"] += "TRAP_BossVisualEvent\nTRAP_ActiveMatchId\nTRAP_ActiveStage\n"
    values["GoroganServerRuntime.luau"] += "Core.new()\n"
    values["GoroganRigDriver.luau"] += "function Driver:requestNavigation(position,reason,now)\n"
    return values


class StaticContractTests(unittest.TestCase):
    def test_core_six_findings(self):
        report = {x["code"]: x["status"] for x in audit.inspect(synthetic())}
        self.assertEqual(report, {
            "D08_TO_D07_ACTIVATE": "REMAP_REQUIRED",
            "BOSS_VISUAL_MOVEMENT": "VISUAL_TRACKING_REVIEW",
            "DAMAGE_RECEIPT_WIRING": "TRUSTED_CALLBACK_REQUIRED",
            "CLIENT_REPLICATION_DEPENDENCY": "PC_INTEGRATION_REQUIRED",
            "ONE_GOROGAN_AI_OWNER": "MUTUAL_EXCLUSION_REQUIRED",
            "NAVIGATION_TIME_ARGUMENT": "SOURCE_CONTRACT_ALIGNED"})

    def test_missing_each_module_fails(self):
        baseline = synthetic()
        for k in baseline:
            x = dict(baseline)
            x.pop(k)
            with self.subTest(module=k), self.assertRaises(audit.SourceBlocked):
                audit.inspect(x)

    def test_detection_changes_are_not_claimed_aligned(self):
        mapping = [
            ("CanonicalEventBridge.luau", "phase = event.event", "D08_TO_D07_ACTIVATE"),
            ("GoroganVisualPolicy.luau", 'snapshot.kind == "STOMP"', "BOSS_VISUAL_MOVEMENT"),
            ("GoroganDamageBoundary.luau", "isCanonicalAttackReceipt", "DAMAGE_RECEIPT_WIRING"),
            ("GoroganClientAdapter.client.luau", "TRAP_BossVisualEvent", "CLIENT_REPLICATION_DEPENDENCY"),
            ("GoroganServerRuntime.luau", "Core.new()", "ONE_GOROGAN_AI_OWNER"),
            ("GoroganRigDriver.luau", "function Driver:requestNavigation(position,reason,now)", "NAVIGATION_TIME_ARGUMENT"),
        ]
        for module, snippet, code in mapping:
            x = synthetic()
            x[module] = x[module].replace(snippet, "")
            with self.subTest(module=module):
                status = {f["code"]: f["status"] for f in audit.inspect(x)}
                self.assertEqual(status[code], "REVIEW_SOURCE_CHANGE")

    def test_manifest_and_source_hash_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = synthetic()
            for area, pid in audit.PACKETS.items():
                folder = root / "packs" / pid
                (folder / "luau").mkdir(parents=True)
                rows = []
                for module in audit.MODULES[area]:
                    data = sample[module].encode()
                    (folder / "luau" / module).write_bytes(data)
                    rows.append({"path": "luau/" + module, "size": len(data),
                                 "sha256": hashlib.sha256(data).hexdigest()})
                (folder / "BUILD_MANIFEST.json").write_text(json.dumps({"packet_id":pid,"files":rows}))
            parsed = audit.load_verified(root)
            self.assertEqual(parsed, sample)
            # Byte corruption must block, not silently become a passing reference.
            bad = root / "packs" / audit.PACKETS["ai"] / "luau" / "GoroganServerAICore.luau"
            bad.write_text("--tampered\n")
            with self.assertRaisesRegex(audit.SourceBlocked, "SHA_MISMATCH"):
                audit.load_verified(root)

    def test_wrong_packet_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "packs" / audit.PACKETS["visual"]
            folder.mkdir(parents=True)
            (folder / "BUILD_MANIFEST.json").write_text(json.dumps({"packet_id":"FAKE","files":[]}))
            with self.assertRaisesRegex(audit.SourceBlocked, "BLOCKED_MANIFEST"):
                audit.load_verified(Path(tmp))

    def test_missing_manifest_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(audit.SourceBlocked, "BLOCKED_MISSING"):
                audit.load_verified(Path(tmp))

    def test_missing_source_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "packs" / audit.PACKETS["visual"]
            folder.mkdir(parents=True)
            (folder / "BUILD_MANIFEST.json").write_text(json.dumps({"packet_id":audit.PACKETS["visual"],"files":[{"path":"luau/GoroganVisualPolicy.luau","size":1,"sha256":"0"*64}]}))
            with self.assertRaisesRegex(audit.SourceBlocked, "BLOCKED_MISSING"):
                audit.load_verified(Path(tmp))

    def test_stage_and_event_immutable_sha_references(self):
        self.assertEqual(len(set(audit.PINNED_COMMITS.values())),5)
        for sha in audit.PINNED_COMMITS.values():
            self.assertEqual(len(sha),40)
            self.assertTrue(all(c in "0123456789abcdef" for c in sha))


if __name__ == "__main__":
    unittest.main()
