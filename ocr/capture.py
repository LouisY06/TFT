import pyautogui
import os
from datetime import datetime
import time
import pytesseract
from PIL import Image

shop_regions = [(460, 1280, 150, 35),
                    (700, 1280, 150, 35),
                    (940, 1280, 150, 35),
                    (1180, 1280, 150, 35),
                    (1420, 1280, 150, 35), #slots 1-5 of shop
                    (1030, 1090, 60, 35)] #gold capture
#captures info
def capture_shop(save_dir="assets/screenshots"):
    os.makedirs(save_dir, exist_ok=True)
    print("debug: get ready")
    time.sleep(3)
    
    for i in range (len(shop_regions)):
        path = os.path.join(save_dir, f"slot_{i+1}.png")
        screenshot = pyautogui.screenshot(region=shop_regions[i])
        screenshot.save(path)
        print(f"Screenshot saved: {path}")

    return path


def capture_level(save_dir="assets/screenshots"):

    pass

def capture_item(save_dir="assets/screenshots"):
    pass

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

    for i in range(len(shop_regions)):
        image_path = os.path.join(directory, f"slot_{i+1}.png")

        if not os.path.exists(image_path):
            print(f"Missing file: {image_path}")
            results.append(None)
            continue

        image = Image.open(image_path)

        image = image.resize((image.width * 3, image.height * 3),resample=Image.Resampling.LANCZOS)

        image = image.convert("L")

        # tesseract config: single-line mode, character whitelist
        config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

        #Perform OCR
        text = pytesseract.image_to_string(image, config=config)

        # Clean up result
        cleaned = text.strip().replace("\n", " ")
        results.append(cleaned)

        print(f"Slot {i+1} OCR: {cleaned}")

    print(f"\nAll OCR results: {results}")
    return results
