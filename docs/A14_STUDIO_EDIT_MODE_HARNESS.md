# Independent A14 hosted Roblox Studio feasibility gate

1. Existing connected Github run #41137070161 exported the exact 54,753-byte XML and actual archive ID #13015999142. Independent security review of PR147 before any remote execution of an artifact from its unreviewed producer. No change to that PR in this lane.
2. Run this probe only on a trusted Windows environment with Roblox Studio Authenticode status VALID, signed by Roblox, and an authenticated copy of the same XML. The provided PowerShell wrapper validates the exe's signature; the Python gate validates the place's exact content digest before invoking Studio CLI in edit mode only. Real studio tool install, GUI availability and sign-in are not established.
3. Keep a complete provider record: GitHub main source SHA, Actions run/attempt/HEAD, artifact ID/ZIP SHA, XML SHA, signed Studio binary version, host/runner version, stdout, stderr, Studio output file, exit status. Redact auth and private account data before publishing any logs.
4. A unique Studio output marker proves only edit-mode local file load and expected object names/classes. NEVER count it as Roblox Play, server boot, multiplayer, touch/mobile or public publish. A separate server Play test will require a new trusted harness and independent evidence.
5. STOP on any artifact/host mismatch, missing Studio exe, timeout, missing/duplicate output marker or new main source; do not retry automatically. Official release gate remains on hold.

## Additional direct-CLI hardening (PR149)
The Python run entrypoint also verifies Windows Authenticode through PowerShell before launching Studio. The exact Luau probe bytes are pinned to SHA256 `75676b530b76f6182fc5b98196759f4e0f9512562eea6b1e1510554ad6dbd549`; a changed script is refused before launching. Simulated Windows subprocesses only test the control flow and cannot be counted as Studio-runtime proof. No hosted Windows runner job or Roblox account access is configured by this change.
