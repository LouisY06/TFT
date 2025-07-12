import os, pyautogui
from PIL import Image
import pytesseract

shop_regions = [
    (460, 1280, 150, 35),
    (700, 1280, 150, 35),
    (940, 1280, 150, 35),
    (1180, 1280, 150, 35),
    (1420, 1280, 150, 35),
    (1030, 1090, 60, 35),   # gold
    (260, 1090, 160, 40)    # level
]

def get_shop_text():
    """
    Screenshot all shop_regions, OCR them, and return list[str]:
     [slot1, slot2, slot3, slot4, slot5, gold_str, level_str]
    """
    texts = []
    for region in shop_regions:
        img = pyautogui.screenshot(region=region)
        img = img.resize((img.width*3, img.height*3), Image.Resampling.LANCZOS)
        img = img.convert("L")
        cfg = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'
        txt = pytesseract.image_to_string(img, config=cfg).strip()
        texts.append(txt)
    return texts

def read_current_gold():
    all_text = get_shop_text()
    gold_str = all_text[5]
    # strip non-digits
    digits = "".join(c for c in gold_str if c.isdigit())
    return int(digits) if digits else 0