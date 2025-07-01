import os
import json
import base64
from io import BytesIO
from PIL import Image
import pyautogui
import openai
import cv2

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "assets", "screenshots")
BENCH_IMAGE_PATH = os.path.join(SCREENSHOT_DIR, "bench.png")
SLOT_DIR = os.path.join(BASE_DIR, "assets", "slots")
TEMPLATE_DIR = "champ_templates"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(SLOT_DIR, exist_ok=True)

def capture_bench():
    region = (330, 850, 1250, 190)
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save(BENCH_IMAGE_PATH)
    print(f"Saved bench screenshot to {BENCH_IMAGE_PATH}")

def match_champion(crop_path, template_dir=TEMPLATE_DIR, threshold=0.75):
    crop = cv2.imread(crop_path)
    best_score = -1
    best_match = "empty"
    for filename in os.listdir(template_dir):
        template_path = os.path.join(template_dir, filename)
        template = cv2.imread(template_path)
        if template is None:
            continue
        result = cv2.matchTemplate(crop, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)
        if score > best_score:
            best_score = score
            best_match = os.path.splitext(filename)[0]
    return best_match if best_score >= threshold else "empty"

def crop_bench_to_slots(image_path=BENCH_IMAGE_PATH, output_dir=SLOT_DIR):
    img = Image.open(image_path)
    width, height = img.size
    slot_width = width // 9
    slot_paths = []
    for i in range(9):
        box = (i * slot_width, 0, (i + 1) * slot_width, height)
        slot = img.crop(box)
        path = os.path.join(output_dir, f"slot_{i+1}.png")
        slot.save(path)
        slot_paths.append(path)
    return slot_paths

def detect_bench(bench_image_path=BENCH_IMAGE_PATH):
    slot_paths = crop_bench_to_slots(bench_image_path)
    bench = {}
    for i, slot_path in enumerate(slot_paths):
        champ = match_champion(slot_path)
        bench[f"slot_{i+1}"] = champ
    return bench

def get_current_bench():
    return detect_bench()