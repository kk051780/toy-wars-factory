# P0D S1 native Luau result QA
Packet P0D-S1-RESULT-NATIVE-LUAU-REPLAY-20261112-02

Source: previous OWN RESULT-LOCALIZATION packet under handoffs.
Pinned original and patched full HUD SHA256; no change to existing game source.
Official Luau source fixed at f46d879e28302a430029304f7f6a162aed66f103.
Compile both full HUD scripts, compile and execute the EXACT original marked RESULT_COPY Lua function in native REPL with 15 semantic assertions, reject invalid syntax and deliberately mutated win branch.
Native Luau is NOT Roblox Studio / 2 client / mobile testing.
No RC branch or main changes, and no merge / publish / paid services / PC use.
