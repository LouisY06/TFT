import requests
from pathlib import Path
from bs4 import BeautifulSoup
import json

# === Data Classes ===
class ChampData:
    def __init__(self, name, cost, traits):
        self.name = name
        self.cost = cost
        self.traits = traits

    def asdict(self):
        return {
            "name": self.name,
            "cost": self.cost,
            "traits": self.traits
        }

class TraitData:
    def __init__(self, name, breaks):
        self.name = name
        self.breaks = breaks

    def asdict(self):
        return {
            "name": self.name,
            "breaks": self.breaks
        }

# === Utility Functions ===
def extract_traits(section):
    traits = []
    if section:
        for div in section.find_all("div", class_="details"):
            img_tag = div.find("div", class_="details__pic").find("img")
            if not img_tag or not img_tag.get("src"):
                continue
            name = Path(img_tag["src"]).stem
            ul = div.find("ul", class_="bbcode_list")
            if ul:
                breaks = [int(li.text.strip()[0]) for li in ul.find_all("li") if li.text.strip()[0].isdigit()]
            else:
                breaks = [1]
            traits.append(TraitData(name, breaks))
    return traits

def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    champs = []

    for div in soup.find_all("div", class_="champions-wrap__details"):
        info = div.find("div", class_="champions-wrap__details__champion__info")
        if not info:
            continue
        name_tag = info.find("span", class_="name")
        name = name_tag.text.strip() if name_tag else "Unknown"
        cost_tag = info.find("span", class_="cost")
        cost = int(cost_tag.text.strip()[:-1]) if cost_tag else 0
        traits = [Path(img["src"]).stem for img in info.find_all("img") if img.get("src")]
        champs.append(ChampData(name, cost, traits))

    synergies = soup.find("div", class_="synergies-wrap")
    origins = synergies.find("div", class_="origins") if synergies else None
    classes = synergies.find("div", class_="classes") if synergies else None

    traits = extract_traits(origins) + extract_traits(classes)
    return champs, traits

# === Main Scrape Function ===
def scrape_to_json(output_dir="data"):
    url = "https://www.mobafire.com/teamfight-tactics/champions"
    print(f"🌐 Scraping {url} ...")

    try:
        r = requests.get(url)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch data: {e}")
        return None, None

    champs, traits = parse_page(r.text)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    champs_file = output_path / "champions.json"
    traits_file = output_path / "traits.json"

    with open(champs_file, "w") as cf:
        json.dump([c.asdict() for c in sorted(champs, key=lambda c: c.name)], cf, indent=4)
    with open(traits_file, "w") as tf:
        json.dump([t.asdict() for t in sorted(traits, key=lambda t: t.name)], tf, indent=4)

    print(f"✅ Champions saved to: {champs_file}")
    print(f"✅ Traits saved to: {traits_file}")
    return str(champs_file), str(traits_file)
