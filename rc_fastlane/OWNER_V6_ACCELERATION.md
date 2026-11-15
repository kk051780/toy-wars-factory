# P0D 高速開発 V6 — 段階的品質保証でRC納品を高速化

正本: [#218 OWNER V6](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6890363903)。
企画 #219、正式RC #220、ゲーム品質 #470、アート品質 #420 へ即時展開。

## 大原則 — 最終品質基準は下げない

- **開発用 SOURCE_ADOPTED** は途中状態。正規のauthenticated writer + nonforce expected-head CAS、同HEAD native/Rojo/source-exact、安全QA、実Place/ZIPが必要。局所的なYELLOWを追跡しながら次の機能を積んでよい。
- **PRODUCT_ACCEPTED** は別物。卵争奪・帰還・得点、ソロAI、群戦、7職全固有能力、3ルートの旗艦マップ、#470競合評価80点以上、#420 PC/Android/子どもFUN、OWNER承認がそろうまでNO_GO。未測定をPASSにしない。
- YELLOWが残るRCは **非公開の開発用** とし公開/課金/最終合格に用いない。

## RED / YELLOW / GREEN

**RED HARD BLOCK:** safety/security、権威多重化、Remote/セーブ/卵・得点の不正、同HEAD CI/Native/Rojo/source lock失敗、重要なコアループ回帰、クラッシュ/フリーズ、未認証writer・CAS/CLAIM不成立、rollbackなし。**公式RC採用を停止**。

**YELLOW KNOWN DEBT:** 安全・主要ゲーム成立に影響しない小さなアニメ/表示/一部職固有能力の未完成。FB-ID / FEATURE_ID / owner / reproduction / impact / fix_trigger / rollback / flag_state を記録し、基本ゲームを損なわない状態で開発用SOURCE統合を続ける。新IDEA追加より既存YELLOW修復が優先。

**GREEN READY:** 必須安全/同HEAD source QAが成功し該当の既知不具合がない。最速で統合検討。

tools/p0d_v6_triage.py は**自己申告した欠陥台帳の検査**であり、認証・本物のCI・影響判断を自動証明しない。YELLOW_TRACK_AND_REVIEW や GREEN_REVIEW の戻り値で **RCの書込み権は絶対に発生しない**。真正根拠は#220既存チェックから取得し直す。

## 高速化手順

1. 新規企画数より SOURCE→RC の実実装を増やす。既存PR/原作者が所持するGame/HUD patch、7職、卵・無双・ソロAI・旗艦フィールドを第一優先。
2. 別ModuleScript/3Dの独立修正だけを並列化する。同じGame/HUD/Remote/Storeには既存原作者/同FEATURE経由でsource-selectiveに集約し、重複PRと古HEAD上書きを禁止。
3. 独立した複数READY候補は最新RC基準で依存/SourceLock/重複を再確認して、一度のfull CIで検証。**古いHEADの成功を新HEADに流用しない**。
4. 各機能単位は短いnative+差分+重大負例QA。全機能横断のPC/Android・実機2client・32旧新・FUNは旗艦RC節目に集約し、致命的P0だけ短時間smokeを早期反復する。
5. 公式ライター増員はbranch保護+真正actor+coord registry GRANT+非force CASを確認できた時だけ。未整備なら#220既存writerが正式RCへ積む。
6. 最短の報告：公式40桁HEAD、実Luau数、企画RC導入数/67、同HEAD Actions・ZIP/Place bytes、RED/YELLOW未解決、今回採用した**本物の**実ソースと各実機/OWNER品質の別状態。UNKNOWNを捏造しない。

## 安全境界

main直書き、無断merge/publish、追加課金、未認証RC writer、CAS回避、OWNER承認のないWindows操作は禁止。既存自動化の実行頻度は変更しない。
