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
