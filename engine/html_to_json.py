import os
import time
import atexit
import shutil

from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once
from engine.comp_scraper import scrape_comp_html
from engine.html_to_json import parse_all_comps
from ocr.matching import load_champ
from assistant.rules_engine import get_current_bench, capture_bench

DATA_DIR = "data"
COMPS_HTML_DIR = "comps_html"
COMPS_JSON_PATH = os.path.join(DATA_DIR, "comps_output.json")

def cleanup_files():
    if os.path.exists(COMPS_JSON_PATH):
        os.remove(COMPS_JSON_PATH)
        print("Deleted:", COMPS_JSON_PATH)

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
    print("=== TFT Assistant Starting ===")

    print("Running TFT data scraper...")
    scrape_comp_html(output_dir=COMPS_HTML_DIR)

    print("Parsing HTML into JSON...")
    parse_all_comps(COMPS_HTML_DIR, COMPS_JSON_PATH)

    if not os.path.exists(COMPS_JSON_PATH):
        print("JSON file not found after scraping.")
        return

    champions = load_champ(COMPS_JSON_PATH)

    while True:
        try:
            if wait_for_shop():
                print("Shop detected, entering monitor loop...")
                while shop_still_visible():
                    print("Shop still visible...")
                    capture_bench()
                    bench = get_current_bench()
                    print("Bench detected:", bench)
                    monitor_shop_loop_once(champions)
                    time.sleep(0.1)
                print("Shop no longer visible.")
        except Exception as e:
            print("Caught exception:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()