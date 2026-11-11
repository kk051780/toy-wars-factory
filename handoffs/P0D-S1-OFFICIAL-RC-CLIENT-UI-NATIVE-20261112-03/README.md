# Genuine native Luau client UI integration test — official S1 RC

This isolates a previously untested **client behavior** slice. It executes the actual full `HUD.client.luau` and `FirstMinuteCoach.client.luau` (both mounted LocalScripts), along with original `FirstMinuteModel.luau`, all fixed to the latest sole integrator's official RC commit `5dc6c958ea5549b1e859d6d250e6179e731181fb`.

Original git object SHA1: HUD `458a23e83d261c51b3bec174e36e183960532f8c`; Coach `63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9`; shared Model `fcdc399bf95b6cd0532691718f5a54e8a4fd84b4`. They are `git show`-fetched from the *official* immutable commit in the CI checkout and git blob SHA1 checked before any executable is assembled.

The only modified original code is the Coach's `local Model = require(shared:WaitForChild("FirstMinuteModel"))` line mapped to an already executed **exact** original `FirstMinuteModel.luau` module within one native Luau process; this substitutes Roblox's ModuleScript reference, not any model/GUI logic. No actual production client script is written or modified.

- A test-only in-memory fake creates Roblox `ScreenGui`, `Frame`, `TextLabel`, `TextButton`, `RemoteEvent`, `UserInputService`, enums and UDim helpers. The real two LocalScripts instantiate the real menu and subscribe to the same fake server-owned existing Remote.
- Simulated server `SNAPSHOT` messages drive both UI scripts. Assertions cover lobby role selection, F/touch attacks with monotonic sequence and no target/damage/position, keyboard gameProcessed blocking, help hide/reopen, active phase 0/13/34/61 second onboarding, carried egg, scoring, result, win/loss/draw Japanese reasons and stale packets.
- Five deliberate mutations of the actual original UI source (client security input, result translation, invalid damage payload, help button, result coach copy) must cause assertion failure.
- Uses official upstream pinned Luau compiler and CLI source commit `f46d879e28302a430029304f7f6a162aed66f103` and GitHub Actions for genuine execution proof.

No claims about real 2-player networking, actual Roblox `Instance` rendering, device screen legibility/taps/FPS, latency, real engine/life-cycle, child playability, P2W/Roblox publishing or Studio. This is **native Luau with explicit test-only Roblox API doubles**, not native Roblox Studio.

Sole integrator #220 controls official RC and global 100-point score. This independent client QA can report only its own fixed acceptance percent. No official RC/main/merge/paid/Roblox live/Windows Codex/P0ABC/5 automations changes.
