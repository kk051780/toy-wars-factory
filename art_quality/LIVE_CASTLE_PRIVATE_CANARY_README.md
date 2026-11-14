# #431 Live castle art pilot — private only

The seven principal cosmetic scripts currently exit outside Studio. This PR
tests only **CastleDetailArt** without touching original Game, AI, HUD, egg,
score, terrain, or colliders.

- Studio mode uses the original full castle V3 art unchanged.
- Non-Studio mode remains **OFF by default**. Only an owner's private test
  Place with a **server-side Workspace Boolean Attribute**
  P0D_PRIVATE_LIVE_CASTLE set to true **before the art script begins**
  may use the reduced 36-part gate-silhouette render. The generated PR
  candidate does not set this attribute itself.
- Live-only visuals contain no new lights, transparent screen UI, physics
  colliders, or world-terrain modifications. They are not proof of Android
  speed or live appearance.
- Clear the attribute or restore the official Castle V3 stage to roll back.
- Existing seven-layer source audit remains OPEN; this intentionally removes
  just the one Castle top-level Studio guard behind a private opt-in. The
  other **six** remain Studio-only. Source audit therefore **LIVE_ART_NO_GO**.
- The real-world private PC/Android screenshots, real 15-minute low-end
  Android FPS and thermals, first 3-minute child enjoyment and OWNER visual
  acceptance are all **NOT_TESTED**.
- No Roblox Publish, merge, official RC branch write, main edit, Windows
  action, additional spend, or claim of release readiness.
