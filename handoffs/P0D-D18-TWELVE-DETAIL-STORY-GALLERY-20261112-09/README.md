# P0-D 企画室 | D18 12体の詳細3D図鑑＋36場面の物語（ソース試作）

- ゲーム: TRAP_RAIDERS (`p0d-siege-v19`)
- `packet_id=P0D-D18-TWELVE-DETAIL-STORY-GALLERY-20261112-09`
- **PUBLIC_SOURCE_V1 / 鍵なし・平文 / 初回S1リリースは変更しない**

## 今回の追加

既存詳細3D＋物語ギャラリー10体（固定 SHA `05c85fb3ecb29b8156caaff49ab123b4cbf11fbc`）に、v8図鑑の最後の2体 `TRCA-TR-063 火輪跳ね台`（罠、21 Parts）と `TRCA-WE-099 遊園ホルン`（武器、27 Parts）の**元のオリジナル低ポリモデルソース**（SHA `98811a9af95e170d359a35647b4c1f22060e49ce`）をバイト不変で追加。

- 全12体から選択し、詳細3Dを1体のみ生成・45度回転・4種ポーズ・LOD切替。`Factory.Destroy` で切替時に後始末。
- `data/story_beats.json` は12体×3幕=**36場面**、姿勢 `idle → loss → win` と連動。次の物語は3→1に循環。
- 6分類、お気に入り（画面中のみ、非保存）、日本語の物語。新2体も同じ UI から選べる。
- `data/gallery.json` は12体の日本語表示メタ情報。元の10体のデータは内容ハッシュで不変を確認、新2体は詳細3D Factory を参照（空の軽量サムネ定義で水増ししない）。
- `src/D18DetailModels/FinalV8/` は元モデルの**バイト不変コピー**。5旧フォルダも不変。
- `default.project.json` はローカル専用Rojoデモ。`DisabledGalleryDemo.client.luau` は初期値 **ENABLED=false**。

## 検証・運用境界

```bash
python tools/generate_catalog.py --check
python tools/generate_story.py --check
python -m unittest discover -s tests -p 'test_*.py' -v
python tools/verify_pack.py
```

本パックは **Luauソース + Python構造/改変負例テスト**。Roblox Studio 実機での描画、ネイティブLuau構文確認、モバイル性能、2人同時接続、子どもによるUI評価は**未実施**。キャラ所有権・解放・報酬・課金・戦闘・サーバーRemoteを扱わない。初回S1リリースには採用必須としない。#220唯一の統合担当だけが任意採否を判断する。

## 成果数の区別

D18 3D試作の種類は **12/72=16.67%（今回増えていない）**。新規に実装されたのは既存モデルを表示する**12体対応図鑑のソース**。648体の個別改稿は78/648。S1全体の公式受入率は #220 の独立監査値であり、当パック受入率と無関係。
