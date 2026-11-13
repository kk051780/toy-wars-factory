# P0D企画室｜市場調査から次の一件を選ぶ・2026年11月13日
market_card_id: P0D-STUDIO-MARKET-H1-90S-20261113 | game: TRAP_RAIDERS | adoption_id: P0D-FUN-H1-001 | 調査・商品判断のみ

## 市場の観測：他社の人気を成功保証と混同しない

- [Fanblox 2026-11-13 02:15 UTC時点](https://fanblox.co/radar?tab=top) の公開スナップショットで Steal An Egg 約482,120同時接続。別時刻の[Statroblox](https://statroblox.com/leaderboards/playing)は別の数値を掲載。収集/奪取に大きな需要があることは示唆されるが、ゲームを模倣すれば当社も伸びる、という因果や収益は不明。
- [Roblox公式Discovery](https://create.roblox.com/docs/discovery) は初回60秒未満・61～180秒離脱、PTR、遊ぶ日数/時間、友達との遊びを重要指標として説明。
- [Roblox公式Onboarding](https://create.roblox.com/docs/production/game-design/onboarding) は初見数分の体験の重要性を説明。
- [Roblox公式Engagement](https://create.roblox.com/docs/production/analytics/engagement) は長い説明より早く行動させる/友達との交流障壁を減らす方向を推奨。
- [Roblox公式Core Loops](https://create.roblox.com/docs/production/game-design/core-loops) は短期の操作→繰返し行動→進歩の動機を分けて設計する。

## TRAP RAIDERS の固有の勝ち筋仮説

「敵の宝を取って、空か海か地上を選んで帰還。仲間に助けてもらい、相手は罠で守る。逆転できるから再戦したくなる」

開始0～15秒（仮説）：赤青の城と卵を見て目的が分かる。
15～45秒（仮説）：RAIDER風走り / GUARDIAN罠と、地上/海/空のいずれかを選ぶ。
45～90秒（仮説）：相手の卵を奪うか、それを守る/妨害する。卵を持つと風走りは使えないため、追跡と護衛が生じる。
試合後（仮説）：自分の作戦が勝敗に関わり「もう一戦」と思える。

現行 H1 は2職のみ本当に実装、海・空の通路もソース生成済みだがStudio物理の実証なし。中立の動く幻獣は既存H1では視覚的存在であり、100種の仲間化AIや7職が実装済みではない。

## 調査→既存SOURCE→人間で一件選ぶ表

| 実際の観測がこうなら | 次に選ぶ一件のみ | 理由 |
|---|---|---|
| 2人のゲームや卵の持帰り自体が失敗 | #255/#220 本体修正 | 演出を足しても根本的に遊べない |
| SKY/SEA の卵運搬が物理的に失敗 | #255/#253 ルート実機修正 | #262の短縮候補は実機不通の原因を直さない |
| スマホのボタンが読めない | #260 児童用HUD | 既存ソースあり。新規UIを作り直さない |
| 卵/帰り道が不明または初動60秒超 | #219 D18追従コンパス | 既存の29 Luau候補あり |
| 物理的には通れるが海/空が遅すぎる | #262 短縮ルート | 理論往復寄り道+46/54%→約+15%。実機数値は未確認 |
| 卵の獲得が地味で手応え不足 | #266 初卵の短い祝福演出 | 既存30 Luau候補あり |
| 序盤の魅力は上がったが再戦しない | #267 星ジャンプなどS2研究 | S1公開を無限延期しない |
| 公開準備の承認が成立した場合のみ | #264 LIVE OFF安全ゲートの正式審査 | ビルド・安全の課題であり面白さ改善とは別 |

現時点、優先ソースは #259 H1 QA-only 30 Luau vs #245 H0 QA-only 23 Luau のA/B。OWNERのStudio二人＋スマホ試遊がまだ無いので候補追加せず実測待ち。#220のみ正式RC採用と完成率を更新する。

## 一件選択の判断支援ツール

- decide_next_ab.py：H0/H1の実機人間観察JSONを受け取り、上の表に従い次の改良を「一件だけ」選ぶ。どんな出力でもRCの書換え・公開・課金・ Studio 操作の実行はできない。
- OWNER_STUDIO_H0_H1_BLANK_NOT_TESTED.json：未試遊状態が明記された入力原本。初期状態では必ずHOLD。
- tests/test_decider.py：実際の人間観察ではない意図的な模擬データに対する28件の異常入力/失敗/優先順位テスト。模擬データが良い結果でも自動公開許可は絶対に出ない。
- H0 SHA256=f0d45aae5469cdb862e3642b65fdc5c4c7da8ada924b3a0d48291cabca89344b (23 scripts)。H1 SHA256=f290c6fccfa8796220fa4f13000a53ed8f8ec7c7a269951280938aff3240ee7e (30 scripts)。どちらも既存QA-only試遊ビルド、正式公開用ではない。

## 必須の実機評価（今は全て NOT_TESTED）

1. H0/H1両方をRoblox Studioで開き、ServerとRED/BLUEの2clientを稼働、別々のOutputを保存。
2. H1で卵獲得→敵に追われる→自己陣地へ納品、Sky/Seaとも持ち運んで通行。
3. スマホ横画面ボタン、案内、城/敵/中立の見え方、エラー、開始から初アクションまで秒数を観測。
4. H0対H1の「最初90秒の楽しさ」を同じ人に0～5点評価、再戦したいかを聞く。点数は検証設計の尺度であり外部市場の標準値ではない。
5. 次のA/Bは、判定器が示す既存1件のみ。#220が採否、失敗したらH0か元のH1へ差戻し。

### 正式の区分
今回の IDEA_DESIGNED=0件追加 / GAME SOURCE_DELIVERED=0件 / RC_GAMEPLAY_INTEGRATED=0件 / STUDIO_HUMAN_ACCEPTED=0件。企画室の独立した市場・判定コード成果のみ。P0D初回リリース正式進捗は#220の最終値75%、WorldField #222は50%、変更なし。継続率・実同接・売上・課金率は UNKNOWN。児童の個人情報、動画のコピー、第三者IPの模倣、追加課金・main/RC書換えを行わない。
