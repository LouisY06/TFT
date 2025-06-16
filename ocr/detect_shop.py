import pyautogui
import time

def wait_for_shop(path="photo/reroll_text.png", confidence=0.8):
    print("⏳ Waiting for shop...")
    while True:
        try:
            location = pyautogui.locateOnScreen(path, confidence=confidence)
            if location:
                print("Shop detected at", location)
                time.sleep(2)
                return True
        except pyautogui.ImageNotFoundException:
            pass

        time.sleep(1)

def shop_still_visible(path="photo/reroll_text.png", confidence=0.8):
    location = pyautogui.locateOnScreen(path, confidence=confidence)
    return location is not None

