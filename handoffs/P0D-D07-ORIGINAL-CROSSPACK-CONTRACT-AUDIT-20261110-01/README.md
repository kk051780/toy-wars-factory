# P0-D / D07–D08 keyless cross-package integration preflight

**Game:** `TRAP_RAIDERS`; **work:** `p0d-siege-v19`  
**Packet:** `P0D-D07-ORIGINAL-CROSSPACK-CONTRACT-AUDIT-20261110-01`  
**Scope:** READ-ONLY independent package; no existing Luau edited, no new boss AI or damage code, no Roblox Studio operation.

This preflight inspects five previously delivered **keyless original-source** packages. It is not a conversion of new legacy encrypted ZIPs and **does not increase the existing count of 21 recovered original source packages**. This tool does not claim Windows intake, Luau compilation, actual 2-client QA or Roblox publication.

## Required input (only after direct OWNER instruction to Windows Codex)

The separate, existing 21-source intake tool is pinned at `be6e5047eff4edb7e5c46a3c65b10f0afffdabfd`. It writes `packs/<packet>/...` and a `RECEIPT.json`. First perform its GitHub immutable SHA intake to an isolated **new** directory, after preserving the genuine PC Place/source checkpoint. Never treat this static report as that intake receipt.

From this audit package directory:

```powershell
python tools/check_d07_contracts.py --root C:\Temp\TRAP_RAIDERS_KEYLESS_21 --json
python -m unittest discover -s tests -p "test_*.py" -v
```

The checker validates each of 11 relevant original Luau source files against its original `BUILD_MANIFEST.json` `sha256` and `size`; missing, changed, unsafe or non-UTF8 sources yield `BLOCKED`. Only then does it print six contract findings, without editing any file. `SOURCE_STATIC_AUDIT_COMPLETE__NOT_STUDIO` is a **review status**, never a green light to enable gameplay. Both the original 21-intake and actual PC/Roblox tests are separate gates.

## Five immutable original-source commits read by this audit

| Area | Immutable commit | File set |
| --- | --- | --- |
| D07 client visual | `e9b0a7496a69bda3e0e6527ff4d112d50cf70e80` | `GoroganVisualPolicy`, `GoroganVisualPrefab`, `GoroganClientAdapter` |
| D07 server AI | `d65adccef6ce08ec48854ff2cc99f77e69e0765e` | `GoroganServerAICore`, `GoroganServerRuntime` |
| D07 combined wiring | `80a1f0ce15adfb475df0c95677f9966bb760a8ae` | `GoroganCombinedRuntime` |
| D07 physical rig / hit gate | `14935dca217391a7d82d809a3856ee602c446704` | `GoroganRigDriver`, `GoroganDamageBoundary`, `GoroganAttackReceiptWindow` |
| D08 canonical event bridge | `70dcc3b50129c288441452776360588184ca6c22` | `CanonicalEventBridge`, `CanonicalEventServerAdapter` |

All five package identities must be checked against the latest shared issue #218 before use. Do not overwrite any original author's branch or game checkout.

## Next step and safety gates

See [`docs/CONTRACT_AUDIT.md`](docs/CONTRACT_AUDIT.md) for concrete incompatibilities and prioritized remediation by the OWNER's actual Windows Codex only. Use **one** canonical event chooser, **one** Gorogan AI runtime and **one** genuine DamageGate/receipt window per round. Do not trust client-origin input for server damage or boss selection. Retain current/latest PC checkpoint; avoid a blind four-pack bulk install. No `main` write/merge, production publish, spending, P0-A/B/C lock/CAS bypass or modification to five Automations.
