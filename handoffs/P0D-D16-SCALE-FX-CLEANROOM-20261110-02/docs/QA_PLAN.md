# D16 separate acceptance gates

- Local Python oracle: reject duplicate/malformed event, player, match, roster and time data, replay after close, stale epochs, capacity overflow, early match close and 8-second TTL. Static Luau inspection also runs, but does not prove native Luau syntax or semantics.
- PC preflight: preserve real newest PC source/Place and verify fixed commit/manifest. Check Luau parser, Core API and server authoritative call site; D08 singleton already owns RNG and event activation, do not register another chooser or RemoteEvent callback.
- Unpublished Studio: S1 two clients, selected GIANT_ONE one-player visuals, MINI_ALL for all participants, 8s expiry, no physics size/hitbox or combat advantage, stale/disconnect/replay end-cleanup. Opt-in visual renderer requires separately reviewed D16 client replica, not part of this pack.
- Accessibility: reduced motion/low-detail check on mobile landscape and actual phones; if not run label NOT_TESTED.
- Studio: Play/Stop/Edit/save in isolated reviewed session, normal exit and PID disappearance. Report actual evidence to #213 and acceptance status to #218.

**Current:** offline Python behavioral oracle and Luau text-policy only; Windows Codex, native Luau parsing, Studio, PC integration and visual display NOT_TESTED. No production enablement.
