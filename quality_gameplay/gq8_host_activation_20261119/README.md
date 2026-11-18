# GQ8 P0: Real55 host cannot start in the official private Place

Real official [run #44393525211](https://github.com/kk051780/toy-wars-factory/actions/runs/44393525211) produced a 55-script Place but the central Studio-only game Host `ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview` is a **ModuleScript**, and no other selected source imports it. The queue, AI and multi-egg castle match are therefore never initialized by this Host. The prior successful Native/Rojo source gate did not test runtime activation.

This candidate changes **only the class** of the existing Host to Script by retaining the original route and bytes and selecting a `.server.luau` filepath. All 55 source contents stay byte-identical, other 54 routes stay identical, no duplicate host, no Roblox publish, purchases, data store or payment. Original Real55 Place is an exact OFF55 rollback.

Test: original Place must FAIL the host activation assertion; candidate 55-source project keeps 55/55 byte fidelity; pinned Rojo compiles actual ON55 Place where Host is Script; OFF55 Place must be byte-identical to the official artifact. This is **SOURCE gate**, not Studio/Android/FUN acceptance.

Integration: #839 naming, #810 owner priority, #220 sole B writer with fresh non-force expected_SHA CAS and SAME NEW HEAD gate. Merge with newer REAL56/57/59 candidates without dropping their independent functionality. Next physical Studio Solo and 2-client test, attack/egg/castle/round/replay and Android/3-min FUN. No author ACK required.
