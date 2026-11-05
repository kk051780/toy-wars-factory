# Toy Wars Factory — 開発進捗ダッシュボード

観測日：2026-10-25 / 根拠main：`f728fa525d8b`

**進捗率は残り日数ではなく「完了条件を満たした工程の重み付き達成率」。** ドラフトPRや未検証の実機は完了扱いしない。初回の自動統合成功を反映したが、長期の無人安定稼働やRobloxエンジン検証は未達。

| 項目 | 基準達成率 | 完了工程 | 未完工程 | うち障害あり |
| --- | ---: | ---: | ---: | ---: |
| 自動開発体制 | **57%** | 8/15 | 7 | 4 |
| ゲーム開発（全体構想） | **38%** | 7/18 | 11 | 5 |

## 自動開発体制

| ID／合格する工程 | 配点 | 状態 | 根拠または次の証拠 |
| --- | ---: | --- | --- |
| A01 GitHubを正本とする構成・引き継ぎ | 8 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/1) |
| A02 オフラインの自動回帰テストと変更検査 | 7 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/32) |
| A03 定期的なゲーム修正ワーカーの実走 | 8 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/34) |
| A04 自動ワーカーのゲーム本体修正PRと正確なCI | 6 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/38) |
| A05 最大3件のPRキューの継続処理 | 6 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/37) |
| A06 手動GO・自動実行の共有排他ロック | 8 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/41) |
| A07 実装と分離した審査タスク・統合判定ルールの導入 | 6 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/43) |
| A08 独立審査による実ゲームPRの無人main統合 | 8 | 達成 | [別タスクがPR #45を統合](https://github.com/kk051780/toy-wars-factory/pull/45)・[統合後QA成功](https://github.com/kk051780/toy-wars-factory/actions/runs/40157791404) |
| A09 無人統合後mainのQAによる後続工程制御 | 6 | 未達 | QA成功・失敗の後続停止/再開を実証 |
| A10 日次METAによる根拠付きの体制改善PR | 7 | 障害あり | no_updateの原因調査と初回PRの成功 |
| A11 故障したmain/CIの自動修復・再検査 | 6 | 未達 | 実際の失敗から修復完了までを検証 |
| A12 no_update・停滞・CI遅延の自動検知/報告 | 5 | 障害あり | Issue #4の再発防止 |
| A13 連続サイクルでの無人安定稼働 | 5 | 未達 | 3サイクル以上の作者/審査/改善結果 |
| A14 非公開Roblox Cloud Engine実機CI接続 | 8 | 障害あり | Issue #3の実機起動証拠 |
| A15 複数人・スマホの自動実機検証 | 6 | 障害あり | Studioホストを使った2接続・画面の証拠 |

## ゲーム開発（全体構想）

| ID／合格する工程 | 配点 | 状態 | 根拠または次の証拠 |
| --- | ---: | --- | --- |
| G01 製品構想と3種の玩具キャラクター定義 | 5 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/1) |
| G02 Lua正本ソースとStudioインストーラの一致検査 | 5 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/32) |
| G03 購入・設備強化・経済計算のオフライン検証 | 8 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/40) |
| G04 PvEウェーブ・生産・敗北処理のオフライン基礎実装 | 7 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/35) |
| G05 HUD価格と正本購入価格の連動 | 4 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/32) |
| G06 工場区画・選択・入退出のサーバー権限判定 | 5 | 達成 | [根拠](https://github.com/kk051780/toy-wars-factory/pull/30) |
| G07 Heartbeat遅延・生産周期の修正をmain統合 | 4 | 達成 | [修正をmainへ統合済み](https://github.com/kk051780/toy-wars-factory/pull/45)・[統合後QA成功](https://github.com/kk051780/toy-wars-factory/actions/runs/40157791404) |
| G08 本物のRobloxエンジンで起動試験 | 8 | 障害あり | Issue #3の非公開実機テスト |
| G09 実機でPvE一周を完走 | 10 | 障害あり | 入場→生産→戦闘→強化→再挑戦の実機ログ |
| G10 2クライアントの独立性・同期・権限検証 | 7 | 障害あり | Studio複数人テスト |
| G11 スマホHUD・操作・フレーム時間の実測 | 7 | 障害あり | 端末テストと実機計測 |
| G12 3キャラのモデルと演出を画面で識別 | 6 | 未達 | キャラ実機スクリーンショット |
| G13 進行・保存・復帰の要件実装 | 5 | 未達 | 復帰/損失耐性テスト |
| G14 導線・初回チュートリアル・UI | 4 | 未達 | 初見の操作テスト |
| G15 プレイヤー実測による楽しさ/難易度調整 | 7 | 未達 | 実プレイログと改善 |
| G16 協力プレイの実装検証 | 3 | 未達 | PvE後の独立検証 |
| G17 PvP・設計図争奪 | 3 | 未達 | ルール/実装/実戦検証 |
| G18 リリース品質判定・公開準備 | 2 | 障害あり | 客観ゲートを満たすまでHOLD |

## 更新規則

- 検査合格済みのmain・実走記録・実機ログなど、証拠を再確認した工程だけを `verified` に変更する。
- 数字が下がっても正直に記録する。配点・工程変更は理由・差分をPRで審査し、以前の値も履歴に保持する。
- `config/progress_milestones.json` を正本とする。`python3 tools/progress_report.py --check` で表示との一致を検査する。
- これは初期スナップショット。定期実行から証拠を自動収集し、独立審査のうえ更新する連携は**今後の実装課題**であり、現時点でリアルタイム更新済みとは言わない。

## 直近の重要ゲート

- 自動体制：独立審査でPR #44/#45をmainへ無人統合した実証が必要。
- ゲーム：Roblox実機でPvE一周、2人、スマホを通すまで公開不可。
- `no_update` やGemini推論事故を承認で素通りしない。新規課金/プロバイダ推論、Roblox公開は別ゲート。
