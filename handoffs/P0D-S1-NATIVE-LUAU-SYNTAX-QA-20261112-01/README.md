# P0-D S1 — independent native Luau compiler gate

This is a read-only syntax/bytecode compile check on the exact 17 Luau source files in game TRAP_RAIDERS's already verified corrected D07/D08 + spatial visual composite, immutable commit `ff291d7a5e6dc53e841552d1abc3cbdf9a805f48`.

The official open-source **Luau compiler** is built with CMake from the fully pinned upstream `luau-lang/luau` commit `f46d879e28302a430029304f7f6a162aed66f103`, not from a floating version or third-party binary. The workflow lives only on isolated branch `handoff/p0d-s1-native-luau-syntax-gate-20261112-01`, with read-only token. Game code and original independent 27/27 source/18/18 assembly pass remain untouched.

The runner `tools/native_luau_syntax_gate.py` compiles each of the 17 actual .luau source files and verifies the compiler accepts a valid Luau typed-function and **rejects deliberately broken Luau syntax** (negative control). Syntax compile success validates language parsing and bytecode compilation only. It does not load Roblox DataModel types, execute the code, validate server/client physics or gameplay, measure boss warnings, enable D07/D08 gates, test Roblox Studio or approve release.

Preceding genuine Python independent source/assembly QA: [GitHub Actions run 43033428465](https://github.com/kk051780/toy-wars-factory/actions/runs/43033428465), PASS 27/27 public hashes, 18/18 source units, 4/4 tamper tests, and Rojo singleton authority. That prior QA is not a substitute for this native compiler check.

Run syntax checker after building official compiler:

```sh
python3 handoffs/P0D-S1-NATIVE-LUAU-SYNTAX-QA-20261112-01/tools/native_luau_syntax_gate.py /path/to/luau-compile
```

**Scope only:** S1 owner #220 still exclusively writes `rc/p0d-s1-kids-rc01`. No main/RC merge, public Roblox publication, paid service, PC Codex or approvals are implied. If official CI fails, the precise native syntax defect is a release blocker, not a license to ignore or downgrade the parser failure. Whole game release progress remains UNKNOWN_PENDING_GATE_AUDIT.
