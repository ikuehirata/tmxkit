# tmxkit

tmxkit は、**巨大な TMX（Translation Memory eXchange）ファイルを
実務で安全に扱うための Python ライブラリ**。

TMX を「XML ドキュメント」としてではなく、  
**`<tu>`（Translation Unit）のストリーム**として扱うことを前提に設計している。

翻訳・校正 といった処理は一切行わない。  
tmxkit は **翻訳データ操作の基盤レイヤー**である。

## 目的

- TMX を **全体展開せずに逐次処理する**
- `<tu>` を最小単位として安全に分解・再構成する
- 人間や別ツールを挟んでも **再結合可能性を失わない**
- CLI やアプリに依存しない **純ライブラリ**として提供する

このライブラリは「翻訳をする」ものではない。  
**TMX を壊さずに触るための下層部品**。

## 対応フォーマット

- 対応：**TMX（主に 1.4 系を想定）**
- 非対応：
  - CAT ツール固有の挙動再現
  - TMX 仕様全体の完全実装
  - 編集 UI / CLI

tmxkit は **仕様準拠よりも実務耐性**を優先する。

## 基本思想

- ライブラリは **状態を持たない**
- 設定・ログ・CLI は上位レイヤーの責務
- TMX を巨大な XML ツリーとして扱わない
- すべての処理は `<tu>` 単位で完結する

tmxkit は  
「静かで、速く、文句を言わない」  
基盤ライブラリであることを目指す。

## ディレクトリ構成

```text
tmxkit/
├─ io/        # TMX の読み書き・マージ（streaming）
├─ tu/        # <tu> / <prop> / <seg> 操作ユーティリティ
├─ pipeline/  # TU ストリームに処理を適用する薄い補助層
└─ errors.py
```

## 想定される使い方

tmxkit は
**「TU を受け取り、TU を返す関数」**
を中心とした処理モデルを想定している。

```python
from pathlib import Path
from tmxkit.io.reader import stream_tu, read_header_only
from tmxkit.io.writer import write_tu_stream
from tmxkit.pipeline.apply import apply
from tmxkit.tu.props import replace_prop_value

def process_tu(tu: etree.Element) -> etree.Element:
  return replace_prop_value(tu, 'domain', 'ingame')

# 単一ファイルから TU をストリームして処理する例
tu_stream = stream_tu(input_path)
tu_stream = apply(tu_stream, process_tu)

write_tu_stream(
  tu_stream=tu_stream,
  header_path=Path(input_path),
  out_path=Path(output_path),
)
```

tmxkit は処理内容を決めない。
**何をするかは呼び出し側が定義する。**

※ 上記は思想説明用の最小例であり、
　完全な実行例であることを目的としていない。

## やらないこと

* 翻訳・校正処理
* 設定ファイル管理
* CLI 提供
* TMX 編集ツール化

それらはすべて **上位プロジェクトの責務**。

## 想定される利用元

* 翻訳メモリ前処理スクリプト
* TMX を別形式に変換する自前ツール

どこから呼ばれても
「TMX を安全に流すだけ」
という立場を崩さない。

## 注意

このライブラリは **実務前提で設計**されている。

汎用性や親切さよりも、

* 壊れない
* 予測可能
* 再結合できる

ことを優先する。

## examples 内の原文ファイル取得元

本リポジトリの `examples/` ディレクトリに含まれる原文テキストは、以下の**著作権フリー（Public Domain）資料**を元にしています。
いずれも、tmxkit の機能例・動作確認を目的としたサンプルデータとして使用しています。

### シャーロック・ホームズ（ボヘミアの醜聞）

* **英語原文**  
  Project Gutenberg  
  *The Adventures of Sherlock Holmes*  
  “A Scandal in Bohemia”  
  [https://www.gutenberg.org/files/1661/1661-h/1661-h.htm#chap01](https://www.gutenberg.org/files/1661/1661-h/1661-h.htm#chap01)

* **日本語訳**  
  青空文庫  
  「ボヘミアの醜聞」  
  [https://www.aozora.gr.jp/cards/000009/files/226_31222.html](https://www.aozora.gr.jp/cards/000009/files/226_31222.html)

### 枕草子

* **英語訳**  
  *The Pillow-Book of Sei Shōnagon*  
  translated by Arthur Waley (1928)  
  Internet Archive  
  [https://archive.org/stream/the-pillow-book/The%20Pillow%20Book_djvu.txt](https://archive.org/stream/the-pillow-book/The%20Pillow%20Book_djvu.txt)

* **日本語原文**  
  日本語版ウィキソース  
  『枕草子』第一段  
  [https://ja.wikisource.org/wiki/%E6%9E%95%E8%8D%89%E5%AD%90_(Wikisource)/%E7%AC%AC%E4%B8%80%E6%AE%B5](https://ja.wikisource.org/wiki/%E6%9E%95%E8%8D%89%E5%AD%90_%28Wikisource%29/%E7%AC%AC%E4%B8%80%E6%AE%B5)

※ 原文および翻訳はいずれも著作権保護期間が終了している資料です。
※ 本リポジトリでは、翻訳の正確性や逐語対応を保証するものではありません。

## License

MIT License
