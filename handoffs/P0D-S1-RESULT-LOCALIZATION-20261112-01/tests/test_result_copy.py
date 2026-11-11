# S1 result-only source patch: runnable stdlib Python tests (NOT Roblox/Studio).
import hashlib, json, math, pathlib, re, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "reference" / "HUD.original.luau.txt"
PATCHED = ROOT / "src" / "client" / "HUD.client.luau"
MANIFEST = ROOT / "BUILD_MANIFEST.json"
ORIGINAL_SHA = "50d9d9a6fc56ee796bc7999ce030c9cfc5d5af697591760c9e444eaefeb5de07"
PATCHED_SHA = "b2c17440a486cb94d3c033c065ad26e9f991b88411d7fba340e9ce204583cb3d"
OLD_BLOCK = '''    if s.phase == "RESULTS" then
        if s.winner == "DRAW" then return "引き分け！ 次の試合まで " .. tostring(s.time) .. " 秒" end
        return (if s.winner == s.team then "勝利！" else "試合終了")
            .. " 理由：" .. tostring(s.reason) .. "　再戦まで " .. tostring(s.time) .. " 秒"
    end'''
NEW_BLOCK = '    if s.phase == "RESULTS" then return resultLine(s) end'
REASONS = {
    "EGG_CAPTURE": "卵を運んで得点",
    "CASTLE_DESTROYED": "城が破壊された",
    "OPPONENT_LEFT": "相手が退出した",
    "TEAM_EMPTY": "相手チームの人数が不足",
    "TIME_LIMIT": "制限時間が終了",
}

def reference_results(winner, team, reason, time):
    outcome = "試合終了"
    if winner == "DRAW":
        outcome = "引き分け！"
    elif winner in ("RED", "BLUE") and team in ("RED", "BLUE"):
        outcome = "勝利！" if winner == team else "敗北！"
    description = REASONS.get(reason, "勝敗が確定しました") if isinstance(reason, str) else "勝敗が確定しました"
    safe_seconds = math.floor(time) if isinstance(time, (int, float)) and not isinstance(time, bool) and math.isfinite(time) and 0 <= time <= 3600 else 0
    return f"{outcome}　{description}｜次の準備まで {safe_seconds} 秒"

class SourcePatchContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o = ORIGINAL.read_text(encoding="utf-8")
        cls.p = PATCHED.read_text(encoding="utf-8")

    def test_original_source_pin(self):
        self.assertEqual(hashlib.sha256(self.o.encode()).hexdigest(), ORIGINAL_SHA)

    def test_patch_source_pin(self):
        self.assertEqual(hashlib.sha256(self.p.encode()).hexdigest(), PATCHED_SHA)

    def test_full_source_reverts_exactly(self):
        self.assertEqual(self.p.count(NEW_BLOCK), 1)
        self.assertEqual(self.o.count(OLD_BLOCK), 1)
        stripped = re.sub(r"-- RESULT_COPY_BEGIN[^\n]*\n.*?-- RESULT_COPY_END\n\n", "", self.p, flags=re.S)
        self.assertEqual(stripped.replace(NEW_BLOCK, OLD_BLOCK), self.o)

    def test_no_second_remote_or_new_authority(self):
        for needle in ('remote:FireServer', 'remote.OnClientEvent', 'TrapRaidersS1Remote'):
            self.assertEqual(self.p.count(needle), self.o.count(needle))
        addition = self.p[self.p.index("-- RESULT_COPY_BEGIN"):self.p.index("-- RESULT_COPY_END")]
        for forbidden in ('FireServer', 'OnServerEvent', 'TakeDamage', 'SetAttribute', 'DataStore', 'LoadCharacter', 'RemoteEvent', 'math.random'):
            self.assertNotIn(forbidden, addition)

    def test_no_raw_reason_leak_after_patch(self):
        addition = self.p[self.p.index("-- RESULT_COPY_BEGIN"):self.p.index("-- RESULT_COPY_END")]
        for code, japanese in REASONS.items():
            self.assertIn(code + ' = "' + japanese + '"', addition)
        self.assertNotIn('tostring(s.reason)', addition)
        self.assertIn('type(s.time) == "number"', addition)
        self.assertIn('math.floor(s.time)', addition)

    def test_reason_fallback(self):
        self.assertIn("勝敗が確定しました", self.p)
        self.assertIn('outcome = "試合終了"', self.p)

    def test_manifest_strict_public_source(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(set(m), {"files", "format", "game_id", "packet_id", "public_source_allowed", "work_id"})
        self.assertEqual(m["format"], "P0D_PUBLIC_SOURCE_V1")
        self.assertTrue(m["public_source_allowed"])
        self.assertEqual(m["game_id"], "TRAP_RAIDERS")
        seen = set()
        for f in m["files"]:
            self.assertEqual(set(f), {"path", "size", "sha256"})
            p = pathlib.PurePosixPath(f["path"])
            self.assertFalse(p.is_absolute())
            self.assertNotIn("..", p.parts)
            self.assertNotIn(f["path"].lower(), seen)
            seen.add(f["path"].lower())
            data = (ROOT / f["path"]).read_bytes()
            self.assertEqual(len(data), f["size"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), f["sha256"])
        self.assertEqual(len(seen), 4)

class ResultCopyOracle(unittest.TestCase):
    def test_five_reasons(self):
        for code, ja in REASONS.items():
            self.assertIn(ja, reference_results("RED", "RED", code, 9))

    def test_win_lose_draw_and_spectator(self):
        self.assertTrue(reference_results("RED","RED","EGG_CAPTURE",9).startswith("勝利！"))
        self.assertTrue(reference_results("RED","BLUE","EGG_CAPTURE",9).startswith("敗北！"))
        self.assertTrue(reference_results("DRAW","RED","TIME_LIMIT",9).startswith("引き分け！"))
        self.assertTrue(reference_results("", "RED","UNKNOWN",9).startswith("試合終了"))
        self.assertTrue(reference_results("BLUE", "NONE","UNKNOWN",9).startswith("試合終了"))

    def test_unknown_reason_never_leaks_raw_token(self):
        actual = reference_results("BLUE", "RED", "MALFORMED_INTERNAL_REASON", 9)
        self.assertIn("勝敗が確定しました", actual)
        self.assertNotIn("MALFORMED", actual)

    def test_time_invalid_clamped(self):
        for t in (float("nan"), float("inf"), -1, 3601, None, "9", True):
            self.assertTrue(reference_results("RED", "RED", "EGG_CAPTURE", t).endswith("0 秒"))
        self.assertTrue(reference_results("RED","RED","TIME_LIMIT",2.99).endswith("2 秒"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
