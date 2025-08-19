import requests
import logging
import time
from pathlib import Path
from bs4 import BeautifulSoup
import json
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChampData:
    """Data class for champion information."""
    name: str
    cost: int
    traits: List[str]

    def asdict(self) -> dict:
        return {
            "name": self.name,
            "cost": self.cost,
            "traits": self.traits
        }

@dataclass
class TraitData:
    """Data class for trait information."""
    name: str
    breaks: List[int]

    def asdict(self) -> dict:
        return {
            "name": self.name,
            "breaks": self.breaks
        }

def extract_traits(section) -> List[TraitData]:
    """Extract trait data from a webpage section.
    
    Args:
        section: BeautifulSoup section containing trait information
        
    Returns:
        List of TraitData objects
    """
    traits = []
    if not section:
        return traits
    
    try:
        for div in section.find_all("div", class_="details"):
            try:
                img_div = div.find("div", class_="details__pic")
                if not img_div:
                    continue
                    
                img_tag = img_div.find("img")
                if not img_tag or not img_tag.get("src"):
                    continue
                    
                name = Path(img_tag["src"]).stem
                
                ul = div.find("ul", class_="bbcode_list")
                if ul:
                    breaks = []
                    for li in ul.find_all("li"):
                        text = li.text.strip()
                        if text and text[0].isdigit():
                            try:
                                breaks.append(int(text[0]))
                            except ValueError:
                                logger.warning(f"Could not parse break value: {text}")
                else:
                    breaks = [1]
                
                traits.append(TraitData(name, breaks))
                
            except Exception as e:
                logger.warning(f"Error parsing trait div: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error extracting traits from section: {e}")
    
    return traits

def parse_page(html: str) -> Tuple[List[ChampData], List[TraitData]]:
    """Parse champion and trait data from HTML content.
    
    Args:
        html: HTML content to parse
        
    Returns:
        Tuple of (champions, traits) lists
    """
    if not html:
        logger.error("Empty HTML content provided")
        return [], []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        champs = []

        for div in soup.find_all("div", class_="champions-wrap__details"):
            try:
                info = div.find("div", class_="champions-wrap__details__champion__info")
                if not info:
                    continue
                
                # Extract champion name
                name_tag = info.find("span", class_="name")
                name = name_tag.text.strip() if name_tag else "Unknown"
                
                # Extract champion cost
                cost_tag = info.find("span", class_="cost")
                cost = 0
                if cost_tag:
                    cost_text = cost_tag.text.strip()
                    try:
                        # Remove the trailing currency symbol
                        cost = int(cost_text[:-1]) if cost_text and cost_text[:-1].isdigit() else 0
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse cost for {name}: {cost_text}")
                
                # Extract champion traits
                traits = []
                for img in info.find_all("img"):
                    src = img.get("src")
                    if src:
                        try:
                            trait_name = Path(src).stem
                            traits.append(trait_name)
                        except Exception as e:
                            logger.warning(f"Error parsing trait image: {e}")
                
                champs.append(ChampData(name, cost, traits))
                
            except Exception as e:
                logger.warning(f"Error parsing champion div: {e}")
                continue

        # Extract synergies (traits)
        synergies = soup.find("div", class_="synergies-wrap")
        origins = synergies.find("div", class_="origins") if synergies else None
        classes = synergies.find("div", class_="classes") if synergies else None

        traits = extract_traits(origins) + extract_traits(classes)
        
        logger.info(f"Parsed {len(champs)} champions and {len(traits)} traits")
        return champs, traits
        
    except Exception as e:
        logger.error(f"Error parsing HTML page: {e}")
        return [], []

def scrape_to_json(
    output_dir: str = "data",
    timeout: float = 30.0,
    max_retries: int = 3
) -> Tuple[Optional[str], Optional[str]]:
    """Scrape champion and trait data and save to JSON files.
    
    Args:
        output_dir: Directory to save JSON files
        timeout: HTTP request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (champions_file_path, traits_file_path) or (None, None) on failure
    """
    url = "https://www.mobafire.com/teamfight-tactics/champions"
    logger.info(f"Scraping TFT data from {url}")

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched data ({len(response.text)} characters)")
            break
            
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            logger.error("All retry attempts failed due to timeout")
            return None, None
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, None
            
        except requests.RequestException as e:
            logger.error(f"Request error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, None

    try:
        champs, traits = parse_page(response.text)
        
        if not champs:
            logger.error("No champions found in scraped data")
            return None, None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        champs_file = output_path / "champions.json"
        traits_file = output_path / "traits.json"

        # Save champions data
        with open(champs_file, "w", encoding="utf-8") as cf:
            json.dump(
                [c.asdict() for c in sorted(champs, key=lambda c: c.name)], 
                cf, 
                indent=4,
                ensure_ascii=False
            )

        # Save traits data
        with open(traits_file, "w", encoding="utf-8") as tf:
            json.dump(
                [t.asdict() for t in sorted(traits, key=lambda t: t.name)], 
                tf, 
                indent=4,
                ensure_ascii=False
            )

        logger.info(f"Champions saved to: {champs_file}")
        logger.info(f"Traits saved to: {traits_file}")
        return str(champs_file), str(traits_file)
        
    except Exception as e:
        logger.error(f"Error saving scraped data: {e}")
        return None, None
