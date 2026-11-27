"""Non-author G4 V2.1 SOURCE-only gate. No CLAIM/RC/Studio/Native authority."""
import hashlib
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

BASE = "72d620d86761f2aa5da80263a251cc5fa63fecbb"
PLACE_SHA = "cacc922501717c417c05e60bdf3c32c6d917e3622931401ab45fc8eeed3da3c5"
BOT_SHA = "c38bcf82df581d2d9f105f9d7843eef0eff8e8bd6315b8520765ee646e1c5051"
ROUTER_SHA = "92d44fd4635878fdfbbf1d8f3db691537ae348472dd5770f82421f78b00d5f52"
G4_CANDIDATE_SHA = "44a9d578d4225d56152be1139f3925b65376d5c4e33ba3d3505a2e4db1cf94fd"
BOT = "ServerScriptService/EGGRUMBLE_BotActors.luau"
ROUTER = "ServerScriptService/EGGRUMBLE_BotPathRouter.luau"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def source_map(place):
    root = ET.fromstring(place)
    scripts, instances = {}, []

    def walk(item, prefix):
        props = item.find("Properties")
        assert props is not None
        name = props.find("string[@name='Name']")
        assert name is not None and name.text
        path = (prefix + "/" if prefix else "") + name.text
        cls, referent = item.get("class"), item.get("referent")
        instances.append((path, cls, referent))
        src = props.find("string[@name='Source']")
        if src is None:
            src = props.find("ProtectedString[@name='Source']")
        if src is not None:
            assert cls in ("Script", "LocalScript", "ModuleScript")
            suffix = ".server.luau" if cls == "Script" else ".client.luau" if cls == "LocalScript" else ".luau"
            key = path + suffix
            assert key not in scripts
            scripts[key] = (src.text or "").encode("utf-8")
        for child in item.findall("Item"):
            walk(child, path)

    for item in root.findall("Item"):
        walk(item, "")
    assert len(scripts) == 69 and len(instances) == 75
    assert len({x[2] for x in instances}) == 75
    return scripts, instances

def replace_one(place, before, after):
    assert b"]]>" not in before + after
    pre = b'<string name="Source"><![CDATA[' + before + b']]></string>'
    post = b'<string name="Source"><![CDATA[' + after + b']]></string>'
    assert place.count(pre) == 1 and pre != post
    return place.replace(pre, post, 1)

def wall_hits_segment(a, b, rect):
    t0, t1 = 0.0, 1.0
    for start, delta, lo, hi in ((a[0], b[0]-a[0], rect[0], rect[1]),
                                  (a[1], b[1]-a[1], rect[2], rect[3])):
        if abs(delta) < 1e-12:
            if not lo <= start <= hi:
                return False
        else:
            x, y = sorted(((lo-start)/delta, (hi-start)/delta))
            t0, t1 = max(t0, x), min(t1, y)
            if t0 > t1:
                return False
    return True

class ActualH72SourceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = os.environ.get("GQ470_H72_ARTIFACT_DIR")
        if not root:
            raise RuntimeError("ACTUAL H72 ARTIFACT REQUIRED; never fixture-only GREEN")
        root = Path(root)
        cls.place = (root / "EGGRUMBLE_REAL69_PRIVATE.rbxlx").read_bytes()
        assert len(cls.place) == 829213 and sha(cls.place) == PLACE_SHA
        cls.scripts, cls.instances = source_map(cls.place)
        cls.files = {p.relative_to(root / "sources").as_posix(): p.read_bytes()
                     for p in (root / "sources").rglob("*.luau")}
        assert cls.scripts == cls.files  # all actual 69 script bytes
        assert len(cls.scripts[BOT]) == 19625 and sha(cls.scripts[BOT]) == BOT_SHA
        assert sha(cls.scripts[ROUTER]) == ROUTER_SHA

    def test_exact_69_sources_and_75_instances(self):
        self.assertEqual(69, len(self.scripts))
        self.assertEqual(75, len(self.instances))

    def test_current_server_authority_has_collision_and_los(self):
        bot, router = self.scripts[BOT], self.scripts[ROUTER]
        for token in (b"local goHome=me.heldEggs>0",
                      b"Rules.depositEggs(session.rules,id,me.heldEggs)",
                      b"Rules.takeEggs(session.rules,id,1,enemy.id)",
                      b"if actualDist<=ACTION_DISTANCE and clearActionPath(actor,actors,actualTarget,actionTarget)",
                      b"if not targetPart or not targetPart.Parent then return false end"):
            self.assertIn(token, bot)
        self.assertIn(b"routeClear(here,here+direction*step,actors)", router)
        self.assertIn(b"params.RespectCanCollide=true", router)

    def test_direct_return_at_sidewall_is_blocked_but_gate_is_not(self):
        # Actual Host: CastleSideRight x=15 +/-1, z=-13..13.
        # This shows a direct fallback obstacle, NOT actual Roblox navmesh.
        wall = (14., 16., -13., 13.)
        self.assertTrue(wall_hits_segment((19., 0.), (-216., -68.), wall))
        self.assertFalse(wall_hits_segment((0., -22.), (0., -30.), wall))

    def test_exact_changed_script_and_off_reversible(self):
        old = self.scripts[BOT]
        synthetic = old.replace(b"local goals:{[string]:string}={}",
                                b"local goals:{[string]:string}={} -- negative fixture", 1)
        self.assertNotEqual(old, synthetic)
        altered = replace_one(self.place, old, synthetic)
        current, instances = source_map(altered)
        self.assertEqual(self.instances, instances)
        self.assertEqual({BOT}, {k for k in self.scripts if current[k] != self.scripts[k]})
        self.assertEqual(self.place, replace_one(altered, synthetic, old))
        self.assertNotEqual(sha(synthetic), G4_CANDIDATE_SHA)

    def test_only_original_author_exact_candidate_can_be_reviewed(self):
        # Without actual G4 V2.1 bytes, never fake candidate PASS.
        path = os.environ.get("GQ470_G4_V21_ACTORS")
        if not path:
            self.skipTest("V2.1 author body not supplied; comparison remains NOT_TESTED")
        candidate = Path(path).read_bytes()
        self.assertEqual(21604, len(candidate))
        self.assertEqual(G4_CANDIDATE_SHA, sha(candidate))
        original = self.scripts[BOT]
        altered = replace_one(self.place, original, candidate)
        new, instances = source_map(altered)
        self.assertEqual(self.instances, instances)
        self.assertEqual({BOT}, {k for k in self.scripts if new[k] != self.scripts[k]})
        self.assertEqual(self.place, replace_one(altered, candidate, original))
        # SOURCE ONLY. Native/Studio/Android/OWNER cannot be inferred.

class MutationNegatives(unittest.TestCase):
    def test_unknown_cdata_is_refused(self):
        with self.assertRaises(AssertionError):
            replace_one(b"<xml/>", b"OLD", b"NEW")

    def test_double_source_cdata_is_refused(self):
        a = b'<string name="Source"><![CDATA[OLD]]></string>'
        with self.assertRaises(AssertionError):
            replace_one(a + a, b"OLD", b"NEW")

    def test_cdata_breakout_is_refused(self):
        with self.assertRaises(AssertionError):
            replace_one(b"body", b"OLD", b"NEW]]>")

    def test_empty_delta_is_refused(self):
        a = b'<string name="Source"><![CDATA[OLD]]></string>'
        with self.assertRaises(AssertionError):
            replace_one(a, b"OLD", b"OLD")

    def test_no_wall_false_positive_off_lane(self):
        self.assertFalse(wall_hits_segment((20., -25.), (-200., -25.), (14., 16., -13., 13.)))

if __name__ == "__main__":
    unittest.main()
