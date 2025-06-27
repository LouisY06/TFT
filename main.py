import os
import time
import atexit
import shutil
from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once
from ocr.matching import load_champ
from scraper import scrape_to_json
from engine.api_engine import capture_bench

DATA_DIR = "data"
CHAMPS_PATH = os.path.join(DATA_DIR, "champions.json")
TRAITS_PATH = os.path.join(DATA_DIR, "traits.json")

def cleanup_files():
    if os.path.exists(CHAMPS_PATH):
        os.remove(CHAMPS_PATH)
        print("Deleted:", CHAMPS_PATH)
    if os.path.exists(TRAITS_PATH):
        os.remove(TRAITS_PATH)
        print("Deleted:", TRAITS_PATH)

def cleanup_pycache():
    if '__file__' in globals():
        base_dir = os.path.abspath(os.path.dirname(__file__))
    else:
        base_dir = os.path.abspath(os.getcwd())

    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d == "__pycache__":
                pycache_dir = os.path.join(root, d)
                for filename in os.listdir(pycache_dir):
                    file_path = os.path.join(pycache_dir, filename)
                    if filename.endswith(".pyc") and os.path.isfile(file_path):
                        os.remove(file_path)
                        print("Deleted .pyc file:", file_path)

atexit.register(cleanup_files)
atexit.register(cleanup_pycache)

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
                capture_bench()
                monitor_shop_loop_once(champions)

if __name__ == "__main__":
    main()