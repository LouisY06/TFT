import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from assistant.tts_utils import speak
from assistant.gemini_service import GeminiClient, GeminiAPIError
from assistant.manual_input_handler import get_input_handler, parse_user_game_state

load_dotenv()
logger = logging.getLogger(__name__)

# Data file paths
DATA_DIR = Path(__file__).parent.parent / "data"
CHAMPS_PATH = DATA_DIR / "champions.json"
COMPS_PATH = DATA_DIR / "comps_output.json"

class TFTAssistant:
    """TFT Voice Assistant with improved error handling and logging."""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self._ensure_data_files()
    
    def _ensure_data_files(self) -> None:
        """Ensure required data files exist."""
        if not CHAMPS_PATH.exists():
            raise FileNotFoundError(f"Champions data file not found: {CHAMPS_PATH}")
        if not COMPS_PATH.exists():
            raise FileNotFoundError(f"Compositions data file not found: {COMPS_PATH}")
    
    def _load_data(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Load champions and compositions data with error handling."""
        try:
            with open(CHAMPS_PATH, encoding="utf-8") as f:
                champs = json.load(f)
            with open(COMPS_PATH, encoding="utf-8") as f:
                comps = json.load(f)
            
            logger.debug(f"Loaded {len(champs)} champions and {len(comps)} compositions")
            return champs, comps
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data files: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load data files: {e}")
            raise

    def _build_system_context(self) -> str:
        """Build the system context for Gemini."""
        return (
            "You are a Teamfight Tactics assistant. "
            "You know the current bench champions and gold levels from JSON, "
            "and the list of comps with their units. "
            "Answer any question dynamically based on that data, "
            "and be concise. Provide strategic advice about team composition, "
            "economy management, and positioning when relevant."
        )
    
    def _build_enhanced_system_context(self, has_manual_state: bool = False) -> str:
        """Build enhanced system context when manual game state is available.
        
        Args:
            has_manual_state: Whether manual game state information is available
            
        Returns:
            Enhanced system context for AI analysis
        """
        base_context = self._build_system_context()
        
        if has_manual_state:
            enhanced_context = (
                f"{base_context}\n\n"
                "CURRENT GAME STATE AVAILABLE:\n"
                "The user has provided their current game state including champions on board, "
                "bench, shop, gold, level, health, round, and target composition. "
                "Numerical data (gold, level, health, round) may be enhanced with real-time "
                "vision detection for accuracy. Use this information to provide highly specific "
                "and actionable advice. Consider synergies, power spikes, economy decisions, and "
                "positioning based on their exact situation.\n\n"
                "ANALYSIS PRIORITIES:\n"
                "1. Evaluate current board strength and synergies\n"
                "2. Suggest optimal purchases from shop\n"
                "3. Recommend positioning improvements\n"
                "4. Advise on economy management (save vs spend)\n"
                "5. Identify transition paths to stronger late-game compositions\n"
                "6. Consider win/loss streak implications\n"
                "7. Suggest items and champion upgrades"
            )
        else:
            enhanced_context = (
                f"{base_context}\n\n"
                "No specific game state provided. Ask the user to describe their current situation "
                "for more tailored advice. They can say things like:\n"
                "- 'I have 50 gold, level 7, with Jinx and Vi on my board'\n"
                "- 'My bench has Caitlyn, shop shows Jayce and Ekko'\n"
                "- 'Round 4-2, trying to play Enforcers, need advice'"
            )
        
        return enhanced_context

    def process_voice_query(self, query: str) -> str:
        """Process a voice query and return strategic advice.
        
        Args:
            query: User's voice query
            
        Returns:
            AI-generated response
        """
        if not query or not isinstance(query, str):
            error_msg = "Invalid query provided"
            logger.warning(error_msg)
            speak(error_msg)
            return error_msg
        
        query = query.strip()
        if not query:
            error_msg = "Empty query provided"
            logger.warning(error_msg)
            speak(error_msg)
            return error_msg
        
        logger.info(f"Processing voice query: {query[:100]}...")
        
        try:
            # First, try to parse manual game state from the query
            input_handler = get_input_handler()
            manual_state = parse_user_game_state(query)
            
            # Try to enhance with vision data for numerical values
            vision_data = None
            try:
                from vision.game_state_analyzer import GameStateAnalyzer
                vision_analyzer = GameStateAnalyzer()
                vision_data = vision_analyzer.get_game_stats_only()
                logger.info("Successfully retrieved vision data for game stats")
            except Exception as vision_error:
                logger.debug(f"Vision data not available: {vision_error}")
            
            # Merge manual and vision data
            if manual_state and vision_data:
                # Use vision data for numerical values if manual data is missing
                if manual_state.gold is None and vision_data.get('gold') is not None:
                    manual_state.gold = vision_data['gold']
                if manual_state.level is None and vision_data.get('level') is not None:
                    manual_state.level = vision_data['level']
                if manual_state.health is None and vision_data.get('health') is not None:
                    manual_state.health = vision_data['health']
                if manual_state.round_stage is None and vision_data.get('round_stage'):
                    manual_state.round_stage = vision_data['round_stage']
                logger.info("Enhanced manual input with vision data")
            elif vision_data and not manual_state:
                # Create a basic state from vision data only
                from assistant.manual_input_handler import GameStateInput
                manual_state = GameStateInput()
                manual_state.gold = vision_data.get('gold')
                manual_state.level = vision_data.get('level')
                manual_state.health = vision_data.get('health')
                manual_state.round_stage = vision_data.get('round_stage')
                logger.info("Created game state from vision data only")
            
            # Load champion and composition data
            champs, comps = self._load_data()
            
            # Build the prompt with available information
            system_ctx = self._build_enhanced_system_context(manual_state is not None)
            
            context = {
                "champions_database": champs,
                "compositions_database": comps
            }
            
            # Add manual state information if available
            if manual_state:
                logger.info("Using manual game state input")
                state_info = input_handler.get_champion_info_for_state(manual_state)
                formatted_state = input_handler.format_state_for_ai(manual_state)
                
                context["current_game_state"] = {
                    "parsed_input": formatted_state,
                    "champion_details": state_info,
                    "board_champions": manual_state.board_champions,
                    "bench_champions": manual_state.bench_champions,
                    "shop_champions": manual_state.shop_champions,
                    "gold": manual_state.gold,
                    "level": manual_state.level,
                    "health": manual_state.health,
                    "round": manual_state.round_stage,
                    "target_comp": manual_state.target_comp
                }
            else:
                logger.info("No manual game state detected, using general context")

            prompt = (
                f"{system_ctx}\n\n"
                f"DATA CONTEXT:\n{json.dumps(context, indent=2)}\n\n"
                f"USER QUERY:\n{query}\n\n"
                f"RESPONSE GUIDELINES:\n"
                f"- Be specific and actionable\n"
                f"- Consider economy, positioning, and win conditions\n"
                f"- Keep response under 200 words for voice delivery\n"
                f"- If game state is provided, give tailored advice\n"
                f"- If no game state, ask for more specific information"
            )

            answer = self.gemini_client.generate_content(prompt)
            
            if answer:
                logger.info("Successfully generated response")
                speak(answer)
                return answer
            else:
                error_msg = "No response generated"
                logger.warning(error_msg)
                speak(error_msg)
                return error_msg
                
        except GeminiAPIError as e:
            error_msg = f"AI service error: {str(e)}"
            logger.error(error_msg)
            speak("Sorry, I'm having trouble connecting to the AI service.")
            return error_msg
            
        except FileNotFoundError as e:
            error_msg = f"Data file error: {str(e)}"
            logger.error(error_msg)
            speak("Sorry, I can't access the game data files.")
            return error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            speak("Sorry, I encountered an unexpected error.")
            return error_msg

# Global assistant instance
_global_assistant = None

def get_assistant() -> TFTAssistant:
    """Get or create the global TFT assistant instance."""
    global _global_assistant
    if _global_assistant is None:
        _global_assistant = TFTAssistant()
    return _global_assistant

def process_voice_query(query: str) -> str:
    """Legacy function for backward compatibility."""
    assistant = get_assistant()
    return assistant.process_voice_query(query)