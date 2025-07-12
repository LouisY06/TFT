import os
import json
import requests
from dotenv import load_dotenv
from assistant.tts_utils import speak

# Load your .env file to pull in GEMINI_API_KEY
load_dotenv()

#–– your data files
DATA_DIR        = os.path.join(os.path.dirname(__file__), "..", "data")
CHAMPS_PATH     = os.path.join(DATA_DIR, "champions.json")
COMPS_PATH      = os.path.join(DATA_DIR, "comps_output.json")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in environment")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-2.0-flash:generateContent"
)

def _load_data():
    with open(CHAMPS_PATH, encoding="utf-8") as f:
        champs = json.load(f)
    with open(COMPS_PATH, encoding="utf-8") as f:
        comps = json.load(f)
    return champs, comps

def _ask_gemini(prompt: str) -> str:
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    resp = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        content = data["candidates"][0]["content"]
        # if Gemini gives us a dict, pull out the text
        if isinstance(content, dict):
            if "text" in content:
                text = content["text"]
            elif "parts" in content:
                text = "".join(p.get("text", "") for p in content["parts"])
            else:
                text = json.dumps(content)
        else:
            text = content
        return text.strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected Gemini response format: {data}")

def process_voice_query(query: str) -> str:
    """
    For any question, hand off to Gemini with your JSON data as context.
    """
    champs, comps = _load_data()

    system_ctx = (
        "You are a Teamfight Tactics assistant. "
        "You know the current bench champions and gold levels from JSON, "
        "and the list of comps with their units. "
        "Answer any question dynamically based on that data, "
        "and be concise."
    )

    context = {
        "bench_data": champs,
        "comps": comps
    }

    prompt = (
        f"{system_ctx}\n\n"
        f"DATA CONTEXT (JSON):\n{json.dumps(context)}\n\n"
        f"USER QUESTION:\n{query}"
    )

    answer = _ask_gemini(prompt)
    speak(answer)
    return answer