import json
import re
from tts_utils import speak

# load comp data once
with open("data/comps_output.json") as f:
    comp_data = json.load(f)

def process_voice_query(query: str, gold: int = 0) -> str:
    match = re.search(r"i have (.+?) what should i sell", query)
    
    if match:
        raw_champ_text = match.group(1)

        split_by_comma = re.split(r",\s*", raw_champ_text)

        split_by_and = []
        for chunk in split_by_comma:
            and_parts = re.split(r"\s+and\s+", chunk)
            for part in and_parts:
                split_by_and.append(part)

        champs = []
        for champ in split_by_and:
            champ = champ.strip()
            if champ != "":
                champ = champ.title()
                champs.append(champ)

        return handle_inventory_query(champs, gold)

    fallback_message = "sorry, i can only advise on rerolling, leveling, or managing gold. "
    fallback_message += "try asking 'should i reroll?', 'when to level up?', or 'how much gold to save?'."
    return fallback_message

def handle_inventory_query(champs: list[str], gold: int) -> str:
    usable = set()

    for comp in comp_data:
        shared = False

        for user_champ in champs:
            if user_champ in comp["champions"]:
                shared = True

        if shared:
            for comp_champ in comp["champions"]:
                usable.add(comp_champ)

    to_sell = []
    for champ in champs:
        if champ not in usable:
            to_sell.append(champ)

    if len(to_sell) == 0:
        response = "all of those can fit into at least one common comp—keep them for now."
    else:
        sell_list = ", ".join(to_sell)
        response = f"sell: {sell_list}. keep the others for potential comp synergies."

    if gold < 50:
        response += " you have less than 50 gold—avoid spending below 50 to maximize interest."
    else:
        response += " good job saving at least 50 gold for interest."

    speak(response)
    return response