# S1 solo local practice integration (opt-in, release owner only)

Base: `35d7d0525388e885aac8281eff2315a59831e0cf`, `releases/P0D_S1_KIDS_RC01`. Compare the latest integration branch and the true Windows Place before adopting; never overwrite changed project source. Source is optional, NO automatic run from this handoff.

1. Sole #220 integrator copies `src/LobbyPracticeModel.luau` and `src/LobbySoloPractice.client.luau` into **RC `src/client/`**, not into `src/server` or `src/shared`.
2. Existing `default.project.json` under `StarterPlayer` / `StarterPlayerScripts` gets exactly one new mapping:

   `"TrapRaidersSoloPractice": {"$path":"src/client/LobbySoloPractice.client.luau"}`

   The `LobbyPracticeModel.luau` sits as a sibling `ModuleScript` under that same mapped `StarterPlayerScripts`. Because `StarterPlayerScripts` presently maps individual `$path` LocalScript under a plain Rojo object, **also add an explicit ModuleScript mapping**:

   `"LobbyPracticeModel": {"$path":"src/client/LobbyPracticeModel.luau"}`

   Both children will be replicated into `PlayerScripts` as siblings at runtime. Do NOT mount the module twice (e.g., via mapping the entire `src/client` folder plus individual scripts). Maintain original `TrapRaidersHUD` mapping unchanged.
3. Ensure remote `TrapRaidersS1Remote` remains the **single** existing server-owned RemoteEvent; this optional local practice only listens to `OnClientEvent`; no `FireServer` and no client-awarded XP/coin/score/HP.
4. Actual mini QA: 1 player enters -> local yellow target and local-only hit counter visible; rotate away or walk too far -> no increment; 0.45s cooldown; hit cap 99; second player enters -> COUNTDOWN -> both target+UI disappear on both clients; ACTIVE/RESULTS -> still absent. Leave and rejoin, respawn while still solo, invalid server snapshot and stale serial; verify no zombie dummy. Track in a separate document; Python oracle does not execute Luau.
5. On 320px screen landscape, verify bottom-right practice button doesn't overlay bottom-left role buttons or native Roblox touch controls, and target doesn't occlude objectives; adjust presentation only under independent review.
6. Remove both mapping entries and copied sources to revert. Do not disable normal HUD, alter `Config.MinPlayers=2`, or touch #220 branch from this isolated feature lane.

No PC Codex action is initiated by GitHub comments. Native Luau parse/Studio two-client/phone QA, actual first-session completion and retention remain **NOT_TESTED / UNKNOWN** until evidence is recorded.
