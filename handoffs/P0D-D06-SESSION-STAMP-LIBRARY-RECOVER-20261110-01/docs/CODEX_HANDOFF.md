# Codex integration guide — NOT an automatic PC trigger

1. Verify game/work ID, local latest HEAD, latest Studio-saved Place ZIP and manifest. Do not roll back v37 changes. Stop if source SHA unknown.
2. Confirm `V37_STATUS=STUDIO_QA_PASS` for egg event and 2-client consistency, or defer this packet.
3. Copy `SessionStampCore.luau` and `SessionStampViewModel.luau` into an isolated **ServerScriptService**, not ReplicatedStorage or client scripts. Use actual Studio ModuleScripts and adapt `require()` paths.
4. ONLY actual server `RoundCoordinator` calls `.apply` after it has irrevocably finalized a round. Verify there is a correct server-generated matchId, roster/userId, a 7-job and 4-map ID, winner, contribution, and qualifying server actions. The `kind` marker is not security authorization.
5. Maintain each player's `state` in a server-only map. Do not reuse another user's state. On server termination the state is intentionally lost. Do not write it to `DataStoreService` under this packet.
6. Send only `.view(state)` and `SessionStampViewModel.fromRewardView(...)` to the client's existing result UI, no raw state or internal ledger. Display **session-only, not saved** text prominently.
7. Prevent double `match_complete`: original coordinator must call once; module ledger independently rejects repeats. Correctly handle AFK, loss, victory, win+assist, disconnect/rejoin, team swap, round boundary, capacity.
8. Use original v37 banner/rematch UI, add a single tiny lobby visual pedestal if one is not present. The two preview items grant **no combat stats**.
9. Run isolated `SessionStampSmoke.server.luau` from the same ServerScriptService test folder; remove it before packaging production Place.
10. Studio QA: initial player +1 on valid loss, +2 win/assist, no double award, AFK0 and finalized, first/second milestone cosmetic preview; 2client opposite-team no reward leak; UI stays unique after rematch; existing 4 stages, 7 jobs, NPC and S1 egg flow unchanged; mobile emulator checks.
11. Save `CHECKPOINT`, `RESUME`, QA, Feature Matrix, original Place & ZIP SHA. Only close the Studio process you launched. Public repo never receives plaintext source/assets without explicit OWNER public-release permission.

The expected integration SHA is **UNKNOWN** until Codex reads the actual local v37/v36.1 files. No automatic `Studio QA PASS` is granted by the 50 Python tests.
