import pyautogui
import time
import os
def wait_for_shop(path="photo/reroll_text.png", confidence=0.8):
    full = os.path.abspath(path)
    print(f"Looking for {full}")
    print("⏳ Waiting for shop...")

    while True:
        try:
            location = pyautogui.locateOnScreen(full, confidence=confidence)
            if location:
                print("Shop detected at", location)
                time.sleep(2)
                return True
        except pyautogui.ImageNotFoundException:
            pass

        time.sleep(1)


def shop_still_visible(path="photo/reroll_text.png", confidence=0.8):
    full = os.path.abspath(path)
    try:
        location = pyautogui.locateOnScreen(full, confidence=confidence)
        return location is not None
    except pyautogui.ImageNotFoundException:
        return False  # Treat as "not visible" if not found

