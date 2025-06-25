import os
import json
from bs4 import BeautifulSoup
from collections import defaultdict

def parse_all_comps(html_dir="./comps_html", output_file="data/comps_output.json"):
    """
    Walks through all files named comp_*.html in html_dir,
    extracts comp_name, units and traits, and writes the
    results to output_file (in JSON).
    """
    def extract_traits(soup):
        traits = defaultdict(int)
        for div in soup.select("#tier__grid-title .synergies .synergy"):
            img = div.find("img")
            lbl = div.find("label")
            if img and lbl:
                name, count = img.get("alt"), lbl.text.strip()
                if name and count.isdigit():
                    traits[name] = max(traits[name], int(count))
        return traits

    def extract_units(soup):
        return [
            d.text.strip()
            for d in soup.select("#tier__grid .name")
            if d.text.strip()
        ]

    def extract_comp_name(soup):
        h1 = soup.find("h1", class_="list-title")
        return h1.get_text(" ", strip=True) if h1 else "Unknown Comp"

    comps = []
    # make sure the directory exists
    if not os.path.isdir(html_dir):
        raise FileNotFoundError(f"Directory not found: {html_dir}")

    for filename in sorted(os.listdir(html_dir)):
        if filename.startswith("comp_") and filename.endswith(".html"):
            filepath = os.path.join(html_dir, filename)
            print(f"Processing {filename}")
            with open(filepath, encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")

            comp = {
                "comp_name": extract_comp_name(soup),
                "units": extract_units(soup),
                "traits": [
                    {"name": name, "count": count}
                    for name, count in extract_traits(soup).items()
                ]
            }
            comps.append(comp)

    # write out the JSON
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(comps, out, indent=2, ensure_ascii=False)

    print(f"Parsed {len(comps)} comps. Output written to {output_file}")
    return comps

if __name__ == "__main__":
    parse_all_comps()