from ocr.capture import capture_shop, extract_text_from_images
from ocr.detect_shop import shop_still_visible, wait_for_shop
from ocr.matching import *
import time

# Load once at top-level
champions = load_champ("data/champs_*.json")  # Replace with actual path if needed

def monitor_shop_loop_once():
    print("📡 Monitoring shop...")

    image_paths = capture_shop()
    champ_names = extract_text_from_images(image_paths[:5])  # Shop slots only

    matched = []
    for name in champ_names:
        if not name:
            matched.append({"name": None, "error": "OCR failed"})
            continue

        champ = match_champ(champions, name)
        if champ:
            matched.append(champ)
        else:
            matched.append({"name": name, "error": "Not found"})

    print("🔍 Matched Champions:")
    for champ in matched:
        if "error" in champ:
            print(f"❌ {champ['name']}: {champ['error']}")
        else:
            print(f"✅ {champ['name']} | Cost: {champ['cost']} | Traits: {', '.join(champ['traits'])}")