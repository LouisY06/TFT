import os
import json
import re
from dotenv import load_dotenv
import requests

load_dotenv() 

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in environment")

CHAMPS_PATH = "data/champions.json"
COMPS_PATH = "data/comps_output.json"


def _load_data():
    with open(CHAMPS_PATH, encoding="utf-8") as f:
        champs = json.load(f)
    with open(COMPS_PATH, encoding="utf-8") as f:
        comps = json.load(f)
    return champs, comps


def _ask_gemini(prompt: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com"
        f"/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    )
    payload = {
        "prompt": {"text": prompt},
        "temperature": 0.2,
        "candidateCount": 1,
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()

    # Debug: print entire response so you can inspect its structure
    print("=== raw Gemini response ===")
    print(json.dumps(data, indent=2))
    print("===========================")

    # Try a few common fields:
    # 1) top-level "candidates"
    if "candidates" in data:
        candidates = data["candidates"]
    # 2) top-level "choices"
    elif "choices" in data:
        candidates = data["choices"]
    # 3) older schema under "output": {"choices": [...]}
    elif data.get("output", {}).get("choices"):
        candidates = data["output"]["choices"]
    else:
        raise RuntimeError("Unexpected Gemini response format (no candidates/choices)")

    if not candidates:
        return "Gemini returned no candidates."

    first = candidates[0]

    # Most likely path: first["content"]["text"]
    if isinstance(first.get("content"), dict) and "text" in first["content"]:
        return first["content"]["text"]

    # Some schemas put the text at first["text"]
    if "text" in first:
        return first["text"]

    # Or nested under message.content
    if first.get("message", {}).get("content"):
        return first["message"]["content"]

    raise RuntimeError("Unexpected Gemini response format (missing text field)")


def process_voice_query(query: str) -> str:
    champs, comps = _load_data()

    # build a dynamic prompt; you can expand this as you add new question types
    prompt = (
        "You are a Teamfight Tactics assistant.  "
        f"The player asked: “{query}”.  "
        "You have access to the champion data (champions.json) and comp data (comps_output.json).  "
        "Answer succinctly, pulling from the JSON where needed."
    )

    return _ask_gemini(prompt)