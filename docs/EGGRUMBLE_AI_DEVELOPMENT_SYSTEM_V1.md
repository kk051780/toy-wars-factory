# EGGRUMBLE 開発の現行案内

- 最新の作業順・実機検証時期は [OWNER #1011](https://github.com/kk051780/toy-wars-factory/issues/1011) を使用する。再開時は正式RCのHEAD、[統合 #220](https://github.com/kk051780/toy-wars-factory/issues/220)、対象CLAIMと固定候補を確認する。
- 正式RCは `rc/p0d-s1-kids-rc01`。最新 #220 が選んだ試遊用Placeを使う。ACTIVE_RUNTIMEとPRIVATE_COMPANIONの成果は区別する。
- 実ソース → 必須QA → 独立レビュー → 認証済み唯一writerによる非force統合 → 公式同HEADの必須CIと実Place。真正な [CLAIM #218](https://github.com/kk051780/toy-wars-factory/issues/218)、SourceLock、即時OFFを保つ。
- Studioは一括試遊時に1検証ずつ実行する。保存、Stop、検証に属するStudio・クライアントを終了し、所有PIDの消失を確認する。PC、Android、ART、FUN、OWNER合否は実測で記録する。
- main昇格、Roblox公開、課金、追加支出、既存自動化の変更は別の正規承認に従う。

[旧規約の保存版 #1012](https://github.com/kk051780/toy-wars-factory/pull/1012)
