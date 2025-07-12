import os
import sys
import atexit
import threading
import time
import speech_recognition as sr
import shlex

from pynput import keyboard
from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once
from ocr.matching import load_champ
from scraper import scrape_to_json
from assistant.rules_engine import process_voice_query
from assistant.tts_utils import speak

# make engine/ importable
sys.path.insert(0, os.path.join(os.getcwd(), "engine"))
import comp_scraper

# make comps_html/ importable
sys.path.insert(0, os.path.join(os.getcwd(), "comps_html"))
import html_to_json

DATA_DIR     = "data"
COMPS_HTML   = "comps_html"
COMPS_JSON   = os.path.join(DATA_DIR, "comps_output.json")
CHAMPS_JSON  = os.path.join(DATA_DIR, "champions.json")
TRAITS_JSON  = os.path.join(DATA_DIR, "traits.json")

def cleanup():
    for p in (COMPS_JSON, CHAMPS_JSON, TRAITS_JSON):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

atexit.register(cleanup)

recognizer = sr.Recognizer()
mic = sr.Microphone()

def recognize_once():
    with mic as src:
        recognizer.adjust_for_ambient_noise(src)
        audio = recognizer.listen(src, timeout=5, phrase_time_limit=5)
    try:
        q = recognizer.recognize_google(audio).lower()
        print("User asked:", q)
        r = process_voice_query(q)
        print("Assistant:", r)
        speak(r)
    except sr.WaitTimeoutError:
        speak("No speech detected.")
    except sr.UnknownValueError:
        speak("Sorry, I could not understand that.")
    except sr.RequestError as e:
        print("Recognition error:", e)
        speak("Recognition error.")

def on_activate():
    speak("Yes?")
    recognize_once()

def shop_monitor(champions):
    while True:
        if wait_for_shop():
            while shop_still_visible():
                try:
                    monitor_shop_loop_once(champions)
                except Exception as e:
                    print("Monitor error:", e)
                time.sleep(0.1)
        time.sleep(1)

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1) scrape all comps HTML
    comp_scraper.scrape_mobafire_comps()

    # 2) convert to JSON under data/
    html_to_json.parse_all_comps(
        html_dir=COMPS_HTML,
        output_file=COMPS_JSON
    )

    # 3) scrape champions & traits
    scrape_to_json(DATA_DIR)
    champions = load_champ(CHAMPS_JSON)

    # start monitor thread
    threading.Thread(
        target=shop_monitor,
        args=(champions,),
        daemon=True
    ).start()

    # bind hotkeys
    with keyboard.GlobalHotKeys({
        '<ctrl>+<shift>+s': on_activate,
        '<esc>': lambda: exit(0),
    }) as h:
        print("Assistant ready; press Ctrl+Shift+S")
        h.join()