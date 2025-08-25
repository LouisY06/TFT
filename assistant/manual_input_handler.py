import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class GameStateInput:
    """Manual input for current game state."""
    board_champions: List[str] = None
    bench_champions: List[str] = None
    gold: Optional[int] = None
    level: Optional[int] = None
    health: Optional[int] = None
    round_stage: Optional[str] = None
    shop_champions: List[str] = None
    target_comp: Optional[str] = None
    
    def __post_init__(self):
        if self.board_champions is None:
            self.board_champions = []
        if self.bench_champions is None:
            self.bench_champions = []
        if self.shop_champions is None:
            self.shop_champions = []

class ManualInputHandler:
    """Handles manual user input for game state information."""
    
    def __init__(self):
        self.champion_aliases = self._load_champion_aliases()
        self.current_state = GameStateInput()
    
    def _load_champion_aliases(self) -> Dict[str, str]:
        """Load champion name aliases for flexible input."""
        # Common abbreviations and alternate names
        aliases = {
            # Example aliases - you'd expand this based on actual champion names
            'mf': 'miss fortune',
            'gp': 'gangplank', 
            'ez': 'ezreal',
            'tf': 'twisted fate',
            'ashe': 'ashe',
            'jinx': 'jinx',
            'vi': 'vi',
            'cait': 'caitlyn',
            'jayce': 'jayce',
            'viktor': 'viktor',
            'ekko': 'ekko',
            'warwick': 'warwick',
            'ww': 'warwick',
            # Add more as needed
        }
        
        # Load from champion data for exact names
        try:
            champs_path = Path("data/champions.json")
            if champs_path.exists():
                with open(champs_path, 'r') as f:
                    champions = json.load(f)
                for champ in champions:
                    name = champ.get('name', '').lower()
                    aliases[name] = name
                    # Add shortened versions
                    if ' ' in name:
                        short_name = name.replace(' ', '')
                        aliases[short_name] = name
        except Exception as e:
            logger.warning(f"Could not load champion aliases: {e}")
        
        return aliases
    
    def parse_voice_input(self, query: str) -> Optional[GameStateInput]:
        """Parse voice input to extract game state information.
        
        Args:
            query: User's voice input
            
        Returns:
            Parsed game state or None if no state info found
        """
        query = query.lower().strip()
        logger.info(f"Parsing voice input: {query}")
        
        state = GameStateInput()
        
        # Parse gold
        gold_match = re.search(r'(?:i have|with|got)\s*(\d+)\s*gold', query)
        if gold_match:
            state.gold = int(gold_match.group(1))
            logger.debug(f"Parsed gold: {state.gold}")
        
        # Parse level
        level_match = re.search(r'(?:level|lvl)\s*(\d+)', query)
        if level_match:
            state.level = int(level_match.group(1))
            logger.debug(f"Parsed level: {state.level}")
        
        # Parse health
        health_match = re.search(r'(?:health|hp|life)\s*(\d+)', query)
        if health_match:
            state.health = int(health_match.group(1))
            logger.debug(f"Parsed health: {state.health}")
        
        # Parse round
        round_match = re.search(r'round\s*(\d+[-–]\d+)', query)
        if round_match:
            state.round_stage = round_match.group(1)
            logger.debug(f"Parsed round: {state.round_stage}")
        
        # Parse champions on board
        board_keywords = ['on my board', 'on board', 'my board has']
        for keyword in board_keywords:
            if keyword in query:
                # Extract text after the keyword until next major section
                after_keyword = query.split(keyword, 1)[1]
                # Stop at bench, shop, or other keywords
                stop_words = ['on bench', 'bench has', 'in shop', 'shop has', 'shop shows']
                text_section = after_keyword
                for stop_word in stop_words:
                    if stop_word in after_keyword:
                        text_section = after_keyword.split(stop_word)[0]
                        break
                
                champions = self._extract_champions_from_text(text_section)
                if champions:
                    state.board_champions.extend(champions)
                    logger.debug(f"Parsed board champions: {champions}")
                break
        
        # Special case: "with X and Y on my board" pattern
        board_with_pattern = re.search(r'with\s+([a-zA-Z\s]+?)\s+on\s+(?:my\s+)?board', query)
        if board_with_pattern and not state.board_champions:
            champion_text = board_with_pattern.group(1).strip()
            # Remove common words and split on 'and'
            champion_text = champion_text.replace(' and ', ',')
            champions = self._extract_champions_from_text(champion_text)
            
            if champions:
                state.board_champions.extend(champions)
                logger.debug(f"Parsed board champions from 'with' pattern: {champions}")
        
        # Parse bench champions
        bench_keywords = ['on my bench', 'on bench', 'bench has', 'benched']
        for keyword in bench_keywords:
            if keyword in query:
                if keyword == 'benched':
                    # Special handling for "X benched" pattern
                    benched_pattern = re.search(r'([a-zA-Z\s,]+?)\s+benched', query)
                    if benched_pattern:
                        text_section = benched_pattern.group(1)
                    else:
                        continue
                else:
                    after_keyword = query.split(keyword, 1)[1]
                    # Stop at shop or other keywords
                    stop_words = ['in shop', 'shop has', 'shop shows', 'can buy', 'trying to', 'going for']
                    text_section = after_keyword
                    for stop_word in stop_words:
                        if stop_word in after_keyword:
                            text_section = after_keyword.split(stop_word)[0]
                            break
                
                champions = self._extract_champions_from_text(text_section)
                if champions:
                    state.bench_champions.extend(champions)
                    logger.debug(f"Parsed bench champions: {champions}")
                break
        
        # Parse shop champions
        shop_keywords = ['in shop', 'shop has', 'shop shows', 'can buy']
        for keyword in shop_keywords:
            if keyword in query:
                after_keyword = query.split(keyword, 1)[1]
                # Stop at target comp or other keywords
                stop_words = ['trying to', 'going for', 'want to play', 'playing']
                text_section = after_keyword
                for stop_word in stop_words:
                    if stop_word in after_keyword:
                        text_section = after_keyword.split(stop_word)[0]
                        break
                
                champions = self._extract_champions_from_text(text_section)
                if champions:
                    state.shop_champions.extend(champions)
                    logger.debug(f"Parsed shop champions: {champions}")
                break
        
        # Parse target comp
        comp_keywords = ['want to play', 'going for', 'trying to build', 'playing']
        for keyword in comp_keywords:
            if keyword in query:
                after_keyword = query.split(keyword, 1)[1]
                # Look for composition names or trait combinations
                comp_match = re.search(r'([a-zA-Z\s]+)', after_keyword)
                if comp_match:
                    state.target_comp = comp_match.group(1).strip()
                    logger.debug(f"Parsed target comp: {state.target_comp}")
                break
        
        # Return state only if we parsed something useful
        if any([
            state.gold is not None,
            state.level is not None,
            state.health is not None,
            state.round_stage is not None,
            state.board_champions,
            state.bench_champions,
            state.shop_champions,
            state.target_comp
        ]):
            return state
        
        return None
    
    def _extract_champions_from_text(self, text: str) -> List[str]:
        """Extract champion names from a text snippet.
        
        Args:
            text: Text that may contain champion names
            
        Returns:
            List of recognized champion names
        """
        text = text.lower().strip()
        found_champions = []
        
        # Split on common separators first
        separators = [',', ' and ', ' & ']
        champion_segments = [text]
        
        for sep in separators:
            new_segments = []
            for segment in champion_segments:
                new_segments.extend(segment.split(sep))
            champion_segments = new_segments
        
        # Process each segment
        for segment in champion_segments:
            segment = segment.strip()
            if not segment:
                continue
                
            # Remove common filler words
            filler_words = ['with', 'plus', 'also', 'have', 'got', 'a', 'an', 'the', 'is', 'are']
            words = [w for w in segment.split() if w not in filler_words]
            cleaned_segment = ' '.join(words)
            
            if not cleaned_segment:
                continue
            
            # First, try exact matches from aliases
            found_in_segment = False
            for alias, real_name in self.champion_aliases.items():
                if alias == cleaned_segment or alias in cleaned_segment:
                    if real_name not in found_champions:
                        found_champions.append(real_name)
                        found_in_segment = True
                    break
            
            # If no exact match, try fuzzy matching
            if not found_in_segment:
                from rapidfuzz import fuzz, process
                
                champion_names = list(self.champion_aliases.values())
                
                # Try fuzzy match on the whole segment first
                match = process.extractOne(cleaned_segment, champion_names, scorer=fuzz.ratio)
                if match and match[1] > 80:  # Higher threshold for whole segment
                    if match[0] not in found_champions:
                        found_champions.append(match[0])
                else:
                    # Try individual words with lower threshold
                    for word in words:
                        if len(word) >= 3:  # Skip very short words
                            match = process.extractOne(word, champion_names, scorer=fuzz.ratio)
                            if match and match[1] > 75:
                                if match[0] not in found_champions:
                                    found_champions.append(match[0])
                                break  # Only take first good match per segment
        
        return found_champions
    
    def create_manual_state_prompt(self) -> str:
        """Create a prompt to ask user for manual input."""
        prompts = [
            "Tell me about your current game state. You can say things like:",
            "• 'I have 50 gold, level 7, with Jinx and Vi on my board'",
            "• 'My bench has Caitlyn and Ekko, shop shows Jayce'", 
            "• 'I'm level 6 with 30 health, trying to play Enforcers'",
            "• 'Round 4-2, I have 40 gold and want to roll for Jinx'",
            "",
            "What's your current situation?"
        ]
        return "\n".join(prompts)
    
    def format_state_for_ai(self, state: GameStateInput) -> str:
        """Format the parsed state for AI analysis.
        
        Args:
            state: Parsed game state
            
        Returns:
            Formatted string for AI prompt
        """
        parts = []
        
        if state.round_stage:
            parts.append(f"Round: {state.round_stage}")
        
        if state.level is not None:
            parts.append(f"Level: {state.level}")
        
        if state.gold is not None:
            parts.append(f"Gold: {state.gold}")
        
        if state.health is not None:
            parts.append(f"Health: {state.health}")
        
        if state.board_champions:
            champions_str = ", ".join(state.board_champions)
            parts.append(f"Board: {champions_str}")
        
        if state.bench_champions:
            champions_str = ", ".join(state.bench_champions)
            parts.append(f"Bench: {champions_str}")
        
        if state.shop_champions:
            champions_str = ", ".join(state.shop_champions)
            parts.append(f"Shop: {champions_str}")
        
        if state.target_comp:
            parts.append(f"Target composition: {state.target_comp}")
        
        return " | ".join(parts) if parts else "No game state information provided"
    
    def get_champion_info_for_state(self, state: GameStateInput) -> Dict[str, Any]:
        """Get detailed champion information for the current state.
        
        Args:
            state: Parsed game state
            
        Returns:
            Dictionary with champion details
        """
        try:
            champs_path = Path("data/champions.json")
            if not champs_path.exists():
                return {}
            
            with open(champs_path, 'r') as f:
                all_champions = json.load(f)
            
            # Create lookup dictionary
            champ_lookup = {champ['name'].lower(): champ for champ in all_champions}
            
            result = {
                'board_details': [],
                'bench_details': [],
                'shop_details': [],
                'traits_analysis': {}
            }
            
            # Get details for board champions
            for champ_name in state.board_champions:
                champ_info = champ_lookup.get(champ_name.lower())
                if champ_info:
                    result['board_details'].append(champ_info)
            
            # Get details for bench champions  
            for champ_name in state.bench_champions:
                champ_info = champ_lookup.get(champ_name.lower())
                if champ_info:
                    result['bench_details'].append(champ_info)
            
            # Get details for shop champions
            for champ_name in state.shop_champions:
                champ_info = champ_lookup.get(champ_name.lower())
                if champ_info:
                    result['shop_details'].append(champ_info)
            
            # Analyze traits from board champions
            trait_counts = {}
            for champ_info in result['board_details']:
                for trait in champ_info.get('traits', []):
                    trait_counts[trait] = trait_counts.get(trait, 0) + 1
            
            result['traits_analysis'] = {
                trait: count for trait, count in trait_counts.items() if count >= 2
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting champion info: {e}")
            return {}

# Global instance
_input_handler: Optional[ManualInputHandler] = None

def get_input_handler() -> ManualInputHandler:
    """Get or create the global input handler."""
    global _input_handler
    if _input_handler is None:
        _input_handler = ManualInputHandler()
    return _input_handler

def parse_user_game_state(query: str) -> Optional[GameStateInput]:
    """Convenience function to parse user input."""
    handler = get_input_handler()
    return handler.parse_voice_input(query)