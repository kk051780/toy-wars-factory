# P0D FAST-RC — 1本のRCを成長させる（OWNER 2026-11-14）
**正本はこの branch の `rc_fastlane/ACTIVE.json` と `rc_fastlane` 用GitHub Actions。** 前の21本S1は immutable commit `1263a03701211a652b99b91d2339575dc8104eff` に保存し、`releases/P0D_S1_KIDS_RC01/`の原本は上書きしない。

## 方針
- 「企画 → 企画室プレビュー → 人間の試遊 → 再採用会議 → RC組み直し」を**廃止**。採用済・依存を満たすソースは#220唯一のRC writerがこの本線のビルドprofileへ即時採用。GitHub Actionsが同じ源からStudio用`.rbxlx`を出す。OWNERの試遊は**後でまとめて**よい。
- 人間の楽しい/面白いゲート、Studio 2client・Androidは**RCの積み増しの必要条件にしない**。公開前のゲートとしてだけ残す。ゲームのバグは報告後OFF/切戻し→改善。
- 停止条件は本物の危険だけ：Game/Remote/HP/score/XP/Storeの二重権威、アンチ複製違反、保存データ消失、他人のコード変更、ビルド不一致、main/公開/課金の無断実行。
- #250は個々の機能の**追跡台帳**であり、同じ機能を再実装する第二工場ではない。#219企画室が各機能のownerと修復を追い、#220だけがRCを更新。重複レビューチケットで開発を停滞させない。

## 2026-11-14 最初の直結
`rich51` を現行RC主開発profileに選択（最新の51本ソース・自動ビルドの対象）。厳密固定SHA `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e`。
- 51本は既存47本のGame/Storeを**バイト同一**に保ち、セッション限定6技能修行台4ファイルを追加。前回元branch CI成功の証拠： https://github.com/kk051780/toy-wars-factory/actions/runs/43479603989
- **本RCで初回ビルドが実際にPASS済み**：RC SHA `5a0864fe9d3980dd6e0fdd9aa44f4d0169009166`、Actions [43483022604](https://github.com/kk051780/toy-wars-factory/actions/runs/43483022604)、51/51 RojoバイナリSourceExact、Game 1本。以後のHEADは毎回独立ビルドで再判定。Studio実プレイ・Android・人間FUNは依然NOT_TESTED。元候補の未確認事項を持ち越す。
- **6技能の永続保存/日次30分枠/追加4技能の実戦能力は未完成**。元H1 2技能LvとV4セッションLvはまだ別体系。保存統合は元Store担当が互換性・移行を処理するまで禁止。

## 追加済みの可逆修正：V4_IDLE_FRIEND_SAFE_FIX（Studio専用）

正式RC `rich51` の51本のうち、6技能道場の**既存2本だけ**を固定原作者版に差し替えます。元の49本（唯一のGame・Store・Remote権限を含む）は1バイトも変更しません。

- サーバー：フレンド確認を非推奨の `IsFriendsWith` から `IsFriendsWithAsync` に移し、元の `task.spawn+pcall` と同サーバー確認を維持。無料XPボーナスのルールや倍率は変更しません。
- クライアント：実際の人間操作がなくなったとき、Robloxの無操作切断が近いことを知らせる警告。**自動操作・擬似入力・AFK回避は一切しません**。保存されていない6技能XPや日次30分の継続利用を保証するものではありません。
- 作者の元ソース固定：`b7de8f8b7b4cccfb49d2d81c1ee4438d13a4b286`、GitBlob `dbb7171add2b29e337171e547bc40101c2b0dce4` / `7ad4ce4fa9d545cb33836c06dc56c0a03e384666`。既存RC源 `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e` の51本を先に完全再構築した後、RC HEAD内の `rc_fastlane/apply_overlays.py` が強制ソースSHA照合して差し替え。差し替え後も51本をRojoとGit blobで完全照合します。
- **個別OFF**：`rc_fastlane/ACTIVE.json` の `feature_switches.V4_IDLE_FRIEND_SAFE_FIX.enabled` を `false` に変更し、同じRC CIを再実行。ソース差し替えを行わず以前の51本のバイトへ完全復帰します。既存6技能そのものを外したければ `rich47` profile。メインGameや他H1機能の独立OFFスイッチはまだ未実装。
- 公式RCのCI成功は**Studio実機2クライアント・Android・面白さの検証を意味しません**。公開前のゲートとして維持。

## 切り離し方法（現時点）
1. `ACTIVE.json`のprofileを`rich47`へ変更すると、**V4セッション修行追加4本を外す**（元47本をそのまま使う）。
2. `legacy21`なら**旧S1に戻す**。前の正式RC `1263a03701211a652b99b91d2339575dc8104eff` は永久に復元可能。
3. H1の無双/天空/卵1/5等の**単体機能ON/OFFはまだ未実装**。次のRC改修はGameを単一権威のまま、サーバー正本のfeature IDで切替できるようにする。現段階で「全部個別に切り離せる」とは言わない。

## ビルド
`.github/workflows/p0d-rc-fastlane.yml` をRC branchへpushすると active profile `rich51` が自動ビルドされ、`P0D-CANONICAL-RC-STUDIO` artifactに`.rbxlx`と検査receiptが出る。source SHA一致→元作者のassemble→Rojo 7.7.1 checksumピン→51/51 XMLソース一致/一意のGame確認という **1回だけの検査**。
`workflow_dispatch` で `rich47` / `legacy21` を個別ビルドもできる（RC本線profileは変えない）。本workflowはRead-only、main変更/merge/Publish/課金/PC操作を行わない。

新機能の実装／ロールバック粒度は [`FEATURE_REGISTRY.json`](FEATURE_REGISTRY.json) に記録し、個別スイッチ未実装を隠さない。

## 次の統合優先
1. ACTIVE `rich51`新RCのビルド成否確認と修正（同一source SHAの再生成だけ）。
2. 6技能の本物のレベル/保存統合・1つのゲーム権威の内部feature flags化（保存データ破損の検証必須）。
3. 卵リレー/進化実戦/7職/巨大ボスなど既存ソースの**小さな実機能**を、#220が同一RCへ追加。先に人間試遊は要求しない。
4. 一括Studio試遊→改善→公開可否はOWNER別承認。

**公式S1進捗75/100は最終監査値。新しいprofileの選択だけで数値を増やさない。**

## RC追加機能：REALM_HUNT_V1（天空・海・炎・星）
4個の秘密の印を実際のマップに配置。生きたプレイヤーが近付いて発見プロンプトを押すと、サーバーのセッション用探索数が1/4ずつ増え、4/4で22秒の金色の演出が発動。Studio内のカウンターはサーバー属性で更新。卵/スコア/HP/戦闘/永続保存/課金は触らない。独立2スクリプト、元の51スクリプトは変更なし。機能スイッチは `rc_fastlane/FEATURE_SWITCHES.json` で無効化可能。実Roblox Studioは未試験。

### 2026-11-14 実証済みRC：修行改善+4秘境探索
1つのRCで51本作者ソースを起点に、V4修行の2本をソース固定で差し替え（残り49本は不変）、REALM_HUNT_V1の2本を追加。最終計53本。GitHub Actions [43488586444](https://github.com/kk051780/toy-wars-factory/actions/runs/43488586444) でLuauネイティブ新規2本、検査、53ソース完全照合、Rojoによる未公開Studio用Placeの生成すべてSUCCESS。実機/FUNはNOT_TESTED。秘境機能OFFは `rc_fastlane/FEATURE_SWITCHES.json`、修行改善OFFは `ACTIVE.json.feature_switches` で独立に切戻し可能。企画台帳のP0D-055はRCに昇格し、17/55件に増加。
