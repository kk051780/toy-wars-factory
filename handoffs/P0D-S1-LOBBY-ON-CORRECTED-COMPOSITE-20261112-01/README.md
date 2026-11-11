# P0-D S1: Lobby deadlock repair atop latest corrected D07/D08 boss game
Game ID: TRAP_RAIDERS; work ID: p0d-siege-v19
Packet: P0D-S1-LOBBY-ON-D07D08-CORRECTED-COMPOSITE-20261112-01

## What is delivered
- src/server/Game.server.luau: **FULL source** of the exact, newer corrected D07/D08 and STOMP ring S1 Game from fixed commit ff291d7a5e6dc53e841552d1abc3cbdf9a805f48, modified at exactly four verified anchors for lobby team rebalancing.
- src/server/LobbyTeamRecovery.luau: **byte-for-byte identical** old owned pure module at 7693d47180c25c078debba9a5cb0ad294580601f.
- docs/SOURCE_PROOF.json: full source SHA256, previous Git blobs, 19 exact source assertions, complete original restoration from reversing four hunk replacements.
- tests/test_source_contract.py: standalone Python contract check (not executed by this chat).

This is an isolated keyless source handoff, not the entire 27-file game project. All existing D07/D08 sources remain in the original 27-file candidate and must continue to be used unchanged. No second match controller and no new game-side remote or monetization.

**Only #220 sole integrator can adopt**: compare current official RC with BOTH the exact corrected composite and the original S1 before editing; if source differs, selectively port four changes instead of blindly overwriting. Do not interpret 19/19 source guards as Luau compilation or Studio2client proof. Do not release without OWNER approval.
