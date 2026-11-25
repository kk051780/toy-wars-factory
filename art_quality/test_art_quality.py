#!/usr/bin/env python3
"""Executable negative/positive tests for the read-only ART gate."""
from __future__ import annotations
import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
import check_art_quality as art

def studio_place(path: Path, missing: str = "", duplicate_game: bool = False,
                 activated: bool = True) -> None:
    root = ET.Element("roblox")
    names = {"Game": "Script", "TrapRaidersHUD": "LocalScript",
             "BattleHUDGovernor": "LocalScript"}
    for required in art.CATEGORIES.values():
        for name in required:
            names.setdefault(name, "ModuleScript")
    if missing:
        names.pop(missing)
    for name, kind in names.items():
        item = ET.SubElement(root, "Item", {"class": kind})
        props = ET.SubElement(item, "Properties")
        ET.SubElement(props, "string", {"name": "Name"}).text = name
        ET.SubElement(props, "string", {"name": "Source"}).text = (
            "attack.Activated:Connect" if name == "TrapRaidersHUD" and activated
            else "-- stub source for " + name)
    if duplicate_game:
        item = ET.SubElement(root, "Item", {"class": "Script"})
        p = ET.SubElement(item, "Properties")
        ET.SubElement(p, "string", {"name": "Name"}).text = "Game"
        ET.SubElement(p, "string", {"name": "Source"}).text = "-- duplicate"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def png_chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def write_test_png(path: Path, width: int, height: int, color: int) -> None:

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixels = (b"\0" + bytes((color, 25, 180)) * width) * height
    path.write_bytes(art.PNG + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", zlib.compress(pixels)) + png_chunk(b"IEND", b""))

class TestArtGate(unittest.TestCase):
    def test_real_xml_inventory_all_ten_categories(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path)
            result = art.scene_inventory(path)
            self.assertEqual(result["source_gate"], "PASS")
            self.assertEqual(set(result["source_coverage"]), set(art.CATEGORIES))
            self.assertTrue(all(v["present_count"] == len(v["required"]) for v in
                                result["source_coverage"].values()))
            self.assertGreater(result["script_count"], 10)

    def test_duplicate_game_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path, duplicate_game=True)
            result = art.scene_inventory(path)
            self.assertEqual(result["source_gate"], "FAIL")
            self.assertIn("AUTHORITY_OR_HUD_COUNT:Game", result["source_violations"])

    def test_missing_art_category_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path, missing="H1SeaGroundRepair")
            result = art.scene_inventory(path)
            self.assertEqual(result["source_gate"], "FAIL")
            self.assertTrue(any("ART_SOURCE_COVERAGE:sea" in t for t in
                                result["source_violations"]))

    def test_non_activated_attack_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path, activated=False)
            self.assertIn("ATTACK_INPUT_NOT_ACTIVATED",
                          art.scene_inventory(path)["source_violations"])

    def test_missing_evidence_is_art_no_go_even_when_source_green(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path)
            result = art.audit(path)
            self.assertEqual(result["gate_level"], "SOURCE_READY_EVIDENCE_MISSING")
            self.assertEqual(result["art_decision"], "ART_NO_GO")
            self.assertFalse(result["owner_accepted"])
            self.assertEqual(result["evidence"]["shots_required"], 32)

    def test_strict_rejects_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            place = root / "place.rbxlx"
            report = root / "report.json"
            studio_place(place)
            self.assertEqual(art.main(["--place", str(place), "--out", str(report)]), 0)
            self.assertEqual(art.main(["--place", str(place), "--out", str(report),
                                       "--strict"]), 2)
            self.assertEqual(json.loads(report.read_text())["art_decision"], "ART_NO_GO")

    def test_manifest_spoofed_place_sha_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            place = root / "place.rbxlx"
            studio_place(place)
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps({"schema": "P0D_ART_STUDIO_EVIDENCE_V1",
                "after_place_sha256": "0"*64, "shots": [],
                "before_head": "a"*40, "after_head": "b"*40,
                "ratings": {}, "performance": {},
                "critical_visual_blockers": [], "human_reviewer": "tester"}))
            result = art.audit(place, evidence)
            self.assertEqual(result["evidence"]["gate"], "FAIL")
            self.assertIn("STUDIO_PLACE_SHA_MISMATCH",
                          result["evidence"]["violations"])
            self.assertEqual(result["art_decision"], "ART_NO_GO")

    def test_art_progress_counts_only_valid_current_unique_pngs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = root / "evidence.json"
            after = "a" * 64
            write_test_png(root / "good-pc.png", 1280, 720, 10)
            write_test_png(root / "low-pc.png", 1717, 596, 20)
            write_test_png(root / "dup-content.png", 1280, 720, 30)
            write_test_png(root / "dup-slot.png", 1280, 720, 40)
            write_test_png(root / "good-android.png", 720, 400, 50)
            invalid = bytearray((root / "good-pc.png").read_bytes())
            invalid[-1] ^= 1
            (root / "bad-crc.png").write_bytes(invalid)
            header = (root / "good-pc.png").read_bytes()[:33]
            (root / "bad-deflate.png").write_bytes(
                header + png_chunk(b"IDAT", bytes(2048)) + png_chunk(b"IEND", b"")
            )
            invalid_row = (b"\x05" + bytes((10, 25, 180)) * 1280) * 720
            (root / "bad-raster.png").write_bytes(
                header + png_chunk(b"IDAT", zlib.compress(invalid_row)) + png_chunk(b"IEND", b"")
            )
            rows = [
                ("lobby", "pc", "before", "good-pc.png"),
                ("lobby", "pc", "after", "low-pc.png"),
                ("field_wide", "pc", "before", "does-not-exist.png"),
                ("castle", "pc", "after", "bad-crc.png"),
                ("sea", "pc", "before", "dup-content.png"),
                ("sea", "pc", "after", "dup-content.png"),
                ("forest", "pc", "before", "dup-slot.png"),
                ("forest", "pc", "before", "dup-slot.png"),
                ("combat", "android", "after", "good-android.png"),
                ("neutral", "pc", "before", "bad-deflate.png"),
                ("beast", "pc", "before", "bad-raster.png"),
            ]
            evidence.write_text(json.dumps({
                "schema": "P0D_ART_STUDIO_EVIDENCE_V1", "before_head": "b"*40,
                "after_head": "c"*40, "after_place_sha256": after,
                "shots": [dict(zip(("scene", "device", "version", "file"), row)) for row in rows],
            }))
            result = art.evidence_audit(evidence, root, after)
            self.assertEqual((result["shots_submitted"], result["shots_received"], result["shots_required"]), (10, 2, 32))
            self.assertEqual(result["gate"], "FAIL")
            for code in ("LOW_PC_RESOLUTION", "PNG_FILE_REQUIRED", "INVALID_PNG_CHUNK_CRC",
                         "REUSED_SCREENSHOT", "DUPLICATE_SHOT_KEY", "INVALID_PNG_IDAT_DEFLATE", "INVALID_PNG_RASTER"):
                self.assertTrue(any(code in detail for detail in result["violations"]), code)
            stale = art.evidence_audit(evidence, root, "f"*64)
            self.assertEqual((stale["shots_submitted"], stale["shots_received"]), (10, 0))

    def test_png_accepts_adam7_split_idat(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "interlaced.png"
            header = struct.pack(">IIBBBBB", 721, 401, 8, 2, 0, 0, 1)
            passes = ((91, 51), (90, 51), (181, 50), (180, 101), (361, 100), (360, 201), (721, 200))
            raster = b"".join((b"\0" + bytes((10, 25, 180)) * columns) * rows for columns, rows in passes)
            encoded = zlib.compress(raster, level=0)
            parts = [png_chunk(b"IDAT", encoded[i:i + 50000]) for i in range(0, len(encoded), 50000)]
            path.write_bytes(art.PNG + png_chunk(b"IHDR", header) + b"".join(parts) + png_chunk(b"IEND", b""))
            self.assertEqual(art.png_info(path)[:2], (721, 401))

    def test_artifact_without_place_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(art.main(["--place", str(root/"notfound.rbxlx"),
                                       "--out", str(root/"report.json")]), 2)
            self.assertEqual(json.loads((root/"report.json").read_text())["art_decision"], "ART_NO_GO")

if __name__ == "__main__":
    unittest.main()
