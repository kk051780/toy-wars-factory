# Resume on Windows Codex

1. Obtain the owner-provided GitHub encrypted artifact and secret key, decrypt into a fresh local ZIP, run the packet's `verify_packet.py` and Python tests.
2. Recover the newest game source/Place from **local** `p0d-siege-v19` checkpoint. Do not infer completeness from GitHub issue comments.
3. Compare real v37 existing result UI and server-owned round events before integrating a single feature slice.
4. First finish missing v37 server/client QA; only then wire `SessionStampCore` into the privileged server coordinator, never Remote directly.
5. Run actual Luau smoke and Studio 2client/mobile checks, remove smoke script from production. Update manifest and report; keep `NO_PUBLISH`.
