# P0-D D18｜10体の詳細3D図鑑に「3幕のおはなし」を追加

- `game_id=TRAP_RAIDERS` / `work_id=p0d-siege-v19`
- `packet_id=P0D-D18-STORY-REACTIONS-TEN-20261112-07`
- 固定元：詳細3D図鑑 `f7d313c2d0fc85493048b86ba0f3d04b1e9a8eb9` / キャラv8 `176bfc400ef6ec561b129a8163a0f4776e1b9ee4`
- **鍵なしオリジナル PUBLIC_SOURCE_V1**。新しい三幕30件は独自に短文化した物語案で、v8のキャラID/設定を変更しない。

## 実装

前の20ファイル一式を保持し、`data/story_beats.json`、再現可能な `tools/generate_story.py`、生成済 `src/D18StoryBeats.luau`、更新した**完全な**`src/D18GalleryController.luau`と`default.project.json`、試験を追加。コードは独立Rojoプロジェクトとして組立可能な形。

10体の詳細3Dは**元ソースそのまま**。カードを選ぶと物語は第1幕へ。図鑑画面の「つぎへ」を押すと1→2→3→1と進み、詳細3D姿勢は待機→しょんぼり→勝利→待機。手動の姿勢4種（タップを含む）・45度回転・詳細/軽量LOD・6分類・お気に入りを維持。文字・姿勢はローカルのみで、進捗を保存・付与しない。勝てばレアがもらえる表示は一切ない。

子ども向けの狙い（**仮説**）：シルエットだけでなく「少し困って工夫して立ち直る」共感を作る。H0＝元の一文説明/手動ポーズ、H1＝10体の3幕＋ポーズ。人間の理解度や再訪意向は未測定。

## 境界

展示はデフォルト無効。非戦闘、非接触、WorldModelの単一ローカルモデル、元ファクトリーのDestroyを実行。サーバーRemote、DataStore、報酬、所持解放、有料ガチャ、時限圧力、音・点滅・パーティクル、アナリティクスは無し。mainや#220 S1 RC/Roblox公開は無変更。20+の元コードの動作互換はオフライン静的試験までで、**Luau本物のコンパイル、Roblox Studio、2client/スマホFPS、児童試遊は未試験**。

## ローカル検証

```bash
python3 tools/generate_story.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/verify_pack.py
```

統合班 #220 は任意採用/スキップ可。S1初回リリースの必須条件にしない。
