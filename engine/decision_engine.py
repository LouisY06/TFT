import os
import json
import base64
from io import BytesIO
from PIL import Image
import pyautogui
import openai
import cv2

# base directories and paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "assets", "screenshots")
BENCH_IMAGE_PATH = os.path.join(SCREENSHOT_DIR, "bench.png")
SLOT_DIR = os.path.join(BASE_DIR, "assets", "slots")
TEMPLATE_DIR = "champ_templates"

# create necessary directories if they don't exist
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

if not os.path.exists(SLOT_DIR):
    os.makedirs(SLOT_DIR)

def capture_bench():
   

    region = (330, 850, 1250, 190)

    screenshot = pyautogui.screenshot(region=region)

    screenshot.save(BENCH_IMAGE_PATH)

    print("saved bench screenshot to", BENCH_IMAGE_PATH)

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

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        score = max_val

        if score > best_score:
            best_score = score
            best_match = os.path.splitext(filename)[0]

    if best_score >= threshold:
        return best_match
    else:
        return "empty"

def crop_bench_to_slots(image_path=BENCH_IMAGE_PATH, output_dir=SLOT_DIR):
    img = Image.open(image_path)

    width, height = img.size

    slot_width = width // 9

    slot_paths = []

    for i in range(9):
        left = i * slot_width
        upper = 0
        right = (i + 1) * slot_width
        lower = height

        box = (left, upper, right, lower)

        slot = img.crop(box)

        slot_filename = f"slot_{i+1}.png"
        path = os.path.join(output_dir, slot_filename)

        slot.save(path)

        slot_paths.append(path)

    return slot_paths

def detect_bench(bench_image_path=BENCH_IMAGE_PATH):
    slot_paths = crop_bench_to_slots(bench_image_path)

    bench = {}

    for i in range(len(slot_paths)):
        slot_path = slot_paths[i]

        champ = match_champion(slot_path)

        slot_key = f"slot_{i+1}"

        bench[slot_key] = champ

    return bench

def get_current_bench():
    current_bench = detect_bench()
    return current_bench