import os
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
ENDPOINT = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-2.0-flash:generateContent"
)

def ask_gemini(text):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY
    }
    payload = {
        "contents": [
            { "parts": [ { "text": text } ] }
        ]
    }
    resp = requests.post(ENDPOINT, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]