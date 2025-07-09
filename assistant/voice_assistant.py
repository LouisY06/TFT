# rules_engine.py
import json
import re
from tts_utils import speak

# Load comp definitions once at import time
with open("data/comps_output.json") as f:
    COMPS = json.load(f)

def process_voice_query(query: str, gold: int = 0) -> str:
    """
    Master entrypoint: handles reroll/level/gold queries AND inventory queries.
    """
    # inventory query: pattern "i have X and Y and Z what should i sell"
    m = re.search(r"i have (.+?) what should i sell", query)
    if m:
        raw = m.group(1)
        # split on commas or 'and'
        champs = re.split(r",\s*|\s+and\s+", raw)
        champs = [c.strip().title() for c in champs if c.strip()]
        return handle_inventory_query(champs, gold)

    # ... your existing reroll/level/gold logic here ...
    # (unchanged)
    return "Sorry, I can only advise on rerolling, leveling, or managing gold. "\
           "Try asking 'should I reroll?', 'when to level up?', or 'how much gold to save?'."

def handle_inventory_query(champs: list[str], gold: int) -> str:
    """
    Given a list of champions and your gold, returns which ones to sell.
    """
    # Find all champions used by any comp that you *could* be building
    usable = set()
    for comp in COMPS:
        # if comp shares at least one of your champs, assume you're aiming for it
        if any(c in comp["champions"] for c in champs):
            usable.update(comp["champions"])

    # sell any champ you don't need
    to_sell = [c for c in champs if c not in usable]
    if not to_sell:
        resp = "All of those can fit into at least one common comp—keep them for now."
    else:
        resp = f"Sell: {', '.join(to_sell)}. " \
               f"Keep the others for potential comp synergies."
    # Optionally mention gold-interest:
    if gold < 50:
        resp += " You have less than 50 gold—avoid spending below 50 to maximize interest."
    else:
        resp += " Good job saving at least 50 gold for interest."
    # speak and return
    speak(resp)
    return resp