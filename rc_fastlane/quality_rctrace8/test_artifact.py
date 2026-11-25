#!/usr/bin/env python3
"""Pure offline unit tests, including adversarial false-positive artifacts."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location("gq8",Path(__file__).with_name("verify_artifact.py"))
assert spec and spec.loader
gq8=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gq8)

HEAD="a"*40

def fixture():
    sources={}
    for scope in gq8.RULES.values():
        for script,tokens in scope.items():
            sources.setdefault(script,set()).update(tokens)
    for _,(script,tokens) in gq8.FEATURE_EVIDENCE.items():
        sources.setdefault(script,set()).update((tokens,) if isinstance(tokens,str) else tokens)
    for name in gq8.ROLE_CLASSES:
        sources.setdefault(name,set())
    i=0
    while len(sources)<31:
        name=f"GQ8_OTHER_SOURCE_{i:02}"
        sources[name]=set(["return {}"])
        i+=1
    root=ET.Element("roblox",{"version":"4"})
    for name,tokens in sources.items():
        cls=gq8.ROLE_CLASSES.get(name,"ModuleScript")
        node=ET.SubElement(root,"Item",{"class":cls})
        props=ET.SubElement(node,"Properties")
        ET.SubElement(props,"string",{"name":"Name"}).text=name
        ET.SubElement(props,"ProtectedString",{"name":"Source"}).text="\n".join(sorted(tokens))
    raw=ET.tostring(root,encoding="utf-8")
    flags={f:True for f in gq8.FEATURE_EVIDENCE}
    heads={"original_game482":"f"*40,"carrier_stale_avatar551":"e"*40}
    manifest={"canonical_branch":"rc/p0d-s1-kids-rc01","profile":"eggrumble_v3_31",
              "source_count":31,"enabled":True,"source_heads":heads,
              "feature_flags":flags}
    active={"active_profile":"rich51","source_profiles":{"eggrumble_v3_31":{"source_count":31}}}
    receipt={"status":"CANONICAL_RC_BRANCH_COMPANION_PROFILE_BUILD_PASS_NOT_STUDIO_PLAYTESTED",
             "canonical_branch":"rc/p0d-s1-kids-rc01",
             "github_commit_sha":HEAD,"official_rc_commit_verified":True,
             "release_profile":"eggrumble_v3_31","script_count":31,
             "script_source_and_class_exact":"31/31",
             "roblox_publish":False,"s1_active_profile_unchanged":True,
             "source_author_heads":copy.deepcopy(heads),
             "place_name":gq8.PLACE,"place_size_bytes":len(raw),
             "place_sha256":hashlib.sha256(raw).hexdigest()}
    return raw,receipt,manifest,active

def change_source(raw:bytes,name:str,replacement:str):
    root=ET.fromstring(raw)
    for item in root.iter("Item"):
        p=item.find("Properties")
        if p is not None and p.findtext("string[@name='Name']")==name:
            p.find("ProtectedString[@name='Source']").text=replacement
            return ET.tostring(root,encoding="utf-8")
    raise ValueError("No test source "+name)

def rehash(data,receipt):
    receipt["place_size_bytes"]=len(data)
    receipt["place_sha256"]=hashlib.sha256(data).hexdigest()

def drop_anchor(raw:bytes,name:str,anchor:str)->bytes:
    root=ET.fromstring(raw)
    for item in root.iter("Item"):
        props=item.find("Properties")
        if props is None or props.findtext("string[@name='Name']")!=name:
            continue
        source=props.find("ProtectedString[@name='Source']")
        if source is None or source.text is None or source.text.count(anchor)!=1:
            raise AssertionError("Missing or duplicate fixture anchor "+anchor)
        source.text=source.text.replace(anchor,"-- GQ8 source mutation removed",1)
        return ET.tostring(root,encoding="utf-8")
    raise AssertionError("Missing script "+name)


class Gate(unittest.TestCase):
    def test_replay_retry_fence_source_must_exist(self):
        b,r,m,a=fixture()
        mutant=drop_anchor(b,"EGGRUMBLE_RoundReplay",
                           "-- GQ8_REPLAY_RESET_RETRY_SESSION_FENCE_20261118")
        rehash(mutant,r)
        with self.assertRaisesRegex(Exception, "GQ8_REPLAY_RESET_RETRY_SESSION_FENCE"):
            gq8.verify(mutant,r,m,a,HEAD)

    def test_valid_covers_eight_domains_and_58_known_flags(self):
        b,r,m,a=fixture()
        v=gq8.verify(b,r,m,a,HEAD)
        self.assertEqual(len(v["domains"]),8)
        self.assertEqual(v["verified_flag_count"],61)
        self.assertEqual(v["script_count"],31)
        self.assertEqual(v["real_studio_2client"],"NOT_TESTED")
        self.assertFalse(v["roblox_published"])
    def test_gq8_mobile_result_source_missing_is_red(self):
        b,r,m,a=fixture()
        b=drop_anchor(b,"EGGRUMBLE_MatchResultService",
            "-- GQ8_RESULT_MOBILE_READABILITY_20261118")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,
            "FEATURE_FALSE_ON_GQ8_RESULT_MOBILE_READABILITY_20261118"):
            gq8.verify(b,r,m,a,HEAD)

    def test_draw_result_real_place_rejects_generic_loss_like_label(self):
        b,r,m,a=fixture()
        b=drop_anchor(b,"EGGRUMBLE_MatchResultService",
            'local status=if session.rules.winner=="DRAW" then "引き分け"')
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,
            "DOMAIN_balance_MISSING_EGGRUMBLE_MatchResultService"):
            gq8.verify(b,r,m,a,HEAD)

    def test_roster16_actual_place_with_old_32_guards_is_red(self):
        b,r,m,a=fixture()
        b=change_source(b,"EGGRUMBLE_CastleMatchRules",
            "M.MAX_HERO_SLOTS=16\nlimit>=2 and limit<=32\n#roster>=2 and #roster<=32")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"DOMAIN_|FEATURE_FALSE_ON"):
            gq8.verify(b,r,m,a,HEAD)
    def test_stale_rc_head_must_fail(self):
        b,r,m,a=fixture()
        with self.assertRaisesRegex(gq8.RedGate,"ARTIFACT_STALE_WRONG_HEAD"):
            gq8.verify(b,r,m,a,"b"*40)
    def test_fake_enabled_feature_but_missing_selected_script_anchor(self):
        b,r,m,a=fixture()
        n="EGGRUMBLE_LobbyCastleModesPreview"
        b=change_source(b,n,"CastleAccessRamp")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"DOMAIN_|FEATURE_FALSE_ON"):
            gq8.verify(b,r,m,a,HEAD)
    def test_31_scripts_duplicate_rejected(self):
        b,r,m,a=fixture()
        root=ET.fromstring(b)
        name=root.findall("Item")[1].find("Properties/string[@name='Name']")
        name.text=root.findall("Item")[0].find("Properties/string[@name='Name']").text
        b=ET.tostring(root,encoding="utf-8")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"DUPLICATE_SCRIPT"):
            gq8.verify(b,r,m,a,HEAD)
    def test_missing_script_rejected(self):
        b,r,m,a=fixture()
        root=ET.fromstring(b)
        root.remove(root.findall("Item")[-1])
        b=ET.tostring(root,encoding="utf-8")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"SCRIPT_COUNT_31"):
            gq8.verify(b,r,m,a,HEAD)
    def test_wrong_script_class_rejected(self):
        b,r,m,a=fixture()
        root=ET.fromstring(b)
        for item in root.findall("Item"):
            if item.find("Properties/string[@name='Name']").text=="EGGRUMBLE_LobbyCastleModesPreview":
                item.attrib["class"]="ModuleScript"
        b=ET.tostring(root,encoding="utf-8")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"ROLE_CLASS"):
            gq8.verify(b,r,m,a,HEAD)
    def test_place_sha_mismatch_fails(self):
        b,r,m,a=fixture()
        with self.assertRaisesRegex(gq8.RedGate,"PLACE_SHA256_WRONG"):
            gq8.verify(b,r|{"place_sha256":"0"*64},m,a,HEAD)
    def test_place_bytes_mismatch_fails(self):
        b,r,m,a=fixture()
        with self.assertRaisesRegex(gq8.RedGate,"PLACE_BYTES_WRONG"):
            gq8.verify(b,r|{"place_size_bytes":123},m,a,HEAD)
    def test_flag_disabled_cannot_be_certified(self):
        b,r,m,a=fixture()
        m["feature_flags"]["CARRIER_STALE_AVATAR_DIED_FENCE_551"]=False
        with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FLAG_DISABLED"):
            gq8.verify(b,r,m,a,HEAD)
    def test_unverified_pr_artifact_cannot_be_official(self):
        b,r,m,a=fixture()
        r["official_rc_commit_verified"]=False
        with self.assertRaisesRegex(gq8.RedGate,"NOT_OFFICIAL_PUSH"):
            gq8.verify(b,r,m,a,HEAD)
    def test_premerge_only_when_explicitly_allowed_and_properly_labeled(self):
        b,r,m,a=fixture()
        r["official_rc_commit_verified"]=False
        r["status"]="RC_PREMERGE_COMPANION_PROFILE_BUILD_PASS_NOT_STUDIO_PLAYTESTED"
        with self.assertRaisesRegex(gq8.RedGate,"NOT_OFFICIAL_PUSH"):
            gq8.verify(b,r,m,a,HEAD)
        v=gq8.verify(b,r,m,a,HEAD,allow_pr_premerge=True)
        self.assertFalse(v["official_rc_push_verified"])
        self.assertIn("NOT_OFFICIAL_RC",v["result"])
    def test_pr_premerge_cannot_launder_undesignated_source_as_valid(self):
        b,r,m,a=fixture()
        r["official_rc_commit_verified"]=False
        r["status"]="SOME_UNVERIFIED_BUILD"
        with self.assertRaisesRegex(gq8.RedGate,"NOT_OFFICIAL_PUSH"):
            gq8.verify(b,r,m,a,HEAD,allow_pr_premerge=True)
    def test_source_author_heads_must_match_manifest(self):
        b,r,m,a=fixture()
        r["source_author_heads"]["carrier_stale_avatar551"]="b"*40
        with self.assertRaisesRegex(gq8.RedGate,"AUTHOR_SHA_MANIFEST_ARTIFACT_DRIFT"):
            gq8.verify(b,r,m,a,HEAD)
    def test_no_misrepresented_studio_or_publish(self):
        b,r,m,a=fixture()
        r["roblox_publish"]=True
        with self.assertRaisesRegex(gq8.RedGate,"UNAUTHORIZED_PUBLISH"):
            gq8.verify(b,r,m,a,HEAD)
    def test_future_enabled_flag_without_real_source_evidence_is_red(self):
        b,r,m,a=fixture()
        m["feature_flags"]["FUTURE_AUTHOR_UNKNOWN_999"]=True
        with self.assertRaisesRegex(
                gq8.RedGate,"ENABLED_FLAG_WITHOUT_SOURCE_EVIDENCE_FUTURE_AUTHOR_UNKNOWN_999"):
            gq8.verify(b,r,m,a,HEAD)
        # The same RED gate also applies to a premerge PR receipt.
        r["official_rc_commit_verified"]=False
        r["status"]="RC_PREMERGE_COMPANION_PROFILE_BUILD_PASS_NOT_STUDIO_PLAYTESTED"
        with self.assertRaisesRegex(
                gq8.RedGate,"ENABLED_FLAG_WITHOUT_SOURCE_EVIDENCE_FUTURE_AUTHOR_UNKNOWN_999"):
            gq8.verify(b,r,m,a,HEAD,allow_pr_premerge=True)

    def test_future_disabled_flag_can_remain_prep_without_claiming_enabled(self):
        b,r,m,a=fixture()
        m["feature_flags"]["FUTURE_AUTHOR_DISABLED_PREP_999"]=False
        v=gq8.verify(b,r,m,a,HEAD)
        self.assertEqual(v["unassessed_new_flags"],["FUTURE_AUTHOR_DISABLED_PREP_999"])
        self.assertEqual(v["verified_flag_count"],61)

    def test_known_feature_flag_must_be_a_json_boolean(self):
        for nonboolean in (1,"true",None,0):
            with self.subTest(nonboolean=nonboolean):
                b,r,m,a=fixture()
                m["feature_flags"]["GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117"]=nonboolean
                with self.assertRaisesRegex(
                        gq8.RedGate,
                        "FEATURE_FLAG_NOT_BOOLEAN_GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117"):
                    gq8.verify(b,r,m,a,HEAD)
    def test_all_current_official_manifest_flags_are_actually_attested(self):
        # Do not allow an enabled official flag to silently pass as unassessed.
        path=Path(__file__).resolve().parents[1]/"EGGRUMBLE_V3_ACTIVE.json"
        manifest=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_count"],31)
        enabled={k for k,flag in manifest["feature_flags"].items() if flag is True}
        self.assertEqual(len(enabled),61)
        self.assertEqual(set(manifest["feature_flags"]),enabled)
        self.assertEqual(enabled,set(gq8.FEATURE_EVIDENCE))
        self.assertEqual(manifest["source_heads"]["zombie_guard582"],
                         "5769b80ed21f5592adcca1936d2d3d04934f0089")

    def test_current34_manifest_anchors_enforce_bot_siege_and_egg_freeze(self):
        late=(
            "NEUTRAL_DEATH_KO_CURRENT_OWNER_508",
            "AI_TAKEOVER_TERMINAL_FENCE_580",
            "TEAM_FIELD_ITEM_RIDGE_FOREST_CLEARANCE_520",
            "FIELD_CARRIER_OFFARENA_DROP_515",
            "ZOMBIE_COMMAND_SQUAD_582",
            "DEPOSIT_CURRENT_SESSION_586",
            "ZOMBIE_NEUTRAL_STABLE_ID_V3",
            "ITEM_CURRENT_SESSION_525",
            "SERVER_PROMPT_CONFIG_REACH_611",
            "ZOMBIE_GUARD_CASTLE_LEASH_582",
            "LOBBY_QUEUE_ETA_615",
            "MATCH_DEADLINE_DRAW_499",
            "BOT_SIEGE_TARGET_PACING_527",
            "POSTWIN_LATE_CARRIER_DEATH_FREEZE_509",
            "GQ512_ROUND_COMBO_REPLAY_RESET_20261117",
            "GQ514_BOSS_KO_ROUND_RESET_20261117",
            "GQ505_SERVER_MODE_FX_FAIR_INLINE31",
            "GQ524_NINJA_TRAPPER_WARP_CLEARANCE_20261117",
            "GQ510_MAGE_TEAM_AI_WALL_LOS_20261117",
            "GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117",
            "GQ506_RESPAWN_GRACE_SINGLE_HOST_20261117",
            "GQ8_CASTLE_DEFENSE_CURRENT_HUMAN_20261117",
            "GQ732_CASTLE_DUPLICATE_DECOR_SLOT_20261117",
            "GQ8_FIELD_EGG_CREATION_LIMIT_20261118",
            "GQ504_ORIGINAL_CONFIRMED_HIT_AUDIO_INLINE_20261117",
        )
        for flag in late:
            script,anchors=gq8.FEATURE_EVIDENCE[flag]
            anchors=(anchors,) if isinstance(anchors,str) else anchors
            for anchor in anchors:
                with self.subTest(flag=flag,anchor=anchor):
                    b,r,m,a=fixture()
                    self.assertEqual(gq8.verify(b,r,m,a,HEAD)["verified_flag_count"],61)
                    b=drop_anchor(b,script,anchor)
                    rehash(b,r)
                    with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FALSE_ON_"+flag):
                        gq8.verify(b,r,m,a,HEAD)

    def test_gq732_original_duplicate_is_red_in_actual_selected_place(self):
        b,r,m,a=fixture()
        b=drop_anchor(b,"EGGRUMBLE_CastleMatchRules","duplicate decoration in this plot")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,
                                    "DOMAIN_castle_MISSING_EGGRUMBLE_CastleMatchRules|FEATURE_FALSE_ON_GQ732"):
            gq8.verify(b,r,m,a,HEAD)

    def test_late_flags_cannot_claim_certification_when_disabled(self):
        for flag in (
            "NEUTRAL_DEATH_KO_CURRENT_OWNER_508",
            "AI_TAKEOVER_TERMINAL_FENCE_580",
            "TEAM_FIELD_ITEM_RIDGE_FOREST_CLEARANCE_520",
            "FIELD_CARRIER_OFFARENA_DROP_515",
            "ZOMBIE_COMMAND_SQUAD_582",
            "DEPOSIT_CURRENT_SESSION_586",
            "ZOMBIE_NEUTRAL_STABLE_ID_V3",
            "ITEM_CURRENT_SESSION_525",
            "SERVER_PROMPT_CONFIG_REACH_611",
            "ZOMBIE_GUARD_CASTLE_LEASH_582",
            "LOBBY_QUEUE_ETA_615",
            "MATCH_DEADLINE_DRAW_499",
            "BOT_SIEGE_TARGET_PACING_527",
            "POSTWIN_LATE_CARRIER_DEATH_FREEZE_509",
            "GQ512_ROUND_COMBO_REPLAY_RESET_20261117",
            "GQ514_BOSS_KO_ROUND_RESET_20261117",
            "GQ505_SERVER_MODE_FX_FAIR_INLINE31",
            "GQ524_NINJA_TRAPPER_WARP_CLEARANCE_20261117",
            "GQ510_MAGE_TEAM_AI_WALL_LOS_20261117",
            "GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117",
            "GQ506_RESPAWN_GRACE_SINGLE_HOST_20261117",
            "GQ8_CASTLE_DEFENSE_CURRENT_HUMAN_20261117",
            "GQ732_CASTLE_DUPLICATE_DECOR_SLOT_20261117",
            "GQ504_ORIGINAL_CONFIRMED_HIT_AUDIO_INLINE_20261117",
        ):
            with self.subTest(flag=flag):
                b,r,m,a=fixture()
                m["feature_flags"][flag]=False
                with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FLAG_DISABLED_OR_UNKNOWN_"+flag):
                    gq8.verify(b,r,m,a,HEAD)

    def test_s1_default_must_remain_unchanged_for_this_profile(self):
        b,r,m,a=fixture()
        a["active_profile"]="eggrumble_v3_31"
        with self.assertRaisesRegex(gq8.RedGate,"S1_LEGACY_CHANGED_WITHOUT_OWNER"):
            gq8.verify(b,r,m,a,HEAD)

if __name__=="__main__":
    unittest.main()
