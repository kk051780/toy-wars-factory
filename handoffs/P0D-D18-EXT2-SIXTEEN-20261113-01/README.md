# EGG RAID RUMBLE / D18-COLLECTION EXT2 — 16件の独立3Dキャラソース

- 台帳: #283 / #219 / #218、元 #278 72+12件はそのまま
- 可視ブランド: EGG RAID RUMBLE / internal TRAP_RAIDERS / work_id p0d-siege-v19
- 新規16件 = 星くず漂流駅4 / 赤熱の歯車図書館4 / 時雨の時計森4 / 雪雲のお菓子城4
- 配分: BEAST4, SPELL3, MOUNT3, ITEM2, ZOMBIE2, TRAP2
- **ソース3Dプロトタイプのみ100件 (既存72+12+新規16)。ゲーム内で100件が所有・装備・実使用可能という意味ではない。**

## 真正ソース

`src/Ext2Catalog.luau` — 新16件の名前・3秒識別の三特徴・パレット・新しい形状6件以上・役割・公平な対抗策・性格・育成外観。既存TRCX-**-001/002と一切衝突しない-003以降のID。

`src/Ext2Factory.luau` — Studio以外は拒否。各モデルをanchored, 非衝突・非クエリ・非タッチの Roblox Parts/WedgeParts でプレビュー生成。計20部品以内、距離LODの場合 signature上位3件のみ。4つの静止ポーズへの変更（フルアニメーションではない）。

`src/StudioGallery.client.luau` — StarterPlayerScripts配下に2 ModuleScriptと共に配置すると、Studio時だけ16件をViewportFrameで前後切替・ポーズ表示するローカルプレビュー。スマホ向け実戦HUDではない。

`data/collection_contract.json` — #275/ #280 アイテムサーバー権威への将来接続要件。sourceItemOnly=true、playerOwned=false、actualAbilityImplemented=false、freeHatchCandidate=true。#281レベルの装飾変化候補はマスタリーLv3/6/10でも性能差なし。

### 検証

`python3 -m unittest discover -s tests -v` を実行可能。これはソース静的検査でありLuauネイティブコンパイル、RojoでのPlace生成、Studio2client、Android FPS、人間FUNの合格とは異なる。

### 統合の提案

①実S1 #220の既存1魔獣無料孵化→所有→ロビー装備→次戦5sサーバー可視探知(#280)をAndroidで検証→②この16件から**魔獣1件のみ**見た目を置換するA/Bテスト→③ロングテール追加、という順序。新能力は#275権限サーバーの一箇所で検査。全16件同時投入はしない。卵取得・得点・HP・攻撃・他人の所持・課金確率は本パックで変えない。

禁止: main/RC/merge/公開/課金/PC Codex・P0ABC/CAS/既存Automationの更新。
