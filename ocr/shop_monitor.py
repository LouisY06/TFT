from ocr.capture import capture_shop, extract_text_from_images
from ocr.detect_shop import *
import time

def monitor_shop_loop(interval=2):
    print("📡 Monitoring shop... Press Ctrl+C to stop.")
    while True:
        if not shop_still_visible():
            print("Shop no longer visible, exiting loop")
            break
        image_paths = capture_shop()
        champ_names = extract_text_from_images(image_paths[:5])  # only the 5 shop slots
        print(f"Shop Champions: {champ_names}")
        time.sleep(interval)