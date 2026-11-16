#!/usr/bin/env python3
"""Pure offline unit tests, including adversarial false-positive artifacts."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
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
        if source is None:raise AssertionError("missing source")
        if source.text is None or source.text.count(anchor)!=1:
            raise AssertionError("missing or duplicate anchor "+anchor)
        source.text=source.text.replace(anchor,"-- selected source anchor removed",1)
        return ET.tostring(root,encoding="utf-8")
    raise AssertionError("missing script "+name)

def fixture_with_current_26_flags():
    raw,receipt,manifest,active=fixture()
    root=ET.fromstring(raw)
    by_name={}
    for item in root.iter("Item"):
        props=item.find("Properties")
        if props is not None:
            by_name[props.findtext("string[@name='Name']")]=props
    for flag,(script,anchors) in gq8.OPTIONAL_FEATURE_EVIDENCE.items():
        source=by_name[script].find("ProtectedString[@name='Source']")
        source.text=(source.text or "")+"\n"+"\n".join(anchors)
        manifest["feature_flags"][flag]=True
    raw=ET.tostring(root,encoding="utf-8")
    rehash(raw,receipt)
    return raw,receipt,manifest,active

class Gate(unittest.TestCase):
    def test_valid_covers_eight_domains_and_twenty_one_current_flags(self):
        b,r,m,a=fixture()
        v=gq8.verify(b,r,m,a,HEAD)
        self.assertEqual(len(v["domains"]),8)
        self.assertEqual(v["verified_flag_count"],21)
        self.assertEqual(v["unassessed_new_flags"],[])
        self.assertEqual(v["script_count"],31)
        self.assertEqual(v["real_studio_2client"],"NOT_TESTED")
        self.assertFalse(v["roblox_published"])
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
    def test_ko508_existing_author_policy_is_not_silently_unassessed(self):
        b,r,m,a=fixture()
        anchor="and KoFence.mayCredit(session,id,m,all) then"
        self.assertTrue(m["feature_flags"]["NEUTRAL_DEATH_KO_CURRENT_OWNER_508"])
        result=gq8.verify(b,r,m,a,HEAD)
        self.assertEqual(result["verified_flag_count"],21)
        self.assertEqual(result["unassessed_new_flags"],[])
        root=ET.fromstring(b)
        found=False
        for item in root.findall("Item"):
            props=item.find("Properties")
            if props is not None and props.findtext("string[@name='Name']")=="EGGRUMBLE_SwarmCombat":
                source=props.find("ProtectedString[@name='Source']")
                self.assertIsNotNone(source)
                self.assertIn(anchor,source.text)
                source.text=source.text.replace(anchor,"-- KO508 policy call removed",1)
                found=True
                break
        self.assertTrue(found)
        b=ET.tostring(root,encoding="utf-8")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FALSE_ON_NEUTRAL_DEATH_KO_CURRENT_OWNER_508"):
            gq8.verify(b,r,m,a,HEAD)

    def test_ko508_disabled_flag_cannot_be_certified(self):
        b,r,m,a=fixture()
        m["feature_flags"]["NEUTRAL_DEATH_KO_CURRENT_OWNER_508"]=False
        with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FLAG_DISABLED_OR_UNKNOWN_NEUTRAL_DEATH_KO_CURRENT_OWNER_508"):
            gq8.verify(b,r,m,a,HEAD)

    def test_580_terminal_ai_takeover_absent_fails_closed(self):
        b,r,m,a=fixture()
        self.assertEqual(gq8.verify(b,r,m,a,HEAD)["unassessed_new_flags"],[])
        b=drop_anchor(b,"EGGRUMBLE_BotActors",
            'if session.rules.phase~="ACTIVE" or not folder.Parent then return false end')
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FALSE_ON_AI_TAKEOVER_TERMINAL_FENCE_580"):
            gq8.verify(b,r,m,a,HEAD)

    def test_520_ridge_and_forest_each_needed_for_one_enabled_flag(self):
        ridge="CentralRidgeRight"
        forest="local z=470+math.floor(n/4)*110+(if n==1 then 18 else 0)"
        for missing in (ridge,forest):
            with self.subTest(missing=missing):
                b,r,m,a=fixture()
                b=drop_anchor(b,"EGGRUMBLE_LobbyCastleModesPreview",missing)
                rehash(b,r)
                with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FALSE_ON_TEAM_FIELD_ITEM_RIDGE_FOREST_CLEARANCE_520"):
                    gq8.verify(b,r,m,a,HEAD)

    def test_580_and_520_disabled_flags_cannot_be_certified(self):
        for flag in ("AI_TAKEOVER_TERMINAL_FENCE_580","TEAM_FIELD_ITEM_RIDGE_FOREST_CLEARANCE_520"):
            with self.subTest(flag=flag):
                b,r,m,a=fixture()
                m["feature_flags"][flag]=False
                with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FLAG_DISABLED_OR_UNKNOWN_"+flag):
                    gq8.verify(b,r,m,a,HEAD)

    def test_current_rc_each_secondary_source_anchor_missing_is_red(self):
        for flag,(script,anchors) in gq8.OPTIONAL_FEATURE_EVIDENCE.items():
            for anchor in anchors[1:]:
                with self.subTest(flag=flag,anchor=anchor):
                    raw,receipt,manifest,active=fixture_with_current_26_flags()
                    raw=drop_anchor(raw,script,anchor)
                    rehash(raw,receipt)
                    with self.assertRaisesRegex(gq8.RedGate,
                        "FEATURE_FALSE_ON_"+flag):
                        gq8.verify(raw,receipt,manifest,active,HEAD)

    def test_current_rc_rejects_false_new_zombie_flag_without_command_source(self):
        b,r,m,a=fixture_with_current_26_flags()
        b=drop_anchor(b,"EGGRUMBLE_SevenRoleCombat",
            "ZombieCommander.begin(p,")
        rehash(b,r)
        with self.assertRaisesRegex(gq8.RedGate,"FEATURE_FALSE_ON_ZOMBIE_COMMAND_SQUAD_582"):
            gq8.verify(b,r,m,a,HEAD)

    def test_no_misrepresented_studio_or_publish(self):
        b,r,m,a=fixture()
        r["roblox_publish"]=True
        with self.assertRaisesRegex(gq8.RedGate,"UNAUTHORIZED_PUBLISH"):
            gq8.verify(b,r,m,a,HEAD)
    def test_future_flags_are_visible_but_not_falsely_certified(self):
        b,r,m,a=fixture()
        m["feature_flags"]["FUTURE_AUTHOR_UNKNOWN_999"]=True
        v=gq8.verify(b,r,m,a,HEAD)
        self.assertEqual(v["unassessed_new_flags"],["FUTURE_AUTHOR_UNKNOWN_999"])
    def test_s1_default_must_remain_unchanged_for_this_profile(self):
        b,r,m,a=fixture()
        a["active_profile"]="eggrumble_v3_31"
        with self.assertRaisesRegex(gq8.RedGate,"S1_LEGACY_CHANGED_WITHOUT_OWNER"):
            gq8.verify(b,r,m,a,HEAD)

    def test_current_rc26_flags_are_individually_source_proved(self):
        b,r,m,a=fixture_with_current_26_flags()
        result=gq8.verify(b,r,m,a,HEAD)
        self.assertEqual(result["verified_flag_count"],26)
        self.assertEqual(len(result["verified_optional_flags"]),5)
        self.assertEqual(result["unassessed_new_flags"],[])
        for flag,(script,anchors) in gq8.OPTIONAL_FEATURE_EVIDENCE.items():
            with self.subTest(flag=flag):
                raw,receipt,manifest,active=fixture_with_current_26_flags()
                raw=drop_anchor(raw,script,anchors[0])
                rehash(raw,receipt)
                with self.assertRaisesRegex(gq8.RedGate,
                    "FEATURE_FALSE_ON_"+flag):
                    gq8.verify(raw,receipt,manifest,active,HEAD)

    def test_current_rc_optional_flags_cannot_be_disabled_or_falsely_assessed(self):
        for flag in gq8.OPTIONAL_FEATURE_EVIDENCE:
            with self.subTest(flag=flag):
                b,r,m,a=fixture_with_current_26_flags()
                m["feature_flags"][flag]=False
                with self.assertRaisesRegex(gq8.RedGate,
                    "FEATURE_FLAG_DISABLED_OR_UNKNOWN_"+flag):
                    gq8.verify(b,r,m,a,HEAD)
        b,r,m,a=fixture()
        result=gq8.verify(b,r,m,a,HEAD)
        self.assertEqual(result["verified_flag_count"],21)
        self.assertEqual(result["verified_optional_flags"],[])

if __name__=="__main__":
    unittest.main()
