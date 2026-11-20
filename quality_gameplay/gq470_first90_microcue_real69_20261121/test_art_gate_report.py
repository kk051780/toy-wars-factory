#!/usr/bin/env python3
"""Negative evidence gate: CI green never means a screenshot, FPS or human ART green.

This validates an explicitly unmeasured 32-shot art gate for First90 microcues.
Screenshots, real devices, human ratings and the owner's accept remain missing.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

import patch_first90_microcue69 as patch

HERE=Path(__file__).resolve().parent
ART=HERE/"ART_CHECK_REPORT.json"
SCENES={"lobby","field_wide","castle","sea","forest","neutral","beast","combat"}
CATEGORIES={"terrain","castle","sea","forest","neutral","beast","roles","combat","lobby","atmosphere"}
DEVICES={"pc","android"}
VERSIONS={"before","after"}

def require(condition: bool, name: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_FIRST90_ART_EVIDENCE_"+name)

def audit(report: dict) -> dict:
    require(report.get("feature_id")=="GQ470_FB015_FIRST90_MICROCUE_VISUAL_20261121", "FEATURE")
    ci=report.get("candidate_source_ci",{})
    require(ci.get("conclusion")=="SUCCESS_SOURCE_ONLY" and
            ci.get("verified_selected_sources")==69 and
            ci.get("changed_routes")==1 and
            ci.get("unmodified_routes_byte_exact")==68 and
            ci.get("native_compile_on")==69 and
            ci.get("native_compile_off")==69 and
            ci.get("rojo_on_off")=="PASS" and
            ci.get("official_rc_adopted") is False,"NO_FALSE_ADOPTION")
    original=(HERE.parents[1]/patch.ORIGINAL_LOCAL).read_text(encoding="utf-8")
    actual_candidate_sha=patch.digest(patch.transform(original).encode("utf-8"))
    require(ci.get("source_sha256_before")==patch.ORIGINAL_SHA256
            and ci.get("source_sha256_after")==actual_candidate_sha,
            "ORIGINAL_AND_CANDIDATE_SRC_DYNAMIC_SOURCE_EXACT")
    visual=report.get("static_visual_delta",{})
    before=visual.get("billboard_before_px")
    after=visual.get("billboard_after_px")
    require(before==[210,43] and after==[184,36] and
            visual.get("billboard_area_before_px2")==before[0]*before[1] and
            visual.get("billboard_area_after_px2")==after[0]*after[1] and
            abs(visual.get("nominal_gui_rect_area_reduction_percent",-1)
                -round(100*(1-after[0]*after[1]/(before[0]*before[1])),1))<0.001,
            "GEOMETRY_AND_PERCENT")
    require(visual.get("new_parts")==0 and visual.get("new_gui_instances")==0 and
            visual.get("new_remote_writers")==0 and visual.get("per_frame_render_callback_additions")==0
            and visual.get("cue_visible_seconds")==4.5
            and visual.get("reminder_after_seconds")==24
            and visual.get("max_lifetime_seconds")==90,
            "STATIC_SAFE_POLICY")
    evidence=report.get("visual_evidence_gate",{})
    require(evidence.get("status")=="MISSING"
            and evidence.get("required_captures")==32
            and evidence.get("real_png_captures_received")==0,
            "NO_FAKE_IMAGE_COUNT")
    shots=evidence.get("shots",[])
    keys=set()
    require(len(shots)==32,"EXACT_CAPTURE_SLOTS")
    for item in shots:
        scene,device,version=item.get("scene"),item.get("device"),item.get("version")
        require(scene in SCENES and device in DEVICES and version in VERSIONS,"SCENE_DEVICE")
        require(item.get("file")==f"{version}/{device}/{scene}.png" and item.get("status")=="MISSING",
                "NO_FAKE_CAPTURE_FILES")
        keys.add((scene,device,version))
    require(len(keys)==32 and
            keys=={(s,d,v) for s in SCENES for d in DEVICES for v in VERSIONS},
            "NO_MISSING_OR_DUPLICATE_SLOTS")
    human=report.get("human_art_gate",{})
    require(human.get("status")=="NOT_TESTED" and human.get("independent_reviewer") is None,
            "HUMAN_NOT_TESTED")
    require(set(human.get("ratings",{}))==CATEGORIES and
            all(x.get("pc") is None and x.get("android") is None
                for x in human["ratings"].values()),"NO_INVENTED_RATINGS")
    runtime=report.get("runtime_gate",{})
    for k in ("studio_solo","studio_2client","android_15min"):
        require(runtime.get(k)=="NOT_TESTED","NO_FALSE_ENGINE_"+k)
    for k in ("lowend_android_median_fps","lowend_android_p10_fps",
              "lowend_android_heat_drop_fraction","first3min_kid_fun"):
        require(runtime.get(k) is None,"NO_FAKE_METRIC_"+k)
    require(runtime.get("owner_accepted") is False,"OWNER")
    decisions=report.get("decisions",{})
    require(decisions.get("source_gate")=="PASS_SOURCE_ONLY_ON_PINNED_3178D3"
            and decisions.get("owner_accepted")==0 and
            all(decisions.get(k)=="NO_GO"
                for k in ("visual_evidence","human_art","android","kid_fun","product")),
            "NO_FALSE_GATE_PASS")
    return {"source":"PASS_SOURCE_ONLY", "real_png_count":0, "missing_scenes":32}

class ReportEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(ART.read_text(encoding="utf-8"))

    def test_actual_32_missing_and_unknown_metrics(self):
        self.assertEqual(audit(self.report)["missing_scenes"],32)

    def test_visual_area_math_not_beauty_rating(self):
        self.assertEqual(round(100*(1-184*36/(210*43)),1),26.6)
        self.assertIn("not measured viewport obstruction",
                      self.report["static_visual_delta"]["interpretation"])

    def test_human_capture_checkpoints_match_actual_first90_steps(self):
        baseline=(HERE.parents[1]/patch.ORIGINAL_LOCAL).read_text(encoding="utf-8")
        self.assertIn("local STEP1=22",baseline)
        self.assertIn("local STEP2=48",baseline)
        slots=self.report["first90_focus_checks"]
        checkpoint_seconds={item["elapsed_s"] for item in slots}
        self.assertTrue({2,8,22,24,48,90}.issubset(checkpoint_seconds))
        self.assertNotIn(30,checkpoint_seconds)  # not a step transition
        self.assertNotIn(55,checkpoint_seconds)
        self.assertTrue(all("4.5秒" in item["expectation"]
                            for item in slots if item["elapsed_s"] in (22,48)))

    def test_synthetic_evidence_mutations_rejected(self):
        mutations=[
            ("falsely green visual",lambda x:x["decisions"].update(human_art="PASS")),
            ("falsely green Android",lambda x:x["decisions"].update(android="PASS")),
            ("invented screenshot count",lambda x:x["visual_evidence_gate"].update(real_png_captures_received=32)),
            ("fake screenshot path",lambda x:x["visual_evidence_gate"]["shots"][0].update(file="fake.png")),
            ("duplicate camera slot",lambda x:x["visual_evidence_gate"]["shots"][0].update(scene="sea")),
            ("fake human score",lambda x:x["human_art_gate"]["ratings"]["lobby"].update(pc=5)),
            ("fake engine",lambda x:x["runtime_gate"].update(studio_2client="PASS")),
            ("fake FPS",lambda x:x["runtime_gate"].update(lowend_android_p10_fps=35)),
            ("invented owner approval",lambda x:x["runtime_gate"].update(owner_accepted=True)),
            ("fabricated formal adoption",lambda x:x["candidate_source_ci"].update(official_rc_adopted=True)),
            ("changed route count",lambda x:x["candidate_source_ci"].update(changed_routes=2)),
            ("budget arithmetic",lambda x:x["static_visual_delta"].update(billboard_area_after_px2=123)),
        ]
        for label,mutation in mutations:
            report=deepcopy(self.report)
            mutation(report)
            with self.subTest(label=label),self.assertRaises(ValueError):
                audit(report)

if __name__=="__main__":
    unittest.main()
