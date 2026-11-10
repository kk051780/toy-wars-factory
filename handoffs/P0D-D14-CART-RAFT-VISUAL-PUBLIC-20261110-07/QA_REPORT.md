# D14 vehicle visual QA

- Python state oracle and Luau source-shape tests: execute `python -m unittest discover -s tests -q`.
- Evidence scope: offline synthetic only; Python does not compile/execute Luau.
- Crypto: AES-256-GCM envelope round-trip checked after deterministic ZIP is built; plaintext ZIP and key stay private.
- **Windows restore / Luau parser / Studio 3D visual / real multiplayer / mobile FPS / Studio exit: NOT_TESTED.**
- PC QA: reject server RemoteEvent source mismatch, stale round/sequence, forged/invalid fields, excessive instance count, invalid coords, client-created occupancy authority, and extra physics. Verify 2 seats correspond to server truth, vehicle model never allows a player to escape walls. Do not claim real vehicle playability.
