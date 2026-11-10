# D15 QA report

- Reference module: `luau/TrapRescueCore.luau` (source written; NOT compiled by Luau compiler; NOT executed in Roblox Studio).
- Python model and source contract tests: 80/80 PASS — Python `unittest discover -s tests -q`.
- Zip/manifest integrity: will be recorded after archive construction.
- AES-256-GCM local encrypt→decrypt exact bytes: will be recorded after sealing.
- GitHub remote readback: NOT_TESTED until GitHub upload and readback.
- Real server `OnServerEvent` authentication/latency/physics/3D map/path validation: NOT_TESTED.
- 2client/3client, smartphones, FPS, Studio Play/Stop and owned instance close: NOT_TESTED.
- Existing v37 egg win and v39 stamp / v42 progression regression: NOT_TESTED.
- Owner's PC source SHA: UNVERIFIED_PC_LOCAL.

**Hard limit:** Reference trust boundary is not a substitute for server-owned match/coordinator logic. Integration MUST reject all client claims and perform real combat damage from the server, after double checking active state and target.
