import subprocess
import os
from datetime import datetime

def run_scraper(output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)

    print("Running TFT data scraper...")
    subprocess.run(["python3", "scraper/main.py", output_dir], check=True)

    champs_path = os.path.join(output_dir, "champions.json")
    traits_path = os.path.join(output_dir, "traits.json")

    if not os.path.exists(champs_path) or not os.path.exists(traits_path):
        raise FileNotFoundError("Champion or trait data not found after scraper run.")

    print(f"Champion data: {champs_path}")
    print(f"Trait data: {traits_path}")
    return champs_path, traits_path