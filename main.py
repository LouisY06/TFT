import os
import time
import atexit
import shutil
from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once
from ocr.matching import load_champ
from scraper import scrape_to_json
import threading
import speech_recognition as sr
import shlex
import importlib
from pynput import keyboard
from assistant.rules_engine import process_voice_query
import assistant.rules_engine as rules_engine

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

# === Voice assistant setup ===
recognizer = sr.Recognizer()
mic = sr.Microphone()

def speak(text: str):
    """Say the text via system TTS."""
    os.system(f"say {shlex.quote(text)}")

def refresh_data():
    """Re-scrape JSON and reload the rules engine."""
    os.makedirs(DATA_DIR, exist_ok=True)
    print("⟳ Scraping champion and trait data…")
    scrape_to_json(DATA_DIR)
    importlib.reload(rules_engine)
    print("✔ Rules engine reloaded.")

def recognize_once():
    """Listen once, process the query, and speak the response."""
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🎙 Listening for question…")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    try:
        query = recognizer.recognize_google(audio).lower()
        print(f"Heard: {query}")
        resp = process_voice_query(query)
        print(f"Assistant: {resp}")
        speak(resp)
    except sr.WaitTimeoutError:
        print("⚠️ No speech detected.")
        speak("No speech detected.")
    except sr.UnknownValueError:
        print("❓ Could not understand.")
        speak("Sorry, I could not understand that.")
    except sr.RequestError as e:
        print(f"⛔ Recognition error: {e}")
        speak("Recognition error.")

def on_activate():
    """Hotkey callback: refresh data then handle one voice query."""
    print("🔑 Hotkey pressed — updating data and answering.")
    refresh_data()
    recognize_once()
# === end voice assistant setup ===

def main():
    print("Starting TFT live monitor...")

    print("Scraping champion and trait data...")
    champs_path, traits_path = scrape_to_json(DATA_DIR)

    if not os.path.exists(champs_path) or not os.path.exists(traits_path):
        print("JSON files not found after scraping.")
        return

    champions = load_champ(champs_path)
    

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
    # Start live-monitor in background
    monitor_thread = threading.Thread(target=main, daemon=True)
    monitor_thread.start()

    # Hotkey listener for voice queries
    print("TFT Voice Assistant ready.")
    print(" • Press CTRL+SHIFT+S to ask a question.")
    print(" • Press ESC to exit.")
    hotkeys = {
        '<ctrl>+<shift>+s': on_activate,
        '<esc>': lambda: exit(0)
    }
    with keyboard.GlobalHotKeys(hotkeys) as h:
        h.join()