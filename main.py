import os
import time
import atexit
import threading
import sys
import logging
from pathlib import Path
import speech_recognition as sr
from pynput import keyboard

from utils.logging_config import setup_logging, log_performance, log_error_with_context
from config.settings import get_settings, get_path_settings, get_voice_settings
from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once
from ocr.matching import load_champ
from scraper import scrape_to_json
from comps_html.html_to_json import parse_all_comps
from engine.comp_scraper import scrape_mobafire_comps
from assistant.rules_engine import process_voice_query
from assistant.tts_utils import speak

# Setup logging
logger = logging.getLogger(__name__)

# Cleanup generated JSON files on exit
def cleanup():
    """Clean up temporary files on application exit."""
    logger.info("Cleaning up temporary files...")
    path_settings = get_path_settings()
    
    cleanup_files = [
        os.path.join(path_settings.data_dir, path_settings.comps_file),
        os.path.join(path_settings.data_dir, path_settings.champions_file),
        os.path.join(path_settings.data_dir, path_settings.traits_file),
    ]
    
    for file_path in cleanup_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Removed: {file_path}")

atexit.register(cleanup)

# Voice recognizer setup
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Single recognition + response
def recognize_once():
    """Handle a single voice recognition and response cycle."""
    voice_settings = get_voice_settings()
    start_time = time.time()
    
    try:
        with mic as source:
            if voice_settings.ambient_noise_adjustment:
                recognizer.adjust_for_ambient_noise(source)
            logger.info("Listening for question...")
            audio = recognizer.listen(
                source, 
                timeout=voice_settings.recognition_timeout,
                phrase_time_limit=voice_settings.phrase_time_limit
            )
        
        # Speech recognition
        recognition_start = time.time()
        query = recognizer.recognize_google(audio).lower()
        recognition_time = time.time() - recognition_start
        
        logger.info(f"User asked: {query}")
        log_performance("speech_recognition", recognition_time, query_length=len(query))
        
        # Process query
        response = process_voice_query(query)
        total_time = time.time() - start_time
        
        logger.info(f"Assistant responded: {response[:100]}...")
        log_performance("total_query_processing", total_time)
        
    except sr.WaitTimeoutError:
        logger.warning("No speech detected within timeout")
        speak("No speech detected.")
    except sr.UnknownValueError:
        logger.warning("Speech recognition could not understand audio")
        speak("Sorry, I could not understand that.")
    except sr.RequestError as e:
        logger.error(f"Speech recognition service error: {e}")
        log_error_with_context(e, {"operation": "speech_recognition"})
        speak("Recognition error.")
    except Exception as e:
        logger.error(f"Unexpected error in voice recognition: {e}")
        log_error_with_context(e, {"operation": "voice_recognition"})
        speak("An error occurred.")

# Hotkey callback
def on_activate():
    """Handle hotkey activation."""
    logger.debug("Hotkey activated")
    speak("Yes?")
    recognize_once()

# TFT shop monitor loop
def shop_monitor(champions):
    """Monitor TFT shop and process champion data."""
    logger.info("Starting shop monitor thread")
    
    while True:
        try:
            if wait_for_shop():
                logger.info("Shop detected, starting monitoring")
                while shop_still_visible():
                    try:
                        start_time = time.time()
                        monitor_shop_loop_once(champions)
                        monitor_time = time.time() - start_time
                        log_performance("shop_monitor_cycle", monitor_time)
                    except Exception as e:
                        logger.error(f"Shop monitor error: {e}")
                        log_error_with_context(e, {"operation": "shop_monitoring"})
                    time.sleep(0.1)
                logger.info("Shop no longer visible")
        except Exception as e:
            logger.error(f"Critical shop monitor error: {e}")
            log_error_with_context(e, {"operation": "shop_monitor_loop"})
            time.sleep(1)

def main():
    """Main application entry point."""
    # Load configuration
    settings = get_settings()
    
    # Initialize logging
    log_dir = Path(settings.logging.log_file).parent if settings.logging.log_file else Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    setup_logging(
        level=settings.logging.level,
        log_file=settings.logging.log_file,
        max_file_size=settings.logging.max_file_size,
        backup_count=settings.logging.backup_count,
        format_str=settings.logging.format_str
    )
    
    logger.info("Starting TFT Voice Assistant")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Configuration loaded")
    
    try:
        # Create data directory
        os.makedirs(settings.paths.data_dir, exist_ok=True)
        logger.info(f"Data directory: {settings.paths.data_dir}")

        # 1) scrape compositions HTML
        logger.info("Scraping compositions from Mobafire...")
        scrape_mobafire_comps()

        # 2) convert HTML to JSON under data/
        logger.info("Converting HTML compositions to JSON...")
        comps_json_path = os.path.join(settings.paths.data_dir, settings.paths.comps_file)
        parse_all_comps(html_dir=settings.paths.comps_html_dir, output_file=comps_json_path)

        # 3) scrape champions & traits JSON
        logger.info("Scraping champions and traits data...")
        champs_path, _ = scrape_to_json(settings.paths.data_dir)
        if champs_path:
            champions = load_champ(champs_path)
            logger.info(f"Loaded {len(champions)} champions")
        else:
            logger.error("Failed to scrape champion data")
            return

        # 4) start shop-monitor thread
        logger.info("Starting shop monitor thread...")
        threading.Thread(target=shop_monitor, args=(champions,), daemon=True).start()

        # 5) register hotkeys
        logger.info("Registering hotkeys...")
        logger.info("Assistant ready; press Ctrl+Shift+S to ask, Esc to exit")
        
        with keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+s': on_activate,
            '<esc>': lambda: sys.exit(0),
        }) as h:
            h.join()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        log_error_with_context(e, {"operation": "main_application"})
        raise
    finally:
        logger.info("Application shutting down")

if __name__ == "__main__":
    main()