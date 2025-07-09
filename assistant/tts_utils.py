# tts_utils.py
import os, shlex

def speak(text: str):
    """Use macOS `say` to vocalize."""
    os.system(f"say {shlex.quote(text)}")