import os
import json
import base64
from io import BytesIO
from PIL import Image
import pyautogui
import openai

# === Config ===
openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace this with your actual key
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "assets", "screenshots")
BENCH_IMAGE_PATH = os.path.join(SCREENSHOT_DIR, "bench.png")

# === Step 1: Capture bench screenshot ===
def capture_bench():
    region = (330, 850, 1250, 190)  # Adjust based on your screen resolution
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save(BENCH_IMAGE_PATH)
    print(f"✅ Saved bench screenshot to {BENCH_IMAGE_PATH}")

# === Step 2: Crop bench into 8 champion slots ===
def crop_bench_slots(bench_path):
    img = Image.open(bench_path)
    width, height = img.size
    slot_width = width // 8
    slots = []

    for i in range(8):
        left = i * slot_width
        box = (left, 0, left + slot_width, height)
        cropped = img.crop(box)
        slots.append(cropped)

    return slots

# === Step 3: Send each crop to GPT-4o ===
def identify_champion(img: Image.Image) -> str:
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a TFT assistant that identifies champions based on images. Reply with only the champion name, or 'empty' if the slot is empty."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=10
    )

    return response.choices[0].message.content.strip()

# === Step 4: Run the full bench identification ===
def identify_bench():
    capture_bench()
    slots = crop_bench_slots(BENCH_IMAGE_PATH)
    bench_result = {}

    for i, slot in enumerate(slots):
        champ_name = identify_champion(slot)
        bench_result[f"slot_{i+1}"] = champ_name
        print(f"Slot {i+1}: {champ_name}")

    with open("bench_result.json", "w") as f:
        json.dump({"bench": bench_result}, f, indent=2)

    print("✅ Saved bench_result.json")

# === Run ===
if __name__ == "__main__":
    identify_bench()