import hashlib, pathlib, subprocess, sys, tempfile
R = pathlib.Path(__file__).resolve().parents[2] / "P0D-S1-RESULT-LOCALIZATION-20261112-01"
ORIG = R / "reference/HUD.original.luau.txt"
PATCH = R / "src/client/HUD.client.luau"
PINS = {
  ORIG: "50d9d9a6fc56ee796bc7999ce030c9cfc5d5af697591760c9e444eaefeb5de07",
  PATCH: "b2c17440a486cb94d3c033c065ad26e9f991b88411d7fba340e9ce204583cb3d"
}
for path, expected in PINS.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, "SOURCE_PIN_MISMATCH"
src = PATCH.read_text(encoding="utf-8")
start = src.index("-- RESULT_COPY_BEGIN")
end = src.index("-- RESULT_COPY_END", start) + len("-- RESULT_COPY_END")
assert src.count("-- RESULT_COPY_BEGIN") == src.count("-- RESULT_COPY_END") == 1
result_function = src[start:end]
assert "local function resultLine(s): string" in result_function
oracle = """
local count = 0
local function check(id, winner, team, reason, seconds, expected)
    local actual = resultLine({winner=winner, team=team, reason=reason, time=seconds})
    assert(actual == expected, id .. " expected=" .. expected .. " actual=" .. tostring(actual))
    count += 1
end
check("win", "RED", "RED", "EGG_CAPTURE", 9, "勝利！　卵を運んで得点｜次の準備まで 9 秒")
check("loss", "RED", "BLUE", "EGG_CAPTURE", 9, "敗北！　卵を運んで得点｜次の準備まで 9 秒")
check("draw", "DRAW", "BLUE", "TIME_LIMIT", 3, "引き分け！　制限時間が終了｜次の準備まで 3 秒")
check("castle", "RED", "RED", "CASTLE_DESTROYED", 1, "勝利！　城が破壊された｜次の準備まで 1 秒")
check("quit", "BLUE", "BLUE", "OPPONENT_LEFT", 2, "勝利！　相手が退出した｜次の準備まで 2 秒")
check("empty", "BLUE", "BLUE", "TEAM_EMPTY", 3, "勝利！　相手チームの人数が不足｜次の準備まで 3 秒")
check("unknown", "RED", "RED", "PRIVATE_REASON", 3, "勝利！　勝敗が確定しました｜次の準備まで 3 秒")
check("unknown-winner", "", "RED", "EGG_CAPTURE", 3, "試合終了　卵を運んで得点｜次の準備まで 3 秒")
check("unknown-team", "RED", "NONE", "EGG_CAPTURE", 3, "試合終了　卵を運んで得点｜次の準備まで 3 秒")
check("nan", "RED", "RED", "EGG_CAPTURE", 0/0, "勝利！　卵を運んで得点｜次の準備まで 0 秒")
check("inf", "RED", "RED", "EGG_CAPTURE", math.huge, "勝利！　卵を運んで得点｜次の準備まで 0 秒")
check("negative", "RED", "RED", "EGG_CAPTURE", -2, "勝利！　卵を運んで得点｜次の準備まで 0 秒")
check("huge", "RED", "RED", "EGG_CAPTURE", 3601, "勝利！　卵を運んで得点｜次の準備まで 0 秒")
check("string", "RED", "RED", "EGG_CAPTURE", "9", "勝利！　卵を運んで得点｜次の準備まで 0 秒")
check("floor", "RED", "RED", "EGG_CAPTURE", 2.9, "勝利！　卵を運んで得点｜次の準備まで 2 秒")
print("NATIVE_LUAU_RESULT_ASSERTIONS=" .. tostring(count))
"""
def run(args, expect=True):
    if pathlib.Path(args[0]).name == "luau-compile":
        # Compiler stdout is binary bytecode, not valid UTF-8 text.
        p = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=30)
    else:
        p = subprocess.run(args, capture_output=True, text=True, timeout=30)
    if (p.returncode == 0) != expect:
        raise AssertionError("PROCESS_FAILED args=%s rc=%s stdout=%s stderr=%s" % (args, p.returncode, p.stdout[-1000:], p.stderr[-1000:]))
    return p.stdout
compiler, interpreter = sys.argv[1:3]
with tempfile.TemporaryDirectory() as temp:
    p = pathlib.Path(temp)
    good = p / "actual_result.luau"
    bad = p / "syntax_invalid.luau"
    mut = p / "mutated_result.luau"
    good.write_text(result_function + "\n" + oracle, encoding="utf-8")
    bad.write_text("local function invalid( end", encoding="utf-8")
    run([compiler, str(ORIG)])
    run([compiler, str(PATCH)])
    run([compiler, str(good)])
    run([compiler, str(bad)], False)
    output = run([interpreter, str(good)])
    assert "NATIVE_LUAU_RESULT_ASSERTIONS=15" in output, output
    from_ = 'outcome = if s.winner == s.team then "勝利！" else "敗北！"'
    to_ = 'outcome = if s.winner == s.team then "敗北！" else "敗北！"'
    assert from_ in result_function
    mut.write_text(result_function.replace(from_, to_) + "\n" + oracle, encoding="utf-8")
    run([interpreter, str(mut)], False)
print("P0D_NATIVE_RESULT_COMPILE_FULL_HUD_AND_RUN_15_PASS_NEGATIVE_2_PASS")
