"""
Hover Dict 5.3.1 Simple — OneOCR + DeepL, Windows / Python 3.12 x64.

First run: Check_And_Install.bat (checks and installs missing requirements).
Use: Start_Hover_Dict.bat. Change keys in the same application window, Save,
then minimise it or return to the game. Settings apply immediately.
Edit keys without starting OCR: Start_Hover_Dict.bat settings

Default controls: 2 lookup; hold 1 to collect words; 3 refresh OCR; F8 virtual
pointer for games/VNs hiding or recentering the mouse; Left Alt + arrows nudge;
F9 experimental Japanese segmentation; Esc exit. Supported text: Latin only.
Some games, including HOI4, currently do not work.

In the dedicated DeepL Chrome window, complete any verification manually,
select the source/target languages you need, and keep the window open.
Read README.vi.md or README.md for setup and troubleshooting.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import queue
import shutil
import string
import struct
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import unicodedata
from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path
from typing import Optional



# Key settings are embedded here; no helper module is needed.
CONFIG_PATH = Path(__file__).with_name("keybindings.json")

DEFAULT_BINDINGS = {
    "collect": "1",
    "lookup": "2",
    "refresh": "3",
    "toggle_pointer": "f8",
    "toggle_japanese": "f9",
    "exit": "esc",
    "pointer_modifier": "alt_l",
    "pointer_left": "left",
    "pointer_right": "right",
    "pointer_up": "up",
    "pointer_down": "down",
}

ACTION_LABELS = {
    "collect": "Giữ để gom từ / Hold to collect words",
    "lookup": "Dịch từ / Translate word",
    "refresh": "Quét OCR lại / Refresh OCR",
    "toggle_pointer": "Con trỏ ảo cho game/VN ẩn chuột / Virtual pointer",
    "toggle_japanese": "Tách từ Nhật thử nghiệm / Experimental Japanese",
    "exit": "Thoát Hover Dict / Exit",
    "pointer_modifier": "Phím giữ khi chỉnh con trỏ / Nudge modifier",
    "pointer_left": "Dời con trỏ sang trái / Nudge left",
    "pointer_right": "Dời con trỏ sang phải / Nudge right",
    "pointer_up": "Dời con trỏ lên / Nudge up",
    "pointer_down": "Dời con trỏ xuống / Nudge down",
}

SPECIAL_VKS = {
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "caps_lock": 0x14,
    "esc": 0x1B, "space": 0x20, "page_up": 0x21, "page_down": 0x22,
    "end": 0x23, "home": 0x24, "left": 0x25, "up": 0x26,
    "right": 0x27, "down": 0x28, "insert": 0x2D, "delete": 0x2E,
    **{f"f{number}": 0x6F + number for number in range(1, 13)},
}

KEY_CHOICES = tuple(string.digits + string.ascii_lowercase) + tuple(SPECIAL_VKS)

MODIFIER_CHOICES = ("alt_l", "alt_r", "ctrl_l", "ctrl_r", "shift_l", "shift_r", "cmd_l", "cmd_r")

_ALIASES = {
    "escape": "esc", "return": "enter", "spacebar": "space",
    "ctrl": "ctrl_l", "control": "ctrl_l", "shift": "shift_l",
    "alt": "alt_l", "cmd": "cmd_l", "win": "cmd_l", "alt_gr": "alt_r",
    "left_ctrl": "ctrl_l", "right_ctrl": "ctrl_r",
    "left_alt": "alt_l", "right_alt": "alt_r",
    "left_shift": "shift_l", "right_shift": "shift_r",
    "left_win": "cmd_l", "right_win": "cmd_r",
}

def normalize_key(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Key names must be strings")
    name = value.strip().lower().removeprefix("key.").replace(" ", "_").replace("-", "_")
    name = _ALIASES.get(name, name)
    if name not in KEY_CHOICES and name not in MODIFIER_CHOICES:
        raise ValueError(f"Unsupported key {value!r}; choose one letter, digit, F1-F12 or a listed key")
    return name

def validate_bindings(data: dict) -> dict[str, str]:
    if not isinstance(data, dict):
        raise ValueError("Keybindings must be a JSON object")
    unknown = set(data) - set(DEFAULT_BINDINGS)
    if unknown:
        raise ValueError("Unknown action(s): " + ", ".join(sorted(map(str, unknown))))
    bindings = DEFAULT_BINDINGS.copy()
    for action, value in data.items():
        bindings[action] = normalize_key(value)
    used = {}
    for action, key in bindings.items():
        allowed = MODIFIER_CHOICES if action == "pointer_modifier" else KEY_CHOICES
        if key not in allowed:
            raise ValueError(f"Invalid key {key!r} for {action}")
        if key in used:
            raise ValueError(f"Duplicate key {key!r}: {used[key]} and {action}")
        used[key] = action
    return bindings

def load_bindings(path: Path = CONFIG_PATH) -> dict[str, str]:
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return DEFAULT_BINDINGS.copy()
    return validate_bindings(json.loads(text))

def save_bindings(path: Path, data: dict) -> dict[str, str]:
    bindings = validate_bindings(data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".keybindings-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            json.dump(bindings, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return bindings

def event_key_name(key) -> str | None:
    """Return a key identity even when Ctrl/Shift changes its typed character."""
    name = getattr(key, "name", None)
    char = getattr(key, "char", None)
    value = name if isinstance(name, str) else char
    if value is not None:
        try:
            return normalize_key(value)
        except ValueError:
            pass  # Ctrl+A / Shift+4 still have a stable Windows virtual key.
    vk = getattr(key, "vk", None)
    if isinstance(vk, int):
        if 0x41 <= vk <= 0x5A:
            return chr(vk).lower()
        if 0x30 <= vk <= 0x39:
            return chr(vk)
        if 0x60 <= vk <= 0x69:
            return str(vk - 0x60)
        return next((name for name, code in SPECIAL_VKS.items() if code == vk), None)
    return None

def display_key(name: str) -> str:
    labels = {"alt_l": "Left Alt", "alt_r": "Right Alt", "ctrl_l": "Left Ctrl",
              "ctrl_r": "Right Ctrl", "shift_l": "Left Shift", "shift_r": "Right Shift",
              "cmd_l": "Left Win", "cmd_r": "Right Win"}
    return labels.get(name, name.replace("_", " ").upper())

KEY_BINDINGS = DEFAULT_BINDINGS.copy()
_editing_keys = threading.Event()
_held_modifiers = set()

# ─── Config ───────────────────────────────────────────────────────────────────
CAPTURE_FPS = 24             # chỉ chụp vùng đang đọc trong chế độ tự động
HOVER_INTERVAL_MS = 12       # Tk lấy tọa độ và vẽ khung độc lập với OCR
POPUP_DISMISS_DISTANCE_PX = 120  # khoảng cách từ con trỏ lúc popup cả cụm hiện lên
LOOKUP_BOX_TOLERANCE_PX = 4  # bỏ qua độ rung nhỏ của bbox OCR, không dời mốc theo chữ
LOOKUP_MISS_GRACE_MS = 180   # chịu được một lần OCR bỏ sót chữ đang tra
LOOKUP_MAX_OCR_ATTEMPTS = 3  # số lần đọc tối đa cho một lần bấm 2
OCR_REGION_WIDTH = 880
OCR_REGION_HEIGHT = 480
OCR_REGION_MARGIN = 100      # rê trong vùng này thì giữ nguyên vùng chụp
DEBUG_OCR      = False        # True: log lý do mỗi lần OCR
VIRTUAL_POINTER_SENSITIVITY = 1.0  # pixel mỗi count chuột thô khi bật F8
GAP_PX        = 4            # pixel gap tối thiểu để tách từ (chỉ dùng khi fallback pixel-gap)
DB_PATH       = Path(__file__).parent / "hover_dict_cache.db"

# ─── Backend dịch ───────────────────────────────────────────────────────────────
# "deepl_app" -> điều khiển app DeepL desktop qua UI Automation (Windows only)
# "deepl_web" -> điều khiển deepl.com/translator qua Playwright (Chrome thật qua CDP)
TRANSLATE_BACKEND = "deepl_web"

# DeepL app — AutomationId của ô input/output. Kiểm tra cây UI Automation để xác nhận
# giá trị đúng trên máy bạn; để rỗng "" thì code sẽ tự đoán (kém tin cậy hơn).
DEEPL_WINDOW_NAME_HINT   = "deepl"   # chuỗi (lowercase) để nhận diện cửa sổ DeepL
DEEPL_INPUT_AUTOMATION_ID  = ""
DEEPL_OUTPUT_AUTOMATION_ID = ""
DEEPL_POLL_INTERVAL   = 0.15   # giây giữa các lần đọc ô output khi chờ dịch xong
DEEPL_STABLE_READS    = 3      # số lần đọc liên tiếp giống nhau mới coi là "dịch xong"
DEEPL_TIMEOUT         = 6.0    # giây tối đa chờ DeepL dịch xong trước khi bỏ cuộc

# DeepL web (Playwright) — KẾT NỐI vào 1 cửa sổ Chrome THẬT đang chạy sẵn
# (chạy Start_Hover_Dict.bat trước để mở), qua CDP (Chrome DevTools Protocol).
# KHÔNG launch Chromium riêng nữa — vì Chrome thật có fingerprint tự nhiên
# hơn, giảm khả năng bị deepl.com chặn như automation. Cửa sổ Chrome này dùng
# profile riêng (BotChromeProfile), tách biệt hoàn toàn với Chrome cá nhân.
DEEPL_WEB_URL          = "https://www.deepl.com/en/translator"
DEEPL_WEB_CDP_URL      = "http://127.0.0.1:9222"   # debug port mà Start_Hover_Dict.bat mở
DEEPL_WEB_POLL_INTERVAL = 0.05  # lấy kết quả sớm hơn; không tăng request dịch lên server
DEEPL_WEB_STABLE_READS  = 3
DEEPL_WEB_TIMEOUT       = 10.0



# ─── OCR Engine (OneOCR — engine native của Snipping Tool, Windows only) ──────
_ocr_engine = None

def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        import oneocr
        print("⏳ Đang load OneOCR (đọc DLL native từ Snipping Tool)...")
        _ocr_engine = oneocr.OcrEngine()
        print("✅ OneOCR ready")
    return _ocr_engine

# ─── SQLite cache ─────────────────────────────────────────────────────────────
import sqlite3

_db_conn: Optional[sqlite3.Connection] = None
_db_lock = threading.Lock()

def _db() -> sqlite3.Connection:
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _db_conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        _db_conn.commit()
    return _db_conn

def cache_get(text: str) -> Optional[str]:
    key = hashlib.md5(text.lower().encode()).hexdigest()
    with _db_lock:
        row = _db().execute("SELECT value FROM cache WHERE key=?", (key,)).fetchone()
    return row[0] if row else None

def cache_set(text: str, translated: str):
    key = hashlib.md5(text.lower().encode()).hexdigest()
    with _db_lock:
        _db().execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (key, translated))
        _db().commit()

# ─── Data types ───────────────────────────────────────────────────────────────
@dataclass
class Token:
    word: str
    x1: int; y1: int; x2: int; y2: int

    def contains(self, mx: int, my: int) -> bool:
        return self.x1 <= mx <= self.x2 and self.y1 <= my <= self.y2


@dataclass
class _LookupTarget:
    token: Token
    seq: int
    snapshot: list[Token]
    signature: Optional[bytes] = None
    missing_since: Optional[float] = None
    misses: int = 0

# ─── Pixel-gap word splitting ─────────────────────────────────────────────────
def _split_line_by_pixel_gaps(
    img_gray: np.ndarray,
    words: list[str],
    line_x1: int, line_y1: int, line_x2: int, line_y2: int,
) -> list[Token]:
    """
    Crop dòng từ ảnh grayscale, đo column projection để tìm bbox chính xác
    cho TỪNG từ trong `words` (số từ đã được quyết định sẵn bởi dấu cách
    trong text OCR trả về — KHÔNG suy luận lại số từ từ pixel, dấu cách
    trong text mới là thứ quyết định ranh giới từ).

    Cách làm: ước lượng vị trí cắt KỲ VỌNG giữa mỗi cặp từ liên tiếp dựa
    theo tỉ lệ độ dài ký tự (word dài hơn → chiếm nhiều pixel hơn). Với
    mỗi vị trí kỳ vọng đó, tìm gap pixel THẬT gần nhất quanh nó để bám
    theo (nếu có, trong 1 cửa sổ tìm kiếm hợp lý) — tránh bị mini-gap
    nội bộ (kerning giữa các nét chữ trong cùng 1 từ) đánh lừa, vì
    mini-gap đó thường nằm xa vị trí kỳ vọng.
    Nếu không tìm thấy gap thật gần vị trí kỳ vọng, dùng thẳng vị trí
    kỳ vọng (chia theo tỉ lệ ký tự) làm điểm cắt.
    """
    h, w = img_gray.shape
    cx1 = max(0, line_x1); cx2 = min(w, line_x2)
    cy1 = max(0, line_y1); cy2 = min(h, line_y2)
    n = len(words)
    if cx2 <= cx1 or cy2 <= cy1 or n == 0:
        return []

    if n == 1:
        return [Token(word=words[0], x1=cx1, y1=line_y1, x2=cx2, y2=line_y2)]

    crop = img_gray[cy1:cy2, cx1:cx2].astype(np.float32)
    col_mean = crop.mean(axis=0)
    cw = crop.shape[1]
    threshold = col_mean.mean() * 0.95
    in_gap = col_mean >= threshold

    # đo các đoạn gap liên tục (khoảng trắng) → midpoint + width của từng đoạn
    gap_runs: list[tuple[int, int]] = []  # (mid_col, width)
    i = 0
    while i < cw:
        if in_gap[i]:
            j = i
            while j < cw and in_gap[j]:
                j += 1
            gap_runs.append(((i + j - 1) // 2, j - i))
            i = j
        else:
            i += 1

    # vị trí cắt KỲ VỌNG theo tỉ lệ ký tự (đường cơ sở luôn đáng tin, không phụ thuộc pixel)
    total_chars = sum(len(w) for w in words)
    expected_cuts: list[int] = []
    if total_chars > 0:
        acc_chars = 0
        for w_str in words[:-1]:
            acc_chars += len(w_str)
            expected_cuts.append(int(cw * acc_chars / total_chars))
    else:
        expected_cuts = [int(cw * (k + 1) / n) for k in range(n - 1)]

    # cửa sổ tìm gap thật quanh mỗi vị trí kỳ vọng — nới đủ rộng để chịu được
    # sai lệch tự nhiên giữa tỉ lệ ký tự và tỉ lệ pixel thực tế (chữ rộng/hẹp
    # khác nhau tùy ký tự, vd "m"/"w" rộng hơn nhiều so với "i"/"l")
    bounds = [0]
    prev_cut = 0
    for k, exp_cut in enumerate(expected_cuts):
        avg_word_chars = (len(words[k]) + len(words[k+1])) / 2 if total_chars else 1
        search_radius = max(14, int(cw * (avg_word_chars / max(total_chars, 1)) * 0.6))

        candidates = [g for g in gap_runs if abs(g[0] - exp_cut) <= search_radius]
        if candidates:
            # ưu tiên gap rộng nhất trong vùng tìm kiếm (gap thật giữa 2 từ thường rộng hơn kerning)
            best = max(candidates, key=lambda g: g[1])
            cut = best[0]
        else:
            # không có gap thật gần đó → dùng thẳng vị trí kỳ vọng
            cut = exp_cut

        cut = max(cut, prev_cut + 1)  # đảm bảo tăng dần
        bounds.append(cut)
        prev_cut = cut
    bounds.append(cw)

    tokens: list[Token] = []
    for k, w_str in enumerate(words):
        s, e = bounds[k], bounds[k+1]
        tokens.append(Token(
            word=w_str,
            x1=cx1 + s, y1=line_y1,
            x2=cx1 + e, y2=line_y2,
        ))

    return tokens

def _quad_to_bbox(rect: Optional[dict]) -> Optional[tuple[int, int, int, int]]:
    """Chuyển bounding_rect tứ giác (x1,y1..x4,y4) mà OneOCR trả về thành
    bbox thẳng (x1,y1,x2,y2). Text màn hình hầu như luôn thẳng (text_angle
    ~0) nên việc lấy min/max 4 điểm là đủ chính xác, không cần xoay."""
    if not rect:
        return None
    try:
        xs = [rect["x1"], rect["x2"], rect["x3"], rect["x4"]]
        ys = [rect["y1"], rect["y2"], rect["y3"], rect["y4"]]
        return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
    except Exception:
        return None


# ─── OCR ──────────────────────────────────────────────────────────────────────
_japanese_tokenizer = None
_japanese_tokenizer_unavailable = False

def _has_kana(text: str) -> bool:
    return any(
        "\u3040" <= c <= "\u30ff" or "\u31f0" <= c <= "\u31ff" or "\uff66" <= c <= "\uff9f"
        for c in text
    )

def _has_japanese_script(text: str) -> bool:
    return _has_kana(text) or any(
        "\u3400" <= c <= "\u9fff" or "\uf900" <= c <= "\ufaff"
        or "\U00020000" <= c <= "\U000323af" for c in text
    )

def _compact_text(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).split())

def _japanese_spans(text: str) -> list[tuple[int, int]]:
    global _japanese_tokenizer, _japanese_tokenizer_unavailable
    if _japanese_tokenizer_unavailable:
        return []
    if _japanese_tokenizer is None:
        try:
            from sudachipy import Dictionary
            dictionary = Dictionary(dict="core")
            factory = getattr(dictionary, "tokenizer", dictionary.create)
            _japanese_tokenizer = factory()
        except (ImportError, OSError, RuntimeError, ValueError) as e:
            _japanese_tokenizer_unavailable = True
            print(f"Tách từ Nhật chưa khả dụng: {e}")
            print("Cài: py -3.12 -m pip install sudachipy sudachidict_core")
            return []
    return [(word.begin(), word.end()) for word in _japanese_tokenizer.tokenize(text)
            if any(c.isalnum() for c in word.surface())]

def _japanese_line_tokens(line: dict) -> list[Token]:
    text = _compact_text(line.get("text") or "")
    if not text:
        return []

    parts = []
    for word in line.get("words") or []:
        chars = _compact_text(word.get("text") or "")
        box = _quad_to_bbox(word.get("bounding_rect"))
        if chars and box:
            parts.append((chars, box))

    line_box = _quad_to_bbox(line.get("bounding_rect"))
    if "".join(chars for chars, _ in parts) != text:
        if line_box is None:
            return []
        parts = [(text, line_box)]

    vertical = line_box is not None and line_box[3] - line_box[1] > (line_box[2] - line_box[0]) * 1.5
    char_boxes = []
    for chars, (x1, y1, x2, y2) in parts:
        length = len(chars)
        for i in range(length):
            if vertical:
                lo = y1 + (y2 - y1) * i // length
                hi = y1 + (y2 - y1) * (i + 1) // length
                char_boxes.append((x1, lo, x2, max(lo, hi - (i + 1 < length))))
            else:
                lo = x1 + (x2 - x1) * i // length
                hi = x1 + (x2 - x1) * (i + 1) // length
                char_boxes.append((lo, y1, max(lo, hi - (i + 1 < length)), y2))

    tokens = []
    for start, end in _japanese_spans(text):
        boxes = char_boxes[start:end]
        if boxes:
            tokens.append(Token(text[start:end], min(b[0] for b in boxes), min(b[1] for b in boxes),
                                max(b[2] for b in boxes), max(b[3] for b in boxes)))
    return tokens

def _run_ocr(img_array: np.ndarray, force_japanese: bool = False) -> list[Token]:
    """
    OneOCR.recognize_pil() trả về dict: {'text', 'text_angle', 'lines': [...]}.
    Mỗi line có 'text', 'bounding_rect' (tứ giác cấp DÒNG), và 'words' — list
    các từ, mỗi từ có 'text', 'bounding_rect' (tứ giác cấp TỪ THẬT do model
    tính, không phải đoán qua khoảng trắng pixel) và 'confidence'.
    Nếu 1 dòng nào đó không có word list hợp lệ (hiếm), fallback về
    _split_line_by_pixel_gaps như bản PaddleOCR cũ.
    """
    from PIL import Image
    result = _get_ocr().recognize_pil(Image.fromarray(img_array))

    img_gray = None
    all_tokens: list[Token] = []
    lines = result.get("lines") or []
    japanese = force_japanese or any(_has_kana(line.get("text") or "") for line in lines)
    for line in lines:
        words = line.get("words") or []
        line_text = (line.get("text") or "").strip()
        if japanese and _has_japanese_script(line_text):
            segmented = _japanese_line_tokens(line)
            if segmented:
                all_tokens.extend(segmented)
                continue

        used_native = False
        for w in words:
            w_text = (w.get("text") or "").strip()
            conf = w.get("confidence")
            if not w_text:
                continue
            # ngưỡng thấp tương tự bản PaddleOCR cũ, để không loại nhầm
            # từ ngắn (to/is/of...) vốn hay có confidence thấp hơn từ dài
            if conf is not None and conf < 0.15:
                continue
            bbox = _quad_to_bbox(w.get("bounding_rect"))
            if bbox is None:
                continue
            bx1, by1, bx2, by2 = bbox
            all_tokens.append(Token(word=w_text, x1=bx1, y1=by1, x2=bx2, y2=by2))
            used_native = True

        if used_native or not line_text:
            continue

        # ── Fallback: dòng không có word list hợp lệ → đoán bằng pixel-gap ──
        bbox = _quad_to_bbox(line.get("bounding_rect"))
        if bbox is None:
            continue
        x1, y1, x2, y2 = bbox
        split_words = line_text.split()
        if not split_words:
            continue
        if len(split_words) == 1:
            all_tokens.append(Token(split_words[0], x1, y1, x2, y2))
            continue
        if img_gray is None:
            img_gray = np.mean(img_array, axis=2, dtype=np.float32)
        toks = _split_line_by_pixel_gaps(img_gray, split_words, x1, y1, x2, y2)
        all_tokens.extend(toks)

    return all_tokens

# ─── Screen capture ───────────────────────────────────────────────────────────
# KHÔNG tạo mss.mss() ở module level — GDI device context trên Windows không
# thread-safe khi dùng chung giữa main thread và OCR thread → BitBlt fail.
# Mỗi thread tự tạo instance riêng qua _thread_local bên dưới.
_thread_local = threading.local()

def _get_sct():
    if not hasattr(_thread_local, "sct"):
        _thread_local.sct = mss.MSS()
    return _thread_local.sct

def _capture_region(monitors, point, previous=None):
    x, y = point
    monitor = next((m for m in monitors[1:] if
                    m["left"] <= x < m["left"] + m["width"] and
                    m["top"] <= y < m["top"] + m["height"]), monitors[0])
    left, top = monitor["left"], monitor["top"]
    right, bottom = left + monitor["width"], top + monitor["height"]
    if previous is not None:
        px, py, w, h = (previous[k] for k in ("left", "top", "width", "height"))
        if (left <= px and top <= py and px + w <= right and py + h <= bottom
                and px + (OCR_REGION_MARGIN if px > left else 0) <= x
                < px + w - (OCR_REGION_MARGIN if px + w < right else 0)
                and py + (OCR_REGION_MARGIN if py > top else 0) <= y
                < py + h - (OCR_REGION_MARGIN if py + h < bottom else 0)):
            return previous
    width = min(OCR_REGION_WIDTH, monitor["width"])
    height = min(OCR_REGION_HEIGHT, monitor["height"])
    return dict(left=min(max(left, x - width // 2), right - width),
                top=min(max(top, y - height // 2), bottom - height),
                width=width, height=height)

def _screen_sig(raw) -> bytes:
    return hashlib.blake2b(raw.raw, digest_size=12).digest()

def _bgra(raw) -> np.ndarray:
    return np.frombuffer(raw.raw, dtype=np.uint8).reshape(raw.height, raw.width, 4)

def _rgb(raw) -> np.ndarray:
    return _bgra(raw)[:, :, 2::-1]

def _capture_key(raw, area, region, japanese):
    if area == region:
        sig = _screen_sig(raw)
    else:
        x = region["left"] - area["left"]
        y = region["top"] - area["top"]
        crop = _bgra(raw)[y:y + region["height"], x:x + region["width"]]
        sig = hashlib.blake2b(crop.tobytes(), digest_size=12).digest()
    return (region["left"], region["top"], region["width"], region["height"], japanese, sig)


def _word_screen_sig(raw, area, token):
    x1, y1 = token.x1 - area["left"], token.y1 - area["top"]
    x2, y2 = token.x2 - area["left"], token.y2 - area["top"]
    if not (0 <= x1 < x2 <= raw.width and 0 <= y1 < y2 <= raw.height):
        return None
    crop = _bgra(raw)[y1:y2, x1:x2, :3]  # ignore unused alpha bytes
    return hashlib.blake2b(crop.tobytes(), digest_size=12).digest()

def _ocr_tokens(img, left, top, japanese, scale=1):
    return [Token(t.word, left + t.x1 // scale, top + t.y1 // scale,
                  left + t.x2 // scale, top + t.y2 // scale)
            for t in _run_ocr(img, japanese)]

def _hit_token(tokens, point):
    return next((token for token in tokens if token.contains(*point)), None)

def _retry_lookup(img, region, point, japanese):
    # Một lần đọc phóng 2× sát con trỏ khi bản gốc bỏ sót chữ.
    from PIL import Image
    left, top = region["left"], region["top"]
    x, y = point[0] - left, point[1] - top
    x1, y1 = max(0, x - 180), max(0, y - 100)
    x2, y2 = min(img.shape[1], x + 180), min(img.shape[0], y + 100)
    if x2 <= x1 or y2 <= y1:
        return None
    crop = Image.fromarray(img[y1:y2, x1:x2]).resize(
        (2 * (x2 - x1), 2 * (y2 - y1)), Image.Resampling.BICUBIC)
    return _hit_token(_ocr_tokens(np.asarray(crop), left + x1, top + y1, japanese, 2), point)

# ─── DeepL desktop app (UI Automation) ────────────────────────────────────────
_deepl_lock = threading.Lock()   # chỉ 1 request DeepL tại 1 thời điểm (UI dùng chung)
_deepl_input_ctrl = None
_deepl_output_ctrl = None
_deepl_window = None

def _deepl_find_window():
    """
    Tìm cửa sổ DeepL desktop THẬT, tránh match nhầm tab trình duyệt có chữ
    'deepl' trong title (ví dụ tab chat đang bàn về DeepL — đây chính là lỗi
    đã gặp: bot tìm thấy nhầm tab Chrome đang mở chat này và cố gõ text vào
    đó). Điều kiện: Name chứa DEEPL_WINDOW_NAME_HINT (không phân biệt hoa
    thường) VÀ ClassName không phải của trình duyệt.
    """
    import uiautomation as auto
    root = auto.GetRootControl()
    browser_classnames = ("Chrome_WidgetWin", "MozillaWindowClass", "ApplicationFrameWindow")
    candidates = []
    for child in root.GetChildren():
        try:
            name = child.Name or ""
            cls = child.ClassName or ""
        except Exception:
            continue
        if DEEPL_WINDOW_NAME_HINT not in name.lower():
            continue
        is_browser = any(cls.startswith(b) for b in browser_classnames)
        candidates.append((child, is_browser))

    non_browser = [c for c, is_b in candidates if not is_b]
    if non_browser:
        return non_browser[0]
    return None


def _deepl_collect_edit_controls(win, max_depth=15):
    """Duyệt control tree, trả về list các control có ControlType Edit/Document
    (đa số UI text-box hiện đại expose qua 1 trong 2 type này)."""
    import uiautomation as auto
    found = []

    def walk(ctrl, depth):
        if depth > max_depth:
            return
        try:
            ctype = ctrl.ControlTypeName
        except Exception:
            ctype = ""
        if ctype in ("EditControl", "DocumentControl"):
            found.append(ctrl)
        try:
            children = ctrl.GetChildren()
        except Exception:
            children = []
        for c in children:
            walk(c, depth + 1)

    walk(win, 0)
    return found


def _deepl_resolve_controls(force_refresh: bool = False):
    """Lấy (window, input_ctrl, output_ctrl) của app DeepL, cache lại để khỏi
    duyệt control tree mỗi lần dịch. Nếu AutomationId được cấu hình sẵn thì
    tìm đúng theo id; nếu để rỗng thì tự đoán: control Edit lớn nhất là input,
    control Edit lớn thứ 2 (khác cái đầu) là output."""
    global _deepl_window, _deepl_input_ctrl, _deepl_output_ctrl

    if not force_refresh and _deepl_input_ctrl is not None and _deepl_output_ctrl is not None:
        try:
            if _deepl_input_ctrl.Exists(0, 0) and _deepl_output_ctrl.Exists(0, 0):
                return _deepl_window, _deepl_input_ctrl, _deepl_output_ctrl
        except Exception:
            pass

    win = _deepl_find_window()
    if win is None:
        raise RuntimeError(
            f"Không tìm thấy cửa sổ DeepL desktop THẬT (đang tìm tên chứa "
            f"'{DEEPL_WINDOW_NAME_HINT}', loại trừ cửa sổ trình duyệt). "
            "Hãy chắc chắn app DeepL desktop (không phải tab trình duyệt) đang mở."
        )

    input_ctrl = None
    output_ctrl = None

    if DEEPL_INPUT_AUTOMATION_ID:
        import uiautomation as auto
        input_ctrl = win.Control(AutomationId=DEEPL_INPUT_AUTOMATION_ID, searchDepth=15)
        if not input_ctrl.Exists(0, 0):
            input_ctrl = None
    if DEEPL_OUTPUT_AUTOMATION_ID:
        output_ctrl = win.Control(AutomationId=DEEPL_OUTPUT_AUTOMATION_ID, searchDepth=15)
        if not output_ctrl.Exists(0, 0):
            output_ctrl = None

    if input_ctrl is None or output_ctrl is None:
        # auto-detect fallback: control Edit/Document lớn nhất = input,
        # lớn thứ 2 = output (giả định layout 2 cột input/output cạnh nhau)
        edits = _deepl_collect_edit_controls(win)
        if len(edits) < 2:
            raise RuntimeError(
                f"Auto-detect chỉ tìm được {len(edits)} ô text trong cửa sổ DeepL, cần ít nhất 2 "
                "(input + output). Hãy kiểm tra UI Automation và đặt "
                "DEEPL_INPUT_AUTOMATION_ID / DEEPL_OUTPUT_AUTOMATION_ID thủ công."
            )

        def area(c):
            try:
                r = c.BoundingRectangle
                return max(0, r.width()) * max(0, r.height())
            except Exception:
                return 0

        edits_sorted = sorted(edits, key=area, reverse=True)
        if input_ctrl is None:
            input_ctrl = edits_sorted[0]
        if output_ctrl is None:
            # lấy control lớn nhất KHÁC input_ctrl
            for c in edits_sorted:
                if c is not input_ctrl:
                    output_ctrl = c
                    break

    if input_ctrl is None or output_ctrl is None:
        raise RuntimeError("Không xác định được control input/output của DeepL.")

    _deepl_window = win
    _deepl_input_ctrl = input_ctrl
    _deepl_output_ctrl = output_ctrl
    return win, input_ctrl, output_ctrl


def _deepl_get_text(ctrl) -> str:
    """Đọc text hiện tại của 1 control, thử ValuePattern trước rồi tới Name."""
    try:
        vp = ctrl.GetValuePattern()
        if vp:
            val = vp.Value
            if val is not None:
                return val
    except Exception:
        pass
    try:
        return ctrl.Name or ""
    except Exception:
        return ""


def _deepl_set_text(ctrl, text: str):
    """Set text vào control qua ValuePattern.SetValue (không cần focus/click chuột
    thật, ổn định hơn simulate gõ phím). Fallback sang LegacyIAccessiblePattern
    nếu control không hỗ trợ ValuePattern (1 số control DeepL có thể chỉ expose
    qua Legacy)."""
    try:
        vp = ctrl.GetValuePattern()
        if vp:
            vp.SetValue(text)
            return
    except Exception:
        pass
    try:
        lp = ctrl.GetLegacyIAccessiblePattern()
        if lp:
            lp.SetValue(text)
            return
    except Exception:
        pass
    raise RuntimeError("Control input của DeepL không hỗ trợ set text qua UI Automation.")


def translate_deepl_app(text: str) -> str:
    """Dịch EN→VI bằng cách điều khiển app DeepL desktop (Windows) qua UI
    Automation: set text vào ô input, poll ô output tới khi text ổn định
    (giống nhau DEEPL_STABLE_READS lần đọc liên tiếp) thì coi là dịch xong."""
    text = text.strip()
    if not text:
        return ""

    cached = cache_get(text)
    if cached is not None:
        return cached

    with _deepl_lock:
        try:
            _win, input_ctrl, output_ctrl = _deepl_resolve_controls()
        except Exception as e:
            print(f"DeepL app: không lấy được control ({e})")
            return ""

        # đọc baseline output TRƯỚC khi set input mới, để biết khi nó đổi
        try:
            baseline = _deepl_get_text(output_ctrl)
        except Exception:
            baseline = None

        try:
            _deepl_set_text(input_ctrl, text)
        except Exception as e:
            print(f"DeepL app: set text input lỗi, thử tìm lại control... ({e})")
            try:
                _win, input_ctrl, output_ctrl = _deepl_resolve_controls(force_refresh=True)
                _deepl_set_text(input_ctrl, text)
            except Exception as e2:
                print(f"DeepL app: set text input lỗi lần 2, bỏ cuộc ({e2})")
                return ""

        start = time.time()
        last_val = None
        stable_count = 0
        result = ""

        while time.time() - start < DEEPL_TIMEOUT:
            time.sleep(DEEPL_POLL_INTERVAL)
            try:
                cur = _deepl_get_text(output_ctrl)
            except Exception:
                continue

            if not cur or not cur.strip():
                stable_count = 0
                last_val = cur
                continue

            if baseline is not None and cur == baseline:
                # output chưa kịp đổi so với trước khi gõ → chưa chắc đã xong
                stable_count = 0
                last_val = cur
                continue

            if cur == last_val:
                stable_count += 1
            else:
                stable_count = 1
                last_val = cur

            if stable_count >= DEEPL_STABLE_READS:
                result = cur.strip()
                break

        if not result and last_val:
            # hết timeout nhưng có giá trị cuối cùng đọc được → dùng tạm, hơn không có gì
            result = last_val.strip()

        if result:
            cache_set(text, result)
        return result


# ─── DeepL web (Playwright) ────────────────────────────────────────────────────
# QUAN TRỌNG: Playwright sync API KHÔNG thread-safe — mọi thao tác (goto, click,
# fill, inner_text...) phải gọi từ ĐÚNG 1 thread đã khởi tạo nó. Vì translate()
# trong app này được gọi từ nhiều thread dịch khác nhau (mỗi lần hover spawn 1
# thread), không thể gọi Playwright trực tiếp từ các thread đó. Giải pháp: 1
# worker thread riêng sở hữu Playwright + page trong suốt vòng đời app; các
# thread khác gửi yêu cầu dịch qua queue, nhận kết quả qua queue.Queue riêng.

_pw_request_q: "queue.Queue" = queue.Queue()
_pw_worker_lock = threading.Lock()
_pw_init_future: Optional[Future] = None


def _deepl_web_worker(ready: Future):
    """Chạy xuyên suốt trên 1 thread riêng. Sở hữu Playwright + kết nối CDP vào
    Chrome THẬT đang chạy sẵn (mở bằng Start_Hover_Dict.bat) + page. Nhận job
    từ _pw_request_q dạng (text, result_queue), xử lý tuần tự (1 job tại 1
    thời điểm — DeepL web chỉ có 1 page dùng chung)."""
    pw = None
    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        try:
            browser = pw.chromium.connect_over_cdp(DEEPL_WEB_CDP_URL)
        except Exception as e:
            raise RuntimeError(
                f"Không kết nối được Chrome qua CDP ({DEEPL_WEB_CDP_URL}). "
                f"Hãy chạy Start_Hover_Dict.bat trước và để cửa sổ Chrome đó mở. ({e})"
            )

        context = browser.contexts[0] if browser.contexts else browser.new_context()

        # tìm tab deepl.com đã mở sẵn (Start_Hover_Dict.bat tự mở sẵn 1 tab),
        # nếu không có thì mở tab mới
        page = None
        for p in context.pages:
            if "deepl.com" in p.url:
                page = p
                break
        if page is None:
            page = context.new_page()
            page.goto(DEEPL_WEB_URL, wait_until="domcontentloaded", timeout=30000)

        # Wait for the actual output, independent of the page's UI language.
        # Connecting in the background must not pull focus out of a game.
        page.locator('[role="textbox"]').nth(1).wait_for(state="attached", timeout=15000)
    except Exception as e:
        if pw is not None:
            try:
                pw.stop()
            except Exception:
                pass
        ready.set_exception(RuntimeError(str(e)))
        return

    ready.set_result(None)

    pending = None
    while True:
        if pending is None:
            text, result_q = _pw_request_q.get()
        else:
            text, result_q = pending
            pending = None
        if text is None:   # tín hiệu shutdown
            break

        # Drain các job khác đang xếp hàng (nếu có) — chỉ giữ job MỚI NHẤT.
        # Lý do: hover qua nhiều từ liên tiếp nhanh có thể dồn nhiều job vào
        # queue cùng lúc; xử lý tuần tự hết sẽ làm job sau bị timeout dây
        # chuyền dù từng job riêng lẻ không lỗi gì. Job bị bỏ qua nhận kết
        # quả rỗng ngay lập tức (không phải lỗi — chỉ là "đã có job mới hơn").
        skipped = []
        while True:
            try:
                next_text, next_result_q = _pw_request_q.get_nowait()
            except queue.Empty:
                break
            skipped.append((text, result_q))
            text, result_q = next_text, next_result_q

        for _old_text, old_result_q in skipped:
            old_result_q.put(None)   # None = "bị huỷ vì có job mới hơn", không phải lỗi thật
        if text is None:
            break

        waiters = [result_q]

        def is_superseded():
            nonlocal pending
            while True:
                try:
                    newest = _pw_request_q.get_nowait()
                except queue.Empty:
                    break
                if pending is not None and pending[1] is not None:
                    pending[1].put(None)
                pending = newest
            if pending is not None and pending[0] == text:
                # Repeated keypresses for the same word share the active result.
                waiters.append(pending[1])
                pending = None
            return pending is not None

        try:
            result = _deepl_web_translate_on_page(page, text, is_superseded)
        except Exception as e:
            print(f"DeepL web: lỗi khi dịch ({e})")
            result = ""
        if result is not None:
            is_superseded()
        for waiter in waiters:
            waiter.put(result)


def _deepl_web_get_input_box(page):
    box = page.get_by_placeholder("Type or paste text to translate").first
    if box.count() > 0:
        return box
    box = page.locator('[role="textbox"]').first
    return box


def _deepl_web_get_output_box(page):
    boxes = page.locator('[role="textbox"]')
    if boxes.count() >= 2:
        return boxes.nth(1)
    return None


def _deepl_web_dismiss_banner(page):
    """Đóng promotional banner ('You're using the free version...') nếu nó
    đang hiện — banner này có thể che mất ô input và khiến click() bị treo
    chờ phần tử "actionable" (không bị che) mà Playwright mặc định yêu cầu."""
    try:
        close_btn = page.locator(
            'button[aria-label*="Close"], button:has-text("✕")'
        ).first
        if close_btn.count() > 0 and close_btn.is_visible(timeout=500):
            close_btn.click(timeout=1000)
    except Exception:
        pass  # không có banner hoặc không đóng được — bỏ qua, không phải lỗi nghiêm trọng


_DEEPL_WEB_OUTPUT_WATCH = r"""
(element, action) => {
    const readText = () => (
        typeof element.value === 'string' ? element.value :
        (element.innerText ?? element.textContent ?? '')
    ).trim();
    if (action === 'start' || action === 'stop') {
        element.__hoverDictOutputWatch?.observer.disconnect();
        delete element.__hoverDictOutputWatch;
    }
    if (action === 'stop') return;
    if (action === 'start') {
        const state = { baseline: readText(), changed: false };
        state.observer = new MutationObserver(() => {
            if (readText() !== state.baseline) state.changed = true;
        });
        state.observer.observe(element, {
            childList: true, characterData: true, subtree: true
        });
        element.__hoverDictOutputWatch = state;
        return state.baseline;
    }
    return {
        text: readText(),
        changed: element.__hoverDictOutputWatch?.changed ?? false
    };
}
"""


def _deepl_web_translate_on_page(page, text: str, is_superseded=None) -> Optional[str]:
    """Chỉ chạy trên worker Playwright; None nghĩa là có yêu cầu mới hơn."""
    started = time.monotonic()
    if is_superseded is None:
        is_superseded = lambda: not _pw_request_q.empty()
    print(f"DeepL web: đang dịch '{text[:40]}...'" if len(text) > 40 else f"DeepL web: đang dịch '{text}'")
    input_box = _deepl_web_get_input_box(page)
    output_box = _deepl_web_get_output_box(page)
    if output_box is None:
        print("DeepL web: không tìm thấy ô output trên trang.")
        return ""

    # Observe before filling: a brief clear can occur entirely between polls.
    # This also distinguishes a new, identical translation from stale output.
    result = ""
    try:
        baseline = output_box.evaluate(_DEEPL_WEB_OUTPUT_WATCH, "start", timeout=1000)
        if is_superseded():
            return None
        try:
            # fill() replaces the input itself; clicking and Ctrl+A are redundant.
            input_box.fill(text, timeout=1500)
        except Exception:
            _deepl_web_dismiss_banner(page)
            input_box.fill(text, timeout=1500)

        deadline = time.monotonic() + DEEPL_WEB_TIMEOUT
        last_val = None
        stable_count = 0
        # Short word lookups settle quickly; allow more time for phrase streaming.
        required_reads = DEEPL_WEB_STABLE_READS
        if len(text) > 40 or len(text.split()) > 2:
            required_reads = max(required_reads, 6)

        while time.monotonic() < deadline:
            if is_superseded():
                return None
            try:
                snapshot = output_box.evaluate(_DEEPL_WEB_OUTPUT_WATCH, "read", timeout=1000)
            except Exception:
                time.sleep(DEEPL_WEB_POLL_INTERVAL)
                continue
            cur = snapshot["text"].strip()
            fresh = snapshot["changed"] or cur != baseline
            if not cur or not fresh:
                stable_count = 0
                last_val = None
            elif cur == last_val:
                stable_count += 1
            else:
                stable_count = 1
                last_val = cur
            if stable_count >= required_reads:
                result = cur
                break
            time.sleep(DEEPL_WEB_POLL_INTERVAL)
    finally:
        try:
            output_box.evaluate(_DEEPL_WEB_OUTPUT_WATCH, "stop", timeout=250)
        except Exception:
            pass

    elapsed_ms = round((time.monotonic() - started) * 1000)
    print(f"DeepL web: {elapsed_ms} ms — '{result[:60]}'" if result else
          f"DeepL web: {elapsed_ms} ms — chưa có kết quả mới, không dùng bản dịch cũ.")
    return result


def _deepl_web_ensure_worker_started(wait: bool = True):
    """Kết nối nền khi mở app; yêu cầu dịch mới đợi nếu page chưa sẵn sàng."""
    global _pw_init_future
    with _pw_worker_lock:
        ready = _pw_init_future
        if ready is None or (ready.done() and ready.exception() is not None):
            ready = _pw_init_future = Future()
            t = threading.Thread(target=_deepl_web_worker, args=(ready,), daemon=True)
            t.start()

    if wait:
        try:
            ready.result(timeout=35.0)
        except TimeoutError as e:
            raise RuntimeError("Timeout chờ trình duyệt DeepL web khởi động.") from e
    return ready


def translate_deepl_web(text: str, request_id: Optional[int] = None) -> str:
    """Dịch EN→VI qua deepl.com (Playwright). An toàn gọi từ bất kỳ thread nào
    — thực thi thật sự diễn ra trên worker thread riêng sở hữu Playwright."""
    text = text.strip()
    if not text:
        return ""

    cached = cache_get(text)
    if cached is not None:
        return cached

    try:
        _deepl_web_ensure_worker_started()
    except Exception as e:
        print(f"DeepL web: không khởi tạo được trình duyệt ({e})")
        return ""

    result_q: "queue.Queue" = queue.Queue()
    if request_id is None:
        _pw_request_q.put((text, result_q))
    else:
        # Connection/cache waits can reorder caller threads. Validate and enqueue
        # atomically with keypress generation changes so old jobs cannot win.
        with _request_lock:
            if request_id != _request_id:
                return ""
            _pw_request_q.put((text, result_q))
    try:
        result = result_q.get(timeout=DEEPL_WEB_TIMEOUT + 5.0)
    except queue.Empty:
        print("DeepL web: timeout chờ kết quả từ worker thread.")
        return ""

    if result is None:
        # job này bị huỷ vì có job mới hơn (người dùng đã hover sang từ khác) —
        # không phải lỗi, không cần log, chỉ cần trả rỗng cho lần gọi này
        return ""

    if result:
        cache_set(text, result)
    return result


def translate(text: str, request_id: Optional[int] = None) -> str:
    """Dispatcher: chọn backend dịch theo TRANSLATE_BACKEND ("deepl_app" / "deepl_web")."""
    if TRANSLATE_BACKEND == "deepl_app":
        return translate_deepl_app(text)
    return translate_deepl_web(text, request_id=request_id)

# ─── App state ────────────────────────────────────────────────────────────────
class State:
    def __init__(self):
        self.lock   = threading.Lock()
        self.tokens: list[Token] = []
        self.focus_target: Optional[_LookupTarget] = None
        self.focus_signature: Optional[bytes] = None

_state = State()

# Chỉ worker OCR gọi OneOCR; Tk chỉ đọc snapshot token.
_ocr_wakeup = threading.Event()
_exit_requested = threading.Event()
_request_lock = threading.Lock()
_pending_lookup = None
_refresh_requested = False
_request_id = 0
_force_japanese = False

_pointer_lock = threading.Lock()
_pointer_enabled = False
_virtual_pointer = None
_pointer_bounds = None
_pointer_modifier_held = False
_toggle_keys_down = set()

def _lookup_point():
    with _pointer_lock:
        point = _virtual_pointer
    if point is not None:
        return tuple(round(value) for value in point)
    import pyautogui
    return tuple(pyautogui.position())

def _nudge_pointer(dx, dy):
    global _virtual_pointer
    with _pointer_lock:
        if not _pointer_enabled or _pointer_bounds is None or _virtual_pointer is None:
            return
        x, y = _virtual_pointer
        left, top, right, bottom = _pointer_bounds
        _virtual_pointer = (min(max(x + dx, left), right - 1),
                            min(max(y + dy, top), bottom - 1))


def _handle_raw_mouse_packet(data, header_size, primary_size=None):
    """Decode Win32 RAWMOUSE with fixed-width fields on 32/64-bit Python."""
    global _virtual_pointer
    if header_size not in (16, 24) or len(data) < header_size + 24:
        return
    kind, size = struct.unpack_from("<II", data)
    if kind != 0 or size < header_size + 24 or size > len(data):
        return
    flags = struct.unpack_from("<H", data, header_size)[0]
    dx, dy = struct.unpack_from("<ii", data, header_size + 12)
    if not flags & 0x01:  # MOUSE_MOVE_RELATIVE; cursor recentering is irrelevant.
        if dx or dy:
            _nudge_pointer(dx * VIRTUAL_POINTER_SENSITIVITY,
                           dy * VIRTUAL_POINTER_SENSITIVITY)
        return
    with _pointer_lock:
        if not _pointer_enabled or _pointer_bounds is None:
            return
        left, top, right, bottom = _pointer_bounds
        if not flags & 0x02 and primary_size is not None:  # primary vs virtual desktop
            left, top = 0, 0
            right, bottom = primary_size
        _virtual_pointer = (
            left + round(min(max(dx, 0), 65535) * (right - left - 1) / 65535),
            top + round(min(max(dy, 0), 65535) * (bottom - top - 1) / 65535))


class _RawMouseInput:
    """Raw Input on Tk's UI thread, including while a game owns foreground focus."""
    def __init__(self, hwnd):
        import ctypes
        global _pointer_bounds
        self._ctypes = ctypes
        self._hwnd = hwnd
        self._registered = False
        self._requested = False
        self._subclass_id = 0x4844
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._comctl = ctypes.WinDLL("comctl32", use_last_error=True)

        class Device(ctypes.Structure):
            _fields_ = [("usUsagePage", ctypes.c_uint16), ("usUsage", ctypes.c_uint16),
                        ("dwFlags", ctypes.c_uint32), ("hwndTarget", ctypes.c_void_p)]

        self._Device = Device
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_void_p,
            ctypes.c_uint32, ctypes.c_size_t, ctypes.c_ssize_t,
            ctypes.c_size_t, ctypes.c_size_t)
        self._callback = callback_type(self._window_proc)  # keep alive until removal
        self._user32.RegisterRawInputDevices.argtypes = [ctypes.POINTER(Device),
                                                        ctypes.c_uint32, ctypes.c_uint32]
        self._user32.RegisterRawInputDevices.restype = ctypes.c_int32
        self._user32.GetRawInputData.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        self._user32.GetRawInputData.restype = ctypes.c_uint32
        self._user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        self._user32.GetSystemMetrics.restype = ctypes.c_int
        self._comctl.SetWindowSubclass.argtypes = [ctypes.c_void_p, callback_type,
                                                  ctypes.c_size_t, ctypes.c_size_t]
        self._comctl.SetWindowSubclass.restype = ctypes.c_int32
        self._comctl.RemoveWindowSubclass.argtypes = [ctypes.c_void_p, callback_type,
                                                     ctypes.c_size_t]
        self._comctl.RemoveWindowSubclass.restype = ctypes.c_int32
        self._comctl.DefSubclassProc.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                                ctypes.c_size_t, ctypes.c_ssize_t]
        self._comctl.DefSubclassProc.restype = ctypes.c_ssize_t
        self._header_size = 8 + 2 * ctypes.sizeof(ctypes.c_void_p)
        self._buffer = (ctypes.c_uint32 * 64)()  # DWORD-aligned, reused for WM_INPUT
        self._primary_size = (self._user32.GetSystemMetrics(0),
                              self._user32.GetSystemMetrics(1))
        with _pointer_lock:
            if _pointer_bounds is None:
                left, top = (self._user32.GetSystemMetrics(n) for n in (76, 77))
                _pointer_bounds = (left, top, left + self._user32.GetSystemMetrics(78),
                                    top + self._user32.GetSystemMetrics(79))
        if not self._comctl.SetWindowSubclass(hwnd, self._callback, self._subclass_id, 0):
            raise OSError("Không cài được bộ đọc Raw Input cho cửa sổ Tk.")

    def _register(self, enabled):
        ctypes = self._ctypes
        # INPUTSINK receives physical motion in the background; REMOVE needs NULL.
        device = self._Device(1, 2, 0x100 if enabled else 0x01,
                              self._hwnd if enabled else None)
        if self._user32.RegisterRawInputDevices(ctypes.byref(device), 1,
                                                ctypes.sizeof(device)):
            self._registered = enabled
            return True
        print(f"Raw Input: đăng ký chuột lỗi {ctypes.get_last_error()}; dùng các phím di chuyển con trỏ đã đặt.")
        return False

    def sync(self):
        # F8 is captured by pynput; all native hook changes stay on Tk's thread.
        with _pointer_lock:
            enabled = _pointer_enabled
        if enabled != self._requested:
            self._requested = enabled
            if enabled or self._registered:
                self._register(enabled)

    def _window_proc(self, hwnd, msg, wparam, lparam, subclass_id, ref_data):
        try:
            if msg == 0x00FF and self._registered:  # WM_INPUT
                with _pointer_lock:
                    enabled = _pointer_enabled
                if enabled:
                    ctypes = self._ctypes
                    size = ctypes.c_uint32(ctypes.sizeof(self._buffer))
                    copied = self._user32.GetRawInputData(lparam, 0x10000003,
                        self._buffer, ctypes.byref(size), self._header_size)
                    if copied != 0xFFFFFFFF and copied <= ctypes.sizeof(self._buffer):
                        _handle_raw_mouse_packet(ctypes.string_at(self._buffer, copied),
                                                 self._header_size, self._primary_size)
            elif msg == 0x0082:  # WM_NCDESTROY: remove before the HWND disappears.
                self.close()
        except Exception as e:
            if DEBUG_OCR:
                print(f"Raw Input: {e}")
        # DefSubclassProc also performs Windows' required WM_INPUT cleanup.
        return self._comctl.DefSubclassProc(hwnd, msg, wparam, lparam)

    def close(self):
        if self._hwnd is not None:
            if self._registered:
                self._register(False)
            self._comctl.RemoveWindowSubclass(self._hwnd, self._callback, self._subclass_id)
            self._hwnd = None

def _take_requests():
    global _pending_lookup, _refresh_requested
    with _request_lock:
        lookup = _pending_lookup
        refresh = _refresh_requested
        _pending_lookup = None
        _refresh_requested = False
        return lookup, refresh, _force_japanese


def _publish_ocr_state(tokens, raw, area):
    # Publish tokens and local pixels from the same captured frame together.
    with _hover_lock:
        target = _hover.lookup_target
    signature = _word_screen_sig(raw, area, target.token) if target is not None else None
    with _state.lock:
        _state.tokens = tokens
        _state.focus_target = target
        _state.focus_signature = signature


def _same_screen_word(anchor, token):
    if max(abs(anchor.x1 - token.x1), abs(anchor.y1 - token.y1),
           abs(anchor.x2 - token.x2), abs(anchor.y2 - token.y2)) > LOOKUP_BOX_TOLERANCE_PX:
        return False
    return (unicodedata.normalize("NFKC", anchor.word).strip().casefold() ==
            unicodedata.normalize("NFKC", token.word).strip().casefold())


def _lookup_still_visible(target, tokens, point, focus_target, focus_signature):
    if not target.token.contains(*point):
        return False
    signature = focus_signature if focus_target is target else None
    unchanged = (signature is not None and target.signature is not None
                 and signature == target.signature)
    matches = unchanged or any(_same_screen_word(target.token, token) for token in tokens)
    if matches:
        # The original anchor stays fixed; OCR jitter cannot accumulate into drift.
        if signature is not None:
            target.signature = signature
        target.snapshot = tokens
        target.missing_since = None
        target.misses = 0
        return True
    now = time.monotonic()
    if target.missing_since is None:
        target.missing_since = now
    if tokens is not target.snapshot:
        target.snapshot = tokens
        target.misses += 1
    return target.misses < 2 and (now - target.missing_since) * 1000 < LOOKUP_MISS_GRACE_MS


def _set_lookup_result(token, seq, meaning="", snapshot=None, pinned=False, signature=None):
    with _request_lock:
        if seq != _request_id:
            return False
        with _hover_lock:
            _hover.token = token
            _hover.meaning = meaning
            _hover.lookup_target = (_LookupTarget(token, seq, snapshot, signature)
                                    if token is not None and snapshot is not None and not pinned
                                    else None)
            _hover.pinned = pinned
            _hover.pin_origin = None
        return True

def _translate_hit(hit, seq):
    meaning = translate(hit.word, request_id=seq)
    with _request_lock:
        if seq != _request_id:
            return
        with _hover_lock:
            target = _hover.lookup_target
            if target is not None and target.seq == seq:
                _hover.meaning = meaning


def _requeue_lookup(lookup, attempts):
    global _pending_lookup
    if lookup is None or attempts >= max(1, LOOKUP_MAX_OCR_ATTEMPTS):
        return False
    with _request_lock:
        if lookup[1] != _request_id or _pending_lookup is not None:
            return False
        _pending_lookup = lookup
        _ocr_wakeup.set()
        return True


def _ocr_loop():
    global _pointer_bounds
    last_key = None
    region = None
    tokens = []
    lookup_retry_seq = None
    lookup_attempts = 0
    next_capture = time.monotonic()
    while not _exit_requested.is_set():
        _ocr_wakeup.wait(max(0, next_capture - time.monotonic()))
        _ocr_wakeup.clear()
        if _exit_requested.is_set():
            break
        next_capture = time.monotonic() + 1.0 / CAPTURE_FPS
        lookup, refresh, japanese = _take_requests()
        if lookup is not None:
            if lookup[1] != lookup_retry_seq:
                lookup_retry_seq = lookup[1]
                lookup_attempts = 0
            lookup_attempts += 1
        try:
            point = lookup[0] if lookup is not None else _lookup_point()
            sct = _get_sct()
            monitors = sct.monitors
            desktop = monitors[0]
            with _pointer_lock:
                _pointer_bounds = (desktop["left"], desktop["top"],
                                   desktop["left"] + desktop["width"],
                                   desktop["top"] + desktop["height"])
            region = _capture_region(monitors, point, region)
            area = desktop if refresh else region
            raw = sct.grab(area)
        except Exception as e:
            print(f"Không capture được màn hình: {e}")
            if _requeue_lookup(lookup, lookup_attempts):
                last_key = None
            _exit_requested.wait(0.25)
            continue

        key = _capture_key(raw, area, region, japanese)
        if refresh or key != last_key:
            if DEBUG_OCR:
                print(f"[OCR] {area['width']}x{area['height']}")
            img = _rgb(raw)
            try:
                tokens = _ocr_tokens(img, area["left"], area["top"], japanese)
            except Exception as e:
                print(f"OCR lỗi: {e}")
                if _requeue_lookup(lookup, lookup_attempts):
                    last_key = None
                _exit_requested.wait(0.25)
                continue
            last_key = key
            if refresh:
                hit_status = "có từ dưới con trỏ" if _hit_token(tokens, point) else "chưa có từ dưới con trỏ"
                print(f"[OCR] Quét toàn màn hình: {len(tokens)} token, {hit_status}.")

        _publish_ocr_state(tokens, raw, area)
        if lookup is not None:
            point, seq = lookup
            with _request_lock:
                if seq != _request_id:
                    continue
            hit = _hit_token(tokens, point)
            if hit is None:
                try:
                    hit = _retry_lookup(_rgb(raw), area, point, japanese)
                except Exception as e:
                    print(f"OCR phóng to lỗi: {e}")
            if hit is None:
                if _requeue_lookup(lookup, lookup_attempts):
                    # A missed read must be retried even on identical pixels.
                    last_key = None
                    continue
                print(f"[Tra từ] Chưa đọc được chữ tại điểm bấm sau {lookup_attempts} lần thử.")
            signature = _word_screen_sig(raw, area, hit) if hit is not None else None
            if _set_lookup_result(hit, seq, snapshot=tokens, signature=signature) and hit is not None:
                _publish_ocr_state(tokens, raw, area)
                threading.Thread(target=_translate_hit, args=(hit, seq), daemon=True).start()

def _trigger_send_translate():
    global _request_id, _pending_lookup
    try:
        point = _lookup_point()
    except Exception as e:
        print(f"Không lấy được vị trí chuột: {e}")
        return
    with _request_lock:
        _request_id += 1
        _pending_lookup = (point, _request_id)
        with _hover_lock:
            _hover.token = None
            _hover.meaning = ""
            _hover.lookup_target = None
            _hover.pinned = False
            _hover.pin_origin = None
    _ocr_wakeup.set()

def _trigger_ocr_refresh():
    global _refresh_requested
    with _request_lock:
        _refresh_requested = True
    _ocr_wakeup.set()

# ─── Key tracking ───────────────────────────────────────────────────────────
# '1' giữ + rê = gom cụm nhiều từ, thả ra dịch cả cụm 1 lần.
# '2' bấm = dịch ngay từ/token đang hover tại thời điểm bấm (single-shot).
_ctrl_held = False
_ctrl_lock = threading.Lock()

def _matches_combo_key(key) -> bool:
    return event_key_name(key) == KEY_BINDINGS["collect"]

def _matches_single_key(key) -> bool:
    return event_key_name(key) == KEY_BINDINGS["lookup"]

def _reset_keyboard_state():
    global _ctrl_held, _pointer_modifier_held
    with _ctrl_lock:
        _ctrl_held = False
        _ctrl_buffer.clear()
    _held_modifiers.clear()
    _toggle_keys_down.clear()
    _pointer_modifier_held = False

def _on_key_press(key):
    global _ctrl_held, _pointer_enabled, _virtual_pointer, _force_japanese, _pointer_modifier_held
    global _request_id, _pending_lookup
    if _editing_keys.is_set():
        return
    name = event_key_name(key)
    if name is None:
        return
    if name in MODIFIER_CHOICES:
        _held_modifiers.add(name)
        if name == KEY_BINDINGS["pointer_modifier"]:
            _pointer_modifier_held = True
        return
    if _pointer_modifier_held and _pointer_enabled:
        movement = {KEY_BINDINGS["pointer_left"]: (-12, 0),
                    KEY_BINDINGS["pointer_right"]: (12, 0),
                    KEY_BINDINGS["pointer_up"]: (0, -12),
                    KEY_BINDINGS["pointer_down"]: (0, 12)}
        if name in movement:
            _nudge_pointer(*movement[name])
            return
    if _held_modifiers:
        return  # Leave Ctrl/Alt/Shift/Win shortcuts to the foreground application.
    if _matches_combo_key(key):
        started = False
        with _ctrl_lock:
            if not _ctrl_held:
                _ctrl_held = True
                _ctrl_buffer.clear()
                started = True
        if started:
            with _request_lock:
                _request_id += 1
                _pending_lookup = None
                with _hover_lock:
                    _hover.token = None
                    _hover.meaning = ""
                    _hover.lookup_target = None
                    _hover.pinned = False
                    _hover.pin_origin = None
    elif _matches_single_key(key):
        _trigger_send_translate()
    elif name == KEY_BINDINGS["refresh"]:
        _trigger_ocr_refresh()
    elif name == KEY_BINDINGS["exit"]:
        _exit_requested.set()
        _ocr_wakeup.set()
    elif name in (KEY_BINDINGS["toggle_pointer"], KEY_BINDINGS["toggle_japanese"]):
        if name in _toggle_keys_down:
            return
        _toggle_keys_down.add(name)
        if name == KEY_BINDINGS["toggle_pointer"]:
            try:
                point = _lookup_point()
            except Exception as e:
                print(f"Không lấy được vị trí ban đầu cho chuột ảo: {e}")
                return
            with _pointer_lock:
                _pointer_enabled = not _pointer_enabled
                _virtual_pointer = point if _pointer_enabled else None
            _ocr_wakeup.set()
        else:
            with _request_lock:
                _force_japanese = not _force_japanese
            print("Tách từ Nhật:", "ép bật" if _force_japanese else "tự động")
            _ocr_wakeup.set()

def _on_key_release(key):
    global _ctrl_held, _request_id, _pointer_modifier_held
    name = event_key_name(key)
    _held_modifiers.discard(name)
    _toggle_keys_down.discard(name)
    if name == KEY_BINDINGS["pointer_modifier"]:
        _pointer_modifier_held = False
    if _matches_combo_key(key):
        with _ctrl_lock:
            was_held = _ctrl_held
            _ctrl_held = False
            selected = list(_ctrl_buffer.values())
            _ctrl_buffer.clear()
        if was_held and selected:
            with _request_lock:
                _request_id += 1
                seq = _request_id
            threading.Thread(target=_flush_ctrl_buffer, args=(selected, seq), daemon=True).start()

# ─── Hover + drag buffer ───────────────────────────────────────────────────────
class _HoverState:
    token: Optional[Token] = None
    meaning: str = ""
    lookup_target: Optional[_LookupTarget] = None
    pinned: bool = False
    pin_origin: Optional[tuple[int, int]] = None

_hover = _HoverState()
_hover_lock = threading.Lock()
_ctrl_buffer: dict[tuple[str, int, int, int, int], Token] = {}

def _flush_ctrl_buffer(toks: list[Token], seq: int):
    toks.sort(key=lambda t: (round(t.y1 / 20), t.x1))
    text = " ".join(t.word for t in toks)
    token = Token(text, min(t.x1 for t in toks), min(t.y1 for t in toks),
                  max(t.x2 for t in toks), max(t.y2 for t in toks))
    meaning = translate(text, request_id=seq)
    _set_lookup_result(token, seq, meaning, pinned=bool(meaning))

# ─── Tkinter UI ───────────────────────────────────────────────────────────────
class KeyboardSettings(tk.Frame):
    """The key editor lives in the same application, with no extra launcher."""
    def __init__(self, parent, config_path=CONFIG_PATH):
        from tkinter import ttk
        super().__init__(parent)
        self.config_path = Path(config_path)
        self.fields = {action: tk.StringVar(self, value=key) for action, key in KEY_BINDINGS.items()}
        self.status = tk.StringVar(self, value="Đổi phím rồi bấm Lưu / Choose keys, then Save.")
        ttk.Label(self, text="Hover Dict — Phím điều khiển / Controls", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text="Thu nhỏ cửa sổ hoặc chuyển về game để dùng phím.\n"
                  "Minimise this window or return to your game to use the hotkeys.",
                  wraplength=680).pack(anchor="w", pady=(8, 12))
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        for title, actions in (
            ("Thao tác / Actions", [a for a in DEFAULT_BINDINGS if not a.startswith("pointer_")]),
            ("Di chuyển con trỏ / Pointer", [a for a in DEFAULT_BINDINGS if a.startswith("pointer_")]),
        ):
            page = ttk.Frame(tabs, padding=12)
            tabs.add(page, text=title)
            page.columnconfigure(0, weight=1)
            for row, action in enumerate(actions):
                ttk.Label(page, text=ACTION_LABELS[action], wraplength=475).grid(
                    row=row, column=0, sticky="w", padx=(0, 12), pady=7)
                choices = MODIFIER_CHOICES if action == "pointer_modifier" else KEY_CHOICES
                ttk.Combobox(page, values=choices, textvariable=self.fields[action], width=15).grid(
                    row=row, column=1, sticky="e", pady=7)
        ttk.Label(self, text="Con trỏ ảo: dùng cho một số game/VN ẩn hoặc ghim chuột.\n"
                  "Virtual pointer: for some games/VNs that hide or lock the cursor.",
                  wraplength=680).pack(anchor="w", pady=(10, 6))
        ttk.Label(self, textvariable=self.status, wraplength=680).pack(anchor="w", pady=(0, 8))
        buttons = ttk.Frame(self)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Mặc định / Defaults", command=self.restore_defaults).pack(side="left")
        ttk.Button(buttons, text="Lưu / Save", command=self.save_values).pack(side="left", padx=8)
        ttk.Button(buttons, text="Thu nhỏ / Minimise", command=parent.iconify).pack(side="right")

    def save_values(self):
        global KEY_BINDINGS
        from tkinter import messagebox
        try:
            bindings = save_bindings(self.config_path, {a: v.get() for a, v in self.fields.items()})
        except (OSError, ValueError) as error:
            self.status.set("Chưa lưu / Not saved.")
            messagebox.showerror("Không lưu được / Cannot save", str(error), parent=self)
            return
        KEY_BINDINGS = bindings
        _reset_keyboard_state()
        for action, key in bindings.items():
            self.fields[action].set(key)
        self.status.set("Đã lưu và áp dụng. Thu nhỏ để dùng / Saved and applied. Minimise to use.")

    def restore_defaults(self):
        for action, key in DEFAULT_BINDINGS.items():
            self.fields[action].set(key)
        self.status.set("Đã điền mặc định; bấm Lưu để áp dụng / Defaults filled; Save to apply.")


def _bind_settings_focus(root):
    # Keyboard hooks run on another thread; only this UI callback touches Tk.
    def update():
        try:
            focused = root.focus_displayof()
            if focused is None or focused.winfo_toplevel() is not root:
                _editing_keys.clear()
        except tk.TclError:
            _editing_keys.clear()

    def focus_in(event):
        _editing_keys.set()
        _reset_keyboard_state()

    def focus_out(event):
        root.after_idle(update)
    _editing_keys.set()
    root.bind("<FocusIn>", focus_in, add="+")
    root.bind("<FocusOut>", focus_out, add="+")
    root.after_idle(update)  # Windows may leave the new window in the background.


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hover Dict v5.3.1 Simple — Scroll + Nhật")
        self.geometry("750x540")
        self.minsize(700, 520)
        KeyboardSettings(self).pack(fill="both", expand=True, padx=16, pady=16)
        _bind_settings_focus(self)
        self.protocol("WM_DELETE_WINDOW", _exit_requested.set)

        self._build_highlight()
        self._build_popup()
        self._build_pointer()
        self._configure_overlays()
        self._raw_mouse_input = None
        try:
            self._raw_mouse_input = _RawMouseInput(self.winfo_id())
        except Exception as e:
            print(f"Raw Input chưa sẵn sàng ({e}); vẫn dùng được các phím di chuyển con trỏ đã đặt.")
        self._popup_visible = False
        self._highlight_visible = False
        self._pointer_drawn_at = None
        self._last_hit = None
        self._rendered = (None, "")
        self.after(0, self._ui_tick)

    def destroy(self):
        if self._raw_mouse_input is not None:
            self._raw_mouse_input.close()
        super().destroy()

    def _build_highlight(self):
        """Cửa sổ viền mỏng trong suốt, vẽ quanh token đang hover."""
        self._hl = tk.Toplevel(self)
        self._hl.overrideredirect(True)
        self._hl.attributes("-topmost", True)
        self._hl.attributes("-transparentcolor", "black")
        self._hl.configure(bg="black")
        self._hl.withdraw()

        self._hl_canvas = tk.Canvas(self._hl, bg="black", highlightthickness=0)
        self._hl_canvas.pack(fill="both", expand=True)

    def _build_popup(self):
        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.attributes("-alpha", 0.92)
        self._popup.configure(bg="#1a1a2e")
        self._popup.withdraw()

        frame = tk.Frame(self._popup, bg="#1a1a2e", padx=10)
        frame.pack(fill="both", expand=True)

        self._lbl_text = tk.Label(frame, text="", font=("Segoe UI", 13, "bold"),
                                  fg="#c9a0ff", bg="#1a1a2e", wraplength=420, justify="left")
        self._lbl_text.pack(fill="x", pady=(8, 2))

        self._lbl_meaning = tk.Label(frame, text="", font=("Segoe UI", 12),
                                     fg="#ffffff", bg="#1a1a2e", wraplength=420, justify="left")
        self._lbl_meaning.pack(fill="x", pady=(0, 8))

    def _build_pointer(self):
        self._pointer = tk.Toplevel(self)
        self._pointer.overrideredirect(True)
        self._pointer.attributes("-topmost", True)
        self._pointer.attributes("-transparentcolor", "black")
        self._pointer.geometry("29x29")
        canvas = tk.Canvas(self._pointer, width=29, height=29, bg="black",
                           highlightthickness=0)
        canvas.pack()
        for x1, y1, x2, y2 in ((14, 2, 14, 9), (14, 19, 14, 26),
                               (2, 14, 9, 14), (19, 14, 26, 14)):
            canvas.create_line(x1, y1, x2, y2, fill="#ffcc00", width=3)
        self._pointer.withdraw()

    def _configure_overlays(self):
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetWindowLongW.restype = ctypes.c_long
        user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
        user32.SetWindowLongW.restype = ctypes.c_long
        user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user32.SetWindowPos.restype = wintypes.BOOL
        self._user32 = user32
        self._overlay_handles = {}

    def _overlay_handle(self, win):
        # wm frame returns the native wrapper of a mapped Tk toplevel.
        hwnd = int(win.wm_frame(), 0)
        if hwnd and self._overlay_handles.get(win) != hwnd:
            style = self._user32.GetWindowLongW(hwnd, -20)
            # Layered + transparent + no-activate. Mouse clicks go through.
            self._user32.SetWindowLongW(hwnd, -20, style | 0x00000020 | 0x08000000)
            # FRAMECHANGED | NOACTIVATE | NOZORDER | NOMOVE | NOSIZE
            self._user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0037)
            if not self._user32.SetWindowDisplayAffinity(hwnd, 0x11) and DEBUG_OCR:
                print("[OCR] Windows không exclude được overlay khỏi capture")
            self._overlay_handles[win] = hwnd
        return hwnd

    def _place_overlay(self, win, x, y, width=0, height=0, show=False):
        # Set geometry before mapping so Tk lays out the canvas at the word box.
        # "+-N" is an absolute negative coordinate in Tk's geometry parser.
        size = f"{width}x{height}" if width else ""
        win.geometry(f"{size}+{x}+{y}")
        if show:
            win.deiconify()
            win.update_idletasks()
            self._overlay_handle(win)

    def _update_pointer(self, point):
        with _pointer_lock:
            enabled = _pointer_enabled
        if enabled and point != self._pointer_drawn_at:
            first = self._pointer_drawn_at is None
            self._place_overlay(self._pointer, point[0] - 14, point[1] - 14, show=first)
            self._pointer_drawn_at = point
        elif not enabled and self._pointer_drawn_at is not None:
            self._pointer.withdraw()
            self._pointer_drawn_at = None

    def _ui_tick(self):
        if _exit_requested.is_set():
            self.destroy()
            return
        if self._raw_mouse_input is not None:
            self._raw_mouse_input.sync()
        try:
            point = _lookup_point()
        except Exception:
            self.after(HOVER_INTERVAL_MS, self._ui_tick)
            return
        self._update_pointer(point)
        with _state.lock:
            tokens = _state.tokens
            focus_target = _state.focus_target
            focus_signature = _state.focus_signature
        hit = _hit_token(tokens, point)
        with _ctrl_lock:
            if _ctrl_held and hit is not None:
                _ctrl_buffer[(hit.word, hit.x1, hit.y1, hit.x2, hit.y2)] = hit
        with _hover_lock:
            target = _hover.lookup_target
            if _hover.pinned:
                if _hover.pin_origin is None:
                    # Anchor at first display, after any translation/network wait.
                    _hover.pin_origin = point
                else:
                    dx = point[0] - _hover.pin_origin[0]
                    dy = point[1] - _hover.pin_origin[1]
                    if dx * dx + dy * dy >= POPUP_DISMISS_DISTANCE_PX ** 2:
                        _hover.pinned = False
                        _hover.pin_origin = None
                        _hover.lookup_target = None
                        _hover.token = hit
                        _hover.meaning = ""
            elif target is not None:
                if not _lookup_still_visible(target, tokens, point, focus_target, focus_signature):
                    _hover.lookup_target = None
                    _hover.token = hit
                    _hover.meaning = ""
            elif _hover.token != hit:
                _hover.token = hit
                _hover.meaning = ""
            self._last_hit = hit
            rendered = (_hover.token, _hover.meaning)
        if rendered != self._rendered:
            self.update_popup(*rendered)
            self._rendered = rendered
        self.after(HOVER_INTERVAL_MS, self._ui_tick)

    def update_popup(self, token, meaning):
        if token is None:
            self._popup.withdraw()
            self._popup_visible = False
            self._hl.withdraw()
            self._highlight_visible = False
            return

        # ── vẽ khung hitbox quanh token ──
        pad = 3
        hx = token.x1 - pad
        hy = token.y1 - pad
        hw = (token.x2 - token.x1) + pad * 2
        hh = (token.y2 - token.y1) + pad * 2

        self._hl_canvas.delete("all")
        x1, y1, x2, y2 = 1, 1, hw - 1, hh - 1
        radius = min(6, (x2 - x1) / 2, (y2 - y1) / 2)
        self._hl_canvas.create_polygon(
            x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
            smooth=True, splinesteps=12, fill="", outline="#ffcc00", width=2
        )
        self._place_overlay(self._hl, hx, hy, hw, hh, show=not self._highlight_visible)
        self._highlight_visible = True

        # ── popup nghĩa (chỉ hiện khi đã có nghĩa, tránh popup rỗng nhấp nháy lúc đang gom Ctrl) ──
        if not meaning:
            self._popup.withdraw()
            self._popup_visible = False
            return

        self._lbl_text.configure(text=token.word)
        self._lbl_meaning.configure(text=meaning)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self._popup.update_idletasks()
        pw = self._popup.winfo_reqwidth()
        ph = self._popup.winfo_reqheight()

        px = min(token.x1, sw - pw - 10)
        py = token.y2 + 8
        if py + ph > sh:
            py = token.y1 - ph - 8

        self._place_overlay(self._popup, px, py, pw, ph, show=not self._popup_visible)
        self._popup_visible = True

# ─── Dependency check (called by Check_And_Install.bat) ────────────────────────
DEPENDENCIES = {
    'oneocr': 'oneocr', 'mss': 'mss', 'pynput': 'pynput', 'Pillow': 'PIL',
    'numpy': 'numpy', 'PyAutoGUI': 'pyautogui', 'playwright': 'playwright.sync_api',
    'SudachiPy': 'sudachipy', 'sudachidict_core': 'sudachidict_core',
}
ENGINE_FILES = ('oneocr.dll', 'oneocr.onemodel', 'onnxruntime.dll')


def _missing_packages(packages=DEPENDENCIES, report_errors=False):
    missing = []
    for package, module in packages.items():
        result = subprocess.run([sys.executable, '-c', f'import {module}'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            missing.append(package)
            if report_errors:
                print(f'[IMPORT ERROR] {package}:')
                print(result.stderr.decode(errors='replace').strip())
    return missing


def _install_python_packages(packages=DEPENDENCIES):
    missing = _missing_packages(packages)
    if not missing:
        print('[OK] Python packages are already installed.')
        return
    print('[INSTALL] Missing Python packages: ' + ', '.join(missing), flush=True)
    if subprocess.run([sys.executable, '-m', 'pip', '--version'], stdout=subprocess.DEVNULL).returncode:
        subprocess.run([sys.executable, '-m', 'ensurepip', '--upgrade'], check=True)
    command = [sys.executable, '-m', 'pip', 'install']
    if sys.prefix == sys.base_prefix:
        command.append('--user')
    subprocess.run(command + missing, check=True)


def _chrome_path():
    for variable, suffix in (
        ('ProgramFiles', 'Google/Chrome/Application/chrome.exe'),
        ('ProgramFiles(x86)', 'Google/Chrome/Application/chrome.exe'),
        ('LocalAppData', 'Google/Chrome/Application/chrome.exe'),
    ):
        base = os.environ.get(variable)
        if base and (Path(base)/suffix).is_file():
            return str(Path(base)/suffix)
    return shutil.which('chrome.exe')


def _winget_install(identifier, source='winget'):
    winget = shutil.which('winget.exe')
    if not winget:
        print('[MISSING] WinGet / App Installer is unavailable. See README for manual setup.')
        return False
    print(f'[INSTALL] {identifier}', flush=True)
    result = subprocess.run([winget, 'install', '--id', identifier, '--exact', '--source', source,
                             '--silent', '--accept-package-agreements', '--accept-source-agreements'])
    return result.returncode == 0


def _copy_engine_files(source, destination):
    source, destination = Path(source), Path(destination)
    if not all((source/name).is_file() and (source/name).stat().st_size for name in ENGINE_FILES):
        return False
    destination.mkdir(parents=True, exist_ok=True)
    # Stage a complete matching set before changing any destination files.
    with tempfile.TemporaryDirectory(dir=destination, prefix='.engine-') as staging:
        for name in ENGINE_FILES:
            shutil.copyfile(source/name, Path(staging)/name)
        for name in ENGINE_FILES:
            os.replace(Path(staging)/name, destination/name)
    return True


def _snipping_tool_locations():
    command = ("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
               "Get-AppxPackage -Name Microsoft.ScreenSketch | "
               "Sort-Object Version -Descending | ForEach-Object { $_.InstallLocation }")
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()] if result.returncode == 0 else []


def _ensure_engine_files():
    destination = Path.home()/'.config/oneocr'
    if all((destination/name).is_file() and (destination/name).stat().st_size for name in ENGINE_FILES):
        print('[OK] OneOCR engine files already exist.')
        return True
    for attempt in range(2):
        locations = [Path(__file__).parent]
        for location in _snipping_tool_locations():
            locations.extend((location/'SnippingTool', location))
        for source in locations:
            try:
                if _copy_engine_files(source, destination):
                    print('[OK] OneOCR engine files copied from: ' + str(source))
                    return True
            except OSError as error:
                print('[CHECK] Cannot copy OneOCR files: ' + str(error))
        if attempt == 0:
            print('[CHECK] Trying to install/update Snipping Tool from Microsoft Store.')
            _winget_install('9MZ95KL8MR0L', 'msstore')
    print('[MISSING] OneOCR needs oneocr.dll, oneocr.onemodel and onnxruntime.dll.')
    print('Place a matching x64 set in ' + str(destination))
    print('Instructions: https://github.com/AuroraWright/oneocr')
    return False


def _setup_environment():
    if os.name != 'nt' or sys.version_info[:2] != (3, 12) or struct.calcsize('P') != 8:
        print('[ERROR] Use Windows and 64-bit Python 3.12. Run Check_And_Install.bat.')
        return 1
    print('[CHECK] Python: ' + sys.executable, flush=True)
    packages = dict(DEPENDENCIES)
    if TRANSLATE_BACKEND == 'deepl_app':
        packages['uiautomation'] = 'uiautomation'
    try:
        _install_python_packages(packages)
        missing = _missing_packages(packages, report_errors=True)
        if missing:
            print('[ERROR] Imports still fail: ' + ', '.join(missing))
            return 1
        chrome_ok = True
        if TRANSLATE_BACKEND == 'deepl_web':
            if not _chrome_path():
                _winget_install('Google.Chrome')
            chrome_ok = bool(_chrome_path())
            print('[OK] Chrome found.' if chrome_ok else '[MISSING] Install Chrome: https://www.google.com/chrome/')
        engine_ok = _ensure_engine_files()
        if engine_ok:
            print('[CHECK] Loading OneOCR engine...', flush=True)
            result = subprocess.run([sys.executable, '-c', 'import oneocr; oneocr.OcrEngine()'])
            engine_ok = result.returncode == 0
            if not engine_ok:
                print('[ERROR] OneOCR files exist but the engine cannot load. Read the error above.')
        if not (chrome_ok and engine_ok):
            print('[NOT READY] Resolve the missing item above, then run this check again.')
            return 1
    except (OSError, subprocess.SubprocessError) as error:
        print('[ERROR] Setup did not finish: ' + str(error))
        return 1
    print('[READY] Open Start_Hover_Dict.bat. Check DeepL verification and languages manually.')
    return 0


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    global KEY_BINDINGS, mss, np, keyboard
    import argparse
    parser = argparse.ArgumentParser(description='Hover Dict — one-file application')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--setup', action='store_true', help='check/install missing dependencies')
    mode.add_argument('--settings', action='store_true', help='edit keys without starting OCR')
    args = parser.parse_args()
    if args.setup:
        return _setup_environment()
    if os.name != 'nt':
        print('Hover Dict requires Windows. Read README.vi.md / README.md.')
        return 1
    try:
        KEY_BINDINGS = load_bindings()
    except (OSError, ValueError) as error:
        print(f'Cấu hình phím bị lỗi ({error}); đang dùng phím mặc định.')
    if args.settings:
        root = tk.Tk()
        root.title('Hover Dict — Phím / Keybindings')
        root.geometry('750x540')
        root.minsize(700, 520)
        KeyboardSettings(root).pack(fill='both', expand=True, padx=16, pady=16)
        root.mainloop()
        return 0
    try:
        mss = importlib.import_module('mss')
        np = importlib.import_module('numpy')
        keyboard = importlib.import_module('pynput.keyboard')
    except (ImportError, OSError) as error:
        print(f'Thiếu/lỗi thư viện ({error}). Chạy Check_And_Install.bat trước.')
        return 1
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError:
        ctypes.windll.user32.SetProcessDPIAware()

    print("─" * 60)
    print(f"  Hover Dict v5.3.1 Simple  —  OneOCR + backend dịch: {TRANSLATE_BACKEND}")
    print("─" * 60)

    try:
        import oneocr  # noqa
        print("✅ oneocr import OK")
    except ImportError:
        print("❌ Thiếu oneocr — chạy: py -3.12 -m pip install oneocr")
        return

    try:
        _get_ocr()
    except Exception as e:
        print(f"❌ Không load được OneOCR engine ({e})")
        print("   Kiểm tra 3 file oneocr.dll / oneocr.onemodel / onnxruntime.dll")
        print("   đã đặt đúng C:/Users/<user>/.config/oneocr/ chưa.")
        return

    try:
        import pyautogui  # noqa
    except ImportError:
        print("❌ Thiếu pyautogui — chạy: py -3.12 -m pip install pyautogui")
        return

    # Start the UI first; browser initialization runs independently of OCR.
    print(f"📦 Cache DB: {DB_PATH}")

    app = App()
    if TRANSLATE_BACKEND == "deepl_web":
        _deepl_web_ensure_worker_started(wait=False)
    threading.Thread(target=_ocr_loop, daemon=True).start()
    listener = keyboard.Listener(on_press=_on_key_press, on_release=_on_key_release)
    listener.daemon = True
    listener.start()

    print("🚀 Đang chạy.")
    print("   Rê chuột vào 1 từ  → chỉ hiện khung, KHÔNG tự dịch.")
    print(f"   {display_key(KEY_BINDINGS['lookup'])} → kiểm tra ảnh mới rồi dịch từ dưới con trỏ.")
    print("   Chữ vẫn ở chỗ cũ → giữ nghĩa; chữ đổi/di chuyển → tự ẩn.")
    print(f"   {display_key(KEY_BINDINGS['refresh'])} → ép OCR màn hình mà không dịch.")
    print(f"   Giữ {display_key(KEY_BINDINGS['collect'])} + rê → gom cụm; thả để dịch.")
    print(f"   Bản dịch cả cụm ẩn khi rê xa {POPUP_DISMISS_DISTANCE_PX} px hoặc tra tiếp.")
    print(f"   {display_key(KEY_BINDINGS['toggle_pointer'])} → con trỏ ảo cho game/VN ẩn hoặc ghim chuột.")
    print(f"   {display_key(KEY_BINDINGS['exit'])} → thoát. Đổi phím trong cửa sổ Hover Dict.\n")

    try:
        app.mainloop()
    finally:
        _exit_requested.set()
        _ocr_wakeup.set()
        listener.stop()
        if app._raw_mouse_input is not None:
            app._raw_mouse_input.close()

if __name__ == "__main__":
    raise SystemExit(main())
