# Resume instructions for OWNER Windows Codex

1. Do NOT stop the latest v37/v39 work. First independently inspect the real Windows PC's `CHECKPOINT`, `RESUME`, `BUILD_MANIFEST`, `QA_REPORT`, actual Place hash and successful Studio QA.
2. Restore this v43-A packet from its GitHub handoff using OWNER's private one-time key. Validate original ZIP SHA, manifest and 56 offline tests in a fresh isolated folder.
3. Treat v43-A as *reference-only*; only integrate into the real game after v37 final QA and v39 stamping result gate are satisfied. First use S1 existing NPCs, no extra spawns; future S2–S4 expansion is separate.
4. Build server RoundCoordinator adapter, actual NPC targeting and PvP/neutral combat integration, UI for mobile and 2/3-client Studio QA. Do not treat the test-supplied `team`, `distance` or `wantsCapture` as trusted in a real RemoteEvent.
5. Save a new versioned Place and full source with `CHECKPOINT/RESUME/QA/FEATURE_MATRIX`, manifests and hashes; stop/play/edit/save and close only your own Roblox Studio processes; report facts to #213 and #217 without code or key.
6. No public repo plaintext game uploads, main changes, merge, publish, Robux charges or additional spending.
