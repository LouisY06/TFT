import speech_recognition as sr
from rules_engine import process_voice_query
from pynput import keyboard

# Initialize recognizer and microphone once
en = sr.Recognizer()
mic = sr.Microphone()


def recognize_once():
    """
    Listen for a single voice command and process it.
    """
    with mic as source:
        en.adjust_for_ambient_noise(source)
        print("Listening... Speak your command.")
        audio = en.listen(source)
    try:
        query = en.recognize_google(audio).lower()
        print(f"Heard: {query}")
        response = process_voice_query(query)
        print(f"Assistant: {response}")
    except sr.UnknownValueError:
        print("Could not understand audio.")
    except sr.RequestError as e:
        print(f"Recognition error: {e}")


def on_activate():
    """Callback for hotkey press to trigger listening."""
    print("Hotkey pressed, activating voice assistant...")
    recognize_once()


def for_canonical(f):
    return lambda k: f(l.canonical(k))


if __name__ == "__main__":
    print("TFT Voice Assistant ready. Press CTRL+SHIFT+S to issue a command. Press ESC to exit.")
    # Map hotkeys
    hotkeys = {
        '<ctrl>+<shift>+s': on_activate,
        '<esc>': lambda: exit(0)
    }
    # Start listening for hotkeys
    with keyboard.GlobalHotKeys(hotkeys) as h:
        h.join()