# P0D D18 Batch9 — 看板72体の追加正規6体（SOURCE ONLY）

- 既存60体の正規3D原作に対して、Atlasの未制作12体中6体を追加して制作ソース目標66/72。**Studio実機未検証、正式RCには新規0体。**
- 固定Atlas SHA256 cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01、既存Batch8 SHA 7bfb7bd5a4d4531ceaf2deaaf19f7591d3c218cd、所有Issue #265、別branchの独立ディレクトリのみ。
- BE081 草竜 / SP090 砂時計 / VE063 鍛造台 / WE108 王城ホルン / ZO027 見張り兵 / TR108 門玉。各モデル独自Partと3つの遠景シルエットタグ、近景/遠景切替、idle/tap/win/lossの4状態。
- `Factory.Build` はViewportFrame配下のWorldModel専用（Part anchored/no collision/no query/no touch）、最大12モデル。全Sourceは無料・鍵なし、Preview無効。原作モデルデータを実ゲームへ勝手に生成しない。
- 企画室のゲーム内能力は design/CHARACTER_CARDS.md にのみ記載。実職業はRAIDER/GUARDIAN 2つのまま。絵だけで完成としない。
- CI/試験はSourceの重複・公式ID/名前/世界・3秒シルエットタグ・予算・危険な権限・未許可の自動実行を拒否する。実際のStudio・2Client・Android・楽しさはNOT_TESTED。
- main、保護された正式RC、H1 #220、既存Batch1-8、公開/課金/パスワード/Windows Codex/5 automationsには変更なし。
