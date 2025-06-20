import json
from rapidfuzz import process, fuzz

#load champ list from json file
def load_champ(path="data/champs_*.json"):
    with open(path, "r") as f:
        data = json.load(f)
        return data

def match_champ(champions, name):
    for champ in champions:
        if champ["name"].lower() == name.lower():
            return champ
    return None