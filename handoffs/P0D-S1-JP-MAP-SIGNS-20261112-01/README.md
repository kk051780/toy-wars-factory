# P0-D S1 — 子ども向けフィールド案内の日本語化

**公開ソース、鍵なし。** パケット `P0D-S1-JP-MAP-SIGNS-20261112-01`。

元ソースは正式RC `5dc6c958ea5549b1e859d6d250e6179e731181fb` の `src/server/MapBuilder.luau`（元Git Blob `d2127b8c20c8abd880a21f84aeeb706feeb14ce8`）。変更版の唯一のゲームファイルは `candidate/src/server/MapBuilder.luau` です。

## 遊ぶ子どもに伝わること

| 元の英語 | 新しい日本語 |
|---|---|
| Steal egg | 卵を取る |
| RED treasure / BLUE treasure | 赤チームの卵 / 青チームの卵 |
| RED EGG / BLUE EGG | 赤チームの卵 / 青チームの卵 |
| Deliver egg | 卵を届ける |
| RED scoring pad / BLUE scoring pad | 赤の納品台 / 青の納品台 |
| DELIVER HERE | 卵はここへ！ |
| RED CASTLE HP / BLUE CASTLE HP | 赤チームの城 / 青チームの城 |
| RED SPAWN / BLUE SPAWN | 赤チームのスタート / 青チームのスタート |

操作の目的が見れば分かるように、プロンプトと3Dの看板だけを日本語化しました。チームカラー、位置、接触判定、プロンプトの起動距離・ホールド時間、ステージの構造、スコア・勝敗・攻撃・罠・ボス・RemoteEventなど**ゲームの挙動はすべて従来どおり**です。物体内部の識別名（`RED_EGG`、`_CASTLE`など）は維持して他スクリプトとの整合性を守ります。

## 検証

`tools/test_jp_map.py` は以下を自動検証します。

1. 正式RCのMapBuilderとConfigをGit Blobで固定し、独立した先行MapBuilder実行テスト（固定コミット `c71d209c56ff3bb33ed0eb2628886b69c2541e81`、原型ソースSHA固定）を読み込みます。
2. 元MapBuilderへの**8件の表示文言差し替えだけ**であることをファイル丸ごと完全照合します。位置・衝突・権限など、1文字でも追加改変があれば失敗します。
3. 固定の公式Luau実行系で、変更版MapBuilder全体と元のConfigを実行。元の物理配置・27パーツ・4プロンプト等のテストを維持し、20件の日本語案内の追加判定を行います。
4. 英語への逆戻り、色の誤案内、看板の誤表示、卵位置改変、ロビーでのプロンプト誤有効化、勝手な衝突設定変更の8種類を意図的に挿入して全件拒否を確認します。
5. `BUILD_MANIFEST.json` の3成果物のSHA-256/バイト長も完全照合します。

GitHub Actionsの実行CIを正本の検証証拠とします。Luau上のテストにはRoblox `Instance` や `Vector3` の**テスト用ダブル**を使用しており、Roblox Studioの実画面やスマホの見やすさを証明しません。

## 統合の境界

正式RCの唯一の書込者は Issue #220 の `P0D-CHAT-INTEGRATOR-S1-RC01-B` です。現在、罠のサーバー実装が別案件で進行中であるため、**RCに勝手に直接書き込まず**、統合担当が最新RCで改めて差分を確認して採否を決めます。統合する場合は最新MapBuilderに対して8箇所だけを採用し、更新されたゲーム全体のCI・実機QAを再度通してください。

公開・マージ・課金・Windows Studio起動・既存PC Place変更はしていません。実際の子どもが日本語を読み取りやすいかはOWNERの最終試遊が必要です。
