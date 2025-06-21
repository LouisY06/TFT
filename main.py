import os
import time
import atexit
from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once
from ocr.matching import load_champ
from scraper import scrape_to_json

DATA_DIR = "data"
CHAMPS_PATH = os.path.join(DATA_DIR, "champions.json")
TRAITS_PATH = os.path.join(DATA_DIR, "traits.json")

def cleanup_files():
    if os.path.exists(CHAMPS_PATH):
        os.remove(CHAMPS_PATH)
        print("🧹 Deleted:", CHAMPS_PATH)
    if os.path.exists(TRAITS_PATH):
        os.remove(TRAITS_PATH)
        print("🧹 Deleted:", TRAITS_PATH)

atexit.register(cleanup_files)

def main():
    print("Starting TFT live monitor...")

    print("Scraping champion and trait data...")
    champs_path, traits_path = scrape_to_json(DATA_DIR)

    if not os.path.exists(champs_path) or not os.path.exists(traits_path):
        print("JSON files not found after scraping.")
        return

    champions = load_champ(champs_path)

    while True:
        if wait_for_shop():
            print("Shop detected, entering monitor loop...")
            while shop_still_visible():
                monitor_shop_loop_once(champions)
               
if __name__ == "__main__":
    main()