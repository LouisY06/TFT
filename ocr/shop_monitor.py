import time
from ocr.capture import capture_shop, extract_text_from_images
from ocr.detect_shop import shop_still_visible
from ocr.matching import load_champ, match_champ

def monitor_shop_loop_once(champions):
    image_paths = capture_shop()
    champ_names = extract_text_from_images(image_paths[:5])

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
            print(f"{champ['name']}: {champ['error']}")
        else:
            print(f"{champ['name']} | Cost: {champ['cost']} | Traits: {', '.join(champ['traits'])}")