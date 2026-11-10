# TRAP RAIDERS D16 — visual-only size FX reference (NOT integrated)

Standalone **pure Luau** `src/ScaleFxCore.luau` and Python oracle. Controls only short-lived visual state for `GIANT_ONE` (1.6x) or `MINI_ALL` (0.7x) for 8 seconds. No actual character model changes, collision, abilities, stats, or network bindings. Does not pick weather/event: the already-existing D08 server event picker must invoke it once. ID and match validation do **not** authenticate network callers. Never use a client Remote to call `begin`.

Test offline: `python -m unittest discover -s tests -q`. Archive preflight: `python tools/verify_packet.py ../TRAP_RAIDERS_D16_SCALE_FX.zip`. Luau/Studio, 2client, mobile, PC actual QA **NOT_TESTED**. Dependencies D08, D01. Pure code is a *candidate*, not an executable game module until reviewed and integrated by Windows Codex.
