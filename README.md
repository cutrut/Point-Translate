# Point & Translate

Point at a word and press `2`. The translation pops up next to it.

Use it to look up words while playing games or reading visual novels in a
language you're learning. It reads text off the screen, even in menus and
dialogue boxes where you can't copy it. It's free, runs on Windows, and
reads **Latin-script text** like English.

[Tiếng Việt](README.vi.md)

## Get it running

1. Unzip it into a folder you can write to. Keep `point_and_translate.py`
   and the two BAT files together.
2. Run `Check_And_Install.bat`. It checks for **Python 3.12 x64**, Python
   packages, Chrome and the OneOCR engine. It tries to install what's missing.
   Wait for `[READY]`.
3. Run `Start_Point_And_Translate.bat`. In the Chrome window for DeepL, pick
   your source and target languages, complete any verification yourself, and
   try a short sentence. Leave that Chrome window open.
4. Minimise **Controls**, go back to the game or app, and try `2` on a word.

Next time, just run `Start_Point_And_Translate.bat`.

If you already use Hover Dict, unzip into the old app folder and replace
`Check_And_Install.bat` when asked. Start it with the new launcher to pick up
your saved keys, translation cache and Chrome session.

### From CMD

Open the app folder in File Explorer, type `cmd` in the address bar, and
press Enter. Run these one at a time, waiting for `[READY]` after the first:

```bat
Check_And_Install.bat
Start_Point_And_Translate.bat
```

To install the Python packages by hand, run
`py -3.12 -m pip install --user -r requirements.txt`. The checker handles
Chrome and the OneOCR engine separately.

## Keys

| Key | What it does |
| --- | --- |
| Point at a word | Highlight it |
| `2` | Read and translate the word at the pointer |
| Hold `1`, sweep over words, then release | Translate the words you picked |
| `3` | Scan the screen again |
| `F8` | Toggle a separate pointer if the game hides or locks the mouse |
| Left `Alt` + arrows | Nudge the separate pointer |
| `Esc` | Close Point & Translate |

The separate pointer moves with your mouse. The game keeps control of its
own cursor and camera.

To change a key, open **Actions** or **Pointer** in **Controls**. Click the
current key, press and release the new one, then hit **Save**. Click the
same button or switch windows to cancel. **Defaults** followed by **Save**
brings back the original keys.

Each action takes one key, and each key can only be assigned once. The game
still gets your keypresses. If you bind a modifier like Ctrl, the action
also fires when you use Ctrl in a shortcut. For a hold action bound to
`Pause`, tap once to start and once to stop. [Windows key limits](https://learn.microsoft.com/en-us/windows/powertoys/keyboard-manager)

Hotkeys pause while **Controls** has focus. **Minimise** keeps the app running,
and **X** closes it. To open just the settings, run
`Start_Point_And_Translate.bat settings` in CMD.

## If it gets stuck

- **Setup stopped.** Read the error in CMD. If WinGet is missing, install
  Python 3.12 x64 with Python Launcher and Tcl/Tk, plus Chrome. Then run the
  checker again. [Python](https://www.python.org/downloads/windows/) · [Chrome](https://www.google.com/chrome/)
- **OneOCR files are missing.** The checker tries to get them from Snipping
  Tool or install/update it through Microsoft Store. For manual setup, put
  a matching x64 set of `oneocr.dll`, `oneocr.onemodel` and `onnxruntime.dll`
  in `%USERPROFILE%\.config\oneocr\`, then rerun the checker. [OneOCR setup](https://github.com/AuroraWright/oneocr)
- **DeepL is stuck.** Check the Chrome window for verification, double-check
  the languages, and read any error in CMD.
- **Overlay missing in a game.** Try **Borderless Windowed**.
  **Hearts of Iron IV (HOI4)** is a known incompatibility.
- **Changed languages or translation backend.** Close the app and delete
  `hover_dict_cache.db`. The cache uses the original text to find translations.

## What it saves

OneOCR reads the screen locally. The text you look up goes to DeepL.
`keybindings.json` holds your keys, `hover_dict_cache.db` holds translations,
and `BotChromeProfile/` holds the app's separate Chrome session.
OCR and translation settings are near the top of `point_and_translate.py`.

---

Source and docs are MIT licensed. Third-party components have their own terms.
Native Windows and game testing are still pending. [Test checklist](TESTING.md)

5.3.3 Simple · [Changes](CHANGELOG.md) · [MIT License](LICENSE)
