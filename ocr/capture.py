import pyautogui
import os
from datetime import datetime
import time
import pytesseract
from PIL import Image

def capture_fullscreen(save_dir="assets/screenshots"):
    os.makedirs(save_dir, exist_ok=True)
    shop_regions = [(515, 1220, 150, 30),
                    (730, 1220, 150, 30),
                    (945, 1220, 150, 30),
                    (1160, 1220, 150, 30),
                    (1375, 1220, 150, 30)]
    print("debug: get ready")
    time.sleep(3)

    for i in range (5):
        path = os.path.join(save_dir, f"slot_{i+1}.png")
        screenshot = pyautogui.screenshot(region=shop_regions[i])
        screenshot.save(path)
        print(f"Screenshot saved: {path}")

    return path

def delete_screenshots(directory="assets/screenshots"):
    if not os.path.exists(directory):
        print("DNE")
        return
    count = 0
    for file in os.listdir(directory):
        if file.endswith(".png"):
            os.remove(os.path.join(directory, file))
            count = count + 1
    print(f"Deleted {count} screenshot(s) from {directory}.")

def extract_text(directory="assets/screenshots"):
    results = []
    for i in range(5):
        image_path = os.path.join(directory, f"slot_{i+1}.png")

        if not os.path.exists(image_path):
            print(f"missing file: {image_path}")
            results.append(None)
            continue
        
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        cleaned = text.strip().replace("\n", " ")
        results.append(cleaned)
        print(f"Slot {i+1} OCR: {cleaned}")


    return results
