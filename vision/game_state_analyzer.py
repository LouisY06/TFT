import cv2
import numpy as np
import pyautogui
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import time

from assistant.gemini_service import get_global_client
from config.settings import get_ocr_settings
from vision.champion_detector import ChampionDetector

logger = logging.getLogger(__name__)

class TFTGameStateAnalyzer:
    """Analyzes TFT game state from screen captures."""
    
    def __init__(self):
        self.ocr_settings = get_ocr_settings()
        self.gemini_client = get_global_client()
        self.champion_detector = ChampionDetector()
        
        # Screen regions for different game elements (you'll need to calibrate these)
        self.regions = {
            'board': (200, 300, 1200, 700),      # Main board area
            'shop': (280, 850, 1000, 150),       # Shop area
            'gold': (50, 850, 100, 50),          # Gold counter
            'level': (150, 850, 100, 50),        # Level indicator
            'health': (50, 50, 200, 50),         # Health bar
            'round': (600, 50, 200, 50),         # Round counter
            'bench': (330, 850, 1250, 190),     # Bench area
        }
    
    def capture_screen_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Capture a specific region of the screen.
        
        Args:
            region: (x, y, width, height) tuple
            
        Returns:
            OpenCV image array
        """
        try:
            screenshot = pyautogui.screenshot(region=region)
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return cv_image
        except Exception as e:
            logger.error(f"Error capturing screen region {region}: {e}")
            return None
    
    def capture_full_game_state(self) -> Dict[str, np.ndarray]:
        """Capture all relevant game regions.
        
        Returns:
            Dictionary mapping region names to captured images
        """
        captures = {}
        
        for region_name, region_coords in self.regions.items():
            image = self.capture_screen_region(region_coords)
            if image is not None:
                captures[region_name] = image
                logger.debug(f"Captured {region_name}: {image.shape}")
            else:
                logger.warning(f"Failed to capture {region_name}")
        
        return captures
    
    def analyze_board_state(self, board_image: np.ndarray) -> Dict[str, Any]:
        """Analyze the main board for champions and positions.
        
        Args:
            board_image: OpenCV image of the board
            
        Returns:
            Dictionary containing board analysis
        """
        if board_image is None:
            return {"error": "No board image provided"}
        
        board_analysis = {
            "champions": [],
            "champion_count": 0,
            "total_cost": 0,
            "traits_active": [],
            "positioning": "unknown"
        }
        
        try:
            # Use template matching to detect specific champions
            detections = self.champion_detector.detect_champion_by_template(board_image, threshold=0.7)
            
            champions_info = []
            total_cost = 0
            
            for detection in detections:
                champ_name = detection['name']
                champ_info = self.champion_detector.get_champion_info(champ_name)
                
                champion_data = {
                    'name': champ_name,
                    'position': detection['position'],
                    'confidence': detection['confidence'],
                    'cost': champ_info.get('cost', 0),
                    'traits': champ_info.get('traits', [])
                }
                
                champions_info.append(champion_data)
                
                # Add to total cost if it's a number
                if isinstance(champ_info.get('cost'), int):
                    total_cost += champ_info['cost']
            
            board_analysis["champions"] = champions_info
            board_analysis["champion_count"] = len(champions_info)
            board_analysis["total_cost"] = total_cost
            
            # Calculate active traits
            trait_counts = {}
            for champ in champions_info:
                for trait in champ.get('traits', []):
                    trait_counts[trait] = trait_counts.get(trait, 0) + 1
            
            # Filter for meaningful trait counts (2+)
            active_traits = {trait: count for trait, count in trait_counts.items() if count >= 2}
            board_analysis["traits_active"] = active_traits
            
            # Save board screenshot for debugging
            timestamp = int(time.time())
            board_path = Path("screenshots") / f"board_{timestamp}.png"
            board_path.parent.mkdir(exist_ok=True)
            cv2.imwrite(str(board_path), board_image)
            
            logger.info(f"Board analysis: {len(champions_info)} champions, {total_cost} total cost, traits: {active_traits}")
            
        except Exception as e:
            logger.error(f"Error analyzing board state: {e}")
            board_analysis["error"] = str(e)
        
        return board_analysis
    
    def analyze_shop_state(self, shop_image: np.ndarray) -> Dict[str, Any]:
        """Analyze the shop for available champions.
        
        Args:
            shop_image: OpenCV image of the shop
            
        Returns:
            Dictionary containing shop analysis
        """
        if shop_image is None:
            return {"error": "No shop image provided"}
        
        shop_analysis = {
            "shop_slots": [],
            "total_cost": 0,
            "available_champions": [],
            "costs_distribution": {},
            "reroll_value": "unknown"
        }
        
        try:
            # Analyze individual shop slots
            slots = self.champion_detector.analyze_shop_slots(shop_image)
            
            available_champions = []
            total_cost = 0
            costs_distribution = {}
            
            for slot in slots:
                if slot.get('champion_name') != 'unknown':
                    champ_name = slot['champion_name']
                    champ_cost = slot.get('cost')
                    
                    available_champions.append({
                        'name': champ_name,
                        'cost': champ_cost,
                        'slot': slot['slot_index'],
                        'confidence': slot.get('confidence', 0)
                    })
                    
                    if champ_cost:
                        total_cost += champ_cost
                        costs_distribution[champ_cost] = costs_distribution.get(champ_cost, 0) + 1
            
            shop_analysis["shop_slots"] = slots
            shop_analysis["available_champions"] = available_champions
            shop_analysis["total_cost"] = total_cost
            shop_analysis["costs_distribution"] = costs_distribution
            
            # Save shop screenshot with analysis
            timestamp = int(time.time())
            shop_path = Path("screenshots") / f"shop_{timestamp}.png"
            shop_path.parent.mkdir(exist_ok=True)
            
            # Draw detection boxes on the image for debugging
            debug_image = shop_image.copy()
            slot_width = shop_image.shape[1] // 5
            
            for i, slot in enumerate(slots):
                x = i * slot_width
                y = 0
                w = slot_width
                h = shop_image.shape[0]
                
                # Draw slot boundaries
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Add text labels
                label = f"{slot.get('champion_name', 'unknown')} ({slot.get('cost', '?')})"
                cv2.putText(debug_image, label, (x + 5, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imwrite(str(shop_path), debug_image)
            shop_analysis["screenshot_path"] = str(shop_path)
            
            logger.info(f"Shop analysis: {len(available_champions)} champions detected, total cost: {total_cost}")
            
        except Exception as e:
            logger.error(f"Error analyzing shop state: {e}")
            shop_analysis["error"] = str(e)
        
        return shop_analysis
    
    def extract_game_text(self, image: np.ndarray, region_name: str) -> str:
        """Extract text from image using OCR.
        
        Args:
            image: OpenCV image
            region_name: Name of the region for logging
            
        Returns:
            Extracted text string
        """
        try:
            # Use the champion detector's OCR method for consistency
            text = self.champion_detector.detect_text_in_region(image, region_name)
            
            logger.debug(f"Extracted text from {region_name}: '{text}'")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from {region_name}: {e}")
            return ""
    
    def analyze_complete_game_state(self) -> Dict[str, Any]:
        """Capture and analyze the complete game state.
        
        Returns:
            Complete analysis of the current game state
        """
        start_time = time.time()
        logger.info("Starting complete game state analysis")
        
        # Capture all regions
        captures = self.capture_full_game_state()
        
        if not captures:
            logger.error("No captures obtained")
            return {"error": "Failed to capture screen"}
        
        # Analyze each component
        analysis = {
            "timestamp": int(time.time()),
            "analysis_duration": 0,
            "board": {},
            "shop": {},
            "resources": {},
            "game_info": {}
        }
        
        # Analyze board
        if 'board' in captures:
            analysis["board"] = self.analyze_board_state(captures['board'])
        
        # Analyze shop
        if 'shop' in captures:
            analysis["shop"] = self.analyze_shop_state(captures['shop'])
        
        # Extract resource information
        resources = {}
        for resource in ['gold', 'level', 'health']:
            if resource in captures:
                text = self.extract_game_text(captures[resource], resource)
                resources[resource] = text
        analysis["resources"] = resources
        
        # Extract game info
        game_info = {}
        for info in ['round']:
            if info in captures:
                text = self.extract_game_text(captures[info], info)
                game_info[info] = text
        analysis["game_info"] = game_info
        
        analysis["analysis_duration"] = time.time() - start_time
        logger.info(f"Game state analysis completed in {analysis['analysis_duration']:.2f}s")
        
        return analysis
    
    def get_strategic_advice(self, game_state: Dict[str, Any]) -> str:
        """Get strategic advice based on the analyzed game state.
        
        Args:
            game_state: Complete game state analysis
            
        Returns:
            Strategic advice text
        """
        try:
            # Create a structured prompt for Gemini
            prompt = self._build_strategic_prompt(game_state)
            
            response = self.gemini_client.generate_content(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error getting strategic advice: {e}")
            return f"Unable to provide strategic advice: {str(e)}"
    
    def _build_strategic_prompt(self, game_state: Dict[str, Any]) -> str:
        """Build a strategic analysis prompt for Gemini.
        
        Args:
            game_state: Complete game state analysis
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are a TFT (Teamfight Tactics) strategic advisor. Analyze this game state and provide specific advice.",
            "",
            "CURRENT GAME STATE:",
        ]
        
        # Add resource information
        if game_state.get("resources"):
            resources = game_state["resources"]
            prompt_parts.append(f"Gold: {resources.get('gold', 'unknown')}")
            prompt_parts.append(f"Level: {resources.get('level', 'unknown')}")
            prompt_parts.append(f"Health: {resources.get('health', 'unknown')}")
        
        # Add game information
        if game_state.get("game_info"):
            game_info = game_state["game_info"]
            prompt_parts.append(f"Round: {game_info.get('round', 'unknown')}")
        
        # Add board information
        if game_state.get("board"):
            board = game_state["board"]
            champion_count = board.get("champion_count", 0)
            prompt_parts.append(f"Champions on board: {champion_count}")
        
        # Add shop information
        if game_state.get("shop"):
            shop = game_state["shop"]
            if shop.get("screenshot_path"):
                prompt_parts.append("Shop state captured for analysis")
        
        prompt_parts.extend([
            "",
            "PROVIDE STRATEGIC ADVICE:",
            "1. Should I reroll or save gold?",
            "2. What should I prioritize buying?",
            "3. Any positioning adjustments needed?",
            "4. Economic strategy for next few rounds?",
            "",
            "Keep advice concise and actionable (under 200 words)."
        ])
        
        return "\n".join(prompt_parts)
    
    def get_game_stats_only(self) -> Dict[str, Any]:
        """Get only the numerical game stats (gold, level, health, round) without champion detection.
        
        This is optimized for speed and reliability when used with manual input for champions.
        
        Returns:
            Dictionary with numerical game stats
        """
        logger.debug("Getting game stats only (no champion detection)")
        
        # Capture only the text regions we need
        text_regions = ['gold', 'level', 'health', 'round']
        captures = {}
        
        for region_name in text_regions:
            if region_name in self.regions:
                image = self.capture_screen_region(self.regions[region_name])
                if image is not None:
                    captures[region_name] = image
        
        # Extract text from each region
        stats = {}
        
        try:
            # Extract and parse gold
            if 'gold' in captures:
                gold_text = self.extract_game_text(captures['gold'], 'gold')
                # Extract number from text (e.g. "50" from "Gold: 50")
                import re
                gold_match = re.search(r'(\d+)', gold_text)
                if gold_match:
                    stats['gold'] = int(gold_match.group(1))
                    logger.debug(f"Detected gold: {stats['gold']}")
            
            # Extract and parse level
            if 'level' in captures:
                level_text = self.extract_game_text(captures['level'], 'level')
                level_match = re.search(r'(\d+)', level_text)
                if level_match:
                    stats['level'] = int(level_match.group(1))
                    logger.debug(f"Detected level: {stats['level']}")
            
            # Extract and parse health
            if 'health' in captures:
                health_text = self.extract_game_text(captures['health'], 'health')
                health_match = re.search(r'(\d+)', health_text)
                if health_match:
                    stats['health'] = int(health_match.group(1))
                    logger.debug(f"Detected health: {stats['health']}")
            
            # Extract round/stage
            if 'round' in captures:
                round_text = self.extract_game_text(captures['round'], 'round')
                # Look for patterns like "4-2" or "Round 4-2"
                round_match = re.search(r'(\d+-\d+)', round_text)
                if round_match:
                    stats['round_stage'] = round_match.group(1)
                    logger.debug(f"Detected round: {stats['round_stage']}")
        
        except Exception as e:
            logger.error(f"Error extracting game stats: {e}")
        
        logger.info(f"Vision stats extracted: {stats}")
        return stats

# Class alias for backwards compatibility and cleaner imports
GameStateAnalyzer = TFTGameStateAnalyzer

# Global analyzer instance
_game_analyzer: Optional[TFTGameStateAnalyzer] = None

def get_game_analyzer() -> TFTGameStateAnalyzer:
    """Get or create the global game state analyzer."""
    global _game_analyzer
    if _game_analyzer is None:
        _game_analyzer = TFTGameStateAnalyzer()
    return _game_analyzer

def analyze_current_game() -> Dict[str, Any]:
    """Convenience function to analyze current game state."""
    analyzer = get_game_analyzer()
    return analyzer.analyze_complete_game_state()

def get_game_advice() -> str:
    """Convenience function to get strategic advice for current game state."""
    analyzer = get_game_analyzer()
    game_state = analyzer.analyze_complete_game_state()
    return analyzer.get_strategic_advice(game_state)