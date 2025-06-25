import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time

BASE_URL = "https://www.mobafire.com"
HTML_DIR = Path("comps_html")  # Output directory for HTML files

class CompData:
    def __init__(self, name, champions):
        self.name = name
        self.champions = champions

    def asdict(self):
        return {"name": self.name, "champions": self.champions}

def get_comp_links():
    url = f"{BASE_URL}/teamfight-tactics/team-comps"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = [
        BASE_URL + a["href"]
        for a in soup.select("div.comps a.tft-row[href^='/teamfight-tactics/team-comps/']")
        if a.get("href")
    ]
    return links

def get_comp_data(url, index):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Ensure the comps_html directory exists
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    # Save full HTML to comps_html folder
    debug_file = HTML_DIR / f"comp_{index:03}.html"
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print(f"Saved HTML to {debug_file}")

    return CompData("TEMP", [])

def scrape_mobafire_comps():
    print("Scraping Mobafire TFT comps...")

    try:
        comp_links = get_comp_links()
    except Exception as e:
        print(f"Failed to fetch comp list: {e}")
        return

    print(f"Found {len(comp_links)} comp links")

    for i, link in enumerate(comp_links, start=1):
        try:
            get_comp_data(link, i)
            time.sleep(0.3)
        except Exception as e:
            print(f"Failed to scrape {link}: {e}")

    print(f"Finished scraping. HTML files are in '{HTML_DIR}'.")
    
if __name__ == "__main__":
    scrape_mobafire_comps()