# S1 actual original Game alternative victory QA (OFFICIAL RC pinned)

This independent keyless native-Luau test exercises **two win conditions not covered by the earlier egg-capture controller replay**: no-score time-limit DRAW, and castle HP destroyed after 22 bounded Raider hits; then a third round with one castle hit wins on HP tiebreaker when the clock reaches 0. It verifies role-independent server-only authority, line-of-sight/direction/distance, attack replay/cooldown, scores, and result→lobby→countdown→rematch transitions.

Production source inputs are ALL loaded in GitHub CI by **Git blob SHA1** from official commit `5dc6c958ea5549b1e859d6d250e6179e731181fb` at `releases/P0D_S1_KIDS_RC01/`: original unchanged full `Game.server.luau`, `S1Rules.luau`, `LobbyTeamRecovery.luau`, `Config.luau`. Only Roblox service require bindings are substituted to exact native-loaded modules; external Roblox services are fake. No RC source modification.

Five? Six deliberately modified unsafe original-source variants MUST be rejected: force RED instead of draw, skip castle win, attack through walls, attack while facing away, trust malicious client damage amount, bypass attack cooldown. Original game code is never altered in the repository. Test-only mock raycast and humanoid are not an actual Studio simulation; actual 2-client physical gameplay, phone controls, bot encounters and boss event remain NOT_TESTED.

This new isolated slice does not duplicate Game.server native egg heist success #218 #6808309157, nor does it implement/change the ongoing Guardian trap code under sole #220 integrator. It does not alter the existing first-release 75/100 score or authorize publication.

Build genuine upstream Luau interpreter `f46d879e28302a430029304f7f6a162aed66f103` with CMake in CI. Verify `PUBLIC_SOURCE_V1` two-file SHA256 manifest. Public keyless source. Never touch main, rc, Roblox publishing, Windows Codex, existing five Automations or protected P0-A/B/C.
