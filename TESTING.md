# Testing Point & Translate 5.3.3 Simple

**Native Windows status: not yet tested for this release.** Check a box only
after observing the expected result. A setup `[READY]` message verifies local
prerequisites; it does not certify game or DeepL compatibility.

## Automated release checks

The release preparation checks Python compilation and import, CLI help,
unsupported-platform exit messages, key capture/cancellation, saved binding
round trips, duplicate rejection, package import detection and complete versus
incomplete OCR engine file copies. Both BAT filenames, their line endings,
README links and the final ZIP manifest are checked separately.

These are logic and packaging checks, not native Windows integration tests.
The original 5.3.3 build passed **15/15 checks** on 2026-11-08 using
Python 3.12.14 on Linux. Native Windows results remain unrecorded.

To repeat the basic syntax/help checks on Windows, run separately in CMD:

```bat
py -3.12 -m py_compile point_and_translate.py
py -3.12 point_and_translate.py --help
```

## Record the test environment

- Test date:
- Windows edition, version and build:
- Python version and architecture (requires 3.12 x64):
- Chrome version:
- Snipping Tool version / source of the matching engine files:
- Source and target translation languages:
- Installation path:
- Fresh installation or upgrade:

## Installation and upgrade

- [ ] Fresh installation: extract into a writable folder, run
  `Check_And_Install.bat`, follow any prompts, and confirm `[READY]` only after
  Python packages import, Chrome exists and OneOCR actually loads.
- [ ] Repeat the checker after a successful install. Working packages are
  retained, the engine loads again and the result remains `[READY]`.
- [ ] Repeat with a folder path containing spaces, Vietnamese characters
  and an ampersand. Both BAT files locate and run `point_and_translate.py`
  from that folder.
- [ ] If Python, WinGet, Chrome or the matching OneOCR files cannot be
  installed, confirm a useful error is shown and the checker does not claim
  `[READY]`. Record which missing-component case was tested.
- [ ] Upgrade an existing Hover Dict folder as described in [README.md](README.md).
  Confirm the app reuses saved keys, the translation cache and the Chrome session.
  Test upgrades with saved numeric and legacy named key bindings.

## Controls and OCR

- [ ] `Start_Point_And_Translate.bat settings` opens the English Controls window
  without starting OCR or opening Chrome.
- [ ] Click a binding button, press and release a key, then Save. The binding
  works after returning to the reading app and survives a restart.
- [ ] A duplicate binding is rejected; clicking the button again or leaving
  the window cancels capture without leaving a key stuck.
- [ ] Try punctuation, left/right modifiers, a numpad key and a function key
  present on the keyboard. Record the keys actually tested.
- [ ] Defaults then Save restores the documented bindings. Hotkeys pause
  while Controls has focus; Minimise keeps the app running and X exits.
- [ ] In a desktop app displaying Latin-alphabet text, moving over a word
  highlights it. `2` captures the current text; `3` refreshes OCR.
- [ ] Hold `1`, sweep across words and release: the selected phrase is sent
  for translation. If Pause is assigned to a hold action, test tap-to-start
  and tap-to-stop separately.
- [ ] F8 toggles the virtual pointer; mouse movement and Left Alt + arrows
  position it. Esc exits from the reading app without leaving the overlay.

## DeepL and games

- [ ] Launch normally. The dedicated Chrome window is ready, any verification
  is completed manually and the selected source/target languages are correct.
- [ ] Translate a new short sentence and confirm that the returned translation
  appears beside the selected text. Repeat it to check cached output.
- [ ] Close the dedicated Chrome window and try a new lookup. Record the
  displayed error and whether restarting the launcher restores translation.
- [ ] Test each target game individually, recording its version, display mode
  and whether it runs elevated. Try Borderless Windowed if needed. Verify
  capture, hooks, overlay and virtual pointer separately.

| Game/app and version | Display mode | Capture | Keys | Overlay | Virtual pointer | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Not yet tested | — | — | — | — | — | — |

HOI4 is a known incompatibility; do not list it as working without a verified
fix and a recorded native test.

For a demo, record the actual Windows app: point at a word, press the lookup
key and show the returned translation. Use the recording only after checking
that the full lookup flow worked.
