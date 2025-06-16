import pyautogui
import os
import time
from PIL import Image
import pytesseract

# Define shop capture regions (5 slots + gold + level)
shop_regions = [
    (460, 1280, 150, 35),
    (700, 1280, 150, 35),
    (940, 1280, 150, 35),
    (1180, 1280, 150, 35),
    (1420, 1280, 150, 35),
    (1030, 1090, 60, 35),   # gold
    (260, 1090, 160, 40)    # level
]

# Set base screenshot directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "assets", "screenshots")


def capture_shop(save_dir=SCREENSHOT_DIR):
    os.makedirs(save_dir, exist_ok=True)
    print("📸 Capturing shop in 3 seconds...")
    time.sleep(3)

    paths = []
    for i, region in enumerate(shop_regions):
        path = os.path.join(save_dir, f"slot_{i+1}.png")
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(path)
        print(f"Saved: {path}")
        paths.append(path)

    return paths


def delete_screenshots(directory=SCREENSHOT_DIR):
    if not os.path.exists(directory):
        print("Screenshot directory does not exist.")
        return
    count = 0
    for file in os.listdir(directory):
        if file.endswith(".png"):
            os.remove(os.path.join(directory, file))
            count += 1
    print(f"Deleted {count} screenshot(s) from {directory}.")


def extract_text_from_images(image_paths):
    results = []
    for path in image_paths:
        if not os.path.exists(path):
            print(f"Missing file: {path}")
            results.append(None)
            continue

        image = Image.open(path)
        image = image.resize((image.width * 3, image.height * 3), resample=Image.Resampling.LANCZOS)
        image = image.convert("L")

        config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(image, config=config)

        cleaned = text.strip().replace("\n", " ")
        results.append(cleaned)
        print(f"OCR: {cleaned}")

    print(f"\nAll OCR results: {results}")
    return results