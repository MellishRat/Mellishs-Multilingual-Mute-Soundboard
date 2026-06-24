# Mellish's Multilingual Mute Soundboard

A lightweight OSC phrase board for VRChat's chatbox.

This tool is designed for people who either cannot speak, do not want to speak, or need fast preset messages while in VRChat. It sends button-based phrases directly to the VRChat chatbox using OSC.

It was originally built to help communicate with Japanese VRChat users during hosted events, using English, Japanese, and Romaji on the same button/message.

## Features

- Sends preset phrases to the VRChat chatbox through OSC
- Current loaded board name shown at the top centre
- Full last-sent phrase shown underneath the current board name
- Tab buttons expand to fit longer JSON filenames
- 64-button soundboard grid
- Five loadable JSON phrase boards
- Tab names are automatically based on the JSON filename
- English and Japanese text on each button
- Full message can include English / Japanese / Romaji
- Custom message box
- Configurable cooldown
- Editable OSC IP and port
- Dark mode and softer grey light mode
- Separate visual JSON editor
- Clear text box button
- No external Python packages required to run from source
- Optional `build_exe.bat` included for creating Windows EXE files

## Use Case

The app is intended to sit on a second monitor, desktop overlay, or OVR-style wrist view while using VRChat.

Example button:

```txt
Follow me
ついて来て
```

Message sent to VRChat:

```txt
Follow me / ついて来てください / Tsuite kite kudasai
```

## Requirements

To run from source:

- Windows
- Python 3.10 or newer
- VRChat with OSC enabled

To build EXEs:

- Python 3.10 or newer
- `build_exe.bat` will install PyInstaller into a local `.venv`

## VRChat Setup

1. Open VRChat.
2. Open the Action Menu.
3. Go to Options.
4. Enable OSC.
5. Run `run_soundboard.bat`.
6. Press a phrase button.

Default OSC target:

```txt
127.0.0.1:9000
```

OSC endpoint used:

```txt
/chatbox/input
```

## Running the App

Run:

```txt
run_soundboard.bat
```

Or manually:

```txt
python Mellishs_Multilingual_Mute_Soundboard.py
```

## Editing Phrase Boards

Run:

```txt
run_phrase_editor.bat
```

Or manually:

```txt
python Phrase_Board_JSON_Editor.py
```

The editor lets you change:

- English button label
- Japanese button label
- Message sent to VRChat
- Whether a slot is the clear-text button

The OSC target and cooldown are edited in the main soundboard app.

## JSON Boards

The included boards are:

```txt
everyday_conversation.json
general_social.json
vrchat_technical.json
flirty_social.json
board_5.json
```

The main host board is:

```txt
host.json
```

If you load a file called:

```txt
japanese_helper.json
```

The tab will display:

```txt
japanese helper
```

## JSON Structure

Each phrase slot looks like this:

```json
{
  "button_en": "Hello",
  "button_ja": "こんにちは",
  "message": "Hello / こんにちは / Konnichiwa"
}
```

The clear button uses:

```json
{
  "button_en": "Clear",
  "button_ja": "消去",
  "message": "",
  "is_clear": true
}
```

## Building EXE Files

Run:

```txt
build_exe.bat
```

The build script will:

1. Create a local Python virtual environment.
2. Install PyInstaller.
3. Build the main soundboard EXE.
4. Build the JSON editor EXE.
5. Copy the JSON files into the `dist` folder.

Output folder:

```txt
dist
```

Expected output:

```txt
dist/Mellishs_Multilingual_Mute_Soundboard.exe
dist/Phrase_Board_JSON_Editor.exe
everyday_conversation.json
general_social.json
vrchat_technical.json
flirty_social.json
board_5.json
dist/board_settings.json
```

## Notes

Japanese text is sent as UTF-8 OSC strings.

This has been tested with VRChat's chatbox OSC input, but VRChat can change OSC behaviour over time. If something stops working, first check that OSC is still enabled in VRChat.

## Suggested GitHub Topics

```txt
vrchat
osc
chatbox
accessibility
python
tkinter
japanese
translation
soundboard
```

## License

MIT License.

====================================================================================================

# Mellish's Multilingual Mute Soundboard

VRChat のチャットボックス向けに開発された、軽量な OSC フレーズボードです。

音声での会話が難しい方、話したくない方、または定型文を素早く送信したい方のために設計されています。OSC を利用して、あらかじめ登録したフレーズを VRChat のチャットボックスへワンクリックで送信できます。

このツールは、イベント運営時に英語圏と日本語圏の VRChat ユーザー同士のコミュニケーションを支援する目的で開発されました。英語・日本語・ローマ字を同時に表示・送信できるため、言語交流や国際交流にも活用できます。

## 主な機能

* OSC を利用した VRChat チャットボックス送信
* 現在読み込まれているボード名を画面上部中央に表示
* 最後に送信したメッセージをボード名の下に表示
* JSON ファイル名に応じてタブサイズを自動調整
* 64 個のフレーズボタンを搭載
* 最大 5 つの JSON フレーズボードを切り替え可能
* JSON ファイル名をもとにタブ名を自動生成
* ボタンに英語と日本語を同時表示
* 英語・日本語・ローマ字を含む多言語メッセージに対応
* カスタムメッセージ送信機能
* クールダウン時間の設定
* OSC の IP アドレスおよびポート番号の変更
* ダークモード／ライトモード対応
* 専用のビジュアル JSON エディターを同梱
* チャットボックス消去ボタン
* ソースコード版は追加ライブラリ不要で動作
* Windows 用 EXE を作成するための `build_exe.bat` を同梱

## 想定用途

VRChat 利用中に、セカンドモニターやデスクトップオーバーレイ、OVR Toolkit などを利用して表示することを想定しています。

ボタン表示例：

```txt
Follow me
ついて来て
```

送信されるメッセージ例：

```txt
Follow me / ついて来てください / Tsuite kite kudasai
```

## 動作環境

ソースコード版を実行する場合：

* Windows
* Python 3.10 以上
* OSC を有効化した VRChat

EXE をビルドする場合：

* Windows
* Python 3.10 以上
* `build_exe.bat` がローカル仮想環境（.venv）と PyInstaller を自動構築

## VRChat 側の設定

1. VRChat を起動
2. Action Menu を開く
3. Options を選択
4. OSC を有効化
5. `run_soundboard.bat` を実行
6. フレーズボタンを押して送信

デフォルト OSC 送信先：

```txt
127.0.0.1:9000
```

使用する OSC エンドポイント：

```txt
/chatbox/input
```

## アプリの起動方法

バッチファイルを利用する場合：

```txt
run_soundboard.bat
```

Python から直接起動する場合：

```txt
python Mellishs_Multilingual_Mute_Soundboard.py
```

## フレーズボードの編集

バッチファイルを利用する場合：

```txt
run_phrase_editor.bat
```

Python から直接起動する場合：

```txt
python Phrase_Board_JSON_Editor.py
```

エディターでは以下を編集できます：

* 英語ボタン名
* 日本語ボタン名
* VRChat に送信するメッセージ
* チャット消去ボタンかどうか

OSC の送信先やクールダウン設定はメインアプリ側で変更します。

## 同梱フレーズボード

```txt
everyday_conversation.json
general_social.json
vrchat_technical.json
flirty_social.json
board_5.json
```

例として `japanese_helper.json` を読み込んだ場合：

```txt
japanese helper
```

というタブ名で表示されます。

## JSON フォーマット例

通常のフレーズ：

```json
{
  "button_en": "Hello",
  "button_ja": "こんにちは",
  "message": "Hello / こんにちは / Konnichiwa"
}
```

チャット消去ボタン：

```json
{
  "button_en": "Clear",
  "button_ja": "消去",
  "message": "",
  "is_clear": true
}
```

## EXE の作成

以下を実行してください：

```txt
build_exe.bat
```

ビルドスクリプトは以下を自動で行います：

1. Python 仮想環境の作成
2. PyInstaller のインストール
3. メインアプリ EXE の作成
4. JSON エディター EXE の作成
5. JSON ファイルを `dist` フォルダーへコピー

出力先：

```txt
dist
```

生成されるファイル例：

```txt
dist/Mellishs_Multilingual_Mute_Soundboard.exe
dist/Phrase_Board_JSON_Editor.exe
everyday_conversation.json
general_social.json
vrchat_technical.json
flirty_social.json
board_5.json
dist/board_settings.json
```

## 注意事項

日本語テキストは UTF-8 の OSC 文字列として送信されます。

本ツールは VRChat の OSC チャットボックス機能で動作確認を行っていますが、将来的な VRChat のアップデートによって仕様が変更される可能性があります。

動作しなくなった場合は、まず VRChat 側で OSC が有効になっているか確認してください。

## 推奨 GitHub Topics

```txt
vrchat
osc
chatbox
accessibility
python
tkinter
japanese
translation
soundboard
```

## ライセンス

MIT License
