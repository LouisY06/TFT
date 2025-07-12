import os
import time
import atexit
import threading
import subprocess
import sys
import speech_recognition as sr
from pynput import keyboard

from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once
from ocr.matching import load_champ
from scraper import scrape_to_json
from comps_html.html_to_json import parse_all_comps
from engine.comp_scraper import scrape_mobafire_comps
from assistant.rules_engine import process_voice_query
from assistant.tts_utils import speak

# Directories
DATA_DIR = "data"
COMPS_HTML_DIR = "comps_html"   # where HTML files are saved
COMPS_JSON = os.path.join(DATA_DIR, "comps_output.json")
CHAMPS_JSON = os.path.join(DATA_DIR, "champions.json")
TRAITS_JSON = os.path.join(DATA_DIR, "traits.json")

# Cleanup generated JSON files on exit
def cleanup():
    for path in (COMPS_JSON, CHAMPS_JSON, TRAITS_JSON):
        if os.path.exists(path):
            os.remove(path)
atexit.register(cleanup)

# Voice recognizer setup

recognizer = sr.Recognizer()
mic = sr.Microphone()

# Single recognition + response
def recognize_once():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for question…")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    try:
        query = recognizer.recognize_google(audio).lower()
        print("User asked:", query)
        response = process_voice_query(query)
        print("Assistant:", response)
        speak(response)
    except sr.WaitTimeoutError:
        print("No speech detected.")
        speak("No speech detected.")
    except sr.UnknownValueError:
        print("Could not understand.")
        speak("Sorry, I could not understand that.")
    except sr.RequestError as e:
        print(f"Recognition error: {e}")
        speak("Recognition error.")
    except Exception as e:
        print(f"Error processing query: {e}")
        speak("An error occurred.")

# Hotkey callback
def on_activate():
    speak("Yes?")
    recognize_once()

# TFT shop monitor loop
def shop_monitor(champions):
    while True:
        try:
            if wait_for_shop():
                while shop_still_visible():
                    try:
                        monitor_shop_loop_once(champions)
                    except Exception as e:
                        print("Monitor error:", e)
                    time.sleep(0.1)
        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1) scrape compositions HTML
    scrape_mobafire_comps()

    # 2) convert HTML to JSON under data/
    parse_all_comps(html_dir=COMPS_HTML_DIR, output_file=COMPS_JSON)

    # 3) scrape champions & traits JSON
    champs_path, traits_path = scrape_to_json(DATA_DIR)
    champions = load_champ(champs_path)

    # 4) start shop-monitor thread
    threading.Thread(target=shop_monitor, args=(champions,), daemon=True).start()

    # 5) register hotkeys
    print("Assistant ready; press Ctrl+Shift+S to ask")
    with keyboard.GlobalHotKeys({
        '<ctrl>+<shift>+s': on_activate,
        '<esc>': lambda: sys.exit(0),
    }) as h:
        h.join()