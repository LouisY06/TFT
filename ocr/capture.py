import pyautogui
import os
from datetime import datetime
import time

def capture_fullscreen(save_dir="assets/screenshots"):
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shop_regions = [(515, 1100, 205, 155),
                    (730, 1100, 205, 155),
                    (945, 1100, 205, 155),
                    (1160, 1100, 205, 155),
                    (1375, 1100, 205, 155)]
    print("debug: get ready")
    time.sleep(3)

    for i in range (5):
        path = os.path.join(save_dir, f"screenshot_{i+1}_{timestamp}.png")
        screenshot = pyautogui.screenshot(region=shop_regions[i])
        screenshot.save(path)
    print(f"Screenshot saved: {path}")
    print("debug ran 1")
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