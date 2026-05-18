# ocr.py
import os
import re
import time
import cv2
import numpy as np
import pyautogui
import pytesseract

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

DEBUG_OCR = False
DEBUG_DIR = "ocr_debug"
if DEBUG_OCR:
    os.makedirs(DEBUG_DIR, exist_ok=True)


def _dump(name: str, img):
    if not DEBUG_OCR:
        return
    ts = int(time.time() * 1000)
    cv2.imwrite(f"{DEBUG_DIR}/{ts}_{name}.png", img)


def _to_float(text: str, prev_balance=None):
    cleaned = re.sub(r"[^0-9,\.]", "", text).replace(",", ".").strip()
    if not cleaned:
        return None

    if "." in cleaned:
        parts = cleaned.split(".")
        int_part = "".join(parts[:-1]) if len(parts) > 1 else parts[0]
        dec_part = parts[-1]
        normalized = f"{int_part}.{dec_part}" if int_part else f"0.{dec_part}"
        try:
            return float(normalized)
        except ValueError:
            return None

    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return None

    # Если разделитель потерян, пробуем несколько масштабов и выбираем ближайший к prev_balance
    candidates = []
    n = int(digits)
    for div in (1, 10, 100, 1000):
        candidates.append(n / div)

    if prev_balance is not None:
        return min(candidates, key=lambda x: abs(x - prev_balance))

    # Без предыдущего значения меньше шансов исказить число: трактуем как целое
    return float(n)


def _fix_scale(value: float, prev_balance):
    if prev_balance is None:
        return round(value, 2)

    candidates = [value, value / 10, value / 100, value / 1000, value * 10, value * 100]
    best = min(candidates, key=lambda x: abs(x - prev_balance))

    if prev_balance > 0 and abs(best - prev_balance) > prev_balance * 0.40:
        return None

    return round(best, 2)


def _ocr_variant(gray_img, variant_name: str, prev_balance=None):
    img = gray_img.copy()

    if variant_name == "normal":
        pass
    elif variant_name == "inv":
        img = 255 - img
    elif variant_name == "otsu":
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        return None, ""

    img = cv2.resize(img, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    img = cv2.GaussianBlur(img, (3, 3), 0)

    if variant_name in ("normal", "inv"):
        img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )

    kernel = np.ones((2, 2), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=1)

    _dump(f"proc_{variant_name}", img)

    text = pytesseract.image_to_string(
        img,
        config="--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789., "
    )
    value = _to_float(text, prev_balance=prev_balance)
    return value, text.strip()


def read_balance(region, prev_balance=None):
    shot = pyautogui.screenshot(region=region)
    bgr = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    _dump("raw", bgr)
    _dump("gray", gray)

    values = []
    raws = []

    for variant in ("normal", "inv", "otsu"):
        value, raw = _ocr_variant(gray, variant, prev_balance=prev_balance)
        raws.append(f"{variant}:{raw}")
        if value is not None:
            values.append(value)

    if not values:
        print(f"[OCR ERROR] не удалось распознать баланс: {raws}")
        return None

    values.sort()
    raw_value = values[len(values) // 2]

    fixed = _fix_scale(raw_value, prev_balance)
    if fixed is None:
        print(f"[OCR WARN] raw={raw_value}, prev={prev_balance}, texts={raws}")
        return None

    return fixed


def _ocr_text_variant(gray_img, variant_name: str):
    img = gray_img.copy()

    if variant_name == "normal":
        pass
    elif variant_name == "inv":
        img = 255 - img
    elif variant_name == "otsu":
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        return ""

    img = cv2.resize(img, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    img = cv2.GaussianBlur(img, (3, 3), 0)

    if variant_name in ("normal", "inv"):
        img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )

    kernel = np.ones((2, 2), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=1)

    _dump(f"proc_text_{variant_name}", img)

    text = pytesseract.image_to_string(
        img,
        config="--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ/ "
    )
    return text.strip()

VALID_PAIRS = [
    "AUD/CAD", "AUD/CHF", "AUD/JPY", "AUD/USD",
    "CAD/CHF", "CAD/JPY",
    "CHF/JPY",
    "EUR/AUD", "EUR/CAD", "EUR/CHF", "EUR/GBP", "EUR/JPY", "EUR/USD",
    "GBP/AUD", "GBP/CAD", "GBP/CHF", "GBP/JPY", "GBP/USD",
    "USD/CAD", "USD/CHF", "USD/JPY",
]

from difflib import SequenceMatcher


def _normalize_pair(text: str) -> str:
    if not text:
        return ""

    text = text.upper()
    text = re.sub(r"[^A-Z/]", "", text)

    # частые OCR ошибки
    replacements = {
        "CHE": "CHF",
        "CHP": "CHF",
        "CH": "CHF",
        "USO": "USD",
        "US0": "USD",
        "AUDD": "AUD",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    # вставка слеша если пропал
    if "/" not in text and len(text) == 6:
        text = text[:3] + "/" + text[3:]

    return text


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _detect_pair(candidates: list[str]) -> str | None:
    best_pair = None
    best_score = 0.0

    for raw in candidates:
        norm = _normalize_pair(raw)

        if not norm:
            continue

        for pair in VALID_PAIRS:
            score = _similarity(norm, pair)

            if score > best_score:
                best_score = score
                best_pair = pair

    if best_score > 0.65:
        return best_pair

    return None

def read_text(region):
    shot = pyautogui.screenshot(region=region)
    bgr = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    _dump("raw_text", bgr)
    _dump("gray_text", gray)

    candidates = []
    for variant in ("normal", "inv", "otsu"):
        raw = _ocr_text_variant(gray, variant)
        cleaned = re.sub(r"[^A-Z/ ]", "", raw.upper()).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if cleaned:
            candidates.append(cleaned)

    if not candidates:
        print("[OCR ERROR] не удалось распознать инструмент")
        return None

    # Берем самый длинный — обычно он наиболее полный
    pair = _detect_pair(candidates)

    if pair:
        return pair

    # fallback
    return max(candidates, key=len)
