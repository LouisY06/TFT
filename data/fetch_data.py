from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import json

# Set up headless browser
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)

# Load the page
driver.get("https://tftactics.gg/db/champion-stats/")
time.sleep(5)

# Get full HTML
html = driver.page_source
driver.quit()

# Parse HTML
soup = BeautifulSoup(html, "html.parser")

# Step 1: Find the script tag that contains __NEXT_DATA__
script_tag = soup.find("script", id="__NEXT_DATA__")
if script_tag:
    json_text = script_tag.string
    data = json.loads(json_text)

    # Step 2: Navigate to the champion data (example structure)
    try:
        champions = data["props"]["pageProps"]["champions"]
        for champ in champions:
            print(f"{champ['name']} - Cost: {champ['cost']} - Traits: {champ['traits']}")
    except KeyError:
        print("❌ Could not locate champion data in JSON.")
else:
    print("❌ __NEXT_DATA__ script tag not found.")