# WORLD G8 | Private three-level Harbor → Sea Glass Castle → Sky Castle
Standalone never-published Roblox Studio demonstration. Unlike previous G7 cosmetic-only preview, this script implements **real player transport** via ProximityPrompt E/tap and server checks; no original S1 match mechanics.

Flow: PORT→SEA→SKY→PORT (optional reverse SKY→SEA→PORT). All three positions are non-collapsing broad 76x76 collision floors with a safe floor and rails, and every remote level has direct harbor return. Spawn in PORT only. Server performs character/Humanoid/HumanoidRootPart validation, authoritative squared distance <=196, approved graph, 1.6s cooldown, alive check, fixed destination and clearing velocity. Does NOT trust client-supplied positions or RemoteEvents. Names and 3-sec prompts Japanese, mobile tap possible.

No swimming physics, no 2-client tested collision, no persistent economy, no egg, no Wind, no Guardian, no community model/paid item, no main/RC game write. Offline native Luau only proves pure rules; Rojo proves Place script embed, NOT Roblox engine test. End users must open Studio as a separate new unpublished Place and press Play.

Studio acceptance: (1) starts on harbor, (2) tap left-side portal to dry sea, (3) tap right-side sea portal to sky, (4) tap sky right-side back to harbor, (5) try abuse rapid taps/long-distance/respawn, (6) compare RED and BLUE two client, (7) phone landscape visual & FPS/rails. Report any false destination, unsafe landing, confusing visual cue before future S2 integration.

## Product boundary
This demo is not H1, not an existing live egg game, and not a release candidate. Studio-only source functionality, with all real gameplay physics and mobile comprehension awaiting a human run.
