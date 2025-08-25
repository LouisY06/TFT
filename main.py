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
from vision.game_state_analyzer import get_game_analyzer

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

def on_analyze_game():
    """Analyze current game state using pure vision and provide feedback."""
    logger.info("Game analysis hotkey activated")
    speak("Analyzing your screen...")
    
    try:
        start_time = time.time()
        
        # Get game analyzer and analyze current state using vision only
        analyzer = get_game_analyzer()
        vision_stats = analyzer.get_game_stats_only()
        
        analysis_time = time.time() - start_time
        log_performance("vision_game_analysis", analysis_time)
        
        # Create strategic advice based on vision data
        if vision_stats:
            advice_parts = []
            advice_parts.append("Based on your screen analysis:")
            
            # Report detected stats
            if vision_stats.get('gold') is not None:
                gold = vision_stats['gold']
                advice_parts.append(f"You have {gold} gold.")
                
                # Gold-based advice
                if gold >= 50:
                    advice_parts.append("With 50+ gold, consider rolling for upgrades or key champions.")
                elif gold >= 30:
                    advice_parts.append("Good economy. Save for next level or roll if you need key units.")
                else:
                    advice_parts.append("Low gold. Focus on economy and avoid unnecessary rerolls.")
            
            if vision_stats.get('level') is not None:
                level = vision_stats['level']
                advice_parts.append(f"You are level {level}.")
                
                # Level-based advice
                if level <= 6:
                    advice_parts.append("Early game. Focus on economy and basic synergies.")
                elif level <= 8:
                    advice_parts.append("Mid game. Start rolling for key 4-cost champions.")
                else:
                    advice_parts.append("Late game. Look for 5-cost champions and perfect positioning.")
            
            if vision_stats.get('health') is not None:
                health = vision_stats['health']
                advice_parts.append(f"Your health is {health}.")
                
                # Health-based advice  
                if health <= 20:
                    advice_parts.append("Critical health! Prioritize immediate strength over economy.")
                elif health <= 40:
                    advice_parts.append("Low health. Balance economy with board strength.")
                else:
                    advice_parts.append("Healthy. You can afford to be greedy with economy.")
            
            if vision_stats.get('round_stage'):
                round_stage = vision_stats['round_stage']
                advice_parts.append(f"It's round {round_stage}.")
                
                # Round-based advice
                if '1-' in round_stage or '2-' in round_stage:
                    advice_parts.append("Early rounds. Focus on economy and basic synergies.")
                elif '3-' in round_stage or '4-' in round_stage:
                    advice_parts.append("Mid game transition. Start building your core composition.")
                else:
                    advice_parts.append("Late game. Focus on optimization and positioning.")
            
            # General advice
            advice_parts.append("For detailed champion advice, use Ctrl+Shift+S and describe your board.")
            
            advice = " ".join(advice_parts)
            logger.info(f"Vision-based analysis: {vision_stats}")
            logger.info(f"Advice provided: {advice[:100]}...")
            speak(advice)
            
        else:
            error_msg = "Could not detect game information from screen. Make sure TFT is visible and try running the calibration tool."
            logger.warning("No vision stats detected")
            speak(error_msg)
            
    except Exception as e:
        error_msg = f"Vision analysis error: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {"operation": "vision_game_analysis"})
        speak("Screen analysis failed. Make sure TFT is visible and try the calibration tool.")

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
        logger.info("Assistant ready:")
        logger.info("  Ctrl+Shift+S: Ask question")
        logger.info("  Ctrl+Shift+A: Analyze current game state")
        logger.info("  Esc: Exit")
        
        with keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+s': on_activate,
            '<ctrl>+<shift>+a': on_analyze_game,
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