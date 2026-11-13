# P0D：クリスタル峡谷＋7職業PvE＋卵リレー60本 統合受渡し

**2026年11月14日｜PRIVATE SOURCE CANDIDATE／正式RCに未導入／Roblox未公開**

## 完了したゲームコード検査

本物の正規RC57を組み立て、WCS峡谷1本追加で58、7職PvE実装（元Game/HUD 2本改修＋純Module1本）で59、その**同じGame/HUD**へ卵リレー元作者9 Game/6 HUD差分＋純Policy1本を適用し60本にした。別Game・別Remote・別Store・追加課金は作っていない。

GitHub Actions [43522746378](https://github.com/kk051780/toy-wars-factory/actions/runs/43522746378) **COMPLETED SUCCESS**、真に検査したソースHEADは `445ff4c057eb5c05f72c59f1ab670ed8cd68965e`。検収ログでは **Luau60/60コンパイル、純EggRelayPolicy 41/41、実際に組み合わされたGameの卵受渡し関数30/30、Rojo v7.7.1実Placeの60/60埋込みLuau完全一致**。非公開成果物[14082764683](https://github.com/kk051780/toy-wars-factory/actions/runs/43522746378/artifacts/14082764683)。**成果物名に「CANONICAL」と含まれるが、ブランチは正式RCではないので採用を意味しない。**

今回追加した `rc_fastlane/apply_relay_classic_private60.py` は59本時点の両ソースロックファイルを再検証し、元作者PR #296の9+6パッチアンカーが各1回だけ存在するときのみ適用。1卵Classicモードの受渡しに限定し、H2の5卵モードの受渡しは未実装として拒否。OFFなら元59本へ完全に戻る。元57本を上書きしていない。

## 次の唯一の正式RC統合担当 #220 への手順

1. 正規 `rc/p0d-s1-kids-rc01` の**現在のHEAD/CAS権限**を再確認する。旧Placeを丸ごとコピーしない。
2. 峡谷WCS（親候補 [#300](https://github.com/kk051780/toy-wars-factory/pull/300)）、7職PvE（親候補 [#303](https://github.com/kk051780/toy-wars-factory/pull/303)／作者[#297](https://github.com/kk051780/toy-wars-factory/pull/297)）、Classicリレー（作者[#296](https://github.com/kk051780/toy-wars-factory/pull/296)）を**同じRC Game/HUD**に順次ソース配線する。それぞれ独立OFF/復旧を確保して、正式新HEADで60/60 native+Rojoと41+30実行検査を再度通す。
3. 成功時だけ台帳のSOURCE→RC昇格・企画室のRC導入率を増やす。未登録の企画は既存IDを流用せず新規一意IDにする。これは隔離ブランチなので**Draft PR [#309](https://github.com/kk051780/toy-wars-factory/pull/309)の一括マージをしない**。
4. Studio実機2client、Android、元保存キーのDEV再入場、OWNER FUN評価は別途要確認。現在の自動テストは本物のStudioエンジン/通信を動かした証拠ではない。

## 進捗率の扱い

最後に照合した正式台帳は **21/58案RC導入=36.2%、48/58案SOURCE以上=82.8%、IDEA10件**。隔離60本の成功によって**正式RCが60本になったわけではなく、完成度も自動で上がらない**。前回リリース審査75/100・FUN_NO_GOは変更なし。

安全境界：正規RC・main無断変更、公開、課金・追加費用、自動化変更なし。
