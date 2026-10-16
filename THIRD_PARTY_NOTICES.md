# 第三者コンポーネントについて（ソース配布版）

ソースZIPには、Python実行環境や第三者ライブラリのバイナリを同梱していません。セットアップ時に必要なパッケージを導入します。

| コンポーネント | 主な用途 | 公式情報 |
| --- | --- | --- |
| Python | 実行環境 | https://www.python.org/ |
| Pillow | 画像処理・クリップボード | https://pillow.readthedocs.io/ |
| OpenCV / opencv-python | 画像認識・MP4処理 | https://github.com/opencv/opencv-python |
| pywebview | YouTubeプレイヤー用WebView | https://pywebview.flowrl.com/ |
| pythonnet | Windows/.NETとの連携 | https://pythonnet.github.io/ |
| Microsoft Edge WebView2 | YouTube画面表示 | https://developer.microsoft.com/microsoft-edge/webview2/ |

ソースZIPの `requirements-windows.txt` は、利用環境の再現性を高めるため主要なPythonパッケージのバージョンを指定しています。各パッケージとその依存関係には、それぞれ固有のライセンスがあります。

**FFmpegについて**：`opencv-python` のWindows wheelにはFFmpegのバイナリが含まれることがあります。ただし、この配布元から配布するソースZIP自体にはそのwheelやDLLを含めません。**第三者が本ソースをEXE化して配布する場合は**、同梱するライブラリに応じてLGPL等の再配布条件を別途満たす必要があります。参考：[opencv-python 第三者ライセンス](https://github.com/opencv/opencv-python/blob/4.x/LICENSE-3RD-PARTY.txt)。

独自制作のコード・画像は[MITライセンス](LICENSE)で公開しています。第三者のライブラリには、それぞれのライセンスが適用されます。
