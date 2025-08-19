import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

def load_champ(path: str) -> List[Dict[str, Any]]:
    """Load champion data from JSON file.
    
    Args:
        path: Path to the JSON file containing champion data
        
    Returns:
        List of champion dictionaries
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Champion data file not found: {path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("Champion data must be a list")
        
        logger.info(f"Loaded {len(data)} champions from {path}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in champion file {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading champion data: {e}")
        raise

def match_champ(
    champions: List[Dict[str, Any]], 
    name: str,
    use_fuzzy: bool = True,
    threshold: float = 80.0
) -> Optional[Dict[str, Any]]:
    """Match a champion name to the champion database.
    
    Args:
        champions: List of champion dictionaries
        name: Champion name to match
        use_fuzzy: Whether to use fuzzy matching if exact match fails
        threshold: Minimum fuzzy match score (0-100)
        
    Returns:
        Champion dictionary if found, None otherwise
    """
    if not name or not isinstance(name, str):
        logger.warning(f"Invalid champion name: {name}")
        return None
    
    if not champions:
        logger.warning("Empty champions list provided")
        return None
    
    name_clean = name.strip().lower()
    
    # Try exact match first
    for champ in champions:
        if not isinstance(champ, dict) or "name" not in champ:
            continue
        
        champ_name = champ.get("name", "").lower()
        if champ_name == name_clean:
            logger.debug(f"Exact match found: {name} -> {champ['name']}")
            return champ
    
    # Try fuzzy matching if enabled
    if use_fuzzy and 0 <= threshold <= 100:
        try:
            champion_names = [
                champ.get("name", "") for champ in champions 
                if isinstance(champ, dict) and "name" in champ
            ]
            
            if not champion_names:
                logger.warning("No valid champion names found for fuzzy matching")
                return None
            
            # Use rapidfuzz for fuzzy matching
            result = process.extractOne(
                name,
                champion_names,
                scorer=fuzz.ratio,
                score_cutoff=threshold
            )
            
            if result:
                matched_name, score, _ = result
                # Find the champion data for the matched name
                for champ in champions:
                    if champ.get("name", "").lower() == matched_name.lower():
                        logger.info(f"Fuzzy match found: {name} -> {matched_name} (score: {score:.1f})")
                        return champ
                        
        except Exception as e:
            logger.error(f"Error during fuzzy matching: {e}")
    
    logger.debug(f"No match found for champion: {name}")
    return None

def find_similar_champions(
    champions: List[Dict[str, Any]], 
    name: str, 
    limit: int = 5
) -> List[tuple]:
    """Find similar champion names for suggestions.
    
    Args:
        champions: List of champion dictionaries
        name: Champion name to find similarities for
        limit: Maximum number of suggestions to return
        
    Returns:
        List of (champion_name, similarity_score) tuples
    """
    if not name or not champions:
        return []
    
    try:
        champion_names = [
            champ.get("name", "") for champ in champions 
            if isinstance(champ, dict) and "name" in champ
        ]
        
        results = process.extract(
            name,
            champion_names,
            scorer=fuzz.ratio,
            limit=limit
        )
        
        return [(match[0], match[1]) for match in results]
        
    except Exception as e:
        logger.error(f"Error finding similar champions: {e}")
        return []