# P0D-FUN-H1-001 | 一体型実ゲーム 25-Luau H1検証候補

**状態: PRIVATE_STUDIO_SOURCE / 実機・スマホ・子ども試遊 NOT_TESTED / 公式RCには未採用**

このプロジェクトは、企画室から個別に開発した2つの試作要素を**実際の一つの TRAP RAIDERS ゲームソース**で組み合わせたもの。Rojoを使う時はこのディレクトリの `default.project.json` をビルドすること。既存Windows Place/v43Aと`rc/p0d-s1-kids-rc01`は上書き禁止。

- H0: 8-safe全体ソース固定 3120b9d3c0a5ec58c9f2613c5d186f3493b54f83
- H1フィールド+動く幻獣: #248 SHA c73f305fb412927aee05b399a4f54a2a16d0579f（既存21 Luau、元#232の2モジュール、H1FunWorld.server）
- RAIDER風走りとGUARDIAN既存罠の対抗: #251 SHA f6c98bc90cd14221d7a0c5940c9641c9fb14d8d8（そのまま Game.server, HUD.client, 新 WindRules を採用）
- 正確に25本のLuau: Server Script 2 / LocalScript 3 / ModuleScript 20。1つの元Game.serverが卵/得点/勝敗/罠/攻撃を管理し、同じRemoteで風走りを受付。H1FunWorldは地形/装飾と非戦闘幻獣のみ管理。

## 組み込んだ「遊び」の実体
空中の坂→高架回廊→敵側の坂と、海側の長い橋を、全職（**現実装はRAIDER/GUARDIANの2職のみ**）で通れる設計。元の中央通路も残す。敵の卵と自陣の納品台は元の位置を使用。
RAIDERはRキー/スマホUIから、18秒クールダウン・2.5秒間の短い風走り（速度27）で回り込み、GUARDIANは元の地上設置罠で迎撃する。持卵・罠スロー中・場外・死亡時に風走りを拒否するのは#251元のGameによるサーバー判定。星くじら/ペガサスは動くオリジナル3Dモデルだが非戦闘/無報酬で、発見は一時Player属性のみ。D18図鑑や7職・魔法・乗物はまだない。

## SOURCE / QA 状況の解釈
- LuauコンパイルとRojoソース一致を同一コミットで確認する。ゲームの動的なエンジンプレイや人間による見た目、物理ルート、スマホ画面は実施していない。
- 既存#248単体Rojo CI PASSと#251単体CIは、合体版のCI PASSを意味しない。
- Owner評価で「まだ陳腐」であれば本H1を採用しない。H0は完全に残す。
- 公式RCを編集できるのは唯一の#220統合担当。候補は#250採用カードで追跡し、H0/H1 OWNER実機比較と独立QA後に検討する。

## 次のStudioで試す受入（未実測）
1. 同じ新規未公開Placeから2clients開始しRAIDERとGUARDIANが赤青各1人になる。
2. 両チームで、中央・海・天空の各通路から相手の卵へ往復し、既存納品台に持ち帰る。落下・罠・走行中の卵ドロップ/高速化解除を確認。
3. R/スマホでRAIDER風走りの成功/18秒再使用/運搬時の拒否。GUARDIANの罠が正しく対抗し、出場者両方に効果が視認できる。
4. 動く星くじら・ペガサスと発見Prompt、卵2個で勝敗、ラウンド再戦、Studio正常終了。
5. 物理スマホ/Device SimulatorのUI重なりとFPS。H0より面白いか OWNER本人が判定。

No main/official RC/merge/Roblox production publication/paid features/costs/Codex/P0ABC/CAS/automations changes.
