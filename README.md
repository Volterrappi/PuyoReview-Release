# PuyoAnalysis — Windows解析ツール

ぷよぷよeスポーツの盤面を手入力・画像・クリップボードから入力して、連鎖STATSやNEXT3組の3手全探索を確認できる非公式ツールです。盤面や解析結果の保存もできます。

## ダウンロード・起動
1. 64bit Windows 10/11とPython 3.12以上（Python Launcherを含む）を準備します。
2. [ダウンロードページ](https://github.com/Volterrappi/PuyoReview-Release/releases/latest)からZIPをダウンロードして展開します。
3. `SETUP_FIRST.bat` を起動します（初回のみ・ネット接続が必要です）。
4. `START_Analysis.bat` を起動します。

Python 3.13で実機動作確認、Python 3.12で自動テスト済みです。環境によって動作しない場合があります。

## 使い方
1. 盤面を入力します。3手探索ではNEXT3組も指定します。
2. 連鎖STATS、または3手全探索を実行します。
3. 残したい盤面・結果を保存します。

保存した記録から、画像・探索結果のCSV・保存フォルダを開けます。

詳しい操作や注意点は[利用ガイド](GUIDE.md)をご覧ください。

## 不具合・要望
[Issues](https://github.com/Volterrappi/PuyoReview-Release/issues) または [X @istnpypy](https://x.com/istnpypy)へ。

## ライセンス
独自制作のコード・画像は[MITライセンス](LICENSE)で公開しています。使用ライブラリについては[第三者コンポーネント](THIRD_PARTY_NOTICES.md)をご覧ください。

本ツールは非公式のファン制作ソフトです。ゲームの名称・商標等の権利は各権利者に帰属します。
