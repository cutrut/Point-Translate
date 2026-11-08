# Hover Dict — simple edition

Point at text on your screen, press a key, and read its translation beside it.
A Windows OCR overlay using OneOCR and DeepL for games, visual novels and
applications whose text cannot be selected.

**Supported text: Latin-alphabet text only, such as English.** Some games,
including **Hearts of Iron IV (HOI4)**, currently do not work with this tool.

[Tiếng Việt](README.vi.md)

## Files

| File | Purpose |
| --- | --- |
| `Start_Hover_Dict.bat` | Open the dedicated DeepL Chrome window and run the app |
| `hover_dict_v5_1_LN_fix.py` | The complete app, including its key settings window |
| `Check_And_Install.bat` | Check requirements and install missing components |
| `requirements.txt` | Python package list for manual CMD installation |
| `README.md`, `README.vi.md` | English and Vietnamese instructions |

Keep the three runnable files together and retain the filenames in the ZIP.

## Install and run

1. Extract into a writable folder. The app requires **Windows and Python 3.12 x64**.
2. Run **`Check_And_Install.bat`**. It checks the same Python used by the launcher
   and installs packages whose imports fail. Existing working packages are
   retained; no `.venv` is required.
3. Missing Python or Chrome: the checker tries WinGet. Missing OneOCR engine
   files: it tries copying a matching set from the installed Snipping Tool,
   then installing/updating Snipping Tool through Microsoft Store. If a step
   cannot finish, it names the missing component; resolve it and run the check again.
4. After **`[READY]`**, double-click **`Start_Hover_Dict.bat`**.
5. Open DeepL in the dedicated Chrome window. **Manually complete any CAPTCHA
   or verification prompt**, select the correct **source and target languages**,
   test a short sentence and keep this Chrome window open.
6. Minimise the Hover Dict window or return to your game/reading application,
   point at text, and press the lookup key (`2` by default).

For later launches, use `Start_Hover_Dict.bat`. Run the checker again if an
installation or import error appears.

## CMD instructions

Open the app folder in **File Explorer**, click the address bar, type `cmd`,
and press **Enter**. Enter each command below separately and press **Enter**:

```bat
Check_And_Install.bat
Start_Hover_Dict.bat
```

Wait for the checker to finish with `[READY]` before starting the app.
To install Python packages manually after installing Python 3.12:

```bat
py -3.12 -m pip install --user -r requirements.txt
```

Pip installs Python packages. The checker separately handles Chrome and the
three OneOCR engine files. `playwright install` is unnecessary because the app
connects to the existing Chrome browser.

## Change the keys

The main Hover Dict window has **Actions** and **Pointer** tabs. Choose/type
keys, click **Save**, then minimise the window or return to your game. Saved
keys apply immediately. **Defaults** fills in the original keys; click **Save**
to apply the reset.

Actions accept one key: `0`–`9`, `a`–`z`, `F1`–`F12`, or a listed named key.
The pointer nudge modifier is configured separately. Action chords such as
`Ctrl+2` are not supported. Duplicate or invalid bindings are rejected.
Global action keys pause while the settings window has focus. Closing the
main window with **X** exits the app; minimise it to keep reading.

To edit keys without starting OCR, open CMD as above and run:

```bat
Start_Hover_Dict.bat settings
```

## Default controls

| Input | Action |
| --- | --- |
| Move the pointer over text | Highlight the current word without translating |
| `2` | Capture fresh pixels and translate the word at the pointer |
| Hold `1`, sweep over words, release | Collect and translate a selection |
| `3` | Force a full-screen OCR refresh |
| `F8` | Toggle the virtual pointer for some games/VNs that hide or lock the cursor |
| Left `Alt` + arrows | Nudge the virtual pointer |
| `F9` | Experimental Japanese segmentation, outside supported scope |
| `Esc` | Exit while using the game/reading application |

The **virtual pointer** draws a separate lookup crosshair when a game or VN
hides the normal mouse or keeps it at the screen centre. Move the mouse or use
the configured nudge keys to position it over text. It does not unlock the
game's cursor or pause its camera. Compatibility varies; the HOI4 limitation
still applies.

## Missing components and troubleshooting

- Without WinGet, install [Python 3.12 x64](https://www.python.org/downloads/windows/)
  with **Python Launcher** and **Tcl/Tk**, plus [Chrome](https://www.google.com/chrome/),
  then rerun the checker.
- If the engine files cannot be copied automatically, follow the
  [OneOCR instructions](https://github.com/AuroraWright/oneocr). Place a matching
  x64 set of `oneocr.dll`, `oneocr.onemodel` and `onnxruntime.dll` in
  `%USERPROFILE%\.config\oneocr\`, then rerun the checker.
- Missing overlay in a game: try **Borderless Windowed**. Some games remain incompatible.
- No translation: read the CMD error and check DeepL verification and languages.
- After changing languages or translation backend, close the app and remove
  `hover_dict_cache.db`; cache entries currently depend only on source text.

The app generates `keybindings.json` when saving keys, `hover_dict_cache.db`
for translations and `BotChromeProfile/` for its dedicated Chrome session.
These do not need to be downloaded or created manually. OCR is local; selected
text is sent to DeepL. Advanced OCR/backend options remain near the top of the
Python source. Japanese code is experimental; supported reading remains Latin only.

**5.3.1 Simple** is based on the two working files supplied by the user.
Automated checks cover logic. Native installation, GUI and game hooks still
need Windows testing. To publish on GitHub, upload the extracted files at the
repository root so README appears on its landing page; do not upload only the ZIP.
