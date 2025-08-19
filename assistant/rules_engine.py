import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from assistant.tts_utils import speak
from assistant.gemini_service import GeminiClient, GeminiAPIError

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
            champs, comps = self._load_data()
            
            system_ctx = self._build_system_context()
            context = {
                "bench_data": champs,
                "comps": comps
            }

            prompt = (
                f"{system_ctx}\n\n"
                f"DATA CONTEXT (JSON):\n{json.dumps(context, indent=2)}\n\n"
                f"USER QUESTION:\n{query}"
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